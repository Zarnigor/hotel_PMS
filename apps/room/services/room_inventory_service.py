import datetime

from django.db import transaction
from django.db.models import F

from apps.room.models import Room, RoomInventory
from exceptions import (
    RatePlanNotFoundError,
    OverbookingError,
    InvalidDateRangeError,
)
from .room_type_service import RoomTypeService
from django.utils.translation import gettext_lazy as _


def _date_range(check_in_date: datetime.date, check_out_date: datetime.date):
    if check_out_date <= check_in_date:
        raise InvalidDateRangeError()
    if check_in_date < datetime.date.today():
        raise InvalidDateRangeError(_("check_in_date o'tib ketgan sana bo'lishi mumkin emas."))
    n_nights = (check_out_date - check_in_date).days
    return [check_in_date + datetime.timedelta(days=i) for i in range(n_nights)]


class RoomInventoryService:
    """
    Manage room inventory on all actions on room management.
    What can the service do:
        -
        -
        -
    """
    @staticmethod
    def get_for_date(room_type_id: int, date: datetime.date) -> RoomInventory:
        try:
            return RoomInventory.objects.get(room_type_id=room_type_id, date=date)
        except RoomInventory.DoesNotExist:
            raise RatePlanNotFoundError(
                _("room_type_id=(id=%(id)s) uchun (date=%(date)) sanasida narx/inventar rejasi yo'q.") % {"id": room_type_id, "date": date}
            )

    @staticmethod
    @transaction.atomic
    def generate_for_date_range(
        room_type_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
        total_rooms: int,
    ) -> list[RoomInventory]:
        RoomTypeService.get_room_type(room_type_id)
        if end_date < start_date:
            raise InvalidDateRangeError(_("end_date start_date dan oldin bo'lishi mumkin emas."))

        existing_dates = set(
            RoomInventory.objects.filter(
                room_type_id=room_type_id,
                date__range=(start_date, end_date),
            ).values_list("date", flat=True)
        )

        n_days = (end_date - start_date).days + 1
        to_create = [
            RoomInventory(
                room_type_id=room_type_id,
                date=start_date + datetime.timedelta(days=i),
                total_rooms=total_rooms,
                booked_rooms=0,
            )
            for i in range(n_days)
            if (start_date + datetime.timedelta(days=i)) not in existing_dates
        ]
        return RoomInventory.objects.bulk_create(to_create)

    @staticmethod
    def check_availability(
        room_type_id: int,
        check_in_date: datetime.date,
        check_out_date: datetime.date,
    ) -> bool:
        nights = _date_range(check_in_date, check_out_date)

        rows = {
            row.date: row
            for row in RoomInventory.objects.filter(
                room_type_id=room_type_id,
                date__in=nights,
            )
        }

        for night in nights:
            row = rows.get(night)
            if row is None or row.booked_rooms >= row.total_rooms:
                return False
        return True

    @classmethod
    @transaction.atomic
    def reserve(
        cls,
        room_type_id: int,
        check_in_date: datetime.date,
        check_out_date: datetime.date,
    ) -> None:
        nights = _date_range(check_in_date, check_out_date)

        rows = list(
            RoomInventory.objects.select_for_update()
            .filter(room_type_id=room_type_id, date__in=nights)
            .order_by("date")
        )

        if len(rows) != len(nights):
            missing = sorted(set(nights) - {row.date for row in rows})
            raise RatePlanNotFoundError(
                _("room_type_id=(room_type_id=%(room_type_id)s) uchun quyidagi sanalarda inventar yo'q: (missing=%(missing)s).") % {"room_type_id": room_type_id, "missing": missing}
            )

        for row in rows:
            if row.booked_rooms >= row.total_rooms:
                raise OverbookingError(
                    _("room_type_id=(room_type_id=%(room_type_id)s) uchun (date=%(date)s) sanasida bo'sh xona qolmagan.") % {"room_type_id": room_type_id, "date": row.date}
                )

        RoomInventory.objects.filter(
            id__in=[row.id for row in rows]
        ).update(booked_rooms=F("booked_rooms") + 1)

    @classmethod
    @transaction.atomic
    def release(
        cls,
        room_type_id: int,
        check_in_date: datetime.date,
        check_out_date: datetime.date,
    ) -> None:
        nights = _date_range(check_in_date, check_out_date)

        rows = list(
            RoomInventory.objects.select_for_update()
            .filter(room_type_id=room_type_id, date__in=nights)
        )
        RoomInventory.objects.filter(
            id__in=[row.id for row in rows if row.booked_rooms > 0]
        ).update(booked_rooms=F("booked_rooms") - 1)

    @staticmethod
    @transaction.atomic
    def sync_total_rooms(room_type_id: int, date: datetime.date) -> RoomInventory:
        """


        :param room_type_id:
        :param date:
        :return:
        """
        actual_count = Room.objects.filter(room_type_id=room_type_id).count()
        row, _created = RoomInventory.objects.select_for_update().get_or_create(
            room_type_id=room_type_id,
            date=date,
            defaults={"total_rooms": actual_count, "booked_rooms": 0},
        )
        if row.total_rooms != actual_count:
            row.total_rooms = actual_count
            row.save(update_fields=["total_rooms"])
        return row