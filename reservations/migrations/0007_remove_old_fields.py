from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('reservations', '0006_migrate_old_room_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reservation',
            name='pax_ad',
        ),
        migrations.RemoveField(
            model_name='reservation',
            name='pax_chd',
        ),
        migrations.RemoveField(
            model_name='reservation',
            name='room_type',
        ),
    ]