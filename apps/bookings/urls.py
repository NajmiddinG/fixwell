from django.urls import path

from .views import AdminBookingListView, AvailabilityView, BookingDetailView, BookingListView, BookingStatusActionView

urlpatterns = [
    path("availability/", AvailabilityView.as_view(), name="availability"),
    path("bookings/", BookingListView.as_view(), name="customer-bookings"),
    path("bookings/<int:pk>/", BookingDetailView.as_view(), name="booking-detail"),
    path("bookings/<int:pk>/<str:action>/", BookingStatusActionView.as_view(), name="booking-status-action"),
    path("admin/bookings/", AdminBookingListView.as_view(), name="admin-bookings"),
]
