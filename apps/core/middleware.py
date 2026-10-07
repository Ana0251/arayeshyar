from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalHostRedirectMiddleware:
    """در production همه درخواست‌ها را به هاست canonical منتقل می‌کند.

    نمونه:
        arayesh-yar.ir/foo?x=1 -> https://www.arayesh-yar.ir/foo?x=1

    در DEBUG غیرفعال است تا localhost دست‌نخورده بماند.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            canonical_host = (getattr(settings, "CANONICAL_HOST", "") or "").strip().lower()
            if not canonical_host:
                site_domain = (getattr(settings, "SITE_DOMAIN", "") or "").strip()
                canonical_host = (urlsplit(site_domain).netloc or site_domain).split(":")[0].lower()

            current_host = request.get_host().split(":")[0].lower()
            if canonical_host and current_host != canonical_host:
                target = f"https://{canonical_host}{request.get_full_path()}"
                return HttpResponsePermanentRedirect(target)

        return self.get_response(request)


class PrivatePagesNoIndexMiddleware:
    """به موتور جستجو می‌گوید صفحات حساب/مدیریت را ایندکس نکند."""
    PRIVATE_PREFIXES=(
        "/admin/","/control/","/auth/","/business/","/support/",
        "/my-","/waiting/",
    )
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        response=self.get_response(request)
        if request.path.startswith(self.PRIVATE_PREFIXES) or "/book/" in request.path or request.path.endswith("/qr/"):
            response["X-Robots-Tag"]="noindex, nofollow"
        return response
