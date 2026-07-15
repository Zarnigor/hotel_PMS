from django.db import models

class RoomQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class RoomManager(models.Manager):
    def get_queryset(self):
        return RoomQuerySet(self.model, using=self._db).alive()


class RoomTypeBaseQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class RoomTypeBaseManager(models.Manager):
    def get_queryset(self):
        return RoomTypeBaseQuerySet(self.model, using=self._db).alive()


class RoomTypeQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class RoomTypeManager(models.Manager):
    def get_queryset(self):
        return RoomTypeQuerySet(self.model, using=self._db).alive()
