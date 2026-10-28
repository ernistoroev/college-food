from django.db import migrations

STAFF_GROUP = 'Сотрудники столовой'


def create_staff_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name=STAFF_GROUP)


def delete_staff_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=STAFF_GROUP).delete()


class Migration(migrations.Migration):
    """Creates the «Сотрудники столовой» group, so it exists on every computer after migrate."""

    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_staff_group, delete_staff_group),
    ]
