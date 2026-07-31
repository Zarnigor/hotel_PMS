
import pytest

from apps.room.models import Room, RoomType, RoomTypeBase
from apps.room.services import RoomService
from apps.room.utils.constants import RoomStatus
from exceptions import RoomInvalidError, RoomNotFoundError


@pytest.mark.django_db
class TestRoomServiceCreateRoom:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(
            room_type_base=room_type_base,
            name="Standard",
            base_price=100,
        )

    def test_create_room_rejects_empty_room_number(self, room_type):
        with pytest.raises(RoomInvalidError):
            RoomService.create_room("", room_type.id)

    def test_create_room_rejects_invalid_status(self, room_type):
        with pytest.raises(RoomInvalidError):
            RoomService.create_room("101", room_type.id, status="not-a-status")

    def test_create_room_raises_on_valid_input(self, room_type):
        room = RoomService.create_room("101", room_type.id)

        assert room.room_number == "101"
        assert room.room_type == room_type
        assert room.status == Room.Status.AVAILABLE


@pytest.mark.django_db
class TestRoomServiceChangeStatus:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(
            room_type_base=room_type_base,
            name="Standard",
            base_price=100,
        )

    @pytest.fixture
    def room(self, room_type):
        return Room.objects.create(room_number="101", room_type=room_type)

    def test_change_status_rejects_value_outside_room_status_choices(self, room):
        with pytest.raises(RoomInvalidError):
            RoomService.change_status(room.id, "not-a-status")

    def test_change_status_rejects_room_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomService.change_status(-1, RoomStatus.AVAILABLE)

    def test_change_status_allows_valid_transition(self, room):
        updated = RoomService.change_status(room.id, RoomStatus.OCCUPIED)

        assert updated.status == RoomStatus.OCCUPIED

    def test_change_status_rejects_disallowed_transition(self, room):
        # AVAILABLE -> CLEANING is not in RoomStatus.ALLOWED_TRANSITIONS[AVAILABLE].
        with pytest.raises(RoomInvalidError):
            RoomService.change_status(room.id, RoomStatus.CLEANING)


@pytest.mark.django_db
class TestRoomServiceUpdateRoom:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(
            room_type_base=room_type_base,
            name="Standard",
            base_price=100,
        )

    @pytest.fixture
    def room(self, room_type):
        return Room.objects.create(room_number="101", room_type=room_type)

    def test_update_room_updates_allowed_fields(self, room):
        updated = RoomService.update_room(room.id, room_number="202")
        assert updated.room_number == "202"

    def test_update_room_ignores_disallowed_fields(self, room):
        updated = RoomService.update_room(room.id, status="occupied")
        assert updated.status == Room.Status.AVAILABLE

    def test_update_room_rejects_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomService.update_room(-1, room_number="202")


@pytest.mark.django_db
class TestRoomServiceDeleteRoom:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(
            room_type_base=room_type_base,
            name="Standard",
            base_price=100,
        )

    @pytest.fixture
    def room(self, room_type):
        return Room.objects.create(room_number="101", room_type=room_type)

    def test_delete_room_soft_deletes(self, room):
        RoomService.delete_room(room.id)

        assert not Room.objects.filter(id=room.id).exists()
        assert Room.all_objects.get(id=room.id).deleted_at is not None

    def test_delete_room_rejects_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomService.delete_room(-1)
