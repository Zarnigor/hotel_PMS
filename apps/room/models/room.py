from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.room.models import RoomType


class Room(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", _("Available")
        OCCUPIED = "occupied", _("Occupied")
        MAINTENANCE = "maintenance", _("Maintenance")
        CLEANING = "cleaning", _("Cleaning")

    ALLOWED_TRANSITIONS = {
        Status.AVAILABLE: {Status.OCCUPIED, Status.MAINTENANCE},
        Status.OCCUPIED: {Status.CLEANING},
        Status.CLEANING: {Status.AVAILABLE, Status.MAINTENANCE},
        Status.MAINTENANCE: {Status.AVAILABLE},
    }

    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    class Meta:
        db_table = "rooms"

    def __str__(self):
        return self.room_number

