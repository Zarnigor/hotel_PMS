from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.room.models import Room


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for the Room model.

    Soft-delete records are
    """