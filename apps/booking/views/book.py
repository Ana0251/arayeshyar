"""
Views رزرو نوبت (عمومی).
"""

import logging

from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from urllib.parse import urlencode

from apps.core.utils.dates import jalali_date_and_time
from apps.core.utils.requests import get_client_ip
from apps.accounts.constants import Role
from apps.accounts.models import CustomerProfile, User
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

CUSTOMER_SESSION_AGE_SECONDS = 60 * 60 * 24 * 30


# ═══════════════════════════════════════════════════════════════
#  Book Appointment
# ═══════════════════════════════════════════════════════════════


@require_http_methods(["GET", "POST"])
def book_appointment(request: HttpRequest, slug: str) -> HttpResponse:
    """صفحه رزرو نوبت."""
    business = get_object_or_404(
        Business.objects.active(),
        slug=slug,
    )

    # ─── اگه کسب‌وکار خودشه، اجازه نده ───
    if request.user.is_authenticated and hasattr(request.user, "business") and request.user.business == business:
        messages.warning(request, _("نمی‌تونی برای کسب‌وکار خودت نوبت بگیری."))
        return redirect("business:dashboard")

    # ─── مشتری لاگین‌شده اگر بلاک شده باشد ───
    if request.user.is_authenticated and request.user.phone and BlockedCustomer.objects.is_blocked(business, request.user.phone):
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
    form = AppointmentForm(
        request.POST,
        require_account=not request.user.is_authenticated,
        require_identity=request.user.is_authenticated,
    )

    if not form.is_valid():
        error_message = _("لطفاً خطاها رو برطرف کن.")
        if not _is_htmx(request):
            messages.error(request, error_message)
        return _render_booking_page(
            request, business, form=form, booking_message=error_message
        )

    # مهمان فقط در انتهای رزرو احراز هویت می‌شود.
    if not request.user.is_authenticated:
        return _start_guest_booking_auth(request, business, form)

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

        # ─── ذخیره‌ی اطلاعات مشتری ───
        customer = request.user
        new_name = (data.get("customer_name") or "").strip()
        new_phone = data.get("customer_phone")

        if customer.is_customer:
            if new_phone and customer.phone != new_phone:
                phone_owner = User.objects.filter(phone=new_phone).exclude(pk=customer.pk).first()
                if phone_owner:
                    raise BookingError("این شماره موبایل قبلاً به حساب دیگری متصل شده.")
                customer.phone = new_phone
                customer.save(update_fields=["phone"])

            profile = getattr(customer, "customer_profile", None)
            if new_name and profile and profile.full_name != new_name:
                profile.full_name = new_name
                profile.save(update_fields=["full_name", "updated_at"])

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
                    "date": jalali_date_and_time(appointment.start_at)[0],
                    "time": jalali_date_and_time(appointment.start_at)[1],
                },
            )
        else:
            messages.success(
                request,
                _("نوبتت ثبت شد و در انتظار تأیید. ⏳"),
            )

        if _is_htmx(request):
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse("booking:my_appointments")
            return response

        return redirect("booking:my_appointments")

    except SlotNotAvailableError:
        error_message = _("این ساعت در دسترس نیست. لطفاً یه ساعت دیگه انتخاب کن.")
        if not _is_htmx(request):
            messages.error(request, error_message)
        return _render_booking_page(
            request, business, form=form, booking_message=error_message
        )

    except BookingError as exc:
        # ValidationError.__str__ پیام را به شکل ['...'] نمایش می‌دهد.
        # برای UX، فقط متن واقعی اولین پیام را نشان می‌دهیم.
        error_message = _booking_error_message(exc)
        if not _is_htmx(request):
            messages.error(request, error_message)
        return _render_booking_page(
            request, business, form=form, booking_message=error_message
        )

    except Exception:
        logger.exception("Booking failed")
        error_message = _("خطا در ثبت نوبت. لطفاً دوباره امتحان کن.")
        if not _is_htmx(request):
            messages.error(request, error_message)
        return _render_booking_page(
            request, business, form=form, booking_message=error_message
        )


# ═══════════════════════════════════════════════════════════════
#  GET Handler
# ═══════════════════════════════════════════════════════════════


