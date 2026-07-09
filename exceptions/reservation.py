from .base import BaseAppException


class BookingConflictError(BaseAppException):
    status_code = 409
    default_message = "Boshqa booking bilan to'qnashuv mavjud"
    error_code = "booking_conflict"


class InvalidDateRangeError(BaseAppException):
    status_code = 400
    default_message = "Check-out sanasi check-in sanasidan oldin bo'lishi mumkin emas"
    error_code = "invalid_date_range"


class ReservationNotFoundError(BaseAppException):
    status_code = 404
    default_message = "Bron topilmadi"
    error_code = "reservation_not_found"


class ReservationCancelledError(BaseAppException):
    status_code = 400
    default_message = "Bu bron allaqachon bekor qilingan"
    error_code = "reservation_cancelled"