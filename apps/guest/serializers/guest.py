from rest_framework import serializers

from apps.guest.models import Guest
from apps.guest.services import GuestService


class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = ["id", "full_name", "country", "birthday", "passport", "created_at"]
        read_only_fields = ["id", "created_at"]


class GuestShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = ["id", "full_name"]
        read_only_fields = fields


class GuestWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = ["id", "full_name", "country", "birthday", "passport"]
        read_only_fields = ["id"]

    def create(self, validated_data: dict) -> Guest:
        return GuestService.create_guest(
            full_name=validated_data["full_name"],
            country=validated_data.get("country", ""),
            birthday=validated_data.get("birthday"),
            passport=validated_data.get("passport", ""),
        )

    def update(self, instance: Guest, validated_data: dict) -> Guest:
        return GuestService.update_guest(instance.id, **validated_data)
