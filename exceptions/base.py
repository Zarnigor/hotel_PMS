from django.utils.translation import gettext_lazy as _

class BaseAppException(Exception):
    """Barcha custom exception'lar shu klassdan meros oladi"""
    status_code = 400
    default_message = _("Xatolik yuz berdi")
    error_code = "error"

    def __init__(self, message=None, error_code=None, extra=None):
        self.message = message or self.default_message
        self.error_code = error_code or self.error_code
        self.extra = extra or {}
        super().__init__(self.message)