"""
URL configuration پروژه آرایشیار.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, JsonResponse
from django.urls import include, path, register_converter, re_path

from apps.core.converters import UnicodeSlugConverter

register_converter(UnicodeSlugConverter, "uslug")


# ═══════════════════════════════════════════════════════════════
#  Views برای PWA
# ═══════════════════════════════════════════════════════════════


def empty_events_json(request):
    return JsonResponse([], safe=False)


def manifest_view(request):
    path = settings.BASE_DIR / "static" / "manifest.webmanifest"
    return FileResponse(
        open(path, "rb"),
        content_type="application/manifest+json",
    )


def service_worker_view(request):
    path = settings.BASE_DIR / "static" / "sw.js"
    response = FileResponse(
        open(path, "rb"),
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    return response


# ═══════════════════════════════════════════════════════════════
#  URL Patterns
# ═══════════════════════════════════════════════════════════════

urlpatterns = [
    path("control/", include("apps.core.control_urls")),
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.business.urls")),
    path("", include("apps.booking.urls")),
    path("", include("apps.customers.urls")),
    path("", include("apps.support.urls")),
    path("", include("apps.blog.urls")),

    path("manifest.webmanifest", manifest_view, name="manifest"),
    path("sw.js", service_worker_view, name="sw"),

    re_path(
        r"^.*data/events\.json$",
        empty_events_json,
        name="empty_events_catchall",
    ),
]


handler400 = "apps.core.views.error_400"
handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]