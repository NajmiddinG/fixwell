from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response

from apps.services.models import Service

from .models import Technician, TechnicianService
from .serializers import TechnicianAssignmentSerializer, TechnicianSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class TechnicianListCreateView(generics.ListCreateAPIView):
    queryset = Technician.objects.select_related("user").prefetch_related("services").order_by("id")
    serializer_class = TechnicianSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        service_id = self.request.query_params.get("service_id")
        if service_id:
            qs = qs.filter(services__id=service_id)
        return qs.distinct()

    def perform_create(self, serializer):
        user = serializer.validated_data.get("user")
        if Technician.objects.filter(user=user).exists():
            raise serializers.ValidationError({"user": "This user is already a technician."})
        serializer.save()


class TechnicianDetailView(generics.RetrieveUpdateAPIView):
    queryset = Technician.objects.select_related("user").prefetch_related("services")
    serializer_class = TechnicianSerializer
    permission_classes = [IsAdminOrReadOnly]


class TechnicianServiceAssignmentView(generics.GenericAPIView):
    permission_classes = [IsAdminOrReadOnly]

    def post(self, request, pk):
        technician = get_object_or_404(Technician.objects.select_related("user"), pk=pk)
        serializer = TechnicianAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = serializer.validated_data["service_id"]
        obj, created = TechnicianService.objects.get_or_create(technician=technician, service=service)
        if not created:
            return Response({"detail": "Service already assigned to this technician."}, status=400)
        return Response({"id": obj.id, "technician_id": technician.id, "service_id": service.id}, status=201)
