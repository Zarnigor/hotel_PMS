from .base import BaseAppException

from .room import (
    RoomInvalidError,
    RoomNotFoundError,
    RoomUnbookableError,
    RatePlanNotFoundError,
    OverbookingError,
)

from .reservation import (
    BookingConflictError,
    InvalidDateRangeError,
    ReservationNotFoundError,
    ReservationCancelledError,
)

from .guest import (
    GuestInvalidError,
    GuestNotFoundError,
    DuplicatePassportError,
)

from .handlers import custom_exception_handler

__all__ = [
    "BaseAppException",
    "RoomInvalidError", "RoomNotFoundError", "RoomUnbookableError",
    "RatePlanNotFoundError", "OverbookingError",
    "BookingConflictError", "InvalidDateRangeError",
    "ReservationNotFoundError", "ReservationCancelledError",
    "GuestInvalidError", "GuestNotFoundError", "DuplicatePassportError",
    "custom_exception_handler",
]