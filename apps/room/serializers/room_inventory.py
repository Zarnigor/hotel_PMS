from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.room.models import RoomType, RoomInventory

class RoomInventoryListSerializer(serializers.ModelSerializer):
    """Ro'yxat (swagger/list) uchun yengil serializer."""

    room_type_name = serializers.CharField(source="room_type.name", read_only=True)
    available_rooms = serializers.SerializerMethodField()

    class Meta:
        model = RoomInventory
        fields = (
            "id",
            "date",
            "room_type",
            "room_type_name",
            "total_rooms",
            "booked_rooms",
            "available_rooms",
        )

    def get_available_rooms(self, obj) -> int:
        return obj.total_rooms - obj.booked_rooms


class RoomInventoryDetailSerializer(serializers.ModelSerializer):
    """Bitta obyekt uchun to'liq detal serializer."""

    room_type_name = serializers.CharField(source="room_type.name", read_only=True)
    available_rooms = serializers.SerializerMethodField()
    occupancy_rate = serializers.SerializerMethodField()

    class Meta:
        model = RoomInventory
        fields = (
            "id",
            "date",
            "room_type",
            "room_type_name",
            "total_rooms",
            "booked_rooms",
            "available_rooms",
            "occupancy_rate",
        )

    def get_available_rooms(self, obj) -> int:
        return obj.total_rooms - obj.booked_rooms

    def get_occupancy_rate(self, obj) -> float:
        if obj.total_rooms == 0:
            return 0.0
        return round((obj.booked_rooms / obj.total_rooms) * 100, 2)


class RoomInventoryWriteSerializer(serializers.ModelSerializer):
    """
    Create/update uchun serializer. Validatsiyadan tashqari barcha
    biznes-logika `RoomInventoryService` ga delegatsiya qilinadi.
    """

    class Meta:
        model = RoomInventory
        fields = (
            "id",
            "date",
            "room_type",
            "total_rooms",
            "booked_rooms",
        )
        read_only_fields = ("id",)

    def validate_room_type(self, value: RoomType) -> RoomType:
        if getattr(value, "is_deleted", False):
            raise serializers.ValidationError(
                _("Bu xona turi o'chirilgan, inventarizatsiya qo'shib bo'lmaydi.")
            )
        return value

    def validate(self, attrs: dict) -> dict:
        total_rooms = attrs.get(
            "total_rooms",
            getattr(self.instance, "total_rooms", None),
        )
        booked_rooms = attrs.get(
            "booked_rooms",
            getattr(self.instance, "booked_rooms", 0),
        )
        if total_rooms is not None and booked_rooms > total_rooms:
            raise serializers.ValidationError(
                {
                    "booked_rooms": _(
                        "Band qilingan xonalar soni umumiy xonalar sonidan oshib ketdi."
                    )
                }
            )
        return attrs

    def create(self, validated_data: dict) -> RoomInventory:
        from apps.room.services import RoomInventoryService

        return RoomInventoryService.create_inventory(**validated_data)

    def update(self, instance: RoomInventory, validated_data: dict) -> RoomInventory:
        from apps.room.services import RoomInventoryService

        return RoomInventoryService.update_inventory(
            instance=instance, **validated_data
        )


class RoomInventoryBulkCreateSerializer(serializers.Serializer):
    """Sana oralig'i uchun ommaviy (bulk) inventarizatsiya yaratish."""

    room_type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all())
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_rooms = serializers.IntegerField(min_value=1)

    def validate(self, attrs: dict) -> dict:
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError(
                _("Tugash sanasi boshlanish sanasidan oldin bo'lishi mumkin emas.")
            )
        return attrs