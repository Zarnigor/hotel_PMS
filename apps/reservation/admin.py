from django.contrib import admin
from apps.reservation.models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "guess_name",
        "room_type_id",
        "assigned_room_id",
        "check_in_date",
        "check_out_date",
        "status",
        "created_at",
    )
    list_filter = ("status", "room_type_id", "check_in_date", "check_out_date")
    search_fields = ("guess_name",)
    autocomplete_fields = ("room_type_id", "assigned_room_id")
    date_hierarchy = "check_in_date"
    ordering = ("-created_at",)