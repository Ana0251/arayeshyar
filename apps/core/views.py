"""
Views اپ core.
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
    """صفحه‌ی اصلی."""
    user = request.user

    if user.is_authenticated and user.is_platform_admin:
        return redirect("/admin/")

    if user.is_authenticated and user.is_business_owner:
        return redirect("business:dashboard")

    if user.is_authenticated and user.is_customer:
        from apps.customers.selectors import get_customer_businesses

        my_businesses = list(get_customer_businesses(user)[:4])

        return render(
            request,
            "core/customer_home.html",
            {"my_businesses": my_businesses},
        )

    return render(request, "core/guest_home.html")


# ═══════════════════════════════════════════════════════════════
#  About
# ═══════════════════════════════════════════════════════════════


@require_GET
def about(request: HttpRequest) -> HttpResponse:
    return render(request, "core/about.html")


# ═══════════════════════════════════════════════════════════════
#  Health Check
# ═══════════════════════════════════════════════════════════════


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    from django.db import connection

    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    return JsonResponse(
        {"status": "ok" if db_ok else "degraded", "database": db_ok},
        status=200 if db_ok else 503,
    )


# ═══════════════════════════════════════════════════════════════
#  Offline
# ═══════════════════════════════════════════════════════════════


@require_GET
def offline_view(request: HttpRequest) -> HttpResponse:
    return render(request, "offline.html")


# ═══════════════════════════════════════════════════════════════
#  Error Handlers
# ═══════════════════════════════════════════════════════════════


def error_400(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, "errors/400.html", status=400)


def error_403(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, "errors/403.html", status=403)


def error_404(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, "errors/404.html", status=404)


def error_500(request: HttpRequest) -> HttpResponse:
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
    logger.warning(f"CSRF failure: {reason}")
    return render(
        request,
        template_name,
        {"reason": reason},
        status=403,
    )