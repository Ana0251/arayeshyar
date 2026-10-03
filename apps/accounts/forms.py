"""
فرم‌های اپ accounts.

شامل:
- LoginPhoneForm  → ورود با شماره موبایل
- LoginOTPForm    → تأیید کد ۶ رقمی
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.utils.phone import normalize_phone

from .constants import OTP_LENGTH


# ═══════════════════════════════════════════════════════════════
#  LoginPhoneForm
# ═══════════════════════════════════════════════════════════════


class LoginPhoneForm(forms.Form):
    """
    فرم ورود با شماره موبایل.

    ─── مراحل: ───
    1. کاربر شماره رو وارد می‌کنه
    2. اعتبارسنجی فرمت (09XXXXXXXXX)
    3. نرمال‌سازی
    4. ارسال OTP
    """

    phone = forms.CharField(
        label=_("شماره موبایل"),
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "type": "tel",
                "inputmode": "numeric",
                "autocomplete": "tel",
                "autofocus": True,
                "placeholder": "09123456789",
                "dir": "ltr",
                "class": (
                    "w-full px-4 py-3 rounded-xl border border-black/10 "
                    "bg-white text-center text-lg font-bold tracking-wider "
                    "font-mono focus:border-accent focus:ring-2 "
                    "focus:ring-accent/20 outline-none transition"
                ),
            }
        ),
    )

    def clean_phone(self) -> str:
        """نرمال‌سازی و اعتبارسنجی شماره."""
        raw = self.cleaned_data.get("phone", "").strip()
        normalized = normalize_phone(raw)

        if not normalized:
            raise forms.ValidationError(
                _("شماره موبایل نامعتبره. فرمت صحیح: 09XXXXXXXXX"),
                code="invalid_phone",
            )

        return normalized


# ═══════════════════════════════════════════════════════════════
#  LoginOTPForm
# ═══════════════════════════════════════════════════════════════


class LoginOTPForm(forms.Form):
    """
    فرم تأیید کد ۶ رقمی.

    ─── نکته: ───
    کد از session میاد (چون کاربر بعد از login_phone به اینجا redirect میشه).
    """

    code = forms.CharField(
        label=_("کد تأیید"),
        max_length=OTP_LENGTH,
        min_length=OTP_LENGTH,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "autofocus": True,
                "placeholder": "–" * OTP_LENGTH,
                "dir": "ltr",
                "maxlength": str(OTP_LENGTH),
                "pattern": "[0-9]*",
                "class": (
                    "w-full px-4 py-4 rounded-xl border-2 border-black/10 "
                    "bg-white text-center text-3xl font-bold "
                    "tracking-[0.5em] font-mono focus:border-accent "
                    "focus:ring-2 focus:ring-accent/20 outline-none transition"
                ),
            }
        ),
    )

    def clean_code(self) -> str:
        """اعتبارسنجی کد."""
        code = self.cleaned_data.get("code", "").strip()

        # ─── حذف فاصله‌ها ───
        code = code.replace(" ", "").replace("-", "")

        # ─── تبدیل ارقام فارسی/عربی به لاتین ───
        code = _persian_to_latin(code)

        if not code:
            raise forms.ValidationError(
                _("کد تأیید الزامیه."),
                code="required_code",
            )

        if not code.isdigit():
            raise forms.ValidationError(
                _("کد باید فقط شامل اعداد باشه."),
                code="invalid_code",
            )

        if len(code) != OTP_LENGTH:
            raise forms.ValidationError(
                _("کد باید %(len)s رقم باشه.") % {"len": OTP_LENGTH},
                code="invalid_length",
            )

        return code


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════


def _persian_to_latin(text: str) -> str:
    """تبدیل ارقام فارسی/عربی به لاتین."""
    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"
    latin = "0123456789"

    return text.translate(
        str.maketrans(persian + arabic, latin + latin)
    )