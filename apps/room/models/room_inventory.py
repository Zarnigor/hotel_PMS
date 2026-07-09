from django.db import models
from apps.room.models import RoomType

class RoomInventory(models.Model):
    date = models.DateField()
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name="inventory_records",
    )
    total_rooms = models.PositiveIntegerField()
    booked_rooms = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "room_inventory"
        constraints = [
            models.UniqueConstraint(
                fields=["date", "room_type"],
                name="unique_inventory_per_date_room_type",
            )
        ]

    def __str__(self):
        return f"{self.room_type} - {self.date}"