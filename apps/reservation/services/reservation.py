"""Reservations service — yozish (create/cancel) operatsiyalari, ORM."""

import logging
from datetime import date

from django.db import transaction
from django.db.models import F

from apps.reservation.models import Reservation
from apps.room.models import RoomType, RoomInventory
from apps.reservation.utils.helpers import validate_date_range
from exceptions import (
    BaseAppException,
    OverbookingError,
    ReservationCancelledError,
    ReservationNotFoundError,
    RoomNotFoundError,
    RoomUnbookableError,
)

logger = logging.getLogger(__name__)


@transaction.atomic
def create_reservation(
    guest_name: str,
    room_type_id: int,
    check_in_date: date,
    check_out_date: date,
) -> Reservation:
    """Yangi reservation yaratadi, RoomInventory'ni lock qilib overbookingdan himoyalaydi.

    Raises:
        InvalidDateRangeError: Sana oralig'i noto'g'ri bo'lsa.
        RoomNotFoundError: RoomType topilmasa.
        RoomUnbookableError: RoomType o'chirilgan (is_deleted=True) bo'lsa.
        OverbookingError: Tanlangan kunlardan biri uchun bo'sh xona qolmasa.
    """
    # guest_name is PII — never logged, reservation_id/room_type_id are used
    # as correlators instead.
    logger.info(
        "create_reservation start room_type_id=%s check_in_date=%s check_out_date=%s",
        room_type_id, check_in_date, check_out_date,
    )
    try:
        validate_date_range(check_in_date, check_out_date)

        try:
            room_type = RoomType.objects.get(pk=room_type_id)
        except RoomType.DoesNotExist:
            logger.warning(
                "create_reservation rejected reason=room_type_not_found room_type_id=%s",
                room_type_id,
            )
            raise RoomNotFoundError(f"RoomType topilmadi: id={room_type_id}")

        if room_type.deleted_at is not None:
            logger.warning(
                "create_reservation rejected reason=room_type_deleted room_type_id=%s",
                room_type_id,
            )
            raise RoomUnbookableError(f"RoomType o'chirilgan: id={room_type_id}")

        expected_days = (check_out_date - check_in_date).days

        logger.debug(
            "create_reservation select_for_update room_type_id=%s expected_days=%s",
            room_type_id, expected_days,
        )
        inventory_qs = (
            RoomInventory.objects.select_for_update()
            .filter(room_type_id=room_type_id, date__gte=check_in_date, date__lt=check_out_date)
            .order_by("date")
        )
        inventory_rows = list(inventory_qs)

        if len(inventory_rows) < expected_days:
            logger.warning(
                "create_reservation rejected reason=missing_inventory room_type_id=%s "
                "expected_days=%s found_days=%s",
                room_type_id, expected_days, len(inventory_rows),
            )
            raise OverbookingError("Ba'zi kunlar uchun inventory yozuvi topilmadi")

        for row in inventory_rows:
            if row.booked_rooms >= row.total_rooms:
                logger.warning(
                    "create_reservation rejected reason=overbooking room_type_id=%s date=%s "
                    "booked_rooms=%s total_rooms=%s",
                    room_type_id, row.date, row.booked_rooms, row.total_rooms,
                )
                raise OverbookingError(f"{row.date} kuni bo'sh xona qolmagan")

        logger.debug(
            "create_reservation F() update room_type_id=%s row_count=%s",
            room_type_id, len(inventory_rows),
        )
        inventory_qs.update(booked_rooms=F("booked_rooms") + 1)

        reservation = Reservation.objects.create(
            guest_name=guest_name,
            room_type_id=room_type_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            status=Reservation.Status.PENDING,
        )
    except BaseAppException:
        raise
    except Exception:
        logger.error(
            "create_reservation failed unexpectedly room_type_id=%s check_in_date=%s check_out_date=%s",
            room_type_id, check_in_date, check_out_date, exc_info=True,
        )
        raise

    logger.info(
        "create_reservation success reservation_id=%s room_type_id=%s status=%s",
        reservation.id, room_type_id, reservation.status,
    )
    return reservation


@transaction.atomic
def cancel_reservation(reservation_id: int) -> Reservation:
    """Reservationni bekor qiladi va RoomInventory'dagi joyni bo'shatadi.

    Raises:
        ReservationNotFoundError: Bunday ID topilmasa.
        ReservationCancelledError: Reservation allaqachon bekor qilingan bo'lsa.
    """
    logger.info("cancel_reservation start reservation_id=%s", reservation_id)
    try:
        try:
            reservation = Reservation.objects.select_for_update().get(pk=reservation_id)
        except Reservation.DoesNotExist:
            logger.warning(
                "cancel_reservation rejected reason=not_found reservation_id=%s",
                reservation_id,
            )
            raise ReservationNotFoundError(f"Reservation topilmadi: id={reservation_id}")

        if reservation.status == Reservation.Status.CANCELLED:
            logger.warning(
                "cancel_reservation rejected reason=already_cancelled reservation_id=%s",
                reservation_id,
            )
            raise ReservationCancelledError(
                f"Reservation allaqachon bekor qilingan: id={reservation_id}"
            )

        logger.debug(
            "cancel_reservation F() update reservation_id=%s room_type_id=%s",
            reservation_id, reservation.room_type_id,
        )
        RoomInventory.objects.filter(
            room_type_id=reservation.room_type_id,
            date__gte=reservation.check_in_date,
            date__lt=reservation.check_out_date,
            booked_rooms__gt=0,
        ).update(booked_rooms=F("booked_rooms") - 1)

        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status"])
    except BaseAppException:
        raise
    except Exception:
        logger.error(
            "cancel_reservation failed unexpectedly reservation_id=%s",
            reservation_id, exc_info=True,
        )
        raise

    logger.info("cancel_reservation success reservation_id=%s", reservation_id)
    return reservation