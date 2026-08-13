"""Reservations service — yozish (create/cancel) operatsiyalari, ORM."""

import logging
from datetime import date

from django.db import transaction
from django.db.models import F

from apps.reservation.models import Reservation
from apps.room.models import Room, RoomType, RoomInventory
from apps.room.services import RoomService, RoomStatus
from apps.room.utils import RoomUtil
from apps.guest.utils import GuestUtil
from apps.reservation.utils.helpers import validate_date_range
from exceptions import (
    BaseAppException,
    BookingConflictError,
    OccupancyExceededError,
    OverbookingError,
    ReservationCancelledError,
    ReservationInvalidStateError,
    ReservationNotFoundError,
    RoomNotAssignedError,
    RoomNotFoundError,
    RoomUnbookableError,
)

logger = logging.getLogger(__name__)


@transaction.atomic
def create_reservation(
    guest_id: int,
    room_type_id: int,
    check_in_date: date,
    check_out_date: date,
    guest_count: int = 1,
) -> Reservation:
    logger.info(
        "create_reservation start guest_id=%s room_type_id=%s check_in_date=%s check_out_date=%s "
        "guest_count=%s",
        guest_id, room_type_id, check_in_date, check_out_date, guest_count,
    )
    try:
        validate_date_range(check_in_date, check_out_date)

        GuestUtil.get_guest(guest_id)

        try:
            room_type = RoomType.all_objects.get(pk=room_type_id)
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

        if guest_count > room_type.max_occupancy:
            logger.warning(
                "create_reservation rejected reason=occupancy_exceeded room_type_id=%s "
                "guest_count=%s max_occupancy=%s",
                room_type_id, guest_count, room_type.max_occupancy,
            )
            raise OccupancyExceededError(
                f"Mehmonlar soni ({guest_count}) xona sig'imidan "
                f"({room_type.max_occupancy}) oshib ketdi"
            )

        logger.debug(
            "create_reservation F() update room_type_id=%s row_count=%s",
            room_type_id, len(inventory_rows),
        )
        inventory_qs.update(booked_rooms=F("booked_rooms") + 1)

        reservation = Reservation.objects.create(
            primary_guest_id=guest_id,
            room_type_id=room_type_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            guest_count=guest_count,
            status=Reservation.Status.PENDING,
        )
    except BaseAppException:
        raise
    except Exception:
        logger.error(
            "create_reservation failed unexpectedly guest_id=%s room_type_id=%s check_in_date=%s check_out_date=%s",
            guest_id, room_type_id, check_in_date, check_out_date, exc_info=True,
        )
        raise

    logger.info(
        "create_reservation success reservation_id=%s room_type_id=%s status=%s",
        reservation.id, room_type_id, reservation.status,
    )
    return reservation


