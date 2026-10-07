مرحله 10 — بازیابی رمز + SEO + وبلاگ

قابلیت‌ها:
- لینک «رمز عبورت رو فراموش کردی؟» در صفحه ورود
- ثبت درخواست بازیابی بدون لاگین و بدون OTP
- مدیریت درخواست‌ها در /control/password-requests/
- امکان تعیین رمز جدید از پنل کنترل فعلی
- اپ وبلاگ با لیست و صفحه مقاله
- مدیریت مقاله از /control/blog/
- Draft / Published، تصویر شاخص، دسته، خلاصه، Meta title/description، keywords
- sitemap.xml پویا برای خانه، وبلاگ، پروفایل کسب‌وکارها و مقالات
- robots.txt
- noindex برای صفحات خصوصی/مدیریتی و رزرو
- Meta description / Canonical / OpenGraph / Twitter card
- Schema.org برای پروفایل سالن/آرایشگر و Article برای وبلاگ
- hook برای Google Search Console با GOOGLE_SITE_VERIFICATION در .env

نصب:
1) فایل‌ها را با همان مسیر روی پروژه جایگزین کنید.
2) اجرا کنید:
   python manage.py migrate
   python manage.py check
   python manage.py runserver

مسیرهای تست:
- /support/password-help/
- /control/password-requests/
- /blog/
- /control/blog/
- /sitemap.xml
- /robots.txt

Search Console:
بعد از اینکه دامنه واقعی بالا آمد، مقدار verification را در .env بگذارید:
GOOGLE_SITE_VERIFICATION=...
سپس سایت را در Google Search Console ثبت و sitemap.xml را معرفی کنید.
