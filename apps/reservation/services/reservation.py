"""Reservations service — yozish (create/cancel) operatsiyalari, ORM."""

from datetime import date

from django.db import transaction
from django.db.models import F

from apps.reservation.models import Reservation
from apps.room.models import RoomType, RoomInventory
from apps.reservation.utils.helpers import validate_date_range
from exceptions import (
    OverbookingError,
    ReservationCancelledError,
    ReservationNotFoundError,
    RoomNotFoundError,
    RoomUnbookableError,
)


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
    validate_date_range(check_in_date, check_out_date)

    try:
        room_type = RoomType.objects.get(pk=room_type_id)
    except RoomType.DoesNotExist:
        raise RoomNotFoundError(f"RoomType topilmadi: id={room_type_id}")

    if room_type.deleted_at is not None:
        raise RoomUnbookableError(f"RoomType o'chirilgan: id={room_type_id}")

    expected_days = (check_out_date - check_in_date).days

    inventory_qs = (
        RoomInventory.objects.select_for_update()
        .filter(room_type_id=room_type_id, date__gte=check_in_date, date__lt=check_out_date)
        .order_by("date")
    )
    inventory_rows = list(inventory_qs)

    if len(inventory_rows) < expected_days:
        raise OverbookingError("Ba'zi kunlar uchun inventory yozuvi topilmadi")

    for row in inventory_rows:
        if row.booked_rooms >= row.total_rooms:
            raise OverbookingError(f"{row.date} kuni bo'sh xona qolmagan")

    inventory_qs.update(booked_rooms=F("booked_rooms") + 1)

    return Reservation.objects.create(
        guest_name=guest_name,
        room_type_id=room_type_id,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        status=Reservation.Status.PENDING,
    )


@transaction.atomic
def cancel_reservation(reservation_id: int) -> Reservation:
    """Reservationni bekor qiladi va RoomInventory'dagi joyni bo'shatadi.

    Raises:
        ReservationNotFoundError: Bunday ID topilmasa.
        ReservationCancelledError: Reservation allaqachon bekor qilingan bo'lsa.
    """
    try:
        reservation = Reservation.objects.select_for_update().get(pk=reservation_id)
    except Reservation.DoesNotExist:
        raise ReservationNotFoundError(f"Reservation topilmadi: id={reservation_id}")

    if reservation.status == Reservation.Status.CANCELLED:
        raise ReservationCancelledError(
            f"Reservation allaqachon bekor qilingan: id={reservation_id}"
        )

    RoomInventory.objects.filter(
        room_type_id=reservation.room_type_id,
        date__gte=reservation.check_in_date,
        date__lt=reservation.check_out_date,
        booked_rooms__gt=0,
    ).update(booked_rooms=F("booked_rooms") - 1)

    reservation.status = Reservation.Status.CANCELLED
    reservation.save(update_fields=["status"])

    return reservation