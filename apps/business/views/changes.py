"""
Views درخواست‌های تغییر.
"""

import logging

from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_POST

from apps.core.decorators import business_required

from ..constants import ChangeRequestStatus
from ..models import ProfileChangeRequest
from ..selectors import get_all_change_requests

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  My Change Requests
# ═══════════════════════════════════════════════════════════════


@business_required
@require_GET
def my_change_requests(request: HttpRequest) -> HttpResponse:
    """لیست درخواست‌های تغییر کاربر."""
    business = request.user.business

    current_status = request.GET.get("status", "all")
    if current_status not in ("all", "pending", "approved", "rejected"):
        current_status = "all"

    requests_list = get_all_change_requests(
        business,
        status=None if current_status == "all" else current_status,
    )

    # ─── شمارش‌ها (یه کوئری) ───
    counts_qs = business.change_requests.aggregate(
        pending=Count(
            "id",
            filter=Q(status=ChangeRequestStatus.PENDING),
        ),
        approved=Count(
            "id",
            filter=Q(status=ChangeRequestStatus.APPROVED),
        ),
        rejected=Count(
            "id",
            filter=Q(status=ChangeRequestStatus.REJECTED),
        ),
    )
    counts = {
        "pending": counts_qs["pending"],
        "approved": counts_qs["approved"],
        "rejected": counts_qs["rejected"],
    }

    return render(
        request,
        "business/my_change_requests.html",
        {
            "business": business,
            "requests_list": requests_list,
            "current_status": current_status,
            "counts": counts,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Cancel Change Request
# ═══════════════════════════════════════════════════════════════


@business_required
@require_POST
def cancel_change_request(
    request: HttpRequest,
    request_id: int,
) -> HttpResponse:
    """لغو یه درخواست معلق."""
    business = request.user.business

    change_req = get_object_or_404(
        ProfileChangeRequest,
        id=request_id,
        business=business,
        status=ChangeRequestStatus.PENDING,
    )

    # ─── حذف فایل اگه داشت ───
    if change_req.new_value_file:
        change_req.new_value_file.delete(save=False)

    change_req.delete()

    messages.success(request, _("درخواست لغو شد. ✅"))

    if request.headers.get("HX-Request"):
        return HttpResponse("")

    return redirect("business:my_change_requests")