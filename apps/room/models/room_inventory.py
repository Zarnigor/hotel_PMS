from django.db import models

class RoomInventory(models.Model):
    date = models.DateField()
    room_type = models.ForeignKey(
        'room.RoomType',
        on_delete=models.CASCADE,
        related_name="inventory_records",
    )
    total_rooms = models.PositiveIntegerField()
    booked_rooms = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Room Inventories"
        db_table = "room_inventories"
        constraints = [
            models.UniqueConstraint(
                fields=["date", "room_type"],
                name="unique_inventory_per_date_room_type",
            )
        ]

    def __str__(self):
        return f"{self.room_type} - {self.date}"