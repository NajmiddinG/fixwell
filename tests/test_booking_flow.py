from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.bookings.models import Booking


@pytest.mark.django_db
class TestBookingFlow:
    def test_create_and_confirm_booking(self, api_client, customer_user, service, technician):
        api_client.force_authenticate(customer_user)
        slot = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        if slot <= timezone.now():
            slot += timedelta(days=7)
        payload = {
            "service_id": service.id,
            "technician_id": technician.id,
            "start_datetime": slot.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "customer_note": "Laptop not turning on.",
        }
        response = api_client.post("/api/bookings/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        booking = Booking.objects.get(id=response.data["id"])
        assert booking.status == Booking.Status.PENDING

        api_client.force_authenticate(user=None)
        admin_client = api_client.__class__()
        admin_user = customer_user.__class__.objects.create_user(
            email="admin2@example.com",
            password="StrongPass123!",
            first_name="Admin",
            last_name="Book",
            is_staff=True,
        )
        admin_client.force_authenticate(admin_user)
        response = admin_client.post(f"/api/bookings/{booking.id}/confirm/")
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED

    def test_conflicting_booking_is_rejected(self, api_client, customer_user, service, technician):
        slot = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        if slot <= timezone.now():
            slot += timedelta(days=7)
        payload = {
            "service_id": service.id,
            "technician_id": technician.id,
            "start_datetime": slot.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        api_client.force_authenticate(customer_user)
        first = api_client.post("/api/bookings/", payload, format="json")
        assert first.status_code == status.HTTP_201_CREATED

        second_customer = customer_user.__class__.objects.create_user(
            email="secondbuyer@example.com",
            password="StrongPass123!",
        )
        api_client.force_authenticate(second_customer)
        second = api_client.post("/api/bookings/", payload, format="json")
        assert second.status_code == status.HTTP_409_CONFLICT
        assert Booking.objects.filter(technician=technician).count() == 1
