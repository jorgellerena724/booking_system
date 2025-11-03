from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Sum, Count, Avg, Q
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
    
    # Ordenamiento por fecha de check-in (ascendente por defecto)
    order_by = request.GET.get('order_by', 'date_from')
    reservations = Reservation.objects.all().order_by(order_by)
    
    # Paginación
    paginator = Paginator(reservations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'reservations/list.html', {
        'page_obj': page_obj,
        'current_order': order_by
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
    
    # Ordenamiento por fecha de check-in (ascendente por defecto)
    order_by = request.GET.get('order_by', 'date_from')
    reservations = Reservation.objects.all().order_by(order_by)
    
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
                models.Q(agency__icontains=search_text) |
                models.Q(meal_plan__icontains=search_text)
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
        'search_performed': search_performed,
        'current_order': order_by
    })

@login_required
def export_reservations_excel(request):
    # Replicar la misma lógica de filtros que en reservation_list
    form = ReservationSearchForm(request.GET or None)
    reservations = Reservation.objects.all().order_by('date_from')
    
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
                models.Q(agency__icontains=search_text) |
                models.Q(meal_plan__icontains=search_text)
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
            'PAX ADULTOS': reservation.pax_ad,
            'PAX NIÑOS': reservation.pax_chd,
            'TOTAL PAX': reservation.total_pax(),
            'ROOM-TYPE': reservation.room_type,
            'MEAL PLAN': reservation.meal_plan,
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
    try:
        # Replicar la misma lógica de filtros que en reservation_search
        form = ReservationSearchForm(request.GET or None)
        reservations = Reservation.objects.all().order_by('date_from')
        
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
                    models.Q(agency__icontains=search_text) |
                    models.Q(meal_plan__icontains=search_text)
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
        
        # Estadísticas para el reporte - EXCLUIR CANCELADAS de ingresos
        total_reservations = reservations.count()
        active_reservations = reservations.exclude(status='CXX')
        total_revenue = active_reservations.aggregate(total=Sum('sale_price'))['total'] or 0
        total_cost = active_reservations.aggregate(total=Sum('touch_cost'))['total'] or 0
        total_profit = total_revenue - total_cost
        
        # Preparar contexto
        context = {
            'reservations': reservations,
            'total_reservations': total_reservations,
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'filters_applied': any(field in request.GET for field in [
                'search_text', 'agency', 'hotel', 'status', 'date_from', 'date_to', 'nationality', 'room_type'
            ]),
            'request': request,
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
        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            encoding='UTF-8'
        )
        
        # Si hubo error al generar el PDF
        if pisa_status.err:
            return HttpResponse(f'Error al generar PDF: {pisa_status.err}')
            
        return response
        
    except Exception as e:
        return HttpResponse(f'Error inesperado al generar PDF: {str(e)}')

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
    
    # MÉTRICAS FINANCIERAS - EXCLUIR CANCELADAS
    active_reservations = reservations.exclude(status='CXX')
    
    # Debug: Verificar datos individuales
    problematic_reservations = active_reservations.filter(touch_cost__gt=models.F('sale_price'))
    print(f"Reservas con costo mayor a venta: {problematic_reservations.count()}")
    
    total_revenue = active_reservations.aggregate(total=Sum('sale_price'))['total'] or 0
    total_cost = active_reservations.aggregate(total=Sum('touch_cost'))['total'] or 0
    total_profit = total_revenue - total_cost
    
    # Calcular margen promedio manualmente para verificar
    total_margin = 0
    count_with_margin = 0
    
    for reservation in active_reservations:
        if reservation.touch_cost and reservation.touch_cost > 0:
            individual_margin = ((reservation.sale_price - reservation.touch_cost) / reservation.touch_cost) * 100
            total_margin += individual_margin
            count_with_margin += 1
    
    avg_profit_percentage_manual = total_margin / count_with_margin if count_with_margin > 0 else 0
    avg_profit_percentage = active_reservations.aggregate(avg=Avg('profit_percentage'))['avg'] or 0
    
    print(f"Revenue: {total_revenue}, Cost: {total_cost}, Profit: {total_profit}")
    print(f"Margen DB: {avg_profit_percentage}, Margen Manual: {avg_profit_percentage_manual}")
    
    # MÉTRICAS OPERATIVAS
    total_reservations = reservations.count()
    cancelled_reservations = reservations.filter(status='CXX').count()
    active_reservations_count = total_reservations - cancelled_reservations
    cancellation_rate = (cancelled_reservations / total_reservations * 100) if total_reservations > 0 else 0
    
    status_counts = reservations.values('status').annotate(count=Count('id'))
    hotel_counts = reservations.values('hotel').annotate(count=Count('id')).order_by('-count')[:10]
    agency_counts = reservations.values('agency').annotate(count=Count('id')).order_by('-count')[:10]
    
    # TENDENCIAS TEMPORALES (últimos 12 meses) - EXCLUIR CANCELADAS
    from datetime import timedelta
    from django.utils import timezone
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=365)
    
    monthly_data = active_reservations.filter(
        date_from__gte=start_date
    ).extra({
        'month': "strftime('%%Y-%%m', date_from)"
    }).values('month').annotate(
        count=Count('id'),
        revenue=Sum('sale_price'),
        profit=Sum('sale_price') - Sum('touch_cost')
    ).order_by('month')
    
    # Preparar datos para gráficos
    status_order = ['OK', 'PENDING', 'CXX']
    status_counts_ordered = sorted(
        status_counts, 
        key=lambda x: status_order.index(x['status']) if x['status'] in status_order else 3
    )
    
    status_data = {
        'labels': [dict(Reservation.STATUS_CHOICES).get(item['status'], item['status']) for item in status_counts_ordered],
        'data': [item['count'] for item in status_counts_ordered],
        'colors': ['#28a745', '#ffc107', '#dc3545']
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
        'avg_profit_percentage_manual': avg_profit_percentage_manual,  # Para debugging
        
        # Métricas operativas
        'total_reservations': total_reservations,
        'cancelled_reservations': cancelled_reservations,
        'active_reservations_count': active_reservations_count,
        'cancellation_rate': cancellation_rate,
        'status_counts': status_counts,
        'hotel_counts': hotel_counts[:5],
        'agency_counts': agency_counts[:5],
        
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
    print("DEBUG CREATE: Iniciando creación de nueva reserva")
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        print(f"DEBUG CREATE - Datos POST recibidos: {request.POST}")
        
        if form.is_valid():
            print("DEBUG CREATE: Formulario es válido")
            
            try:
                # Crear la reserva pero no guardar aún
                reservation = form.save(commit=False)
                reservation.created_by = request.user
                
                print(f"DEBUG CREATE - Valores antes de guardar:")
                print(f"  PAX AD: {reservation.pax_ad} (tipo: {type(reservation.pax_ad)})")
                print(f"  PAX CHD: {reservation.pax_chd} (tipo: {type(reservation.pax_chd)})")
                print(f"  Meal Plan: '{reservation.meal_plan}'")
                print(f"  Sale Price: {reservation.sale_price}")
                print(f"  Touch Cost: {reservation.touch_cost}")
                print(f"  Status: {reservation.status}")
                
                # Guardar (esto ejecutará el método save() del modelo)
                reservation.save()
                print("DEBUG CREATE: Reserva guardada en la base de datos")
                
                # Verificar que realmente se guardó
                saved_reservation = Reservation.objects.get(pk=reservation.pk)
                print(f"DEBUG CREATE - Verificación después de guardar:")
                print(f"  ID: {saved_reservation.pk}")
                print(f"  PAX AD: {saved_reservation.pax_ad}")
                print(f"  PAX CHD: {saved_reservation.pax_chd}")
                print(f"  Meal Plan: '{saved_reservation.meal_plan}'")
                print(f"  Profit %: {saved_reservation.profit_percentage}")
                
                messages.success(request, 'Reserva creada exitosamente!')
                return redirect('reservations:list')
                
            except Exception as e:
                print(f"DEBUG CREATE: Error durante el guardado: {e}")
                messages.error(request, f'Error al crear la reserva: {str(e)}')
                
        else:
            print(f"DEBUG CREATE: Formulario inválido")
            print(f"DEBUG CREATE - Errores: {form.errors}")
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ReservationForm()
        print("DEBUG CREATE: Mostrando formulario vacío")
    
    return render(request, 'reservations/form.html', {'form': form, 'title': 'Crear Reserva'})

@login_required
def reservation_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    return render(request, 'reservations/detail.html', {'reservation': reservation})

@login_required
def reservation_update(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    
    print(f"DEBUG UPDATE: Editando reserva {reservation.booking_code}")
    print(f"DEBUG UPDATE - Valores actuales: PAX AD={reservation.pax_ad}, PAX CHD={reservation.pax_chd}")
    
    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            print("DEBUG UPDATE: Formulario válido")
            print(f"DEBUG UPDATE - Datos POST: {request.POST}")
            
            # Guardar el formulario (esto ejecutará el método save() del modelo)
            reservation = form.save()
            
            # Verificar los valores guardados
            print(f"DEBUG UPDATE - Valores después de guardar:")
            print(f"  PAX AD: {reservation.pax_ad}")
            print(f"  PAX CHD: {reservation.pax_chd}")
            print(f"  Meal Plan: {reservation.meal_plan}")
            print(f"  Profit %: {reservation.profit_percentage}")
            
            messages.success(request, f'Reserva {reservation.booking_code} actualizada exitosamente!')
            return redirect('reservations:list')
        else:
            print(f"DEBUG UPDATE: Formulario inválido - Errores: {form.errors}")
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ReservationForm(instance=reservation)
        print(f"DEBUG UPDATE - Valores en instancia: PAX AD={reservation.pax_ad}, PAX CHD={reservation.pax_chd}")
    
    return render(request, 'reservations/form.html', {'form': form, 'title': 'Editar Reserva'})

@login_required
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        reservation.delete()
        messages.success(request, 'Reserva eliminada exitosamente!')
        return redirect('reservations:list')
    return render(request, 'reservations/confirm_delete.html', {'reservation': reservation})

@login_required
def financial_debug(request):
    """Vista temporal para diagnosticar problemas financieros"""
    
    # Todas las reservas activas (OK y PENDING)
    active_reservations = Reservation.objects.filter(status__in=['OK', 'PENDING'])
    
    # Reservas problemáticas
    negative_profit_reservations = active_reservations.filter(
        models.Q(sale_price__lt=models.F('touch_cost')) |
        models.Q(profit_percentage__lt=0)
    )
    
    # Cálculos detallados
    total_revenue = active_reservations.aggregate(total=Sum('sale_price'))['total'] or 0
    total_cost = active_reservations.aggregate(total=Sum('touch_cost'))['total'] or 0
    total_profit = total_revenue - total_cost
    
    # Calcular margen manualmente y preparar datos para template
    margin_data = []
    for reservation in active_reservations:
        if reservation.touch_cost and reservation.touch_cost > 0:
            # Convertir Decimal a float para cálculos consistentes
            sale_price_float = float(reservation.sale_price)
            touch_cost_float = float(reservation.touch_cost)
            stored_margin_float = float(reservation.profit_percentage) if reservation.profit_percentage else 0.0
            
            # Calcular margen manual
            manual_margin = ((sale_price_float - touch_cost_float) / touch_cost_float) * 100
            difference = manual_margin - stored_margin_float
            
            margin_data.append({
                'reservation': reservation,
                'sale_price': sale_price_float,
                'touch_cost': touch_cost_float,
                'stored_margin': stored_margin_float,
                'manual_margin': manual_margin,
                'difference': difference
            })
    
    # Calcular margen global
    profit_margin_percentage = (float(total_profit) / float(total_cost) * 100) if total_cost and float(total_cost) > 0 else 0
    
    context = {
        'total_active_reservations': active_reservations.count(),
        'negative_profit_count': negative_profit_reservations.count(),
        'total_revenue': float(total_revenue),
        'total_cost': float(total_cost),
        'total_profit': float(total_profit),
        'profit_margin_percentage': profit_margin_percentage,
        
        'negative_profit_reservations': negative_profit_reservations,
        'margin_data': margin_data,
        
        # Métricas del dashboard para comparar
        'dashboard_margin': active_reservations.aggregate(avg=Avg('profit_percentage'))['avg'] or 0,
    }
    
    return render(request, 'reservations/financial_debug.html', context)

@login_required
def recalculate_margins(request):
    """Vista para recalcular todos los márgenes de ganancia"""
    if request.method == 'POST':
        updated_count = 0
        reservations = Reservation.objects.all()
        
        for reservation in reservations:
            # Forzar el recálculo llamando al save()
            original_margin = reservation.profit_percentage
            reservation.save()
            
            if reservation.profit_percentage != original_margin:
                updated_count += 1
        
        messages.success(request, f'Se recalcularon {updated_count} márgenes de ganancia.')
        return redirect('reservations:financial_debug')
    
    return render(request, 'reservations/confirm_recalculate.html')

@login_required
def export_dashboard_pdf(request):
    """Exportar dashboard completo a PDF"""
    try:
        # Replicar la lógica del dashboard para obtener los datos
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Base queryset
        reservations = Reservation.objects.all()
        
        # Aplicar filtros de fecha si existen
        if date_from:
            reservations = reservations.filter(date_from__gte=date_from)
        if date_to:
            reservations = reservations.filter(date_to__lte=date_to)
        
        # MÉTRICAS FINANCIERAS - EXCLUIR CANCELADAS
        active_reservations = reservations.exclude(status='CXX')
        total_revenue = active_reservations.aggregate(total=Sum('sale_price'))['total'] or 0
        total_cost = active_reservations.aggregate(total=Sum('touch_cost'))['total'] or 0
        total_profit = total_revenue - total_cost
        avg_profit_percentage = active_reservations.aggregate(avg=Avg('profit_percentage'))['avg'] or 0
        
        # MÉTRICAS OPERATIVAS
        total_reservations = reservations.count()
        cancelled_reservations = reservations.filter(status='CXX').count()
        active_reservations_count = total_reservations - cancelled_reservations
        cancellation_rate = (cancelled_reservations / total_reservations * 100) if total_reservations > 0 else 0
        
        status_counts = reservations.values('status').annotate(count=Count('id'))
        hotel_counts = reservations.values('hotel').annotate(count=Count('id')).order_by('-count')[:5]
        agency_counts = reservations.values('agency').annotate(count=Count('id')).order_by('-count')[:5]
        
        # Preparar datos para el reporte
        context = {
            # Métricas financieras
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'total_profit': total_profit,
            'avg_profit_percentage': avg_profit_percentage,
            
            # Métricas operativas
            'total_reservations': total_reservations,
            'cancelled_reservations': cancelled_reservations,
            'active_reservations_count': active_reservations_count,
            'cancellation_rate': cancellation_rate,
            'status_counts': status_counts,
            'hotel_counts': hotel_counts,
            'agency_counts': agency_counts,
            
            # Filtros aplicados
            'date_from': date_from,
            'date_to': date_to,
            'filters_applied': any([date_from, date_to]),
            
            'generated_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
        }
        
        # Renderizar template
        template = get_template('reservations/dashboard_pdf.html')
        html = template.render(context)
        
        # Crear respuesta PDF
        response = HttpResponse(content_type='application/pdf')
        filename = f"dashboard_reservas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Generar PDF
        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            encoding='UTF-8'
        )
        
        if pisa_status.err:
            return HttpResponse(f'Error al generar PDF: {pisa_status.err}')
            
        return response
        
    except Exception as e:
        return HttpResponse(f'Error inesperado al generar PDF: {str(e)}')

@login_required
def export_dashboard_excel(request):
    """Exportar métricas del dashboard a Excel"""
    try:
        # Replicar la lógica del dashboard para obtener los datos
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Base queryset
        reservations = Reservation.objects.all()
        
        # Aplicar filtros de fecha si existen
        if date_from:
            reservations = reservations.filter(date_from__gte=date_from)
        if date_to:
            reservations = reservations.filter(date_to__lte=date_to)
        
        # MÉTRICAS FINANCIERAS - EXCLUIR CANCELADAS
        active_reservations = reservations.exclude(status='CXX')
        total_revenue = active_reservations.aggregate(total=Sum('sale_price'))['total'] or 0
        total_cost = active_reservations.aggregate(total=Sum('touch_cost'))['total'] or 0
        total_profit = total_revenue - total_cost
        avg_profit_percentage = active_reservations.aggregate(avg=Avg('profit_percentage'))['avg'] or 0
        
        # MÉTRICAS OPERATIVAS
        total_reservations = reservations.count()
        cancelled_reservations = reservations.filter(status='CXX').count()
        active_reservations_count = total_reservations - cancelled_reservations
        cancellation_rate = (cancelled_reservations / total_reservations * 100) if total_reservations > 0 else 0
        
        status_counts = reservations.values('status').annotate(count=Count('id'))
        hotel_counts = reservations.values('hotel').annotate(count=Count('id')).order_by('-count')[:10]
        agency_counts = reservations.values('agency').annotate(count=Count('id')).order_by('-count')[:10]
        
        # Crear DataFrame para Excel
        data = {
            'MÉTRICA': [
                'Total Reservas',
                'Reservas Activas',
                'Reservas Canceladas',
                'Tasa de Cancelación',
                'Ingresos Totales',
                'Costo Total',
                'Ganancia Neta',
                'Margen Promedio'
            ],
            'VALOR': [
                total_reservations,
                active_reservations_count,
                cancelled_reservations,
                f"{cancellation_rate:.2f}%",
                f"${total_revenue:.2f}",
                f"${total_cost:.2f}",
                f"${total_profit:.2f}",
                f"{avg_profit_percentage:.2f}%"
            ]
        }
        
        df_metrics = pd.DataFrame(data)
        
        # DataFrame para estados
        status_data = []
        for status in status_counts:
            status_name = dict(Reservation.STATUS_CHOICES).get(status['status'], status['status'])
            status_data.append({
                'Estado': status_name,
                'Cantidad': status['count'],
                'Porcentaje': f"{(status['count'] / total_reservations * 100):.1f}%"
            })
        df_status = pd.DataFrame(status_data)
        
        # DataFrame para top hoteles
        hotel_data = []
        for hotel in hotel_counts[:5]:
            hotel_data.append({
                'Hotel': hotel['hotel'],
                'Reservas': hotel['count']
            })
        df_hotels = pd.DataFrame(hotel_data)
        
        # DataFrame para top agencias
        agency_data = []
        for agency in agency_counts[:5]:
            agency_data.append({
                'Agencia': agency['agency'],
                'Reservas': agency['count']
            })
        df_agencies = pd.DataFrame(agency_data)
        
        # Crear respuesta HTTP con el Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f"dashboard_reservas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Escribir DataFrames a Excel
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df_metrics.to_excel(writer, sheet_name='Métricas Principales', index=False)
            df_status.to_excel(writer, sheet_name='Reservas por Estado', index=False)
            df_hotels.to_excel(writer, sheet_name='Top Hoteles', index=False)
            df_agencies.to_excel(writer, sheet_name='Top Agencias', index=False)
            
            # Ajustar anchos de columnas
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
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
        
    except Exception as e:
        return HttpResponse(f'Error al generar Excel: {str(e)}')