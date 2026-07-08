from django.db import models

class RoomType(models.Model):
    class Types(models.TextChoices):
        DELUXEKING = 'deluxe king', 'DELUXE KING'
        STANDARDTWIN = 'standard twin', 'STANDARD TWIN'

    room_type = models.CharField(max_length=20, choices=Types.choices, default=Types.STANDARDTWIN)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)


class Room(models.Model):
    class Status(models.TextChoices):
        VACANT = 'vacant', 'VACANT'
        OCCUPIED = 'occupied', 'OCCUPIED'
        DIRTY = 'dirty', 'dirty'

    type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    number = models.IntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.VACANT)