@transaction.atomic
def cancel_reservation(reservation_id: int) -> Reservation:
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

        if reservation.status == Reservation.Status.CHECKED_OUT:
            logger.warning(
                "cancel_reservation rejected reason=already_checked_out reservation_id=%s",
                reservation_id,
            )
            raise ReservationInvalidStateError(
                f"Reservation allaqachon check-out qilingan, bekor qilib bo'lmaydi: id={reservation_id}"
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

        if reservation.status == Reservation.Status.CHECKED_IN and reservation.assigned_room_id is not None:
            logger.debug(
                "cancel_reservation room status update reservation_id=%s room_id=%s",
                reservation_id, reservation.assigned_room_id,
            )
            RoomService.change_status(reservation.assigned_room_id, RoomStatus.CLEANING)

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


@transaction.atomic
def assign_room(reservation_id: int, room_id: int) -> Reservation:
    logger.info("assign_room start reservation_id=%s room_id=%s", reservation_id, room_id)
    try:
        try:
            reservation = Reservation.objects.select_for_update().get(pk=reservation_id)
        except Reservation.DoesNotExist:
            logger.warning("assign_room rejected reason=not_found reservation_id=%s", reservation_id)
            raise ReservationNotFoundError(f"Reservation topilmadi: id={reservation_id}")

        if reservation.status != Reservation.Status.PENDING:
            logger.warning(
                "assign_room rejected reason=invalid_state reservation_id=%s status=%s",
                reservation_id, reservation.status,
            )
            raise ReservationInvalidStateError(
                f"Reservation xona biriktirish uchun mos holatda emas: "
                f"id={reservation_id} status={reservation.status}"
            )

        room = RoomUtil.get_bookable_room(room_id)

        if reservation.guest_count > room.room_type.max_occupancy:
            logger.warning(
                "assign_room rejected reason=occupancy_exceeded reservation_id=%s room_id=%s "
                "guest_count=%s max_occupancy=%s",
                reservation_id, room_id, reservation.guest_count, room.room_type.max_occupancy,
            )
            raise OccupancyExceededError(
                f"Mehmonlar soni ({reservation.guest_count}) xona sig'imidan "
                f"({room.room_type.max_occupancy}) oshib ketdi"
            )

        Room.objects.select_for_update().get(pk=room.id)

        conflict_exists = (
            Reservation.objects
            .filter(
                assigned_room_id=room.id,
                status__in=[Reservation.Status.PENDING, Reservation.Status.CHECKED_IN],
                check_in_date__lt=reservation.check_out_date,
                check_out_date__gt=reservation.check_in_date,
            )
            .exclude(pk=reservation.id)
            .exists()
        )
        if conflict_exists:
            logger.warning(
                "assign_room rejected reason=room_conflict reservation_id=%s room_id=%s",
                reservation_id, room_id,
            )
            raise BookingConflictError(
                f"Xona (id={room_id}) berilgan sanalar uchun boshqa reservation bilan band"
            )

        reservation.assigned_room = room
        reservation.save(update_fields=["assigned_room"])
    except BaseAppException:
        raise
    except Exception:
        logger.error(
            "assign_room failed unexpectedly reservation_id=%s room_id=%s",
            reservation_id, room_id, exc_info=True,
        )
        raise

    logger.info("assign_room success reservation_id=%s room_id=%s", reservation_id, room_id)
    return reservation


@transaction.atomic
def check_in(reservation_id: int) -> Reservation:
    logger.info("check_in start reservation_id=%s", reservation_id)
    try:
        try:
            reservation = Reservation.objects.select_for_update().get(pk=reservation_id)
        except Reservation.DoesNotExist:
            logger.warning("check_in rejected reason=not_found reservation_id=%s", reservation_id)
            raise ReservationNotFoundError(f"Reservation topilmadi: id={reservation_id}")

        if reservation.status != Reservation.Status.PENDING:
            logger.warning(
                "check_in rejected reason=invalid_state reservation_id=%s status=%s",
                reservation_id, reservation.status,
            )
            raise ReservationInvalidStateError(
                f"Reservation check-in uchun mos holatda emas: id={reservation_id} status={reservation.status}"
            )

        if reservation.assigned_room_id is None:
            logger.warning(
                "check_in rejected reason=room_not_assigned reservation_id=%s",
                reservation_id,
            )
            raise RoomNotAssignedError(
                f"Reservation uchun xona biriktirilmagan, avval assign_room chaqiring: id={reservation_id}"
            )

        room = RoomUtil.get_room(reservation.assigned_room_id)
        if room.status == RoomStatus.OCCUPIED:
            logger.warning(
                "check_in rejected reason=room_conflict reservation_id=%s room_id=%s",
                reservation_id, reservation.assigned_room_id,
            )
            raise BookingConflictError(
                f"Xona (id={reservation.assigned_room_id}) hozir boshqa reservation tomonidan band"
            )

        reservation.status = Reservation.Status.CHECKED_IN
        reservation.save(update_fields=["status"])

        logger.debug(
            "check_in room status update reservation_id=%s room_id=%s",
            reservation_id, reservation.assigned_room_id,
        )
        RoomService.change_status(reservation.assigned_room_id, RoomStatus.OCCUPIED)
    except BaseAppException:
        raise
    except Exception:
        logger.error(
            "check_in failed unexpectedly reservation_id=%s",
            reservation_id, exc_info=True,
        )
        raise

    logger.info("check_in success reservation_id=%s", reservation_id)
    return reservation


@transaction.atomic
def check_out(reservation_id: int) -> Reservation:
    logger.info("check_out start reservation_id=%s", reservation_id)
    try:
        try:
            reservation = Reservation.objects.select_for_update().get(pk=reservation_id)
        except Reservation.DoesNotExist:
            logger.warning("check_out rejected reason=not_found reservation_id=%s", reservation_id)
            raise ReservationNotFoundError(f"Reservation topilmadi: id={reservation_id}")

        if reservation.status != Reservation.Status.CHECKED_IN:
            logger.warning(
                "check_out rejected reason=invalid_state reservation_id=%s status=%s",
                reservation_id, reservation.status,
            )
            raise ReservationInvalidStateError(
                f"Reservation check-out uchun mos holatda emas: id={reservation_id} status={reservation.status}"
            )

        reservation.status = Reservation.Status.CHECKED_OUT
        reservation.save(update_fields=["status"])

        logger.debug(
            "check_out room status update reservation_id=%s room_id=%s",
            reservation_id, reservation.assigned_room_id,
        )
        RoomService.change_status(reservation.assigned_room_id, RoomStatus.CLEANING)

        logger.debug(
            "check_out F() update reservation_id=%s room_type_id=%s",
            reservation_id, reservation.room_type_id,
        )
        RoomInventory.objects.filter(
            room_type_id=reservation.room_type_id,
            date__gte=reservation.check_in_date,
            date__lt=reservation.check_out_date,
            booked_rooms__gt=0,
        ).update(booked_rooms=F("booked_rooms") - 1)
    except BaseAppException:
        raise
    except Exception:
        logger.error(
            "check_out failed unexpectedly reservation_id=%s",
            reservation_id, exc_info=True,
        )
        raise

    logger.info("check_out success reservation_id=%s", reservation_id)
    return reservation