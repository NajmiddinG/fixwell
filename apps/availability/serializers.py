from rest_framework import serializers

from .models import Unavailability, WorkingHour


class WorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHour
        fields = ["id", "technician", "weekday", "start_time", "end_time"]
        read_only_fields = ["id"]


class UnavailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Unavailability
        fields = ["id", "technician", "start_datetime", "end_datetime", "reason", "created_at"]
        read_only_fields = ["id", "created_at"]
