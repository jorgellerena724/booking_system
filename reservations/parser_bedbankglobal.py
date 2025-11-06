# parser_bedbankglobal.py - VERSIÓN CORREGIDA 
import re
from datetime import datetime
from bs4 import BeautifulSoup

def parsear_html_bedbankglobal(html_content):
    """
    Parsea el contenido HTML de BedBankGlobal manejando etiquetas y valores en líneas separadas
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    reservas = []
    
    print("=== INICIANDO PARSER BEDBANKGLOBAL - LÍNEAS SEPARADAS ===")
    
    # Obtener texto plano y dividir en líneas
    texto_completo = soup.get_text()
    lineas = texto_completo.split('\n')
    
    # Variables para el barrido
    booking_code = None
    hotel = None
    adultos = 0
    niños = 0
    bebés = 0
    pasajeros = []
    nacionalidad = None
    fecha_entrada = None
    fecha_salida = None
    room_type = None
    precio = None
    meal_plan = "All Inclusive"
    
    # Estados del barrido
    en_booking_section = False
    en_accommodation_section = False
    en_passengers_section = False
    
    # Barrido línea por línea con manejo de líneas consecutivas
    i = 0
    while i < len(lineas):
        linea_actual = lineas[i].strip()
        if not linea_actual:
            i += 1
            continue
            
        #print(f"Línea {i}: {linea_actual}")
        
        # Detectar secciones
        if "Booking Data" in linea_actual:
            en_booking_section = True
            en_accommodation_section = False
            en_passengers_section = False
            print("🔍 ENTRANDO A BOOKING DATA SECTION")
            i += 1
            continue
            
        if "Accommodation" in linea_actual:
            en_booking_section = False
            en_accommodation_section = True
            en_passengers_section = False
            print("🔍 ENTRANDO A ACCOMMODATION SECTION")
            i += 1
            continue
            
        # Extraer datos de Booking Section - manejar líneas separadas
        if en_booking_section and "Booking" in linea_actual and i + 1 < len(lineas):
            linea_siguiente = lineas[i + 1].strip()
            if "code:" in linea_siguiente:
                # Formato: Línea 85: "Booking", Línea 86: "code: Q7R1SF"
                booking_code = extraer_valor_despues_de_dos_puntos(linea_siguiente, "code:")
                print(f"✅ Booking code encontrado: {booking_code}")
                i += 2  # Saltar ambas líneas
                continue
                
        # Extraer datos de Accommodation Section - manejar líneas separadas
        if en_accommodation_section:
            # Hotel: Línea 153: "Hotel:", Línea 154: "Melia Las Dunas"
            if "Hotel:" in linea_actual and i + 1 < len(lineas):
                hotel = lineas[i + 1].strip()
                print(f"✅ Hotel encontrado: {hotel}")
                i += 2
                continue
                
            # Number of adults: Línea 159: "Number", Línea 160: "of adults: 2"
            if "Number" in linea_actual and i + 1 < len(lineas):
                linea_siguiente = lineas[i + 1].strip()
                if "of adults:" in linea_siguiente:
                    adultos_str = extraer_valor_despues_de_dos_puntos(linea_siguiente, "of adults:")
                    adultos = int(adultos_str) if adultos_str and adultos_str.isdigit() else 0
                    print(f"✅ Adultos encontrados: {adultos}")
                    i += 2
                    continue
                    
            # Children: Línea 165: "Children:", Línea 166: "0"
            if "Children:" in linea_actual and i + 1 < len(lineas):
                niños_str = lineas[i + 1].strip()
                niños = int(niños_str) if niños_str and niños_str.isdigit() else 0
                print(f"✅ Niños encontrados: {niños}")
                i += 2
                continue
                
            # Babies: Línea 171: "Babies: 0" (en una sola línea)
            if "Babies:" in linea_actual:
                bebés_str = extraer_valor_despues_de_dos_puntos(linea_actual, "Babies:")
                bebés = int(bebés_str) if bebés_str and bebés_str.isdigit() else 0
                print(f"✅ Bebés encontrados: {bebés}")
                i += 1
                continue
                
            # Passengers: Línea 177: "Passengers:", luego lista de pasajeros
            if "Passengers:" in linea_actual:
                en_passengers_section = True
                print("🔍 ENTRANDO A PASSENGERS SECTION")
                i += 1
                continue
                
            # Nationality: Línea 183: "Nationality:  SPAIN" (en una línea)
            if "Nationality:" in linea_actual:
                nacionalidad = extraer_valor_despues_de_dos_puntos(linea_actual, "Nationality:")
                print(f"✅ Nacionalidad encontrada: {nacionalidad}")
                en_passengers_section = False
                i += 1
                continue
                
            # Arrival Date y Departure Date: Líneas separadas
            if "Arrival" in linea_actual and i + 1 < len(lineas):
                linea_siguiente = lineas[i + 1].strip()
                if "Date:" in linea_siguiente:
                    fecha_str = extraer_valor_despues_de_dos_puntos(linea_siguiente, "Date:")
                    if fecha_str:
                        fecha_entrada = parsear_fecha(fecha_str)
                        print(f"✅ Fecha entrada encontrada: {fecha_str}")
                    i += 2
                    continue
                    
            if "Departure" in linea_actual and i + 1 < len(lineas):
                linea_siguiente = lineas[i + 1].strip()
                if "Date:" in linea_siguiente:
                    fecha_str = extraer_valor_despues_de_dos_puntos(linea_siguiente, "Date:")
                    if fecha_str:
                        fecha_salida = parsear_fecha(fecha_str)
                        print(f"✅ Fecha salida encontrada: {fecha_str}")
                    i += 2
                    continue
                    
            # Rooms: Línea 204: "Rooms: 1", Línea 205: "x CLASSIC ROOM DOUBLE (2 Adults)"
            if "Rooms:" in linea_actual and i + 1 < len(lineas):
                room_type_line = lineas[i + 1].strip()
                if "x CLASSIC ROOM DOUBLE" in room_type_line:
                    room_type = "CLASSIC ROOM DOUBLE"
                    print(f"✅ Room type encontrado: {room_type}")
                i += 2
                continue
                
            # Meal plan: Línea 210: "Meal", Línea 211: "plan: All Inclusive"
            if "Meal" in linea_actual and i + 1 < len(lineas):
                linea_siguiente = lineas[i + 1].strip()
                if "plan:" in linea_siguiente:
                    meal_plan = extraer_valor_despues_de_dos_puntos(linea_siguiente, "plan:")
                    print(f"✅ Meal plan encontrado: {meal_plan}")
                i += 2
                continue
                
            # Cost price: Línea 246: "Cost", Línea 247: "price: 77.38", Línea 248: "USD"
            if "Cost" in linea_actual and i + 2 < len(lineas):
                linea_siguiente1 = lineas[i + 1].strip()
                linea_siguiente2 = lineas[i + 2].strip()
                if "price:" in linea_siguiente1 and "USD" in linea_siguiente2:
                    precio_str = extraer_valor_despues_de_dos_puntos(linea_siguiente1, "price:")
                    if precio_str:
                        precio = float(precio_str)
                        print(f"✅ Precio encontrado: {precio} USD")
                    i += 3
                    continue
            
            # Pasajeros en passengers section
            if en_passengers_section and linea_actual.startswith('*'):
                nombre_match = re.match(r'\*\s*([^(]+)\s*\(Years:\s*\d+\)', linea_actual)
                if nombre_match:
                    nombre = nombre_match.group(1).strip()
                    # Corregir nombre con 'A' extra si existe
                    if nombre.endswith('A') and len(nombre) > 1:
                        nombre = nombre[:-1].strip()
                    pasajeros.append(nombre.title())
                    print(f"✅ Pasajero encontrado: {nombre}")
                i += 1
                continue
        
        i += 1  # Pasar a la siguiente línea
    
    # Validar que tenemos los datos mínimos
    if not booking_code:
        print("❌ No se pudo encontrar booking code")
        return reservas
        
    if not fecha_entrada or not fecha_salida:
        print("❌ No se pudieron encontrar las fechas de check-in/check-out")
        return reservas
    
    # Preparar datos de habitaciones
    habitaciones = [{
        'tipo': room_type or "CLASSIC ROOM DOUBLE",
        'adultos': adultos,
        'ninos': niños + bebés,  # PAX_CHD = Children + Babies
        'bebes': 0  # Ya incluidos en ninos
    }]
    
    # Crear objeto de reserva
    reserva_data = {
        'booking_code': booking_code,
        'hotel': hotel or "Hotel no especificado",
        'fecha_entrada': fecha_entrada,
        'fecha_salida': fecha_salida,
        'pasajeros': pasajeros,
        'habitaciones': habitaciones,
        'precio': precio,
        'nacionalidad': nacionalidad or "No especificada",
        'meal_plan': meal_plan,
        'proveedor': 'BedBankGlobal'
    }
    
    reservas.append(reserva_data)
    print(f"✅ Reserva parseada exitosamente: {booking_code}")
    
    # Mostrar resumen
    print(f"\n📊 RESUMEN RESERVA {booking_code}:")
    print(f"   Hotel: {reserva_data['hotel']}")
    print(f"   Fechas: {fecha_entrada.date()} a {fecha_salida.date()}")
    print(f"   Pasajeros: {', '.join(pasajeros)}")
    print(f"   Habitación: {habitaciones[0]['tipo']} (AD: {adultos}, CHD: {niños + bebés})")
    print(f"   Precio: {precio} USD")
    print(f"   Nacionalidad: {nacionalidad}")
    print(f"   Meal Plan: {meal_plan}")
    
    return reservas

def extraer_valor_despues_de_dos_puntos(linea, etiqueta):
    """
    Extrae el valor después de los dos puntos en una línea
    """
    if etiqueta in linea:
        partes = linea.split(':', 1)
        if len(partes) > 1:
            valor = partes[1].strip()
            return valor
    return None

def parsear_fecha(fecha_str):
    """Convierte string de fecha a objeto datetime"""
    try:
        return datetime.strptime(fecha_str, '%d/%m/%Y')
    except ValueError:
        print(f"⚠️  No se pudo parsear fecha: {fecha_str}")
        return None

# Función principal de procesamiento
def procesar_reserva_bedbankglobal(html_content):
    """
    Función principal que procesa el contenido HTML y devuelve las reservas
    """
    # Parsear las reservas
    reservas = parsear_html_bedbankglobal(html_content)
    
    print(f"=== PARSER COMPLETADO: {len(reservas)} reservas encontradas ===")
    return reservas