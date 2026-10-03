"""
Views اپ core.

شامل:
- home (بسته به نقش کاربر)
- error handlers
- health check
"""

import logging
import sys

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Home
# ═══════════════════════════════════════════════════════════════


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    """
    صفحه‌ی اصلی.

    بسته به وضعیت کاربر:
    - مهمان → guest_home
    - مشتری → customer_home
    - صاحب کسب‌وکار → redirect به /business/dashboard/
    - ادمین → redirect به /admin/
    """
    user = request.user

    # ─── ادمین پلتفرم ───
    if user.is_authenticated and user.is_platform_admin:
        return redirect("/admin/")

    # ─── صاحب کسب‌وکار ───
    if user.is_authenticated and user.is_business_owner:
        return redirect("business:dashboard")

    # ─── مشتری ───
    if user.is_authenticated and user.is_customer:
        return render(request, "core/customer_home.html")

    # ─── مهمان ───
    return render(request, "core/guest_home.html")


# ═══════════════════════════════════════════════════════════════
#  About
# ═══════════════════════════════════════════════════════════════


@require_GET
def about(request: HttpRequest) -> HttpResponse:
    """صفحه‌ی درباره ما."""
    return render(request, "core/about.html")


# ═══════════════════════════════════════════════════════════════
#  Health Check
# ═══════════════════════════════════════════════════════════════


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """بررسی سلامت سرویس."""
    from django.db import connection

    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    return JsonResponse(
        {
            "status": "ok" if db_ok else "degraded",
            "database": db_ok,
        },
        status=200 if db_ok else 503,
    )


# ═══════════════════════════════════════════════════════════════
#  Offline
# ═══════════════════════════════════════════════════════════════


@require_GET
def offline_view(request: HttpRequest) -> HttpResponse:
    """صفحه‌ی offline (برای PWA)."""
    return render(request, "offline.html")


# ═══════════════════════════════════════════════════════════════
#  Error Handlers
# ═══════════════════════════════════════════════════════════════


def error_400(request: HttpRequest, exception=None) -> HttpResponse:
    """صفحه‌ی خطای 400."""
    return render(request, "errors/400.html", status=400)


def error_403(request: HttpRequest, exception=None) -> HttpResponse:
    """صفحه‌ی خطای 403."""
    return render(request, "errors/403.html", status=403)


def error_404(request: HttpRequest, exception=None) -> HttpResponse:
    """صفحه‌ی خطای 404."""
    return render(request, "errors/404.html", status=404)


def error_500(request: HttpRequest) -> HttpResponse:
    """صفحه‌ی خطای 500."""
    # ─── exception فعلی رو از sys.exc_info بگیر ───
    exc_info = sys.exc_info()
    if exc_info and exc_info[0] is not None:
        logger.error("Internal server error", exc_info=exc_info)
    else:
        logger.error("Internal server error (no exception info)")

    return render(request, "errors/500.html", status=500)


def csrf_failure(
    request: HttpRequest,
    reason: str = "",
    template_name: str = "errors/csrf_failure.html",
) -> HttpResponse:
    """صفحه‌ی خطای CSRF."""
    logger.warning(f"CSRF failure: {reason}")
    return render(
        request,
        template_name,
        {"reason": reason},
        status=403,
    )