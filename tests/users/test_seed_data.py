import pytest
from django.core.management import call_command

from apps.availability.models import WorkingHour
from apps.bookings.models import Booking
from apps.services.models import Service
from apps.technicians.models import Technician, TechnicianService
from apps.users.models import User


@pytest.mark.django_db
def test_seed_data_is_repeatable_and_creates_related_records():
    call_command("seed_data")
    call_command("seed_data")

    assert Service.objects.count() == 10
    assert User.objects.count() == 10
    assert Technician.objects.count() == 10
    assert TechnicianService.objects.count() == 30
    assert WorkingHour.objects.count() == 100
    assert Booking.objects.count() == 0