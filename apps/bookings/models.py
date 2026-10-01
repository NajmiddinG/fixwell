from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.services.models import Service
from apps.technicians.models import Technician


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    technician = models.ForeignKey(Technician, on_delete=models.PROTECT, related_name="bookings")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="bookings")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    price_at_booking = models.DecimalField(max_digits=10, decimal_places=2)
    duration_at_booking = models.PositiveIntegerField()
    customer_note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "bookings"
        indexes = [
            models.Index(fields=["technician", "start_datetime"]),
            models.Index(fields=["status"]),
            models.Index(fields=["customer", "created_at"]),
        ]

    def __str__(self):
        return f"{self.customer.email} -> {self.technician} @ {self.start_datetime}"

    @classmethod
    def can_transition(cls, current, target):
        allowed = {
            cls.Status.PENDING: {cls.Status.CONFIRMED, cls.Status.CANCELLED},
            cls.Status.CONFIRMED: {cls.Status.COMPLETED, cls.Status.CANCELLED},
            cls.Status.CANCELLED: set(),
            cls.Status.COMPLETED: set(),
        }
        return target in allowed.get(current, set())

    def set_status(self, new_status):
        if not self.can_transition(self.status, new_status):
            raise ValueError("Invalid status transition.")
        self.status = new_status
        if new_status == self.Status.CANCELLED and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        elif new_status != self.Status.CANCELLED:
            self.cancelled_at = None
        self.save(update_fields=["status", "cancelled_at", "updated_at"])
