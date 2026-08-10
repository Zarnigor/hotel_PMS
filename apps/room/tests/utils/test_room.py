import pytest

from apps.room.models import Room, RoomType, RoomTypeBase
from apps.room.utils import RoomUtil
from exceptions import OverbookingError, RoomNotFoundError, RoomUnbookableError


@pytest.mark.django_db
class TestRoomUtilLookups:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

    @pytest.fixture
    def room(self, room_type):
        return Room.objects.create(room_number="101", room_type=room_type)

    def test_get_room_type_base(self, room_type_base):
        assert RoomUtil.get_room_type_base(room_type_base.id) == room_type_base

    def test_get_room_type_base_rejects_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomUtil.get_room_type_base(-1)

    def test_get_room_type(self, room_type):
        assert RoomUtil.get_room_type(room_type.id) == room_type

    def test_get_room_type_rejects_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomUtil.get_room_type(-1)

    def test_get_room(self, room):
        assert RoomUtil.get_room(room.id) == room

    def test_get_room_rejects_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomUtil.get_room(-1)


@pytest.mark.django_db
class TestRoomUtilListing:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def other_room_type_base(self):
        return RoomTypeBase.objects.create(name="Other", description="Other room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(room_type_base=room_type_base, name="Zebra", base_price=100)

    @pytest.fixture
    def other_room_type(self, other_room_type_base):
        return RoomType.objects.create(room_type_base=other_room_type_base, name="Alpha", base_price=50)

    def test_list_room_type_bases_orders_by_name(self, room_type_base, other_room_type_base):
        names = list(RoomUtil.list_room_type_bases().values_list("name", flat=True))
        assert names == ["Other", "Standard"]

    def test_list_room_types_orders_by_name(self, room_type, other_room_type):
        names = list(RoomUtil.list_room_types().values_list("name", flat=True))
        assert names == ["Alpha", "Zebra"]

    def test_list_room_types_filters_by_room_type_base(self, room_type, other_room_type, room_type_base):
        result = list(RoomUtil.list_room_types(room_type_base.id))
        assert result == [room_type]

    def test_list_rooms_orders_by_room_number(self, room_type):
        Room.objects.create(room_number="202", room_type=room_type)
        Room.objects.create(room_number="101", room_type=room_type)

        numbers = list(RoomUtil.list_rooms().values_list("room_number", flat=True))
        assert numbers == ["101", "202"]

    def test_list_rooms_filters_by_room_type(self, room_type, other_room_type):
        matching = Room.objects.create(room_number="101", room_type=room_type)
        Room.objects.create(room_number="201", room_type=other_room_type)

        result = list(RoomUtil.list_rooms(room_type_id=room_type.id))
        assert result == [matching]

    def test_list_rooms_filters_by_status(self, room_type):
        Room.objects.create(room_number="101", room_type=room_type, status=Room.Status.AVAILABLE)
        occupied = Room.objects.create(room_number="102", room_type=room_type, status=Room.Status.OCCUPIED)

        result = list(RoomUtil.list_rooms(status=Room.Status.OCCUPIED))
        assert result == [occupied]


@pytest.mark.django_db
class TestRoomUtilBookability:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

    def test_find_available_room_finds_an_available_room(self, room_type):
        room = Room.objects.create(room_number="101", room_type=room_type, status=Room.Status.AVAILABLE)

        result = RoomUtil.find_available_room(room_type.id)

        assert result == room

    def test_find_available_room_rejects_when_none_available(self, room_type):
        Room.objects.create(room_number="101", room_type=room_type, status=Room.Status.OCCUPIED)

        with pytest.raises(OverbookingError):
            RoomUtil.find_available_room(room_type.id)

    def test_ensure_bookable_rejects_unbookable_status(self, room_type):
        room = Room.objects.create(room_number="101", room_type=room_type, status=Room.Status.MAINTENANCE)

        with pytest.raises(RoomUnbookableError):
            RoomUtil.ensure_bookable(room)

    def test_get_bookable_room_rejects_unbookable_status(self, room_type):
        room = Room.objects.create(room_number="101", room_type=room_type, status=Room.Status.OUT_OF_SERVICE)

        with pytest.raises(RoomUnbookableError):
            RoomUtil.get_bookable_room(room.id)

    def test_get_bookable_room_rejects_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomUtil.get_bookable_room(-1)
