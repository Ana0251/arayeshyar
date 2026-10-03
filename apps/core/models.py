"""
مدل‌های پایه‌ی پروژه.

این مدل‌ها abstract هستن و توی همه‌ی اپ‌ها استفاده میشن.
"""

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    مدل abstract که created_at و updated_at رو به همه‌ی مدل‌ها اضافه می‌کنه.

    استفاده:
        class MyModel(TimeStampedModel):
            name = models.CharField(max_length=100)

    ─── نکته: ───
    created_at با db_index=True هست چون معمولاً توی کوئری‌ها
    بر اساس تاریخ مرتب‌سازی یا فیلتر می‌کنیم.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="تاریخ ایجاد",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین ویرایش",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet با قابلیت soft delete."""

    def delete(self):
        """Soft delete — فقط is_deleted رو True می‌کنه."""
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """حذف کامل از دیتابیس."""
        return super().delete()

    def alive(self):
        """فقط رکوردهای حذف‌نشده."""
        return self.filter(is_deleted=False)

    def dead(self):
        """فقط رکوردهای حذف‌شده."""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Manager که به‌صورت پیش‌فرض فقط رکوردهای alive رو برمی‌گردونه."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        """شامل رکوردهای حذف‌شده."""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def dead(self):
        """فقط رکوردهای حذف‌شده."""
        return SoftDeleteQuerySet(self.model, using=self._db).dead()


class SoftDeleteModel(models.Model):
    """
    مدل abstract با soft delete.

    به‌جای حذف فیزیکی، فقط is_deleted = True میشه.
    این برای audit و recovery عالیه.
    """

    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="حذف شده",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ حذف",
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # شامل حذف‌شده‌ها

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        """حذف فیزیکی."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """بازگردانی رکورد حذف‌شده."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])


class TimeStampedSoftDeleteModel(TimeStampedModel, SoftDeleteModel):
    """ترکیب TimeStamped + SoftDelete."""

    class Meta:
        abstract = True