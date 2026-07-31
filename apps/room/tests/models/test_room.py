import pytest
from apps.room.models import Room, RoomType, RoomTypeBase


@pytest.mark.django_db
class TestRoomModel:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(
            room_type_base=room_type_base,
            name="Standard",
            base_price=100
        )

    @pytest.fixture
    def room(self, room_type):
        return Room.objects.create(
            room_number="101 XZQ",
            room_type=room_type,
        )

    def test_str_method(self, room):
        assert str(room) == "101 XZQ"

    def test_default_status(self, room):
        assert room.status == Room.Status.AVAILABLE

    def test_soft_delete(self, room):
        assert room.deleted_at is None

        room.delete()
        room.refresh_from_db()

        assert room.deleted_at is not None

    def test_hard_delete(self, room):
        room_id = room.id
        room.hard_delete()
        assert not Room.all_objects.filter(id=room_id).exists()

    def test_default_manager_excludes_soft_deleted_rooms(self, room):
        room.delete()

        assert not Room.objects.filter(id=room.id).exists()
        assert Room.all_objects.filter(id=room.id).exists()

    def test_create_room(self, room):
        assert room.room_number == "101 XZQ"
        assert room.room_type is not None