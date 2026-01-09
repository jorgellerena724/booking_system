import os
import sys
import django
import pandas as pd

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_project.settings')
django.setup()

from reservations.models import Reservation, Room
from django.contrib.auth.models import User

print("=== DIAGNÓSTICO COMPLETO IMPORTACIÓN PAXIMUM ===")

# 1. Verificar estado inicial
print(f"📊 Reservas en BD antes: {Reservation.objects.count()}")

# 2. Verificar que el archivo Excel existe y es legible
excel_file = "PAXIMUM - MANIFIESTO DE CONFIRMACION HOTELES - 2025.xlsx"
print(f"📁 Verificando archivo: {excel_file}")

if not os.path.exists(excel_file):
    print(f"❌ Archivo no encontrado: {excel_file}")
    sys.exit(1)

print("✅ Archivo Excel encontrado")

# 3. Intentar leer el Excel
try:
    excel_data = pd.ExcelFile(excel_file)
    print(f"✅ Excel cargado: {len(excel_data.sheet_names)} hojas")
    print(f"📑 Hojas: {excel_data.sheet_names}")
except Exception as e:
    print(f"❌ Error leyendo Excel: {e}")
    sys.exit(1)

# 4. Procesar cada hoja y mostrar información
for sheet_name in excel_data.sheet_names:
    if sheet_name in ['Consolidado', 'Cancelaciones']:
        continue
        
    print(f"\n--- Procesando hoja: {sheet_name} ---")
    
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        print(f"   Filas: {len(df)}")
        print(f"   Columnas: {list(df.columns)}")
        
        # Buscar códigos de reserva en las primeras filas
        booking_codes = []
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            # Buscar en diferentes nombres de columna
            for col_name in ['CODIGO DEL GRUPO', 'PAXIMUM CODE', 'CODIGO PAXIMUM']:
                if col_name in df.columns and pd.notna(row[col_name]):
                    code = str(row[col_name]).strip()
                    if code and code != 'nan' and not code.startswith('CODIGO'):
                        booking_codes.append(code)
                        break
        
        print(f"   Códigos encontrados (primeras 5 filas): {booking_codes}")
        
    except Exception as e:
        print(f"   ❌ Error procesando hoja: {e}")

# 5. Verificar usuario para importación
try:
    user = User.objects.get(id=1)
    print(f"\n✅ Usuario para importación: {user.username} (ID: {user.id})")
except User.DoesNotExist:
    print(f"\n❌ Usuario con ID 1 no existe")

# 6. Probar una importación real de una fila específica
print(f"\n--- PRUEBA DE IMPORTACIÓN REAL ---")
try:
    # Tomar la primera hoja de meses
    test_sheet = None
    for sheet_name in excel_data.sheet_names:
        if sheet_name not in ['Consolidado', 'Cancelaciones']:
            test_sheet = sheet_name
            break
    
    if test_sheet:
        df = pd.read_excel(excel_file, sheet_name=test_sheet)
        
        # Buscar la primera fila con datos reales
        for i in range(len(df)):
            row = df.iloc[i]
            booking_code = None
            
            # Buscar código de reserva
            for col_name in ['CODIGO DEL GRUPO', 'PAXIMUM CODE', 'CODIGO PAXIMUM']:
                if col_name in df.columns and pd.notna(row[col_name]):
                    code = str(row[col_name]).strip()
                    if code and code != 'nan' and not code.startswith('CODIGO'):
                        booking_code = code
                        break
            
            if booking_code:
                print(f"📝 Probando importar: {booking_code}")
                
                # Verificar si ya existe
                if Reservation.objects.filter(booking_code=booking_code).exists():
                    print(f"   ⚠️  Ya existe en BD, probando con otro...")
                    continue
                
                # Intentar crear reserva
                try:
                    # Datos mínimos para prueba
                    reserva = Reservation(
                        status='OK',
                        agency='PAXIMUM',
                        booking_code=booking_code,
                        clients_names='CLIENTE PRUEBA IMPORT',
                        hotel='HOTEL PRUEBA IMPORT',
                        date_from='2025-01-01',
                        date_to='2025-01-02',
                        sale_price=100,
                        touch_cost=80,
                        nationality='TEST',
                        remarks='PRUEBA DE IMPORTACIÓN',
                        created_by=user
                    )
                    reserva.save()
                    print(f"   ✅ Reserva de prueba creada: {booking_code}")
                    
                    # Crear habitación
                    room = Room(
                        reservation=reserva,
                        room_type='STANDARD',
                        pax_ad=2,
                        pax_chd=0
                    )
                    room.save()
                    print(f"   ✅ Habitación creada")
                    
                    # Eliminar prueba
                    reserva.delete()
                    print(f"   ✅ Prueba limpiada")
                    
                    break  # Solo probar una reserva
                    
                except Exception as e:
                    print(f"   ❌ Error creando reserva: {e}")
                    import traceback
                    traceback.print_exc()
                    break

except Exception as e:
    print(f"❌ Error en prueba de importación: {e}")

print(f"\n📊 Reservas en BD después: {Reservation.objects.count()}")
print("=== DIAGNÓSTICO COMPLETADO ===")