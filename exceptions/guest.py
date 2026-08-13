from .base import BaseAppException
from django.utils.translation import gettext_lazy as _


class GuestInvalidError(BaseAppException):
    status_code = 400
    default_message = _("Mehmon ma'lumotlari noto'g'ri")
    error_code = _("guest_invalid")


class GuestNotFoundError(BaseAppException):
    status_code = 404
    default_message = _("Mehmon topilmadi")
    error_code = _("guest_not_found")


class DuplicatePassportError(BaseAppException):
    status_code = 409
    default_message = _("Bu passport raqami bilan mehmon allaqachon mavjud")
    error_code = _("duplicate_passport")
