import datetime

import pytest

from apps.guest.models import Guest
from apps.guest.services import GuestService
from exceptions import DuplicatePassportError, GuestInvalidError, GuestNotFoundError


@pytest.mark.django_db
class TestGuestServiceCreateGuest:
    def test_create_guest_rejects_empty_full_name(self):
        with pytest.raises(GuestInvalidError):
            GuestService.create_guest("")

    def test_create_guest_rejects_blank_full_name(self):
        with pytest.raises(GuestInvalidError):
            GuestService.create_guest("   ")

    def test_create_guest_with_minimal_fields(self):
        guest = GuestService.create_guest("Ali")

        assert guest.full_name == "Ali"
        assert guest.country == ""
        assert guest.birthday is None
        assert guest.passport == ""

    def test_create_guest_with_all_fields(self):
        guest = GuestService.create_guest(
            "Ali", country="Uzbekistan", birthday=datetime.date(1990, 1, 1), passport="AA1111111"
        )

        assert guest.country == "Uzbekistan"
        assert guest.birthday == datetime.date(1990, 1, 1)
        assert guest.passport == "AA1111111"

    def test_create_guest_rejects_duplicate_passport(self):
        GuestService.create_guest("Ali", passport="AA1111111")

        with pytest.raises(DuplicatePassportError):
            GuestService.create_guest("Vali", passport="AA1111111")

    def test_create_guest_allows_multiple_blank_passports(self):
        GuestService.create_guest("Ali")
        guest = GuestService.create_guest("Vali")

        assert guest.passport == ""


@pytest.mark.django_db
class TestGuestServiceUpdateGuest:
    @pytest.fixture
    def guest(self):
        return Guest.objects.create(full_name="Ali")

    def test_update_guest_rejects_not_found(self):
        with pytest.raises(GuestNotFoundError):
            GuestService.update_guest(-1, full_name="Vali")

    def test_update_guest_rejects_empty_full_name(self, guest):
        with pytest.raises(GuestInvalidError):
            GuestService.update_guest(guest.id, full_name="   ")

    def test_update_guest_changes_fields(self, guest):
        updated = GuestService.update_guest(guest.id, full_name="Vali", country="Uzbekistan")

        assert updated.full_name == "Vali"
        assert updated.country == "Uzbekistan"

    def test_update_guest_rejects_duplicate_passport(self, guest):
        Guest.objects.create(full_name="Other", passport="BB2222222")

        with pytest.raises(DuplicatePassportError):
            GuestService.update_guest(guest.id, passport="BB2222222")


@pytest.mark.django_db
class TestGuestServiceDeleteGuest:
    @pytest.fixture
    def guest(self):
        return Guest.objects.create(full_name="Ali")

    def test_delete_guest_rejects_not_found(self):
        with pytest.raises(GuestNotFoundError):
            GuestService.delete_guest(-1)

    def test_delete_guest_removes_row(self, guest):
        GuestService.delete_guest(guest.id)

        assert not Guest.objects.filter(id=guest.id).exists()

    def test_delete_guest_protected_when_referenced_by_reservation(self, guest):
        from django.db.models import ProtectedError

        from apps.reservation.services import create_reservation
        from apps.room.models import RoomType, RoomTypeBase
        from apps.room.services import RoomInventoryService

        room_type_base = RoomTypeBase.objects.create(name="Standard", description="Standard room type")
        room_type = RoomType.objects.create(room_type_base=room_type_base, name="Standard", base_price=100)
        check_in = datetime.date.today() + datetime.timedelta(days=1)
        check_out = check_in + datetime.timedelta(days=2)
        RoomInventoryService.generate_for_date_range(room_type.id, check_in, check_out, total_rooms=1)
        create_reservation(guest.id, room_type.id, check_in, check_out)

        with pytest.raises(ProtectedError):
            GuestService.delete_guest(guest.id)
