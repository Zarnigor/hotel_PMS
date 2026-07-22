from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.room.models import Room, RoomType
from apps.room.serializers import RoomTypeShortSerializer


class RoomSerializer(serializers.ModelSerializer):
    """Room modelini o'qish (read) uchun serializer.

    `room_type` maydoni nested holda RoomTypeShortSerializer bilan
    ko'rsatiladi. Soft-delete maydoni faqat read-only.
    """

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
    """Room yaratish va yangilash (create/update) uchun serializer.

    `room_type` bu yerda PrimaryKeyRelatedField sifatida qabul
    qilinadi, soft-delete qilingan
    RoomType'larni tanlashning oldini olish uchun queryset
    manager orqali filterlanadi.
    """

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
    """Selectordan kelgan nested assigned_room dict yoki Room ORM obyekti uchun.

    Selector (raw SQL) `number` kalitli dict qaytaradi, ORM oqimlar
    (masalan reservation cancel/create) esa haqiqiy `Room` obyektini —
    u yerda maydon nomi `room_number`. Shu farqni hisobga olish uchun
    `number` maydoni ikkala manbadan ham o'qiy oladigan qilib yozilgan.
    """
    id = serializers.IntegerField()
    number = serializers.SerializerMethodField()

    def get_number(self, obj) -> str:
        if isinstance(obj, dict):
            return obj.get("number")
        return obj.room_number