"""
Views مدیریت پرداخت و پلن.
"""

import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.decorators import business_required

from ..constants import PaymentMethod, PaymentStatus
from ..forms import PaymentForm
from ..models import Payment, Plan

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  My Plan
# ═══════════════════════════════════════════════════════════════


@business_required
@require_GET
def my_plan(request: HttpRequest) -> HttpResponse:
    """صفحه‌ی پلن فعلی + تاریخچه."""
    business = request.user.business

    payments = business.payments.all().order_by("-created_at")[:20]

    context = {
        "business": business,
        "payments": payments,
        "today": timezone.localdate(),
    }

    return render(request, "business/my_plan.html", context)


# ═══════════════════════════════════════════════════════════════
#  Buy Plan
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def buy_plan(request: HttpRequest) -> HttpResponse:
    """صفحه‌ی خرید پلن (کارت به کارت)."""
    business = request.user.business

    # ─── پلن‌های فعال (غیر از trial) ───
    paid_plans = Plan.objects.filter(
        is_active=True,
        is_paid=True,
    ).order_by("order", "price")

    if request.method == "POST":
        form = PaymentForm(request.POST, request.FILES, business=business)

        if form.is_valid():
            payment = form.save(commit=False)
            payment.business = business
            payment.method = PaymentMethod.CARD_TO_CARD
            payment.status = PaymentStatus.PENDING

            # ─── قیمت از Plan میاد ───
            payment.amount = payment.plan.price

            payment.save()

            logger.info(
                f"Payment created: {business.name} — "
                f"{payment.plan.name} — {payment.amount:,} تومان"
            )

            messages.success(
                request,
                _("رسیدت ثبت شد! ✅ بعد از تأیید مدیر، پلنت فعال میشه."),
            )
            return redirect("business:my_plan")
    else:
        form = PaymentForm(business=business)

    # ─── اطلاعات کارت ───
    card_info = {
        "number": getattr(settings, "PAYMENT_CARD_NUMBER", "6037-XXXX-XXXX-XXXX"),
        "owner": getattr(settings, "PAYMENT_CARD_OWNER", "آرایشیار"),
        "bank": getattr(settings, "PAYMENT_CARD_BANK", "بانک ملی"),
    }

    context = {
        "business": business,
        "form": form,
        "plans": paid_plans,
        "card_info": card_info,
    }

    return render(request, "business/buy_plan.html", context)


# ═══════════════════════════════════════════════════════════════
#  Cancel Payment
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["POST"])
def cancel_payment(request: HttpRequest, payment_id: int) -> HttpResponse:
    """لغو پرداخت معلق."""
    business = request.user.business
    payment = get_object_or_404(
        Payment,
        id=payment_id,
        business=business,
        status=PaymentStatus.PENDING,
    )

    if payment.receipt:
        payment.receipt.delete(save=False)

    payment.delete()

    if request.headers.get("HX-Request"):
        return HttpResponse("")

    messages.success(request, _("پرداخت لغو شد."))
    return redirect("business:my_plan")