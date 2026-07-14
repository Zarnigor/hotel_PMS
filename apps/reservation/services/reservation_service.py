"""Reservations service — raw SQL bilan, mavjud modellarga moslab yozilgan.

Muhim farq: bron alohida `Room` ga emas, `RoomType` + `RoomInventory`
(kunlik total_rooms/booked_rooms hisobiga) asosida qilinadi. `assigned_room`
faqat check-in bosqichida to'ldiriladi, shu sabab bu servis uni ishlatmaydi.

Ishlatiladigan jadvallar (mavjud modellardan):
    - room_types(id, room_type_base_id, name, base_price, created_at,
      is_deleted, deleted_at)
    - room_inventories(id, date, room_type_id, total_rooms, booked_rooms)
    - reservations(id, guess_name, room_type_id, assigned_room_id,
      check_in_date, check_out_date, status, created_at)

Concurrency: `room_inventories` qatorlari `SELECT ... FOR UPDATE` bilan
lock qilinadi, barcha yozish operatsiyalari `transaction.atomic()` ichida.
"""

from datetime import date
from typing import Any

from django.db import connection, transaction

from apps.reservation.utils.helpers import validate_date_range, dictfetchall
from exceptions import (
    OverbookingError,
    ReservationCancelledError,
    ReservationNotFoundError,
    RoomNotFoundError,
    RoomUnbookableError,
)

@transaction.atomic
def create_reservation(
    guess_name: str,
    room_type_id: int,
    check_in_date: date,
    check_out_date: date,
) -> dict[str, Any]:
    """Yangi reservation yaratadi, room_inventories'ni lock qilib overbookingdan himoyalaydi.

    Ishlash tartibi:
        1. RoomType mavjudligi va o'chirilmaganligi tekshiriladi.
        2. check_in_date..check_out_date oralig'idagi room_inventories
           qatorlari `FOR UPDATE` bilan lock qilinadi.
        3. Har bir kun uchun booked_rooms < total_rooms tekshiriladi.
        4. booked_rooms +1 oshiriladi va reservation status='pending' bilan yaratiladi.

    Raises:
        InvalidDateRangeError: Sana oralig'i noto'g'ri bo'lsa.
        RoomNotFoundError: RoomType topilmasa.
        RoomUnbookableError: RoomType o'chirilgan (is_deleted=True) bo'lsa.
        OverbookingError: Tanlangan kunlardan biri uchun bo'sh xona qolmasa.
    """
    validate_date_range(check_in_date, check_out_date)

    with connection.cursor() as cursor:
        # 1. RoomType tekshiruvi
        cursor.execute(
            "SELECT id, is_deleted FROM room_types WHERE id = %s",
            [room_type_id],
        )
        room_type = dictfetchall(cursor)
        if not room_type:
            raise RoomNotFoundError(f"RoomType topilmadi: id={room_type_id}")
        if room_type[0]["is_deleted"]:
            raise RoomUnbookableError(f"RoomType o'chirilgan: id={room_type_id}")

        # 2. Inventory qatorlarini lock qilish (race condition himoyasi)
        cursor.execute(
            """
            SELECT id, date, total_rooms, booked_rooms
            FROM room_inventories
            WHERE room_type_id = %s AND date >= %s AND date < %s
            ORDER BY date
            FOR UPDATE
            """,
            [room_type_id, check_in_date, check_out_date],
        )
        inventory_rows = dictfetchall(cursor)

        expected_days = (check_out_date - check_in_date).days
        if len(inventory_rows) < expected_days:
            raise OverbookingError("Ba'zi kunlar uchun inventory yozuvi topilmadi")

        # 3. Har bir kun uchun bo'sh joy borligini tekshirish
        for row in inventory_rows:
            if row["booked_rooms"] >= row["total_rooms"]:
                raise OverbookingError(f"{row['date']} kuni bo'sh xona qolmagan")

        # 4. Inventoryni band qilish
        cursor.execute(
            """
            UPDATE room_inventories
            SET booked_rooms = booked_rooms + 1
            WHERE room_type_id = %s AND date >= %s AND date < %s
            """,
            [room_type_id, check_in_date, check_out_date],
        )

        # 5. Reservation yaratish
        cursor.execute(
            """
            INSERT INTO reservations
                (guess_name, room_type_id, check_in_date, check_out_date, status, created_at)
            VALUES (%s, %s, %s, %s, 'pending', NOW())
            RETURNING id, guess_name, room_type_id, assigned_room_id,
                      check_in_date, check_out_date, status, created_at
            """,
            [guess_name, room_type_id, check_in_date, check_out_date],
        )
        return dictfetchall(cursor)[0]


@transaction.atomic
def cancel_reservation(reservation_id: int) -> dict[str, Any]:
    """Reservationni bekor qiladi va room_inventories'dagi joyni bo'shatadi.

    Raises:
        ReservationNotFoundError: Bunday ID topilmasa.
        ReservationCancelledError: Reservation allaqachon bekor qilingan bo'lsa.
    """
    with connection.cursor() as cursor:
        # Reservationni lock qilib o'qish
        cursor.execute(
            """
            SELECT id, room_type_id, check_in_date, check_out_date, status
            FROM reservations
            WHERE id = %s
            FOR UPDATE
            """,
            [reservation_id],
        )
        rows = dictfetchall(cursor)
        if not rows:
            raise ReservationNotFoundError(f"Reservation topilmadi: id={reservation_id}")

        reservation = rows[0]
        if reservation["status"] == "cancelled":
            raise ReservationCancelledError(
                f"Reservation allaqachon bekor qilingan: id={reservation_id}"
            )

        # Inventoryni bo'shatish (0 dan pastga tushmasligi uchun GREATEST)
        cursor.execute(
            """
            UPDATE room_inventories
            SET booked_rooms = GREATEST(booked_rooms - 1, 0)
            WHERE room_type_id = %s AND date >= %s AND date < %s
            """,
            [
                reservation["room_type_id"],
                reservation["check_in_date"],
                reservation["check_out_date"],
            ],
        )

        # Reservation statusini yangilash
        cursor.execute(
            """
            UPDATE reservations
            SET status = 'cancelled'
            WHERE id = %s
            RETURNING id, guess_name, room_type_id, assigned_room_id,
                      check_in_date, check_out_date, status, created_at
            """,
            [reservation_id],
        )
        return dictfetchall(cursor)[0]