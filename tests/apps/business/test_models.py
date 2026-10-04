"""
تست‌های مدل‌های business.
"""

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.business.models import Business, Plan, Service, Staff, StaffSchedule


@pytest.mark.django_db
class TestPlanModel:
    """تست‌های Plan."""

    def test_create_plan(self, trial_plan):
        assert trial_plan.slug == "trial"
        assert trial_plan.is_paid is False

    def test_features_count(self, pro_plan):
        pro_plan.features = ["a", "b", "c"]
        assert pro_plan.features_count == 3

    def test_slug_unique(self, trial_plan):
        with pytest.raises(IntegrityError):
            Plan.objects.create(slug="trial", name="another")


@pytest.mark.django_db
class TestBusinessModel:
    """تست‌های Business."""

    def test_create_business(self, business):
        assert business.pk is not None
        assert business.owner is not None

    def test_slug_auto_generated(self, business):
        assert business.slug is not None
        assert len(business.slug) > 0

    def test_slug_unique(self, business, owner_user, trial_plan):
        # یه کسب‌وکار دیگه با همون نام
        owner2 = business.owner.__class__.objects.create_user(phone="09129999999")
        b2 = Business.objects.create(
            owner=owner2,
            target_audience=business.target_audience,
            activity_type=business.activity_type,
            name=business.name,
            region="test",
            address="test",
            plan=trial_plan,
        )
        assert b2.slug != business.slug

    def test_is_plan_active(self, business):
        assert business.is_plan_active is True

    def test_is_plan_expired(self, business):
        business.plan_expires_at = timezone.localdate() - timezone.timedelta(days=1)
        business.save()
        assert business.is_plan_active is False

    def test_has_pro_features_trial(self, business):
        assert business.has_pro_features is False

    def test_has_pro_features_pro(self, salon, pro_plan):
        salon.plan = pro_plan
        salon.plan_expires_at = timezone.localdate() + timezone.timedelta(days=30)
        salon.save()
        assert salon.has_pro_features is True

    def test_staff_count(self, business):
        # سیگنال خودکار یه Staff صاحب ساخته
        assert business.staff_count >= 1

    def test_public_url(self, business):
        assert business.public_url == f"/b/{business.slug}/"


@pytest.mark.django_db
class TestStaffSchedule:
    """تست‌های StaffSchedule."""

    def test_create_schedule(self, business, owner_staff, station):
        schedule = StaffSchedule.objects.create(
            staff=owner_staff,
            station=station,
            weekday=0,
            start_time="09:00",
            end_time="14:00",
        )
        assert schedule.pk is not None

    def test_unique_constraint(self, business, owner_staff, station):
        StaffSchedule.objects.create(
            staff=owner_staff,
            station=station,
            weekday=0,
            start_time="09:00",
            end_time="14:00",
        )
        with pytest.raises(IntegrityError):
            StaffSchedule.objects.create(
                staff=owner_staff,
                station=station,
                weekday=0,
                start_time="09:00",
                end_time="15:00",
            )


@pytest.mark.django_db
class TestService:
    """تست‌های Service."""

    def test_staff_count_from_staffservice(self, service):
        # service fixture یه StaffService ساخته
        assert service.staff_count == 1

    def test_price_display(self, service):
        assert "150" in service.price_display or "۱۵۰" in service.price_display