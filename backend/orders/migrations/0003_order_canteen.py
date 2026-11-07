import django.db.models.deletion
from django.db import migrations, models


def set_first_floor(apps, schema_editor):
    """Orders made before the canteens appeared are counted as the 1st floor canteen."""
    Canteen = apps.get_model('menu', 'Canteen')
    Order = apps.get_model('orders', 'Order')
    first_floor = Canteen.objects.get(floor=1)
    Order.objects.update(canteen=first_floor)


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0005_canteens'),
        ('orders', '0002_statuses_comment_messages'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='canteen',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='orders',
                to='menu.canteen',
                verbose_name='столовая',
            ),
        ),
        migrations.RunPython(set_first_floor, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='canteen',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='orders',
                to='menu.canteen',
                verbose_name='столовая',
            ),
        ),
    ]
