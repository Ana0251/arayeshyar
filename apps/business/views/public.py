"""
Views عمومی کسب‌وکار.

- business_profile_public — پروفایل عمومی
- qr_code — QR Code
- share_page — صفحه اشتراک‌گذاری
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET

from apps.core.decorators import business_required

from ..models import Business
from ..selectors import (
    get_business_by_slug,
    get_public_business_data,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Public Profile
# ═══════════════════════════════════════════════════════════════


@require_GET
def business_profile_public(
    request: HttpRequest,
    slug: str,
) -> HttpResponse:
    """
    پروفایل عمومی کسب‌وکار.

    ─── دسترسی: ───
    - همه (مهمان + لاگین)
    - فقط کسب‌وکار فعال
    """
    business = get_business_by_slug(slug)
    if not business:
        messages.error(request, _("کسب‌وکار مورد نظر پیدا نشد."))
        return redirect("core:home")

    context = get_public_business_data(business)
    return render(request, "business/public_profile.html", context)


# ═══════════════════════════════════════════════════════════════
#  QR Code
# ═══════════════════════════════════════════════════════════════


@require_GET
def qr_code(request: HttpRequest, slug: str) -> HttpResponse:
    """
    تولید QR Code PNG.

    ─── نکته: ───
    QR به URL پروفایل عمومی اشاره می‌کنه.
    """
    import io

    import qrcode

    business = get_business_by_slug(slug)
    if not business:
        return HttpResponse(status=404)

    # ─── URL پروفایل ───
    profile_url = request.build_absolute_uri(f"/b/{business.slug}/")

    # ─── ساخت QR ───
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(profile_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#2C3E50", back_color="white")

    # ─── خروجی PNG ───
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="image/png")
    response["Cache-Control"] = "public, max-age=86400"  # ۱ روز
    return response


# ═══════════════════════════════════════════════════════════════
#  Share Page
# ═══════════════════════════════════════════════════════════════


@business_required
@require_GET
def share_page(request: HttpRequest) -> HttpResponse:
    """
    صفحه اشتراک‌گذاری.

    ─── نمایش: ───
    - QR Code
    - لینک اختصاصی
    - دکمه‌های اشتراک‌گذاری (واتساپ، تلگرام، ...)
    """
    business = request.user.business

    if not business.is_active:
        messages.warning(
            request,
            _("بعد از تأیید کسب‌وکارت، لینک اختصاصی فعال میشه."),
        )
        return redirect("business:dashboard")

    book_url = request.build_absolute_uri(f"/b/{business.slug}/")

    return render(
        request,
        "business/share.html",
        {
            "business": business,
            "book_url": book_url,
        },
    )