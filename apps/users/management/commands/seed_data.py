from django.core.management.base import BaseCommand

from apps.availability.models import WorkingHour
from apps.services.models import Service
from apps.technicians.models import Technician, TechnicianService
from apps.users.models import User


SERVICES = [
    ("Laptop Diagnostics", "Hardware and software troubleshooting.", 60, "100.00"),
    ("Phone Screen Repair", "Screen replacement and diagnostics.", 90, "150.00"),
    ("Tablet Battery Replacement", "Battery replacement and testing.", 45, "90.00"),
    ("Laptop Battery Replacement", "Laptop battery replacement and health check.", 60, "120.00"),
    ("Charging Port Repair", "Repair or replacement of charging ports.", 75, "110.00"),
    ("Water Damage Assessment", "Device inspection and liquid damage treatment.", 90, "130.00"),
    ("Data Recovery", "Attempted recovery of data from faulty devices.", 120, "180.00"),
    ("Console Repair", "Diagnosis and repair of game consoles.", 90, "140.00"),
    ("Desktop PC Repair", "Desktop computer diagnostics and repair.", 90, "125.00"),
    ("Software Installation", "Operating system and software setup.", 60, "80.00"),
]

TECHNICIANS = [
    ("ali@example.com", "Ali", "Karimov", "Computer and device repair specialist."),
    ("nora@example.com", "Nora", "Yusupova", "Mobile device and screen repair specialist."),
    ("sam@example.com", "Sam", "User", "Experienced electronics repair specialist."),
    ("dilshod@example.com", "Dilshod", "Rasulov", "Laptop and desktop hardware technician."),
    ("madina@example.com", "Madina", "Tursunova", "Mobile device diagnostics technician."),
    ("aziz@example.com", "Aziz", "Saidov", "Console and computer repair specialist."),
    ("malika@example.com", "Malika", "Nazarova", "Data recovery and software technician."),
    ("bekzod@example.com", "Bekzod", "Rahimov", "Board-level electronics repair technician."),
    ("sara@example.com", "Sara", "Ismailova", "Tablet and phone repair specialist."),
    ("jamshid@example.com", "Jamshid", "Usmonov", "Diagnostics and general repair technician."),
]


class Command(BaseCommand):
    help = "Create the standard services, technicians, service assignments, and work schedules."

    def handle(self, *args, **options):
        services = []
        for name, description, duration, price in SERVICES:
            service, _ = Service.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "duration_minutes": duration,
                    "price": price,
                },
            )
            services.append(service)

        technicians = []
        for email, first_name, last_name, bio in TECHNICIANS:
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_active": True,
                },
            )
            technician, _ = Technician.objects.get_or_create(
                user=user,
                defaults={"bio": bio, "is_active": True},
            )
            technicians.append(technician)

        for index, technician in enumerate(technicians):
            for offset in range(3):
                service = services[(index + offset) % len(services)]
                TechnicianService.objects.get_or_create(
                    technician=technician,
                    service=service,
                )

            for weekday in range(5):
                for start_time, end_time in (("09:00:00", "13:00:00"), ("14:00:00", "18:00:00")):
                    WorkingHour.objects.get_or_create(
                        technician=technician,
                        weekday=weekday,
                        start_time=start_time,
                        end_time=end_time,
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Ensured {len(services)} services, {len(technicians)} technicians, "
                "their service assignments, and weekday schedules."
            )
        )