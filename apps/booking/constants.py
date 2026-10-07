"""
ثابت‌های اپ booking.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


# ═══════════════════════════════════════════════════════════════
#  وضعیت نوبت
# ═══════════════════════════════════════════════════════════════


class AppointmentStatus(models.TextChoices):
    """
    وضعیت نوبت.

    ─── چرخه: ───
    PENDING → CONFIRMED (تأیید توسط کسب‌وکار)
    PENDING → CANCELLED (لغو توسط کسب‌وکار یا مشتری)
    CONFIRMED → COMPLETED (انجام شد)
    CONFIRMED → CANCELLED (لغو بعد از تأیید)
    CONFIRMED → NO_SHOW (مشتری نیامد)
    """

    PENDING = "pending", _("در انتظار تأیید")
    CONFIRMED = "confirmed", _("تأیید شده")
    CANCELLED = "cancelled", _("لغو شده")
    COMPLETED = "completed", _("انجام شده")
    NO_SHOW = "no_show", _("عدم حضور")


# ═══════════════════════════════════════════════════════════════
#  وضعیت لیست انتظار
# ═══════════════════════════════════════════════════════════════


class WaitingStatus(models.TextChoices):
    """وضعیت لیست انتظار."""

    WAITING = "waiting", _("در انتظار")
    NOTIFIED = "notified", _("اطلاع داده شده")
    EXPIRED = "expired", _("منقضی شده")
    CANCELLED = "cancelled", _("لغو شده")
    CONVERTED = "converted", _("تبدیل به نوبت")


# ═══════════════════════════════════════════════════════════════
#  اسلات‌های زمانی
# ═══════════════════════════════════════════════════════════════

# ─── گام پیش‌فرض اسلات‌ها (دقیقه) ───
DEFAULT_SLOT_DURATION = 30

# ─── حداکثر روزهای آینده برای رزرو ───
MAX_BOOKING_DAYS_AHEAD = 7

# ─── حداقل مدت خدمت (دقیقه) ───
MIN_SERVICE_DURATION = 5

# ─── حداکثر مدت خدمت (دقیقه) ───
MAX_SERVICE_DURATION = 600


# ═══════════════════════════════════════════════════════════════
#  وضعیت اسلات (برای نمایش)
# ═══════════════════════════════════════════════════════════════


class SlotStatus(models.TextChoices):
    """وضعیت هر اسلات زمانی."""

    AVAILABLE = "available", _("آزاد")
    BOOKED = "booked", _("رزرو شده")
    BREAK = "break", _("استراحت")
    SHORT = "short", _("زمان کم")


# ═══════════════════════════════════════════════════════════════
#  محدودیت‌ها
# ═══════════════════════════════════════════════════════════════

# ─── حداکثر نوبت همزمان برای یه مشتری ───
MAX_ACTIVE_APPOINTMENTS_PER_CUSTOMER = 3

# ─── حداکثر نوبت فعال آینده در کل سیستم برای یک مشتری ───
MAX_GLOBAL_ACTIVE_APPOINTMENTS_PER_CUSTOMER = 5

# ─── حداکثر رزرو موفق مشتری در یک بازه کوتاه ───
MAX_BOOKINGS_PER_WINDOW = 3
BOOKING_RATE_WINDOW_SECONDS = 10 * 60

# ─── حداکثر آیتم لیست انتظار برای یه مشتری ───
MAX_WAITING_ITEMS_PER_CUSTOMER = 5