"""Reservation views — GET action'lar selectordan, write action'lar
serializer orqali service'ga yo'naltiriladi. Custom exceptionlar (masalan
`OverbookingError`, `ReservationNotFoundError`) global exception handler
orqali tegishli HTTP status'ga map qilinadi, shuning uchun view'larda
try/except yozilmaydi."""
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.reservation.serializers import (
    ReservationListSerializer,
    ReservationDetailSerializer,
    ReservationWriteSerializer,
    ReservationCancelSerializer,
)
from apps.reservation.utils import get_reservation, list_reservations


@extend_schema_view(
    create=extend_schema( request=ReservationWriteSerializer,
                          responses={201: ReservationDetailSerializer}
                        ),
    list=extend_schema(responses={200: ReservationListSerializer}),
)
class ReservationViewSet(viewsets.ViewSet):
    """Reservation'lar uchun CRUD + cancel action.

    GET (list/retrieve) — selector orqali, raw SQL.
    POST (create) va cancel — serializer orqali, service (ORM) chaqiriladi.
    """
    @extend_schema(tags=['reservation'])
    def list(self, request):
        """Reservationlar ro'yxati, filtr va pagination bilan."""
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))

        data = list_reservations(
            room_type_id=request.query_params.get('room_type_id'),
            status=request.query_params.get('status'),
            limit=limit,
            offset=offset,
        )
        serializer = ReservationListSerializer(data['results'], many=True)
        return Response({**data, 'results': serializer.data})

    @extend_schema(tags=['reservation'])
    def retrieve(self, request, pk=None):
        """Bitta reservation, nested room_type/assigned_room bilan."""
        reservation = get_reservation(pk)
        serializer = ReservationDetailSerializer(reservation)
        return Response(serializer.data)

    @extend_schema(tags=['reservation'])
    def create(self, request):
        """Yangi reservation yaratish — inventory lock va overbooking
        tekshiruvi `services.create_reservation` ichida bajariladi."""
        serializer = ReservationWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=['reservation'])
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Reservationni bekor qilish — inventory bo'shatiladi."""
        serializer = ReservationCancelSerializer(
            data={}, context={'reservation_id': pk}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)