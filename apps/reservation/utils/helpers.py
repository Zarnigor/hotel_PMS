import logging
from datetime import date
from typing import Any
from django.db.backends.utils import CursorWrapper
from exceptions import InvalidDateRangeError

logger = logging.getLogger(__name__)


def dictfetchall(cursor: CursorWrapper) -> list[dict[str, Any]]:
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]



def validate_date_range(check_in_date: date, check_out_date: date) -> None:
    if check_out_date <= check_in_date:
        logger.warning(
            "validate_date_range rejected reason=check_out_before_check_in "
            "check_in_date=%s check_out_date=%s",
            check_in_date, check_out_date,
        )
        raise InvalidDateRangeError(
            "check_out_date check_in_date dan keyin bo'lishi kerak"
        )


def to_nested(row: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    nested: dict[str, dict[str, Any]] = {}
    for key, value in row.items():
        if "__" in key:
            prefix, field = key.split("__", 1)
            nested.setdefault(prefix, {})[field] = value
        else:
            result[key] = value
    if nested.get("assigned_room", {}).get("id") is None:
        nested["assigned_room"] = None
    result.update(nested)
    return result