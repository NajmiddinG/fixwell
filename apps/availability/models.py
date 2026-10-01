from django.core.exceptions import ValidationError
from django.db import models


class WeekdayChoices(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class WorkingHour(models.Model):
    technician = models.ForeignKey("technicians.Technician", on_delete=models.CASCADE, related_name="working_hours")
    weekday = models.IntegerField(choices=WeekdayChoices.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "working_hours"
        indexes = [models.Index(fields=["technician", "weekday"])]
        constraints = [
            models.CheckConstraint(check=models.Q(start_time__lt=models.F("end_time")), name="working_hour_start_before_end"),
        ]

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "End time must be later than start time."})

        overlaps = WorkingHour.objects.filter(
            technician=self.technician,
            weekday=self.weekday,
        ).exclude(pk=self.pk)
        for interval in overlaps:
            if not (self.end_time <= interval.start_time or self.start_time >= interval.end_time):
                raise ValidationError({"start_time": "This working-hour interval overlaps with an existing one."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.technician} {self.weekday} {self.start_time}-{self.end_time}"


class Unavailability(models.Model):
    technician = models.ForeignKey("technicians.Technician", on_delete=models.CASCADE, related_name="unavailability")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    reason = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "unavailability"
        indexes = [models.Index(fields=["technician", "start_datetime"])]
        constraints = [
            models.CheckConstraint(check=models.Q(start_datetime__lt=models.F("end_datetime")), name="unavailability_start_before_end"),
        ]

    def clean(self):
        if self.start_datetime and self.end_datetime and self.start_datetime >= self.end_datetime:
            raise ValidationError({"end_datetime": "End datetime must be later than the start datetime."})

        overlaps = Unavailability.objects.filter(technician=self.technician).exclude(pk=self.pk)
        for existing in overlaps:
            if self.start_datetime < existing.end_datetime and self.end_datetime > existing.start_datetime:
                raise ValidationError({"start_datetime": "This unavailability overlaps with an existing period."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.technician} {self.start_datetime} - {self.end_datetime}"
