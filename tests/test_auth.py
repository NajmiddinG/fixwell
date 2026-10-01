import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestAuthAPI:
    def test_register_user(self, api_client):
        response = api_client.post(
            "/api/auth/register/",
            {"email": "newuser@example.com", "first_name": "Test", "last_name": "User", "password": "StrongPass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_duplicate_email_is_rejected(self, api_client):
        User.objects.create_user(email="dup@example.com", password="StrongPass123!")
        response = api_client.post(
            "/api/auth/register/",
            {"email": "dup@example.com", "first_name": "Test", "last_name": "User", "password": "StrongPass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_authenticated_user_me(self, api_client, customer_user):
        api_client.force_authenticate(customer_user)
        response = api_client.get("/api/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == customer_user.email
