"""
منطق اعمال درخواست‌های تغییر پروفایل.
"""

import logging

from django.utils import timezone

from ..constants import ProfileField

logger = logging.getLogger(__name__)


def apply_change_request(change_request) -> None:
    """
    اعمال یه درخواست تغییر روی کسب‌وکار.

    Args:
        change_request: ProfileChangeRequest
    """
    business = change_request.business
    field_name = change_request.field_name

    if not business:
        logger.warning(
            f"Change request {change_request.pk} has no business"
        )
        return

    # ─── فیلدهای فایل ───
    if change_request.is_file_field:
        if change_request.new_value_file:
            # حذف فایل قدیمی (اختیاری)
            old_file = getattr(business, field_name, None)
            if old_file:
                old_file.delete(save=False)

            # ذخیره فایل جدید
            setattr(business, field_name, change_request.new_value_file)
            logger.info(
                f"Applied file change for {business.name} — {field_name}"
            )
        else:
            # حذف فایل (new_value_file خالیه)
            old_file = getattr(business, field_name, None)
            if old_file:
                old_file.delete(save=False)
            setattr(business, field_name, None)
            logger.info(
                f"Removed file for {business.name} — {field_name}"
            )
    else:
        # ─── فیلدهای متنی ───
        setattr(business, field_name, change_request.new_value_text)
        logger.info(
            f"Applied text change for {business.name} — {field_name}"
        )

    business.save()