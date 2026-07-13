class RoomQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class RoomManager(models.Manager):
    def get_queryset(self):
        return RoomQuerySet(self.model, using=self._db).alive()