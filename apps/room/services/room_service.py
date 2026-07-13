from django.db import transaction

from apps.room.models import Room
from apps.room.services.room_type_service import RoomTypeService
from exceptions import RoomInvalidError

from django.utils.translation import gettext_lazy as _

class RoomStatus:
    AVAILABLE = _("AVAILABLE")
    OCCUPIED = _("OCCUPIED")
    CLEANING = _("CLEANING")
    MAINTENANCE = _("MAINTENANCE")
    OUT_OF_SERVICE = _("OUT_OF_SERVICE")

    CHOICES = (AVAILABLE, OCCUPIED, CLEANING, MAINTENANCE, OUT_OF_SERVICE)

    UNBOOKABLE = {CLEANING, MAINTENANCE, OUT_OF_SERVICE}

    ALLOWED_TRANSITIONS = {
        AVAILABLE: {OCCUPIED, MAINTENANCE, OUT_OF_SERVICE},
        OCCUPIED: {CLEANING, MAINTENANCE},
        CLEANING: {AVAILABLE, MAINTENANCE},
        MAINTENANCE: {AVAILABLE, OUT_OF_SERVICE},
        OUT_OF_SERVICE: {MAINTENANCE, AVAILABLE},
    }


class RoomService:
    @staticmethod
    def create_room(room_number: str, room_type: int, status: str = RoomStatus.AVAILABLE) -> Room:
        """Create a new room by room_number, room_type and status.
            First verifies that the status is valid and room_number is not empty, then creates a new Room object.
        """
        if not room_number:
            raise RoomInvalidError(_("Xona raqami bo'sh bo'lishi munkin emas"))
        if not status in RoomStatus.CHOICES:
            raise RoomInvalidError(_("Xona statusi xato"))
        RoomTypeService.get_room_type(room_type)

        return Room.objects.create(room_number=room_number,room_status=status,room_type=room_type)

    @classmethod
    @transaction.atomic
    def change_status(cls, room_id: int, new_status: str) -> Room:
        """Change the status of the room by room_id.
            Firstly verifies that the new_status is acceptable from room.status
        """


        if new_status not in RoomStatus.CHOICES:
            raise RoomInvalidError(f"'(new_status=%(new_status)s)' — noto'g'ri xona statusi.")

        room = cls.get_room(room_id)
        allowed_next = RoomStatus.ALLOWED_TRANSITIONS.get(room.status, set())
        if new_status not in allowed_next and new_status != room.status:
            raise RoomInvalidError(
                f"Xona '(number=%(number)s)' uchun '(status=%(status)s)' -> '(new_status=%(new_status)s)' o'tishga ruxsat berilmagan." % {"number": room.room_number, "status": room.status, "new_status": new_status}
            )
        room.status = new_status
        room.save(update_fields=["status"])
        return room

    @classmethod
    @transaction.atomic
    def update_room(cls, room_id: int, **fields) -> Room:
        """Update the room by room_id"""

        room = cls.get_room(room_id)
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

        room = cls.get_room(room_id)
        room.delete()