from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.room.models import RoomType, RoomTypeBase


class RoomTypeBaseSerializer(serializers.ModelSerializer):
    """Serializer for the RoomTypeBase model.

    Soft-deleted records are
    excluded via the default manager at the view/queryset level.
    """

    class Meta:
        model = RoomTypeBase
        fields = [
            "id",
            "name",
            "description"
        ]


class RoomTypeSerializer(serializers.ModelSerializer):
    """Serializer for the RoomType model.

    Includes a nested read-only representation of the related RoomTypeBase.
    """

    base = RoomTypeBaseSerializer(read_only=True)
    base = serializers.PrimaryKeyRelatedField(
        queryset=RoomTypeBase.objects.filter(is_deleted=False),
        source="base",
        write_only=True,
    )

    class Meta:
        model = RoomType
        fields = [
            "id",
            "base",
            "base_id",
            "name",
            "price",
            "is_deleted",
            "deleted_at"
        ]
        read_only_fields = ["id", "is_deleted", "deleted_at"]

    def validate_price_override(self, value):
        """Allow null (inherit base price) but disallow negative values."""
        if value is not None and value < 0:
            raise serializers.ValidationError(
                _("Price override cannot be negative.")
            )
        return value


class RoomTypeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for RoomType list endpoints.

    Excludes heavy/nested fields to keep list responses fast.
    """

    class Meta:
        model = RoomType
        fields = ["id", "name", "price"]