from django.db import models

class Guest(models.Model):
    full_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True, default="")
    birthday = models.DateField(null=True, blank=True)
    passport = models.CharField(max_length=20, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "guests"
        constraints = [
            models.UniqueConstraint(
                fields=["passport"],
                condition=~models.Q(passport=""),
                name="unique_guest_passport_when_present",
            )
        ]

    def __str__(self):
        return self.full_name
