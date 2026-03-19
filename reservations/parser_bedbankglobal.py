import re
from datetime import datetime
from decimal import Decimal


def limpiar_valor_html(valor):
    """Limpia valores extraídos del HTML"""
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

def parsear_bedbankglobal_final_funcional(html_content):
    """
    Parser FINAL FUNCIONAL - Extrae nacionalidad correctamente
    Ahora también separa cantidad de niños/bebés de sus edades
    """
    print("\n" + "="*60)
    print("PARSEO BEDBANKGLOBAL - VERSIÓN FINAL FUNCIONAL")
    print("="*60)
    
    reservas = []
    
    try:
        # Normalizar HTML
        html_norm = html_content.replace('\r\n', ' ').replace('\n', ' ')
        
        # ===== 1. BOOKING CODE =====
        booking_code = None
        
        booking_match = re.search(r'color:#28A745[^>]*>Booking Code:\s*([A-Z0-9]+)', html_norm)
        if not booking_match:
            booking_match = re.search(r'Booking [Cc]ode:\s*([A-Z0-9]+)', html_norm)
        
        if booking_match:
            booking_code = booking_match.group(1).strip()
            print(f"✅ Booking Code: {booking_code}")
        
        if not booking_code:
            return reservas
        
        # ===== 2. PASAJEROS =====
        pasajeros = []
        
        # Buscar sección de passengers
        passenger_section = re.search(r'Passengers[^<]*:(.*?)(?=<[^>]+>\s*<|</td>)', html_norm, re.IGNORECASE | re.DOTALL)
        
        if passenger_section:
            section = passenger_section.group(1)
            name_matches = re.findall(r'\*\s*([^(]+?)\s*\(Age:\s*\d+\)', section)
            if name_matches:
                pasajeros = [limpiar_valor_html(name).strip() for name in name_matches]
        
        if not pasajeros:
            name_matches = re.findall(r'\*\s*([^(]+?)\s*\(Age:\s*\d+\)', html_norm)
            if name_matches:
                pasajeros = [limpiar_valor_html(name).strip() for name in name_matches]
        
        if pasajeros:
            print(f"✅ Pasajeros: {len(pasajeros)}")
        else:
            pasajeros = ["CLIENTE NO ESPECIFICADO"]
            print("⚠️ Usando nombre genérico")
        
        # ===== 3. HOTEL =====
        hotel = ""
        
        hotel_match = re.search(r'Hotel[^>]*>(.*?)</span>', html_norm, re.IGNORECASE)
        if hotel_match:
            raw_hotel = hotel_match.group(1).strip()
            hotel = limpiar_valor_html(raw_hotel)
        
        if not hotel:
            hotel_match2 = re.search(r'>Hotel[^<]*<[^>]*>([^<]+)<', html_norm, re.IGNORECASE)
            if hotel_match2:
                raw_hotel = hotel_match2.group(1).strip()
                hotel = limpiar_valor_html(raw_hotel)
        
        if hotel:
            print(f"✅ Hotel: {hotel}")
        else:
            hotel = "HOTEL NO ESPECIFICADO"
            print("⚠️ Hotel no encontrado")
        
        # ===== 4. NACIONALIDAD - PATRÓN EXACTO DEL HTML =====
        nacionalidad = "NO ESPECIFICADA"
        
        # PATRÓN EXACTO basado en el HTML que vimos:
        # Nationality:&nbsp;</span></strong><span ...>&nbsp;SPAIN<o:p>
        nationality_pattern = r'Nationality[^>]*>&nbsp;</span></strong><span[^>]*>&nbsp;([A-Z]+)<'
        nationality_match = re.search(nationality_pattern, html_norm, re.IGNORECASE)
        
        if nationality_match:
            nacionalidad = nationality_match.group(1).strip()
            print(f"✅ Nacionalidad encontrada: {nacionalidad}")
        else:
            # Patrón alternativo más flexible
            alt_pattern = r'Nationality.*?>.*?([A-Z]{2,})<'
            alt_match = re.search(alt_pattern, html_norm, re.IGNORECASE | re.DOTALL)
            if alt_match:
                nacionalidad = alt_match.group(1).strip()
                print(f"✅ Nacionalidad (alternativo): {nacionalidad}")
        
        # Limpiar nacionalidad
        nacionalidad = limpiar_valor_html(nacionalidad)
        if not nacionalidad or len(nacionalidad) < 2:
            nacionalidad = "NO ESPECIFICADA"
        
        if nacionalidad != "NO ESPECIFICADA":
            print(f"✅ Nacionalidad final: {nacionalidad}")
        
        # ===== 5. FECHAS =====
        fecha_entrada = ""
        fecha_salida = ""
        
        arrival_match = re.search(r'Arrival Date[^>]*>(.*?)</span>', html_norm, re.IGNORECASE)
        if arrival_match:
            raw_fecha = arrival_match.group(1).strip()
            fecha_entrada = limpiar_valor_html(raw_fecha)
        
        departure_match = re.search(r'Departure Date[^>]*>(.*?)</span>', html_norm, re.IGNORECASE)
        if departure_match:
            raw_fecha = departure_match.group(1).strip()
            fecha_salida = limpiar_valor_html(raw_fecha)
        
        if fecha_entrada and fecha_salida:
            print(f"✅ Fechas: {fecha_entrada} a {fecha_salida}")
        else:
            all_dates = re.findall(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', html_norm)
            if len(all_dates) >= 3:
                fecha_entrada = all_dates[1]
                fecha_salida = all_dates[2]
                print(f"✅ Fechas (alternativo): {fecha_entrada} a {fecha_salida}")
        
        # Convertir a YYYY-MM-DD
        def convertir_fecha(fecha_str):
            try:
                return datetime.strptime(fecha_str, '%d/%m/%Y').strftime('%Y-%m-%d')
            except:
                return fecha_str
        
        fecha_entrada = convertir_fecha(fecha_entrada) if fecha_entrada else ""
        fecha_salida = convertir_fecha(fecha_salida) if fecha_salida else ""
        
        # ===== 6. PRECIO =====
        precio = Decimal('0')
        
        price_match = re.search(r'Cost price[^>]*>([\d.,]+)\s*USD', html_norm, re.IGNORECASE)
        if not price_match:
            all_usd = re.findall(r'([\d.,]+)\s*USD', html_norm)
            if all_usd:
                precio_str = all_usd[-1].replace(',', '')
                try:
                    precio = Decimal(precio_str)
                except:
                    pass
        
        if price_match:
            try:
                precio_str = price_match.group(1).replace(',', '')
                precio = Decimal(precio_str)
            except:
                pass
        
        if precio > 0:
            print(f"✅ Precio: {precio} USD")
        else:
            print("⚠️ Precio no encontrado")
        
        # ===== 7. HABITACIONES =====
        adultos = 2
        ninos = 0
        bebes = 0
        observaciones_list = []  # Lista para acumular observaciones
        
        # Adultos
        adults_match = re.search(r'Number of adults[^>]*>(.*?)</span>', html_norm, re.IGNORECASE)
        if adults_match:
            raw_adults = adults_match.group(1).strip()
            adults_text = limpiar_valor_html(raw_adults)
            try:
                adultos = int(adults_text) if adults_text.isdigit() else 2
            except:
                pass
        
        # Children - MODIFICADO: Separar cantidad de edades
        children_match = re.search(r'Children[^>]*>(.*?)</span>', html_norm, re.IGNORECASE)
        if children_match:
            raw_children = children_match.group(1).strip()
            children_text = limpiar_valor_html(raw_children)
            
            # Separar cantidad de edades
            # Formato esperado: "2 5,7" o "1 3" o solo "2"
            if children_text:
                children_parts = children_text.split(' ', 1)  # Separar por primer espacio
                
                if len(children_parts) >= 1 and children_parts[0].isdigit():
                    # Primer parte es la cantidad de niños
                    ninos = int(children_parts[0])
                    
                    # Si hay segunda parte, son las edades (ir a observaciones)
                    if len(children_parts) > 1 and children_parts[1].strip():
                        edades_children = children_parts[1].strip()
                        observaciones_list.append(f"Edades niños: {edades_children} años")
        
        # Babies - MODIFICADO: Separar cantidad de edades
        babies_match = re.search(r'Babies[^>]*>(.*?)</span>', html_norm, re.IGNORECASE)
        if babies_match:
            raw_babies = babies_match.group(1).strip()
            babies_text = limpiar_valor_html(raw_babies)
            
            # Separar cantidad de edades
            if babies_text:
                babies_parts = babies_text.split(' ', 1)  # Separar por primer espacio
                
                if len(babies_parts) >= 1 and babies_parts[0].isdigit():
                    # Primer parte es la cantidad de bebés
                    bebes = int(babies_parts[0])
                    
                    # Si hay segunda parte, son las edades (ir a observaciones)
                    if len(babies_parts) > 1 and babies_parts[1].strip():
                        edades_babies = babies_parts[1].strip()
                        observaciones_list.append(f"Edades bebés: {edades_babies} años")
        
        print(f"✅ Ocupación: {adultos} adultos, {ninos} niños, {bebes} bebés")
        
        # Unir todas las observaciones en un solo string
        observaciones = ""
        if observaciones_list:
            observaciones = " | ".join(observaciones_list)
            print(f"📝 Observaciones: {observaciones}")
        
        # Tipo de habitación
        room_type = "DELUXE ROOM DOUBLE"
        rooms_match = re.search(r'Rooms[^>]*>(.*?)</span>', html_norm, re.IGNORECASE)
        if rooms_match:
            raw_rooms = rooms_match.group(1).strip()
            rooms_text = limpiar_valor_html(raw_rooms)
            room_match = re.search(r'\d+\s*x\s*([^(]+)', rooms_text)
            if room_match:
                room_type = room_match.group(1).strip()
        
        print(f"🛏️ Habitación: {room_type}")
        
        habitaciones = [{
            'tipo': room_type.upper(),
            'adultos': adultos,
            'ninos': ninos,
            'bebes': bebes
        }]
        
        # ===== 8. PLAN DE COMIDAS =====
        meal_plan = "ALL INCLUSIVE"
        meal_match = re.search(r'Meal plan[^>]*>(.*?)</span>', html_norm, re.IGNORECASE)
        if meal_match:
            raw_meal = meal_match.group(1).strip()
            meal_text = limpiar_valor_html(raw_meal)
            meal_plan = meal_text if meal_text else "ALL INCLUSIVE"
        
        print(f"🍽️ Plan: {meal_plan}")
        
        # ===== 9. CREAR RESERVA =====
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
            print("🎉 IMPORTACIÓN COMPLETA 🎉")
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
        print(f"\n❌ Error en parser: {e}")
        import traceback
        traceback.print_exc()
        return []


def parsear_bedbankglobal(html_content):
    print("\n" + "="*60)
    print("PARSEO BEDBANKGLOBAL")
    print("="*60)
    return parsear_bedbankglobal_final_funcional(html_content)


def procesar_reserva_bedbankglobal(html_content):
    return parsear_bedbankglobal(html_content)