"""
Converter های سفارشی URL.

برای پشتیبانی از slug فارسی.
"""

from django.urls.converters import StringConverter


class UnicodeSlugConverter(StringConverter):
    """
    Converter سفارشی برای slug با کاراکترهای یونیکد (فارسی).

    ─── الگو: ───
    \w شامل حروف یونیکد (فارسی) و اعداد و _ هست، به‌علاوه - .
    """

    regex = r"[\w-]+"


# ─── نمونه‌ها (برای register در urls.py) ───
# مسیر ثبت: apps.core.converters.UnicodeSlugConverter