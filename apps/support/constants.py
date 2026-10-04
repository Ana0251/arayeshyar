"""
ثابت‌های اپ support.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


# ═══════════════════════════════════════════════════════════════
#  دسته‌بندی تیکت
# ═══════════════════════════════════════════════════════════════


class TicketCategory(models.TextChoices):
    """دسته‌بندی تیکت."""

    TECHNICAL = "technical", _("مشکل فنی")
    PAYMENT = "payment", _("پرداخت و پلن")
    BOOKING = "booking", _("نوبت‌دهی")
    COMPLAINT = "complaint", _("شکایت")
    SUGGESTION = "suggestion", _("پیشنهاد")
    OTHER = "other", _("سایر")


# ═══════════════════════════════════════════════════════════════
#  اولویت تیکت
# ═══════════════════════════════════════════════════════════════


class TicketPriority(models.TextChoices):
    """اولویت تیکت."""

    LOW = "low", _("کم")
    NORMAL = "normal", _("متوسط")
    HIGH = "high", _("زیاد")
    URGENT = "urgent", _("فوری")


# ═══════════════════════════════════════════════════════════════
#  وضعیت تیکت
# ═══════════════════════════════════════════════════════════════


class TicketStatus(models.TextChoices):
    """وضعیت تیکت."""

    OPEN = "open", _("باز")
    IN_PROGRESS = "in_progress", _("در حال بررسی")
    ANSWERED = "answered", _("پاسخ داده شده")
    CLOSED = "closed", _("بسته شده")