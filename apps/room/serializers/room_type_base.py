# room_types/serializers/room_type_base.py
from rest_framework import serializers
from apps.room.models import RoomTypeBase


class RoomTypeBaseListSerializer(serializers.ModelSerializer):
    """Lightweight — list endpoint uchun (Swagger: GET /room-type-bases/)."""

    class Meta:
        model = RoomTypeBase
        fields = ["id", "name", "price"]


class RoomTypeBaseDetailSerializer(serializers.ModelSerializer):
    """To'liq representation — single object uchun (Swagger: GET /room-type-bases/{id}/)."""

    class Meta:
        model = RoomTypeBase
        fields = ["id", "name", "price", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoomTypeBaseWriteSerializer(serializers.ModelSerializer):
    """Create/update uchun (Swagger: POST/PATCH /room-type-bases/).

    Faqat shape/field validatsiya. Biznes logika RoomTypeBaseService'ga tegishli.
    """

    class Meta:
        model = RoomTypeBase
        fields = ["id", "name", "price", "description"]
        read_only_fields = ["id"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Narx musbat bo'lishi kerak.")
        return value