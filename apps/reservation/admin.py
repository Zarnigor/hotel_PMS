from django.contrib import admin
from apps.reservation.models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "primary_guest",
        "room_type",
        "assigned_room",
        "check_in_date",
        "check_out_date",
        "status",
        "created_at",
    )
    list_filter = ("status", "room_type", "check_in_date", "check_out_date")
    search_fields = ("primary_guest__full_name", "primary_guest__passport")
    autocomplete_fields = ("primary_guest", "room_type", "assigned_room")
    date_hierarchy = "check_in_date"
    ordering = ("-created_at",)