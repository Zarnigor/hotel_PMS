from django.contrib import admin
from apps.reservation.models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "guest",
        "room_type",
        "assigned_room",
        "check_in_date",
        "check_out_date",
        "status",
        "created_at",
    )
    list_filter = ("status", "room_type", "check_in_date", "check_out_date")
    search_fields = ("guest__full_name", "guest__passport")
    autocomplete_fields = ("guest", "room_type", "assigned_room")
    date_hierarchy = "check_in_date"
    ordering = ("-created_at",)