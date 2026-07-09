from django.db import models
from apps.room.models import RoomTypeBase


class RoomType(models.Model):
    room_type_base = models.ForeignKey(
        RoomTypeBase,
        on_delete=models.PROTECT,
        related_name="room_types",
    )
    name = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "room_type"

    def __str__(self):
        return self.name

