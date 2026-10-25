from django.contrib import admin

from .models import Booking, Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity", "price_per_day")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "car", "user", "start_date", "end_date", "total_cost", "is_approved")
    list_filter = ("is_approved", "car")
