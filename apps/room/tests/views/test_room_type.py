import pytest
from rest_framework.test import APIClient

from apps.room.models import RoomInventory, RoomType, RoomTypeBase


@pytest.mark.django_db
class TestRoomTypeViewSet:
    @pytest.fixture(autouse=True)
    def _allow_testserver(self, settings):
        settings.ALLOWED_HOSTS = ["*"]

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

    def test_list_room_types(self, api_client, room_type):
        response = api_client.get("/api/v1/room-types/")

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Standard"

    def test_retrieve_room_type(self, api_client, room_type):
        response = api_client.get(f"/api/v1/room-types/{room_type.id}/")

        assert response.status_code == 200
        assert response.data["name"] == "Standard"

    def test_create_room_type_also_generates_inventory(self, api_client, room_type_base):
        payload = {"room_type_base": room_type_base.id, "name": "Deluxe", "base_price": "150.00"}

        response = api_client.post("/api/v1/room-types/", payload, format="json")

        assert response.status_code == 201
        assert RoomInventory.objects.filter(room_type_id=response.data["id"]).exists()

    def test_create_room_type_rejects_non_positive_base_price(self, api_client, room_type_base):
        payload = {"room_type_base": room_type_base.id, "name": "Deluxe", "base_price": "0.00"}

        response = api_client.post("/api/v1/room-types/", payload, format="json")

        assert response.status_code == 400

    def test_delete_room_type_soft_deletes_and_restore_brings_it_back(self, api_client, room_type):
        delete_response = api_client.delete(f"/api/v1/room-types/{room_type.id}/")
        assert delete_response.status_code == 204
        assert not RoomType.objects.filter(id=room_type.id).exists()

        restore_response = api_client.post(f"/api/v1/room-types/{room_type.id}/restore/")
        assert restore_response.status_code == 200
        assert RoomType.objects.filter(id=room_type.id).exists()

    def test_filter_by_room_type_base(self, api_client, room_type_base):
        other_base = RoomTypeBase.objects.create(name="Other", description="Other")
        RoomType.objects.create(room_type_base=other_base, name="Suite", base_price=200)
        matching = RoomType.objects.create(room_type_base=room_type_base, name="Standard2", base_price=90)

        response = api_client.get("/api/v1/room-types/", {"room_type_base": room_type_base.id})

        assert response.status_code == 200
        ids = [item["id"] for item in response.data["results"]]
        assert ids == [matching.id]


@pytest.mark.django_db
class TestRoomTypeBaseViewSet:
    @pytest.fixture(autouse=True)
    def _allow_testserver(self, settings):
        settings.ALLOWED_HOSTS = ["*"]

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    def test_list_room_type_bases(self, api_client, room_type_base):
        response = api_client.get("/api/v1/room-type-bases/")

        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_create_room_type_base(self, api_client):
        payload = {"name": "Deluxe", "description": "Deluxe rooms"}

        response = api_client.post("/api/v1/room-type-bases/", payload, format="json")

        assert response.status_code == 201
        assert RoomTypeBase.objects.filter(name="Deluxe").exists()

    def test_update_room_type_base(self, api_client, room_type_base):
        response = api_client.patch(
            f"/api/v1/room-type-bases/{room_type_base.id}/", {"name": "Renamed"}, format="json"
        )

        assert response.status_code == 200
        room_type_base.refresh_from_db()
        assert room_type_base.name == "Renamed"

    def test_delete_room_type_base_soft_deletes(self, api_client, room_type_base):
        response = api_client.delete(f"/api/v1/room-type-bases/{room_type_base.id}/")

        assert response.status_code == 204
        assert not RoomTypeBase.objects.filter(id=room_type_base.id).exists()
        assert RoomTypeBase.all_objects.get(id=room_type_base.id).deleted_at is not None
