from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

def add_permissions_to_drivers(apps, schema_editor):
    # Obtenir le groupe Conducteurs
    drivers_group = Group.objects.get(name='Conducteurs')
    
    # Obtenir les permissions pour les modèles nécessaires
    ride_permissions = Permission.objects.filter(content_type__app_label='rides', 
                                              content_type__model__in=['ride', 'vehicle'])
    
    # Ajouter toutes les permissions au groupe
    for permission in ride_permissions:
        drivers_group.permissions.add(permission)

def remove_permissions_from_drivers(apps, schema_editor):
    # Obtenir le groupe Conducteurs
    drivers_group = Group.objects.get(name='Conducteurs')
    
    # Supprimer toutes les permissions
    drivers_group.permissions.clear()

class Migration(migrations.Migration):
    dependencies = [
        ('rides', '0008_merge_20250524_1707'),
    ]

    operations = [
        migrations.RunPython(add_permissions_to_drivers, remove_permissions_from_drivers),
    ] 