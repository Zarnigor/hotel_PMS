import datetime

import pytest

from apps.room.models import RoomInventory, RoomType, RoomTypeBase
from apps.room.utils import RoomInventoryUtil
from exceptions import RatePlanNotFoundError


@pytest.mark.django_db
class TestRoomInventoryUtilGetForDate:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

    def test_returns_matching_row(self, room_type):
        target_date = datetime.date.today()
        inventory = RoomInventory.objects.create(room_type=room_type, date=target_date, total_rooms=5)

        assert RoomInventoryUtil.get_for_date(room_type.id, target_date) == inventory

    def test_rejects_not_found(self, room_type):
        with pytest.raises(RatePlanNotFoundError):
            RoomInventoryUtil.get_for_date(room_type.id, datetime.date.today())


@pytest.mark.django_db
class TestRoomInventoryUtilCheckAvailability:
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

    def test_false_when_inventory_missing(self, room_type, date_range):
        check_in, check_out = date_range

        assert RoomInventoryUtil.check_availability(room_type.id, check_in, check_out) is False

    def test_false_when_any_night_is_full(self, room_type, date_range):
        check_in, check_out = date_range
        RoomInventory.objects.create(room_type=room_type, date=check_in, total_rooms=1, booked_rooms=0)
        RoomInventory.objects.create(
            room_type=room_type, date=check_in + datetime.timedelta(days=1), total_rooms=1, booked_rooms=1
        )

        assert RoomInventoryUtil.check_availability(room_type.id, check_in, check_out) is False

    def test_true_when_every_night_has_room(self, room_type, date_range):
        check_in, check_out = date_range
        RoomInventory.objects.create(room_type=room_type, date=check_in, total_rooms=1, booked_rooms=0)
        RoomInventory.objects.create(
            room_type=room_type, date=check_in + datetime.timedelta(days=1), total_rooms=1, booked_rooms=0
        )

        assert RoomInventoryUtil.check_availability(room_type.id, check_in, check_out) is True
