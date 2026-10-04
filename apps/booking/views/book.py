"""
Views رزرو نوبت (عمومی).
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from apps.business.models import (
    Business,
    Service,
    Staff,
    StaffService,
    Station,
)
from apps.business.selectors import get_business_by_slug
from apps.customers.services import CustomerBusinessService

from ..forms import AppointmentForm
from ..models import BlockedCustomer
from ..services import BookingError, BookingService, SlotNotAvailableError
from ..services.availability import AvailabilityService

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Book Appointment
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET", "POST"])
def book_appointment(request: HttpRequest, slug: str) -> HttpResponse:
    """صفحه رزرو نوبت."""
    business = get_object_or_404(
        Business.objects.active(),
        slug=slug,
    )

    # ─── اگه کسب‌وکار خودشه، اجازه نده ───
    if hasattr(request.user, "business") and request.user.business == business:
        messages.warning(request, _("نمی‌تونی برای کسب‌وکار خودت نوبت بگیری."))
        return redirect("business:dashboard")

    # ─── چک بلاک نبودن ───
    if BlockedCustomer.objects.is_blocked(business, request.user.phone):
        messages.error(request, _("امکان رزرو برای شما وجود نداره."))
        return redirect("business:public_profile", slug=slug)

    # ─── POST: ثبت ───
    if request.method == "POST":
        return _handle_booking_post(request, business)

    # ─── GET: نمایش ───
    return _render_booking_page(request, business)


# ═══════════════════════════════════════════════════════════════
#  POST Handler
# ═══════════════════════════════════════════════════════════════


def _handle_booking_post(request: HttpRequest, business: Business) -> HttpResponse:
    """پردازش POST رزرو."""
    form = AppointmentForm(request.POST)

    if not form.is_valid():
        messages.error(request, _("لطفاً خطاها رو برطرف کن."))
        return _render_booking_page(request, business, form=form)

    try:
        data = form.cleaned_data

        # ─── پیدا کردن خدمت ───
        service = get_object_or_404(
            Service,
            id=data["service_id"],
            business=business,
            is_active=True,
        )

        # ─── پیدا کردن staff (اگه انتخاب شده) ───
        staff = None
        staff_id = data.get("staff_id")
        if staff_id:
            staff = Staff.objects.filter(
                id=staff_id,
                business=business,
                is_active=True,
            ).first()

        # ─── ذخیره‌ی نام مشتری ───
        customer = request.user
        new_name = (data.get("customer_name") or "").strip()

        if new_name and customer.is_customer:
            profile = getattr(customer, "customer_profile", None)
            if profile and profile.full_name != new_name:
                profile.full_name = new_name
                profile.save(update_fields=["full_name", "updated_at"])
                logger.info(f"Customer name saved: {customer.phone} → {new_name}")

        # ─── ثبت نوبت ───
        booking_service = BookingService(business)
        appointment = booking_service.create_appointment(
            customer=customer,
            service=service,
            start_at=data["start_at"],
            staff=staff,
            customer_note=data.get("customer_note", ""),
        )

        # ─── ثبت در لیست مشتری ───
        CustomerBusinessService.add_to_my_list(customer, business)

        # ─── پیام ───
        if appointment.is_confirmed:
            messages.success(
                request,
                _("نوبتت تأیید شد! ✅ %(date)s ساعت %(time)s")
                % {
                    "date": appointment.start_at.strftime("%Y/%m/%d"),
                    "time": appointment.start_at.strftime("%H:%M"),
                },
            )
        else:
            messages.success(
                request,
                _("نوبتت ثبت شد و در انتظار تأیید. ⏳"),
            )

        return redirect("booking:my_appointments")

    except SlotNotAvailableError:
        messages.error(
            request,
            _("این ساعت در دسترس نیست. لطفاً یه ساعت دیگه انتخاب کن."),
        )
        return _render_booking_page(request, business, form=form)

    except BookingError as exc:
        messages.error(request, str(exc))
        return _render_booking_page(request, business, form=form)

    except Exception:
        logger.exception("Booking failed")
        messages.error(request, _("خطا در ثبت نوبت. لطفاً دوباره امتحان کن."))
        return _render_booking_page(request, business, form=form)


# ═══════════════════════════════════════════════════════════════
#  GET Handler
# ═══════════════════════════════════════════════════════════════


def _render_booking_page(
    request: HttpRequest,
    business: Business,
    form: AppointmentForm | None = None,
) -> HttpResponse:
    """رندر صفحه‌ی رزرو."""
    # ─── پارامترهای GET ───
    selected_station_id = request.GET.get("station")
    selected_service_id = request.GET.get("service")
    selected_staff_id = request.GET.get("staff")
    selected_date_str = request.GET.get("date")

    has_date_param = bool(selected_date_str)

    # ─── ایستگاه‌ها ───
    stations = []
    if business.is_salon:
        stations = list(
            business.stations.filter(is_active=True).order_by("order", "id")
        )

    # ─── ایستگاه انتخابی ───
    selected_station = None
    if selected_station_id:
        selected_station = Station.objects.filter(
            id=selected_station_id,
            business=business,
            is_active=True,
        ).first()

    # ─── خدمات ───
    services_qs = business.services.filter(is_active=True).select_related("station")
    if business.is_salon:
        if selected_station:
            services_qs = services_qs.filter(station=selected_station)
        if not selected_station:
            services_qs = services_qs.none()

    services_qs = services_qs.order_by("order", "name")
    services = list(services_qs)

    # ─── خدمت انتخابی ───
    selected_service = None
    if selected_service_id:
        selected_service = (
            Service.objects.filter(
                id=selected_service_id,
                business=business,
                is_active=True,
            )
            .select_related("station")
            .first()
        )

    # ═══════════════════════════════════════════════════════════
    #  staff (از StaffService — نه M2M)
    # ═══════════════════════════════════════════════════════════
    staff_members = []
    selected_staff = None
    if selected_service:
        staff_services = (
            StaffService.objects.filter(
                service=selected_service,
                station=selected_service.station,
                is_active=True,
                staff__is_active=True,
            )
            .select_related("staff")
            .order_by("staff__order", "staff__name")
        )

        staff_members = [ss.staff for ss in staff_services]

        if selected_staff_id:
            selected_staff = next(
                (s for s in staff_members if str(s.id) == str(selected_staff_id)),
                None,
            )

    # ─── تاریخ ───
    selected_date = _parse_date(selected_date_str)

    # ─── اسلات‌ها ───
    slots = []
    if selected_service and has_date_param:
        duration = selected_service.duration
        availability = AvailabilityService(
            business,
            selected_date,
            station=selected_station,
            staff=selected_staff,
        )
        slots = availability.get_all_slots_with_status(duration=duration)

    # ─── فرم ───
    if form is None:
        customer_name = request.user.display_name
        customer_phone = request.user.phone

        form = AppointmentForm(
            initial={
                "customer_name": customer_name,
                "customer_phone": customer_phone,
            }
        )

    # ─── context ───
    context = {
        "business": business,
        "is_salon": business.is_salon,
        "stations": stations,
        "selected_station": selected_station,
        "services": services,
        "selected_service": selected_service,
        "staff_members": staff_members,
        "selected_staff": selected_staff,
        "selected_date": selected_date,
        "has_date_param": has_date_param,
        "slots": slots,
        "form": form,
        "today": timezone.localdate(),
    }

    return render(request, "booking/book.html", context)


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════


def _parse_date(date_str: str | None):
    """تاریخ از query یا امروز."""
    from datetime import datetime

    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    return timezone.localdate()