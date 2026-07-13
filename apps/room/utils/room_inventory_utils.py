import datetime

from apps.room.models import Room, RoomInventory
from exceptions import (
    RatePlanNotFoundError,
    InvalidDateRangeError,
)
from django.utils.translation import gettext_lazy as _


def _date_range(check_in_date: datetime.date, check_out_date: datetime.date):
    if check_out_date <= check_in_date:
        raise InvalidDateRangeError()
    if check_in_date < datetime.date.today():
        raise InvalidDateRangeError(_("check_in_date o'tib ketgan sana bo'lishi mumkin emas."))
    n_nights = (check_out_date - check_in_date).days
    return [check_in_date + datetime.timedelta(days=i) for i in range(n_nights)]


class RoomInventoryUtil:

    @staticmethod
    def get_for_date(room_type_id: int, date: datetime.date) -> RoomInventory:
        try:
            return RoomInventory.objects.get(room_type_id=room_type_id, date=date)
        except RoomInventory.DoesNotExist:
            raise RatePlanNotFoundError(
                _("room_type_id=(id=%(id)s) uchun (date=%(date)s) sanasida narx/inventar rejasi yo'q.") % {"id": room_type_id, "date": date}
            )

    @staticmethod
    def check_availability(
        room_type_id: int,
        check_in_date: datetime.date,
        check_out_date: datetime.date,
    ) -> bool:
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

