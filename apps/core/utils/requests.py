"""
Helper های HTTP request.
"""

from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str | None:
    """
    گرفتن IP کاربر (پشت proxy هم کار می‌کنه).

    ─── چرا؟ ───
    توی production پشت nginx/Liara هستیم، پس REMOTE_ADDR
    IP پروکسی رو نشون میده. X-Forwarded-For درست‌تره.

    ─── امنیت: ───
    X-Forwarded-For می‌تونه spoof بشه اگه پروکسی غیرقابل اعتماد باشه.
    ولی برای rate limiting و لاگ، کافیه.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # اولین IP رو بگیر (چپ‌ترین = client اصلی)
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")