import logging

from django.db import transaction
from apps.room.utils.constants import RoomStatus
from apps.room.models import Room
from exceptions import RoomInvalidError
from apps.room.utils import RoomUtil

logger = logging.getLogger(__name__)


class RoomService:
    @staticmethod
    def create_room(room_number: str, room_type: int, status: str = RoomStatus.AVAILABLE) -> Room:
        """Create a new room by room_number, room_type and status.
            First verifies that the status is valid and room_number is not empty, then creates a new Room object.
        """
        if not room_number:
            logger.warning("create_room rejected reason=empty_room_number room_type=%s", room_type)
            raise RoomInvalidError(_("Xona raqami bo'sh bo'lishi munkin emas"))
        if not status in RoomStatus.CHOICES:
            logger.warning(
                "create_room rejected reason=invalid_status room_type=%s status=%s",
                room_type, status,
            )
            raise RoomInvalidError(_("Xona statusi xato"))
        RoomUtil.get_room_type(room_type)

        return Room.objects.create(room_number=room_number,room_status=status,room_type=room_type)

    @classmethod
    @transaction.atomic
    def change_status(cls, room_id: int, new_status: str) -> Room:
        """Change the status of the room by room_id.
            Firstly verifies that the new_status is acceptable from room.status
        """


        logger.info("change_status start room_id=%s new_status=%s", room_id, new_status)
        if new_status not in RoomStatus.CHOICES:
            logger.warning(
                "change_status rejected reason=invalid_status room_id=%s new_status=%s",
                room_id, new_status,
            )
            raise RoomInvalidError(f"'(new_status=%(new_status)s)' — noto'g'ri xona statusi.")

        room = RoomUtil.get_room(room_id)
        allowed_next = RoomStatus.ALLOWED_TRANSITIONS.get(room.status, set())
        if new_status not in allowed_next and new_status != room.status:
            logger.warning(
                "change_status rejected reason=disallowed_transition room_id=%s "
                "status=%s new_status=%s",
                room_id, room.status, new_status,
            )
            raise RoomInvalidError(
                f"Xona '(number=%(number)s)' uchun '(status=%(status)s)' -> '(new_status=%(new_status)s)' o'tishga ruxsat berilmagan." % {"number": room.room_number, "status": room.status, "new_status": new_status}
            )
        room.status = new_status
        room.save(update_fields=["status"])
        logger.info("change_status success room_id=%s status=%s", room_id, new_status)
        return room

    @classmethod
    @transaction.atomic
    def update_room(cls, room_id: int, **fields) -> Room:
        """Update the room by room_id"""

        room = RoomUtil.get_room(room_id)
        allowed = {"room_number", "room_type_id"}
        for key, value in fields.items():
            if key in allowed:
                setattr(room, key, value)
        room.save(update_fields=[k for k in fields if k in allowed])
        return room

    @classmethod
    @transaction.atomic
    def delete_room(cls, room_id: int) -> None:
        """Delete the room by room_id"""

        room = RoomUtil.get_room(room_id)
        room.delete()
        logger.info("delete_room success room_id=%s", room_id)