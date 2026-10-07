"""
Decorator های مشترک پروژه.

شامل:
- business_required     → فقط صاحب کسب‌وکار
- customer_required     → فقط مشتری
- active_business_required → کسب‌وکار باید تأیید شده باشه
- ajax_required         → فقط درخواست‌های AJAX/HTMX
- htmx_required         → فقط درخواست‌های HTMX
"""

from functools import wraps
from typing import Any, Callable

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


# ═══════════════════════════════════════════════════════════════
#  Business & Customer
# ═══════════════════════════════════════════════════════════════


def business_required(view_func: Callable) -> Callable:
    """
    فقط صاحب کسب‌وکار.

    ─── چک‌ها: ───
    1. کاربر لاگین باشه
    2. کاربر نقش business_owner داشته باشه
    3. کاربر یه Business داشته باشه

    ─── استفاده: ───
        @business_required
        def dashboard(request):
            business = request.user.business  # ← امن
    """

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # ─── لاگین؟ ───
        if not request.user.is_authenticated:
            messages.warning(
                request,
                _("برای دسترسی به این صفحه باید وارد بشی."),
            )
            login_url = f"/auth/login/?next={request.path}"
            return redirect(login_url)

        # ─── نقش؟ ───
        if not request.user.is_business_owner:
            messages.error(
                request,
                _("این صفحه مخصوص صاحبان کسب‌وکاره."),
            )
            return redirect("core:home")

        # ─── Business داره؟ ───
        if not hasattr(request.user, "business"):
            messages.error(
                request,
                _("هنوز کسب‌وکاری ثبت نکردی."),
            )
            return redirect("core:home")

        return view_func(request, *args, **kwargs)

    return wrapper


def customer_required(view_func: Callable) -> Callable:
    """
    فقط مشتری.

    ─── چک‌ها: ───
    1. کاربر لاگین باشه
    2. کاربر نقش customer داشته باشه
    """

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            messages.warning(
                request,
                _("برای دسترسی به این صفحه باید وارد بشی."),
            )
            login_url = f"/auth/login/?next={request.path}"
            return redirect(login_url)

        if not request.user.is_customer:
            messages.error(
                request,
                _("این صفحه مخصوص مشتری‌هاست."),
            )
            return redirect("core:home")

        return view_func(request, *args, **kwargs)

    return wrapper


def active_business_required(view_func: Callable) -> Callable:
    """
    کسب‌وکار باید تأیید شده باشه (is_active=True).

    ─── استفاده: ───
    برای view هایی که قبل از تأیید نباید کار کنن
    (مثل لینک عمومی، QR، دریافت نوبت).
    """

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        business = getattr(request.user, "business", None)
        if not business:
            messages.error(request, _("کسب‌وکاری پیدا نشد."))
            return redirect("core:home")

        if not business.is_active:
            messages.warning(
                request,
                _("کسب‌وکارت هنوز تأیید نشده. لطفاً منتظر بمون."),
            )
            return redirect("business:dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


# ═══════════════════════════════════════════════════════════════
#  AJAX / HTMX
# ═══════════════════════════════════════════════════════════════


def ajax_required(view_func: Callable) -> Callable:
    """فقط درخواست‌های AJAX."""

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"error": _("این endpoint فقط برای AJAX هست.")},
                status=400,
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def htmx_required(view_func: Callable) -> Callable:
    """فقط درخواست‌های HTMX."""

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.headers.get("HX-Request"):
            return HttpResponse(
                _("این endpoint فقط برای HTMX هست."),
                status=400,
            )
        return view_func(request, *args, **kwargs)

    return wrapper