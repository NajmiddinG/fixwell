from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from apps.technicians.models import Technician

from .models import Unavailability, WorkingHour
from .serializers import UnavailabilitySerializer, WorkingHourSerializer


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class TechnicianWorkingHourListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkingHourSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return WorkingHour.objects.filter(technician_id=self.kwargs["technician_id"]).order_by("weekday", "start_time")

    def perform_create(self, serializer):
        technician = get_object_or_404(Technician, pk=self.kwargs["technician_id"])
        serializer.save(technician=technician)


class WorkingHourDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WorkingHour.objects.all()
    serializer_class = WorkingHourSerializer
    permission_classes = [IsAdminUser]


class TechnicianUnavailabilityListCreateView(generics.ListCreateAPIView):
    serializer_class = UnavailabilitySerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Unavailability.objects.filter(technician_id=self.kwargs["technician_id"]).order_by("start_datetime")

    def perform_create(self, serializer):
        technician = get_object_or_404(Technician, pk=self.kwargs["technician_id"])
        serializer.save(technician=technician)


class UnavailabilityDetailView(generics.DestroyAPIView):
    queryset = Unavailability.objects.all()
    serializer_class = UnavailabilitySerializer
    permission_classes = [IsAdminUser]
