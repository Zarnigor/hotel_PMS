from .base import BaseAppException


class RoomInvalidError(BaseAppException):
    status_code = 400
    default_message = "Xona ma'lumotlari noto'g'ri"
    error_code = "room_invalid"


class RoomNotFoundError(BaseAppException):
    status_code = 404
    default_message = "Xona topilmadi"
    error_code = "room_not_found"


class RoomUnbookableError(BaseAppException):
    status_code = 409
    default_message = "Xona hozircha band qilib bo'lmaydi"
    error_code = "room_unbookable"


class RatePlanNotFoundError(BaseAppException):
    status_code = 404
    default_message = "Berilgan sana uchun narx rejasi topilmadi"
    error_code = "rate_plan_not_found"


class OverbookingError(BaseAppException):
    status_code = 409
    default_message = "Bu sana uchun bo'sh xona qolmadi"
    error_code = "overbooking"