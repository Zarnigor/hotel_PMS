import datetime

import pytest
from rest_framework.test import APIClient

from apps.reservation.models import Reservation
from apps.reservation.services import create_reservation
from apps.room.models import RoomType, RoomTypeBase
from apps.room.services import RoomInventoryService
from apps.guest.models import Guest


@pytest.mark.django_db
class TestReservationViewSet:
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
    def guest(self):
        return Guest.objects.create(full_name="Ali")

    @pytest.fixture
    def guest2(self):
        return Guest.objects.create(full_name="Bob")

    @pytest.fixture
    def date_range(self):
        start = datetime.date.today() + datetime.timedelta(days=1)
        end = start + datetime.timedelta(days=2)
        return start, end

    @pytest.fixture
    def reservation(self, room_type, guest, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=2)
        return create_reservation(guest.id, room_type.id, check_in, check_out)

    def test_list_reservations(self, api_client, reservation):
        response = api_client.get("/api/v1/reservations/")

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["guest"]["full_name"] == "Ali"

    def test_retrieve_reservation(self, api_client, reservation):
        response = api_client.get(f"/api/v1/reservations/{reservation.id}/")

        assert response.status_code == 200
        assert response.data["guest"]["full_name"] == "Ali"
        assert response.data["assigned_room"] is None

    def test_create_reservation(self, api_client, room_type, guest2, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=1)
        payload = {
            "guest": guest2.id,
            "room_type": room_type.id,
            "check_in_date": str(check_in),
            "check_out_date": str(check_out),
        }

        response = api_client.post("/api/v1/reservations/", payload, format="json")

        assert response.status_code == 201
        assert response.data["guest"]["full_name"] == "Bob"
        assert response.data["status"] == Reservation.Status.PENDING

    def test_create_reservation_rejects_invalid_date_range(self, api_client, room_type, guest2, date_range):
        check_in, check_out = date_range
        payload = {
            "guest": guest2.id,
            "room_type": room_type.id,
            "check_in_date": str(check_out),
            "check_out_date": str(check_in),
        }

        response = api_client.post("/api/v1/reservations/", payload, format="json")

        assert response.status_code == 400

    def test_create_reservation_rejects_missing_guest(self, api_client, room_type, date_range):
        check_in, check_out = date_range
        payload = {
            "guest": 999999,
            "room_type": room_type.id,
            "check_in_date": str(check_in),
            "check_out_date": str(check_out),
        }

        response = api_client.post("/api/v1/reservations/", payload, format="json")

        assert response.status_code == 400

    def test_create_reservation_propagates_overbooking_as_409(self, api_client, room_type, guest2, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=1)
        payload = {
            "guest": guest2.id,
            "room_type": room_type.id,
            "check_in_date": str(check_in),
            "check_out_date": str(check_out),
        }
        first = api_client.post("/api/v1/reservations/", payload, format="json")
        assert first.status_code == 201

        second = api_client.post("/api/v1/reservations/", payload, format="json")

        assert second.status_code == 409

    def test_cancel_action(self, api_client, reservation):
        response = api_client.post(f"/api/v1/reservations/{reservation.id}/cancel/")

        assert response.status_code == 200
        assert response.data["status"] == Reservation.Status.CANCELLED
        reservation.refresh_from_db()
        assert reservation.status == Reservation.Status.CANCELLED

    def test_put_is_not_allowed(self, api_client, reservation):
        response = api_client.put(f"/api/v1/reservations/{reservation.id}/", {}, format="json")

        assert response.status_code == 405

    def test_delete_is_not_allowed(self, api_client, reservation):
        response = api_client.delete(f"/api/v1/reservations/{reservation.id}/")

        assert response.status_code == 405

    def test_filter_by_status(self, api_client, reservation):
        response = api_client.get("/api/v1/reservations/", {"status": "cancelled"})

        assert response.status_code == 200
        assert response.data["count"] == 0
