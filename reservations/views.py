from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Sum, Count, Avg
from datetime import datetime
import pandas as pd
from .models import Reservation
from .forms import ReservationForm, ReservationSearchForm
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

@login_required
def reservation_list(request):
    # Verificar si se solicita exportación
    if 'export' in request.GET:
        if request.GET.get('export') == 'pdf':
            return export_reservations_pdf(request)
        else:
            return export_reservations_excel(request)
    
    reservations = Reservation.objects.all().order_by('-created_at')
    
    # Paginación
    paginator = Paginator(reservations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'reservations/list.html', {
        'page_obj': page_obj,
    })

@login_required
def reservation_search(request):
    # Verificar si se solicita exportación
    if 'export' in request.GET:
        if request.GET.get('export') == 'pdf':
            return export_reservations_pdf(request)
        else:
            return export_reservations_excel(request)
    
    form = ReservationSearchForm(request.GET or None)
    reservations = Reservation.objects.all().order_by('-created_at')
    search_performed = False
    
    if form.is_valid():
        search_text = form.cleaned_data.get('search_text')
        agency = form.cleaned_data.get('agency')
        hotel = form.cleaned_data.get('hotel')
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        nationality = form.cleaned_data.get('nationality')
        room_type = form.cleaned_data.get('room_type')
        
        search_performed = any([search_text, agency, hotel, status, date_from, date_to, nationality, room_type])
        
        if search_text:
            reservations = reservations.filter(
                models.Q(booking_code__icontains=search_text) |
                models.Q(clients_names__icontains=search_text) |
                models.Q(hotel__icontains=search_text) |
                models.Q(hotel_confirmation__icontains=search_text) |
                models.Q(valid_rates__icontains=search_text) |
                models.Q(remarks__icontains=search_text) |
                models.Q(agency__icontains=search_text)
            )
        
        if agency:
            reservations = reservations.filter(agency__icontains=agency)
        if hotel:
            reservations = reservations.filter(hotel__icontains=hotel)
        if status:
            reservations = reservations.filter(status=status)
        if nationality:
            reservations = reservations.filter(nationality__icontains=nationality)
        if room_type:
            reservations = reservations.filter(room_type__icontains=room_type)
            
        if date_from:
            reservations = reservations.filter(date_from__gte=date_from)
        if date_to:
            reservations = reservations.filter(date_to__lte=date_to)
    
    # Paginación
    paginator = Paginator(reservations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'reservations/search.html', {
        'form': form,
        'page_obj': page_obj,
        'search_performed': search_performed
    })

@login_required
def export_reservations_excel(request):
    # Replicar la misma lógica de filtros que en reservation_list
    form = ReservationSearchForm(request.GET or None)
    reservations = Reservation.objects.all().order_by('-created_at')
    
    if form.is_valid():
        search_text = form.cleaned_data.get('search_text')
        agency = form.cleaned_data.get('agency')
        hotel = form.cleaned_data.get('hotel')
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        nationality = form.cleaned_data.get('nationality')
        room_type = form.cleaned_data.get('room_type')
        
        if search_text:
            reservations = reservations.filter(
                models.Q(booking_code__icontains=search_text) |
                models.Q(clients_names__icontains=search_text) |
                models.Q(hotel__icontains=search_text) |
                models.Q(hotel_confirmation__icontains=search_text) |
                models.Q(valid_rates__icontains=search_text) |
                models.Q(remarks__icontains=search_text) |
                models.Q(agency__icontains=search_text)
            )
        
        if agency:
            reservations = reservations.filter(agency__icontains=agency)
        if hotel:
            reservations = reservations.filter(hotel__icontains=hotel)
        if status:
            reservations = reservations.filter(status=status)
        if nationality:
            reservations = reservations.filter(nationality__icontains=nationality)
        if room_type:
            reservations = reservations.filter(room_type__icontains=room_type)
            
        if date_from:
            reservations = reservations.filter(date_from__gte=date_from)
        if date_to:
            reservations = reservations.filter(date_to__lte=date_to)
    
    # Preparar datos para Excel
    data = []
    for reservation in reservations:
        data.append({
            'STATUS': reservation.get_status_display(),
            'AGENCY': reservation.agency,
            'BOOKING CODE': reservation.booking_code,
            'CLIENTS NAMES': reservation.clients_names,
            'HOTELS': reservation.hotel,
            'From': reservation.date_from.strftime('%Y-%m-%d'),
            'to': reservation.date_to.strftime('%Y-%m-%d'),
            'Hotel confirmation': reservation.hotel_confirmation,
            'PAX': reservation.pax,
            'ROOM-TYPE': reservation.room_type,
            'Sale Price': float(reservation.sale_price),
            'TOUCH COST': float(reservation.touch_cost),
            'PROFIT %': f"{float(reservation.profit_percentage):.2f}%" if reservation.profit_percentage else "0%",
            'VALID RATES TO APPLY': reservation.valid_rates,
            'NATIONALITY': reservation.nationality,
            'REMARKS': reservation.remarks,
        })
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    # Crear respuesta HTTP con el Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"reservas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Escribir DataFrame a Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='RESERVAS', index=False)
        
        # Obtener el workbook y la hoja para formatear
        workbook = writer.book
        worksheet = writer.sheets['RESERVAS']
        
        # Ajustar el ancho de las columnas
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    return response

