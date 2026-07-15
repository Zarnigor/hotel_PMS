from django.db import models

class RoomQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at=None)

    def dead(self):
        return self.filter(deleted_at=None)


class RoomManager(models.Manager):
    def get_queryset(self):
        return RoomQuerySet(self.model, using=self._db).alive()


class RoomTypeBaseQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at=None)

    def dead(self):
        return self.filter(deleted_at=None)


class RoomTypeBaseManager(models.Manager):
    def get_queryset(self):
        return RoomTypeBaseQuerySet(self.model, using=self._db).alive()


class RoomTypeQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at=None)

    def dead(self):
        return self.filter(deleted_at=None)


class RoomTypeManager(models.Manager):
    def get_queryset(self):
        return RoomTypeQuerySet(self.model, using=self._db).alive()
