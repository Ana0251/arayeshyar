"""
ثابت‌های اپ business.

مقادیری که توی چند جا استفاده میشن اینجا جمع شدن.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


# ═══════════════════════════════════════════════════════════════
#  Plan (پلن اشتراک)
# ═══════════════════════════════════════════════════════════════


class Plan(models.TextChoices):
    """
    پلن‌های اشتراک.

    ─── Trial ───
    دوره‌ی تست ۳۰ روزه رایگان (خودکار هنگام ثبت‌نام).

    ─── Basic ───
    نوبت‌دهی، لینک اختصاصی، QR، پنل.

    ─── Pro ───
    + یادآور پیامکی، لیست انتظار، گزارش درآمد،
    ساعات طلایی، مشتریان خواب‌رفته، نوبت‌های تکراری.
    """

    TRIAL = "trial", _("دوره تست")
    BASIC = "basic", _("پایه")
    PRO = "pro", _("ویژه")

    @property
    def is_paid(self) -> bool:
        return self in (Plan.BASIC, Plan.PRO)

    @property
    def has_pro_features(self) -> bool:
        return self == Plan.PRO


# ─── قیمت‌ها (تومان) ───
PLAN_PRICES = {
    Plan.TRIAL: 0,
    Plan.BASIC: 500_000,      # ← قیمت پایه (۱ ماهه)
    Plan.PRO: 1_200_000,      # ← قیمت ویژه (۱ ماهه)
}

# ─── مدت پلن (روز) ───
PLAN_DURATION_DAYS = {
    Plan.TRIAL: 30,
    Plan.BASIC: 30,
    Plan.PRO: 30,
}

# ─── برچسب‌ها ───
PLAN_LABELS = {
    Plan.TRIAL: "🎁 دوره تست",
    Plan.BASIC: "⭐ پلن پایه",
    Plan.PRO: "💎 پلن ویژه",
}


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
    GATEWAY = "gateway", _("درگاه پرداخت")  # ← بعداً

# ═══════════════════════════════════════════════════════════════
#  هفته (روزهای هفته ایرانی)
# ═══════════════════════════════════════════════════════════════


class Weekday(models.IntegerChoices):
    """
    روزهای هفته — شنبه=۰ تا جمعه=۶.

    ─── نکته مهم: ───
    Django برای `date.weekday()` از شنبه=۵ استفاده می‌کنه
    (چون دوشنبه=۰). این تبدیل رو توی utility می‌کنیم:

        python_weekday = target_date.weekday()  # 0=Mon
        iranian_weekday = (python_weekday + 2) % 7  # 0=Sat
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
    """
    فیلدهای پروفایل کسب‌وکار که تغییرشون نیاز به تأیید ادمین داره.

    ─── چرا؟ ───
    جلوگیری از:
    - تغییر نام به اسم‌های نامناسب
    - تغییر آدرس برای فرار از مسئولیت
    - تغییر تصاویر به محتوای نامناسب
    """

    # ─── فیلدهای متنی ───
    NAME = "name", _("نام")
    ADDRESS = "address", _("آدرس")
    REGION = "region", _("منطقه")
    BIO = "bio", _("درباره ما")

    # ─── فایل‌ها ───
    AVATAR = "avatar", _("عکس پروفایل")
    BUSINESS_LICENSE = "business_license", _("پروانه کسب")
    ENTRANCE_PHOTO = "entrance_photo", _("عکس ورودی")


# ─── فیلدهای حساس (set برای O(1) lookup) ───
SENSITIVE_FIELDS: frozenset[str] = frozenset(
    {
        ProfileField.NAME,
        ProfileField.ADDRESS,
        ProfileField.REGION,
        ProfileField.BIO,
        ProfileField.AVATAR,
        ProfileField.BUSINESS_LICENSE,
        ProfileField.ENTRANCE_PHOTO,
    }
)

# ─── فیلدهای فایل (نیاز به upload) ───
FILE_FIELDS: frozenset[str] = frozenset(
    {
        ProfileField.AVATAR,
        ProfileField.BUSINESS_LICENSE,
        ProfileField.ENTRANCE_PHOTO,
    }
)


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

# مسیر آپلود (upload_to)
UPLOAD_PATHS = {
    "avatar": "business/avatars/",
    "business_license": "business/licenses/",
    "entrance_photo": "business/entrances/",
    "change_request": "business/change_requests/",
}

# ─── محدودیت حجم (بایت) ───
MAX_UPLOAD_SIZE_BYTES = 2 * 1024 * 1024  # ۲ مگابایت

# ─── فرمت‌های مجاز ───
ALLOWED_IMAGE_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "webp"})


# ═══════════════════════════════════════════════════════════════
#  اعتبارسنجی ایستگاه
# ═══════════════════════════════════════════════════════════════

# ─── حداکثر تعداد ایستگاه برای سالن ───
MAX_STATIONS_PER_BUSINESS = 20

# ─── حداکثر تعداد خدمت ───
MAX_SERVICES_PER_BUSINESS = 100