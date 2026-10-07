مرحله 4B-1 — ورود ایمیلی

1) فایل‌ها را با همان مسیر جایگزین کنید.
2) سپس اجرا کنید:
   python manage.py migrate
   python manage.py check
   python manage.py runserver

در محیط Development ایمیل OTP در ترمینال چاپ می‌شود (ConsoleEmailBackend).
برای Production متغیرهای SMTP را در .env تنظیم کنید:
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=

نکته مهم: ورود قدیمی با موبایل موقتاً در /accounts/login/phone/ باقی مانده تا حساب‌های قدیمی قفل نشوند.
بعد از اینکه ایمیل حساب‌های قدیمی ثبت شد، مسیر پیامکی ورود را حذف می‌کنیم و SMS فقط برای اعلان‌ها می‌ماند.
