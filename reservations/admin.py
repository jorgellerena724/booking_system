from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        'booking_code', 
        'clients_names', 
        'hotel', 
        'date_from', 
        'date_to', 
        'status',
        'profit_percentage'
    ]
    list_filter = ['status', 'agency', 'hotel', 'room_type']
    search_fields = ['booking_code', 'clients_names', 'hotel']
    readonly_fields = ['profit_percentage', 'created_at', 'updated_at']
    fieldsets = (
        ('Información de Reserva', {
            'fields': (
                'status', 'agency', 'booking_code', 'clients_names', 
                'hotel', 'date_from', 'date_to', 'hotel_confirmation'
            )
        }),
        ('Detalles de Habitación', {
            'fields': ('pax', 'room_type')
        }),
        ('Información Financiera', {
            'fields': ('sale_price', 'touch_cost', 'profit_percentage')
        }),
        ('Información Adicional', {
            'fields': ('valid_rates', 'nationality', 'remarks')
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