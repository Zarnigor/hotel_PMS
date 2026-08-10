import datetime
import logging

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, extend_schema_view

from exceptions import InvalidDateRangeError

logger = logging.getLogger(__name__)


def tagged_viewset_schema(tag: str, extra: set = set()):
    actions = {"list", "retrieve", "create", "update", "partial_update", "destroy"}
    schema_kwargs = {
        action: extend_schema(tags=[tag])
        for action in actions.union(extra)
    }
    return extend_schema_view(**schema_kwargs)


def date_range(check_in_date: datetime.date, check_out_date: datetime.date) -> list[datetime.date]:
    if check_out_date <= check_in_date:
        logger.warning(
            "date_range rejected reason=check_out_before_check_in check_in_date=%s check_out_date=%s",
            check_in_date, check_out_date,
        )
        raise InvalidDateRangeError()
    if check_in_date < datetime.date.today():
        logger.warning(
            "date_range rejected reason=check_in_in_past check_in_date=%s",
            check_in_date,
        )
        raise InvalidDateRangeError(_("check_in_date o'tib ketgan sana bo'lishi mumkin emas."))
    n_nights = (check_out_date - check_in_date).days
    return [check_in_date + datetime.timedelta(days=i) for i in range(n_nights)]
