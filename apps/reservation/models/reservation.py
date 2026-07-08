from django.db import models

from apps.room.models import Room


class Reservation(models.Model):
    class Status(models.TextChoices):
        BOOKED = 'booked', 'BOOKED'
        CHECKEDIN = 'checked in', 'CHECKED IN'
        CHECKEDOUT = 'checked out', 'CHECKED OUT'
        CANCELED = 'canceled', 'CANCELED'


    guess_name = models.CharField(max_length=200)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in_date = models.DateTimeField(auto_now_add=True)
    check_out_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices)


