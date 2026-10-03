"""
Views لیست انتظار.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.business.models import Business, Service
from apps.core.decorators import business_required, customer_required

from ..constants import WaitingStatus
from ..forms import WaitingListForm
from ..models import WaitingList
from ..selectors import get_business_waiting_list
from ..services import BookingService, WaitingListService
from ._helpers import htmx_response, is_htmx

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Join Waiting List (مشتری)
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET", "POST"])
def join_waiting_list(request: HttpRequest, slug: str) -> HttpResponse:
    """ثبت در لیست انتظار."""
    business = get_object_or_404(
        Business.objects.active(),
        slug=slug,
    )

    # ─── چک بلاک ───
    from ..models import BlockedCustomer

    if BlockedCustomer.objects.is_blocked(business, request.user.phone):
        messages.error(request, _("امکان ثبت در لیست انتظار وجود نداره."))
        return redirect("business:public_profile", slug=slug)

    # ─── چک کسب‌وکار خودش ───
    if hasattr(request.user, "business") and request.user.business == business:
        messages.warning(request, _("نمی‌تونی برای خودت ثبت کنی."))
        return redirect("business:dashboard")

    if request.method == "POST":
        form = WaitingListForm(request.POST)
        service_id = request.POST.get("service_id")

        if form.is_valid() and service_id:
            service = get_object_or_404(
                Service,
                id=service_id,
                business=business,
                is_active=True,
            )

            wl_service = WaitingListService(business)
            item = wl_service.add_to_waiting_list(
                customer=request.user,
                service=service,
                target_date=form.cleaned_data["date"],
                preferred_time=form.cleaned_data.get("preferred_time"),
                note=form.cleaned_data.get("note", ""),
            )

            messages.success(
                request,
                _("توی لیست انتظار %(name)s ثبت شدی. ✅")
                % {"name": business.name},
            )
            return redirect("booking:my_waiting")
        else:
            messages.error(request, _("لطفاً خطاها رو برطرف کن."))
    else:
        initial = {}
        date_str = request.GET.get("date")
        if date_str:
            from datetime import datetime

            try:
                initial["date"] = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        form = WaitingListForm(initial=initial)

    services = business.services.filter(is_active=True).order_by("order", "name")

    return render(
        request,
        "booking/join_waiting.html",
        {
            "business": business,
            "form": form,
            "services": services,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Manage Waiting List (کسب‌وکار)
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET"])
def manage_waiting_list(request: HttpRequest) -> HttpResponse:
    """مدیریت لیست انتظار."""
    business = request.user.business

    waiting = get_business_waiting_list(business)
    past = get_business_waiting_list(business, include_past=True).exclude(
        status=WaitingStatus.WAITING
    )[:20]

    return render(
        request,
        "booking/waiting_list.html",
        {
            "business": business,
            "waiting": waiting,
            "past": past,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Update Waiting Status
# ═══════════════════════════════════════════════════════════════


@business_required
@require_POST
def update_waiting_status(
    request: HttpRequest,
    item_id: int,
    new_status: str,
) -> HttpResponse:
    """
    تغییر وضعیت آیتم لیست انتظار.

    ─── HTMX: ───
    یه پاسخ خالی برمی‌گردونه که آیتم از DOM حذف بشه.
    """
    business = request.user.business
    item = get_object_or_404(
        WaitingList,
        id=item_id,
        business=business,
    )

    valid = ["waiting", "notified", "expired", "cancelled"]
    if new_status not in valid:
        if is_htmx(request):
            return HttpResponse(status=400)
        messages.error(request, _("وضعیت نامعتبره."))
        return redirect("booking:manage_waiting_list")

    # ─── آپدیت وضعیت ───
    item.status = new_status
    item.save(update_fields=["status", "updated_at"])

    # ─── اگه HTMX → پاسخ خالی (آیتم از DOM حذف میشه) ───
    if is_htmx(request):
        return HttpResponse("")

    messages.success(request, _("وضعیت به‌روزرسانی شد."))
    return redirect("booking:manage_waiting_list")


# ═══════════════════════════════════════════════════════════════
#  Convert Waiting to Appointment
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def convert_waiting_to_appointment(
    request: HttpRequest,
    item_id: int,
) -> HttpResponse:
    """تبدیل آیتم لیست انتظار به نوبت."""
    business = request.user.business
    item = get_object_or_404(
        WaitingList,
        id=item_id,
        business=business,
    )

    # ─── چک وضعیت ───
    if item.status in (
        WaitingStatus.NOTIFIED,
        WaitingStatus.CANCELLED,
        WaitingStatus.EXPIRED,
        WaitingStatus.CONVERTED,
    ):
        messages.warning(request, _("این آیتم قبلاً پردازش شده."))
        return redirect("booking:manage_waiting_list")

    # ─── اسلات‌های آزاد ───
    from ..services.availability import AvailabilityService

    service = item.service
    duration = service.duration if service else 30

    availability = AvailabilityService(business, item.date)
    slots = availability.get_available_slots(duration=duration)

    if request.method == "POST":
        time_str = request.POST.get("time")

        if not time_str:
            messages.error(request, _("لطفاً یه ساعت انتخاب کن."))
        else:
            try:
                from datetime import datetime, time

                h, m = time_str.split(":")
                time_obj = time(int(h), int(m))

                if time_obj not in slots:
                    messages.error(request, _("این ساعت آزاد نیست."))
                else:
                    from datetime import datetime as dt

                    start_at = dt.combine(item.date, time_obj)
                    start_at = timezone.make_aware(
                        start_at,
                        timezone.get_current_timezone(),
                    )

                    booking_service = BookingService(business)
                    appointment = booking_service.create_appointment(
                        customer=item.customer,
                        service=service,
                        start_at=start_at,
                        customer_note=item.note,
                        created_by=request.user,
                        force=True,
                    )

                    item.mark_converted()

                    messages.success(
                        request,
                        _("نوبت %(name)s ثبت و تأیید شد. ✅")
                        % {"name": item.customer.display_name},
                    )
                    return redirect("booking:manage_waiting_list")

            except Exception as exc:
                logger.exception(f"Convert failed: {exc}")
                messages.error(request, _("خطا در تبدیل."))

    return render(
        request,
        "booking/convert_waiting.html",
        {
            "business": business,
            "item": item,
            "slots": slots,
            "preferred_str": (
                item.preferred_time.strftime("%H:%M")
                if item.preferred_time
                else None
            ),
        },
    )