def _render_booking_page(
    request: HttpRequest,
    business: Business,
    form: AppointmentForm | None = None,
    booking_message: str | None = None,
) -> HttpResponse:
    """رندر صفحه‌ی رزرو."""
    # ─── پارامترهای GET ───
    selected_station_id = request.GET.get("station")
    selected_service_id = request.GET.get("service")
    selected_staff_id = request.GET.get("staff")
    selected_date_str = request.GET.get("date")

    # در POSTهای HTMX پارامترهای انتخاب از hidden inputها میان، نه query string.
    # این fallback باعث میشه در صورت خطای اعتبارسنجی انتخاب‌های کاربر نپرن.
    if request.method == "POST":
        selected_service_id = selected_service_id or request.POST.get("service_id")
        selected_staff_id = selected_staff_id or request.POST.get("staff_id")
        if not selected_date_str:
            start_at_raw = request.POST.get("start_at", "")
            if "T" in start_at_raw:
                selected_date_str = start_at_raw.split("T", 1)[0]

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

    # خدمت مرجع نهایی اتاق است؛ اجازه نمی‌دیم station و service ناسازگار باشند.
    if business.is_salon and selected_service:
        selected_station = selected_service.station
        selected_station_id = selected_station.id if selected_station else None
        services = list(
            business.services.filter(
                is_active=True, station=selected_station
            )
            .select_related("station")
            .order_by("order", "name")
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
            eligible_staff_ids=(
                [staff.id for staff in staff_members]
                if business.is_salon and selected_staff is None
                else None
            ),
        )
        slots = availability.get_all_slots_with_status(duration=duration)

    # ─── فرم ───
    if form is None:
        customer_name = request.user.display_name if request.user.is_authenticated else ""
        customer_phone = request.user.phone if request.user.is_authenticated else ""
        customer_email = request.user.email if request.user.is_authenticated else ""

        form = AppointmentForm(
            require_account=not request.user.is_authenticated,
            require_identity=request.user.is_authenticated,
            initial={
                "customer_email": customer_email,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
            },
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
        "booking_message": booking_message,
    }

    # انتخاب تاریخ فقط بخش ساعت‌ها/فرم نهایی را به‌روز می‌کند.
    # این کار از destroy/re-init شدن DatePicker و state صفحه جلوگیری می‌کند.
    if _is_htmx(request) and request.GET.get("slots_only") == "1":
        return render(
            request,
            "booking/partials/_booking_date_results.html",
            context,
        )

    template_name = (
        "booking/partials/_booking_flow.html"
        if _is_htmx(request)
        else "booking/book.html"
    )
    return render(request, template_name, context)


# ═══════════════════════════════════════════════════════════════
#  Guest booking authentication
# ═══════════════════════════════════════════════════════════════


def _start_guest_booking_auth(request: HttpRequest, business: Business, form: AppointmentForm) -> HttpResponse:
    """در انتهای رزرو با موبایل+رمز وارد می‌کند یا همان‌جا حساب مشتری می‌سازد."""
    data = form.cleaned_data
    phone = data["customer_phone"]
    password = data["customer_password"]
    full_name = (data.get("customer_name") or "").strip()
    email = (data.get("customer_email") or "").strip().lower() or None

    if BlockedCustomer.objects.is_blocked(business, phone):
        form.add_error("customer_phone", _("امکان رزرو برای این شماره موبایل وجود نداره."))
        return _render_booking_page(request, business, form=form, booking_message=_("امکان رزرو با این شماره وجود نداره."))

    user = User.objects.filter(phone=phone).first()
    created = False

    if user:
        if user.role != Role.CUSTOMER:
            form.add_error("customer_phone", _("این شماره مربوط به حساب کسب‌وکار یا مدیریت است."))
            return _render_booking_page(request, business, form=form, booking_message=_("برای رزرو از حساب مشتری استفاده کن."))
        if not user.is_active:
            form.add_error("customer_phone", _("این حساب غیرفعاله."))
            return _render_booking_page(request, business, form=form, booking_message=_("حساب غیرفعاله."))
        if not user.check_password(password):
            form.add_error("customer_password", _("رمز عبور اشتباهه."))
            return _render_booking_page(request, business, form=form, booking_message=_("شماره موبایل یا رمز عبور درست نیست."))
    else:
        if email and User.objects.filter(email__iexact=email).exists():
            form.add_error("customer_email", _("این ایمیل قبلاً به حساب دیگری متصل شده."))
            return _render_booking_page(request, business, form=form, booking_message=_("ایمیل تکراریه."))
        user = User.objects.create_user(
            phone=phone, password=password, email=email, role=Role.CUSTOMER, is_active=True
        )
        created = True

    profile, profile_created = CustomerProfile.objects.get_or_create(user=user)
    if full_name and profile.full_name != full_name:
        profile.full_name = full_name
        profile.save(update_fields=["full_name", "updated_at"])
    if email and user.email != email:
        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            form.add_error("customer_email", _("این ایمیل قبلاً به حساب دیگری متصل شده."))
            return _render_booking_page(request, business, form=form, booking_message=_("ایمیل تکراریه."))
        user.email = email
        user.save(update_fields=["email"])

    user.last_login_ip = get_client_ip(request)
    user.save(update_fields=["last_login_ip"])
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.set_expiry(CUSTOMER_SESSION_AGE_SECONDS)

    pending = {
        "business_slug": business.slug,
        "service_id": data["service_id"],
        "staff_id": data.get("staff_id") or None,
        "start_at": data["start_at"].isoformat(),
        "customer_note": data.get("customer_note", ""),
    }
    if created:
        messages.success(request, _("حسابت ساخته شد و وارد شدی. ✅"))
    return _finalize_pending_guest_booking(request, business, user, pending)


