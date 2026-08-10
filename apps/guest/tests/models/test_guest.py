import datetime

import pytest

from apps.guest.models import Guest


@pytest.mark.django_db
class TestGuestModel:
    @pytest.fixture
    def guest(self):
        return Guest.objects.create(
            full_name="Ali Valiyev",
            country="Uzbekistan",
            birthday=datetime.date(1990, 1, 1),
            passport="AA1234567",
        )

    def test_create_guest(self, guest):
        assert guest.full_name == "Ali Valiyev"
        assert guest.country == "Uzbekistan"
        assert guest.passport == "AA1234567"
        assert guest.created_at is not None

    def test_str_method(self, guest):
        assert str(guest) == "Ali Valiyev"

    def test_optional_fields_default_blank(self):
        guest = Guest.objects.create(full_name="Bob")

        assert guest.country == ""
        assert guest.birthday is None
        assert guest.passport == ""

    def test_multiple_guests_with_blank_passport_allowed(self):
        Guest.objects.create(full_name="Ali")
        Guest.objects.create(full_name="Vali")

        assert Guest.objects.filter(passport="").count() == 2

    def test_duplicate_passport_rejected(self, guest):
        from django.db import IntegrityError, transaction

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Guest.objects.create(full_name="Boshqa Odam", passport="AA1234567")
