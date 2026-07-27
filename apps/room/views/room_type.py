from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _

from apps.room.models import RoomType
from apps.room.serializers import RoomTypeSerializer, RoomTypeWriteSerializer
from apps.room.utils.helpers import tagged_viewset_schema


@tagged_viewset_schema('Room Types', {'restore'})
class RoomTypeViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["room_type_base"]
    search_fields = ["name"]
    ordering_fields = ["id", "base_price", "created_at"]

    def get_queryset(self):
        """
        Soft deleted uchun filter qo'yilgan
        """
        return RoomType.objects.filter(deleted_at__isnull=True)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RoomTypeWriteSerializer
        return RoomTypeSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete: obyektni o'chirish o'rniga
        deleted_at=now()` qilib belgilaydi.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        """
        Soft-delete qilingan RoomType obyektini qayta tiklaydi
        (`deleted_at=None`).
        """
        instance = RoomType.all_objects.get(pk=pk)
        instance.deleted_at = None
        instance.save(update_fields=["deleted_at"])
        return Response(
            {"detail": _("Xona turi muvaffaqiyatli tiklandi.")},
            status=status.HTTP_200_OK,
        )