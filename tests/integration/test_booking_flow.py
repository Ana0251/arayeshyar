"""
تست Integration جریان رزرو نوبت.
"""

from datetime import time, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.booking.constants import AppointmentStatus
from apps.booking.models import Appointment
from apps.customers.models import CustomerBusiness


@pytest.mark.django_db
class TestBookingFlow:
    """جریان کامل رزرو."""

    def test_full_booking_flow_personal(
        self,
        client,
        customer,
        business,
        service_with_working_hours,
        next_saturday,
    ):
        """رزرو در کسب‌وکار شخصی."""
        client.force_login(customer)

        # ۱. صفحه رزرو
        url = reverse("booking:book", args=[business.slug])
        response = client.get(url, {"service": service_with_working_hours.pk, "date": next_saturday.isoformat()})
        assert response.status_code == 200

        # ۲. ثبت نوبت
        start = timezone.make_aware(
            timezone.datetime.combine(next_saturday, time(10, 0)),
            timezone.get_current_timezone(),
        )
        response = client.post(
            url,
            {
                "service_id": service_with_working_hours.pk,
                "start_at": start.isoformat(),
                "customer_name": "زهرا تست",
                "customer_phone": customer.phone,
                "customer_note": "تست",
            },
        )
        assert response.status_code == 302

        # ۳. نوبت ساخته شده
        assert Appointment.objects.filter(
            business=business,
            customer=customer,
        ).exists()

        # ۴. customer به لیست اضافه شده
        assert CustomerBusiness.objects.filter(
            customer=customer,
            business=business,
        ).exists()

    def test_booking_creates_customer_business_relation(
        self,
        client,
        customer,
        business,
        service_with_working_hours,
        next_saturday,
    ):
        """رزرو → customer_business relation."""
        client.force_login(customer)

        assert not CustomerBusiness.objects.filter(
            customer=customer, business=business
        ).exists()

        url = reverse("booking:book", args=[business.slug])
        start = timezone.make_aware(
            timezone.datetime.combine(next_saturday, time(11, 0)),
            timezone.get_current_timezone(),
        )
        client.post(url, {
            "service_id": service_with_working_hours.pk,
            "start_at": start.isoformat(),
            "customer_name": "زهرا",
            "customer_phone": customer.phone,
        })

        assert CustomerBusiness.objects.filter(
            customer=customer, business=business
        ).exists()