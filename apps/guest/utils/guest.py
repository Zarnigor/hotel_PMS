import logging

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from apps.guest.models import Guest
from exceptions import GuestNotFoundError

logger = logging.getLogger(__name__)


class GuestUtil:
    @staticmethod
    def get_guest(guest_id: int) -> Guest:
        try:
            return Guest.objects.get(id=guest_id)
        except Guest.DoesNotExist:
            logger.warning("get_guest rejected reason=not_found guest_id=%s", guest_id)
            raise GuestNotFoundError(_("Mehmon (id=%(id)s) topilmadi.") % {"id": guest_id})

    @staticmethod
    def list_guests(country: str | None = None) -> QuerySet[Guest]:
        qs = Guest.objects.all()
        if country is not None:
            qs = qs.filter(country=country)
        return qs.order_by("full_name")
