from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from apps.room.filters import RoomInventoryFilter
from apps.room.models import RoomInventory
from apps.room.serializers import (
    RoomInventoryBulkCreateSerializer,
    RoomInventoryDetailSerializer,
    RoomInventoryListSerializer,
    RoomInventoryWriteSerializer,
)
from apps.room.services import RoomInventoryService
from apps.room.utils.helpers import tagged_viewset_schema


@tagged_viewset_schema('Room Inventory', {'bulk_create'})
class RoomInventoryViewSet(ModelViewSet):
    """RoomInventory uchun CRUD va qo'shimcha (bulk-create) endpointlar."""

    queryset = RoomInventory.objects.select_related("room_type").all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RoomInventoryFilter
    ordering_fields = ["id", "date", "total_rooms", "booked_rooms"]
    ordering = ["date"]

    def get_serializer_class(self):
        if self.action == "list":
            return RoomInventoryListSerializer
        if self.action in ("create", "update", "partial_update"):
            return RoomInventoryWriteSerializer
        if self.action == "bulk_create":
            return RoomInventoryBulkCreateSerializer
        return RoomInventoryDetailSerializer

    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        instance = write_serializer.save()
        detail_serializer = RoomInventoryDetailSerializer(instance)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        write_serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        write_serializer.is_valid(raise_exception=True)
        updated_instance = write_serializer.save()
        detail_serializer = RoomInventoryDetailSerializer(updated_instance)
        return Response(detail_serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create(self, request):
        """Sana oralig'i uchun ommaviy inventarizatsiya yaratish."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_records = RoomInventoryService.bulk_create_inventory(
            room_type=serializer.validated_data["room_type"],
            start_date=serializer.validated_data["start_date"],
            end_date=serializer.validated_data["end_date"],
            total_rooms=serializer.validated_data["total_rooms"],
        )
        response_serializer = RoomInventoryListSerializer(created_records, many=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)