"""
فرم‌های اپ support.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .constants import TicketCategory, TicketPriority
from .models import Ticket, TicketMessage


# ═══════════════════════════════════════════════════════════════
#  Classes
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

SELECT_CLASS = (
    "w-full px-4 py-3 rounded-xl border border-black/10 bg-white "
    "focus:border-accent focus:ring-2 focus:ring-accent/20 "
    "outline-none transition"
)


# ═══════════════════════════════════════════════════════════════
#  NewTicketForm
# ═══════════════════════════════════════════════════════════════


class NewTicketForm(forms.Form):
    """فرم ایجاد تیکت جدید."""

    subject = forms.CharField(
        label=_("موضوع"),
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "مثلاً: مشکل در ثبت نوبت",
            }
        ),
    )
    category = forms.ChoiceField(
        label=_("دسته"),
        choices=TicketCategory.choices,
        initial=TicketCategory.TECHNICAL,
        widget=forms.Select(attrs={"class": SELECT_CLASS}),
    )
    priority = forms.ChoiceField(
        label=_("اولویت"),
        choices=TicketPriority.choices,
        initial=TicketPriority.NORMAL,
        widget=forms.Select(attrs={"class": SELECT_CLASS}),
    )
    message = forms.CharField(
        label=_("متن پیام"),
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "class": TEXTAREA_CLASS,
                "rows": 6,
                "placeholder": "مشکل یا سوالت رو کامل توضیح بده...",
            }
        ),
    )
    attachment = forms.FileField(
        label=_("فایل پیوست (اختیاری)"),
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": INPUT_CLASS,
                "accept": "image/*,.pdf",
            }
        ),
    )

    def clean_attachment(self):
        """چک حجم فایل."""
        f = self.cleaned_data.get("attachment")
        if f and f.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                _("حجم فایل نباید بیشتر از ۵ مگابایت باشه.")
            )
        return f


# ═══════════════════════════════════════════════════════════════
#  TicketReplyForm
# ═══════════════════════════════════════════════════════════════


class TicketReplyForm(forms.Form):
    """فرم پاسخ توی تیکت."""

    message = forms.CharField(
        label=_("پاسخ"),
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "class": TEXTAREA_CLASS,
                "rows": 4,
                "placeholder": "پاسخت رو بنویس...",
            }
        ),
    )
    attachment = forms.FileField(
        label=_("فایل پیوست (اختیاری)"),
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": INPUT_CLASS,
                "accept": "image/*,.pdf",
            }
        ),
    )

    def clean_attachment(self):
        f = self.cleaned_data.get("attachment")
        if f and f.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                _("حجم فایل نباید بیشتر از ۵ مگابایت باشه.")
            )
        return f