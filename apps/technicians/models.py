from django.conf import settings
from django.db import models


class Technician(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    services = models.ManyToManyField(
        "services.Service",
        through="TechnicianService",
        blank=True,
        related_name="technicians",
    )

    class Meta:
        db_table = "technicians"
        indexes = [models.Index(fields=["is_active"]) ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}"


class TechnicianService(models.Model):
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name="technician_services")
    service = models.ForeignKey("services.Service", on_delete=models.CASCADE, related_name="technician_services")

    class Meta:
        db_table = "technician_services"
        constraints = [
            models.UniqueConstraint(fields=["technician", "service"], name="unique_technician_service"),
        ]

    def __str__(self):
        return f"{self.technician} -> {self.service}"
