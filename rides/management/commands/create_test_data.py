from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from rides.models import Ride
from datetime import timedelta, time

class Command(BaseCommand):
    help = 'Crée des données de test pour l\'application'

    def handle(self, *args, **options):
        try:
            # Création d'un conducteur de test
            conducteur = User.objects.create_user(
                username='conducteur_test',
                email='conducteur@test.com',
                password='Test123!',
                first_name='Jean',
                last_name='Dupont'
            )
            self.stdout.write(self.style.SUCCESS('Utilisateur conducteur_test créé avec succès'))
            
            # Ajout au groupe Conducteurs
            conducteurs_group = Group.objects.get(name='Conducteurs')
            conducteur.groups.add(conducteurs_group)

            # Création d'un passager de test
            passager = User.objects.create_user(
                username='passager_test',
                email='passager@test.com',
                password='Test123!',
                first_name='Marie',
                last_name='Martin'
            )
            self.stdout.write(self.style.SUCCESS('Utilisateur passager_test créé avec succès'))
            
            # Ajout au groupe Passagers
            passagers_group = Group.objects.get(name='Passagers')
            passager.groups.add(passagers_group)
            
            # Création de trajets de test
            trajets = [
                {
                    'departure_city': 'Paris',
                    'arrival_city': 'Lyon',
                    'departure_address': '1 Place de la République, Paris',
                    'arrival_address': '10 Place Bellecour, Lyon',
                    'departure_date': timezone.now().date() + timedelta(days=1),
                    'departure_time': time(8, 0),  # 8h00
                    'price_per_seat': 35.00,
                    'available_seats': 3,
                    'vehicle_description': 'Peugeot 308 grise',
                },
                {
                    'departure_city': 'Lyon',
                    'arrival_city': 'Marseille',
                    'departure_address': '10 Place Bellecour, Lyon',
                    'arrival_address': '1 Quai du Port, Marseille',
                    'departure_date': timezone.now().date() + timedelta(days=2),
                    'departure_time': time(14, 30),  # 14h30
                    'price_per_seat': 30.00,
                    'available_seats': 4,
                    'vehicle_description': 'Peugeot 308 grise',
                },
                {
                    'departure_city': 'Marseille',
                    'arrival_city': 'Nice',
                    'departure_address': '1 Quai du Port, Marseille',
                    'arrival_address': '1 Place Masséna, Nice',
                    'departure_date': timezone.now().date() + timedelta(days=3),
                    'departure_time': time(10, 0),  # 10h00
                    'price_per_seat': 25.00,
                    'available_seats': 3,
                    'vehicle_description': 'Peugeot 308 grise',
                }
            ]

            for trajet in trajets:
                ride = Ride.objects.create(
                    driver=conducteur,
                    status='confirmed',
                    **trajet
                )
                self.stdout.write(self.style.SUCCESS(
                    f'Trajet créé : {ride.departure_city} → {ride.arrival_city}'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur : {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('''
Données de test créées avec succès !

Compte conducteur :
Username: conducteur_test
Password: Test123!

Compte passager :
Username: passager_test
Password: Test123!
''')) 