from django.db import migrations

def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    groups = ['Passagers', 'Conducteurs', 'Administrateurs']
    for group_name in groups:
        Group.objects.get_or_create(name=group_name)

def delete_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    groups = ['Passagers', 'Conducteurs', 'Administrateurs']
    Group.objects.filter(name__in=groups).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('rides', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups, delete_groups),
    ] 