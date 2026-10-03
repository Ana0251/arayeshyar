"""
Views کسب‌وکار — مدیریت نوبت‌ها.
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.business.models import Service
from apps.core.decorators import business_required

from ..forms import ManualAppointmentForm
from ..models import Appointment
from ..services import BookingService
from ._helpers import htmx_error, htmx_response, is_htmx

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Update Status (HTMX)
# ═══════════════════════════════════════════════════════════════


@business_required
@require_POST
def update_status(
    request: HttpRequest,
    appointment_id: int,
    new_status: str,
) -> HttpResponse:
    """
    تغییر وضعیت نوبت (تأیید/لغو/انجام).

    ─── HTMX: ───
    برمی‌گردونه ردیف نوبت رو با وضعیت جدید.
    """
    business = request.user.business

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        business=business,
    )

    # ─── تغییر وضعیت ───
    if new_status == "confirmed":
        appointment.confirm(by_user=request.user)
    elif new_status == "cancelled":
        appointment.cancel(reason="لغو توسط کسب‌وکار", by_user=request.user)
    elif new_status == "completed":
        appointment.complete()
    else:
        if is_htmx(request):
            return htmx_error(request, _("وضعیت نامعتبره."))
        messages.error(request, _("وضعیت نامعتبره."))
        return redirect("business:dashboard")

    # ─── پاسخ HTMX ───
    if is_htmx(request):
        return htmx_response(
            request,
            template="business/partials/_appointment_row.html",
            context={
                "appt": appointment,
                "business": business,
            },
        )

    status_labels = {
        "confirmed": "تأیید شد ✅",
        "cancelled": "لغو شد ❌",
        "completed": "انجام شد ✓",
    }
    messages.success(
        request,
        _("نوبت %(name)s %(status)s")
        % {
            "name": appointment.customer.display_name,
            "status": status_labels.get(new_status, ""),
        },
    )
    return redirect("business:dashboard")


# ═══════════════════════════════════════════════════════════════
#  Delete Appointment
# ═══════════════════════════════════════════════════════════════


@business_required
@require_POST
def delete_appointment(
    request: HttpRequest,
    appointment_id: int,
) -> HttpResponse:
    """حذف کامل نوبت."""
    business = request.user.business
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        business=business,
    )

    name = appointment.customer.display_name
    appointment.delete()

    if is_htmx(request):
        return HttpResponse("")  # حذف از DOM

    messages.success(
        request,
        _("نوبت %(name)s حذف شد.") % {"name": name},
    )
    return redirect("business:dashboard")


# ═══════════════════════════════════════════════════════════════
#  Add Manual Appointment
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def add_manual_appointment(request: HttpRequest) -> HttpResponse:
    """
    ثبت نوبت دستی (تلفنی/حضوری).

    ─── نکته: ───
    با force=True → می‌شه نوبت متداخل ثبت کرد (با هشدار).
    """
    business = request.user.business

    if not business.is_active:
        messages.warning(request, _("کسب‌وکارت هنوز تأیید نشده."))
        return redirect("business:dashboard")

    if request.method == "POST":
        form = ManualAppointmentForm(request.POST, business=business)

        if form.is_valid():
            try:
                # ─── پیدا یا ساخت کاربر ───
                from apps.accounts.models import User

                customer, created = User.objects.get_or_create(
                    phone=form.cleaned_data["customer_phone"],
                    defaults={
                        "role": "customer",
                        "is_active": True,
                    },
                )

                # ─── آپدیت نام اگه لازم ───
                if not created:
                    profile = getattr(customer, "customer_profile", None)
                    if profile and profile.full_name != form.cleaned_data["customer_name"]:
                        profile.full_name = form.cleaned_data["customer_name"]
                        profile.save()

                # ─── چک بلاک ───
                from ..models import BlockedCustomer

                is_blocked = BlockedCustomer.objects.is_blocked(
                    business, customer.phone
                )
                if is_blocked:
                    messages.warning(
                        request,
                        _("⚠️ این شماره توی لیست سیاه تو هست."),
                    )

                # ─── ثبت نوبت ───
                service = get_object_or_404(
                    Service,
                    id=form.cleaned_data["service_id"],
                    business=business,
                )

                booking_service = BookingService(business)
                appointment = booking_service.create_appointment(
                    customer=customer,
                    service=service,
                    start_at=form.cleaned_data["start_at"],
                    customer_note=form.cleaned_data.get("customer_note", ""),
                    created_by=request.user,
                    force=True,  # ← اجازه تداخل
                )

                # ─── وضعیت دلخواه ───
                if form.cleaned_data["status"] == "pending":
                    appointment.status = "pending"
                    appointment.save(update_fields=["status"])

                # ─── ثبت در لیست مشتری ───
                from apps.customers.services import CustomerBusinessService

                CustomerBusinessService.add_to_my_list(customer, business)

                messages.success(
                    request,
                    _("نوبت %(name)s برای %(date)s ساعت %(time)s ثبت شد. ✅")
                    % {
                        "name": customer.display_name,
                        "date": appointment.start_at.strftime("%Y/%m/%d"),
                        "time": appointment.start_at.strftime("%H:%M"),
                    },
                )
                return redirect("business:dashboard")

            except Exception as exc:
                logger.exception(f"Manual booking failed: {exc}")
                messages.error(
                    request,
                    _("خطا در ثبت نوبت. لطفاً دوباره امتحان کن."),
                )
        else:
            messages.error(request, _("لطفاً خطاها رو برطرف کن."))
    else:
        initial = {
            "start_at": timezone.now().replace(
                minute=0, second=0, microsecond=0
            ) + timezone.timedelta(hours=1),
            "status": "confirmed",
        }
        form = ManualAppointmentForm(initial=initial, business=business)

    return render(
        request,
        "booking/add_appointment.html",
        {
            "business": business,
            "form": form,
        },
    )