"""
Fixtureهای مشترک pytest.

─── نکته: ───
همه‌ی fixtureها اینجا تعریف میشن تا توی تست‌های مختلف قابل استفاده باشن.
"""

from datetime import time

import pytest
from django.utils import timezone
from django.core.cache import cache
from apps.accounts.constants import Role
from apps.accounts.models import User
from apps.business.constants import Plan
from apps.business.models import (
    ActivityType,
    Business,
    Service,
    Staff,
    Station,
    TargetAudience,
    WorkingHours,
)


# ═══════════════════════════════════════════════════════════════
#  Fixtureهای پایه (Master Data)
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def audience(db):
    """TargetAudience نمونه."""
    return TargetAudience.objects.create(
        slug="men",
        name="آقایان",
        icon="👨",
        order=1,
    )


@pytest.fixture
def activity_type(db):
    """ActivityType نمونه (شخصی)."""
    return ActivityType.objects.create(
        slug="barber",
        name="آرایشگر مردانه",
        icon="💈",
        is_salon=False,
        order=1,
    )


@pytest.fixture
def activity_salon(db):
    """ActivityType نمونه (سالن)."""
    return ActivityType.objects.create(
        slug="beauty-salon",
        name="سالن زیبایی",
        icon="🏢",
        is_salon=True,
        order=1,
    )


# ═══════════════════════════════════════════════════════════════
#  Fixtureهای Business
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def owner_user(db):
    """کاربر صاحب کسب‌وکار."""
    user = User.objects.create_user(
        phone="09111111111",
        role=Role.BUSINESS_OWNER,
    )
    return user


@pytest.fixture
def business(owner_user, audience, activity_type):
    """کسب‌وکار شخصی با تنظیمات پایه."""
    business = Business.objects.create(
        owner=owner_user,
        target_audience=audience,
        activity_type=activity_type,
        is_salon=False,
        name="آرایشگر تست",
        owner_name="علی تست",
        region="ونک",
        address="خیابان تست، پلاک ۱",
        plan=Plan.TRIAL,
        is_active=True,
        auto_confirm=True,
    )
    return business


@pytest.fixture
def business_with_hours(business):
    """کسب‌وکار با برنامه هفتگی (شنبه تا چهارشنبه، ۹-۲۱)."""
    for weekday in range(0, 5):  # شنبه تا چهارشنبه
        WorkingHours.objects.create(
            business=business,
            station=None,
            weekday=weekday,
            start_time=time(9, 0),
            end_time=time(21, 0),
            is_active=True,
        )
    return business


@pytest.fixture
def station(business):
    """
    ایستگاه پیش‌فرض.

    ─── نکته: ───
    سیگنال `on_business_created` خودکار Station با نام «محل کار» می‌سازه.
    پس اینجا از get_or_create استفاده می‌کنیم تا تکراری نشه.
    """
    station, _ = Station.objects.get_or_create(
        business=business,
        name="محل کار",
        defaults={
            "order": 0,
            "is_active": True,
        },
    )
    return station


@pytest.fixture
def owner_staff(business):
    """Staff صاحب (خودکار ساخته میشه، ولی اینجا صریح)."""
    staff, _ = Staff.objects.get_or_create(
        business=business,
        is_owner=True,
        defaults={
            "name": business.owner_name,
            "phone": business.owner.phone,
        },
    )
    return staff


@pytest.fixture
def service(business, station, owner_staff):
    """خدمت نمونه (کوتاهی مو، ۳۰ دقیقه)."""
    svc = Service.objects.create(
        business=business,
        station=station,
        name="کوتاهی مو",
        duration=30,
        price=150_000,
        is_active=True,
        order=0,
    )
    svc.staff_members.add(owner_staff)
    return svc


# ═══════════════════════════════════════════════════════════════
#  Fixtureهای Customer
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def customer(db):
    """کاربر مشتری."""
    user = User.objects.create_user(
        phone="09190000001",
        role=Role.CUSTOMER,
    )
    # ─── نام کامل ───
    profile = user.customer_profile
    profile.full_name = "زهرا تست"
    profile.save()
    return user


# ═══════════════════════════════════════════════════════════════
#  Fixtureهای تاریخ
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def tomorrow():
    """فردا (localdate)."""
    return timezone.localdate() + timezone.timedelta(days=1)


@pytest.fixture
def next_saturday():
    """
    شنبه‌ی آینده (روز تعطیل رسمی ایرانی نیست).

    ─── نکته: ───
    اگه امروز شنبه باشه، ۷ روز جلوتر میره.
    """
    today = timezone.localdate()
    # ─── شنبه=۵ توی Python weekday() ───
    days_ahead = (5 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timezone.timedelta(days=days_ahead)

# ═══════════════════════════════════════════════════════════════
#  Fixtureهای Cache (پاک‌کردن بین تست‌ها)
# ═══════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def clear_cache():
    """
    پاک‌کردن cache قبل و بعد از هر تست.

    ─── چرا؟ ───
    LocMemCache بین تست‌ها persist می‌کنه، و OTP rate limit
    و cooldown باعث fail شدن تست‌های بعدی میشن.

    ─── autouse=True: ───
    خودکار برای همه‌ی تست‌ها اجرا میشه.
    """
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()
    
    