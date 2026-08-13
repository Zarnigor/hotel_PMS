import logging
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.room.models import RoomType, RoomTypeBase
from apps.room.services.room_inventory import RoomInventoryService
from apps.room.utils import RoomUtil
from exceptions import RoomInvalidError

logger = logging.getLogger(__name__)

INVENTORY_HORIZON_DAYS = 365


class RoomTypeService:
    @staticmethod
    def create_base(name: str, description: str = "") -> RoomTypeBase:
        if not name:
            logger.warning("create_base rejected reason=empty_name")
            raise RoomInvalidError(_("name bo'sh bo'lishi mumkin emas."))
        return RoomTypeBase.objects.create(name=name, description=description)

    @classmethod
    @transaction.atomic
    def update_base(cls, room_type_base_id: int, **fields) -> RoomTypeBase:
        base = RoomUtil.get_room_type_base(room_type_base_id)
        allowed = {"name", "description"}
        for key, value in fields.items():
            if key in allowed:
                setattr(base, key, value)
        base.save(update_fields=[k for k in fields if k in allowed])
        return base

    @classmethod
    @transaction.atomic
    def delete_base(cls, room_type_base_id: int) -> None:
        base = RoomUtil.get_room_type_base(room_type_base_id)
        base.delete()
        logger.info("delete_base success room_type_base_id=%s", room_type_base_id)

    @staticmethod
    @transaction.atomic
    def create_room_type(
        room_type_base_id: int,
        name: str,
        base_price: Decimal,
        max_occupancy: int = 2,
    ) -> RoomType:
        if not name:
            logger.warning("create_room_type rejected reason=empty_name room_type_base_id=%s", room_type_base_id)
            raise RoomInvalidError(_("name bo'sh bo'lishi mumkin emas."))
        if base_price is None or base_price < 0:
            logger.warning(
                "create_room_type rejected reason=negative_base_price room_type_base_id=%s base_price=%s",
                room_type_base_id, base_price,
            )
            raise RoomInvalidError(_("base_price manfiy bo'lishi mumkin emas."))
        if max_occupancy is None or max_occupancy <= 0:
            logger.warning(
                "create_room_type rejected reason=invalid_max_occupancy room_type_base_id=%s max_occupancy=%s",
                room_type_base_id, max_occupancy,
            )
            raise RoomInvalidError(_("max_occupancy 0 dan katta bo'lishi kerak."))

        RoomUtil.get_room_type_base(room_type_base_id)
        room_type = RoomType.objects.create(
            room_type_base_id=room_type_base_id,
            name=name,
            base_price=base_price,
            max_occupancy=max_occupancy,
        )

        today = date.today()
        RoomInventoryService.generate_for_date_range(
            room_type_id=room_type.id,
            start_date=today,
            end_date=today + timedelta(days=INVENTORY_HORIZON_DAYS),
            total_rooms=0,
        )
        logger.info(
            "create_room_type success room_type_id=%s room_type_base_id=%s base_price=%s",
            room_type.id, room_type_base_id, base_price,
        )
        return room_type

    @classmethod
    @transaction.atomic
    def update_price(cls, room_type_id: int, base_price: Decimal) -> RoomType:
        """Update a room type object. Get the type from base class"""
        if base_price is None or base_price < 0:
            logger.warning(
                "update_price rejected reason=negative_base_price room_type_id=%s base_price=%s",
                room_type_id, base_price,
            )
            raise RoomInvalidError(_("base_price manfiy bo'lishi mumkin emas."))
        room_type = RoomUtil.get_room_type(room_type_id)
        room_type.base_price = base_price
        room_type.save(update_fields=["base_price"])
        logger.info("update_price success room_type_id=%s base_price=%s", room_type_id, base_price)
        return room_type

    @classmethod
    @transaction.atomic
    def update_room_type(cls, room_type_id: int, **fields) -> RoomType:
        room_type = RoomUtil.get_room_type(room_type_id)
        allowed = {"name", "base_price", "room_type_base_id", "max_occupancy"}
        if "base_price" in fields and fields["base_price"] is not None and fields["base_price"] < 0:
            logger.warning(
                "update_room_type rejected reason=negative_base_price room_type_id=%s base_price=%s",
                room_type_id, fields["base_price"],
            )
            raise RoomInvalidError(_("base_price manfiy bo'lishi mumkin emas."))
        if "max_occupancy" in fields and fields["max_occupancy"] is not None and fields["max_occupancy"] <= 0:
            logger.warning(
                "update_room_type rejected reason=invalid_max_occupancy room_type_id=%s max_occupancy=%s",
                room_type_id, fields["max_occupancy"],
            )
            raise RoomInvalidError(_("max_occupancy 0 dan katta bo'lishi kerak."))
        for key, value in fields.items():
            if key in allowed:
                setattr(room_type, key, value)
        room_type.save(update_fields=[k for k in fields if k in allowed])
        return room_type

    @classmethod
    @transaction.atomic
    def delete_room_type(cls, room_type_id: int) -> None:
        """Delete a room type object by room_type_id.
        By soft deletes the room type.
        """
        room_type = RoomUtil.get_room_type(room_type_id)
        room_type.delete() # TO DO soft delete kerak
        logger.info("delete_room_type success room_type_id=%s", room_type_id)