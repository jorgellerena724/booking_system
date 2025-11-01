from django import forms
from .models import Reservation

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = [
            'status', 'agency', 'booking_code', 'clients_names',
            'hotel', 'date_from', 'date_to', 'hotel_confirmation',
            'pax', 'room_type', 'sale_price', 'touch_cost',
            'valid_rates', 'nationality', 'remarks'
        ]
        widgets = {
            'date_from': forms.DateInput(attrs={'type': 'date'}),
            'date_to': forms.DateInput(attrs={'type': 'date'}),
            'clients_names': forms.Textarea(attrs={'rows': 2}),
            'valid_rates': forms.Textarea(attrs={'rows': 2}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }

class ReservationSearchForm(forms.Form):
    search_text = forms.CharField(
        required=False,
        label='Buscar en todos los campos',
        widget=forms.TextInput(attrs={'placeholder': 'Texto en cualquier campo...'})
    )
    agency = forms.CharField(required=False, label='Agencia')
    hotel = forms.CharField(required=False, label='Hotel')
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Reservation.STATUS_CHOICES,
        label='Estado'
    )
    date_from = forms.DateField(
        required=False,
        label='Fecha desde',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        label='Fecha hasta',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    nationality = forms.CharField(required=False, label='Nacionalidad')
    room_type = forms.CharField(required=False, label='Tipo de habitación')