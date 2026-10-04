"""
تست‌های مدل User + پروفایل‌ها.
"""

import pytest
from django.db import IntegrityError

from apps.accounts.constants import Role
from apps.accounts.models import CustomerProfile, User
from apps.core.utils.phone import normalize_phone


@pytest.mark.django_db
class TestUserModel:
    """تست‌های User."""

    def test_create_user_with_phone(self):
        user = User.objects.create_user(phone="09123456789")
        assert user.phone == "09123456789"
        assert user.is_active is True
        assert user.role == Role.CUSTOMER
        assert user.check_password(None) is False

    def test_create_user_normalizes_phone(self):
        user = User.objects.create_user(phone="+989123456789")
        assert user.phone == "09123456789"

    def test_create_user_invalid_phone_raises(self):
        with pytest.raises(ValueError):
            User.objects.create_user(phone="invalid")

    def test_create_superuser_role_admin(self):
        user = User.objects.create_superuser(
            phone="09120000000",
            password="test123!",
        )
        assert user.role == Role.ADMIN
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_phone_unique(self):
        User.objects.create_user(phone="09123456789")
        with pytest.raises(IntegrityError):
            User.objects.create_user(phone="09123456789")

    def test_is_customer_property(self, customer):
        assert customer.is_customer is True
        assert customer.is_business_owner is False
        assert customer.is_platform_admin is False

    def test_is_business_owner_property(self, owner_user):
        assert owner_user.is_business_owner is True
        assert owner_user.is_customer is False

    def test_display_name_from_profile(self, customer):
        assert customer.display_name == "زهرا تست"

    def test_display_name_fallback_to_phone(self):
        user = User.objects.create_user(phone="09120000001")
        assert user.display_name == "09120000001"


@pytest.mark.django_db
class TestCustomerProfileAutoCreate:
    """تست سیگنال ساخت خودکار پروفایل."""

    def test_customer_profile_created_on_user_create(self):
        user = User.objects.create_user(phone="09120000002", role=Role.CUSTOMER)
        assert hasattr(user, "customer_profile")
        assert user.customer_profile is not None

    def test_business_owner_profile_created(self):
        user = User.objects.create_user(phone="09120000003", role=Role.BUSINESS_OWNER)
        assert hasattr(user, "business_owner_profile")