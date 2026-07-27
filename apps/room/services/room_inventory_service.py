import datetime
from datetime import date

from apps.room.utils import RoomUtil

from django.db import transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from apps.room.models import Room, RoomInventory, RoomType
from exceptions import (
    RatePlanNotFoundError,
    OverbookingError,
    InvalidDateRangeError,
)

def _date_range(check_in_date: datetime.date, check_out_date: datetime.date):
    if check_out_date <= check_in_date:
        raise InvalidDateRangeError()
    if check_in_date < datetime.date.today():
        raise InvalidDateRangeError(_("check_in_date o'tib ketgan sana bo'lishi mumkin emas."))
    n_nights = (check_out_date - check_in_date).days
    return [check_in_date + datetime.timedelta(days=i) for i in range(n_nights)]


class RoomInventoryService:
    """Manage room inventory availability across date ranges.

    Public methods:
        - generate_inventory: Create inventory rows for a room type over
          a date range. Idempotent — skips dates that already have rows.
        - reserve_inventory: Decrement available count; raises
          OverbookingError if insufficient stock.
        - release_inventory: Increment available count on cancellation.
    """

    @staticmethod
    @transaction.atomic
    def generate_for_date_range(
        room_type_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
        total_rooms: int,
    ) -> list[RoomInventory]:
        """Generate RoomInventory records for a given date range.

        Verifies that the room_type_id exists, then creates a RoomInventory
        object for each date between start_date and end_date. Dates that
        already have an inventory record are skipped (idempotent) — only
        dates missing from existing_dates get a new record.
        """

        RoomUtil.get_room_type(room_type_id)
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

    @classmethod
    @transaction.atomic
    def reserve(
            cls,
            room_type_id: int,
            check_in_date: datetime.date,
            check_out_date: datetime.date,
            room_count: int,
    ) -> None:
        """Reserve rooms for a date range by incrementing booked_rooms.

        Locks the RoomInventory rows for the given room_type_id and date
        range with select_for_update(), verifies that inventory exists for
        every night in the range and that enough rooms are available on
        each date, then atomically increments booked_rooms by
        total_room_count for all matching rows.
        """
        nights = _date_range(check_in_date, check_out_date)

        rows = list(
            RoomInventory.objects.select_for_update()
            .filter(room_type_id=room_type_id, date__in=nights)
            .order_by("date")
        )

        if len(rows) != len(nights):
            missing = sorted(set(nights) - {row.date for row in rows})
            raise RatePlanNotFoundError(
                _("room_type_id=(room_type_id=%(room_type_id)s) uchun quyidagi sanalarda inventar yo'q: (missing=%(missing)s).")
                % {"room_type_id": room_type_id, "missing": missing}
            )

        for row in rows:
            if row.booked_rooms + room_count > row.total_rooms:
                raise OverbookingError(
                    _("room_type_id=(room_type_id=%(room_type_id)s) uchun (date=%(date)s) sanasida yetarli bo'sh xona yo'q.")
                    % {"room_type_id": room_type_id, "date": row.date}
                )

        RoomInventory.objects.filter(
            id__in=[row.id for row in rows]
        ).update(booked_rooms=F("booked_rooms") + room_count)

    @classmethod
    @transaction.atomic
    def release(
        cls,
        room_type_id: int,
        check_in_date: datetime.date,
        check_out_date: datetime.date,
    ) -> None:
        """Release previously reserved rooms for a date range.

            Locks the RoomInventory rows for the given room_type_id and date
            range with select_for_update(), then decrements booked_rooms by
            room_count for each row — but never below zero. Rows where
            booked_rooms is already 0, or where fewer than room_count rooms
            are booked, are clamped rather than skipped, so booked_rooms
            never goes negative.
        """
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
        """Sync a RoomInventory row's total_rooms with the actual Room count.

        Locks (or creates, if missing) the RoomInventory row for the given
        room_type_id and date, then updates total_rooms to match the current
        count of Room objects for that room_type_id if they differ.
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

    @staticmethod
    @transaction.atomic
    def create_inventory(
            *,
            room_type: RoomType,
            date: datetime.date,
            total_rooms: int,
            booked_rooms: int = 0,
    ) -> RoomInventory:
        """Bitta (room_type, date) juftligi uchun RoomInventory yozuvi yaratadi."""
        return RoomInventory.objects.create(
            room_type=room_type,
            date=date,
            total_rooms=total_rooms,
            booked_rooms=booked_rooms,
        )

    @staticmethod
    @transaction.atomic
    def update_inventory(*, instance: RoomInventory, **validated_data) -> RoomInventory:
        """RoomInventory yozuvini berilgan maydonlar bilan yangilaydi."""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save(update_fields=list(validated_data.keys()) or None)
        return instance

    @staticmethod
    @transaction.atomic
    def bulk_create_inventory(
            *,
            room_type: RoomType,
            start_date: date,
            end_date: date,
            total_rooms: int,
    ) -> list[RoomInventory]:
        """Sana oralig'i uchun ommaviy inventarizatsiya yaratadi (idempotent).

        Allaqachon mavjud (date, room_type) juftliklari qayta yaratilmaydi —
        `unique_inventory_per_date_room_type` constraint asosida filtrlanadi.
        """
        target_dates = list(_date_range(start_date, end_date))

        existing_dates = set(
            RoomInventory.objects.filter(
                room_type=room_type,
                date__in=target_dates,
            ).values_list("date", flat=True)
        )

        new_records = [
            RoomInventory(
                date=day,
                room_type=room_type,
                total_rooms=total_rooms,
                booked_rooms=0,
            )
            for day in target_dates
            if day not in existing_dates
        ]

        return RoomInventory.objects.bulk_create(new_records)
