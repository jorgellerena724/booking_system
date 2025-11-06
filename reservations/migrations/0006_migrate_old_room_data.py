from django.db import migrations

def migrate_old_room_data(apps, schema_editor):
    Reservation = apps.get_model('reservations', 'Reservation')
    Room = apps.get_model('reservations', 'Room')
    
    print("\n=== Iniciando migración de datos de habitaciones ===")
    
    total_reservations = Reservation.objects.count()
    migrated_count = 0
    
    for reservation in Reservation.objects.all():
        # Verificar si los campos antiguos existen y tienen datos
        room_type = getattr(reservation, 'room_type', None)
        pax_ad = getattr(reservation, 'pax_ad', None)
        pax_chd = getattr(reservation, 'pax_chd', None)
        
        # Usar valores por defecto si son None
        if pax_ad is None:
            pax_ad = 1
        if pax_chd is None:
            pax_chd = 0
        if not room_type:
            room_type = "Habitación Standard"
        
        # Crear registro en Room
        Room.objects.create(
            reservation=reservation,
            room_type=room_type,
            pax_ad=pax_ad,
            pax_chd=pax_chd
        )
        migrated_count += 1
        print(f"✓ Migrada habitación para: {reservation.booking_code} -> {room_type} (AD:{pax_ad}, CHD:{pax_chd})")
    
    print(f"\n=== Migración completada ===")
    print(f"Reservas procesadas: {migrated_count}/{total_reservations}")
    print(f"Habitaciones creadas: {migrated_count}")

def reverse_migrate(apps, schema_editor):
    Room = apps.get_model('reservations', 'Room')
    room_count = Room.objects.count()
    Room.objects.all().delete()
    print(f"← Reversión: {room_count} habitaciones eliminadas")

class Migration(migrations.Migration):
    dependencies = [
        ('reservations', '0005_add_room_model'),
    ]

    operations = [
        migrations.RunPython(migrate_old_room_data, reverse_migrate),
    ]