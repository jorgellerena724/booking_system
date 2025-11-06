from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('reservations', '0004_alter_reservation_pax_ad_alter_reservation_pax_chd'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_type', models.CharField(max_length=100, verbose_name='Tipo de Habitación')),
                ('pax_ad', models.IntegerField(default=1, help_text='Número de adultos en esta habitación', verbose_name='PAX Adultos')),
                ('pax_chd', models.IntegerField(default=0, help_text='Número de niños en esta habitación', verbose_name='PAX Niños')),
                ('reservation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rooms', to='reservations.Reservation')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]