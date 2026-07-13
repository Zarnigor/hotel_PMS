from apps.room.models import RoomType
from django.db.models import QuerySet

from apps.room.models import Room, RoomTypeBase
from apps.room.services import RoomStatus
from exceptions import RoomNotFoundError, RoomUnbookableError, OverbookingError

from django.utils.translation import gettext_lazy as _

class RoomUtil:
    @staticmethod
    def get_room_type_base(room_type_base_id: int) -> RoomTypeBase:
        """

        """
        try:
            return RoomTypeBase.objects.get(id=room_type_base_id)
        except RoomTypeBase.DoesNotExist:
            raise RoomNotFoundError(
                _("RoomTypeBase (id=%(id)s) topilmadi.") % {"id": room_type_base_id}
            )

    @staticmethod
    def list_room_type_bases() -> QuerySet[RoomTypeBase]:
        """Gets all room type bases"""
        return RoomTypeBase.objects.all().order_by("name")

    @staticmethod
    def list_room_types(room_type_base_id: int | None = None) -> QuerySet[RoomType]:
        """Gets all rooms list by room_type_base_id"""
        qs = RoomType.objects.select_related("room_type_base").all()
        if room_type_base_id is not None:
            qs = qs.filter(room_type_base_id=room_type_base_id)
        return qs.order_by("name")

    @staticmethod
    def list_rooms(room_type_id: int | None = None, status: str | None = None) -> QuerySet[Room]:
        """Gets all rooms list by room_type_id and status"""
        qs = Room.objects.select_related("room_type").all()
        if room_type_id is not None:
            qs = qs.filter(room_type=room_type_id)
        if status is not None:
            qs = qs.filter(status=status)
        return qs.order_by("room_number")

    @staticmethod
    def get_room_type(room_type_id: int) -> RoomType:
        """Gets room type by room_type_id"""
        try:
            return RoomType.objects.select_related("room_type_base").get(id=room_type_id)
        except RoomType.DoesNotExist:
            raise RoomNotFoundError(_("RoomType (id=%(id)s) topilmadi.") % {"id": room_type_id})

    @staticmethod
    def get_room(room_id: int) -> Room:
        """Gets room by room_id. Exception: RoomNotFoundError"""
        try:
            return Room.objects.select_related("room_type").get(id=room_id)
        except Room.DoesNotExist:
            raise RoomNotFoundError(_("Xona (id=%(id)s) topilmadi.")%{"id":room_id})

    @classmethod
    def find_available_room(cls, room_type_id: int) -> Room:
        """Gets available room by room_type_id. Exception: RoomNotFoundError"""
        room = (
            Room.objects.select_related("room_type")
            .filter(room_type_id=room_type_id, status=RoomStatus.AVAILABLE)
            .first()
        )
        if room is None:
            raise OverbookingError(
                _("(id=%(id)s) uchun hozir bo'sh xona yo'q.")%{"id": room_type_id}
            )
        return room

    @classmethod
    def get_bookable_room(cls, room_id: int) -> Room:
        """Gets bookable room by room_id. Exception: RoomNotFoundError"""
        room = cls.get_room(room_id)
        cls.ensure_bookable(room)
        return room

    @classmethod
    def ensure_bookable(cls, room: Room) -> None:
        """Checks if room is bookable"""
        if room.status in RoomStatus.UNBOOKABLE:
            raise RoomUnbookableError(
                _("Xona '(number=%(number)s)' hozir '(status=%(status)s)' holatida — band qilib bo'lmaydi.") % {"number": room.room_number, "status": room.status}
            )

