import datetime
import threading

import pytest
from django.db import connection

from apps.reservation.models import Reservation
from apps.reservation.services import assign_room, cancel_reservation, check_in, check_out, create_reservation
from apps.reservation.utils import get_reservation, list_reservations
from apps.room.models import Room, RoomInventory, RoomType, RoomTypeBase
from apps.room.services import RoomInventoryService, RoomStatus
from apps.guest.models import Guest
from exceptions import (
    BookingConflictError,
    GuestNotFoundError,
    InvalidDateRangeError,
    OccupancyExceededError,
    OverbookingError,
    ReservationCancelledError,
    ReservationInvalidStateError,
    ReservationNotFoundError,
    RoomNotAssignedError,
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
        assert reservation.primary_guest_id == guest.id
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

    def test_accepts_guest_count_within_max_occupancy(self, room_type, guest, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=2)

        reservation = create_reservation(
            guest.id, room_type.id, check_in, check_out, guest_count=room_type.max_occupancy
        )

        assert reservation.guest_count == room_type.max_occupancy

    def test_rejects_guest_count_exceeding_max_occupancy(self, room_type, guest, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=2)

        with pytest.raises(OccupancyExceededError):
            create_reservation(
                guest.id, room_type.id, check_in, check_out, guest_count=room_type.max_occupancy + 1
            )

        # occupancy tekshiruvi inventory'ni o'zgartirmasligi kerak — rad etilgan urinish
        # bo'sh xonalar sonini kamaytirmaydi.
        rows = RoomInventory.objects.filter(room_type=room_type, date__gte=check_in, date__lt=check_out)
        assert all(row.booked_rooms == 0 for row in rows)

    def test_overbooking_check_still_raised_when_guest_count_is_valid(
        self, room_type, guest, guest2, date_range
    ):
        """Occupancy tekshiruvi qo'shilgani OverbookingError'ni bosib qolmasligini tasdiqlaydi —
        guest_count limit ichida bo'lsa ham, bo'sh xona qolmasa OverbookingError chiqishi kerak."""
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=1)
        create_reservation(guest.id, room_type.id, check_in, check_out, guest_count=1)

        with pytest.raises(OverbookingError):
            create_reservation(guest2.id, room_type.id, check_in, check_out, guest_count=1)

    def test_overbooking_takes_precedence_over_occupancy_check(self, room_type, guest, guest2, date_range):
        """Ikkala shart ham buzilganda (bo'sh xona yo'q va guest_count limitdan oshgan),
        avval OverbookingError ko'tariladi — ikkita tekshiruv bir-biriga xalaqit bermaydi."""
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=1)
        create_reservation(guest.id, room_type.id, check_in, check_out, guest_count=1)

        with pytest.raises(OverbookingError):
            create_reservation(
                guest2.id, room_type.id, check_in, check_out, guest_count=room_type.max_occupancy + 1
            )


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
    def room(self, room_type):
        return Room.objects.create(room_number="301", room_type=room_type)

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

    def test_cancels_checked_in_reservation_and_frees_room(self, reservation, room, room_type, date_range):
        check_in_date, check_out_date = date_range
        assign_room(reservation.id, room.id)
        check_in(reservation.id)

        cancelled = cancel_reservation(reservation.id)

        assert cancelled.status == Reservation.Status.CANCELLED
        room.refresh_from_db()
        assert room.status == RoomStatus.CLEANING
        rows = RoomInventory.objects.filter(room_type=room_type, date__gte=check_in_date, date__lt=check_out_date)
        assert all(row.booked_rooms == 0 for row in rows)

    def test_rejects_already_checked_out(self, reservation, room):
        assign_room(reservation.id, room.id)
        check_in(reservation.id)
        check_out(reservation.id)

        with pytest.raises(ReservationInvalidStateError):
            cancel_reservation(reservation.id)


