"""
Helper های مشترک views business.

برای جلوگیری از تکرار کد در views مختلف.
"""

from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from ..models import Business


# ═══════════════════════════════════════════════════════════════
#  HTMX Helper
# ═══════════════════════════════════════════════════════════════


def is_htmx(request: HttpRequest) -> bool:
    """آیا درخواست HTMX هست؟"""
    return bool(request.headers.get("HX-Request"))


def htmx_response(
    request: HttpRequest,
    *,
    template: str,
    context: dict[str, Any] | None = None,
    status: int = 200,
) -> HttpResponse:
    """Render یه partial HTMX."""
    return render(
        request,
        template,
        context or {},
        status=status,
    )


def htmx_error(
    request: HttpRequest,
    message: str,
    *,
    status: int = 400,
) -> HttpResponse:
    """
    پاسخ خطای HTMX (به‌صورت toast قرمز).

    ─── نکته: ───
    این HTML رو HTMX جایگزین target می‌کنه.
    """
    if not is_htmx(request):
        messages.error(request, message)

    return HttpResponse(
        f'<div class="bg-danger/10 border border-danger/30 text-danger '
        f'text-sm rounded-xl p-3">⚠️ {message}</div>',
        status=status,
    )


def htmx_success_message(
    message: str,
    *,
    status: int = 200,
) -> HttpResponse:
    """پاسخ موفق HTMX (فقط یه پیام)."""
    return HttpResponse(
        f'<div class="bg-success/10 border border-success/30 text-success '
        f'text-sm rounded-xl p-3">✅ {message}</div>',
        status=status,
    )


# ═══════════════════════════════════════════════════════════════
#  Check Helpers
# ═══════════════════════════════════════════════════════════════


def check_salon_required(
    request: HttpRequest,
    business: Business,
) -> HttpResponse | None:
    """
    چک می‌کنه کسب‌وکار سالن باشه.

    Returns:
        HttpResponse (redirect) اگه سالن نبود، وگرنه None.
    """
    from django.shortcuts import redirect

    if not business.is_salon:
        messages.warning(
            request,
            _("این بخش فقط برای سالن‌هاست."),
        )
        return redirect("business:dashboard")
    return None