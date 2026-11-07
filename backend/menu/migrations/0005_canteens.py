from django.db import migrations, models

CANTEENS = [(1, 'Столовая, 1 этаж'), (5, 'Столовая, 5 этаж'), (6, 'Столовая, 6 этаж')]


def create_canteens(apps, schema_editor):
    """The college canteens; the dishes that already exist are served in all of them."""
    Canteen = apps.get_model('menu', 'Canteen')
    Dish = apps.get_model('menu', 'Dish')
    canteens = [Canteen.objects.get_or_create(floor=floor, defaults={'name': name})[0] for floor, name in CANTEENS]
    for dish in Dish.objects.all():
        dish.canteens.add(*canteens)


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0004_dish_search_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Canteen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('floor', models.PositiveSmallIntegerField(unique=True, verbose_name='этаж')),
                ('name', models.CharField(max_length=100, verbose_name='название')),
            ],
            options={
                'verbose_name': 'столовая',
                'verbose_name_plural': 'столовые',
                'ordering': ['floor'],
            },
        ),
        migrations.AddField(
            model_name='dish',
            name='canteens',
            field=models.ManyToManyField(
                blank=True,
                help_text='В каких столовых подают блюдо: заказать его можно только с получением там.',
                related_name='dishes',
                to='menu.canteen',
                verbose_name='где есть',
            ),
        ),
        migrations.RunPython(create_canteens, migrations.RunPython.noop),
    ]
