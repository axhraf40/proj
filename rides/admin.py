from django.contrib import admin
from .models import Ride, RideRequest

@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('departure_city', 'arrival_city', 'departure_date', 'departure_time', 'driver', 'available_seats', 'status')
    list_filter = ('status', 'departure_date', 'departure_city', 'arrival_city')
    search_fields = ('departure_city', 'arrival_city', 'driver__username')
    date_hierarchy = 'departure_date'

@admin.register(RideRequest)
class RideRequestAdmin(admin.ModelAdmin):
    list_display = ('ride', 'passenger', 'number_of_seats', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('passenger__username', 'ride__departure_city', 'ride__arrival_city') 