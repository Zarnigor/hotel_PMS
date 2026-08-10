import datetime
import logging

import exceptions

from apps.room.models import RoomInventory
from django.utils.translation import gettext_lazy as _

from apps.room.utils.helpers import date_range as _date_range

logger = logging.getLogger(__name__)


class RoomInventoryUtil:

    @staticmethod
    def get_for_date(room_type_id: int, date: datetime.date) -> RoomInventory:
        """get room inventory for given date and room type."""
        try:
            return RoomInventory.objects.get(room_type_id=room_type_id, date=date)
        except RoomInventory.DoesNotExist:
            logger.warning(
                "get_for_date rejected reason=not_found room_type_id=%s date=%s",
                room_type_id, date,
            )
            raise exceptions.RatePlanNotFoundError(
                _("room_type_id=(id=%(id)s) uchun (date=%(date)s) sanasida narx/inventar rejasi yo'q.") % {"id": room_type_id, "date": date}
            )

    @staticmethod
    def check_availability(
        room_type_id: int,
        check_in_date: datetime.date,
        check_out_date: datetime.date,
    ) -> bool:
        """Check availability of room inventory."""
        nights = _date_range(check_in_date, check_out_date)

        logger.debug(
            "check_availability query room_type_id=%s nights=%s",
            room_type_id, len(nights),
        )
        rows = {
            row.date: row
            for row in RoomInventory.objects.filter(
                room_type_id=room_type_id,
                date__in=nights,
            )
        }

        for night in nights:
            row = rows.get(night)
            if row is None or row.booked_rooms >= row.total_rooms:
                return False
        return True

