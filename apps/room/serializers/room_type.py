"""RoomType uchun DRF serializerlari."""

from rest_framework import serializers

from apps.room.models import RoomType
from django.utils.translation import gettext_lazy as _

class RoomTypeSerializer(serializers.ModelSerializer):
    """RoomType modelini to'liq ko'rsatish uchun serializer.

    List/detail response'larida ishlatiladi.
    """

    class Meta:
        model = RoomType
        fields = [
            "id",
            "name",
            "base_price",
        ]
        read_only_fields = ["id"]


class RoomTypeShortSerializer(serializers.ModelSerializer):
    """RoomType uchun qisqartirilgan (nested) serializer.

    Room serializerlari ichida to'liq RoomTypeSerializer o'rniga
    ishlatiladi — ortiqcha ma'lumot yubormaslik uchun.
    """

    class Meta:
        model = RoomType
        fields = ["id", "name", "base_price"]
        read_only_fields = fields


class RoomTypeWriteSerializer(serializers.ModelSerializer):
    """RoomType yaratish va yangilash (create/update) uchun serializer.

    `create`, `update`, `partial_update` action'larida ishlatiladi.
    """

    class Meta:
        model = RoomType
        fields = [
            "name",
            "base_price",
        ]

    def validate_base_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                _("Narx 0 dan katta bo'lishi kerak.")
            )
        return value
