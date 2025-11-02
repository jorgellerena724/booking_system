import os
import sys
import threading
import webbrowser
from time import sleep

def setup_environment():
    """Configura el entorno para la aplicación standalone"""
    if hasattr(sys, '_MEIPASS'):
        # Estamos en el ejecutable PyInstaller
        base_path = sys._MEIPASS
    else:
        # Estamos en desarrollo
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    sys.path.insert(0, base_path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_project.settings')

def init_database():
    """Inicializa la base de datos si es necesario"""
    try:
        import django
        django.setup()
        
        from django.core.management import execute_from_command_line
        from django.conf import settings
        
        # Configurar settings para standalone
        settings.DEBUG = False
        settings.ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']
        
        # Deshabilitar SSL en standalone
        settings.SECURE_SSL_REDIRECT = False
        settings.SESSION_COOKIE_SECURE = False
        settings.CSRF_COOKIE_SECURE = False
        
        # Verificar si la base de datos existe y tiene tablas
        from django.db import connection
        from django.db.utils import OperationalError
        
        try:
            connection.ensure_connection()
            print("✅ Base de datos conectada")
            
            # Verificar si hay usuarios, si no, crear superusuario
            from django.contrib.auth.models import User
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser('admin', 'admin@localhost', 'admin123')
                print("✅ Usuario admin creado: admin / admin123")
                
        except OperationalError:
            print("⚠️  Creando base de datos...")
            execute_from_command_line(['manage.py', 'migrate', '--noinput'])
            
            # Crear superusuario
            from django.contrib.auth.models import User
            User.objects.create_superuser('admin', 'admin@localhost', 'admin123')
            print("✅ Usuario admin creado: admin / admin123")
            
            # Crear datos de demostración
            create_sample_data()
                
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")

def create_sample_data():
    """Crear datos de demostración si no existen reservas"""
    try:
        from reservations.models import Reservation
        from datetime import date, timedelta
        
        if Reservation.objects.count() == 0:
            # Crear algunas reservas de ejemplo
            Reservation.objects.create(
                status='OK',
                agency='BEDBANKGLOBAL',
                booking_code='DEMO001',
                clients_names='Juan Pérez y familia',
                hotel='MELIA PENINSULA',
                date_from=date.today() + timedelta(days=7),
                date_to=date.today() + timedelta(days=10),
                hotel_confirmation='MP12345',
                pax=3,
                room_type='TRIPLE',
                sale_price=450.00,
                touch_cost=380.00,
                valid_rates='ADVANCED OFFER 1 CONTRATO',
                nationality='USA',
                remarks='Cliente frecuente - solicita vista al mar'
            )
            
            Reservation.objects.create(
                status='PENDING',
                agency='TOUROPERATOR',
                booking_code='DEMO002', 
                clients_names='María García',
                hotel='HOTEL EJEMPLO',
                date_from=date.today() + timedelta(days=14),
                date_to=date.today() + timedelta(days=16),
                pax=2,
                room_type='DOBLE',
                sale_price=280.00,
                touch_cost=220.00,
                nationality='ESP',
                remarks='Por confirmar método de pago'
            )
            
            print("✅ Datos de demostración creados")
            
    except Exception as e:
        print(f"⚠️  No se pudieron crear datos demo: {e}")

def open_browser():
    """Abre el navegador automáticamente después de 4 segundos"""
    sleep(4)
    try:
        webbrowser.open('http://127.0.0.1:9000')
        print("🌐 Navegador abierto automáticamente")
    except Exception as e:
        print(f"⚠️  No se pudo abrir el navegador: {e}")
        print("📍 Accede manualmente a: http://127.0.0.1:9000")

def run_server():
    """Ejecuta el servidor Django"""
    try:
        from django.core.management import execute_from_command_line
        
        print("🚀 Iniciando servidor Django...")
        print("📍 URL: http://127.0.0.1:9000")
        print("👤 Usuario: admin")
        print("🔑 Contraseña: maXS@sdasd1234")
        print("⏹️  Presiona CTRL+C para detener el servidor")
        print("=" * 50)
        
        # Ejecutar servidor en puerto 9000
        execute_from_command_line(['manage.py', 'runserver', '--noreload', '127.0.0.1:9000'])
        
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido")
        print("¡Gracias por usar el Sistema de Reservas!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Si el problema persiste, reinicia la aplicación")
        input("Presiona Enter para salir...")

if __name__ == '__main__':
    print("=" * 50)
    print("    SISTEMA DE RESERVAS HOTELERAS")
    print("    Versión Portable - Build Final")
    print("=" * 50)
    print("⚡ Inicializando aplicación...")
    
    # Configurar entorno
    setup_environment()
    
    # Inicializar base de datos
    init_database()
    
    # Iniciar navegador en hilo separado
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Ejecutar servidor
    run_server()