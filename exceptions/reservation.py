from .base import BaseAppException
from django.utils.translation import gettext_lazy as _

class BookingConflictError(BaseAppException):
    status_code = 409
    default_message = _("Boshqa booking bilan to'qnashuv mavjud")
    error_code = _("booking_conflict")


class InvalidDateRangeError(BaseAppException):
    status_code = 400
    default_message = _("Check-out sanasi check-in sanasidan oldin bo'lishi mumkin emas")
    error_code = _("invalid_date_range")


class ReservationNotFoundError(BaseAppException):
    status_code = 404
    default_message = _("Bron topilmadi")
    error_code = _("reservation_not_found")


class ReservationCancelledError(BaseAppException):
    status_code = 400
    default_message = _("Bu bron allaqachon bekor qilingan")
    error_code = _("reservation_cancelled")


class OccupancyExceededError(BaseAppException):
    status_code = 400
    default_message = _("Mehmonlar soni xona sig'imidan oshib ketdi")
    error_code = _("occupancy_exceeded")


class ReservationInvalidStateError(BaseAppException):
    status_code = 400
    default_message = _("Reservation bu amal uchun noto'g'ri holatda")
    error_code = _("reservation_invalid_state")


class RoomNotAssignedError(BaseAppException):
    status_code = 400
    default_message = _("Reservationga xona biriktirilmagan — avval xona belgilang")
    error_code = _("room_not_assigned")