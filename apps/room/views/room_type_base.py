from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets, permissions
from apps.room.models import RoomTypeBase
from apps.room.serializers.room_type_base import (
    RoomTypeBaseSerializer,
    RoomTypeBaseCreateUpdateSerializer, RoomTypeBaseListSerializer,
)

@extend_schema_view(
    list=extend_schema(responses={200: RoomTypeBaseListSerializer}, tags=['room base types']),
    retrieve=extend_schema(tags=['room base types']),
    create=extend_schema(
        request=RoomTypeBaseSerializer,
        responses={201: RoomTypeBaseCreateUpdateSerializer},
        tags=['room base types'],
    ),
    update=extend_schema(tags=['room base types']),
    partial_update=extend_schema(tags=['room base types']),
    destroy=extend_schema(tags=['room base types']),
)
class RoomTypeBaseViewSet(viewsets.ModelViewSet):
    """
    CRUD uchun ViewSet.
    - `objects` manager orqali faqat `deleted_at` bo'sh bo'lgan yozuvlar qaytariladi
      (RoomTypeBaseManager shunday filter qilingan deb faraz qilinmoqda).
    - DELETE so'rovi model darajasidagi soft delete (`delete()` override) orqali ishlaydi.
    """

    queryset = RoomTypeBase.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RoomTypeBaseCreateUpdateSerializer
        return RoomTypeBaseSerializer

    def perform_destroy(self, instance):
        # instance.delete() model ichida override qilingan — soft delete qiladi
        instance.delete()