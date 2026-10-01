import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create an admin superuser if one does not already exist"

    def handle(self, *args, **options):
        User = get_user_model()

        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD "
                    "are not configured."
                )
            )
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f"Superuser '{email}' already exists."
                )
            )
            return

        User.objects.create_superuser(
            email=email,
            password=password,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Superuser '{email}' created successfully."
            )
        )
