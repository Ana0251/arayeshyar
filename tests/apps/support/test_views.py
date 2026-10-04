"""
تست‌های views اپ support.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestNewTicket:
    """تست صفحه‌ی تیکت جدید."""

    def test_login_required(self, client):
        url = reverse("support:new_ticket")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url or "auth" in response.url

    def test_get_form(self, client, customer):
        client.force_login(customer)
        url = reverse("support:new_ticket")
        response = client.get(url)
        assert response.status_code == 200

    def test_create_ticket(self, client, customer):
        client.force_login(customer)
        url = reverse("support:new_ticket")
        response = client.post(
            url,
            {
                "subject": "مشکل تست",
                "category": "technical",
                "priority": "normal",
                "message": "این یه پیام تست هست",
            },
        )
        assert response.status_code == 302

        from apps.support.models import Ticket
        assert Ticket.objects.filter(user=customer, subject="مشکل تست").exists()


@pytest.mark.django_db
class TestMyTickets:
    """تست صفحه‌ی لیست تیکت‌ها."""

    def test_requires_login(self, client):
        url = reverse("support:my_tickets")
        response = client.get(url)
        assert response.status_code == 302

    def test_list_tickets(self, client, customer):
        from apps.support.models import Ticket

        Ticket.objects.create(user=customer, subject="تیکت ۱")
        Ticket.objects.create(user=customer, subject="تیکت ۲")

        client.force_login(customer)
        url = reverse("support:my_tickets")
        response = client.get(url)
        assert response.status_code == 200

        # ─── fix: encode به UTF-8 ───
        content = response.content.decode("utf-8")
        assert "تیکت ۱" in content
        assert "تیکت ۲" in content


@pytest.mark.django_db
class TestTicketDetail:
    """تست جزئیات تیکت."""

    def test_owner_can_view(self, client, customer):
        from apps.support.models import Ticket

        ticket = Ticket.objects.create(user=customer, subject="test")
        client.force_login(customer)

        url = reverse("support:ticket_detail", args=[ticket.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_other_user_cannot_view(self, client, customer, second_customer):
        from apps.support.models import Ticket

        ticket = Ticket.objects.create(user=customer, subject="test")
        client.force_login(second_customer)

        url = reverse("support:ticket_detail", args=[ticket.pk])
        response = client.get(url)
        assert response.status_code == 302  # redirect به my_tickets

    def test_reply_creates_message(self, client, customer):
        from apps.support.models import Ticket, TicketMessage

        ticket = Ticket.objects.create(user=customer, subject="test")
        client.force_login(customer)

        url = reverse("support:ticket_detail", args=[ticket.pk])
        response = client.post(url, {"message": "پاسخ من"})
        assert response.status_code == 302

        assert TicketMessage.objects.filter(
            ticket=ticket,
            user=customer,
            message="پاسخ من",
        ).exists()