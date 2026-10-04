"""
تست‌های UserManager.
"""

import pytest

from apps.accounts.constants import Role
from apps.accounts.models import User


@pytest.mark.django_db
class TestUserManager:
    """تست‌های UserManager."""

    def test_create_user_default_role(self):
        user = User.objects.create_user(phone="09123456789")
        assert user.role == Role.CUSTOMER

    def test_create_user_custom_role(self):
        user = User.objects.create_user(
            phone="09123456789",
            role=Role.BUSINESS_OWNER,
        )
        assert user.role == Role.BUSINESS_OWNER

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            phone="09123456789",
            password="test123!",
        )
        assert user.role == Role.ADMIN
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_create_superuser_requires_staff(self):
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                phone="09123456789",
                password="test123!",
                is_staff=False,
            )

    def test_get_by_phone(self):
        User.objects.create_user(phone="09123456789")
        found = User.objects.get_by_phone("+989123456789")
        assert found is not None
        assert found.phone == "09123456789"

    def test_get_by_phone_not_found(self):
        assert User.objects.get_by_phone("09120000000") is None

    def test_get_by_phone_invalid(self):
        assert User.objects.get_by_phone("invalid") is None