from django.urls import path

from .views import (
    TechnicianUnavailabilityListCreateView,
    TechnicianWorkingHourListCreateView,
    UnavailabilityDetailView,
    WorkingHourDetailView,
)

urlpatterns = [
    path("technicians/<int:technician_id>/working-hours/", TechnicianWorkingHourListCreateView.as_view(), name="working-hours"),
    path("working-hours/<int:pk>/", WorkingHourDetailView.as_view(), name="working-hour-detail"),
    path("technicians/<int:technician_id>/unavailability/", TechnicianUnavailabilityListCreateView.as_view(), name="unavailability"),
    path("unavailability/<int:pk>/", UnavailabilityDetailView.as_view(), name="unavailability-detail"),
]
