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
    pax = models.IntegerField()
    room_type = models.CharField(max_length=50)
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
        if self.sale_price and self.touch_cost and self.touch_cost != 0:
            self.profit_percentage = ((self.sale_price - self.touch_cost) / self.touch_cost) * 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_code} - {self.clients_names}"

    class Meta:
        ordering = ['-created_at']