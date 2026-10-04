"""
تست‌های signals business.
"""

import pytest
from django.utils import timezone

from apps.accounts.constants import Role
from apps.accounts.models import BusinessOwnerProfile
from apps.business.models import Business, Staff, Station


@pytest.mark.django_db
class TestBusinessSignals:
    """تست‌های سیگنال‌ها."""

    def test_owner_role_updated(self, owner_user, trial_plan):
        # قبل: BUSINESS_OWNER
        assert owner_user.role == Role.BUSINESS_OWNER

    def test_business_owner_profile_created(self, business):
        assert BusinessOwnerProfile.objects.filter(user=business.owner).exists()

    def test_owner_staff_created(self, business):
        assert business.staff.filter(is_owner=True).exists()

    def test_default_station_created_for_personal(self, business):
        # کسب‌وکار شخصی → Station «محل کار»
        assert business.stations.filter(name="محل کار").exists()

    def test_no_default_station_for_salon(self, salon):
        # سالن → نباید Station «محل کار» بسازه
        assert not salon.stations.filter(name="محل کار").exists()

    def test_trial_expires_set(self, business):
        assert business.plan_expires_at is not None
        assert business.plan_expires_at >= timezone.localdate()