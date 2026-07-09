from django.contrib import admin
from .models import RoomTypeBase, RoomType, Room, RoomInventory


@admin.register(RoomTypeBase)
class RoomTypeBaseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("-created_at",)


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "room_type_base", "base_price", "created_at")
    list_filter = ("room_type_base",)
    search_fields = ("name",)
    autocomplete_fields = ("room_type_base",)
    ordering = ("-created_at",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "room_number", "room_type_id", "status")
    list_filter = ("status", "room_type_id")
    search_fields = ("room_number",)
    autocomplete_fields = ("room_type_id",)



@admin.register(RoomInventory)
class RoomInventoryAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "room_type_id", "total_rooms", "booked_rooms", "available_rooms")
    list_filter = ("room_type", "date")
    search_fields = ("room_type__name",)
    autocomplete_fields = ("room_type",)
    date_hierarchy = "date"
    ordering = ("-date",)

    def available_rooms(self, obj):
        return obj.total_rooms - obj.booked_rooms

    available_rooms.short_description = "Bo'sh xonalar"