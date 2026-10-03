"""
Custom widgets برای فرم‌های Django.

شامل:
- JalaliDateInput: DateInput با Persian Datepicker Element
- JalaliTimeInput: TimeInput با dropdown ساعت + دقیقه
"""

from django import forms


class JalaliDateInput(forms.DateInput):
    """
    DateInput با Persian Datepicker Element.

    ─── رفتار: ───
    - input نوع text میشه
    - JS یه Web Component کنارش می‌سازه
    - کاربر تقویم شمسی می‌بینه
    - مقدار ارسالی به backend: میلادی (Y-m-d)
    """

    input_type = "text"

    DEFAULT_ATTRS = {
        "data-persian-datepicker": "true",
        "autocomplete": "off",
        # ─── class حذف شد (date-picker.js خودش input رو مخفی می‌کنه) ───
    }

    def __init__(self, attrs=None, format=None):
        final_attrs = {**self.DEFAULT_ATTRS}
        if attrs:
            final_attrs.update(attrs)
        super().__init__(attrs=final_attrs, format=format or "%Y-%m-%d")


class JalaliTimeInput(forms.TimeInput):
    """
    TimeInput با dropdown ساعت + دقیقه.
    """

    input_type = "time"

    DEFAULT_ATTRS = {
        "data-time-picker": "true",
        # ─── class حذف شد (time-picker.js خودش input رو مخفی می‌کنه) ───
    }

    def __init__(self, attrs=None, format=None):
        final_attrs = {**self.DEFAULT_ATTRS}
        if attrs:
            final_attrs.update(attrs)
        super().__init__(attrs=final_attrs, format=format or "%H:%M")

    def get_context(self, name, value, attrs):
        """name رو توی data-name ذخیره کن."""
        context = super().get_context(name, value, attrs)
        context["widget"]["attrs"]["data-name"] = name
        return context