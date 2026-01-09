#!/usr/bin/env python
"""
Script CORREGIDO para importar datos del Excel de Paximum - VERSIÓN COMPLETA MEJORADA
"""

import os
import sys
import django
import pandas as pd
import re
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_project.settings')
django.setup()

from reservations.models import Reservation, Room
from django.contrib.auth.models import User

class PaximumExcelImporter:
    def __init__(self, excel_file_path, user_id=1):
        self.excel_file = excel_file_path
        self.user = User.objects.get(id=user_id)
        self.month_mapping = {
            'Enero 2025': '01', 'Febrero 2025': '02', 'MARZO 2025': '03',
            'ABRIL 2025': '04', 'MAYO 2025': '05', 'JUNIO 2025': '06',
            'JULIO 2025': '07', 'AGOSTO 2025': '08', 'SEPTIEMBRE 2025': '09',
            'OCTUBRE 2025': '10', 'NOVIEMBRE 2025': '11', 'DICIEMBRE 2025': '12'
        }
        
        self.stats = {
            'total_processed': 0,
            'created': 0,
            'skipped_duplicates': 0,
            'errors': 0
        }
    
    def print_status(self, message, type="info"):
        symbols = {
            "info": "📊",
            "success": "✅", 
            "warning": "⚠️",
            "error": "❌"
        }
        print(f"{symbols.get(type, '')} {message}")
    
    def find_header_row(self, df):
        """
        Encontrar automáticamente la fila que contiene los encabezados reales
        """
        for i in range(len(df)):
            row = df.iloc[i]
            # Buscar palabras clave que indican encabezados
            row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
            if any(keyword in row_str.upper() for keyword in ['CODIGO', 'HOTEL', 'FECHA', 'CONFIRMACION', 'PAX', 'PAXIMUM']):
                return i
        return 0
    
    def parse_pax_room(self, pax_room_text):
        if not pax_room_text or pd.isna(pax_room_text):
            return [{'room_type': 'STANDARD', 'pax_ad': 1, 'pax_chd': 0}]
        
        text = str(pax_room_text).upper().strip()
        rooms = []
        
        # Patrones de parsing
        patterns = [
            r'(\d+)\s*PAX\s*/\s*(\d+)\s*(HAB|DBL|SGL|TRP|ROOM)',
            r'(\d+)\+(\d+)\s*/\s*(\d+)\s*(HAB|DBL|SGL|TRP)',
            r'(\d+)\s*PAX',
            r'(\d+)\s*PAX\s*/\s*(\d+)\s*HAB'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    if len(match) == 2:  # "2 pax"
                        pax_total = int(match[0])
                        rooms.append({
                            'room_type': 'STANDARD',
                            'pax_ad': pax_total,
                            'pax_chd': 0
                        })
                    elif len(match) == 4 and '+' in text:  # "2+1 / 1 DBL"
                        pax_ad = int(match[0])
                        pax_chd = int(match[1])
                        room_count = int(match[2])
                        room_type = match[3]
                        for _ in range(room_count):
                            rooms.append({
                                'room_type': room_type,
                                'pax_ad': pax_ad // room_count,
                                'pax_chd': pax_chd // room_count
                            })
                    elif len(match) == 3:  # "2 pax / 1 DBL"
                        pax_total = int(match[0])
                        room_count = int(match[1])
                        room_type = match[2]
                        for _ in range(room_count):
                            rooms.append({
                                'room_type': room_type,
                                'pax_ad': pax_total // room_count,
                                'pax_chd': 0
                            })
                break
        
        if not rooms:
            numbers = re.findall(r'\d+', text)
            if numbers:
                pax_ad = int(numbers[0])
                rooms.append({
                    'room_type': 'STANDARD',
                    'pax_ad': pax_ad,
                    'pax_chd': 0
                })
            else:
                rooms.append({
                    'room_type': 'STANDARD',
                    'pax_ad': 1,
                    'pax_chd': 0
                })
        
        return rooms
    
    def parse_dates(self, date_text, sheet_name):
        """
        Parsear diferentes formatos de fecha - MEJORADO para formato día.mes
        """
        if not date_text or pd.isna(date_text):
            return None, None
        
        text = str(date_text).strip()
        
        # Formato: "21.01 - 23.01" o "06.01 - 09.01"
        if re.match(r'\d{2}\.\d{2}\s*-\s*\d{2}\.\d{2}', text):
            try:
                start_str, end_str = text.split('-')
                start_clean = start_str.strip().replace('.', '-')
                end_clean = end_str.strip().replace('.', '-')
                
                # Asumir año 2025 para todas las fechas
                start_date = datetime.strptime(f"2025-{start_clean}", "%Y-%d-%m")
                end_date = datetime.strptime(f"2025-{end_clean}", "%Y-%d-%m")
                
                return start_date.date(), end_date.date()
            except Exception as e:
                self.print_status(f"❌ Error parseando formato día.mes: {e}", "error")
        
        # Formato: "2025-04-01 00:00:00"
        if re.match(r'\d{4}-\d{2}-\d{2}', text):
            try:
                date_part = text.split(' ')[0]
                date_obj = datetime.strptime(date_part, "%Y-%m-%d")
                return date_obj.date(), date_obj.date()
            except Exception as e:
                self.print_status(f"❌ Error parseando formato YYYY-MM-DD: {e}", "error")
        
        # Si no se puede parsear, usar fechas basadas en el mes
        year = 2025
        month = self.month_mapping.get(sheet_name, '01')
        default_date = datetime(year, int(month), 1).date()
        self.print_status(f"⚠️ Usando fecha por defecto: {default_date}", "warning")
        return default_date, default_date
    
    def get_column_mapping(self, df_columns, sheet_name):
        """
        Mapear columnas numéricas a nombres lógicos - MEJORADO PARA TODAS LAS VARIACIONES
        """
        mapping = {}
        column_names = [str(col).upper() for col in df_columns]
        
        print(f"   Columnas detectadas en {sheet_name}: {column_names}")
        
        for i, col_name in enumerate(column_names):
            # CÓDIGO DE BOOKING - IMPORTANTE: Diferentes nombres por periodo
            if 'CODIGO DEL GRUPO' in col_name:  # Para Enero-Marzo
                mapping['booking_code'] = i
                print(f"   ✅ Encontrado CODIGO DEL GRUPO en columna {i}")
            elif 'CODIGO PAXIMUM' in col_name:  # Para Abril
                mapping['booking_code'] = i
                print(f"   ✅ Encontrado CODIGO PAXIMUM en columna {i}")
            elif 'PAXIMUM CODE' in col_name:  # Para Mayo-Diciembre
                mapping['booking_code'] = i
                print(f"   ✅ Encontrado PAXIMUM CODE en columna {i}")
            elif 'CODIGO' in col_name:  # Fallback para código
                mapping['booking_code'] = i
            elif 'CODE' in col_name:  # Fallback para code
                mapping['booking_code'] = i
            
            # Nombre de clientes
            elif 'NOMBRE' in col_name or 'CLIENT' in col_name:
                mapping['clients_names'] = i
            
            # Hotel
            elif 'HOTEL' in col_name:
                mapping['hotel'] = i
            
            # Fechas
            elif 'FECHA' in col_name or 'DESDE' in col_name or 'FROM' in col_name:
                mapping['date_from'] = i
            elif 'HASTA' in col_name or 'TO' in col_name:
                mapping['date_to'] = i
            
            # Confirmación - IMPORTANTE: Diferentes nombres por mes
            elif 'CONFIRMACION' in col_name:  # Para meses tempranos
                mapping['confirmation'] = i
                print(f"   ✅ Encontrado CONFIRMACION en columna {i}")
            elif 'HOTEL' in col_name and 'CONFIRMATION' in col_name:  # Para meses posteriores
                mapping['confirmation'] = i
                print(f"   ✅ Encontrado HOTEL CONFIRMATION en columna {i}")
            elif 'CONFIRMATION' in col_name:  # Fallback
                mapping['confirmation'] = i
            
            # PAX/ROOM
            elif 'PAX' in col_name and 'ROOM' in col_name:
                mapping['pax_room'] = i
            elif 'PAX' in col_name and 'HAB' in col_name:
                mapping['pax_room'] = i
            
            # Precio de venta
            elif 'SALE' in col_name or 'VENTA' in col_name:
                mapping['sale_price'] = i
            
            # COSTO - IMPORTANTE: Diferentes nombres por mes
            elif 'COSTO' in col_name and 'HOTEL' in col_name:  # Para ABRIL
                mapping['touch_cost'] = i
                print(f"   ✅ Encontrado COSTO HOTEL en columna {i}")
            elif 'TOUCH' in col_name and 'COST' in col_name:  # Para otros meses
                mapping['touch_cost'] = i
                print(f"   ✅ Encontrado TOUCH COST en columna {i}")
            elif 'COST' in col_name:  # Fallback
                mapping['touch_cost'] = i
            
            # Tarifas válidas
            elif 'TARIFAS' in col_name or 'RATES' in col_name:
                mapping['valid_rates'] = i
            
            # Observaciones
            elif 'REMARKS' in col_name or 'OBSERVACIONES' in col_name:
                mapping['remarks'] = i
        
        # Verificar que tenemos las columnas críticas
        critical_columns = ['booking_code', 'hotel', 'date_from']
        missing_columns = [col for col in critical_columns if col not in mapping]
        if missing_columns:
            print(f"   ⚠️  Columnas críticas faltantes: {missing_columns}")
        
        # Verificar booking_code - CRÍTICO
        if 'booking_code' not in mapping:
            print(f"   ❌ COLUMNA BOOKING CODE NO ENCONTRADA en {sheet_name}")
            for i, col_name in enumerate(column_names):
                if any(word in col_name for word in ['CODIGO', 'CODE', 'GRUPO', 'PAXIMUM']):
                    mapping['booking_code'] = i
                    print(f"   🔍 Asumiendo booking_code en columna {i}: {col_name}")
                    break
        
        # Verificar touch_cost
        if 'touch_cost' not in mapping:
            print(f"   ❌ COLUMNA TOUCH COST NO ENCONTRADA en {sheet_name}")
            for i, col_name in enumerate(column_names):
                if any(word in col_name for word in ['COST', 'PRICE', 'PRECIO']):
                    if 'SALE' not in col_name and 'VENTA' not in col_name:
                        mapping['touch_cost'] = i
                        print(f"   🔍 Asumiendo touch_cost en columna {i}: {col_name}")
                        break
        
        # Verificar confirmation
        if 'confirmation' not in mapping:
            print(f"   ❌ COLUMNA CONFIRMACIÓN NO ENCONTRADA en {sheet_name}")
            for i, col_name in enumerate(column_names):
                if any(word in col_name for word in ['CONFIRMACION', 'CONFIRMATION']):
                    mapping['confirmation'] = i
                    print(f"   🔍 Asumiendo confirmation en columna {i}: {col_name}")
                    break
        
        print(f"   Mapeo final: {mapping}")
        return mapping
    
    def get_numeric_value(self, value, default=0):
        """Convertir valor a numérico de forma segura"""
        if pd.isna(value):
            return default
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                # Limpiar string y convertir
                cleaned = value.replace(',', '.').replace(' ', '').replace('$', '').replace('USD', '')
                return float(cleaned) if cleaned and cleaned != 'NAN' else default
            else:
                return default
        except (ValueError, TypeError):
            return default
    
    def get_cell_value(self, row, col_index, default=''):
        """Obtener valor de celda de forma segura"""
        if col_index is None or col_index >= len(row):
            return default
        value = row.iloc[col_index]
        return value if pd.notna(value) else default
    
    def process_sheet(self, sheet_name, df):
        self.print_status(f"Procesando hoja: {sheet_name}", "info")
        
        # Encontrar fila de encabezado
        header_row = self.find_header_row(df)
        print(f"   Usando fila {header_row} como encabezado")
        
        # Si no es la primera fila, re-leer el DataFrame
        if header_row > 0:
            df = pd.read_excel(self.excel_file, sheet_name=sheet_name, header=header_row)
            print(f"   Nuevas columnas: {list(df.columns)}")
        
        # Obtener mapeo de columnas MEJORADO
        column_mapping = self.get_column_mapping(df.columns, sheet_name)
        
        sheet_reservas = 0
        
        for index, row in df.iterrows():
            self.stats['total_processed'] += 1
            
            try:
                # Obtener código de reserva - MEJORADO
                booking_code = str(self.get_cell_value(row, column_mapping.get('booking_code'))).strip()
                
                if not booking_code or booking_code == 'NAN' or any(keyword in booking_code for keyword in ['CODIGO', 'GRUPO', 'PAXIMUM']):
                    continue
                
                # Verificar si ya existe
                if Reservation.objects.filter(booking_code=booking_code).exists():
                    self.print_status(f"Duplicado: {booking_code}", "warning")
                    self.stats['skipped_duplicates'] += 1
                    continue
                
                # Obtener otros datos
                clients_names = str(self.get_cell_value(row, column_mapping.get('clients_names'), 'CLIENTE PAXIMUM')).upper()
                hotel = str(self.get_cell_value(row, column_mapping.get('hotel'), 'HOTEL NO ESPECIFICADO')).upper()
                
                # Fechas - MEJORADO
                date_from_text = self.get_cell_value(row, column_mapping.get('date_from'))
                date_from, date_to = self.parse_dates(date_from_text, sheet_name)
                
                if not date_from:
                    self.print_status(f"Sin fechas válidas: {booking_code}", "error")
                    self.stats['errors'] += 1
                    continue
                
                # PAX/ROOM
                pax_room_text = self.get_cell_value(row, column_mapping.get('pax_room'))
                rooms_data = self.parse_pax_room(pax_room_text)
                
                # Precios - MEJORADO para detectar correctamente touch_cost
                sale_price = self.get_numeric_value(self.get_cell_value(row, column_mapping.get('sale_price')))
                touch_cost = self.get_numeric_value(self.get_cell_value(row, column_mapping.get('touch_cost')))
                
                # Confirmación del hotel - MEJORADO
                hotel_confirmation = str(self.get_cell_value(row, column_mapping.get('confirmation'), '')).upper()
                
                # Otros campos
                valid_rates = str(self.get_cell_value(row, column_mapping.get('valid_rates'), '')).upper()
                remarks = str(self.get_cell_value(row, column_mapping.get('remarks'), f"IMPORTADO DESDE EXCEL - {sheet_name}")).upper()
                
                # Determinar estado
                status = 'OK'
                if 'CXX' in hotel_confirmation or 'CANCELADO' in remarks:
                    status = 'CXX'
                
                # Crear la reserva
                reserva = Reservation(
                    status=status,
                    agency='PAXIMUM',
                    booking_code=booking_code,
                    clients_names=clients_names,
                    hotel=hotel,
                    date_from=date_from,
                    date_to=date_to,
                    hotel_confirmation=hotel_confirmation,
                    meal_plan='ALL INCLUSIVE',
                    sale_price=sale_price,
                    touch_cost=touch_cost,
                    valid_rates=valid_rates,
                    nationality='NO ESPECIFICADA',
                    remarks=remarks,
                    created_by=self.user
                )
                
                reserva.save()
                
                # Crear habitaciones
                for room_info in rooms_data:
                    Room.objects.create(
                        reservation=reserva,
                        room_type=room_info['room_type'],
                        pax_ad=room_info['pax_ad'],
                        pax_chd=room_info['pax_chd']
                    )
                
                sheet_reservas += 1
                self.stats['created'] += 1
                self.print_status(f"Creada: {booking_code} - {hotel} (${sale_price}/${touch_cost})", "success")
                
            except Exception as e:
                self.print_status(f"Error en fila {index}: {str(e)}", "error")
                self.stats['errors'] += 1
                continue
        
        return sheet_reservas
    
    def import_all_sheets(self):
        self.print_status("INICIANDO IMPORTACIÓN DESDE EXCEL PAXIMUM - VERSIÓN COMPLETA MEJORADA", "info")
        
        try:
            if not os.path.exists(self.excel_file):
                self.print_status(f"Archivo no encontrado: {self.excel_file}", "error")
                return
            
            excel_file = pd.ExcelFile(self.excel_file)
            self.print_status(f"Archivo cargado: {len(excel_file.sheet_names)} hojas", "info")
            
            for sheet_name in excel_file.sheet_names:
                if sheet_name in ['Consolidado', 'Cancelaciones']:
                    self.print_status(f"Saltando hoja: {sheet_name}", "warning")
                    continue
                
                try:
                    # Leer sin encabezado primero para detectar la fila correcta
                    df_raw = pd.read_excel(self.excel_file, sheet_name=sheet_name, header=None)
                    reservas_en_sheet = self.process_sheet(sheet_name, df_raw)
                    self.print_status(f"Hoja {sheet_name}: {reservas_en_sheet} reservas creadas", "success")
                except Exception as e:
                    self.print_status(f"Error en hoja {sheet_name}: {str(e)}", "error")
                    continue
            
            # Resumen final
            self.print_status("\n" + "="*50, "info")
            self.print_status("RESUMEN FINAL DE IMPORTACIÓN", "info")
            self.print_status(f"Total procesadas: {self.stats['total_processed']}", "info")
            self.print_status(f"Creadas: {self.stats['created']}", "success")
            self.print_status(f"Duplicados omitidos: {self.stats['skipped_duplicates']}", "warning")
            self.print_status(f"Errores: {self.stats['errors']}", "error")
            self.print_status("="*50, "info")
            
        except Exception as e:
            self.print_status(f"Error crítico: {str(e)}", "error")

def main():
    print("Script de Importación Paximum Excel - VERSIÓN COMPLETA MEJORADA")
    print("=" * 60)
    print("MEJORAS COMPLETAS:")
    print("- CODIGO DEL GRUPO (Enero-Marzo)")
    print("- CODIGO PAXIMUM (Abril)") 
    print("- PAXIMUM CODE (Mayo-Diciembre)")
    print("- CONFIRMACION (Enero-Abril)")
    print("- Hotel confirmation (Mayo-Diciembre)")
    print("- COSTO HOTEL (Abril) vs TOUCH COST (otros meses)")
    print("- Parseo mejorado de fechas en formato día.mes")
    print("=" * 60)
    
    EXCEL_FILE = input("Ruta del archivo Excel (o Enter para default): ").strip()
    if not EXCEL_FILE:
        EXCEL_FILE = "PAXIMUM - MANIFIESTO DE CONFIRMACION HOTELES - 2025.xlsx"
    
    USER_ID = input("ID de usuario (o Enter para 1): ").strip()
    if not USER_ID:
        USER_ID = 1
    else:
        USER_ID = int(USER_ID)
    
    print(f"\nConfiguración:")
    print(f"   Archivo: {EXCEL_FILE}")
    print(f"   User ID: {USER_ID}")
    
    confirm = input("\n¿Continuar con la importación? (s/N): ").strip().lower()
    if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
        print("Importación cancelada")
        return
    
    importer = PaximumExcelImporter(EXCEL_FILE, USER_ID)
    importer.import_all_sheets()

if __name__ == '__main__':
    main()