"""
تست Integration جریان تیکت.
"""

import pytest
from django.urls import reverse

from apps.support.constants import TicketStatus
from apps.support.models import Ticket, TicketMessage


@pytest.mark.django_db
class TestSupportFlow:
    """جریان کامل تیکت."""

    def test_full_ticket_flow(self, client, customer):
        """ایجاد تیکت → پاسخ → بستن."""
        client.force_login(customer)

        # ۱. ساخت تیکت
        url = reverse("support:new_ticket")
        response = client.post(url, {
            "subject": "مشکل تست",
            "category": "technical",
            "priority": "high",
            "message": "متن مشکل",
        })
        assert response.status_code == 302

        ticket = Ticket.objects.get(user=customer, subject="مشکل تست")
        assert ticket.status == TicketStatus.OPEN
        assert ticket.messages_count == 1

        # ۲. پاسخ کاربر
        detail_url = reverse("support:ticket_detail", args=[ticket.pk])
        client.post(detail_url, {"message": "پاسخ کاربر"})

        assert TicketMessage.objects.filter(
            ticket=ticket, message="پاسخ کاربر"
        ).exists()

        # ۳. بستن
        close_url = reverse("support:close_ticket", args=[ticket.pk])
        client.post(close_url)

        ticket.refresh_from_db()
        assert ticket.status == TicketStatus.CLOSED