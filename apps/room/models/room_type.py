from django.db import models
from apps.room.models.managers import RoomTypeManager
from django.utils import timezone

class RoomType(models.Model):
    room_type_base = models.ForeignKey(
        'room.RoomTypeBase',
        on_delete=models.PROTECT,
        related_name="room_types",
    )
    name = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = RoomTypeManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "room_types"

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)


