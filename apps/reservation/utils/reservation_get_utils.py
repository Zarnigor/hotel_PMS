from typing import Any

from django.db import connection

from apps.reservation.utils.helpers import dictfetchall
from exceptions import ReservationNotFoundError


def get_reservation(reservation_id: int) -> dict[str, Any]:
    """ID bo'yicha bitta reservationni qaytaradi.

    Raises:
        ReservationNotFoundError: Bunday ID topilmasa.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, guess_name, room_type_id, assigned_room_id,
                   check_in_date, check_out_date, status, created_at
            FROM reservations
            WHERE id = %s
            """,
            [reservation_id],
        )
        rows = dictfetchall(cursor)

    if not rows:
        raise ReservationNotFoundError(f"Reservation topilmadi: id={reservation_id}")
    return rows[0]


def list_reservations(
    room_type_id: int | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """
    Filtrlar bo'yicha reservationlar ro'yxatini qaytaradi.
    """
    conditions = []
    params: list[Any] = []

    if room_type_id is not None:
        conditions.append("room_type_id = %s")
        params.append(room_type_id)
    if status is not None:
        conditions.append("status = %s")
        params.append(status)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT id, guess_name, room_type_id, assigned_room_id,
               check_in_date, check_out_date, status, created_at
        FROM reservations
        {where_clause}
        ORDER BY check_in_date DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return dictfetchall(cursor)

