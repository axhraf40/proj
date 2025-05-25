from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from ..models import Ride, RideRequest

User = get_user_model()

class RideViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        self.ride = Ride.objects.create(
            driver=self.user,
            departure_city='Paris',
            arrival_city='Lyon',
            departure_date=self.tomorrow,
            departure_time='10:00',
            price_per_seat=25,
            available_seats=4,
            status='confirmed'
        )

    def test_ride_list_view(self):
        """Test la vue de liste des trajets"""
        response = self.client.get(reverse('rides:ride_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rides/ride_list.html')
        self.assertContains(response, 'Paris')
        self.assertContains(response, 'Lyon')

    def test_ride_list_search(self):
        """Test la recherche dans la liste des trajets"""
        response = self.client.get(reverse('rides:ride_list'), {'q': 'Paris'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Paris')
        
        response = self.client.get(reverse('rides:ride_list'), {'q': 'NonExistent'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Paris')

    def test_ride_detail_view(self):
        """Test la vue de détail d'un trajet"""
        response = self.client.get(reverse('rides:ride_detail', args=[self.ride.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rides/ride_detail.html')
        self.assertContains(response, 'Paris')
        self.assertContains(response, 'Lyon')

    def test_ride_create_view(self):
        """Test la création d'un trajet"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test GET
        response = self.client.get(reverse('rides:ride_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rides/ride_form.html')
        
        # Test POST
        ride_data = {
            'departure_city': 'Marseille',
            'arrival_city': 'Nice',
            'departure_date': self.tomorrow,
            'departure_time': '14:00',
            'price_per_seat': 20,
            'available_seats': 3,
            'description': 'Test ride'
        }
        response = self.client.post(reverse('rides:ride_create'), ride_data)
        self.assertEqual(response.status_code, 302)  # Redirection après création
        self.assertTrue(Ride.objects.filter(departure_city='Marseille').exists())

    def test_ride_edit_view(self):
        """Test la modification d'un trajet"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test GET
        response = self.client.get(reverse('rides:ride_edit', args=[self.ride.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rides/ride_form.html')
        
        # Test POST
        edit_data = {
            'departure_city': 'Paris',
            'arrival_city': 'Marseille',  # Changed
            'departure_date': self.tomorrow,
            'departure_time': '10:00',
            'price_per_seat': 30,  # Changed
            'available_seats': 4,
            'description': 'Updated ride'
        }
        response = self.client.post(reverse('rides:ride_edit', args=[self.ride.pk]), edit_data)
        self.assertEqual(response.status_code, 302)
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.arrival_city, 'Marseille')
        self.assertEqual(self.ride.price_per_seat, 30)

    def test_ride_delete_view(self):
        """Test la suppression d'un trajet"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('rides:ride_delete', args=[self.ride.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Ride.objects.filter(pk=self.ride.pk).exists())

    def test_unauthorized_ride_edit(self):
        """Test qu'un utilisateur ne peut pas modifier le trajet d'un autre"""
        self.client.login(username='otheruser', password='otherpass123')
        
        response = self.client.get(reverse('rides:ride_edit', args=[self.ride.pk]))
        self.assertEqual(response.status_code, 302)  # Redirection
        
        edit_data = {
            'departure_city': 'Changed',
            'arrival_city': 'Changed',
            'departure_date': self.tomorrow,
            'departure_time': '10:00',
            'price_per_seat': 25,
            'available_seats': 4
        }
        response = self.client.post(reverse('rides:ride_edit', args=[self.ride.pk]), edit_data)
        self.assertEqual(response.status_code, 302)
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.departure_city, 'Paris')  # Unchanged

class RideRequestViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.driver = User.objects.create_user(
            username='driver',
            email='driver@example.com',
            password='driverpass123'
        )
        self.passenger = User.objects.create_user(
            username='passenger',
            email='passenger@example.com',
            password='passengerpass123'
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        self.ride = Ride.objects.create(
            driver=self.driver,
            departure_city='Paris',
            arrival_city='Lyon',
            departure_date=self.tomorrow,
            departure_time='10:00',
            price_per_seat=25,
            available_seats=4,
            status='confirmed'
        )

    def test_create_request(self):
        """Test la création d'une demande de réservation"""
        self.client.login(username='passenger', password='passengerpass123')
        
        response = self.client.post(reverse('rides:ride_detail', args=[self.ride.pk]), {
            'seats': 2
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(RideRequest.objects.filter(
            ride=self.ride,
            passenger=self.passenger,
            seats=2
        ).exists())

    def test_accept_request(self):
        """Test l'acceptation d'une demande"""
        request = RideRequest.objects.create(
            ride=self.ride,
            passenger=self.passenger,
            seats=2,
            status='pending'
        )
        self.client.login(username='driver', password='driverpass123')
        
        response = self.client.post(reverse('rides:request_action', args=[request.pk, 'accept']))
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, 'accepted')
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.available_seats, 2)

    def test_reject_request(self):
        """Test le refus d'une demande"""
        request = RideRequest.objects.create(
            ride=self.ride,
            passenger=self.passenger,
            seats=2,
            status='pending'
        )
        self.client.login(username='driver', password='driverpass123')
        
        response = self.client.post(reverse('rides:request_action', args=[request.pk, 'reject']))
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, 'rejected')
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.available_seats, 4)  # Unchanged

    def test_my_rides_view(self):
        """Test la vue des trajets personnels"""
        self.client.login(username='passenger', password='passengerpass123')
        
        # Créer une demande acceptée
        RideRequest.objects.create(
            ride=self.ride,
            passenger=self.passenger,
            seats=2,
            status='accepted'
        )
        
        response = self.client.get(reverse('rides:my_rides'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rides/my_rides.html')
        self.assertContains(response, 'Paris')
        self.assertContains(response, 'Lyon') 