from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.reservation.filters import ReservationFilter
from apps.reservation.models import Reservation
from apps.reservation.serializers import (
    ReservationListSerializer,
    ReservationDetailSerializer,
    ReservationWriteSerializer,
    ReservationCancelSerializer,
)
from apps.room.utils.helpers import tagged_viewset_schema


@tagged_viewset_schema('Reservation', {'cancel'})
class ReservationViewSet(viewsets.ModelViewSet):
    """Reservation'lar uchun list/retrieve/create + cancel action."""

    queryset = Reservation.objects.select_related('room_type', 'assigned_room').all()
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filterset_class = ReservationFilter
    ordering_fields = ['id', 'check_in_date', 'check_out_date', 'created_at']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_serializer_class(self):
        if self.action == "create":
            return ReservationWriteSerializer
        if self.action == "list":
            return ReservationListSerializer
        return ReservationDetailSerializer

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Reservationni bekor qilish — inventory bo'shatiladi."""
        serializer = ReservationCancelSerializer(
            data={}, context={'reservation_id': pk}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
