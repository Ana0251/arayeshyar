"""
اعتبارسنجی فایل‌های آپلودی.

جلوگیری از:
- فایل‌های خیلی بزرگ
- فایل‌های غیرتصویری
- فایل‌های مخرب (که پسوندشون عوض شده)
"""

from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .constants import (
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
)


def validate_image_size(file) -> None:
    """
    اعتبارسنجی حجم فایل تصویری.

    Raises:
        ValidationError: اگه فایل بزرگ‌تر از حد مجاز باشه.
    """
    if file.size > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        raise ValidationError(
            _("حجم فایل نباید بیشتر از %(max)s مگابایت باشه.")
            % {"max": int(max_mb)},
            code="file_too_large",
        )


def validate_image_extension(file) -> None:
    """
    اعتبارسنجی فرمت فایل تصویری (بر اساس پسوند).

    Raises:
        ValidationError: اگه فرمت مجاز نباشه.
    """
    ext = Path(file.name).suffix.lower().lstrip(".")
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = "، ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
        raise ValidationError(
            _("فرمت فایل باید یکی از اینا باشه: %(allowed)s")
            % {"allowed": allowed},
            code="invalid_extension",
        )


def validate_image_content(file) -> None:
    """
    اعتبارسنجی محتوای فایل (که واقعاً تصویره).

    ─── چرا؟ ───
    ممکنه کسی یه فایل PHP رو با پسوند .jpg آپلود کنه.
    Pillow محتوا رو چک می‌کنه و اگه تصویر نباشه، خطا می‌ده.

    Raises:
        ValidationError: اگه فایل واقعاً تصویر نباشه.
    """
    try:
        from PIL import Image

        # ─── reset position (چون ممکنه قبلاً خونده شده باشه) ───
        file.seek(0)
        img = Image.open(file)
        img.verify()  # چک می‌کنه که فایل تصویره
        file.seek(0)  # دوباره reset برای ذخیره‌ی بعدی
    except Exception:
        raise ValidationError(
            _("فایل آپلود‌شده یه تصویر معتبر نیست."),
            code="invalid_image_content",
        )


def validate_image(file) -> None:
    """
    اعتبارسنجی کامل فایل تصویری (پسوند + حجم + محتوا).

    استفاده توی model:
        avatar = models.ImageField(
            upload_to=...,
            validators=[validate_image],
        )
    """
    validate_image_extension(file)
    validate_image_size(file)
    validate_image_content(file)