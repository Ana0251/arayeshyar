"""
تست Integration جریان ثبت‌نام کسب‌وکار.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestRegistrationFlow:
    """جریان ثبت‌نام."""

    def test_register_audience_requires_login(self, client):
        url = reverse("business:register_audience")
        response = client.get(url)
        assert response.status_code == 302

    def test_register_audience_page(self, client, customer):
        from tests.factories import TargetAudienceFactory

        TargetAudienceFactory(slug="men", name="آقایان")

        client.force_login(customer)
        url = reverse("business:register_audience")
        response = client.get(url)
        assert response.status_code == 200

    def test_full_registration_flow(self, client, customer, all_plans):
        """جریان کامل ثبت‌نام."""
        from tests.factories import ActivityTypeFactory, TargetAudienceFactory
        from apps.business.models import Business

        audience = TargetAudienceFactory(slug="men")
        activity = ActivityTypeFactory(slug="barber", is_salon=False)

        client.force_login(customer)

        # ۱. Audience
        response = client.post(
            reverse("business:register_audience"),
            {"audience_id": audience.pk},
        )
        assert response.status_code == 302

        # ۲. Salon type
        response = client.post(
            reverse("business:register_salon_type"),
            {"is_salon": "no"},
        )
        assert response.status_code == 302

        # ۳. Activity
        response = client.post(
            reverse("business:register_activity"),
            {"activity_id": activity.pk},
        )
        assert response.status_code == 302

        # ۴. Services (چون شخصی)
        response = client.post(
            reverse("business:register_services"),
            {
                "service_name[]": ["کوتاهی مو"],
                "service_duration[]": ["30"],
                "service_price[]": ["150000"],
            },
        )
        assert response.status_code == 302

        # ۵. Info
        response = client.post(
            reverse("business:register_info"),
            {
                "name": "کسب‌وکار تست",
                "owner_name": "تست",
                "region": "ونک",
                "address": "تست",
                "bio": "توضیحات",
            },
        )
        assert response.status_code == 302

        # ۶. Business ساخته شده
        assert Business.objects.filter(
            owner=customer,
            name="کسب‌وکار تست",
        ).exists()