from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.users.admin import CustomUserAdmin
from apps.users.models import User


def test_custom_user_admin_change_form_ignores_non_editable_timestamp_fields(db):
    user = User.objects.create_user(
        email="admin-form@example.com",
        password="StrongPass123!",
        first_name="Jane",
        last_name="Doe",
    )

    request = RequestFactory().get(f"/admin/users/user/{user.pk}/change/")
    admin = CustomUserAdmin(User, AdminSite())

    form_class = admin.get_form(request, obj=user)

    assert "date_joined" not in form_class.base_fields
    assert "created_at" not in form_class.base_fields
    assert "updated_at" not in form_class.base_fields