@pytest.mark.django_db
class TestAssignRoom:
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
    def room(self, room_type):
        return Room.objects.create(room_number="201", room_type=room_type)

    @pytest.fixture
    def date_range(self):
        start = datetime.date.today() + datetime.timedelta(days=1)
        end = start + datetime.timedelta(days=2)
        return start, end

    @pytest.fixture
    def reservation(self, room_type, guest, date_range):
        check_in_date, check_out_date = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in_date, check_out_date, total_rooms=2)
        return create_reservation(guest.id, room_type.id, check_in_date, check_out_date, guest_count=2)

    def test_assigns_room(self, reservation, room):
        assigned = assign_room(reservation.id, room.id)

        assert assigned.assigned_room_id == room.id

    def test_rejects_reservation_not_found(self, room):
        with pytest.raises(ReservationNotFoundError):
            assign_room(-1, room.id)

    def test_rejects_room_not_found(self, reservation):
        with pytest.raises(RoomNotFoundError):
            assign_room(reservation.id, -1)

    def test_rejects_insufficient_capacity(self, reservation, room_type_base):
        small_room_type = RoomType.objects.create(
            room_type_base=room_type_base, name="Small", base_price=50, max_occupancy=1
        )
        small_room = Room.objects.create(room_number="202", room_type=small_room_type)

        with pytest.raises(OccupancyExceededError):
            assign_room(reservation.id, small_room.id)

    def test_rejects_unavailable_room(self, reservation, room_type):
        unavailable_room = Room.objects.create(
            room_number="203", room_type=room_type, status=RoomStatus.MAINTENANCE
        )

        with pytest.raises(RoomUnbookableError):
            assign_room(reservation.id, unavailable_room.id)

    def test_rejects_overlapping_dates(self, reservation, room, room_type, guest, date_range):
        check_in_date, check_out_date = date_range
        assign_room(reservation.id, room.id)
        overlapping = create_reservation(guest.id, room_type.id, check_in_date, check_out_date, guest_count=1)

        with pytest.raises(BookingConflictError):
            assign_room(overlapping.id, room.id)

    def test_allows_non_overlapping_dates(self, room, room_type, guest):
        first_in = datetime.date.today() + datetime.timedelta(days=1)
        first_out = first_in + datetime.timedelta(days=2)
        second_in = first_out
        second_out = second_in + datetime.timedelta(days=2)
        RoomInventoryService.generate_for_date_range(room_type.id, first_in, second_out, total_rooms=1)
        first = create_reservation(guest.id, room_type.id, first_in, first_out)
        second = create_reservation(guest.id, room_type.id, second_in, second_out)
        assign_room(first.id, room.id)

        assigned_second = assign_room(second.id, room.id)

        assert assigned_second.assigned_room_id == room.id

    def test_rejects_reassignment_after_check_in(self, reservation, room, room_type):
        other_room = Room.objects.create(room_number="205", room_type=room_type)
        assign_room(reservation.id, room.id)
        check_in(reservation.id)

        with pytest.raises(ReservationInvalidStateError):
            assign_room(reservation.id, other_room.id)

        room.refresh_from_db()
        other_room.refresh_from_db()
        assert room.status == RoomStatus.OCCUPIED
        assert other_room.status == RoomStatus.AVAILABLE

    def test_rejects_assignment_for_cancelled_reservation(self, reservation, room):
        cancel_reservation(reservation.id)

        with pytest.raises(ReservationInvalidStateError):
            assign_room(reservation.id, room.id)

    @pytest.mark.django_db(transaction=True)
    def test_concurrent_assign_room_only_one_succeeds(self, room_type, guest):
        room = Room.objects.create(room_number="204", room_type=room_type)
        check_in_date = datetime.date.today() + datetime.timedelta(days=1)
        check_out_date = check_in_date + datetime.timedelta(days=2)
        RoomInventoryService.generate_for_date_range(room_type.id, check_in_date, check_out_date, total_rooms=2)
        first = create_reservation(guest.id, room_type.id, check_in_date, check_out_date)
        second = create_reservation(guest.id, room_type.id, check_in_date, check_out_date)

        barrier = threading.Barrier(2)
        results = []

        def worker(reservation_id):
            try:
                barrier.wait(timeout=5)
                assign_room(reservation_id, room.id)
                results.append("ok")
            except BookingConflictError:
                results.append("conflict")
            finally:
                connection.close()

        threads = [threading.Thread(target=worker, args=(r.id,)) for r in (first, second)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sorted(results) == ["conflict", "ok"]


@pytest.mark.django_db
class TestCheckIn:
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
    def room(self, room_type):
        return Room.objects.create(room_number="101", room_type=room_type)

    @pytest.fixture
    def date_range(self):
        start = datetime.date.today() + datetime.timedelta(days=1)
        end = start + datetime.timedelta(days=2)
        return start, end

    @pytest.fixture
    def reservation(self, room_type, guest, room, date_range):
        check_in_date, check_out_date = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in_date, check_out_date, total_rooms=2)
        res = create_reservation(guest.id, room_type.id, check_in_date, check_out_date)
        return assign_room(res.id, room.id)

    def test_checks_in_and_occupies_room(self, reservation, room):
        checked_in = check_in(reservation.id)

        assert checked_in.status == Reservation.Status.CHECKED_IN
        room.refresh_from_db()
        assert room.status == RoomStatus.OCCUPIED

    def test_rejects_not_found(self):
        with pytest.raises(ReservationNotFoundError):
            check_in(-1)

    def test_rejects_without_assigned_room(self, room_type, guest, date_range):
        check_in_date, check_out_date = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in_date, check_out_date, total_rooms=2)
        res = create_reservation(guest.id, room_type.id, check_in_date, check_out_date)

        with pytest.raises(RoomNotAssignedError):
            check_in(res.id)

    def test_rejects_wrong_state(self, reservation):
        check_in(reservation.id)

        with pytest.raises(ReservationInvalidStateError):
            check_in(reservation.id)

    def test_rejects_when_room_occupied_by_other_reservation(
        self, reservation, room, room_type, guest, date_range
    ):
        check_in_date, check_out_date = date_range
        check_in(reservation.id)

        next_check_in = check_out_date
        next_check_out = next_check_in + datetime.timedelta(days=2)
        RoomInventoryService.generate_for_date_range(room_type.id, next_check_in, next_check_out, total_rooms=2)
        other = create_reservation(guest.id, room_type.id, next_check_in, next_check_out)
        assign_room(other.id, room.id)

        with pytest.raises(BookingConflictError):
            check_in(other.id)


