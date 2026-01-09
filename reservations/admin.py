from django.contrib import admin
from .models import Reservation, Room

class RoomInline(admin.TabularInline):
    model = Room
    extra = 1
    fields = ['room_type', 'pax_ad', 'pax_chd']
    verbose_name = "Habitación"
    verbose_name_plural = "Habitaciones"

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        'booking_code', 
        'clients_names', 
        'hotel', 
        'date_from', 
        'date_to', 
        'status',
        'profit_percentage',
        'total_pax_display'
    ]
    list_filter = ['status', 'agency', 'hotel']  # Eliminado 'room_type'
    search_fields = ['booking_code', 'clients_names', 'hotel', 'rooms__room_type']
    readonly_fields = ['profit_percentage', 'created_at', 'updated_at', 'total_pax_display']
    
    inlines = [RoomInline]  # Agregado para gestionar habitaciones
    
    fieldsets = (
        ('Información de Reserva', {
            'fields': (
                'status', 'agency', 'booking_code', 'clients_names', 
                'hotel', 'date_from', 'date_to', 'hotel_confirmation'
            )
        }),
        ('Información Financiera', {
            'fields': ('sale_price', 'touch_cost', 'profit_percentage')
        }),
        ('Información Adicional', {
            'fields': ('meal_plan', 'valid_rates', 'nationality', 'remarks')
        }),
        ('Resumen de Pasajeros', {
            'fields': ('total_pax_display',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def total_pax_display(self, obj):
        return f"AD: {obj.total_pax_ad()} | CHD: {obj.total_pax_chd()} | Total: {obj.total_pax()}"
    total_pax_display.short_description = 'Resumen PAX'

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'room_type', 'pax_ad', 'pax_chd', 'total_pax']
    list_filter = ['room_type', 'reservation__status', 'reservation__hotel']
    search_fields = ['room_type', 'reservation__booking_code', 'reservation__clients_names']
    
    def total_pax(self, obj):
        return obj.pax_ad + obj.pax_chd
    total_pax.short_description = 'Total PAX'