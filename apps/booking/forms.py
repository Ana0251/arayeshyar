"""
فرم‌های اپ booking.
"""

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.utils.phone import normalize_phone
from apps.core.widgets import JalaliDateInput, JalaliTimeInput   # ← ← ← این خط

from .models import Appointment, WaitingList


# ═══════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════

INPUT_CLASS = (
    "w-full px-4 py-3 rounded-xl border border-black/10 bg-white "
    "focus:border-accent focus:ring-2 focus:ring-accent/20 "
    "outline-none transition"
)

TEXTAREA_CLASS = (
    "w-full px-4 py-3 rounded-xl border border-black/10 bg-white "
    "focus:border-accent focus:ring-2 focus:ring-accent/20 "
    "outline-none transition resize-none"
)


# ═══════════════════════════════════════════════════════════════
#  AppointmentForm (مشتری) — بازنویسی
# ═══════════════════════════════════════════════════════════════


class AppointmentForm(forms.Form):
    """
    فرم رزرو نوبت توسط مشتری.

    ─── نکته: ───
    - customer_name و customer_phone از user لاگین‌شده میان
    - service_id، staff_id، start_at از UI میان
    """

    # ─── اطلاعات مشتری ───
    customer_name = forms.CharField(
        label=_("نام شما"),
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": INPUT_CLASS, "placeholder": "مثلاً: مریم احمدی"}
        ),
    )
    customer_phone = forms.CharField(
        label=_("شماره موبایل"),
        max_length=15,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "09123456789",
                "dir": "ltr",
            }
        ),
    )

    # ─── انتخاب‌ها (hidden) ───
    service_id = forms.IntegerField(
        required=True,
        widget=forms.HiddenInput,
    )
    staff_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput,
    )
    start_at = forms.DateTimeField(
        required=True,
        widget=forms.HiddenInput,
    )

    # ─── یادداشت ───
    customer_note = forms.CharField(
        label=_("یادداشت (اختیاری)"),
        required=False,
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "class": TEXTAREA_CLASS,
                "rows": 2,
                "placeholder": "مثلاً: لطفاً کوتاه‌تر از حد معمول",
            }
        ),
    )

    def clean_customer_phone(self) -> str:
        """نرمال‌سازی شماره."""
        raw = self.cleaned_data["customer_phone"]
        normalized = normalize_phone(raw)
        if not normalized:
            raise forms.ValidationError(_("شماره موبایل نامعتبره."))
        return normalized

    def clean_start_at(self):
        """چک: تاریخ گذشته نباشه."""
        start_at = self.cleaned_data["start_at"]
        if start_at < timezone.now():
            raise forms.ValidationError(_("نمی‌تونی برای زمان گذشته نوبت بگیری."))
        return start_at


# ═══════════════════════════════════════════════════════════════
#  WaitingListForm (مشتری)
# ═══════════════════════════════════════════════════════════════


class WaitingListForm(forms.ModelForm):
    """فرم ثبت در لیست انتظار."""

    class Meta:
        model = WaitingList
        fields = ["date", "preferred_time", "note"]
        widgets = {
            "date": JalaliDateInput(),           # ← ← ← استفاده از Jalali
            "preferred_time": JalaliTimeInput(),  # ← ← ← استفاده از Jalali
            "note": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "placeholder": "مثلاً: فقط صبح‌ها می‌تونم",
                }
            ),
        }

    def clean_date(self):
        target_date = self.cleaned_data["date"]
        if target_date < timezone.localdate():
            raise forms.ValidationError(_("تاریخ مورد نظر نمی‌تونه گذشته باشه."))
        return target_date


# ═══════════════════════════════════════════════════════════════
#  ManualAppointmentForm (کسب‌وکار)
# ═══════════════════════════════════════════════════════════════


class ManualAppointmentForm(forms.Form):
    """فرم ثبت نوبت دستی توسط کسب‌وکار."""

    customer_phone = forms.CharField(
        label=_("شماره موبایل مشتری"),
        max_length=15,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "09123456789",
                "dir": "ltr",
            }
        ),
    )
    customer_name = forms.CharField(
        label=_("نام مشتری"),
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": INPUT_CLASS, "placeholder": "مثلاً: محمد احمدی"}
        ),
    )

    service_id = forms.IntegerField(
        label=_("خدمت"),
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )

    start_at = forms.DateTimeField(
        label=_("تاریخ و ساعت"),
        widget=forms.DateTimeInput(
            attrs={"class": INPUT_CLASS, "type": "datetime-local"}
        ),
    )

    status = forms.ChoiceField(
        label=_("وضعیت"),
        choices=[
            ("confirmed", _("تأیید شده")),
            ("pending", _("در انتظار")),
        ],
        initial="confirmed",
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )

    customer_note = forms.CharField(
        label=_("یادداشت (اختیاری)"),
        required=False,
        max_length=500,
        widget=forms.Textarea(
            attrs={"class": TEXTAREA_CLASS, "rows": 2}
        ),
    )

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.business = business
        if business:
            services = business.services.filter(is_active=True).order_by("order", "name")
            self.fields["service_id"].widget = forms.Select(
                attrs={"class": INPUT_CLASS},
                choices=[(s.id, f"{s.name} — {s.duration} دقیقه") for s in services],
            )

    def clean_customer_phone(self) -> str:
        raw = self.cleaned_data["customer_phone"]
        normalized = normalize_phone(raw)
        if not normalized:
            raise forms.ValidationError(_("شماره موبایل نامعتبره."))
        return normalized

    def clean_start_at(self):
        start_at = self.cleaned_data["start_at"]
        if start_at < timezone.now():
            raise forms.ValidationError(_("نمی‌تونی برای زمان گذشته نوبت ثبت کنی."))
        return start_at