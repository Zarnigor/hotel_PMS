# from decimal import Decimal
#
# from django.db import transaction
# from django.db.models import QuerySet
#
# from apps.room.models import Room, RoomTypeBase
# from apps.room.services.room_type_service import RoomTypeService
# from exceptions import RoomInvalidError
#
# from django.utils.translation import gettext_lazy as _
#
# class RoomStatus:
#     AVAILABLE = _("AVAILABLE")
#     OCCUPIED = _("OCCUPIED")
#     CLEANING = _("CLEANING")
#     MAINTENANCE = _("MAINTENANCE")
#     OUT_OF_SERVICE = _("OUT_OF_SERVICE")
#
#     CHOICES = (AVAILABLE, OCCUPIED, CLEANING, MAINTENANCE, OUT_OF_SERVICE)
#
#
#     UNBOOKABLE = {CLEANING, MAINTENANCE, OUT_OF_SERVICE}
#
#
#     ALLOWED_TRANSITIONS = {
#         AVAILABLE: {OCCUPIED, MAINTENANCE, OUT_OF_SERVICE},
#         OCCUPIED: {CLEANING, MAINTENANCE},
#         CLEANING: {AVAILABLE, MAINTENANCE},
#         MAINTENANCE: {AVAILABLE, OUT_OF_SERVICE},
#         OUT_OF_SERVICE: {MAINTENANCE, AVAILABLE},
#     }
#
#
# class RoomService:
#     @staticmethod
#     def create_room(room_number: str, room_type: int, status: str = RoomStatus.AVAILABLE) -> Room:
#         if not room_number:
#             raise RoomInvalidError("Xona raqami bo'sh bo'lishi munkin emas")
#         if not status in RoomStatus.CHOICES:
#             raise RoomInvalidError("Xona statusi xato")
#         RoomTypeService.get_room_type(room_type)
#
#         return Room.objects.create(room_number=room_number,room_status=status,room_type=room_type)
#
#