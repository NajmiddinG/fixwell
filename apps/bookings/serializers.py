from django.utils import timezone
from rest_framework import serializers

from apps.services.models import Service
from apps.services.serializers import ServiceSerializer
from apps.technicians.models import Technician

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    technician = serializers.SerializerMethodField()
    price = serializers.DecimalField(source="price_at_booking", max_digits=10, decimal_places=2, read_only=True)
    duration_minutes = serializers.IntegerField(source="duration_at_booking", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "service",
            "technician",
            "start_datetime",
            "end_datetime",
            "status",
            "price",
            "duration_minutes",
            "customer_note",
            "created_at",
        ]

    def get_technician(self, obj):
        return {"id": obj.technician.id, "name": obj.technician.user.get_full_name() or obj.technician.user.email}


class BookingCreateSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()
    technician_id = serializers.IntegerField()
    start_datetime = serializers.DateTimeField()
    customer_note = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_service_id(self, value):
        try:
            service = Service.objects.get(pk=value)
        except Service.DoesNotExist as exc:
            raise serializers.ValidationError("Unknown service.") from exc
        if not service.is_active:
            raise serializers.ValidationError("Service is inactive.")
        return service

    def validate_technician_id(self, value):
        try:
            technician = Technician.objects.select_related("user").get(pk=value)
        except Technician.DoesNotExist as exc:
            raise serializers.ValidationError("Unknown technician.") from exc
        if not technician.is_active:
            raise serializers.ValidationError("Technician is inactive.")
        return technician

    def validate(self, attrs):
        service = attrs.get("service_id")
        technician = attrs.get("technician_id")
        start_dt = attrs.get("start_datetime")
        if start_dt and start_dt <= timezone.now():
            raise serializers.ValidationError({"start_datetime": "Booking start must be in the future."})
        if service and technician and not technician.services.filter(id=service.id).exists():
            raise serializers.ValidationError({"detail": "Technician does not provide this service."})
        return attrs