@login_required
def export_reservations_pdf(request):
    # Replicar la misma lógica de filtros que en reservation_list
    form = ReservationSearchForm(request.GET or None)
    reservations = Reservation.objects.all().order_by('-created_at')
    
    # Aplicar filtros
    if form.is_valid():
        search_text = form.cleaned_data.get('search_text')
        agency = form.cleaned_data.get('agency')
        hotel = form.cleaned_data.get('hotel')
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        nationality = form.cleaned_data.get('nationality')
        room_type = form.cleaned_data.get('room_type')
        
        if search_text:
            reservations = reservations.filter(
                models.Q(booking_code__icontains=search_text) |
                models.Q(clients_names__icontains=search_text) |
                models.Q(hotel__icontains=search_text) |
                models.Q(hotel_confirmation__icontains=search_text) |
                models.Q(valid_rates__icontains=search_text) |
                models.Q(remarks__icontains=search_text) |
                models.Q(agency__icontains=search_text)
            )
        
        if agency:
            reservations = reservations.filter(agency__icontains=agency)
        if hotel:
            reservations = reservations.filter(hotel__icontains=hotel)
        if status:
            reservations = reservations.filter(status=status)
        if nationality:
            reservations = reservations.filter(nationality__icontains=nationality)
        if room_type:
            reservations = reservations.filter(room_type__icontains=room_type)
            
        if date_from:
            reservations = reservations.filter(date_from__gte=date_from)
        if date_to:
            reservations = reservations.filter(date_to__lte=date_to)
    
    # Estadísticas para el reporte
    total_reservations = reservations.count()
    total_revenue = reservations.aggregate(total=Sum('sale_price'))['total'] or 0
    total_profit = total_revenue - (reservations.aggregate(total=Sum('touch_cost'))['total'] or 0)
    
    # Preparar contexto
    context = {
        'reservations': reservations,
        'total_reservations': total_reservations,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'filters_applied': any(field in request.GET for field in [
            'search_text', 'agency', 'hotel', 'status', 'date_from', 'date_to', 'nationality', 'room_type'
        ]),
        'request_params': request.GET,
        'generated_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
    }
    
    # Renderizar template
    template = get_template('reservations/report_pdf.html')
    html = template.render(context)
    
    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f"reporte_reservas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Generar PDF
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), response)
    
    if pdf.err:
        return HttpResponse('Error al generar PDF', status=500)
    
    return response

@login_required
def dashboard(request):
    # Filtros de fecha opcionales
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Base queryset
    reservations = Reservation.objects.all()
    
    # Aplicar filtros de fecha si existen
    if date_from:
        reservations = reservations.filter(date_from__gte=date_from)
    if date_to:
        reservations = reservations.filter(date_to__lte=date_to)
    
    # MÉTRICAS FINANCIERAS
    total_revenue = reservations.aggregate(total=Sum('sale_price'))['total'] or 0
    total_cost = reservations.aggregate(total=Sum('touch_cost'))['total'] or 0
    total_profit = total_revenue - total_cost
    avg_profit_percentage = reservations.aggregate(avg=Avg('profit_percentage'))['avg'] or 0
    
    # MÉTRICAS OPERATIVAS
    total_reservations = reservations.count()
    status_counts = reservations.values('status').annotate(count=Count('id'))
    hotel_counts = reservations.values('hotel').annotate(count=Count('id')).order_by('-count')[:10]
    agency_counts = reservations.values('agency').annotate(count=Count('id')).order_by('-count')[:10]
    
    # TENDENCIAS TEMPORALES (últimos 12 meses)
    from datetime import timedelta
    from django.utils import timezone
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=365)
    
    monthly_data = reservations.filter(
        date_from__gte=start_date
    ).extra({
        'month': "strftime('%%Y-%%m', date_from)"
    }).values('month').annotate(
        count=Count('id'),
        revenue=Sum('sale_price'),
        profit=Sum('sale_price') - Sum('touch_cost')
    ).order_by('month')
    
    # Preparar datos para gráficos
    status_data = {
        'labels': [dict(Reservation.STATUS_CHOICES).get(item['status'], item['status']) for item in status_counts],
        'data': [item['count'] for item in status_counts],
        'colors': ['#28a745', '#dc3545', '#ffc107']  # Verde, Rojo, Amarillo
    }
    
    hotel_data = {
        'labels': [item['hotel'] for item in hotel_counts],
        'data': [item['count'] for item in hotel_counts]
    }
    
    monthly_trend = {
        'labels': [item['month'] for item in monthly_data],
        'reservations': [item['count'] for item in monthly_data],
        'revenue': [float(item['revenue'] or 0) for item in monthly_data],
        'profit': [float(item['profit'] or 0) for item in monthly_data]
    }
    
    context = {
        # Métricas financieras
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'avg_profit_percentage': avg_profit_percentage,
        
        # Métricas operativas
        'total_reservations': total_reservations,
        'status_counts': status_counts,
        'hotel_counts': hotel_counts[:5],  # Top 5 hoteles
        'agency_counts': agency_counts[:5],  # Top 5 agencias
        
        # Datos para gráficos
        'status_data': status_data,
        'hotel_data': hotel_data,
        'monthly_trend': monthly_trend,
        
        # Filtros
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'reservations/dashboard.html', context)

@login_required
def reservation_create(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.created_by = request.user
            reservation.save()
            messages.success(request, 'Reserva creada exitosamente!')
            return redirect('reservations:list')
    else:
        form = ReservationForm()
    return render(request, 'reservations/form.html', {'form': form, 'title': 'Crear Reserva'})

@login_required
def reservation_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    return render(request, 'reservations/detail.html', {'reservation': reservation})

@login_required
def reservation_update(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reserva actualizada exitosamente!')
            return redirect('reservations:list')
    else:
        form = ReservationForm(instance=reservation)
    return render(request, 'reservations/form.html', {'form': form, 'title': 'Editar Reserva'})

@login_required
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        reservation.delete()
        messages.success(request, 'Reserva eliminada exitosamente!')
        return redirect('reservations:list')
    return render(request, 'reservations/confirm_delete.html', {'reservation': reservation})