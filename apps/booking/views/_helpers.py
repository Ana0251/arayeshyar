"""
Helper های مشترک views booking.
"""

from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


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
    return render(request, template, context or {}, status=status)


def htmx_error(request: HttpRequest, message: str, *, status: int = 400) -> HttpResponse:
    """پاسخ خطای HTMX."""
    if not is_htmx(request):
        messages.error(request, message)

    return HttpResponse(
        f'<div class="bg-danger/10 border border-danger/30 text-danger '
        f'text-sm rounded-xl p-3">⚠️ {message}</div>',
        status=status,
    )