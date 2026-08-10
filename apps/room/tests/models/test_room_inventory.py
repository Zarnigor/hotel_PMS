import pytest
from datetime import date

from apps.room.models import RoomType, RoomInventory, RoomTypeBase


@pytest.mark.django_db
class TestRoomInventoryModel:
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
    def inventory(self, room_type):
        return RoomInventory.objects.create(
            date=date(2026, 7, 29),
            room_type=room_type,
            total_rooms=20,
            booked_rooms=5,
        )

    def test_create_inventory(self, inventory):
        assert inventory.total_rooms == 20
        assert inventory.booked_rooms == 5
        assert inventory.room_type.name == "Standard"

    def test_str_method(self, inventory):
        assert str(inventory) == f"{inventory.room_type} - {inventory.date}"

    def test_default_booked_rooms(self, room_type):
        inventory = RoomInventory.objects.create(
            date=date(2026, 7, 30),
            room_type=room_type,
            total_rooms=15,
        )

        assert inventory.booked_rooms == 0

    def test_unique_inventory_per_date_and_room_type(self, room_type):
        RoomInventory.objects.create(
            date=date(2026, 7, 29),
            room_type=room_type,
            total_rooms=20,
        )

        with pytest.raises(Exception):
            RoomInventory.objects.create(
                date=date(2026, 7, 29),
                room_type=room_type,
                total_rooms=15,
            )