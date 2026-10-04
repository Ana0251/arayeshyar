"""
تست‌های مدل‌های support.
"""

import pytest

from apps.support.constants import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from apps.support.models import Ticket, TicketMessage


@pytest.mark.django_db
class TestTicketModel:
    """تست‌های Ticket."""

    def test_create_ticket(self, customer):
        ticket = Ticket.objects.create(
            user=customer,
            subject="مشکل تست",
            category=TicketCategory.TECHNICAL,
            priority=TicketPriority.NORMAL,
        )
        assert ticket.pk is not None
        assert ticket.status == TicketStatus.OPEN
        assert ticket.is_open is True
        assert ticket.is_closed is False

    def test_close_ticket(self, customer):
        ticket = Ticket.objects.create(
            user=customer,
            subject="test",
        )
        ticket.close()
        assert ticket.status == TicketStatus.CLOSED
        assert ticket.closed_at is not None
        assert ticket.is_closed is True

    def test_reopen_ticket(self, customer):
        ticket = Ticket.objects.create(user=customer, subject="test")
        ticket.close()
        ticket.reopen()
        assert ticket.status == TicketStatus.OPEN
        assert ticket.closed_at is None

    def test_messages_count(self, customer):
        ticket = Ticket.objects.create(user=customer, subject="test")
        assert ticket.messages_count == 0

        TicketMessage.objects.create(
            ticket=ticket,
            user=customer,
            message="پیام ۱",
        )
        assert ticket.messages_count == 1


@pytest.mark.django_db
class TestTicketMessage:
    """تست‌های TicketMessage."""

    def test_message_updates_last_reply_at(self, customer):
        ticket = Ticket.objects.create(user=customer, subject="test")
        assert ticket.last_reply_at is None

        TicketMessage.objects.create(
            ticket=ticket,
            user=customer,
            message="پیام تست",
        )
        ticket.refresh_from_db()
        assert ticket.last_reply_at is not None