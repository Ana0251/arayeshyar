"""
مدل‌های اپ customers.

شامل:
- CustomerBusiness (رابطه many-to-many بین User و Business)
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.constants import Role
from apps.accounts.models import User
from apps.business.models import Business
from apps.core.models import TimeStampedModel


# ═══════════════════════════════════════════════════════════════
#  CustomerBusiness
# ═══════════════════════════════════════════════════════════════


class CustomerBusiness(TimeStampedModel):
    """
    رابطه‌ی مشتری و کسب‌وکار.

    ─── چرا؟ ───
    مشتری از یه کسب‌وکار نوبت می‌گیره → به لیست «کسب‌وکارهای من» اضافه میشه.

    ─── متادیتا: ───
    - first_visit_at: اولین نوبت
    - last_visit_at: آخرین نوبت
    - visits_count: تعداد کل نوبت‌ها
    - is_favorite: مشتری علامت‌گذاری کرده (آینده)

    ─── Unique: ───
    یه مشتری نمی‌تونه دوبار یه کسب‌وکار رو «اضافه» کنه.
    """

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="my_businesses",
        verbose_name=_("مشتری"),
        limit_choices_to={"role": Role.CUSTOMER},
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="my_customers",
        verbose_name=_("کسب‌وکار"),
    )

    # ─── متادیتا ───
    first_visit_at = models.DateTimeField(
        _("اولین بازدید"),
        null=True,
        blank=True,
        help_text=_("اولین نوبتی که مشتری گرفت"),
    )
    last_visit_at = models.DateTimeField(
        _("آخرین بازدید"),
        null=True,
        blank=True,
        help_text=_("آخرین نوبت مشتری"),
    )
    visits_count = models.PositiveIntegerField(
        _("تعداد نوبت‌ها"),
        default=0,
    )
    is_favorite = models.BooleanField(
        _("علاقه‌مندی"),
        default=False,
        help_text=_("مشتری این کسب‌وکار رو نشون کرده"),
    )

    # ─── یادداشت مشتری ───
    note = models.CharField(
        _("یادداشت مشتری"),
        max_length=200,
        blank=True,
    )

    class Meta:
        verbose_name = _("کسب‌وکار مشتری")
        verbose_name_plural = _("کسب‌وکارهای مشتری")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "business"],
                name="unique_customer_business",
            ),
        ]
        indexes = [
            models.Index(fields=["customer", "-created_at"]),
            models.Index(fields=["business", "-created_at"]),
            models.Index(fields=["is_favorite"]),
        ]

    def __str__(self) -> str:
        return f"{self.customer.display_name} → {self.business.name}"

    # ═══════════════════════════════════════════════════════════
    #  Methods
    # ═══════════════════════════════════════════════════════════

    def record_visit(self, at=None) -> None:
        """
        ثبت بازدید جدید.

        Args:
            at: زمان بازدید (پیش‌فرض: الان)
        """
        at = at or timezone.now()

        if not self.first_visit_at:
            self.first_visit_at = at

        self.last_visit_at = at
        self.visits_count += 1
        self.save(
            update_fields=[
                "first_visit_at",
                "last_visit_at",
                "visits_count",
                "updated_at",
            ]
        )