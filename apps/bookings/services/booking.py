import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.availability.models import Unavailability, WorkingHour
from apps.bookings.models import Booking


class BookingValidationError(ValueError):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


def _localize(dt):
    return timezone.make_aware(dt, timezone=ZoneInfo(getattr(settings, "TIME_ZONE", "UTC")))


def _is_within_working_hours(technician, start_dt, end_dt):
    weekday = start_dt.weekday()
    intervals = WorkingHour.objects.filter(technician=technician, weekday=weekday)
    for interval in intervals:
        window_start = _localize(datetime.datetime.combine(start_dt.date(), interval.start_time))
        window_end = _localize(datetime.datetime.combine(start_dt.date(), interval.end_time))
        if window_start <= start_dt and end_dt <= window_end:
            return True
    return False


def _is_during_unavailability(technician, start_dt, end_dt):
    overlap = Unavailability.objects.filter(technician=technician).filter(start_datetime__lt=end_dt, end_datetime__gt=start_dt)
    return overlap.exists()


def _has_booking_conflict(technician, start_dt, end_dt):
    conflicts = Booking.objects.filter(
        technician=technician,
        status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED, Booking.Status.COMPLETED],
    ).filter(start_datetime__lt=end_dt, end_datetime__gt=start_dt)
    return conflicts.exists()


def create_booking(*, customer, service, technician, start_datetime, customer_note=None):
    if not service.is_active:
        raise BookingValidationError("SERVICE_NOT_AVAILABLE", "Service is inactive.")
    if not technician.is_active:
        raise BookingValidationError("TECHNICIAN_UNAVAILABLE", "Technician is inactive.")
    if not technician.services.filter(id=service.id).exists():
        raise BookingValidationError("SERVICE_NOT_AVAILABLE", "Technician does not provide this service.")
    if start_datetime is None or not timezone.is_aware(start_datetime):
        raise BookingValidationError("INVALID_DATETIME", "Start datetime must be timezone-aware.")
    if start_datetime <= timezone.now():
        raise BookingValidationError("PAST_BOOKING", "Booking must be in the future.")

    end_datetime = start_datetime + timedelta(minutes=service.duration_minutes)

    if not _is_within_working_hours(technician, start_datetime, end_datetime):
        raise BookingValidationError("INVALID_WORKING_HOURS", "Appointment is outside working hours.")
    if _is_during_unavailability(technician, start_datetime, end_datetime):
        raise BookingValidationError("TECHNICIAN_UNAVAILABLE", "Technician is unavailable for that period.")

    with transaction.atomic():
        technician_row = technician.__class__.objects.select_for_update().get(pk=technician.pk)
        if _has_booking_conflict(technician_row, start_datetime, end_datetime):
            raise BookingValidationError("BOOKING_CONFLICT", "The selected time slot is no longer available.")
        booking = Booking.objects.create(
            customer=customer,
            technician=technician_row,
            service=service,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            status=Booking.Status.PENDING,
            price_at_booking=service.price,
            duration_at_booking=service.duration_minutes,
            customer_note=customer_note or "",
        )
        return booking
