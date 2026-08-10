import datetime

import pytest
from rest_framework.test import APIClient

from apps.room.models import RoomInventory, RoomType, RoomTypeBase


@pytest.mark.django_db
class TestRoomInventoryViewSet:
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
    def inventory(self, room_type):
        return RoomInventory.objects.create(
            date=datetime.date.today(), room_type=room_type, total_rooms=10, booked_rooms=2
        )

    def test_list_inventory(self, api_client, inventory):
        response = api_client.get("/api/v1/room-inventories/")

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["available_rooms"] == 8

    def test_retrieve_inventory(self, api_client, inventory):
        response = api_client.get(f"/api/v1/room-inventories/{inventory.id}/")

        assert response.status_code == 200
        assert response.data["available_rooms"] == 8
        assert response.data["occupancy_rate"] == 20.0

    def test_create_inventory(self, api_client, room_type):
        payload = {
            "date": str(datetime.date.today() + datetime.timedelta(days=1)),
            "room_type": room_type.id,
            "total_rooms": 5,
            "booked_rooms": 0,
        }

        response = api_client.post("/api/v1/room-inventories/", payload, format="json")

        assert response.status_code == 201
        assert response.data["total_rooms"] == 5

    def test_create_inventory_rejects_booked_over_total(self, api_client, room_type):
        payload = {
            "date": str(datetime.date.today() + datetime.timedelta(days=1)),
            "room_type": room_type.id,
            "total_rooms": 5,
            "booked_rooms": 10,
        }

        response = api_client.post("/api/v1/room-inventories/", payload, format="json")

        assert response.status_code == 400

    def test_update_inventory(self, api_client, inventory):
        payload = {
            "date": str(inventory.date),
            "room_type": inventory.room_type_id,
            "total_rooms": 20,
            "booked_rooms": 2,
        }

        response = api_client.put(f"/api/v1/room-inventories/{inventory.id}/", payload, format="json")

        assert response.status_code == 200
        assert response.data["total_rooms"] == 20

    def test_bulk_create_action(self, api_client, room_type):
        start = datetime.date.today() + datetime.timedelta(days=10)
        end = start + datetime.timedelta(days=2)
        payload = {
            "room_type": room_type.id,
            "start_date": str(start),
            "end_date": str(end),
            "total_rooms": 5,
        }

        response = api_client.post("/api/v1/room-inventories/bulk-create/", payload, format="json")

        # bulk_create_inventory reuses the nights-based _date_range helper, which is
        # exclusive of end_date, so a 2-day span yields 2 rows, not 3.
        assert response.status_code == 201
        assert RoomInventory.objects.filter(room_type=room_type, date__gte=start, date__lte=end).count() == 2

    def test_bulk_create_action_rejects_end_before_start(self, api_client, room_type):
        start = datetime.date.today() + datetime.timedelta(days=10)
        end = start - datetime.timedelta(days=1)
        payload = {
            "room_type": room_type.id,
            "start_date": str(start),
            "end_date": str(end),
            "total_rooms": 5,
        }

        response = api_client.post("/api/v1/room-inventories/bulk-create/", payload, format="json")

        assert response.status_code == 400

    def test_filter_by_date_range(self, api_client, room_type):
        today = datetime.date.today()
        RoomInventory.objects.create(date=today, room_type=room_type, total_rooms=5)
        RoomInventory.objects.create(date=today + datetime.timedelta(days=5), room_type=room_type, total_rooms=5)

        response = api_client.get(
            "/api/v1/room-inventories/",
            {"date_after": str(today), "date_before": str(today + datetime.timedelta(days=1))},
        )

        assert response.status_code == 200
        assert response.data["count"] == 1
