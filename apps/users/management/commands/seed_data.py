from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.availability.models import WorkingHour
from apps.bookings.models import Booking
from apps.services.models import Service
from apps.technicians.models import Technician, TechnicianService
from apps.users.models import User


class Command(BaseCommand):
    help = "Seed the database with demo users, services, technicians, schedules, and bookings."

    def handle(self, *args, **options):
        admin_user, _ = User.objects.get_or_create(
            email="admin@example.com",
            defaults={"first_name": "Admin", "last_name": "User", "is_staff": True, "is_active": True},
        )
        if not admin_user.has_usable_password():
            admin_user.set_password("admin12345")
            admin_user.save()

        services = [
            Service.objects.get_or_create(name="Laptop Diagnostics", defaults={"description": "Hardware and software check.", "duration_minutes": 60, "price": "100.00"})[0],
            Service.objects.get_or_create(name="Phone Screen Repair", defaults={"description": "Screen replacement and diagnostics.", "duration_minutes": 90, "price": "150.00"})[0],
            Service.objects.get_or_create(name="Tablet Battery Replacement", defaults={"description": "Battery replacement and test.", "duration_minutes": 45, "price": "90.00"})[0],
        ]

        technicians = []
        for index, email in enumerate(["ali@example.com", "nora@example.com", "sam@example.com"], start=1):
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={"first_name": "Tech", "last_name": f"User{index}", "is_active": True},
            )
            technician, _ = Technician.objects.get_or_create(user=user, defaults={"bio": "Repair specialist"})
            technicians.append(technician)

        for technician, service in zip(technicians, services):
            TechnicianService.objects.get_or_create(technician=technician, service=service)
            for weekday in range(0, 5):
                WorkingHour.objects.get_or_create(
                    technician=technician,
                    weekday=weekday,
                    start_time="09:00:00",
                    end_time="13:00:00",
                )
                WorkingHour.objects.get_or_create(
                    technician=technician,
                    weekday=weekday,
                    start_time="14:00:00",
                    end_time="18:00:00",
                )

        customer, _ = User.objects.get_or_create(
            email="customer@example.com",
            defaults={"first_name": "Demo", "last_name": "Customer", "is_active": True},
        )
        if not customer.has_usable_password():
            customer.set_password("customer123")
            customer.save()

        today = timezone.now()
        if not Booking.objects.exists():
            start = today.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
            Booking.objects.create(
                customer=customer,
                technician=technicians[0],
                service=services[0],
                start_datetime=start,
                end_datetime=start + timedelta(minutes=services[0].duration_minutes),
                status=Booking.Status.PENDING,
                price_at_booking=services[0].price,
                duration_at_booking=services[0].duration_minutes,
                customer_note="Demo booking",
            )

        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))
