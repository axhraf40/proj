from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rides.models import Ride, RideRequest

class Command(BaseCommand):
    help = 'Crée les groupes de base et configure leurs permissions'

    def handle(self, *args, **options):
        # Création du groupe Conducteurs
        conducteurs_group, created = Group.objects.get_or_create(name='Conducteurs')
        if created:
            self.stdout.write(self.style.SUCCESS('Groupe Conducteurs créé avec succès'))
        
        # Création du groupe Passagers
        passagers_group, created = Group.objects.get_or_create(name='Passagers')
        if created:
            self.stdout.write(self.style.SUCCESS('Groupe Passagers créé avec succès'))

        # Obtenir les content types
        ride_content_type = ContentType.objects.get_for_model(Ride)
        ride_request_content_type = ContentType.objects.get_for_model(RideRequest)

        # Permissions pour les Conducteurs
        conducteur_permissions = [
            Permission.objects.get_or_create(
                codename='add_ride',
                name='Can add ride',
                content_type=ride_content_type,
            )[0],
            Permission.objects.get_or_create(
                codename='change_ride',
                name='Can change ride',
                content_type=ride_content_type,
            )[0],
            Permission.objects.get_or_create(
                codename='delete_ride',
                name='Can delete ride',
                content_type=ride_content_type,
            )[0],
            Permission.objects.get_or_create(
                codename='view_ride',
                name='Can view ride',
                content_type=ride_content_type,
            )[0],
            Permission.objects.get_or_create(
                codename='can_accept_request',
                name='Can accept ride request',
                content_type=ride_request_content_type,
            )[0],
        ]
        conducteurs_group.permissions.set(conducteur_permissions)

        # Permissions pour les Passagers
        passager_permissions = [
            Permission.objects.get_or_create(
                codename='add_riderequest',
                name='Can add ride request',
                content_type=ride_request_content_type,
            )[0],
            Permission.objects.get_or_create(
                codename='view_ride',
                name='Can view ride',
                content_type=ride_content_type,
            )[0],
            Permission.objects.get_or_create(
                codename='view_riderequest',
                name='Can view ride request',
                content_type=ride_request_content_type,
            )[0],
        ]
        passagers_group.permissions.set(passager_permissions)

        self.stdout.write(self.style.SUCCESS('Permissions configurées avec succès')) 