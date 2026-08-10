"""Reservation'lar uchun o'qish (get/list) funksiyalari — raw SQL, side-effect yo'q."""

import logging
from datetime import date
from typing import Any

from django.db import connection

from apps.reservation.utils.helpers import dictfetchall, to_nested
from exceptions import ReservationNotFoundError

logger = logging.getLogger(__name__)


_BASE_SELECT = """
    SELECT
        r.id, r.check_in_date, r.check_out_date,
        r.status, r.created_at,
        g.id AS guest__id, g.full_name AS guest__full_name,
        rt.id AS room_type__id, rt.name AS room_type__name, rt.base_price AS room_type__base_price,
        room.id AS assigned_room__id, room.room_number AS assigned_room__number
    FROM reservations r
    INNER JOIN guests g ON g.id = r.guest_id
    INNER JOIN room_types rt ON rt.id = r.room_type_id
    LEFT JOIN rooms room ON room.id = r.assigned_room_id
"""


def get_reservation(reservation_id: int) -> dict[str, Any]:
    """ID bo'yicha bitta reservationni nested bilan qaytaradi.

    Raises:
        ReservationNotFoundError: Bunday ID topilmasa.
    """
    logger.debug("get_reservation raw_sql reservation_id=%s", reservation_id)
    with connection.cursor() as cursor:
        cursor.execute(f"{_BASE_SELECT} WHERE r.id = %s", [reservation_id])
        rows = dictfetchall(cursor)
    if not rows:
        logger.warning(
            "get_reservation rejected reason=not_found reservation_id=%s",
            reservation_id,
        )
        raise ReservationNotFoundError(f"Reservation topilmadi: id={reservation_id}")
    return to_nested(rows[0])


def list_reservations(
    room_type_id: int | None = None,
    status: str | None = None,
    check_in_date_after: date | None = None,
    check_in_date_before: date | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """Filtrlar bo'yicha reservationlar ro'yxatini pagination bilan qaytaradi."""
    conditions = []
    params: list[Any] = []
    if room_type_id is not None:
        conditions.append("r.room_type_id = %s")
        params.append(room_type_id)
    if status is not None:
        conditions.append("r.status = %s")
        params.append(status)
    if check_in_date_after is not None:
        conditions.append("r.check_in_date >= %s")
        params.append(check_in_date_after)
    if check_in_date_before is not None:
        conditions.append("r.check_in_date <= %s")
        params.append(check_in_date_before)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    logger.debug(
        "list_reservations raw_sql room_type_id=%s status=%s limit=%s offset=%s",
        room_type_id, status, limit, offset,
    )
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM reservations r {where_clause}", params)
        total_count = cursor.fetchone()[0]

        cursor.execute(
            f"{_BASE_SELECT} {where_clause} ORDER BY r.check_in_date DESC LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        rows = dictfetchall(cursor)

    return {
        "count": total_count,
        "limit": limit,
        "offset": offset,
        "results": [to_nested(row) for row in rows],
    }