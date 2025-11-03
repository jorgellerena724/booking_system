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
        default='PENDING'
    )
    agency = models.CharField(max_length=100)
    booking_code = models.CharField(max_length=50, unique=True)
    clients_names = models.TextField()
    hotel = models.CharField(max_length=200)
    date_from = models.DateField()
    date_to = models.DateField()
    hotel_confirmation = models.CharField(max_length=100, blank=True)
    
    # CAMPOS CORREGIDOS - Ahora son opcionales
    pax_ad = models.IntegerField(verbose_name='PAX Adultos', blank=True, null=True, default=0)
    pax_chd = models.IntegerField(verbose_name='PAX Niños', blank=True, null=True, default=0)
    
    room_type = models.CharField(max_length=50)
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
        
        # Asegurarse de que los campos numéricos tengan valores válidos
        if self.pax_ad is None:
            self.pax_ad = 0
        if self.pax_chd is None:
            self.pax_chd = 0
        
        super().save(*args, **kwargs)

    def total_pax(self):
        """Calcular el total de pasajeros"""
        return (self.pax_ad or 0) + (self.pax_chd or 0)

    def __str__(self):
        return f"{self.booking_code} - {self.clients_names}"

    class Meta:
        ordering = ['date_from']  # Orden ascendente por fecha de check-in