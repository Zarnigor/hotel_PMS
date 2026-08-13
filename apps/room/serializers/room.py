from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.room.models import Room, RoomType
from apps.room.serializers import RoomTypeShortSerializer


class RoomSerializer(serializers.ModelSerializer):
    room_type = RoomTypeShortSerializer(read_only=True)
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = Room
        fields = [
            "id",
            "room_number",
            "room_type",
            "status",
            "status_display",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "deleted_at"
        ]


class RoomWriteSerializer(serializers.ModelSerializer):

    room_type = serializers.PrimaryKeyRelatedField(
        queryset=RoomType.objects.filter(deleted_at__isnull=True)
    )

    class Meta:
        model = Room
        fields = ["id", "room_number",  "room_type", "status"]
        read_only_fields = ["id"]

    def validate_room_number(self, value):
        """Room raqami bo'sh yoki faqat probeldan iborat bo'lmasligini tekshiradi."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Room number bo'sh bo'lishi mumkin emas.")
            )
        return value.strip()

    def validate(self, attrs):
        """
        Soft-delete qilingan xonalar hisobga olinmaydi — buni
        `RoomManager` (is_deleted=False) allaqachon ta'minlaydi.
        """
        room_number = attrs.get("room_number", getattr(self.instance, "room_number", None))

        qs = Room.objects.filter(room_number=room_number)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                {"room_number": _("Bu qavatda shu raqamli xona allaqachon mavjud.")}
            )
        return attrs


class AssignedRoomShortSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    number = serializers.SerializerMethodField()

    def get_number(self, obj) -> str:
        if isinstance(obj, dict):
            return obj.get("number")
        return obj.room_number