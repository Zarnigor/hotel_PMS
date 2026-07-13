from django.db import models

from apps.room.models.managers import RoomTypeBaseManager


class RoomTypeBase(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = RoomTypeBaseManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "room_type_bases"

    def __str__(self):
        return self.name