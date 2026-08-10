import pytest
from rest_framework.test import APIClient

from apps.room.models import Room, RoomType, RoomTypeBase


@pytest.mark.django_db
class TestRoomViewSet:
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

    @pytest.fixture
    def room(self, room_type):
        return Room.objects.create(room_number="101", room_type=room_type)

    def test_list_rooms(self, api_client, room):
        response = api_client.get("/api/v1/rooms/")

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["room_number"] == "101"

    def test_retrieve_room(self, api_client, room):
        response = api_client.get(f"/api/v1/rooms/{room.id}/")

        assert response.status_code == 200
        assert response.data["room_number"] == "101"
        assert response.data["room_type"]["id"] == room.room_type_id

    def test_create_room(self, api_client, room_type):
        payload = {"room_number": "202", "room_type": room_type.id, "status": "available"}

        response = api_client.post("/api/v1/rooms/", payload, format="json")

        assert response.status_code == 201
        assert Room.objects.filter(room_number="202").exists()

    def test_create_room_rejects_blank_room_number(self, api_client, room_type):
        payload = {"room_number": "   ", "room_type": room_type.id, "status": "available"}

        response = api_client.post("/api/v1/rooms/", payload, format="json")

        assert response.status_code == 400

    def test_create_room_rejects_duplicate_room_number(self, api_client, room):
        payload = {"room_number": room.room_number, "room_type": room.room_type_id, "status": "available"}

        response = api_client.post("/api/v1/rooms/", payload, format="json")

        assert response.status_code == 400

    def test_update_room(self, api_client, room):
        payload = {"room_number": "303", "room_type": room.room_type_id, "status": "available"}

        response = api_client.put(f"/api/v1/rooms/{room.id}/", payload, format="json")

        assert response.status_code == 200
        room.refresh_from_db()
        assert room.room_number == "303"

    def test_delete_room_soft_deletes_and_restore_brings_it_back(self, api_client, room):
        delete_response = api_client.delete(f"/api/v1/rooms/{room.id}/")
        assert delete_response.status_code == 204
        assert not Room.objects.filter(id=room.id).exists()

        restore_response = api_client.post(f"/api/v1/rooms/{room.id}/restore/")
        assert restore_response.status_code == 200
        assert Room.objects.filter(id=room.id).exists()

    def test_filter_by_status(self, api_client, room_type):
        Room.objects.create(room_number="A1", room_type=room_type, status=Room.Status.OCCUPIED)
        Room.objects.create(room_number="A2", room_type=room_type, status=Room.Status.AVAILABLE)

        response = api_client.get("/api/v1/rooms/", {"status": "occupied"})

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["room_number"] == "A1"
