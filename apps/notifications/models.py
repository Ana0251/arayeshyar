"""
مدل‌های notifications.

- SMSLog: لاگ همه‌ی پیام‌های ارسالی
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

from .constants import SMSStatus, SMSType


# ═══════════════════════════════════════════════════════════════
#  SMSLog
# ═══════════════════════════════════════════════════════════════


class SMSLog(TimeStampedModel):
    """
    لاگ SMS های ارسالی.

    ─── چرا؟ ───
    - Debug
    - آمار (چند پیامک در ماه)
    - صورتحساب کاوه‌نگار
    - Rate limiting
    """

    phone = models.CharField(
        _("شماره موبایل"),
        max_length=11,
        db_index=True,
    )
    message = models.TextField(
        _("متن پیام"),
    )
    sms_type = models.CharField(
        _("نوع"),
        max_length=20,
        choices=SMSType.choices,
        default=SMSType.OTHER,
        db_index=True,
    )
    status = models.CharField(
        _("وضعیت"),
        max_length=15,
        choices=SMSStatus.choices,
        default=SMSStatus.PENDING,
        db_index=True,
    )

    # ─── Backend ───
    backend = models.CharField(
        _("سرویس‌دهنده"),
        max_length=50,
        blank=True,
    )

    # ─── شناسه پیام ───
    external_id = models.CharField(
        _("شناسه پیام (سرویس‌دهنده)"),
        max_length=100,
        blank=True,
    )

    # ─── خطا ───
    error_message = models.TextField(
        _("پیام خطا"),
        blank=True,
    )

    # ─── Retry ───
    retry_count = models.PositiveSmallIntegerField(
        _("تعداد تلاش"),
        default=0,
    )

    # ─── زمان ───
    sent_at = models.DateTimeField(
        _("زمان ارسال"),
        null=True,
        blank=True,
    )
    delivered_at = models.DateTimeField(
        _("زمان تحویل"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("لاگ SMS")
        verbose_name_plural = _("لاگ‌های SMS")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone", "-created_at"]),
            models.Index(fields=["sms_type", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.phone} — {self.get_sms_type_display()} — {self.status}"

    # ═══════════════════════════════════════════════════════════
    #  Helpers
    # ═══════════════════════════════════════════════════════════

    def mark_sent(self, external_id: str = "") -> None:
        """علامت‌گذاری به‌عنوان ارسال‌شده."""
        from django.utils import timezone

        self.status = SMSStatus.SENT
        self.sent_at = timezone.now()
        if external_id:
            self.external_id = external_id
        self.save(update_fields=["status", "sent_at", "external_id", "updated_at"])

    def mark_failed(self, error: str = "") -> None:
        """علامت‌گذاری به‌عنوان ناموفق."""
        self.status = SMSStatus.FAILED
        self.error_message = error
        self.retry_count += 1
        self.save(update_fields=["status", "error_message", "retry_count", "updated_at"])

    def mark_delivered(self) -> None:
        """علامت‌گذاری به‌عنوان تحویل‌شده."""
        from django.utils import timezone

        self.status = SMSStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=["status", "delivered_at", "updated_at"])

    @property
    def is_sent(self) -> bool:
        return self.status in (SMSStatus.SENT, SMSStatus.DELIVERED)

    @property
    def can_retry(self) -> bool:
        from .constants import MAX_RETRY_ATTEMPTS

        return self.status == SMSStatus.FAILED and self.retry_count < MAX_RETRY_ATTEMPTS