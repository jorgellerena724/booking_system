from django import forms
from .models import Reservation, Room

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_type', 'pax_ad', 'pax_chd']
        widgets = {
            'room_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Doble Standard, Suite, etc.'
            }),
            'pax_ad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '1'
            }),
            'pax_chd': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
        }

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = [
            'status', 'agency', 'booking_code', 'clients_names',
            'hotel', 'date_from', 'date_to', 'hotel_confirmation',
            'meal_plan', 'sale_price', 'touch_cost',
            'valid_rates', 'nationality', 'remarks'
        ]
        widgets = {
            'date_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'clients_names': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'valid_rates': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'meal_plan': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'agency': forms.TextInput(attrs={'class': 'form-control'}),
            'booking_code': forms.TextInput(attrs={'class': 'form-control'}),
            'hotel': forms.TextInput(attrs={'class': 'form-control'}),
            'hotel_confirmation': forms.TextInput(attrs={'class': 'form-control'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'touch_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ReservationSearchForm(forms.Form):
    search_text = forms.CharField(
        required=False,
        label='Buscar en todos los campos',
        widget=forms.TextInput(attrs={
            'placeholder': 'Texto en cualquier campo...',
            'class': 'form-control'
        })
    )
    agency = forms.CharField(
        required=False, 
        label='Agencia',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    hotel = forms.CharField(
        required=False, 
        label='Hotel',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Reservation.STATUS_CHOICES,
        label='Estado',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        label='Fecha desde',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        label='Fecha hasta',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    nationality = forms.CharField(
        required=False, 
        label='Nacionalidad',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    # AGREGAR ESTE CAMPO NUEVO
    room_type = forms.CharField(
        required=False, 
        label='Tipo de habitación',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Doble Standard, Suite, etc.'
        })
    )