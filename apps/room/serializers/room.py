from rest_framework import serializers


class AssignedRoomShortSerializer(serializers.Serializer):
    """Selectordan kelgan nested assigned_room dict uchun."""
    id = serializers.IntegerField()
    number = serializers.CharField()