from django.contrib import admin

from .models import Technician, TechnicianService


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ["user", "bio", "is_active"]
    search_fields = ["user__email", "bio"]


@admin.register(TechnicianService)
class TechnicianServiceAdmin(admin.ModelAdmin):
    list_display = ["technician", "service"]
