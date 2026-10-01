import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.availability.models import WorkingHour
from apps.services.models import Service
from apps.technicians.models import Technician, TechnicianService

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@example.com",
        password="StrongPass123!",
        first_name="Admin",
        last_name="User",
        is_staff=True,
    )


@pytest.fixture
def customer_user(db):
    return User.objects.create_user(
        email="customer@example.com",
        password="StrongPass123!",
        first_name="Customer",
        last_name="User",
    )


@pytest.fixture
def service(db):
    return Service.objects.create(
        name="Laptop Diagnostics",
        description="Check laptop hardware and software issues.",
        duration_minutes=60,
        price="100.00",
        is_active=True,
    )


@pytest.fixture
def technician(db, service):
    tech_user = User.objects.create_user(
        email="ali@example.com",
        password="StrongPass123!",
        first_name="Ali",
        last_name="Karimov",
    )
    weekday = timezone.now().weekday()
    technician = Technician.objects.create(user=tech_user, bio="Experienced technician")
    TechnicianService.objects.create(technician=technician, service=service)
    WorkingHour.objects.create(technician=technician, weekday=weekday, start_time="09:00:00", end_time="13:00:00")
    WorkingHour.objects.create(technician=technician, weekday=weekday, start_time="14:00:00", end_time="18:00:00")
    return technician
