"""
Views مشتری — نوبت‌های من، لیست انتظار من.
"""

from datetime import timedelta

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_POST

from apps.core.decorators import customer_required

from ..constants import AppointmentStatus
from ..models import Appointment
from ..selectors import (
    get_customer_appointments,
    get_customer_waiting_items,
)


# ═══════════════════════════════════════════════════════════════
#  My Appointments
# ═══════════════════════════════════════════════════════════════


@customer_required
@require_GET
def my_appointments(request: HttpRequest) -> HttpResponse:
    """نوبت‌های من."""
    upcoming = get_customer_appointments(request.user, upcoming_only=True)
    past = get_customer_appointments(request.user, upcoming_only=False).exclude(
        id__in=[a.id for a in upcoming]
    )[:20]

    return render(
        request,
        "booking/my_appointments.html",
        {
            "upcoming": upcoming,
            "past": past,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Cancel My Appointment
# ═══════════════════════════════════════════════════════════════


@customer_required
@require_POST
def cancel_my_appointment(
    request: HttpRequest,
    appointment_id: int,
) -> HttpResponse:
    """
    لغو نوبت توسط مشتری.

    ─── قانون: ───
    فقط تا ۱ ساعت قبل از نوبت می‌شه لغو کرد.

    ─── HTMX: ───
    پاسخ خالی برمی‌گردونه تا آیتم از DOM حذف بشه.
    """
    customer = request.user

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        customer=customer,
    )

    # ─── چک امکان لغو ───
    if not appointment.can_be_cancelled:
        msg = _build_cancel_error_message(appointment)

        if request.headers.get("HX-Request"):
            return HttpResponse(msg, status=400)

        messages.error(request, msg)
        return redirect("booking:my_appointments")

    # ─── لغو ───
    appointment.cancel(reason="لغو توسط مشتری", by_user=customer)

    # ─── اگه HTMX → پاسخ خالی ───
    if request.headers.get("HX-Request"):
        return HttpResponse("")

    messages.success(request, _("نوبت لغو شد."))
    return redirect("booking:my_appointments")


# ═══════════════════════════════════════════════════════════════
#  My Waiting
# ═══════════════════════════════════════════════════════════════


@customer_required
@require_GET
def my_waiting(request: HttpRequest) -> HttpResponse:
    """لیست انتظار من."""
    items = get_customer_waiting_items(request.user)

    return render(
        request,
        "booking/my_waiting.html",
        {"items": items},
    )


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════


def _build_cancel_error_message(appointment: Appointment) -> str:
    """
    ساخت پیام خطای مناسب برای لغو.

    ─── حالت‌ها: ───
    - cancelled   → قبلاً لغو شده
    - completed   → انجام شده
    - past        → گذشته
    - too_close   → کمتر از ۱ ساعت مونده
    - no_start    → زمان شروع نداره
    """
    reason = appointment.can_be_cancelled_reason

    if reason == "cancelled":
        return str(_("این نوبت قبلاً لغو شده."))

    if reason == "completed":
        return str(_("این نوبت انجام شده و قابل لغو نیست."))

    if reason == "past":
        return str(_("این نوبت گذشته و قابل لغو نیست."))

    if reason == "no_start":
        return str(_("امکان لغو این نوبت وجود نداره."))

    if reason == "too_close":
        # ─── محاسبه‌ی دقیقه‌ی باقی‌مونده ───
        time_left = appointment.start_at - timezone.now()
        minutes_left = max(0, int(time_left.total_seconds() / 60))
        return str(
            _(
                "کمتر از ۱ ساعت به نوبت مونده (%(min)s دقیقه). "
                "امکان لغو وجود نداره. لطفاً با کسب‌وکار تماس بگیر."
            )
            % {"min": minutes_left}
        )

    return str(_("امکان لغو این نوبت وجود نداره."))