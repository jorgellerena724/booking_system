# parser_paximum.py
from bs4 import BeautifulSoup
import re
from datetime import datetime
from collections import defaultdict
from decimal import Decimal

class ParserPaximum:
    
    @staticmethod
    def parsear_html(contenido_html):
        """Parsear el HTML de Paximum de forma genérica"""
        soup = BeautifulSoup(contenido_html, 'html.parser')
        
        # Diccionario para agrupar por voucher
        reservas_por_voucher = defaultdict(lambda: {
            'voucher': '',
            'hotel': '',
            'fechas': {'checkin': None, 'checkout': None},
            'habitaciones': [],
            'huespedes': [],
            'precio_total': Decimal('0.00')
        })
        
        # Encontrar todas las secciones por voucher
        secciones_voucher = soup.find_all(string=re.compile(r'VOUCHER NO:'))
        
        for voucher_text in secciones_voucher:
            tabla_reserva = voucher_text.find_parent('table')
            if tabla_reserva:
                voucher_numero = ParserPaximum._extraer_voucher(tabla_reserva)
                if voucher_numero:
                    ParserPaximum._procesar_seccion_voucher(tabla_reserva, voucher_numero, reservas_por_voucher)
        
        return list(reservas_por_voucher.values())
    
    @staticmethod
    def _procesar_seccion_voucher(tabla_reserva, voucher_numero, reservas_por_voucher):
        """Procesar una sección de voucher específica"""
        # Inicializar datos base si es la primera vez que vemos este voucher
        if not reservas_por_voucher[voucher_numero]['voucher']:
            reservas_por_voucher[voucher_numero]['voucher'] = voucher_numero
            reservas_por_voucher[voucher_numero]['fechas'] = ParserPaximum._extraer_fechas(tabla_reserva)
            reservas_por_voucher[voucher_numero]['precio_total'] = ParserPaximum._extraer_precio(tabla_reserva)
            reservas_por_voucher[voucher_numero]['hotel'] = ParserPaximum._extraer_hotel(tabla_reserva)
        
        # Extraer y agregar habitación
        habitacion_data = ParserPaximum._extraer_info_habitacion(tabla_reserva)
        if habitacion_data:
            reservas_por_voucher[voucher_numero]['habitaciones'].append(habitacion_data)
        
        # Extraer y agregar huésped
        huesped_data = ParserPaximum._extraer_info_huesped(tabla_reserva)
        if huesped_data and not ParserPaximum._huesped_ya_existe(huesped_data, reservas_por_voucher[voucher_numero]['huespedes']):
            reservas_por_voucher[voucher_numero]['huespedes'].append(huesped_data)
    
    @staticmethod
    def _huesped_ya_existe(nuevo_huesped, lista_huespedes):
        """Verificar si un huésped ya existe en la lista"""
        for huesped in lista_huespedes:
            if (huesped['nombre'] == nuevo_huesped['nombre'] and 
                huesped['apellido'] == nuevo_huesped['apellido']):
                return True
        return False
    
    @staticmethod
    def _extraer_voucher(tabla_reserva):
        """Extraer número de voucher de forma genérica"""
        voucher_text = tabla_reserva.find(string=re.compile(r'VOUCHER NO:'))
        if voucher_text:
            return voucher_text.split('VOUCHER NO:')[-1].strip()
        return None
    
    @staticmethod
    def _extraer_hotel(tabla_reserva):
        """Extraer nombre del hotel de forma genérica"""
        # Buscar texto que contenga el nombre del hotel
        textos = [t.strip() for t in tabla_reserva.find_all(string=True) if t.strip()]
    
        # Buscar patrones específicos de Paximum
        for i, texto in enumerate(textos):
            # Buscar después de "HOTEL RESERVATION FORM" o cerca de "ROYALTON"
            if 'ROYALTON' in texto.upper():
                return texto.strip().upper()  # CONVERTIR A UPPER CASE
            elif 'HABANA' in texto.upper() and len(texto) > 3:
                return texto.strip().upper()  # CONVERTIR A UPPER CASE
    
        # Buscar en elementos strong/negrita que parezcan nombres de hotel
        strong_elements = tabla_reserva.find_all('strong')
        for element in strong_elements:
            texto = element.get_text().strip()
            # Filtrar textos que parezcan nombres de hotel (más de 2 palabras, sin números)
            if (len(texto) > 5 and 
                len(texto.split()) >= 2 and
                not any(char.isdigit() for char in texto) and
                texto not in ['PAXIMUM', 'HOTEL RESERVATION FORM', 'VOUCHER NO:']):
                return texto.upper()  # CONVERTIR A UPPER CASE
    
        # Buscar en la estructura de tablas de Paximum
        try:
            rows = tabla_reserva.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    texto = cell.get_text().strip()
                    if (len(texto) > 5 and 
                        len(texto.split()) >= 2 and
                        'ROYALTON' in texto.upper()):
                        return texto.upper()  # CONVERTIR A UPPER CASE
        except:
            pass
    
        # Último recurso: buscar cualquier texto que parezca un nombre de hotel
        for texto in textos:
            palabras = texto.split()
            if (len(palabras) >= 2 and 
                len(texto) > 5 and
                not any(char.isdigit() for char in texto) and
                texto not in ['PAXIMUM', 'HOTEL RESERVATION FORM', 'CUBA'] and
                not texto.startswith('VOUCHER')):
                return texto.upper()  # CONVERTIR A UPPER CASE
    
        return "HOTEL NO ESPECIFICADO"  # EN UPPER CASE
    
    @staticmethod
    def _extraer_fechas(tabla_reserva):
        """Extraer fechas de check-in y check-out"""
        fechas = {'checkin': None, 'checkout': None}
        textos = [t.strip() for t in tabla_reserva.find_all(string=True) if t.strip()]
        
        for i, texto in enumerate(textos):
            if 'C/in Date:' in texto and i + 1 < len(textos):
                fecha_texto = textos[i + 1]
                fechas['checkin'] = ParserPaximum._parsear_fecha(fecha_texto)
            
            elif 'C/out Date:' in texto and i + 1 < len(textos):
                fecha_texto = textos[i + 1]
                fechas['checkout'] = ParserPaximum._parsear_fecha(fecha_texto)
            
            # También buscar otros formatos de fecha
            elif 'Check-in:' in texto and i + 1 < len(textos):
                fecha_texto = textos[i + 1]
                fechas['checkin'] = ParserPaximum._parsear_fecha(fecha_texto)
            
            elif 'Check-out:' in texto and i + 1 < len(textos):
                fecha_texto = textos[i + 1]
                fechas['checkout'] = ParserPaximum._parsear_fecha(fecha_texto)
        
        return fechas
    
    @staticmethod
    def _parsear_fecha(fecha_texto):
        """Convertir fecha de múltiples formatos posibles"""
        formatos_fecha = [
            '%d.%m.%Y',  # 24.11.2025
            '%d/%m/%Y',  # 24/11/2025
            '%Y-%m-%d',  # 2025-11-24
            '%m/%d/%Y',  # 11/24/2025 (formato US)
        ]
        
        for formato in formatos_fecha:
            try:
                return datetime.strptime(fecha_texto.strip(), formato).date()
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def _extraer_info_habitacion(tabla_reserva):
        """Extraer información de la habitación de forma genérica"""
        habitacion = {
            'tipo': 'HABITACIÓN ESTÁNDAR',  # EN UPPER CASE
            'adultos': 1,
            'ninios': 0,
            'regimen': 'ALOJAMIENTO DESAYUNO'  # EN UPPER CASE
        }
        
        textos = [t.strip() for t in tabla_reserva.find_all(string=True) if t.strip()]
        
        for i, texto in enumerate(textos):
            if any(keyword in texto for keyword in ['Room:', 'Habitación:', 'Room Type:']) and i + 1 < len(textos):
                habitacion['tipo'] = textos[i + 1].strip().upper()  # CONVERTIR A UPPER CASE
            
            elif any(keyword in texto for keyword in ['Adult:', 'Adults:', 'Adultos:']) and i + 1 < len(textos):
                try:
                    habitacion['adultos'] = int(textos[i + 1])
                except (ValueError, TypeError):
                    pass
            
            elif any(keyword in texto for keyword in ['Child:', 'Children:', 'Niños:']) and i + 1 < len(textos):
                try:
                    habitacion['ninios'] = int(textos[i + 1])
                except (ValueError, TypeError):
                    pass
            
            elif any(keyword in texto for keyword in ['Board:', 'Meal Plan:', 'Régimen:']) and i + 1 < len(textos):
                habitacion['regimen'] = textos[i + 1].strip().upper()  # CONVERTIR A UPPER CASE
        
        return habitacion
    
    @staticmethod
    def _extraer_info_huesped(tabla_reserva):
        """Extraer información del huésped de forma genérica"""
        huesped = {
            'titulo': '',
            'nombre': '',
            'apellido': '',
            'nacionalidad': ''
        }
        
        # Buscar líneas que contengan datos personales
        lineas_personales = tabla_reserva.find_all(string=re.compile(
            r'(Mr|Mrs|Ms|Sr|Sra|Srta)\s+[A-Z]', re.IGNORECASE
        ))
        
        for linea in lineas_personales:
            texto = linea.strip()
            
            # Extraer título (Mr, Mrs, Ms, etc.)
            titulo_match = re.search(r'\b(Mr|Mrs|Ms|Sr|Sra|Srta)\b', texto, re.IGNORECASE)
            if titulo_match:
                huesped['titulo'] = titulo_match.group(1).upper()  # CONVERTIR A UPPER CASE
            
            # Extraer nombre y apellido (asumir que son las siguientes 2 palabras después del título)
            partes = texto.split()
            for i, parte in enumerate(partes):
                if parte.lower() in ['mr', 'mrs', 'ms', 'sr', 'sra', 'srta']:
                    if i + 1 < len(partes):
                        huesped['nombre'] = partes[i + 1].upper()  # CONVERTIR A UPPER CASE
                    if i + 2 < len(partes):
                        huesped['apellido'] = partes[i + 2].upper()  # CONVERTIR A UPPER CASE
                    break
            
            # Extraer nacionalidad (buscar palabras que parezcan países)
            paises_comunes = ['RUSSIAN', 'SPAIN', 'FRANCE', 'GERMANY', 'ITALY', 'USA', 'UK', 'MEXICO', 'BRAZIL', 'CANADIAN', 'CUBAN']
            for pais in paises_comunes:
                if pais.lower() in texto.lower():
                    huesped['nacionalidad'] = pais  # YA EN UPPER CASE
                    break
            
            # Si encontramos datos, salir del bucle
            if huesped['nombre']:
                break
        
        return huesped
    
    @staticmethod
    def _extraer_precio(tabla_reserva):
        """Extraer precio de forma genérica"""
        # Buscar en un área más amplia alrededor de la tabla
        area_busqueda = tabla_reserva
        for _ in range(5):  # Buscar en padres hasta 5 niveles
            # Buscar patrones de precio
            patrones_precio = [
                r'(\d+[.,]\d+)\s*(USD|EUR|GBP|MXN)',
                r'(USD|EUR|GBP|MXN)\s*(\d+[.,]\d+)',
                r'Price:\s*(\d+[.,]\d+)',
                r'Precio:\s*(\d+[.,]\d+)'
            ]
            
            for patron in patrones_precio:
                precio_match = area_busqueda.find(string=re.compile(patron, re.IGNORECASE))
                if precio_match:
                    # Extraer el número del precio
                    numeros = re.findall(r'\d+[.,]\d+', precio_match)
                    if numeros:
                        # Convertir a Decimal para precisión
                        precio_str = numeros[0].replace(',', '.')
                        try:
                            return Decimal(precio_str)
                        except:
                            return Decimal('0.00')
            
            # Moverse al elemento padre
            if hasattr(area_busqueda, 'parent'):
                area_busqueda = area_busqueda.parent
            else:
                break
        
        return Decimal('0.00')