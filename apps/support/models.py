"""
مدل‌های اپ support.

- Ticket         → تیکت پشتیبانی
- TicketMessage  → پیام‌های تیکت
- TicketAttachment → فایل پیوست
"""

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.core.models import TimeStampedModel

from .constants import TicketCategory, TicketPriority, TicketStatus


# ═══════════════════════════════════════════════════════════════
#  Ticket
# ═══════════════════════════════════════════════════════════════


class Ticket(TimeStampedModel):
    """تیکت پشتیبانی."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tickets",
        verbose_name=_("کاربر"),
    )
    subject = models.CharField(
        _("موضوع"),
        max_length=200,
    )
    category = models.CharField(
        _("دسته"),
        max_length=20,
        choices=TicketCategory.choices,
        default=TicketCategory.OTHER,
        db_index=True,
    )
    priority = models.CharField(
        _("اولویت"),
        max_length=10,
        choices=TicketPriority.choices,
        default=TicketPriority.NORMAL,
        db_index=True,
    )
    status = models.CharField(
        _("وضعیت"),
        max_length=15,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN,
        db_index=True,
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name=_("بررسی‌کننده"),
        limit_choices_to={"is_staff": True},
    )
    closed_at = models.DateTimeField(
        _("تاریخ بسته شدن"),
        null=True,
        blank=True,
    )
    last_reply_at = models.DateTimeField(
        _("آخرین پاسخ"),
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        verbose_name = _("تیکت")
        verbose_name_plural = _("تیکت‌ها")
        ordering = ["-last_reply_at", "-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["assigned_to", "status"]),
        ]

    def __str__(self) -> str:
        return f"#{self.pk} — {self.subject}"

    # ═══════════════════════════════════════════════════════════
    #  Properties
    # ═══════════════════════════════════════════════════════════

    @property
    def is_open(self) -> bool:
        return self.status == TicketStatus.OPEN

    @property
    def is_closed(self) -> bool:
        return self.status == TicketStatus.CLOSED

    @property
    def messages_count(self) -> int:
        return self.messages.count()

    @property
    def unread_count(self) -> int:
        """تعداد پیام‌های خوانده‌نشده (برای کاربر)."""
        return self.messages.filter(
            is_read=False,
            is_staff_reply=True,
        ).count()

    # ═══════════════════════════════════════════════════════════
    #  Methods
    # ═══════════════════════════════════════════════════════════

    def close(self) -> None:
        """بستن تیکت."""
        self.status = TicketStatus.CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=["status", "closed_at", "updated_at"])

    def reopen(self) -> None:
        """باز کردن دوباره."""
        self.status = TicketStatus.OPEN
        self.closed_at = None
        self.save(update_fields=["status", "closed_at", "updated_at"])


# ═══════════════════════════════════════════════════════════════
#  TicketMessage
# ═══════════════════════════════════════════════════════════════


class TicketMessage(TimeStampedModel):
    """پیام توی تیکت."""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("تیکت"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ticket_messages",
        verbose_name=_("فرستنده"),
    )
    message = models.TextField(
        _("متن پیام"),
        max_length=2000,
    )
    is_staff_reply = models.BooleanField(
        _("پاسخ ادمین"),
        default=False,
        db_index=True,
    )
    is_read = models.BooleanField(
        _("خوانده شده"),
        default=False,
        db_index=True,
    )

    class Meta:
        verbose_name = _("پیام تیکت")
        verbose_name_plural = _("پیام‌های تیکت")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ticket", "created_at"]),
            models.Index(fields=["is_read", "is_staff_reply"]),
        ]

    def __str__(self) -> str:
        kind = "ادمین" if self.is_staff_reply else "کاربر"
        return f"#{self.ticket_id} — {kind} — {self.created_at:%H:%M}"

    def save(self, *args, **kwargs) -> None:
        """آپدیت last_reply_at تیکت."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.ticket.last_reply_at = self.created_at
            self.ticket.save(update_fields=["last_reply_at"])


# ═══════════════════════════════════════════════════════════════
#  TicketAttachment
# ═══════════════════════════════════════════════════════════════


class TicketAttachment(TimeStampedModel):
    """فایل پیوست تیکت."""

    ticket_message = models.ForeignKey(
        TicketMessage,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("پیام"),
    )
    file = models.FileField(
        _("فایل"),
        upload_to="tickets/attachments/%Y/%m/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "jpg", "jpeg", "png", "webp", "gif",
                    "pdf",
                ]
            )
        ],
    )
    original_name = models.CharField(
        _("نام اصلی"),
        max_length=255,
        blank=True,
    )
    file_size = models.PositiveIntegerField(
        _("حجم (بایت)"),
        default=0,
    )

    class Meta:
        verbose_name = _("فایل پیوست")
        verbose_name_plural = _("فایل‌های پیوست")
        ordering = ["id"]

    def __str__(self) -> str:
        return self.original_name or str(self.file)

    @property
    def is_image(self) -> bool:
        ext = self.file.name.rsplit(".", 1)[-1].lower()
        return ext in ("jpg", "jpeg", "png", "webp", "gif")

    @property
    def size_display(self) -> str:
        """حجم به صورت خوانا."""
        if self.file_size < 1024:
            return f"{self.file_size} بایت"
        if self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} کیلوبایت"
        return f"{self.file_size / (1024 * 1024):.1f} مگابایت"
class PasswordResetRequest(TimeStampedModel):
    """درخواست بازیابی رمز وقتی کانال OTP در دسترس نیست."""
    STATUS_CHOICES=[("open","باز"),("done","انجام شد"),("rejected","رد شد")]
    phone=models.CharField("شماره موبایل",max_length=15,db_index=True)
    full_name=models.CharField("نام",max_length=120,blank=True)
    note=models.TextField("توضیحات",max_length=1000,blank=True)
    status=models.CharField("وضعیت",max_length=10,choices=STATUS_CHOICES,default="open",db_index=True)
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="password_reset_requests",verbose_name="کاربر مرتبط")
    handled_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="handled_password_reset_requests",verbose_name="رسیدگی‌کننده")
    handled_at=models.DateTimeField("زمان رسیدگی",null=True,blank=True)
    class Meta:
        ordering=["-created_at"]
        verbose_name="درخواست بازیابی رمز"
        verbose_name_plural="درخواست‌های بازیابی رمز"
    def __str__(self): return f"{self.phone} - {self.get_status_display()}"
