import datetime
from decimal import Decimal

import pytest

from apps.room.models import RoomInventory, RoomType, RoomTypeBase
from apps.room.services import RoomTypeService
from exceptions import RoomInvalidError, RoomNotFoundError


@pytest.mark.django_db
class TestRoomTypeServiceBase:
    def test_create_base(self):
        base = RoomTypeService.create_base("Standard", "Standard room type")

        assert base.name == "Standard"
        assert base.description == "Standard room type"

    def test_create_base_rejects_empty_name(self):
        with pytest.raises(RoomInvalidError):
            RoomTypeService.create_base("")

    def test_update_base(self):
        base = RoomTypeBase.objects.create(name="Standard", description="Standard room type")

        updated = RoomTypeService.update_base(base.id, name="Deluxe")

        assert updated.name == "Deluxe"

    def test_update_base_rejects_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomTypeService.update_base(-1, name="Deluxe")

    def test_delete_base_soft_deletes(self):
        base = RoomTypeBase.objects.create(name="Standard", description="Standard room type")

        RoomTypeService.delete_base(base.id)

        assert not RoomTypeBase.objects.filter(id=base.id).exists()
        assert RoomTypeBase.all_objects.get(id=base.id).deleted_at is not None

    def test_delete_base_rejects_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomTypeService.delete_base(-1)


@pytest.mark.django_db
class TestRoomTypeServiceRoomType:
    @pytest.fixture
    def room_type_base(self):
        return RoomTypeBase.objects.create(name="Standard", description="Standard room type")

    def test_create_room_type(self, room_type_base):
        room_type = RoomTypeService.create_room_type(room_type_base.id, "Standard", Decimal("100.00"))

        assert room_type.name == "Standard"
        assert room_type.base_price == Decimal("100.00")

    def test_create_room_type_generates_inventory_horizon(self, room_type_base):
        room_type = RoomTypeService.create_room_type(room_type_base.id, "Standard", Decimal("100.00"))

        today = datetime.date.today()
        assert RoomInventory.objects.filter(room_type=room_type).count() == 366
        assert RoomInventory.objects.filter(room_type=room_type, date=today).exists()
        assert RoomInventory.objects.filter(
            room_type=room_type, date=today + datetime.timedelta(days=365)
        ).exists()

    def test_create_room_type_rejects_empty_name(self, room_type_base):
        with pytest.raises(RoomInvalidError):
            RoomTypeService.create_room_type(room_type_base.id, "", Decimal("100.00"))

    def test_create_room_type_rejects_negative_base_price(self, room_type_base):
        with pytest.raises(RoomInvalidError):
            RoomTypeService.create_room_type(room_type_base.id, "Standard", Decimal("-1.00"))

    def test_create_room_type_rejects_missing_base(self):
        with pytest.raises(RoomNotFoundError):
            RoomTypeService.create_room_type(-1, "Standard", Decimal("100.00"))

    def test_update_price(self, room_type_base):
        room_type = RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

        updated = RoomTypeService.update_price(room_type.id, Decimal("150.00"))

        assert updated.base_price == Decimal("150.00")

    def test_update_price_rejects_negative(self, room_type_base):
        room_type = RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

        with pytest.raises(RoomInvalidError):
            RoomTypeService.update_price(room_type.id, Decimal("-1.00"))

    def test_update_price_rejects_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomTypeService.update_price(-1, Decimal("100.00"))

    def test_update_room_type_updates_allowed_fields(self, room_type_base):
        room_type = RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

        updated = RoomTypeService.update_room_type(room_type.id, name="Deluxe")

        assert updated.name == "Deluxe"

    def test_update_room_type_rejects_negative_base_price(self, room_type_base):
        room_type = RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

        with pytest.raises(RoomInvalidError):
            RoomTypeService.update_room_type(room_type.id, base_price=Decimal("-5.00"))

    def test_update_room_type_rejects_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomTypeService.update_room_type(-1, name="Deluxe")

    def test_delete_room_type_soft_deletes(self, room_type_base):
        room_type = RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)

        RoomTypeService.delete_room_type(room_type.id)

        assert not RoomType.objects.filter(id=room_type.id).exists()
        assert RoomType.all_objects.get(id=room_type.id).deleted_at is not None

    def test_delete_room_type_rejects_not_found(self):
        with pytest.raises(RoomNotFoundError):
            RoomTypeService.delete_room_type(-1)
