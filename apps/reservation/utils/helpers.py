from datetime import date
from typing import Any

from django.db.backends.utils import CursorWrapper

def dictfetchall(cursor: CursorWrapper) -> list[dict[str, Any]]:
    """Cursor natijasini list[dict] ko'rinishiga o'giradi."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def validate_date_range(check_in_date: date, check_out_date: date) -> None:
    """check_in_date/check_out_date oralig'ini tekshiradi.

    Raises:
        InvalidDateRangeError: check_out_date check_in_date dan katta bo'lmasa.
    """
    if check_out_date <= check_in_date:
        raise InvalidDateRangeError(
            "check_out_date check_in_date dan keyin bo'lishi kerak"
        )
