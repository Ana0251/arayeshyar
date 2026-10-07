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
    """صفحه‌ی اصلی + جست‌وجوی سریع آرایشگر/سالن با شماره موبایل."""
    user = request.user

    if user.is_authenticated and user.is_platform_admin:
        return redirect("control:dashboard")

    if user.is_authenticated and user.is_business_owner:
        return redirect("business:dashboard")

    # جست‌وجوی شماره عمداً Exact Match است؛ نتیجه با نام/منطقه لو نمی‌رود.
    query = (request.GET.get("q") or "").strip()
    search_result = None
    search_error = ""
    search_is_saved = False

    if query:
        from apps.business.models import Business
        from apps.core.utils.phone import normalize_phone

        phone = normalize_phone(query)
        if not phone:
            search_error = "شماره موبایل معتبر وارد کن؛ مثلاً 09123456789"
        else:
            search_result = (
                Business.objects.filter(
                    owner__phone=phone,
                    is_active=True,
                    is_rejected=False,
                )
                .select_related("activity_type", "owner")
                .first()
            )
            if not search_result:
                search_error = "آرایشگر یا سالن فعالی با این شماره پیدا نشد."
            elif user.is_authenticated and user.is_customer:
                from apps.customers.models import CustomerBusiness

                search_is_saved = CustomerBusiness.objects.filter(
                    customer=user,
                    business=search_result,
                ).exists()

    common_context = {
        "query": query,
        "search_result": search_result,
        "search_error": search_error,
        "search_is_saved": search_is_saved,
    }

    if user.is_authenticated and user.is_customer:
        from apps.customers.selectors import get_customer_businesses

        my_businesses = list(get_customer_businesses(user)[:4])
        return render(
            request,
            "core/customer_home.html",
            {**common_context, "my_businesses": my_businesses},
        )

    return render(request, "core/guest_home.html", common_context)


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
@require_GET
def robots_txt(request: HttpRequest) -> HttpResponse:
    sitemap=request.build_absolute_uri("/sitemap.xml")
    body=("User-agent: *\n"
          "Allow: /\n"
          "Disallow: /admin/\nDisallow: /control/\nDisallow: /business/\nDisallow: /auth/\n"
          "Disallow: /support/my-tickets/\nDisallow: /my-appointments/\n"
          f"Sitemap: {sitemap}\n")
    return HttpResponse(body,content_type="text/plain; charset=utf-8")

@require_GET
def sitemap_xml(request: HttpRequest) -> HttpResponse:
    from django.urls import reverse
    from django.utils import timezone
    from django.utils.html import escape
    from apps.business.models import Business
    from apps.blog.models import BlogPost
    items=[]
    for name,priority,freq in [("core:home","1.0","daily"),("blog:list","0.8","daily"),("core:about","0.5","monthly")]:
        items.append((request.build_absolute_uri(reverse(name)),None,freq,priority))
    for b in Business.objects.filter(is_active=True,is_rejected=False).only("slug","updated_at"):
        items.append((request.build_absolute_uri(reverse("business:public_profile",kwargs={"slug":b.slug})),b.updated_at,"weekly","0.9"))
    for p in BlogPost.objects.filter(status="published",published_at__lte=timezone.now()).only("slug","updated_at"):
        items.append((request.build_absolute_uri(p.get_absolute_url()),p.updated_at,"monthly","0.8"))
    rows=[]
    for loc,lastmod,freq,priority in items:
        lm=f"<lastmod>{lastmod.date().isoformat()}</lastmod>" if lastmod else ""
        rows.append(f"<url><loc>{escape(loc)}</loc>{lm}<changefreq>{freq}</changefreq><priority>{priority}</priority></url>")
    xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(rows)+"</urlset>"
    return HttpResponse(xml,content_type="application/xml; charset=utf-8")
