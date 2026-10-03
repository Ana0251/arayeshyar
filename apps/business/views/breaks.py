"""
Views مدیریت وقفه‌ها.
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import business_required

from ..forms import BreakForm
from ..models import Break

from ._helpers import htmx_error, htmx_response, is_htmx

logger = logging.getLogger(__name__)


@business_required
@require_http_methods(["GET", "POST"])
def manage_breaks(request: HttpRequest) -> HttpResponse:
    """مدیریت وقفه‌های استراحت."""
    business = request.user.business

    breaks = business.breaks.filter(
        station__isnull=True
    ).order_by("start_time")

    if request.method == "POST":
        form = BreakForm(request.POST)

        if form.is_valid():
            br = form.save(commit=False)
            br.business = business

            # ─── چک تداخل با وقفه‌های دیگه ───
            conflict = Break.objects.filter(
                business=business,
                station__isnull=True,
                is_active=True,
                start_time__lt=br.end_time,
                end_time__gt=br.start_time,
            ).exists()

            if conflict:
                if is_htmx(request):
                    return htmx_error(
                        request,
                        _("این بازه با یه وقفه دیگه تداخل داره."),
                    )
                messages.error(
                    request,
                    _("این بازه با یه وقفه دیگه تداخل داره."),
                )
            else:
                br.save()

                if is_htmx(request):
                    breaks = business.breaks.filter(
                        station__isnull=True
                    ).order_by("start_time")
                    return htmx_response(
                        request,
                        template="business/partials/_breaks_list.html",
                        context={
                            "breaks": breaks,
                            "business": business,
                        },
                    )

                messages.success(request, _("وقفه ثبت شد. ✅"))
                return redirect("business:manage_breaks")
        else:
            if is_htmx(request):
                return htmx_error(
                    request,
                    _("لطفاً خطاها رو برطرف کن."),
                )
    else:
        form = BreakForm()

    return render(
        request,
        "business/manage_breaks.html",
        {
            "business": business,
            "breaks": breaks,
            "form": form,
        },
    )


@business_required
@require_POST
def delete_break(
    request: HttpRequest,
    break_id: int,
) -> HttpResponse:
    """حذف وقفه."""
    business = request.user.business
    br = get_object_or_404(
        Break,
        id=break_id,
        business=business,
    )
    br.delete()

    if is_htmx(request):
        breaks = business.breaks.filter(
            station__isnull=True
        ).order_by("start_time")
        return htmx_response(
            request,
            template="business/partials/_breaks_list.html",
            context={
                "breaks": breaks,
                "business": business,
            },
        )

    messages.success(request, _("وقفه حذف شد."))
    return redirect("business:manage_breaks")