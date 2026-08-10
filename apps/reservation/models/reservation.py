from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.room.models import RoomType, Room
from apps.guest.models import Guest


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        CHECKED_IN = "checked_in", _("Checked in")
        CHECKED_OUT = "checked_out", _("Checked out")
        CANCELLED = "cancelled", _("Cancelled")

    guest = models.ForeignKey(Guest, on_delete=models.PROTECT, related_name="reservations")
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT)
    assigned_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reservations'

    def __str__(self):
        return self.guest.full_name
