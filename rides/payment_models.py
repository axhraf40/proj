from django.db import models
from django.contrib.auth.models import User
from .models import Booking
import random
import string

class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente de paiement'),
        ('paid', 'Payé'),
        ('validated', 'Validé'),
        ('refunded', 'Remboursé'),
        ('cancelled', 'Annulé'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    validation_code = models.CharField(max_length=6, blank=True, null=True)
    
    def generate_validation_code(self):
        """Génère un code de validation à 6 chiffres"""
        code = ''.join(random.choices(string.digits, k=6))
        self.validation_code = code
        self.save()
        return code

    def validate_payment(self, code):
        """Valide le paiement avec le code fourni"""
        if self.validation_code == code:
            self.status = 'validated'
            self.save()
            
            # Mettre à jour le statut de la réservation
            self.booking.status = 'completed'
            self.booking.save()
            
            # Calculer la répartition du paiement (80% conducteur, 20% plateforme)
            driver_amount = self.amount * 0.8
            platform_amount = self.amount * 0.2
            
            # Créer les transactions pour le conducteur et la plateforme
            DriverTransaction.objects.create(
                payment=self,
                user=self.booking.ride.driver,
                amount=driver_amount
            )
            
            PlatformTransaction.objects.create(
                payment=self,
                amount=platform_amount
            )
            
            return True
        return False

class DriverTransaction(models.Model):
    """Transactions pour les paiements aux conducteurs"""
    payment = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

class PlatformTransaction(models.Model):
    """Transactions pour les commissions de la plateforme"""
    payment = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True) 