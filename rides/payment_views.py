from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Booking
from .payment_models import PaymentTransaction
from django.core.mail import send_mail
from django.conf import settings

@login_required
def initiate_payment(request, booking_id):
    """Initie le processus de paiement pour une réservation"""
    booking = get_object_or_404(Booking, id=booking_id, passenger=request.user)
    
    if booking.status != 'confirmed':
        messages.error(request, 'Cette réservation ne peut pas être payée actuellement.')
        return redirect('rides:ride_detail', pk=booking.ride.id)
    
    # Créer ou récupérer la transaction
    payment, created = PaymentTransaction.objects.get_or_create(
        booking=booking,
        defaults={
            'amount': booking.ride.price * booking.number_of_seats
        }
    )
    
    if created or payment.status == 'pending':
        # Générer un nouveau code de validation
        validation_code = payment.generate_validation_code()
        
        # Envoyer le code par email au passager
        send_mail(
            'Code de validation pour votre trajet',
            f'Votre code de validation pour le trajet {booking.ride.departure_city} → {booking.ride.arrival_city} est : {validation_code}\n'
            f'Montant à payer : {payment.amount} DH\n'
            'Veuillez communiquer ce code au conducteur uniquement après le trajet.',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=True,
        )
        
        messages.success(request, 'Un code de validation vous a été envoyé par email. Veuillez procéder au paiement.')
    
    return render(request, 'rides/payment.html', {
        'booking': booking,
        'payment': payment
    })

@login_required
def validate_payment(request, booking_id):
    """Valide le paiement avec le code fourni par le passager"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Vérifier que l'utilisateur est le conducteur
    if request.user != booking.ride.driver:
        messages.error(request, 'Vous n\'êtes pas autorisé à valider ce paiement.')
        return redirect('rides:ride_detail', pk=booking.ride.id)
    
    if request.method == 'POST':
        code = request.POST.get('validation_code')
        payment = get_object_or_404(PaymentTransaction, booking=booking)
        
        if payment.validate_payment(code):
            messages.success(request, 'Paiement validé avec succès ! L\'argent sera transféré sur votre compte.')
            
            # Envoyer un email de confirmation au conducteur
            send_mail(
                'Paiement validé',
                f'Le paiement pour le trajet {booking.ride.departure_city} → {booking.ride.arrival_city} a été validé.\n'
                f'Montant : {payment.amount * 0.8} DH (80% du total)',
                settings.DEFAULT_FROM_EMAIL,
                [booking.ride.driver.email],
                fail_silently=True,
            )
        else:
            messages.error(request, 'Code de validation incorrect.')
        
        return redirect('rides:ride_detail', pk=booking.ride.id)
    
    return render(request, 'rides/validate_payment.html', {
        'booking': booking
    }) 