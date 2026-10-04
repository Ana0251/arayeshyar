"""
Factory Boy factories برای تست‌ها.
"""

import factory
from django.utils import timezone

from apps.accounts.constants import Role
from apps.accounts.models import User
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


# ═══════════════════════════════════════════════════════════════
#  User
# ═══════════════════════════════════════════════════════════════


class UserFactory(factory.django.DjangoModelFactory):
    """User factory."""

    class Meta:
        model = User
        django_get_or_create = ("phone",)

    phone = factory.Sequence(lambda n: f"0912000{n:04d}")
    role = Role.CUSTOMER
    is_active = True


class CustomerUserFactory(UserFactory):
    """مشتری."""

    role = Role.CUSTOMER


class BusinessOwnerUserFactory(UserFactory):
    """صاحب کسب‌وکار."""

    role = Role.BUSINESS_OWNER


# ═══════════════════════════════════════════════════════════════
#  Business
# ═══════════════════════════════════════════════════════════════


class TargetAudienceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TargetAudience

    slug = factory.Sequence(lambda n: f"audience-{n}")
    name = "آقایان"
    icon = "👨"
    order = 1
    is_active = True


class ActivityTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActivityType

    slug = factory.Sequence(lambda n: f"activity-{n}")
    name = "آرایشگر"
    icon = "💈"
    is_salon = False
    order = 1
    is_active = True


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Plan
        django_get_or_create = ("slug",)

    slug = factory.Sequence(lambda n: f"plan-{n}")
    name = "پلن پایه"
    icon = "⭐"
    price = 500_000
    duration_days = 30
    features = ["نوبت‌دهی آنلاین"]
    order = 1
    is_active = True
    is_paid = True
    has_pro_features = False


class TrialPlanFactory(PlanFactory):
    slug = "trial"
    name = "دوره تست"
    icon = "🎁"
    price = 0
    is_paid = False


class ProPlanFactory(PlanFactory):
    slug = "pro"
    name = "پلن ویژه"
    icon = "💎"
    price = 1_200_000
    has_pro_features = True


class BusinessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Business

    owner = factory.SubFactory(BusinessOwnerUserFactory)
    target_audience = factory.SubFactory(TargetAudienceFactory)
    activity_type = factory.SubFactory(ActivityTypeFactory)
    is_salon = False
    name = factory.Sequence(lambda n: f"کسب‌وکار {n}")
    owner_name = "علی رضایی"
    region = "ونک"
    address = "خیابان تست"
    plan = factory.SubFactory(TrialPlanFactory)
    plan_expires_at = factory.LazyFunction(
        lambda: timezone.localdate() + timezone.timedelta(days=30)
    )
    is_active = True
    auto_confirm = True


class StationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Station

    business = factory.SubFactory(BusinessFactory)
    name = factory.Sequence(lambda n: f"ایستگاه {n}")
    order = 1
    is_active = True


class StaffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Staff

    business = factory.SubFactory(BusinessFactory)
    name = factory.Sequence(lambda n: f"کارمند {n}")
    phone = factory.Sequence(lambda n: f"0913000{n:04d}")
    is_owner = False
    is_active = True
    order = 1


class ServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Service

    business = factory.SubFactory(BusinessFactory)
    station = factory.SubFactory(StationFactory)
    name = factory.Sequence(lambda n: f"خدمت {n}")
    duration = 30
    price = 100_000
    is_active = True
    order = 1