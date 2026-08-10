import logging
import datetime

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.guest.models import Guest
from apps.guest.utils import GuestUtil
from exceptions import GuestInvalidError, DuplicatePassportError

logger = logging.getLogger(__name__)


class GuestService:
    @staticmethod
    def create_guest(
        full_name: str,
        country: str = "",
        birthday: datetime.date | None = None,
        passport: str = "",
    ) -> Guest:
        if not full_name or not full_name.strip():
            logger.warning("create_guest rejected reason=empty_full_name")
            raise GuestInvalidError(_("Mehmon ismi bo'sh bo'lishi mumkin emas"))

        if passport and Guest.objects.filter(passport=passport).exists():
            logger.warning("create_guest rejected reason=duplicate_passport passport=%s", passport)
            raise DuplicatePassportError()

        guest = Guest.objects.create(
            full_name=full_name.strip(),
            country=country or "",
            birthday=birthday,
            passport=passport or "",
        )
        logger.info("create_guest success guest_id=%s", guest.id)
        return guest

    @classmethod
    @transaction.atomic
    def update_guest(cls, guest_id: int, **fields) -> Guest:
        guest = GuestUtil.get_guest(guest_id)

        if "full_name" in fields and not (fields["full_name"] or "").strip():
            logger.warning("update_guest rejected reason=empty_full_name guest_id=%s", guest_id)
            raise GuestInvalidError(_("Mehmon ismi bo'sh bo'lishi mumkin emas"))

        passport = fields.get("passport")
        if passport:
            if Guest.objects.filter(passport=passport).exclude(pk=guest.pk).exists():
                logger.warning(
                    "update_guest rejected reason=duplicate_passport guest_id=%s passport=%s",
                    guest_id, passport,
                )
                raise DuplicatePassportError()

        allowed = {"full_name", "country", "birthday", "passport"}
        update_fields = [key for key in fields if key in allowed]
        for key in update_fields:
            value = fields[key]
            if key == "full_name":
                value = value.strip()
            setattr(guest, key, value)
        guest.save(update_fields=update_fields)
        logger.info("update_guest success guest_id=%s", guest_id)
        return guest

    @classmethod
    @transaction.atomic
    def delete_guest(cls, guest_id: int) -> None:
        guest = GuestUtil.get_guest(guest_id)
        guest.delete()
        logger.info("delete_guest success guest_id=%s", guest_id)
