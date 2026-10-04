"""
تست‌های CustomerBusinessService.
"""

import pytest

from apps.customers.models import CustomerBusiness
from apps.customers.services import CustomerBusinessService


@pytest.mark.django_db
class TestCustomerBusinessService:
    """تست‌های سرویس مشتری."""

    def test_add_to_my_list(self, customer, business):
        relation, created = CustomerBusinessService.add_to_my_list(customer, business)
        assert created is True
        assert relation.customer == customer
        assert relation.business == business

    def test_add_duplicate_returns_existing(self, customer, business):
        relation1, created1 = CustomerBusinessService.add_to_my_list(customer, business)
        relation2, created2 = CustomerBusinessService.add_to_my_list(customer, business)

        assert created1 is True
        assert created2 is False
        assert relation1.pk == relation2.pk

    def test_remove_from_my_list(self, customer, business):
        CustomerBusinessService.add_to_my_list(customer, business)
        deleted = CustomerBusinessService.remove_from_my_list(customer, business)
        assert deleted == 1
        assert not CustomerBusiness.objects.filter(customer=customer, business=business).exists()

    def test_record_visit(self, customer, business):
        relation = CustomerBusinessService.record_visit(customer, business)
        assert relation.visits_count == 1
        assert relation.first_visit_at is not None
        assert relation.last_visit_at is not None

        relation = CustomerBusinessService.record_visit(customer, business)
        assert relation.visits_count == 2

    def test_toggle_favorite(self, customer, business):
        relation = CustomerBusinessService.toggle_favorite(customer, business)
        assert relation.is_favorite is True

        relation = CustomerBusinessService.toggle_favorite(customer, business)
        assert relation.is_favorite is False