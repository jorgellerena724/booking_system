from django.db import models
from django.contrib.auth.models import User

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('OK', 'Confirmada'),
        ('CXX', 'Cancelada'),
        ('PENDING', 'Pendiente'),
    ]
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='OK'
    )
    agency = models.CharField(max_length=100)
    booking_code = models.CharField(max_length=50, unique=True)
    clients_names = models.TextField()
    hotel = models.CharField(max_length=200)
    date_from = models.DateField()
    date_to = models.DateField()
    hotel_confirmation = models.CharField(max_length=100, blank=True)
    
    # CAMPOS ELIMINADOS: pax_ad, pax_chd, room_type (ahora están en Room)
    
    meal_plan = models.TextField(blank=True, verbose_name='Plan de Comidas')
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    touch_cost = models.DecimalField(max_digits=10, decimal_places=2)
    profit_percentage = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    valid_rates = models.TextField(blank=True)
    nationality = models.CharField(max_length=50)
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calcular automáticamente el profit percentage al guardar
        # Solo si no está cancelada y tenemos los datos necesarios
        if self.status != 'CXX' and self.sale_price is not None and self.touch_cost is not None:
            try:
                if self.touch_cost > 0:
                    self.profit_percentage = ((self.sale_price - self.touch_cost) / self.touch_cost) * 100
                else:
                    self.profit_percentage = 0
            except (TypeError, ZeroDivisionError):
                self.profit_percentage = 0
        elif self.status == 'CXX':
            self.profit_percentage = 0
        
        super().save(*args, **kwargs)

    def total_pax_ad(self):
        """Calcular el total de PAX adultos sumando todas las habitaciones"""
        return sum(room.pax_ad for room in self.rooms.all())

    def total_pax_chd(self):
        """Calcular el total de PAX niños sumando todas las habitaciones"""
        return sum(room.pax_chd for room in self.rooms.all())

    def total_pax(self):
        """Calcular el total de pasajeros"""
        return self.total_pax_ad() + self.total_pax_chd()

    def get_rooms_display(self):
        """Obtener representación de texto de todas las habitaciones"""
        rooms = []
        for room in self.rooms.all():
            rooms.append(f"{room.room_type} (AD:{room.pax_ad}/CHD:{room.pax_chd})")
        return " | ".join(rooms)

    def __str__(self):
        return f"{self.booking_code} - {self.clients_names}"

    class Meta:
        ordering = ['created_at']

class Room(models.Model):
    reservation = models.ForeignKey(
        Reservation, 
        on_delete=models.CASCADE, 
        related_name='rooms'
    )
    room_type = models.CharField(max_length=100, verbose_name='Tipo de Habitación')
    pax_ad = models.IntegerField(
        verbose_name='PAX Adultos', 
        default=1,
        help_text='Número de adultos en esta habitación'
    )
    pax_chd = models.IntegerField(
        verbose_name='PAX Niños', 
        default=0,
        help_text='Número de niños en esta habitación'
    )
    
    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.room_type} - AD:{self.pax_ad} CHD:{self.pax_chd}"