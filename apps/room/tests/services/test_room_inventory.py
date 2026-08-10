import datetime

import pytest

from apps.room.models import RoomInventory, RoomType, RoomTypeBase
from apps.room.services import RoomInventoryService
from exceptions import InvalidDateRangeError, OverbookingError, RatePlanNotFoundError, RoomNotFoundError


@pytest.mark.django_db
class TestGenerateForDateRange:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

    def test_creates_a_row_for_each_date_inclusive(self, room_type):
        start = datetime.date.today()
        end = start + datetime.timedelta(days=2)

        created = RoomInventoryService.generate_for_date_range(room_type.id, start, end, total_rooms=5)

        assert len(created) == 3
        assert RoomInventory.objects.filter(room_type=room_type).count() == 3

    def test_is_idempotent_for_existing_dates(self, room_type):
        start = datetime.date.today()
        end = start + datetime.timedelta(days=1)

        RoomInventoryService.generate_for_date_range(room_type.id, start, end, total_rooms=5)
        second = RoomInventoryService.generate_for_date_range(room_type.id, start, end, total_rooms=5)

        assert second == []
        assert RoomInventory.objects.filter(room_type=room_type).count() == 2

    def test_rejects_end_before_start(self, room_type):
        start = datetime.date.today()
        end = start - datetime.timedelta(days=1)

        with pytest.raises(InvalidDateRangeError):
            RoomInventoryService.generate_for_date_range(room_type.id, start, end, total_rooms=5)

    def test_rejects_missing_room_type(self):
        start = datetime.date.today()
        end = start + datetime.timedelta(days=1)

        with pytest.raises(RoomNotFoundError):
            RoomInventoryService.generate_for_date_range(-1, start, end, total_rooms=5)


@pytest.mark.django_db
class TestReserveAndRelease:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

    @pytest.fixture
    def date_range(self):
        start = datetime.date.today() + datetime.timedelta(days=1)
        end = start + datetime.timedelta(days=2)
        return start, end

    def test_reserve_increments_booked_rooms_for_each_night(self, room_type, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=3)

        RoomInventoryService.reserve(room_type.id, check_in, check_out, room_count=2)

        rows = RoomInventory.objects.filter(room_type=room_type, date__gte=check_in, date__lt=check_out)
        assert all(row.booked_rooms == 2 for row in rows)

    def test_reserve_rejects_overbooking(self, room_type, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=1)

        with pytest.raises(OverbookingError):
            RoomInventoryService.reserve(room_type.id, check_in, check_out, room_count=2)

    def test_reserve_rejects_missing_inventory(self, room_type, date_range):
        check_in, check_out = date_range

        with pytest.raises(RatePlanNotFoundError):
            RoomInventoryService.reserve(room_type.id, check_in, check_out, room_count=1)

    def test_release_decrements_booked_rooms_by_one(self, room_type, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=3)
        RoomInventoryService.reserve(room_type.id, check_in, check_out, room_count=2)

        RoomInventoryService.release(room_type.id, check_in, check_out)

        rows = RoomInventory.objects.filter(room_type=room_type, date__gte=check_in, date__lt=check_out)
        assert all(row.booked_rooms == 1 for row in rows)

    def test_release_never_goes_below_zero(self, room_type, date_range):
        check_in, check_out = date_range
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=3)

        RoomInventoryService.release(room_type.id, check_in, check_out)

        rows = RoomInventory.objects.filter(room_type=room_type, date__gte=check_in, date__lt=check_out)
        assert all(row.booked_rooms == 0 for row in rows)


@pytest.mark.django_db
class TestSyncTotalRooms:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

    def test_creates_row_when_missing(self, room_type):
        target_date = datetime.date.today()

        row = RoomInventoryService.sync_total_rooms(room_type.id, target_date)

        assert row.total_rooms == 0
        assert row.date == target_date

    def test_updates_existing_row_to_match_actual_room_count(self, room_type):
        from apps.room.models import Room

        target_date = datetime.date.today()
        RoomInventory.objects.create(room_type=room_type, date=target_date, total_rooms=0)
        Room.objects.create(room_number="101", room_type=room_type)
        Room.objects.create(room_number="102", room_type=room_type)

        row = RoomInventoryService.sync_total_rooms(room_type.id, target_date)

        assert row.total_rooms == 2


@pytest.mark.django_db
class TestCreateAndUpdateInventory:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

    def test_create_inventory(self, room_type):
        target_date = datetime.date.today()

        inventory = RoomInventoryService.create_inventory(
            room_type=room_type, date=target_date, total_rooms=10, booked_rooms=1
        )

        assert inventory.total_rooms == 10
        assert inventory.booked_rooms == 1

    def test_update_inventory(self, room_type):
        target_date = datetime.date.today()
        inventory = RoomInventory.objects.create(room_type=room_type, date=target_date, total_rooms=10)

        updated = RoomInventoryService.update_inventory(instance=inventory, total_rooms=15)

        assert updated.total_rooms == 15

    def test_bulk_create_inventory_skips_existing_dates(self, room_type):
        start = datetime.date.today() + datetime.timedelta(days=10)
        end = start + datetime.timedelta(days=2)
        RoomInventory.objects.create(room_type=room_type, date=start, total_rooms=4)

        created = RoomInventoryService.bulk_create_inventory(
            room_type=room_type, start_date=start, end_date=end, total_rooms=4
        )

        assert len(created) == 1
        assert created[0].date == start + datetime.timedelta(days=1)

    def test_bulk_create_inventory_rejects_end_before_start(self, room_type):
        start = datetime.date.today() + datetime.timedelta(days=10)
        end = start - datetime.timedelta(days=1)

        with pytest.raises(InvalidDateRangeError):
            RoomInventoryService.bulk_create_inventory(
                room_type=room_type, start_date=start, end_date=end, total_rooms=4
            )
