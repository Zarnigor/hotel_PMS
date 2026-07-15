from rest_framework import serializers


class RoomTypeShortSerializer(serializers.Serializer):
    """Selectordan kelgan nested room_type dict uchun (swagger uchun ham kerak)."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2)