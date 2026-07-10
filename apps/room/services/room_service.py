from decimal import Decimal

from django.db import transaction
from django.db.models import QuerySet

from apps.room.models import Room, RoomTypeBase
from apps.room.services.room_type_service import RoomTypeService
from exceptions import RoomInvalidError, RoomNotFoundError, RoomUnbookableError, OverbookingError

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
        if not room_number:
            raise RoomInvalidError("Xona raqami bo'sh bo'lishi munkin emas")
        if not status in RoomStatus.CHOICES:
            raise RoomInvalidError("Xona statusi xato")
        RoomTypeService.get_room_type(room_type)

        return Room.objects.create(room_number=room_number,room_status=status,room_type=room_type)


    @staticmethod
    def get_room(room_id: int) -> Room: #room_type
        try:
            return Room.objects.select_related("room_type").get(id=room_id)
        except Room.DoesNotExist:
            raise RoomNotFoundError(f"Xona (id={room_id}) topilmadi.")

    @staticmethod
    def list_rooms(room_type_id: int | None = None, status: str | None = None) -> QuerySet[Room]:
        qs = Room.objects.select_related("room_type").all()
        if room_type_id is not None:
            qs = qs.filter(room_type=room_type_id)
        if status is not None:
            qs = qs.filter(status=status)
        return qs.order_by("room_number")

    @classmethod
    def ensure_bookable(cls, room: Room) -> None:
        """Status check"""
        if room.status in RoomStatus.UNBOOKABLE:
            raise RoomUnbookableError(
                f"Xona '{room.room_number}' hozir '{room.status}' holatida — band qilib bo'lmaydi."
            )

    @classmethod
    @transaction.atomic
    def change_status(cls, room_id: int, new_status: str) -> Room:
        if new_status not in RoomStatus.CHOICES:
            raise RoomInvalidError(f"'{new_status}' — noto'g'ri xona statusi.")

        room = cls.get_room(room_id)
        allowed_next = RoomStatus.ALLOWED_TRANSITIONS.get(room.status, set())
        if new_status not in allowed_next and new_status != room.status:
            raise RoomInvalidError(
                f"Xona '{room.room_number}' uchun '{room.status}' -> '{new_status}' "
                f"o'tishga ruxsat berilmagan."
            )
        room.status = new_status
        room.save(update_fields=["status"])
        return room


    @classmethod
    def find_available_room(cls, room_type_id: int) -> Room:
        room = (
            Room.objects.select_related("room_type")
            .filter(room_type_id=room_type_id, status=RoomStatus.AVAILABLE)
            .first()
        )
        if room is None:
            raise OverbookingError(
                f"room_type_id={room_type_id} uchun hozir bo'sh xona yo'q."
            )
        return room

    @classmethod
    def get_bookable_room(cls, room_id: int) -> Room:
        room = cls.get_room(room_id)
        cls.ensure_bookable(room)
        return room

    @classmethod
    @transaction.atomic
    def update_room(cls, room_id: int, **fields) -> Room:
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
        room = cls.get_room(room_id)
        room.delete()