"""
Views ویرایش پروفایل کسب‌وکار.
"""

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.decorators import business_required

from ..forms import AvatarForm, BusinessProfileForm
from ..models import Business
from ..selectors import get_pending_change_requests
from ..services import ProfileService

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Edit Profile
# ═══════════════════════════════════════════════════════════════


@business_required
@require_http_methods(["GET", "POST"])
def edit_profile(request: HttpRequest) -> HttpResponse:
    """
    ویرایش پروفایل کسب‌وکار.

    ─── منطق: ───
    - فیلدهای غیرحساس → فوری
    - فیلدهای حساس → ProfileChangeRequest
    """
    business = request.user.business

    if request.method == "POST":
        form = BusinessProfileForm(
            request.POST,
            instance=business,
        )
        avatar_form = AvatarForm(
            request.POST,
            request.FILES,
            instance=business,
        )

        if form.is_valid() and avatar_form.is_valid():
            # ─── جمع‌آوری داده ───
            data = {}
            files = {}

            # ─── فیلدهای تغییر یافته ───
            for field_name in form.changed_data:
                data[field_name] = form.cleaned_data.get(field_name, "")

            # ─── فایل‌ها ───
            if "avatar" in avatar_form.changed_data and request.FILES.get(
                "avatar"
            ):
                files["avatar"] = request.FILES["avatar"]

            # ─── آپدیت ───
            if data or files:
                service = ProfileService(business)
                result = service.update_profile(data=data, files=files)

                instant = result["instant_changes"]
                pending = result["pending_changes"]

                # ─── پیام مناسب ───
                if instant and pending:
                    messages.warning(
                        request,
                        _(
                            "✅ %(count)s تغییر فوری اعمال شد. "
                            "⏳ %(pending)s تغییر نیاز به تأیید مدیر داره."
                        )
                        % {"count": len(instant), "pending": len(pending)},
                    )
                elif pending:
                    messages.warning(
                        request,
                        _(
                            "⏳ %(count)s تغییر برای بررسی به مدیر ارسال شد. "
                            "بعد از تأیید، اعمال میشه."
                        )
                        % {"count": len(pending)},
                    )
                elif instant:
                    messages.success(request, _("تغییرات با موفقیت اعمال شد. ✅"))
                else:
                    messages.info(request, _("هیچ تغییری ثبت نشد."))

                return redirect("business:edit_profile")
            else:
                messages.info(request, _("هیچ تغییری ثبت نشد."))
        else:
            messages.error(request, _("لطفاً خطاها رو برطرف کن."))
    else:
        form = BusinessProfileForm(instance=business)
        avatar_form = AvatarForm(instance=business)

    # ─── درخواست‌های معلق ───
    pending_requests = get_pending_change_requests(business)

    return render(
        request,
        "business/edit_profile.html",
        {
            "business": business,
            "form": form,
            "avatar_form": avatar_form,
            "pending_requests": pending_requests,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Delete Avatar
# ═══════════════════════════════════════════════════════════════


@business_required
@require_POST
def delete_avatar(request: HttpRequest) -> HttpResponse:
    """
    درخواست حذف آواتار.

    ─── چرا؟ ───
    حذف آواتار هم یه تغییر حساسه (نیاز به تأیید ادمین).
    """
    business = request.user.business

    if not business.avatar:
        messages.warning(request, _("آواتاری برای حذف وجود نداره."))
        return redirect("business:edit_profile")

    from django.contrib.contenttypes.models import ContentType

    from ..constants import ChangeRequestStatus, ProfileField
    from ..models import Business, ProfileChangeRequest

    # ─── اگه درخواست معلق داره، لغوش کن ───
    existing = ProfileChangeRequest.objects.filter(
        business=business,
        field_name=ProfileField.AVATAR,
        status=ChangeRequestStatus.PENDING,
    ).first()

    if existing:
        if existing.new_value_file:
            existing.new_value_file.delete(save=False)
        existing.delete()
        messages.success(request, _("درخواست تغییر آواتار لغو شد."))
    else:
        # ─── درخواست حذف ───
        ct = ContentType.objects.get_for_model(Business)

        ProfileChangeRequest.objects.create(
            business=business,
            content_type=ct,
            object_id=business.pk,
            field_name=ProfileField.AVATAR,
            old_value_text=business.avatar.url,
            new_value_text="",
            status=ChangeRequestStatus.PENDING,
        )
        messages.warning(
            request,
            _("⏳ درخواست حذف آواتار برای تأیید به مدیر ارسال شد."),
        )

    return redirect("business:edit_profile")