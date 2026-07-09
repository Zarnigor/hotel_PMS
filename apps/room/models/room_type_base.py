from django.db import models


class RoomTypeBase(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "room_type_bases"

    def __str__(self):
        return self.name