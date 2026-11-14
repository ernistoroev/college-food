from django.db import migrations, models


def rename_to_floors(apps, schema_editor):
    """«Столовая, 5 этаж» → «5 этаж»: the student picks the floor the order is delivered to."""
    Canteen = apps.get_model('menu', 'Canteen')
    for canteen in Canteen.objects.all():
        if canteen.name == f'Столовая, {canteen.floor} этаж':
            canteen.name = f'{canteen.floor} этаж'
            canteen.save(update_fields=['name'])


def rename_back(apps, schema_editor):
    Canteen = apps.get_model('menu', 'Canteen')
    for canteen in Canteen.objects.all():
        if canteen.name == f'{canteen.floor} этаж':
            canteen.name = f'Столовая, {canteen.floor} этаж'
            canteen.save(update_fields=['name'])


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0005_canteens'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='canteen',
            options={'ordering': ['floor'], 'verbose_name': 'этаж доставки', 'verbose_name_plural': 'этажи доставки'},
        ),
        migrations.AlterField(
            model_name='dish',
            name='canteens',
            field=models.ManyToManyField(blank=True, help_text='На какие этажи доставляют блюдо: заказать его можно только с доставкой туда.', related_name='dishes', to='menu.canteen', verbose_name='этажи доставки'),
        ),
        migrations.RunPython(rename_to_floors, rename_back),
    ]
