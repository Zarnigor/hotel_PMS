import pytest
from apps.room.models import Room, RoomType, RoomTypeBase


@pytest.mark.django_db
class TestRoomTypeBaseModel:

    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(
            name="Standard",
            description="Standard room type",
        )

    def test_create_room_type_base(self, room_type_base):
        assert room_type_base.name == "Standard"
        assert room_type_base.description == "Standard room type"
        assert room_type_base.created_at is not None

    def test_str_method(self, room_type_base):
        assert str(room_type_base) == "Standard"

    def test_soft_delete(self, room_type_base):
        assert room_type_base.deleted_at is None
        room_type_base.delete()
        room_type_base.refresh_from_db()
        assert room_type_base.deleted_at is not None

    def test_hard_delete(self, room_type_base):
        room_type_base_id = room_type_base.id
        room_type_base.hard_delete()
        assert not RoomTypeBase.all_objects.filter(id=room_type_base_id).exists()

    def test_default_manager_soft_deleted_objects(self, room_type_base):
        room_type_base.delete()

        assert not RoomTypeBase.objects.filter(id=room_type_base.id).exists()
        assert RoomTypeBase.all_objects.filter(id=room_type_base.id).exists()


@pytest.mark.django_db
class TestRoomTypeModel:

    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard XXX", description="Standard room type X")

    @pytest.fixture
    def room_type(self, room_type_base):
        return RoomType.objects.create(
            room_type_base=room_type_base,
            name="Standard",
            base_price=100
        )

    def test_create_room_type(self, room_type):
        assert room_type.name == "Standard"
        assert room_type.base_price == 100
        assert room_type.created_at is not None
        assert room_type.deleted_at is None
        assert room_type.room_type_base is not None

    def test_soft_delete_room_type(self, room_type_base):
        assert room_type_base.deleted_at is None
        room_type_base.delete()
        room_type_base.refresh_from_db()
        assert room_type_base.deleted_at is not None

    def test_hard_delete_room_type(self, room_type_base):
        room_type_base_id = room_type_base.id
        room_type_base.hard_delete()
        assert not RoomTypeBase.all_objects.filter(id=room_type_base_id).exists()

    def test_default_manager_soft_deleted_objects_room_type(self, room_type_base):
        room_type_base.delete()

        assert not RoomTypeBase.objects.filter(id=room_type_base.id).exists()
        assert RoomTypeBase.all_objects.filter(id=room_type_base.id).exists()

