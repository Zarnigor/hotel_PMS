import datetime

import pytest

from apps.reservation.models import Reservation
from apps.reservation.services import cancel_reservation, create_reservation
from apps.reservation.utils import get_reservation, list_reservations
from apps.room.models import RoomInventory, RoomType, RoomTypeBase
from apps.room.services import RoomInventoryService
from apps.guest.models import Guest
from exceptions import (
    GuestNotFoundError,
    InvalidDateRangeError,
    OverbookingError,
    ReservationCancelledError,
    ReservationNotFoundError,
    RoomNotFoundError,
    RoomUnbookableError,
)


@pytest.mark.django_db
class TestCreateReservation:
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

    def test_creates_reservation_and_reserves_inventory(self, room_type, guest, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=2)

        reservation = create_reservation(guest.id, room_type.id, check_in, check_out)

        assert reservation.status == Reservation.Status.PENDING
        assert reservation.guest_id == guest.id
        rows = RoomInventory.objects.filter(room_type=room_type, date__gte=check_in, date__lt=check_out)
        assert all(row.booked_rooms == 1 for row in rows)

    def test_rejects_invalid_date_range(self, room_type, guest, date_range):
        check_in, check_out = date_range

        with pytest.raises(InvalidDateRangeError):
            create_reservation(guest.id, room_type.id, check_out, check_in)

    def test_rejects_missing_guest(self, room_type, date_range):
        check_in, check_out = date_range

        with pytest.raises(GuestNotFoundError):
            create_reservation(-1, room_type.id, check_in, check_out)

    def test_rejects_missing_room_type(self, guest, date_range):
        check_in, check_out = date_range

        with pytest.raises(RoomNotFoundError):
            create_reservation(guest.id, -1, check_in, check_out)

    def test_rejects_deleted_room_type(self, room_type, guest, date_range):
        check_in, check_out = date_range
        room_type.delete()

        with pytest.raises(RoomUnbookableError):
            create_reservation(guest.id, room_type.id, check_in, check_out)

    def test_rejects_missing_inventory(self, room_type, guest, date_range):
        check_in, check_out = date_range

        with pytest.raises(OverbookingError):
            create_reservation(guest.id, room_type.id, check_in, check_out)

    def test_rejects_overbooking(self, room_type, guest, guest2, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=1)
        create_reservation(guest.id, room_type.id, check_in, check_out)

        with pytest.raises(OverbookingError):
            create_reservation(guest2.id, room_type.id, check_in, check_out)


@pytest.mark.django_db
class TestCancelReservation:
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
    def date_range(self):
        start = datetime.date.today() + datetime.timedelta(days=1)
        end = start + datetime.timedelta(days=2)
        return start, end

    @pytest.fixture
    def reservation(self, room_type, guest, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=2)
        return create_reservation(guest.id, room_type.id, check_in, check_out)

    def test_cancels_reservation_and_releases_inventory(self, reservation, room_type, date_range):
        check_in, check_out = date_range

        cancelled = cancel_reservation(reservation.id)

        assert cancelled.status == Reservation.Status.CANCELLED
        rows = RoomInventory.objects.filter(room_type=room_type, date__gte=check_in, date__lt=check_out)
        assert all(row.booked_rooms == 0 for row in rows)

    def test_rejects_not_found(self):
        with pytest.raises(ReservationNotFoundError):
            cancel_reservation(-1)

    def test_rejects_already_cancelled(self, reservation):
        cancel_reservation(reservation.id)

        with pytest.raises(ReservationCancelledError):
            cancel_reservation(reservation.id)


@pytest.mark.django_db
class TestReservationReadHelpers:
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
    def date_range(self):
        start = datetime.date.today() + datetime.timedelta(days=1)
        end = start + datetime.timedelta(days=2)
        return start, end

    @pytest.fixture
    def reservation(self, room_type, guest, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=2)
        return create_reservation(guest.id, room_type.id, check_in, check_out)

    def test_get_reservation_returns_nested_dict(self, reservation, room_type, guest):
        data = get_reservation(reservation.id)

        assert data["id"] == reservation.id
        assert data["guest"]["id"] == guest.id
        assert data["guest"]["full_name"] == "Ali"
        assert data["room_type"]["id"] == room_type.id
        assert data["assigned_room"] is None

    def test_get_reservation_rejects_not_found(self):
        with pytest.raises(ReservationNotFoundError):
            get_reservation(-1)

    def test_list_reservations_filters_by_room_type(self, reservation, room_type):
        other_base = RoomTypeBase.objects.create(name="Other", description="Other")
        other_type = RoomType.objects.create(room_type_base=other_base, name="Other", base_price=50)

        result = list_reservations(room_type_id=room_type.id)

        assert result["count"] == 1
        assert result["results"][0]["id"] == reservation.id

    def test_list_reservations_paginates(self, reservation):
        result = list_reservations(limit=1, offset=0)

        assert result["limit"] == 1
        assert result["offset"] == 0
        assert len(result["results"]) == 1
