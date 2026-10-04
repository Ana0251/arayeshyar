"""
Data migration — پر کردن جدول Plan با مقادیر اولیه.

─── چرا؟ ───
مدل Plan تازه ساخته شده و خالیه. این migration داده‌های
trial, basic, pro رو به عنوان رکورد اضافه می‌کنه.
"""

from django.db import migrations


# ═══════════════════════════════════════════════════════════════
#  داده‌های اولیه
# ═══════════════════════════════════════════════════════════════

PLANS_DATA = [
    {
        "slug": "trial",
        "name": "دوره تست",
        "icon": "🎁",
        "description": "دوره‌ی تست ۳۰ روزه رایگان",
        "price": 0,
        "duration_days": 30,
        "features": [
            "همه‌ی امکانات پایه",
            "۳۰ روز رایگان",
        ],
        "order": 1,
        "is_active": True,
        "is_paid": False,
        "has_pro_features": False,
    },
    {
        "slug": "basic",
        "name": "پلن پایه",
        "icon": "⭐",
        "description": "پلن اقتصادی برای شروع",
        "price": 500_000,
        "duration_days": 30,
        "features": [
            "نوبت‌دهی آنلاین",
            "لینک اختصاصی + QR Code",
            "پنل کسب‌وکار",
            "مدیریت خدمات و ایستگاه‌ها",
            "برنامه هفتگی",
        ],
        "order": 2,
        "is_active": True,
        "is_paid": True,
        "has_pro_features": False,
    },
    {
        "slug": "pro",
        "name": "پلن ویژه",
        "icon": "💎",
        "description": "پلن حرفه‌ای با همه‌ی امکانات",
        "price": 1_200_000,
        "duration_days": 30,
        "features": [
            "همه‌ی امکانات پایه",
            "یادآور پیامکی",
            "لیست انتظار هوشمند",
            "گزارش درآمد",
            "ساعات طلایی",
            "مشتریان خواب‌رفته",
            "نوبت‌های تکراری",
        ],
        "order": 3,
        "is_active": True,
        "is_paid": True,
        "has_pro_features": True,
    },
]


def create_plans(apps, schema_editor):
    """ساخت پلن‌های اولیه."""
    Plan = apps.get_model("business", "Plan")

    for data in PLANS_DATA:
        Plan.objects.update_or_create(
            slug=data["slug"],
            defaults=data,
        )


def delete_plans(apps, schema_editor):
    """حذف پلن‌ها (برای rollback)."""
    Plan = apps.get_model("business", "Plan")
    Plan.objects.filter(
        slug__in=[p["slug"] for p in PLANS_DATA]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("business", "0004_add_plan_model"),
    ]

    operations = [
        migrations.RunPython(create_plans, delete_plans),
    ]