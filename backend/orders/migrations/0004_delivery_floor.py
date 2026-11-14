import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0006_delivery_floors'),
        ('orders', '0003_order_canteen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='canteen',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='menu.canteen', verbose_name='этаж доставки'),
        ),
        migrations.AlterField(
            model_name='order',
            name='pickup_time',
            field=models.CharField(choices=[('12:20', '12:20'), ('12:40', '12:40'), ('13:00', '13:00'), ('13:20', '13:20'), ('13:40', '13:40'), ('14:00', '14:00')], max_length=5, verbose_name='время доставки'),
        ),
    ]
