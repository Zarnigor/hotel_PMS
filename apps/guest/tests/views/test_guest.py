import pytest
from rest_framework.test import APIClient

from apps.guest.models import Guest


@pytest.mark.django_db
class TestGuestViewSet:
    @pytest.fixture(autouse=True)
    def _allow_testserver(self, settings):
        settings.ALLOWED_HOSTS = ["*"]

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def guest(self):
        return Guest.objects.create(full_name="Ali", country="Uzbekistan")

    def test_list_guests(self, api_client, guest):
        response = api_client.get("/api/v1/guests/")

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["full_name"] == "Ali"

    def test_retrieve_guest(self, api_client, guest):
        response = api_client.get(f"/api/v1/guests/{guest.id}/")

        assert response.status_code == 200
        assert response.data["full_name"] == "Ali"

    def test_create_guest(self, api_client):
        payload = {"full_name": "Vali", "country": "Uzbekistan"}

        response = api_client.post("/api/v1/guests/", payload, format="json")

        assert response.status_code == 201
        assert Guest.objects.filter(full_name="Vali").exists()

    def test_create_guest_rejects_blank_full_name(self, api_client):
        payload = {"full_name": "   "}

        response = api_client.post("/api/v1/guests/", payload, format="json")

        assert response.status_code == 400

    def test_create_guest_rejects_duplicate_passport(self, api_client, guest):
        guest.passport = "AA1234567"
        guest.save(update_fields=["passport"])

        payload = {"full_name": "Boshqa", "passport": "AA1234567"}

        response = api_client.post("/api/v1/guests/", payload, format="json")

        assert response.status_code == 400

    def test_update_guest(self, api_client, guest):
        payload = {"full_name": "Yangi Ism", "country": guest.country}

        response = api_client.put(f"/api/v1/guests/{guest.id}/", payload, format="json")

        assert response.status_code == 200
        guest.refresh_from_db()
        assert guest.full_name == "Yangi Ism"

    def test_delete_guest(self, api_client, guest):
        response = api_client.delete(f"/api/v1/guests/{guest.id}/")

        assert response.status_code == 204
        assert not Guest.objects.filter(id=guest.id).exists()

    def test_search_by_full_name(self, api_client, guest):
        response = api_client.get("/api/v1/guests/", {"search": "Ali"})

        assert response.status_code == 200
        assert response.data["count"] == 1
