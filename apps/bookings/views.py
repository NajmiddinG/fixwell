from datetime import datetime

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.services.models import Service
from apps.technicians.models import Technician

from .models import Booking
from .serializers import BookingCreateSerializer, BookingSerializer
from .services.availability import get_available_slots
from .services.booking import BookingValidationError, create_booking


class IsCustomerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.customer == request.user


class BookingListView(generics.ListCreateAPIView):
    permission_classes = [IsCustomerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.select_related("customer", "technician__user", "service").order_by("-created_at")
        return Booking.objects.filter(customer=user).select_related("customer", "technician__user", "service").order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BookingCreateSerializer
        return BookingSerializer

    def post(self, request, *args, **kwargs):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = serializer.validated_data["service_id"]
        technician = serializer.validated_data["technician_id"]
        start_dt = serializer.validated_data["start_datetime"]
        try:
            booking = create_booking(
                customer=request.user,
                service=service,
                technician=technician,
                start_datetime=start_dt,
                customer_note=serializer.validated_data.get("customer_note", ""),
            )
        except BookingValidationError as exc:
            status_code = status.HTTP_409_CONFLICT if exc.code == "BOOKING_CONFLICT" else status.HTTP_400_BAD_REQUEST
            return Response({"error": {"code": exc.code, "message": exc.message}}, status=status_code)
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingDetailView(generics.RetrieveAPIView):
    queryset = Booking.objects.select_related("customer", "technician__user", "service").all()
    serializer_class = BookingSerializer
    permission_classes = [IsCustomerOrAdmin]


class BookingStatusActionView(generics.GenericAPIView):
    queryset = Booking.objects.all()
    permission_classes = [IsCustomerOrAdmin]

    def _get_booking(self):
        return get_object_or_404(Booking.objects.select_related("customer", "technician__user", "service"), pk=self.kwargs["pk"])

    def post(self, request, *args, **kwargs):
        booking = self._get_booking()
        self.check_object_permissions(request, booking)
        action_name = self.kwargs.get("action")
        try:
            if action_name == "cancel":
                if not request.user.is_staff:
                    now = timezone.now()
                    if (booking.start_datetime - now).total_seconds() < 2 * 60 * 60:
                        return Response({"error": {"code": "CANCELLATION_NOT_ALLOWED", "message": "Cancellation must be requested at least 2 hours before the appointment."}}, status=400)
                booking.set_status(Booking.Status.CANCELLED)
            elif action_name == "confirm":
                if not request.user.is_staff:
                    return Response({"error": {"code": "FORBIDDEN", "message": "Only admins can confirm bookings."}}, status=403)
                booking.set_status(Booking.Status.CONFIRMED)
            elif action_name == "complete":
                if not request.user.is_staff:
                    return Response({"error": {"code": "FORBIDDEN", "message": "Only admins can complete bookings."}}, status=403)
                booking.set_status(Booking.Status.COMPLETED)
            else:
                return Response({"error": {"code": "INVALID_ACTION", "message": "Unsupported booking action."}}, status=400)
        except ValueError as exc:
            return Response({"error": {"code": "INVALID_STATUS_TRANSITION", "message": str(exc)}}, status=400)
        return Response(BookingSerializer(booking).data)


class AvailabilityView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        service_id = request.query_params.get("service_id")
        technician_id = request.query_params.get("technician_id")
        date = request.query_params.get("date")
        if not service_id or not technician_id or not date:
            return Response({"error": {"code": "INVALID_REQUEST", "message": "service_id, technician_id and date are required."}}, status=400)
        try:
            service = Service.objects.get(pk=service_id)
            technician = Technician.objects.select_related("user").get(pk=technician_id)
        except (Service.DoesNotExist, Technician.DoesNotExist):
            return Response({"error": {"code": "NOT_FOUND", "message": "Service or technician not found."}}, status=404)
        try:
            day = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": {"code": "INVALID_DATE", "message": "Date must be in YYYY-MM-DD format."}}, status=400)
        try:
            slots = get_available_slots(technician, service, day)
        except ValueError as exc:
            return Response({"error": {"code": "SERVICE_NOT_AVAILABLE", "message": str(exc)}}, status=400)
        return Response({
            "date": date,
            "technician_id": technician.id,
            "service_id": service.id,
            "slots": [{"start": slot["start"], "end": slot["end"]} for slot in slots],
        })


class AdminBookingListView(generics.ListAPIView):
    queryset = Booking.objects.select_related("customer", "technician__user", "service").all().order_by("-created_at")
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAdminUser]
