from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets, permissions, filters
from apps.room.models import RoomTypeBase
from apps.room.serializers.room_type_base import (
    RoomTypeBaseSerializer,
    RoomTypeBaseCreateUpdateSerializer, RoomTypeBaseListSerializer,
)
from apps.room.utils.helpers import tagged_viewset_schema


@tagged_viewset_schema('Room Type bases')
class RoomTypeBaseViewSet(viewsets.ModelViewSet):
    queryset = RoomTypeBase.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["id", "name", "created_at"]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return RoomTypeBaseCreateUpdateSerializer
        return RoomTypeBaseSerializer

    def perform_destroy(self, instance):
        # instance.delete() model ichida override qilingan — soft delete qiladi
        instance.delete()