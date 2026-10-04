"""
Fixtureهای مشترک pytest.
"""

from datetime import time, timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.accounts.constants import Role
from apps.business.models import (
    ActivityType,
    Business,
    Plan,
    Service,
    Staff,
    StaffSchedule,
    StaffService,
    Station,
    TargetAudience,
    WorkingHours,
)

from .factories import (
    ActivityTypeFactory,
    BusinessFactory,
    BusinessOwnerUserFactory,
    CustomerUserFactory,
    PlanFactory,
    ProPlanFactory,
    ServiceFactory,
    StaffFactory,
    StationFactory,
    TargetAudienceFactory,
    TrialPlanFactory,
)


# ═══════════════════════════════════════════════════════════════
#  Auto-use: پاک‌کردن cache
# ═══════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def clear_cache():
    """پاک‌کردن cache قبل و بعد از هر تست."""
    cache.clear()
    yield
    cache.clear()


# ═══════════════════════════════════════════════════════════════
#  Auto-use: غیرفعال‌کردن debug_toolbar
# ═══════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def disable_debug_toolbar(settings):
    """
    غیرفعال‌کردن debug_toolbar توی تست‌ها.

    ─── چرا؟ ───
    debug_toolbar middleware توی URLها دنبال namespace 'djdt' می‌گرده.
    توی تست، DEBUG=False میشه و URL 'djdt' ثبت نمیشه → خطا.
    این fixture middleware رو حذف می‌کنه.
    """
    settings.DEBUG = False
    settings.MIDDLEWARE = [
        m for m in settings.MIDDLEWARE
        if "debug_toolbar" not in m
    ]


# ═══════════════════════════════════════════════════════════════
#  Planها (خودکار)
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def trial_plan(db):
    """پلن trial."""
    return TrialPlanFactory()


@pytest.fixture
def basic_plan(db):
    """پلن basic."""
    return PlanFactory(slug="basic", name="پلن پایه", is_paid=True)


@pytest.fixture
def pro_plan(db):
    """پلن pro."""
    return ProPlanFactory()


@pytest.fixture
def all_plans(db, trial_plan, basic_plan, pro_plan):
    """همه‌ی پلن‌ها."""
    return {"trial": trial_plan, "basic": basic_plan, "pro": pro_plan}


# ═══════════════════════════════════════════════════════════════
#  Master Data
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def audience(db):
    """مخاطب."""
    return TargetAudienceFactory()


@pytest.fixture
def activity_type(db):
    """نوع فعالیت (شخصی)."""
    return ActivityTypeFactory(is_salon=False)


@pytest.fixture
def activity_salon(db):
    """نوع فعالیت (سالن)."""
    return ActivityTypeFactory(
        slug="beauty-salon",
        name="سالن زیبایی",
        is_salon=True,
    )


# ═══════════════════════════════════════════════════════════════
#  User
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def owner_user(db):
    """کاربر صاحب کسب‌وکار."""
    user = BusinessOwnerUserFactory(phone="09111111111")
    user.set_unusable_password()
    user.save()
    return user


@pytest.fixture
def customer(db):
    """مشتری."""
    user = CustomerUserFactory(phone="09190000001")
    user.set_unusable_password()
    user.save()

    profile = user.customer_profile
    profile.full_name = "زهرا تست"
    profile.save()

    return user


@pytest.fixture
def second_customer(db):
    """مشتری دوم."""
    user = CustomerUserFactory(phone="09190000002")
    user.set_unusable_password()
    user.save()

    profile = user.customer_profile
    profile.full_name = "فاطمه تست"
    profile.save()

    return user


# ═══════════════════════════════════════════════════════════════
#  Business
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def business(db, owner_user, trial_plan):
    """کسب‌وکار شخصی."""
    return BusinessFactory(
        owner=owner_user,
        plan=trial_plan,
        is_salon=False,
        name="آرایشگر تست",
    )


@pytest.fixture
def salon(db, trial_plan):
    """سالن زیبایی."""
    owner = BusinessOwnerUserFactory(phone="09122222222")
    owner.set_unusable_password()
    owner.save()

    salon = BusinessFactory(
        owner=owner,
        plan=trial_plan,
        is_salon=True,
        name="سالن تست",
        auto_confirm=False,
    )
    return salon


@pytest.fixture
def station(business):
    """ایستگاه پیش‌فرض کسب‌وکار شخصی."""
    station = Station.objects.filter(business=business).first()
    if not station:
        station = StationFactory(business=business, name="محل کار")
    return station


@pytest.fixture
def salon_station(salon):
    """ایستگاه سالن."""
    return StationFactory(business=salon, name="اتاق رنگ")


@pytest.fixture
def owner_staff(business):
    """Staff صاحب کسب‌وکار."""
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
def service(business, station, owner_staff, trial_plan):
    """خدمت نمونه."""
    svc = ServiceFactory(
        business=business,
        station=station,
        name="کوتاهی مو",
        duration=30,
        price=150_000,
    )
    StaffService.objects.get_or_create(
        staff=owner_staff,
        service=svc,
        station=station,
        defaults={"price": 0, "is_active": True},
    )
    return svc


@pytest.fixture
def service_with_working_hours(business, service, station):
    """خدمت + ساعت کاری (برای شخصی)."""
    for weekday in range(0, 5):
        WorkingHours.objects.get_or_create(
            business=business,
            station=None,
            weekday=weekday,
            defaults={
                "start_time": time(9, 0),
                "end_time": time(21, 0),
                "is_active": True,
            },
        )
    return service


# ═══════════════════════════════════════════════════════════════
#  تاریخ‌ها
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def tomorrow():
    """فردا."""
    return timezone.localdate() + timedelta(days=1)


@pytest.fixture
def next_saturday():
    """شنبه‌ی آینده."""
    today = timezone.localdate()
    days_ahead = (5 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


@pytest.fixture
def next_saturday_10am(next_saturday):
    """شنبه‌ی آینده ساعت ۱۰:۰۰ (aware)."""
    from datetime import datetime

    dt = datetime.combine(next_saturday, time(10, 0))
    return timezone.make_aware(dt, timezone.get_current_timezone())