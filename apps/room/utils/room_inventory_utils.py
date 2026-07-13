import datetime
import exceptions

from apps.room.models import RoomInventory
from django.utils.translation import gettext_lazy as _

from apps.room.services.room_inventory_service import _date_range


class RoomInventoryUtil:

    @staticmethod
    def get_for_date(room_type_id: int, date: datetime.date) -> RoomInventory:
        """get room inventory for given date and room type."""
        try:
            return RoomInventory.objects.get(room_type_id=room_type_id, date=date)
        except RoomInventory.DoesNotExist:
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

