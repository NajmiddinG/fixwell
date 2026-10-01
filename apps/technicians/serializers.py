from rest_framework import serializers

from apps.services.models import Service
from apps.services.serializers import ServiceSerializer

from .models import Technician, TechnicianService


class TechnicianServiceSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = TechnicianService
        fields = ["id", "service"]


class TechnicianSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Technician
        fields = ["id", "user", "name", "bio", "is_active", "services", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at", "services", "name"]

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.email


class TechnicianAssignmentSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()

    def validate_service_id(self, value):
        try:
            from apps.services.models import Service
            return Service.objects.get(pk=value)
        except Service.DoesNotExist as exc:
            raise serializers.ValidationError("Service not found.") from exc
