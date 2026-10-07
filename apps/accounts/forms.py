"""فرم‌های ورود و ساخت حساب با شماره موبایل و رمز عبور."""
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from apps.core.utils.phone import normalize_phone
from .models import User

INPUT_CLASS = (
    "w-full px-4 py-3 rounded-xl border border-black/10 bg-white "
    "focus:border-accent focus:ring-2 focus:ring-accent/20 outline-none transition"
)


class PhonePasswordLoginForm(forms.Form):
    phone = forms.CharField(
        label=_("شماره موبایل"), max_length=15,
        widget=forms.TextInput(attrs={
            "autocomplete": "tel", "autofocus": True, "placeholder": "09123456789",
            "dir": "ltr", "inputmode": "numeric", "class": INPUT_CLASS,
        }),
    )
    password = forms.CharField(
        label=_("رمز عبور"), min_length=6,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "current-password", "placeholder": "حداقل ۶ کاراکتر", "class": INPUT_CLASS,
        }),
    )

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))
        if not phone:
            raise forms.ValidationError(_("شماره موبایل معتبر نیست."))
        return phone


class CustomerSignupForm(forms.Form):
    full_name = forms.CharField(
        label=_("نام و نام خانوادگی"), max_length=100,
        widget=forms.TextInput(attrs={
            "autocomplete": "name", "placeholder": "مثلاً علی رضایی", "class": INPUT_CLASS,
        }),
    )
    phone = forms.CharField(
        label=_("شماره موبایل"), max_length=15,
        widget=forms.TextInput(attrs={
            "autocomplete": "tel", "placeholder": "09123456789",
            "dir": "ltr", "inputmode": "numeric", "class": INPUT_CLASS,
        }),
    )
    email = forms.EmailField(
        label=_("ایمیل (اختیاری)"), required=False,
        widget=forms.EmailInput(attrs={
            "autocomplete": "email", "placeholder": "name@example.com", "dir": "ltr", "class": INPUT_CLASS,
        }),
    )
    password = forms.CharField(
        label=_("رمز عبور"), min_length=6,
        help_text=_("حداقل ۶ کاراکتر؛ برای ورودهای بعدی همین رمز رو استفاده می‌کنی."),
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password", "placeholder": "حداقل ۶ کاراکتر", "class": INPUT_CLASS,
        }),
    )
    password_confirm = forms.CharField(
        label=_("تکرار رمز عبور"), min_length=6,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password", "placeholder": "رمز رو دوباره وارد کن", "class": INPUT_CLASS,
        }),
    )

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))
        if not phone:
            raise forms.ValidationError(_("شماره موبایل معتبر نیست."))
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(_("این شماره قبلاً حساب دارد؛ از صفحه ورود استفاده کن."))
        return phone

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("این ایمیل قبلاً برای حساب دیگری ثبت شده."))
        return email or None

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password"), cleaned.get("password_confirm")
        if p1 and p2 and p1 != p2:
            self.add_error("password_confirm", _("تکرار رمز با رمز عبور یکی نیست."))
        return cleaned


class BusinessSignupForm(forms.Form):
    phone = forms.CharField(
        label=_("شماره موبایل"), max_length=15,
        widget=forms.TextInput(attrs={
            "autocomplete": "tel", "autofocus": True, "placeholder": "09123456789",
            "dir": "ltr", "inputmode": "numeric", "class": INPUT_CLASS,
        }),
    )
    email = forms.EmailField(
        label=_("ایمیل (اختیاری)"), required=False,
        widget=forms.EmailInput(attrs={
            "autocomplete": "email", "placeholder": "name@example.com", "dir": "ltr", "class": INPUT_CLASS,
        }),
    )
    password = forms.CharField(
        label=_("رمز عبور"), min_length=6,
        help_text=_("حداقل ۶ کاراکتر؛ لازم نیست حتماً علامت یا حرف بزرگ داشته باشه."),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "حداقل ۶ کاراکتر", "class": INPUT_CLASS}),
    )
    password_confirm = forms.CharField(
        label=_("تکرار رمز عبور"), min_length=6,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "رمز رو دوباره وارد کن", "class": INPUT_CLASS}),
    )

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))
        if not phone:
            raise forms.ValidationError(_("شماره موبایل معتبر نیست."))
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(_("این شماره قبلاً حساب دارد؛ از صفحه ورود استفاده کن."))
        return phone

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("این ایمیل قبلاً برای حساب دیگری ثبت شده."))
        return email or None

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password"), cleaned.get("password_confirm")
        if p1 and p2 and p1 != p2:
            self.add_error("password_confirm", _("تکرار رمز با رمز عبور یکی نیست."))
        return cleaned


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label=_("رمز فعلی"),
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "class": INPUT_CLASS}),
    )
    new_password = forms.CharField(
        label=_("رمز جدید"), min_length=6,
        help_text=_("حداقل ۶ کاراکتر."),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": INPUT_CLASS}),
    )
    new_password_confirm = forms.CharField(
        label=_("تکرار رمز جدید"), min_length=6,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": INPUT_CLASS}),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        value = self.cleaned_data.get("current_password")
        if not self.user.check_password(value):
            raise forms.ValidationError(_("رمز فعلی درست نیست."))
        return value

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password")
        p2 = cleaned.get("new_password_confirm")
        if p1 and p2 and p1 != p2:
            self.add_error("new_password_confirm", _("تکرار رمز جدید با رمز جدید یکی نیست."))
        if p1 and self.user.check_password(p1):
            self.add_error("new_password", _("رمز جدید باید با رمز فعلی متفاوت باشد."))
        return cleaned


class AdminResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label=_("رمز جدید"), min_length=6,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": INPUT_CLASS}),
    )
    new_password_confirm = forms.CharField(
        label=_("تکرار رمز جدید"), min_length=6,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": INPUT_CLASS}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") and cleaned.get("new_password") != cleaned.get("new_password_confirm"):
            self.add_error("new_password_confirm", _("تکرار رمز با رمز جدید یکی نیست."))
        return cleaned
