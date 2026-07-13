from django.utils import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.room.models import RoomType
from apps.room.models.managers import RoomManager


class Room(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", _("Available")
        OCCUPIED = "occupied", _("Occupied")
        MAINTENANCE = "maintenance", _("Maintenance")
        CLEANING = "cleaning", _("Cleaning")
        OUT_OF_SERVICE = "out_of_service", _("OUT_OF_SERVICE")

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    objects = RoomManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "rooms"
        constraints = [
            models.UniqueConstraint(
                fields=["room_number"],
                condition=models.Q(is_deleted=False),
                name="unique_active_room_number",
            )
        ]

    def __str__(self):
        return self.room_number

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
