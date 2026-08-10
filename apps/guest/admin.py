from django.contrib import admin
from .models import Guest


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "country", "birthday", "passport", "created_at")
    list_filter = ("country",)
    search_fields = ("full_name", "passport")
    ordering = ("-created_at",)
