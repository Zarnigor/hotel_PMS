import datetime
import logging
from datetime import date

from apps.room.utils import RoomUtil
from apps.room.utils.helpers import date_range as _date_range

from django.db import transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from apps.room.models import Room, RoomInventory, RoomType
from exceptions import (
    BaseAppException,
    RatePlanNotFoundError,
    OverbookingError,
    InvalidDateRangeError,
)

logger = logging.getLogger(__name__)


class RoomInventoryService:
    @staticmethod
    @transaction.atomic
    def generate_for_date_range(
        room_type_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
        total_rooms: int,
    ) -> list[RoomInventory]:

        RoomUtil.get_room_type(room_type_id)
        if end_date < start_date:
            logger.warning(
                "generate_for_date_range rejected reason=end_before_start "
                "room_type_id=%s start_date=%s end_date=%s",
                room_type_id, start_date, end_date,
            )
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
        logger.debug(
            "generate_for_date_range bulk_create room_type_id=%s row_count=%s",
            room_type_id, len(to_create),
        )
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
        logger.info(
            "reserve_inventory start room_type_id=%s check_in_date=%s check_out_date=%s room_count=%s",
            room_type_id, check_in_date, check_out_date, room_count,
        )
        try:
            nights = _date_range(check_in_date, check_out_date)

            logger.debug(
                "reserve_inventory select_for_update room_type_id=%s nights=%s",
                room_type_id, len(nights),
            )
            rows = list(
                RoomInventory.objects.select_for_update()
                .filter(room_type_id=room_type_id, date__in=nights)
                .order_by("date")
            )

            if len(rows) != len(nights):
                missing = sorted(set(nights) - {row.date for row in rows})
                logger.warning(
                    "reserve_inventory rejected reason=missing_inventory room_type_id=%s missing=%s",
                    room_type_id, missing,
                )
                raise RatePlanNotFoundError(
                    _("room_type_id=(room_type_id=%(room_type_id)s) uchun quyidagi sanalarda inventar yo'q: (missing=%(missing)s).")
                    % {"room_type_id": room_type_id, "missing": missing}
                )

            for row in rows:
                if row.booked_rooms + room_count > row.total_rooms:
                    logger.warning(
                        "reserve_inventory rejected reason=overbooking room_type_id=%s date=%s "
                        "booked_rooms=%s total_rooms=%s room_count=%s",
                        room_type_id, row.date, row.booked_rooms, row.total_rooms, room_count,
                    )
                    raise OverbookingError(
                        _("room_type_id=(room_type_id=%(room_type_id)s) uchun (date=%(date)s) sanasida yetarli bo'sh xona yo'q.")
                        % {"room_type_id": room_type_id, "date": row.date}
                    )

            logger.debug(
                "reserve_inventory F() update room_type_id=%s row_count=%s increment=%s",
                room_type_id, len(rows), room_count,
            )
            RoomInventory.objects.filter(
                id__in=[row.id for row in rows]
            ).update(booked_rooms=F("booked_rooms") + room_count)
        except BaseAppException:
            raise
        except Exception:
            logger.error(
                "reserve_inventory failed unexpectedly room_type_id=%s check_in_date=%s check_out_date=%s",
                room_type_id, check_in_date, check_out_date, exc_info=True,
            )
            raise

        logger.info(
            "reserve_inventory success room_type_id=%s check_in_date=%s check_out_date=%s room_count=%s",
            room_type_id, check_in_date, check_out_date, room_count,
        )

    @classmethod
    @transaction.atomic
    def release(
        cls,
        room_type_id: int,
        check_in_date: datetime.date,
        check_out_date: datetime.date,
    ) -> None:
        logger.info(
            "release_inventory start room_type_id=%s check_in_date=%s check_out_date=%s",
            room_type_id, check_in_date, check_out_date,
        )
        try:
            nights = _date_range(check_in_date, check_out_date)

            logger.debug(
                "release_inventory select_for_update room_type_id=%s nights=%s",
                room_type_id, len(nights),
            )
            rows = list(
                RoomInventory.objects.select_for_update()
                .filter(room_type_id=room_type_id, date__in=nights)
            )
            releasable_ids = [row.id for row in rows if row.booked_rooms > 0]
            logger.debug(
                "release_inventory F() update room_type_id=%s row_count=%s",
                room_type_id, len(releasable_ids),
            )
            RoomInventory.objects.filter(id__in=releasable_ids).update(
                booked_rooms=F("booked_rooms") - 1
            )
        except BaseAppException:
            raise
        except Exception:
            logger.error(
                "release_inventory failed unexpectedly room_type_id=%s check_in_date=%s check_out_date=%s",
                room_type_id, check_in_date, check_out_date, exc_info=True,
            )
            raise

        logger.info(
            "release_inventory success room_type_id=%s check_in_date=%s check_out_date=%s",
            room_type_id, check_in_date, check_out_date,
        )

    @staticmethod
    @transaction.atomic
    def sync_total_rooms(room_type_id: int, date: datetime.date) -> RoomInventory:
        actual_count = Room.objects.filter(room_type_id=room_type_id).count()
        row, _created = RoomInventory.objects.select_for_update().get_or_create(
            room_type_id=room_type_id,
            date=date,
            defaults={"total_rooms": actual_count, "booked_rooms": 0},
        )
        if row.total_rooms != actual_count:
            logger.debug(
                "sync_total_rooms update room_type_id=%s date=%s total_rooms=%s->%s",
                room_type_id, date, row.total_rooms, actual_count,
            )
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

        logger.debug(
            "bulk_create_inventory room_type_id=%s row_count=%s",
            room_type.id, len(new_records),
        )
        return RoomInventory.objects.bulk_create(new_records)
