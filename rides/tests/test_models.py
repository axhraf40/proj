from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from ..models import Ride, RideRequest

User = get_user_model()

class RideModelTests(TestCase):
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

    def test_ride_creation(self):
        """Test la création d'un trajet"""
        self.assertEqual(self.ride.driver.username, 'testuser')
        self.assertEqual(self.ride.departure_city, 'Paris')
        self.assertEqual(self.ride.arrival_city, 'Lyon')
        self.assertEqual(self.ride.available_seats, 4)
        self.assertEqual(self.ride.status, 'confirmed')

    def test_ride_str_representation(self):
        """Test la représentation string d'un trajet"""
        expected = f"Paris → Lyon le {self.tomorrow}"
        self.assertEqual(str(self.ride), expected)

    def test_ride_is_full(self):
        """Test la méthode is_full"""
        self.assertFalse(self.ride.is_full())
        self.ride.available_seats = 0
        self.ride.save()
        self.assertTrue(self.ride.is_full())

    def test_ride_is_past(self):
        """Test si un trajet est passé"""
        self.assertFalse(self.ride.is_past())
        self.ride.departure_date = timezone.now().date() - timedelta(days=1)
        self.ride.save()
        self.assertTrue(self.ride.is_past())

class RideRequestModelTests(TestCase):
    def setUp(self):
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
        self.request = RideRequest.objects.create(
            ride=self.ride,
            passenger=self.passenger,
            seats=2,
            status='pending'
        )

    def test_request_creation(self):
        """Test la création d'une demande de réservation"""
        self.assertEqual(self.request.ride, self.ride)
        self.assertEqual(self.request.passenger, self.passenger)
        self.assertEqual(self.request.seats, 2)
        self.assertEqual(self.request.status, 'pending')

    def test_request_str_representation(self):
        """Test la représentation string d'une demande"""
        expected = f"Demande de passenger pour Paris → Lyon"
        self.assertEqual(str(self.request), expected)

    def test_accept_request(self):
        """Test l'acceptation d'une demande"""
        initial_seats = self.ride.available_seats
        self.request.accept()
        self.request.refresh_from_db()
        self.ride.refresh_from_db()
        
        self.assertEqual(self.request.status, 'accepted')
        self.assertEqual(self.ride.available_seats, initial_seats - self.request.seats)

    def test_reject_request(self):
        """Test le refus d'une demande"""
        initial_seats = self.ride.available_seats
        self.request.reject()
        self.request.refresh_from_db()
        self.ride.refresh_from_db()
        
        self.assertEqual(self.request.status, 'rejected')
        self.assertEqual(self.ride.available_seats, initial_seats)  # Les places ne doivent pas changer

    def test_cannot_request_own_ride(self):
        """Test qu'un conducteur ne peut pas réserver son propre trajet"""
        with self.assertRaises(ValueError):
            RideRequest.objects.create(
                ride=self.ride,
                passenger=self.driver,
                seats=1,
                status='pending'
            )

    def test_cannot_request_more_than_available_seats(self):
        """Test qu'on ne peut pas demander plus de places que disponibles"""
        with self.assertRaises(ValueError):
            RideRequest.objects.create(
                ride=self.ride,
                passenger=self.passenger,
                seats=self.ride.available_seats + 1,
                status='pending'
            ) 