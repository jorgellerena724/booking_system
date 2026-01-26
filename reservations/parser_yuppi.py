import re
from datetime import datetime

def limpiar_valor_html(valor):
    """Limpia valores extraídos del HTML (misma función que BedBankGlobal)"""
    if not valor:
        return ""
    
    # Eliminar etiquetas HTML
    valor = re.sub(r'<[^>]*>', '', valor)
    
    # Eliminar CSS
    valor = re.sub(r'\d+(\.\d+)?\s*(pt|px|em|rem|%)[\s;]*', '', valor)
    valor = re.sub(r'font-[a-z\-]+:\s*[^;\s]+[;\s]*', '', valor, flags=re.IGNORECASE)
    valor = re.sub(r'color:\s*#[0-9A-f]+[;\s]*', '', valor, flags=re.IGNORECASE)
    
    # Eliminar entidades HTML
    valor = re.sub(r'&[a-z]+;', '', valor)
    
    # Eliminar caracteres especiales
    valor = re.sub(r"['\":;<>]", '', valor)
    valor = re.sub(r'^\s*:+\s*', '', valor)
    valor = re.sub(r'\s+', ' ', valor).strip()
    
    return valor

def parsear_yuppi(html_content):
    """
    Parser específico para emails de YUPPI
    """
    print("\n" + "="*60)
    print("PARSEO YUPPI")
    print("="*60)
    
    reservas = []
    
    try:
        # Normalizar HTML
        html_norm = html_content.replace('\r\n', ' ').replace('\n', ' ')
        
        # ===== 1. BOOKING CODE =====
        booking_code = None
        
        # Buscar Booking Code en el formato YUPPI
        # Ejemplo: <strong>Booking Code:</strong> DYQBGW
        booking_match = re.search(r'Booking Code:</strong[^>]*>\s*([A-Z0-9]+)', html_norm, re.IGNORECASE)
        
        if not booking_match:
            # Intentar otro patrón
            booking_match = re.search(r'Booking Code:\s*([A-Z0-9]+)', html_norm, re.IGNORECASE)
        
        if booking_match:
            booking_code = booking_match.group(1).strip()
            print(f"✅ Booking Code: {booking_code}")
        
        if not booking_code:
            return reservas
        
        # ===== 2. AGENCY BOOKING REFERENCE =====
        agency_ref = ""
        agency_match = re.search(r'Agency booking reference:</strong[^>]*>\s*([^<]+)', html_norm, re.IGNORECASE)
        if agency_match:
            agency_ref = limpiar_valor_html(agency_match.group(1)).strip()
            print(f"✅ Agency Ref: {agency_ref}")
        
        # ===== 3. PASAJEROS =====
        pasajeros = []
        
        # Buscar en Rooming List (formato YUPPI)
        # Ejemplo: Classic Room Single (Bed&Breakfast)<br>* Xiaoyan Zheng
        rooming_section = re.search(r'Rooming List:</strong[^>]*>(.*?)(?=<strong>|</td>)', html_norm, re.IGNORECASE | re.DOTALL)
        
        if rooming_section:
            section = rooming_section.group(1)
            # Buscar nombres con asterisco
            name_matches = re.findall(r'\*\s*([^<]+)', section)
            if name_matches:
                pasajeros = [limpiar_valor_html(name).strip() for name in name_matches]
        
        # Si no encuentra en Rooming List, buscar en otras partes
        if not pasajeros:
            # Buscar Lead guest
            lead_match = re.search(r'Lead guest:</strong[^>]*>\s*([^<]+)', html_norm, re.IGNORECASE)
            if lead_match:
                lead_name = limpiar_valor_html(lead_match.group(1)).strip()
                pasajeros = [lead_name]
        
        if pasajeros:
            print(f"✅ Pasajeros: {len(pasajeros)}")
        else:
            pasajeros = ["CLIENTE NO ESPECIFICADO"]
            print("⚠️ Usando nombre genérico")
        
        # ===== 4. HOTEL =====
        hotel = ""
        
        hotel_match = re.search(r'Hotel:</strong[^>]*>\s*([^<]+)', html_norm, re.IGNORECASE)
        if hotel_match:
            raw_hotel = hotel_match.group(1).strip()
            hotel = limpiar_valor_html(raw_hotel)
        
        if hotel:
            print(f"✅ Hotel: {hotel}")
        else:
            hotel = "HOTEL NO ESPECIFICADO"
            print("⚠️ Hotel no encontrado")
        
        # ===== 5. NACIONALIDAD =====
        nacionalidad = "NO ESPECIFICADA"
        
        nationality_match = re.search(r'Nationality:</strong[^>]*>\s*([^<]+)', html_norm, re.IGNORECASE)
        if nationality_match:
            nacionalidad = limpiar_valor_html(nationality_match.group(1)).strip()
        
        if nacionalidad and nacionalidad != "NO ESPECIFICADA":
            print(f"✅ Nacionalidad: {nacionalidad}")
        
        # ===== 6. FECHAS =====
        fecha_entrada = ""
        fecha_salida = ""
        
        checkin_match = re.search(r'Check-in date:</strong[^>]*>\s*([^<]+)', html_norm, re.IGNORECASE)
        if checkin_match:
            raw_fecha = checkin_match.group(1).strip()
            fecha_entrada = limpiar_valor_html(raw_fecha)
        
        checkout_match = re.search(r'Check-out date:</strong[^>]*>\s*([^<]+)', html_norm, re.IGNORECASE)
        if checkout_match:
            raw_fecha = checkout_match.group(1).strip()
            fecha_salida = limpiar_valor_html(raw_fecha)
        
        if fecha_entrada and fecha_salida:
            print(f"✅ Fechas: {fecha_entrada} a {fecha_salida}")
        else:
            # Buscar alternativas
            all_dates = re.findall(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', html_norm)
            if len(all_dates) >= 2:
                fecha_entrada = all_dates[0]
                fecha_salida = all_dates[1]
                print(f"✅ Fechas (alternativo): {fecha_entrada} a {fecha_salida}")
        
        # Convertir a YYYY-MM-DD
        def convertir_fecha(fecha_str):
            try:
                return datetime.strptime(fecha_str, '%d/%m/%Y').strftime('%Y-%m-%d')
            except:
                return fecha_str
        
        fecha_entrada = convertir_fecha(fecha_entrada) if fecha_entrada else ""
        fecha_salida = convertir_fecha(fecha_salida) if fecha_salida else ""
        
        # ===== 7. PRECIO =====
        precio = 0
        
        price_match = re.search(r'Total cost:</strong[^>]*>\s*([\d.,]+)\s*USD', html_norm, re.IGNORECASE)
        if not price_match:
            # Buscar cualquier número seguido de USD
            all_usd = re.findall(r'([\d.,]+)\s*USD', html_norm)
            if all_usd:
                precio_str = all_usd[-1].replace(',', '')
                try:
                    precio = float(precio_str)
                except:
                    pass
        
        if price_match:
            try:
                precio_str = price_match.group(1).replace(',', '')
                precio = float(precio_str)
            except:
                pass
        
        if precio > 0:
            print(f"✅ Precio: {precio} USD")
        else:
            print("⚠️ Precio no encontrado")
        
        # ===== 8. HABITACIONES - ANÁLISIS ESPECÍFICO YUPPI =====
        adultos = 1  # Default
        ninos = 0
        bebes = 0
        observaciones_list = []
        
        # Extraer información de Rooms
        rooms_match = re.search(r'Room\(s\):</strong[^>]*>\s*([^<]+)', html_norm, re.IGNORECASE)
        if rooms_match:
            rooms_text = limpiar_valor_html(rooms_match.group(1)).strip()
            print(f"🔍 Texto Rooms: '{rooms_text}'")
            
            # Patrón: "1 x Classic Room Single (1 Adult)"
            room_match = re.search(r'(\d+)\s*x\s*([^(]+)\((\d+)\s*Adult', rooms_text, re.IGNORECASE)
            if room_match:
                cantidad_habitaciones = int(room_match.group(1))
                room_type = room_match.group(2).strip()
                adultos = int(room_match.group(3))
                print(f"🛏️ Habitación: {cantidad_habitaciones} x {room_type} ({adultos} adultos)")
            else:
                # Intentar otro patrón
                room_type_match = re.search(r'x\s*([^(]+)', rooms_text)
                if room_type_match:
                    room_type = room_type_match.group(1).strip()
                else:
                    room_type = rooms_text
        
        # ===== 9. CHILDREN AGES - ESPECÍFICO YUPPI =====
        children_ages_match = re.search(r'Children ages:</strong[^>]*>\s*([^<]+)', html_norm, re.IGNORECASE)
        if children_ages_match:
            ages_text = limpiar_valor_html(children_ages_match.group(1)).strip()
            
            if ages_text and ages_text not in ['', '&nbsp;', ' ']:
                print(f"🔍 Children ages encontrado: '{ages_text}'")
                
                # Procesar diferentes formatos de edades
                # Formato 1: "5,7,10" (comas)
                # Formato 2: "5 7 10" (espacios)
                # Formato 3: "5;7;10" (punto y coma)
                
                # Reemplazar diferentes separadores por espacios
                ages_normalized = re.sub(r'[,;]+', ' ', ages_text)
                
                # Separar por espacios y filtrar números
                age_parts = re.findall(r'\d+', ages_normalized)
                
                if age_parts:
                    ninos = len(age_parts)
                    edades_str = ','.join(age_parts)
                    observaciones_list.append(f"Edades niños: {edades_str} años")
                    print(f"👶 Children: {ninos} (edades: {edades_str})")
        
        # ===== 10. BABIES - POR SI APARECE EN EL FUTURO =====
        # (Por ahora no hay campo específico, pero lo dejamos preparado)
        
        print(f"✅ Ocupación: {adultos} adultos, {ninos} niños, {bebes} bebés")
        
        # Unir todas las observaciones
        observaciones = ""
        if observaciones_list:
            observaciones = " | ".join(observaciones_list)
        
        # Agregar agency reference a observaciones si existe
        if agency_ref:
            if observaciones:
                observaciones += f" | Agency Ref: {agency_ref}"
            else:
                observaciones = f"Agency Ref: {agency_ref}"
        
        if observaciones:
            print(f"📝 Observaciones: {observaciones}")
        
        # Tipo de habitación (si no se extrajo antes)
        if 'room_type' not in locals():
            room_type = "STANDARD ROOM"
            room_type_match = re.search(r'Room\(s\):</strong[^>]*>\s*([^<]+)', html_norm, re.IGNORECASE)
            if room_type_match:
                raw_room = room_type_match.group(1).strip()
                room_type = limpiar_valor_html(raw_room)
        
        print(f"🛏️ Tipo habitación: {room_type}")
        
        # Crear estructura de habitaciones
        habitaciones = [{
            'tipo': room_type.upper(),
            'adultos': adultos,
            'ninos': ninos,
            'bebes': bebes
        }]
        
        # ===== 11. PLAN DE COMIDAS =====
        meal_plan = "BED & BREAKFAST"
        meal_match = re.search(r'Board type:</strong[^>]*>\s*([^<]+)', html_norm, re.IGNORECASE)
        if meal_match:
            raw_meal = meal_match.group(1).strip()
            meal_text = limpiar_valor_html(raw_meal)
            meal_plan = meal_text if meal_text else "BED & BREAKFAST"
        
        print(f"🍽️ Plan: {meal_plan}")
        
        # ===== 12. CREAR RESERVA =====
        if fecha_entrada and fecha_salida:
            # Concatenar TODOS los nombres de pasajeros
            nombres_completos = ", ".join([p.upper() for p in pasajeros])
            
            reserva = {
                'booking_code': booking_code,
                'voucher': booking_code,
                'pasajeros': pasajeros,
                'nombres_completos': nombres_completos,
                'nacionalidad': nacionalidad.upper(),
                'hotel': hotel.upper(),
                'fechas': {
                    'checkin': fecha_entrada,
                    'checkout': fecha_salida
                },
                'fecha_entrada': fecha_entrada,
                'fecha_salida': fecha_salida,
                'precio': precio,
                'precio_total': precio,
                'habitaciones': habitaciones,
                'meal_plan': meal_plan.upper(),
                'observaciones': observaciones.upper() if observaciones else ""
            }
            
            reservas.append(reserva)
            
            print("\n" + "="*60)
            print("🎉 IMPORTACIÓN YUPPI COMPLETA 🎉")
            print("="*60)
            print(f"📋 Código: {booking_code}")
            print(f"🏨 Hotel: {hotel}")
            print(f"📅 Check-in: {fecha_entrada}")
            print(f"📅 Check-out: {fecha_salida}")
            print(f"👥 Huéspedes: {nombres_completos}")
            print(f"💰 Total: {precio} USD")
            print(f"🛏️ Tipo: {room_type}")
            print(f"🍽️ Régimen: {meal_plan}")
            print(f"🇪🇸 Nacionalidad: {nacionalidad}")
            if observaciones:
                print(f"📝 Observaciones: {observaciones}")
            print("="*60 + "\n")
        
        return reservas
        
    except Exception as e:
        print(f"\n❌ Error en parser YUPPI: {e}")
        import traceback
        traceback.print_exc()
        return []


def procesar_reserva_yuppi(html_content):
    """
    Función principal para procesar reservas de YUPPI
    (Mantiene compatibilidad con la interfaz de BedBankGlobal)
    """
    return parsear_yuppi(html_content)