@pytest.mark.django_db
class TestCheckOut:
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
    def room(self, room_type):
        return Room.objects.create(room_number="102", room_type=room_type)

    @pytest.fixture
    def date_range(self):
        start = datetime.date.today() + datetime.timedelta(days=1)
        end = start + datetime.timedelta(days=2)
        return start, end

    @pytest.fixture
    def checked_in_reservation(self, room_type, guest, room, date_range):
        check_in_date, check_out_date = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in_date, check_out_date, total_rooms=2)
        res = create_reservation(guest.id, room_type.id, check_in_date, check_out_date)
        assign_room(res.id, room.id)
        return check_in(res.id)

    def test_checks_out_and_frees_room(self, checked_in_reservation, room):
        checked_out = check_out(checked_in_reservation.id)

        assert checked_out.status == Reservation.Status.CHECKED_OUT
        room.refresh_from_db()
        assert room.status == RoomStatus.CLEANING

    def test_checks_out_and_releases_inventory(self, checked_in_reservation, room_type, date_range):
        check_in_date, check_out_date = date_range

        check_out(checked_in_reservation.id)

        rows = RoomInventory.objects.filter(room_type=room_type, date__gte=check_in_date, date__lt=check_out_date)
        assert all(row.booked_rooms == 0 for row in rows)

    def test_rejects_not_found(self):
        with pytest.raises(ReservationNotFoundError):
            check_out(-1)

    def test_rejects_wrong_state(self, room_type, guest, date_range):
        check_in_date, check_out_date = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in_date, check_out_date, total_rooms=2)
        res = create_reservation(guest.id, room_type.id, check_in_date, check_out_date)

        with pytest.raises(ReservationInvalidStateError):
            check_out(res.id)


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
        assert data["primary_guest"]["id"] == guest.id
        assert data["primary_guest"]["full_name"] == "Ali"
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
