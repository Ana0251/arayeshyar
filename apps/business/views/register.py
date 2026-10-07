"""
Views ثبت‌نام کسب‌وکار.

─── جریان: ───
1.  register_start         → شروع (پاک کردن session قبلی)
2.  register_audience      → مرحله ۱: انتخاب مخاطب
3.  register_salon_type    → مرحله ۲: سالن یا شخصی
4.  register_activity      → مرحله ۳: نوع فعالیت
5.  register_stations      → مرحله ۴-الف: ایستگاه‌ها (سالن)
6.  register_services      → مرحله ۴-ب: خدمات (شخصی)
7.  register_business_info → مرحله ۵: اطلاعات پایه
8.  register_done          → پایان

─── نکته امنیتی: ───
کاربر باید لاگین باشه و نقشش customer باشه (نه business_owner).
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from ..forms import (
    RegisterActivityForm,
    RegisterAudienceForm,
    RegisterBusinessInfoForm,
    RegisterSalonTypeForm,
)
from ..models import ActivityType, TargetAudience
from ..services import RegisterService

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Guards
# ═══════════════════════════════════════════════════════════════


def _ensure_not_already_business(request: HttpRequest) -> HttpResponse | None:
    """اگه کاربر صاحب کسب‌وکاره، redirectش کن."""
    if hasattr(request.user, "business"):
        messages.info(request, _("شما قبلاً کسب‌وکار ثبت کردی."))
        return redirect("business:dashboard")
    return None


def _ensure_session(request: HttpRequest, *keys: str) -> HttpResponse | None:
    """چک می‌کنه این کلیدها توی session هستن."""
    for key in keys:
        if key not in request.session:
            messages.warning(
                request,
                _("لطفاً از مرحله‌ی اول شروع کن."),
            )
            return redirect("business:register_start")
    return None


# ═══════════════════════════════════════════════════════════════
#  Step 0 — Start
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET"])
def register_start(request: HttpRequest) -> HttpResponse:
    """
    شروع ثبت‌نام.

    ─── کار: ───
    1. چک کاربر صاحب کسب‌وکار نباشه
    2. پاک کردن session قبلی
    3. redirect به مرحله ۱
    """
    # ─── چک ───
    guard = _ensure_not_already_business(request)
    if guard:
        return guard

    # ─── پاک کردن session ───
    RegisterService(request).clear_session()

    return redirect("business:register_audience")


# ═══════════════════════════════════════════════════════════════
#  Step 1 — Audience
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET", "POST"])
def register_audience(request: HttpRequest) -> HttpResponse:
    """مرحله ۱: انتخاب مخاطب."""
    guard = _ensure_not_already_business(request)
    if guard:
        return guard

    if request.method == "POST":
        form = RegisterAudienceForm(request.POST)

        if form.is_valid():
            audience_id = form.cleaned_data["audience_id"]
            audience = get_object_or_404(
                TargetAudience,
                id=audience_id,
                is_active=True,
            )

            RegisterService(request).set("reg_audience", audience.id)
            return redirect("business:register_salon_type")
    else:
        form = RegisterAudienceForm()

    audiences = TargetAudience.objects.filter(is_active=True).order_by("order")

    return render(
        request,
        "business/register/audience.html",
        {
            "audiences": audiences,
            "form": form,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Step 2 — Salon Type
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET", "POST"])
def register_salon_type(request: HttpRequest) -> HttpResponse:
    """مرحله ۲: سالن داری یا شخصی؟"""
    guard = _ensure_not_already_business(request)
    if guard:
        return guard

    session_guard = _ensure_session(request, "reg_audience")
    if session_guard:
        return session_guard

    if request.method == "POST":
        form = RegisterSalonTypeForm(request.POST)
        if form.is_valid():
            is_salon = form.cleaned_data["is_salon"]
            RegisterService(request).set("reg_is_salon", is_salon)
            return redirect("business:register_activity")
    else:
        form = RegisterSalonTypeForm()

    return render(request, "business/register/salon_type.html", {"form": form})


# ═══════════════════════════════════════════════════════════════
#  Step 3 — Activity
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET", "POST"])
def register_activity(request: HttpRequest) -> HttpResponse:
    """مرحله ۳: نوع فعالیت."""
    guard = _ensure_not_already_business(request)
    if guard:
        return guard

    session_guard = _ensure_session(request, "reg_audience", "reg_is_salon")
    if session_guard:
        return session_guard

    is_salon = bool(request.session.get("reg_is_salon", False))

    if request.method == "POST":
        form = RegisterActivityForm(request.POST)

        if form.is_valid():
            activity_id = form.cleaned_data.get("activity_id")
            other_activity = (
                form.cleaned_data.get("other_activity") or ""
            ).strip()

            service = RegisterService(request)

            if activity_id:
                activity = get_object_or_404(
                    ActivityType,
                    id=activity_id,
                    is_active=True,
                )
                service.set("reg_activity", activity.id)
                service.set("reg_custom_activity", "")
            else:
                service.set("reg_activity", None)
                service.set("reg_custom_activity", other_activity)

            # ─── بر اساس is_salon ───
            if is_salon:
                return redirect("business:register_stations")
            return redirect("business:register_services")
    else:
        form = RegisterActivityForm()

    activities = ActivityType.objects.filter(
        is_active=True,
        is_salon=is_salon,
    ).order_by("order")

    return render(
        request,
        "business/register/activity.html",
        {
            "activities": activities,
            "is_salon": is_salon,
            "form": form,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Step 4-A — Stations (سالن)
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET", "POST"])
def register_stations(request: HttpRequest) -> HttpResponse:
    """مرحله ۴-الف: ایستگاه‌ها (برای سالن‌ها)."""
    guard = _ensure_not_already_business(request)
    if guard:
        return guard

    session_guard = _ensure_session(
        request,
        "reg_audience",
        "reg_is_salon",
    )
    if session_guard:
        return session_guard

    # ─── چک: باید سالن باشه ───
    if not request.session.get("reg_is_salon"):
        return redirect("business:register_services")

    # ─── چک activity ───
    has_activity = bool(
        request.session.get("reg_activity")
        or request.session.get("reg_custom_activity")
    )
    if not has_activity:
        return redirect("business:register_activity")

    if request.method == "POST":
        stations = []
        names = request.POST.getlist("station_name[]")
        staffs = request.POST.getlist("station_staff[]")

        for idx, name in enumerate(names):
            name = (name or "").strip()
            if not name:
                continue
            stations.append(
                {
                    "name": name,
                    "staff": (staffs[idx] if idx < len(staffs) else "").strip(),
                }
            )

        RegisterService(request).set("reg_stations", stations)
        return redirect("business:register_info")

    return render(
        request,
        "business/register/stations.html",
    )


# ═══════════════════════════════════════════════════════════════
#  Step 4-B — Services (شخصی)
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET", "POST"])
def register_services(request: HttpRequest) -> HttpResponse:
    """مرحله ۴-ب: خدمات (برای کسب‌وکار شخصی)."""
    guard = _ensure_not_already_business(request)
    if guard:
        return guard

    session_guard = _ensure_session(
        request,
        "reg_audience",
        "reg_is_salon",
    )
    if session_guard:
        return session_guard

    # ─── چک activity ───
    has_activity = bool(
        request.session.get("reg_activity")
        or request.session.get("reg_custom_activity")
    )
    if not has_activity:
        return redirect("business:register_activity")

    if request.method == "POST":
        services = []
        names = request.POST.getlist("service_name[]")
        durations = request.POST.getlist("service_duration[]")
        prices = request.POST.getlist("service_price[]")

        for idx, name in enumerate(names):
            name = (name or "").strip()
            if not name:
                continue

            try:
                duration = int(
                    durations[idx] if idx < len(durations) else 30
                )
            except (ValueError, IndexError):
                duration = 30

            try:
                price = int(prices[idx] if idx < len(prices) else 0)
            except (ValueError, IndexError):
                price = 0

            services.append(
                {
                    "name": name,
                    "duration": duration,
                    "price": price,
                }
            )

        RegisterService(request).set("reg_services", services)
        return redirect("business:register_info")

    return render(
        request,
        "business/register/services.html",
    )


# ═══════════════════════════════════════════════════════════════
#  Step 5 — Business Info
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET", "POST"])
def register_business_info(request: HttpRequest) -> HttpResponse:
    """مرحله ۵: اطلاعات پایه کسب‌وکار."""
    guard = _ensure_not_already_business(request)
    if guard:
        return guard

    session_guard = _ensure_session(
        request,
        "reg_audience",
        "reg_is_salon",
    )
    if session_guard:
        return session_guard

    has_activity = bool(
        request.session.get("reg_activity")
        or request.session.get("reg_custom_activity")
    )
    if not has_activity:
        return redirect("business:register_activity")

    is_salon = bool(request.session.get("reg_is_salon", False))

    if request.method == "POST":
        form = RegisterBusinessInfoForm(
            request.POST,
            request.FILES,
            is_salon=is_salon,
            user=request.user,
        )

        if form.is_valid():
            # ─── جمع آوری داده ───
            info_data = {
                "name": form.cleaned_data["name"],
                "owner_name": form.cleaned_data.get("owner_name", ""),
                "owner_phone": form.cleaned_data["owner_phone"],
                "landline": form.cleaned_data.get("landline", ""),
                "region": form.cleaned_data["region"],
                "address": form.cleaned_data["address"],
                "bio": form.cleaned_data.get("bio", ""),
            }

            files = {}
            for f in ["avatar", "business_license", "entrance_photo"]:
                if request.FILES.get(f):
                    files[f] = request.FILES[f]

            # ─── ساخت Business ───
            try:
                service = RegisterService(request)
                business = service.finalize(
                    info_data=info_data,
                    files=files,
                )

                messages.success(
                    request,
                    _(
                        "درخواستت ثبت شد! 🎉 "
                        "بعد از تأیید مدیر، پروفایلت فعال میشه."
                    ),
                )
                return redirect("business:register_done")

            except Exception as exc:
                logger.exception(f"Register finalize failed: {exc}")
                messages.error(
                    request,
                    _("خطا در ثبت اطلاعات. لطفاً دوباره امتحان کن."),
                )
    else:
        form = RegisterBusinessInfoForm(is_salon=is_salon, user=request.user)

    return render(
        request,
        "business/register/info.html",
        {
            "form": form,
            "is_salon": is_salon,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Step 6 — Done
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET"])
def register_done(request: HttpRequest) -> HttpResponse:
    """پایان ثبت‌نام."""
    # ─── چک: کاربر باید Business داشته باشه ───
    business = getattr(request.user, "business", None)
    if not business:
        messages.warning(request, _("ابتدا ثبت‌نام کن."))
        return redirect("business:register_start")

    return render(
        request,
        "business/register/done.html",
        {"business": business},
    )