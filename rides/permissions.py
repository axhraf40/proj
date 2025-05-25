from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Ride, Booking, Vehicle, Rating

def setup_groups_and_permissions():
    # Création des groupes
    conducteur_group, _ = Group.objects.get_or_create(name='Conducteurs')
    passager_group, _ = Group.objects.get_or_create(name='Passagers')

    # Permissions pour les conducteurs
    conducteur_permissions = [
        # Gestion des trajets
        ('add_ride', 'Can add ride'),
        ('change_ride', 'Can change ride'),
        ('delete_ride', 'Can delete ride'),
        ('view_ride', 'Can view ride'),
        # Gestion des véhicules
        ('add_vehicle', 'Can add vehicle'),
        ('change_vehicle', 'Can change vehicle'),
        ('delete_vehicle', 'Can delete vehicle'),
        ('view_vehicle', 'Can view vehicle'),
        # Gestion des réservations
        ('view_booking', 'Can view booking'),
        ('change_booking', 'Can change booking'),  # Pour accepter/refuser les réservations
        # Notation
        ('add_rating', 'Can add rating'),
        ('view_rating', 'Can view rating'),
    ]

    # Permissions pour les passagers
    passager_permissions = [
        # Consultation des trajets
        ('view_ride', 'Can view ride'),
        # Gestion des réservations
        ('add_booking', 'Can add booking'),
        ('change_booking', 'Can change booking'),  # Pour annuler leurs réservations
        ('view_booking', 'Can view booking'),
        # Notation
        ('add_rating', 'Can add rating'),
        ('view_rating', 'Can view rating'),
    ]

    # Attribution des permissions aux groupes
    for codename, name in conducteur_permissions:
        for model in [Ride, Booking, Vehicle, Rating]:
            content_type = ContentType.objects.get_for_model(model)
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type,
            )
            conducteur_group.permissions.add(permission)

    for codename, name in passager_permissions:
        for model in [Ride, Booking, Rating]:
            content_type = ContentType.objects.get_for_model(model)
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type,
            )
            passager_group.permissions.add(permission) 