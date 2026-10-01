import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.availability.models import Unavailability, WorkingHour
from apps.bookings.models import Booking


def _localize(dt):
    return timezone.make_aware(dt, timezone=ZoneInfo(getattr(settings, "TIME_ZONE", "UTC")))


def get_available_slots(technician, service, date):
    if not technician.is_active:
        raise ValueError("Technician is inactive.")
    if not service.is_active:
        raise ValueError("Service is inactive.")
    if not technician.services.filter(id=service.id).exists():
        raise ValueError("Technician does not provide this service.")

    weekday = date.weekday()
    slots = []
    working_hours = WorkingHour.objects.filter(technician=technician, weekday=weekday).order_by("start_time")
    if not working_hours.exists():
        return slots

    duration = timedelta(minutes=service.duration_minutes)
    slot_interval = timedelta(minutes=15)

    for working_hour in working_hours:
        start_dt = _localize(datetime.datetime.combine(date, working_hour.start_time))
        end_dt = _localize(datetime.datetime.combine(date, working_hour.end_time))
        cursor = start_dt
        while cursor + duration <= end_dt:
            candidate_end = cursor + duration
            blocked = False
            for unavailability in Unavailability.objects.filter(technician=technician):
                if not (unavailability.end_datetime <= cursor or unavailability.start_datetime >= candidate_end):
                    blocked = True
                    break
            if not blocked:
                overlap_query = Booking.objects.filter(
                    technician=technician,
                    status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
                ).filter(start_datetime__lt=candidate_end, end_datetime__gt=cursor)
                if overlap_query.exists():
                    blocked = True
            if not blocked:
                slots.append({
                    "start": cursor.astimezone(ZoneInfo(getattr(settings, "TIME_ZONE", "UTC"))).strftime("%H:%M"),
                    "end": candidate_end.astimezone(ZoneInfo(getattr(settings, "TIME_ZONE", "UTC"))).strftime("%H:%M"),
                    "datetime_start": cursor.isoformat(),
                    "datetime_end": candidate_end.isoformat(),
                })
            cursor += slot_interval
    return slots
