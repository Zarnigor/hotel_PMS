from django.db import models

from apps.room.models import RoomType, Room


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CHECKED_IN = "checked_in", "Checked in"
        CHECKED_OUT = "checked_out", "Checked out"
        CANCELLED = "cancelled", "Cancelled"


    guess_name = models.CharField(max_length=10, unique=True)
    room_type_id = models.ForeignKey(RoomType, on_delete=models.PROTECT)
    assigned_room_id = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reservation'

    def __str__(self):
        return self.guess_name
