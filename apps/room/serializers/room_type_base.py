from rest_framework import serializers
from apps.room.models import RoomTypeBase


class RoomTypeBaseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomTypeBase
        fields = ["id", "name"]


class RoomTypeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomTypeBase
        fields = [
            "id",
            "name",
            "description",
            "deleted_at",
        ]
        read_only_fields = ["id", "deleted_at"]


class RoomTypeBaseCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = RoomTypeBase
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]