from .base import BaseAppException
from django.utils.translation import gettext_lazy as _

class RoomInvalidError(BaseAppException):
    status_code = 400
    default_message = _("Xona ma'lumotlari noto'g'ri")
    error_code = _("room_invalid")


class RoomNotFoundError(BaseAppException):
    status_code = 404
    default_message = _("Xona topilmadi")
    error_code = _("room_not_found")


class RoomUnbookableError(BaseAppException):
    status_code = 409
    default_message = _("Xona hozircha band qilib bo'lmaydi")
    error_code = _("room_unbookable")


class RatePlanNotFoundError(BaseAppException):
    status_code = 404
    default_message = _("Berilgan sana uchun narx rejasi topilmadi")
    error_code = _("rate_plan_not_found")


class OverbookingError(BaseAppException):
    status_code = 409
    default_message = _("Bu sana uchun bo'sh xona qolmadi")
    error_code = _("overbooking")