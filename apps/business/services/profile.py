"""
سرویس مدیریت پروفایل کسب‌وکار.

شامل:
- ویرایش فیلدهای غیرحساس (فوری)
- ثبت درخواست تغییر فیلدهای حساس
"""

import logging

from django.db import transaction

from apps.accounts.models import User

from ..constants import (
    FILE_FIELDS,
    SENSITIVE_FIELDS,
    ChangeRequestStatus,
    ProfileField,
)
from ..models import Business, ProfileChangeRequest

logger = logging.getLogger(__name__)


class ProfileService:
    """
    سرویس ویرایش پروفایل کسب‌وکار.

    ─── منطق: ───
    - فیلدهای غیرحساس → فوری ذخیره
    - فیلدهای حساس → ProfileChangeRequest ساخته میشه
    """

    def __init__(self, business: Business) -> None:
        self.business = business

    @transaction.atomic
    def update_profile(
        self,
        *,
        data: dict,
        files: dict | None = None,
    ) -> dict:
        """
        آپدیت پروفایل.

        Args:
            data: دیکشنری مقادیر متنی
            files: دیکشنری فایل‌ها

        Returns:
            dict با کلیدها:
            - instant_changes: لیست فیلدهای فوری ذخیره‌شده
            - pending_changes: لیست فیلدهای نیازمند تأیید
        """
        files = files or {}
        instant_changes: list[str] = []
        pending_changes: list[str] = []

        # ─── فیلدهای متنی ───
        for field_name, new_value in data.items():
            if field_name not in SENSITIVE_FIELDS:
                # ─── فوری ذخیره کن ───
                setattr(self.business, field_name, new_value)
                instant_changes.append(field_name)
            else:
                # ─── چک تغییر ───
                old_value = getattr(self.business, field_name, "") or ""
                if str(old_value) == str(new_value):
                    continue

                self._create_or_update_change_request(
                    field_name=field_name,
                    new_value_text=new_value,
                    old_value_text=old_value,
                )
                pending_changes.append(field_name)

        # ─── فایل‌ها ───
        for field_name, file_obj in files.items():
            if field_name not in FILE_FIELDS:
                continue
            if not file_obj:
                continue

            self._create_or_update_file_change_request(
                field_name=field_name,
                new_file=file_obj,
            )
            pending_changes.append(field_name)

        # ─── ذخیره‌ی تغییرات فوری ───
        if instant_changes:
            self.business.save()

        logger.info(
            f"Profile update for {self.business.name}: "
            f"instant={instant_changes}, pending={pending_changes}"
        )

        return {
            "instant_changes": instant_changes,
            "pending_changes": pending_changes,
        }

    # ═══════════════════════════════════════════════════════════
    #  Private
    # ═══════════════════════════════════════════════════════════

    def _create_or_update_change_request(
        self,
        *,
        field_name: str,
        new_value_text: str,
        old_value_text: str = "",
    ) -> ProfileChangeRequest:
        """ساخت یا آپدیت درخواست تغییر متنی."""
        existing = ProfileChangeRequest.objects.filter(
            business=self.business,
            field_name=field_name,
            status=ChangeRequestStatus.PENDING,
        ).first()

        if existing:
            existing.new_value_text = new_value_text
            existing.old_value_text = old_value_text or existing.old_value_text
            existing.save(
                update_fields=["new_value_text", "old_value_text", "updated_at"]
            )
            return existing

        return ProfileChangeRequest.objects.create(
            business=self.business,
            content_type_id=self._get_business_content_type_id(),
            object_id=self.business.pk,
            field_name=field_name,
            old_value_text=old_value_text,
            new_value_text=new_value_text,
            status=ChangeRequestStatus.PENDING,
        )

    def _create_or_update_file_change_request(
        self,
        *,
        field_name: str,
        new_file,
    ) -> ProfileChangeRequest:
        """ساخت یا آپدیت درخواست تغییر فایل."""
        old_file = getattr(self.business, field_name, None)
        old_value_text = old_file.url if old_file else ""

        existing = ProfileChangeRequest.objects.filter(
            business=self.business,
            field_name=field_name,
            status=ChangeRequestStatus.PENDING,
        ).first()

        if existing:
            # ─── حذف فایل قبلی درخواست ───
            if existing.new_value_file:
                existing.new_value_file.delete(save=False)

            existing.new_value_file = new_file
            existing.old_value_text = old_value_text
            existing.save(
                update_fields=[
                    "new_value_file",
                    "old_value_text",
                    "updated_at",
                ]
            )
            return existing

        return ProfileChangeRequest.objects.create(
            business=self.business,
            content_type_id=self._get_business_content_type_id(),
            object_id=self.business.pk,
            field_name=field_name,
            old_value_text=old_value_text,
            new_value_file=new_file,
            status=ChangeRequestStatus.PENDING,
        )

    @staticmethod
    def _get_business_content_type_id() -> int:
        """گرفتن ContentType ID برای Business."""
        from django.contrib.contenttypes.models import ContentType

        ct, _ = ContentType.objects.get_or_create(
            app_label="business",
            model="business",
        )
        return ct.id