from django.contrib import admin

from .models import Unavailability, WorkingHour


@admin.register(WorkingHour)
class WorkingHourAdmin(admin.ModelAdmin):
    list_display = ["technician", "weekday", "start_time", "end_time"]


@admin.register(Unavailability)
class UnavailabilityAdmin(admin.ModelAdmin):
    list_display = ["technician", "start_datetime", "end_datetime", "reason"]
