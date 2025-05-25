from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from ..models import Ride
from ..forms import RideForm, RideRequestForm

User = get_user_model()

class RideFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        self.valid_data = {
            'departure_city': 'Paris',
            'arrival_city': 'Lyon',
            'departure_date': self.tomorrow,
            'departure_time': '10:00',
            'price_per_seat': 25,
            'available_seats': 4,
            'description': 'Test ride'
        }

    def test_valid_form(self):
        """Test que le formulaire est valide avec des données correctes"""
        form = RideForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_invalid_dates(self):
        """Test que le formulaire est invalide avec une date passée"""
        yesterday = timezone.now().date() - timedelta(days=1)
        data = self.valid_data.copy()
        data['departure_date'] = yesterday
        
        form = RideForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('departure_date', form.errors)

    def test_invalid_seats(self):
        """Test que le formulaire est invalide avec un nombre de places incorrect"""
        data = self.valid_data.copy()
        data['available_seats'] = 0
        
        form = RideForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('available_seats', form.errors)
        
        data['available_seats'] = 9
        form = RideForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('available_seats', form.errors)

    def test_invalid_price(self):
        """Test que le formulaire est invalide avec un prix incorrect"""
        data = self.valid_data.copy()
        data['price_per_seat'] = -1
        
        form = RideForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('price_per_seat', form.errors)

    def test_same_cities(self):
        """Test que le formulaire est invalide avec la même ville de départ et d'arrivée"""
        data = self.valid_data.copy()
        data['departure_city'] = 'Paris'
        data['arrival_city'] = 'Paris'
        
        form = RideForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('arrival_city', form.errors)

class RideRequestFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
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

    def test_valid_request(self):
        """Test que le formulaire est valide avec des données correctes"""
        form = RideRequestForm(data={'seats': 2}, ride=self.ride)
        self.assertTrue(form.is_valid())

    def test_too_many_seats(self):
        """Test que le formulaire est invalide avec trop de places demandées"""
        form = RideRequestForm(data={'seats': 5}, ride=self.ride)
        self.assertFalse(form.is_valid())
        self.assertIn('seats', form.errors)

    def test_zero_seats(self):
        """Test que le formulaire est invalide avec zéro place"""
        form = RideRequestForm(data={'seats': 0}, ride=self.ride)
        self.assertFalse(form.is_valid())
        self.assertIn('seats', form.errors)

    def test_negative_seats(self):
        """Test que le formulaire est invalide avec un nombre négatif de places"""
        form = RideRequestForm(data={'seats': -1}, ride=self.ride)
        self.assertFalse(form.is_valid())
        self.assertIn('seats', form.errors)

    def test_full_ride(self):
        """Test que le formulaire est invalide quand le trajet est complet"""
        self.ride.available_seats = 0
        self.ride.save()
        
        form = RideRequestForm(data={'seats': 1}, ride=self.ride)
        self.assertFalse(form.is_valid())
        self.assertIn('seats', form.errors) 