from django.urls import path

from .views import TechnicianDetailView, TechnicianListCreateView, TechnicianServiceAssignmentView

urlpatterns = [
    path("", TechnicianListCreateView.as_view(), name="technician-list-create"),
    path("<int:pk>/", TechnicianDetailView.as_view(), name="technician-detail"),
    path("<int:pk>/services/", TechnicianServiceAssignmentView.as_view(), name="technician-service-assignment"),
]
