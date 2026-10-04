"""
تست‌های selectors اپ support.
"""

import pytest

from apps.support.constants import TicketStatus
from apps.support.models import Ticket
from apps.support.selectors import (
    get_open_tickets_count,
    get_ticket_by_id,
    get_user_tickets,
)


@pytest.mark.django_db
class TestSelectors:
    """تست selectors."""

    def test_get_user_tickets(self, customer):
        Ticket.objects.create(user=customer, subject="1")
        Ticket.objects.create(user=customer, subject="2")
        tickets = get_user_tickets(customer)
        assert tickets.count() == 2

    def test_get_open_tickets_count(self, customer):
        Ticket.objects.create(user=customer, subject="1")
        t2 = Ticket.objects.create(user=customer, subject="2")
        t2.close()

        assert get_open_tickets_count(customer) == 1

    def test_get_ticket_by_id(self, customer):
        ticket = Ticket.objects.create(user=customer, subject="test")
        found = get_ticket_by_id(ticket.pk)
        assert found == ticket

    def test_get_ticket_by_id_not_found(self):
        assert get_ticket_by_id(99999) is None