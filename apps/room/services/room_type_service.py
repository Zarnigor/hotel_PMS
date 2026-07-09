from decimal import Decimal

from django.db import transaction
from django.db.models import QuerySet

from apps.room.models import RoomType, RoomTypeBase
from exceptions import RoomNotFoundError, RoomInvalidError


class RoomTypeService:
    @staticmethod
    def create_base(name: str, description: str = "") -> RoomTypeBase:
        if not name:
            raise RoomInvalidError("name bo'sh bo'lishi mumkin emas.")
        return RoomTypeBase.objects.create(name=name, description=description)

    @staticmethod
    def get_base(room_type_base_id: int) -> RoomTypeBase:
        try:
            return RoomTypeBase.objects.get(id=room_type_base_id)
        except RoomTypeBase.DoesNotExist:
            raise RoomNotFoundError(
                f"RoomTypeBase (id={room_type_base_id}) topilmadi."
            )

    @staticmethod
    def list_bases() -> QuerySet[RoomTypeBase]:
        return RoomTypeBase.objects.all().order_by("name")

    @classmethod
    @transaction.atomic
    def update_base(cls, room_type_base_id: int, **fields) -> RoomTypeBase:
        base = cls.get_base(room_type_base_id)
        allowed = {"name", "description"}
        for key, value in fields.items():
            if key in allowed:
                setattr(base, key, value)
        base.save(update_fields=[k for k in fields if k in allowed])
        return base

    @classmethod
    @transaction.atomic
    def delete_base(cls, room_type_base_id: int) -> None:
        base = cls.get_base(room_type_base_id)
        base.delete()


    @staticmethod
    @transaction.atomic
    def create_room_type(
        room_type_base_id: int,
        name: str,
        base_price: Decimal,
    ) -> RoomType:
        if not name:
            raise RoomInvalidError("name bo'sh bo'lishi mumkin emas.")
        if base_price is None or base_price < 0:
            raise RoomInvalidError("base_price manfiy bo'lishi mumkin emas.")

        RoomTypeService.get_base(room_type_base_id)
        return RoomType.objects.create(
            room_type_base_id=room_type_base_id,
            name=name,
            base_price=base_price,
        )

    @staticmethod
    def get_room_type(room_type_id: int) -> RoomType:
        try:
            return RoomType.objects.select_related("room_type_base").get(id=room_type_id)
        except RoomType.DoesNotExist:
            raise RoomNotFoundError(f"RoomType (id={room_type_id}) topilmadi.")

    @staticmethod
    def list_room_types(room_type_base_id: int | None = None) -> QuerySet[RoomType]:
        qs = RoomType.objects.select_related("room_type_base").all()
        if room_type_base_id is not None:
            qs = qs.filter(room_type_base_id=room_type_base_id)
        return qs.order_by("name")

    @classmethod
    @transaction.atomic
    def update_price(cls, room_type_id: int, base_price: Decimal) -> RoomType:
        if base_price is None or base_price < 0:
            raise RoomInvalidError("base_price manfiy bo'lishi mumkin emas.")
        room_type = cls.get_room_type(room_type_id)
        room_type.base_price = base_price
        room_type.save(update_fields=["base_price"])
        return room_type

    @classmethod
    @transaction.atomic
    def update_room_type(cls, room_type_id: int, **fields) -> RoomType:
        room_type = cls.get_room_type(room_type_id)
        allowed = {"name", "base_price", "room_type_base_id"}
        if "base_price" in fields and fields["base_price"] is not None and fields["base_price"] < 0:
            raise RoomInvalidError("base_price manfiy bo'lishi mumkin emas.")
        for key, value in fields.items():
            if key in allowed:
                setattr(room_type, key, value)
        room_type.save(update_fields=[k for k in fields if k in allowed])
        return room_type

    @classmethod
    @transaction.atomic
    def delete_room_type(cls, room_type_id: int) -> None:
        room_type = cls.get_room_type(room_type_id)
        room_type.delete()