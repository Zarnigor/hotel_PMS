"""Reservation ro'yxati uchun django-filter FilterSet.

`ReservationViewSet` bu FilterSet'ni `DjangoFilterBackend` orqali
to'g'ridan-to'g'ri ORM queryset'ni filtrlash uchun ishlatadi (qarang:
`apps.reservation.views.reservations.ReservationViewSet`).
"""

import django_filters

from apps.reservation.models import Reservation


class ReservationFilter(django_filters.FilterSet):
    """Reservationlarni `status`, `room_type` va check-in sana oralig'i bo'yicha filtrlaydi."""

    check_in_date_after = django_filters.DateFilter(
        field_name="check_in_date", lookup_expr="gte"
    )
    check_in_date_before = django_filters.DateFilter(
        field_name="check_in_date", lookup_expr="lte"
    )

    class Meta:
        model = Reservation
        fields = ["status", "room_type"]
