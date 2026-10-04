"""
ثابت‌های اپ business.

مقادیری که توی چند جا استفاده میشن اینجا جمع شدن.

─── نکته: ───
Plan از enum به Model تبدیل شد (توی models.py).
PLAN_PRICES, PLAN_DURATION_DAYS, PLAN_LABELS دیگه لازم نیستن
چون توی مدل Plan ذخیره میشن.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


# ═══════════════════════════════════════════════════════════════
#  Payment
# ═══════════════════════════════════════════════════════════════


class PaymentStatus(models.TextChoices):
    """وضعیت پرداخت."""

    PENDING = "pending", _("در انتظار بررسی")
    APPROVED = "approved", _("تأیید شده")
    REJECTED = "rejected", _("رد شده")


class PaymentMethod(models.TextChoices):
    """روش پرداخت."""

    CARD_TO_CARD = "card_to_card", _("کارت به کارت")
    GATEWAY = "gateway", _("درگاه پرداخت")


# ═══════════════════════════════════════════════════════════════
#  هفته (روزهای هفته ایرانی)
# ═══════════════════════════════════════════════════════════════


class Weekday(models.IntegerChoices):
    """
    روزهای هفته — شنبه=۰ تا جمعه=۶.
    """

    SATURDAY = 0, _("شنبه")
    SUNDAY = 1, _("یکشنبه")
    MONDAY = 2, _("دوشنبه")
    TUESDAY = 3, _("سه‌شنبه")
    WEDNESDAY = 4, _("چهارشنبه")
    THURSDAY = 5, _("پنجشنبه")
    FRIDAY = 6, _("جمعه")

    @classmethod
    def from_python_weekday(cls, python_weekday: int) -> int:
        """تبدیل weekday پایتون (دوشنبه=۰) به ایرانی (شنبه=۰)."""
        return (python_weekday + 2) % 7


# ═══════════════════════════════════════════════════════════════
#  فیلدهای حساس پروفایل
# ═══════════════════════════════════════════════════════════════


class ProfileField(models.TextChoices):
    """فیلدهای پروفایل کسب‌وکار که تغییرشون نیاز به تأیید ادمین داره."""

    NAME = "name", _("نام")
    ADDRESS = "address", _("آدرس")
    REGION = "region", _("منطقه")
    BIO = "bio", _("درباره ما")

    AVATAR = "avatar", _("عکس پروفایل")
    BUSINESS_LICENSE = "business_license", _("پروانه کسب")
    ENTRANCE_PHOTO = "entrance_photo", _("عکس ورودی")


SENSITIVE_FIELDS: frozenset[str] = frozenset({
    ProfileField.NAME,
    ProfileField.ADDRESS,
    ProfileField.REGION,
    ProfileField.BIO,
    ProfileField.AVATAR,
    ProfileField.BUSINESS_LICENSE,
    ProfileField.ENTRANCE_PHOTO,
})

FILE_FIELDS: frozenset[str] = frozenset({
    ProfileField.AVATAR,
    ProfileField.BUSINESS_LICENSE,
    ProfileField.ENTRANCE_PHOTO,
})


# ═══════════════════════════════════════════════════════════════
#  وضعیت درخواست تغییر
# ═══════════════════════════════════════════════════════════════


class ChangeRequestStatus(models.TextChoices):
    """وضعیت درخواست تغییر پروفایل."""

    PENDING = "pending", _("در انتظار بررسی")
    APPROVED = "approved", _("تأیید شده")
    REJECTED = "rejected", _("رد شده")


# ═══════════════════════════════════════════════════════════════
#  آپلود فایل
# ═══════════════════════════════════════════════════════════════

UPLOAD_PATHS = {
    "avatar": "business/avatars/",
    "business_license": "business/licenses/",
    "entrance_photo": "business/entrances/",
    "change_request": "business/change_requests/",
}

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # ۵ مگابایت

ALLOWED_IMAGE_EXTENSIONS = frozenset({
    "jpg", "jpeg", "png", "webp",
    "gif", "bmp", "tiff",
    "heic", "heif",
})


# ═══════════════════════════════════════════════════════════════
#  اعتبارسنجی
# ═══════════════════════════════════════════════════════════════

MAX_STATIONS_PER_BUSINESS = 20
MAX_SERVICES_PER_BUSINESS = 100