def _finalize_pending_guest_booking(request, business, customer, pending):
    """بعد از احراز هویت، همان رزرو انتخاب‌شده را نهایی می‌کند."""
    start_at = _pending_start_at(pending)
    service = get_object_or_404(
        Service, id=pending["service_id"], business=business, is_active=True
    )
    staff = None
    if pending.get("staff_id"):
        staff = Staff.objects.filter(
            id=pending["staff_id"], business=business, is_active=True
        ).first()

    try:
        appointment = BookingService(business).create_appointment(
            customer=customer,
            service=service,
            start_at=start_at,
            staff=staff,
            customer_note=pending.get("customer_note", ""),
        )
        CustomerBusinessService.add_to_my_list(customer, business)

        date_text, time_text = jalali_date_and_time(appointment.start_at)
        if appointment.is_confirmed:
            messages.success(request, _("نوبتت تأیید شد! ✅ %(date)s ساعت %(time)s") % {
                "date": date_text, "time": time_text,
            })
        else:
            messages.success(request, _("نوبتت ثبت شد و در انتظار تأیید. ⏳"))
        return redirect("booking:my_appointments")

    except SlotNotAvailableError:
        messages.error(request, _("این ساعت در فاصله ثبت نوبت پر شد. لطفاً یک ساعت دیگه انتخاب کن."))
    except BookingError as exc:
        messages.error(request, _booking_error_message(exc))

    query = {
        "service": pending["service_id"],
        "date": start_at.date().isoformat() if start_at else "",
    }
    if service.station_id:
        query["station"] = service.station_id
    if pending.get("staff_id"):
        query["staff"] = pending["staff_id"]
    return redirect(f'{reverse("booking:book", kwargs={"slug": business.slug})}?{urlencode(query)}')


def _customer_identity_complete(user) -> bool:
    profile = getattr(user, "customer_profile", None)
    return bool(user.phone and profile and (profile.full_name or "").strip())


def _pending_start_at(pending):
    value = parse_datetime(pending.get("start_at", ""))
    if value and timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return value


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════


def _booking_error_message(exc: BookingError) -> str:
    """پیام ValidationError را بدون نمایش براکت/لیست برای کاربر برمی‌گرداند."""
    messages_list = getattr(exc, "messages", None)
    if messages_list:
        return str(messages_list[0])

    message = getattr(exc, "message", None)
    if message:
        return str(message)

    return str(exc).strip("[]'\"")


def _parse_date(date_str: str | None):
    """تاریخ از query یا امروز."""
    from datetime import datetime

    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    return timezone.localdate()

def _is_htmx(request: HttpRequest) -> bool:
    """آیا درخواست از HTMX اومده؟"""
    return request.headers.get("HX-Request", "").lower() == "true"
