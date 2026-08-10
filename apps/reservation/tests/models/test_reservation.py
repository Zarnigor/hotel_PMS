import datetime
import pytest
from apps.reservation.models import Reservation
from apps.room.models import RoomType, RoomTypeBase
from apps.guest.models import Guest


@pytest.mark.django_db
class TestReservationModel:
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
    def reservation(self, room_type, guest):
        return Reservation.objects.create(
            guest=guest,
            room_type=room_type,
            check_in_date=datetime.date.today() + datetime.timedelta(days=1),
            check_out_date=datetime.date.today() + datetime.timedelta(days=3),
        )

    def test_create_reservation(self, reservation, guest):
        assert reservation.guest == guest
        assert reservation.assigned_room is None
        assert reservation.created_at is not None

    def test_str_method(self, reservation):
        assert str(reservation) == "Ali"

    def test_default_status(self, reservation):
        assert reservation.status == Reservation.Status.PENDING

    def test_room_type_protected_on_delete(self, reservation, room_type):
        from django.db.models import ProtectedError

        with pytest.raises(ProtectedError):
            room_type.hard_delete()
