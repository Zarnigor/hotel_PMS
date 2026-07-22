"""Room ilovasi uchun django-filter FilterSet'lari."""

import django_filters

from apps.room.models import RoomInventory


class RoomInventoryFilter(django_filters.FilterSet):
    """RoomInventory ro'yxatini `room_type` va sana oralig'i bo'yicha filtrlaydi."""

    date_after = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = RoomInventory
        fields = ["room_type"]
