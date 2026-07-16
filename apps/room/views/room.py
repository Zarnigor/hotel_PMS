from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from apps.room.models import Room
from apps.room.serializers import RoomSerializer, RoomWriteSerializer
from apps.room.utils.helpers import tagged_viewset_schema


@tagged_viewset_schema('Room',{'restore'})
class RoomViewSet(viewsets.ModelViewSet):
    """
    Room uchun CRUD operatsiyalarini boshqaruvchi ViewSet.
    Soft-delete qo'llab-quvvatlanadi.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["room_type"]
    search_fields = ["room_number"]
    ordering_fields = ["room_number"]

    def get_queryset(self):
        return Room.objects.filter(deleted_at__isnull=True).select_related("room_type")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RoomWriteSerializer
        return RoomSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        instance = Room.all_objects.get(pk=pk)
        instance.deleted_at = None
        instance.save(update_fields=["deleted_at"])
        return Response({"detail": _("Xona muvaffaqiyatli tiklandi.")}, status=status.HTTP_200_OK)