from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from apps.guest.models import Guest
from apps.guest.serializers import GuestSerializer, GuestWriteSerializer
from apps.room.utils.helpers import tagged_viewset_schema


@tagged_viewset_schema('Guest')
class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["country"]
    search_fields = ["full_name", "passport"]
    ordering_fields = ["id", "full_name", "created_at"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return GuestWriteSerializer
        return GuestSerializer
