from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.bookings.models import Booking
from apps.bookings.services.booking import BookingValidationError, create_booking

User = get_user_model()


@pytest.mark.django_db(transaction=True)
def test_concurrent_booking_requests_only_create_one_booking(service, technician):
    slot = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
    if slot <= timezone.now():
        slot += timedelta(days=7)

    customer_one = User.objects.create_user(email="buyer1@example.com", password="StrongPass123!")
    customer_two = User.objects.create_user(email="buyer2@example.com", password="StrongPass123!")

    first = create_booking(customer=customer_one, service=service, technician=technician, start_datetime=slot)
    assert first.status == Booking.Status.PENDING

    with pytest.raises(BookingValidationError):
        create_booking(customer=customer_two, service=service, technician=technician, start_datetime=slot)

    assert Booking.objects.filter(technician=technician).count() == 1
