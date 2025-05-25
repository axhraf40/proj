from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.auth import login
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.utils import timezone
from .models import Ride, RideRequest, Booking, Vehicle, Rating, Profile, EmailVerificationToken, PricingSettings, RideReport
from .forms import RideForm, RideRequestForm, SignUpForm, BookingForm, VehicleForm, RatingForm, ProfileForm, RideReportForm
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.db import models
from .services import calculate_distance
from decimal import Decimal, ROUND_UP
from django.db.utils import IntegrityError
from .cities import MOROCCAN_CITIES, get_distance, calculate_price

def ride_list(request):
    rides = Ride.objects.filter(
        departure_date__gte=timezone.now().date(),
        status='confirmed'
    ).select_related('driver').order_by('departure_date', 'departure_time')
    
    # Recherche
    query = request.GET.get('q')
    if query:
        rides = rides.filter(
            Q(departure_city__icontains=query) |
            Q(arrival_city__icontains=query)
        )

    # Filtres
    departure_city = request.GET.get('departure')
    arrival_city = request.GET.get('arrival')
    date_filter = request.GET.get('date')

    if departure_city:
        rides = rides.filter(departure_city__icontains=departure_city)
    if arrival_city:
        rides = rides.filter(arrival_city__icontains=arrival_city)
    if date_filter:
        rides = rides.filter(departure_date=date_filter)

    # Pagination
    paginator = Paginator(rides, 10)
    page = request.GET.get('page')
    rides = paginator.get_page(page)

    return render(request, 'rides/ride_list.html', {
        'rides': rides,
        'query': query,
        'departure_city': departure_city,
        'arrival_city': arrival_city,
        'date_filter': date_filter
    })

@login_required
def dashboard(request):
    """Tableau de bord personnalisé selon le rôle de l'utilisateur"""
    context = {
        'is_driver': request.user.groups.filter(name='Conducteurs').exists()
    }
    
    if context['is_driver']:
        context.update({
            'upcoming_rides': Ride.objects.filter(
                driver=request.user,
                status='scheduled'
            ).order_by('departure_date', 'departure_time')[:5],
            'pending_requests': Booking.objects.filter(
                ride__driver=request.user,
                status='pending'
            ).select_related('ride', 'passenger')
        })
    else:
        context.update({
            'my_bookings': Booking.objects.filter(
                passenger=request.user
            ).select_related('ride').order_by('ride__departure_date')[:5]
        })
    
    return render(request, 'rides/dashboard.html', context)

@login_required
def ride_search(request):
    """Recherche de trajets disponibles"""
    departure = request.GET.get('departure', '')
    arrival = request.GET.get('arrival', '')
    date = request.GET.get('date')

    rides = Ride.objects.filter(status='scheduled')
    
    if departure:
        rides = rides.filter(departure_city__icontains=departure)
    if arrival:
        rides = rides.filter(arrival_city__icontains=arrival)
    if date:
        rides = rides.filter(departure_date=date)

    context = {
        'rides': rides,
        'departure': departure,
        'arrival': arrival,
        'date': date
    }
    return render(request, 'rides/ride_list.html', context)

@login_required
@permission_required('rides.add_ride', raise_exception=True)
def ride_create(request):
    """Création d'un nouveau trajet (conducteurs uniquement)"""
    # Vérifier si l'utilisateur est un conducteur
    if not request.user.groups.filter(name='Conducteurs').exists():
        messages.error(request, 'Seuls les conducteurs peuvent créer des trajets.')
        return redirect('rides:ride_list')
        
    if request.method == 'POST':
        form = RideForm(request.POST)
        if form.is_valid():
            ride = form.save(commit=False)
            ride.driver = request.user
            
            # Calculer la distance et le prix
            distance = get_distance(ride.departure_city, ride.arrival_city)
            if distance:
                ride.distance_km = distance
                ride.price = calculate_price(distance)
                ride.driver_profit = round(ride.price * 0.8, 2)  # 80% pour le conducteur
                ride.admin_profit = round(ride.price * 0.2, 2)   # 20% pour la plateforme
                ride.save()
                messages.success(request, 'Votre trajet a été créé avec succès.')
                return redirect('rides:ride_detail', pk=ride.pk)
            else:
                messages.error(request, 'Impossible de calculer la distance entre ces villes. Veuillez vérifier les adresses.')
    else:
        form = RideForm()
    
    return render(request, 'rides/ride_form.html', {'form': form})

@login_required
def ride_edit(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    
    if ride.driver != request.user:
        messages.error(request, 'Vous n\'êtes pas autorisé à modifier ce trajet.')
        return redirect('rides:ride_detail', pk=pk)
    
    if request.method == 'POST':
        form = RideForm(request.POST, instance=ride)
        if form.is_valid():
            form.save()
            messages.success(request, 'Le trajet a été modifié avec succès !')
            return redirect('rides:ride_detail', pk=pk)
    else:
        form = RideForm(instance=ride)
    
    return render(request, 'rides/ride_form.html', {
        'form': form,
        'ride': ride,
        'title': 'Modifier le trajet'
    })

@login_required
def ride_detail(request, pk):
    """Détails d'un trajet avec possibilité de réservation"""
    ride = get_object_or_404(Ride.objects.select_related('driver', 'vehicle'), pk=pk)
    user_booking = None
    
    if request.user != ride.driver:
        user_booking = Booking.objects.filter(
            ride=ride,
            passenger=request.user
        ).first()

    context = {
        'ride': ride,
        'user_booking': user_booking,
        'is_driver': request.user.groups.filter(name='Conducteurs').exists(),
    }
    return render(request, 'rides/ride_detail.html', context)

@login_required
def ride_delete(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    
    if ride.driver != request.user:
        messages.error(request, 'Vous n\'êtes pas autorisé à supprimer ce trajet.')
        return redirect('rides:ride_detail', pk=pk)
    
    if request.method == 'POST':
        ride.delete()
        messages.success(request, 'Le trajet a été supprimé avec succès.')
        return redirect('rides:ride_list')
    
    return render(request, 'rides/ride_confirm_delete.html', {'ride': ride})

@login_required
def request_action(request, pk, action):
    ride_request = get_object_or_404(RideRequest, pk=pk)
    
    # Vérifier que l'utilisateur est bien le conducteur du trajet
    if request.user != ride_request.ride.driver:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à effectuer cette action.")
    
    # Vérifier que la demande est en attente
    if ride_request.status != 'pending':
        messages.error(request, 'Cette demande a déjà été traitée.')
        return redirect('rides:ride_detail', pk=ride_request.ride.pk)
    
    if action == 'accept':
        # Vérifier qu'il y a assez de places disponibles
        if ride_request.ride.available_seats >= ride_request.seats:
            ride_request.status = 'accepted'
            ride_request.ride.available_seats = F('available_seats') - ride_request.seats
            ride_request.ride.save()
            ride_request.save()
            messages.success(request, 'La demande de réservation a été acceptée.')
        else:
            messages.error(request, 'Il n\'y a plus assez de places disponibles.')
    
    elif action == 'reject':
        ride_request.status = 'rejected'
        ride_request.save()
        messages.success(request, 'La demande de réservation a été refusée.')
    
    return redirect('rides:ride_detail', pk=ride_request.ride.pk)

@login_required
def my_rides(request):
    """Vue des trajets personnels avec séparation conducteur/passager"""
    context = {
        'is_driver': request.user.groups.filter(name='Conducteurs').exists()
    }

    if context['is_driver']:
        # Récupérer les véhicules
        context['vehicles'] = Vehicle.objects.filter(driver=request.user)
        
        # Récupérer les trajets en tant que conducteur
        context['rides_as_driver'] = (Ride.objects
            .filter(driver=request.user)
            .select_related('vehicle')
            .prefetch_related('bookings', 'bookings__passenger')
            .order_by('-departure_date', '-departure_time')
        )
        
        # Récupérer les réservations en attente
        context['pending_bookings'] = (Booking.objects
            .filter(
                ride__driver=request.user,
                status='pending'
            )
            .select_related('ride', 'passenger')
            .order_by('ride__departure_date')
        )

    # Récupérer les réservations en tant que passager
    context['bookings'] = (Booking.objects
        .filter(passenger=request.user)
        .select_related('ride', 'ride__driver', 'ride__vehicle')
        .order_by('-ride__departure_date', '-ride__departure_time')
    )

    return render(request, 'rides/my_rides.html', context)

def send_verification_email(user, token):
    """Envoie l'email de vérification à l'utilisateur"""
    subject = 'Vérification de votre compte Covoiturage'
    verification_url = f"{settings.SITE_URL}/verify-email/{token}/"
    
    # Créer le contenu HTML de l'email
    html_message = render_to_string('registration/verification_email.html', {
        'user': user,
        'verification_url': verification_url
    })
    
    # Version texte de l'email
    plain_message = strip_tags(html_message)
    
    # Envoyer l'email
    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [user.email],
        html_message=html_message
    )

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Créer l'utilisateur et l'activer directement
            user = form.save(commit=False)
            user.is_active = True  # Activer directement l'utilisateur
            user.save()
            
            # Assigner l'utilisateur au groupe approprié
            role = form.cleaned_data.get('role')
            if role == 'conducteur':
                group = Group.objects.get(name='Conducteurs')
            else:
                group = Group.objects.get(name='Passagers')
            user.groups.add(group)
            
            # Créer un profil pour l'utilisateur
            Profile.objects.create(user=user, is_verified=True)  # Marquer le profil comme vérifié
            
            messages.success(request, 'Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter.')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

def verify_email(request, token):
    """Vue pour vérifier l'email de l'utilisateur"""
    try:
        verification = EmailVerificationToken.objects.get(token=token)
        
        if verification.is_valid():
            if not verification.is_verified:
                user = verification.user
                user.is_active = True
                user.save()
                
                verification.is_verified = True
                verification.save()
                
                messages.success(request, 'Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter.')
            else:
                messages.info(request, 'Votre compte est déjà vérifié.')
        else:
            messages.error(
                request,
                'Le lien de vérification a expiré. Veuillez vous réinscrire pour recevoir un nouveau lien.'
            )
            
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Le lien de vérification est invalide.')
    
    return redirect('login')

@login_required
def profile_view(request):
    """Affichage et modification du profil utilisateur"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Récupérer tous les trajets passés où l'utilisateur était passager
    past_rides_as_passenger = Ride.objects.filter(
        bookings__passenger=request.user,
        bookings__status='accepted',
        departure_date__lt=timezone.now().date()
    ).select_related('driver').order_by('-departure_date', '-departure_time')

    # Si l'utilisateur est un conducteur, récupérer aussi ses trajets passés
    past_rides_as_driver = []
    if request.user.groups.filter(name='Conducteurs').exists():
        past_rides_as_driver = Ride.objects.filter(
            driver=request.user,
            departure_date__lt=timezone.now().date()
        ).order_by('-departure_date', '-departure_time')

    # Statistiques
    total_rides_as_passenger = past_rides_as_passenger.count()
    total_rides_as_driver = len(past_rides_as_driver)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour.')
            return redirect('rides:profile')
    else:
        form = ProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
        'is_driver': request.user.groups.filter(name='Conducteurs').exists(),
        'past_rides_as_passenger': past_rides_as_passenger,
        'past_rides_as_driver': past_rides_as_driver,
        'total_rides_as_passenger': total_rides_as_passenger,
        'total_rides_as_driver': total_rides_as_driver
    }
    return render(request, 'rides/profile.html', context)

@login_required
def booking_request(request, ride_id):
    """Demande de réservation d'un trajet par un passager"""
    ride = get_object_or_404(Ride, pk=ride_id)
    
    # Vérifier que l'utilisateur n'est pas le conducteur
    if request.user == ride.driver:
        messages.error(request, 'Vous ne pouvez pas réserver votre propre trajet.')
        return redirect('rides:ride_detail', pk=ride_id)
    
    # Vérifier que le trajet est confirmé
    if ride.status != 'confirmed':
        messages.error(request, 'Ce trajet n\'est pas encore disponible pour les réservations.')
        return redirect('rides:ride_detail', pk=ride_id)
    
    # Vérifier si une réservation existe déjà
    existing_booking = Booking.objects.filter(passenger=request.user, ride=ride).first()
    if existing_booking:
        messages.warning(request, 'Vous avez déjà une réservation pour ce trajet.')
        return redirect('rides:ride_detail', pk=ride_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.passenger = request.user
            booking.ride = ride
            
            # Vérifier la disponibilité des places
            if booking.number_of_seats <= ride.available_seats:
                booking.save()
                messages.success(request, 'Votre demande de réservation a été envoyée au conducteur.')
                return redirect('rides:ride_detail', pk=ride_id)
            else:
                messages.error(request, 'Il n\'y a pas assez de places disponibles.')
    else:
        form = BookingForm()
    
    return render(request, 'rides/booking_form.html', {
        'form': form,
        'ride': ride
    })

@login_required
def booking_action(request, booking_id, action):
    """Action sur une demande de réservation par le conducteur"""
    booking = get_object_or_404(Booking, pk=booking_id)
    
    # Vérifier que l'utilisateur est le conducteur
    if request.user != booking.ride.driver:
        messages.error(request, 'Vous n\'êtes pas autorisé à effectuer cette action.')
        return redirect('rides:my_rides')
    
    # Vérifier que la réservation est en attente
    if booking.status != 'pending':
        messages.error(request, 'Cette réservation a déjà été traitée.')
        return redirect('rides:my_rides')
    
    if action == 'confirm':
        # Vérifier la disponibilité des places
        if booking.ride.available_seats >= booking.number_of_seats:
            booking.status = 'confirmed'
            booking.ride.available_seats -= booking.number_of_seats
            booking.ride.save()
            booking.save()
            
            # Envoyer un email de confirmation au passager
            subject = 'Réservation confirmée'
            message = f'Votre réservation pour le trajet {booking.ride.departure_city} → {booking.ride.arrival_city} le {booking.ride.departure_date} a été confirmée.'
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [booking.passenger.email],
                fail_silently=True
            )
            
            messages.success(request, 'La réservation a été confirmée.')
        else:
            messages.error(request, 'Il n\'y a plus assez de places disponibles.')
    
    elif action == 'reject':
        booking.status = 'rejected'
        booking.save()
        
        # Envoyer un email d'information au passager
        subject = 'Réservation refusée'
        message = f'Votre réservation pour le trajet {booking.ride.departure_city} → {booking.ride.arrival_city} le {booking.ride.departure_date} a été refusée.'
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.passenger.email],
            fail_silently=True
        )
        
        messages.success(request, 'La réservation a été refusée.')
    
    return redirect('rides:my_rides')

@login_required
def rate_ride(request, booking_id):
    """Évaluation d'un trajet et de l'utilisateur associé"""
    booking = get_object_or_404(Booking, pk=booking_id)
    
    # Vérifier que l'utilisateur a participé au trajet
    if request.user != booking.passenger and request.user != booking.ride.driver:
        messages.error(request, 'Vous n\'êtes pas autorisé à évaluer ce trajet.')
        return redirect('rides:my_rides')
    
    # Vérifier que le trajet est terminé
    if booking.status != 'completed':
        messages.error(request, 'Vous ne pouvez évaluer que les trajets terminés.')
        return redirect('rides:my_rides')
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.from_user = request.user
            rating.ride = booking.ride
            
            # Déterminer qui est évalué
            if request.user == booking.passenger:
                rating.to_user = booking.ride.driver
            else:
                rating.to_user = booking.passenger
            
            try:
                rating.save()
                messages.success(request, 'Merci pour votre évaluation !')
                return redirect('rides:my_rides')
            except IntegrityError:
                messages.error(request, 'Vous avez déjà évalué ce critère pour ce trajet.')
    else:
        form = RatingForm()
    
    return render(request, 'rides/rating_form.html', {
        'form': form,
        'booking': booking
    })

@login_required
def report_ride(request, ride_id):
    """Signalement d'un problème lié à un trajet"""
    ride = get_object_or_404(Ride, pk=ride_id)
    
    # Vérifier que l'utilisateur a participé au trajet
    if not Booking.objects.filter(ride=ride, passenger=request.user).exists() and request.user != ride.driver:
        messages.error(request, 'Vous n\'êtes pas autorisé à signaler ce trajet.')
        return redirect('rides:ride_detail', pk=ride_id)
    
    if request.method == 'POST':
        form = RideReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.ride = ride
            report.reporter = request.user
            
            # Déterminer qui est signalé
            if request.user == ride.driver:
                report.reported_user = ride.bookings.first().passenger
            else:
                report.reported_user = ride.driver
            
            report.save()
            messages.success(request, 'Votre signalement a été enregistré et sera traité par notre équipe.')
            
            # Notification immédiate si nécessaire
            if report.requires_immediate_action:
                messages.warning(request, 'Notre équipe a été notifiée et traitera ce signalement en priorité.')
            
            return redirect('rides:ride_detail', pk=ride_id)
    else:
        form = RideReportForm()
    
    return render(request, 'rides/report_form.html', {
        'form': form,
        'ride': ride
    })

@login_required
def my_reports(request):
    """Liste des signalements de l'utilisateur"""
    reports_made = RideReport.objects.filter(reporter=request.user).order_by('-created_at')
    reports_received = RideReport.objects.filter(reported_user=request.user).order_by('-created_at')
    
    return render(request, 'rides/my_reports.html', {
        'reports_made': reports_made,
        'reports_received': reports_received
    })

@login_required
def ride_validate(request, pk):
    """Validation d'un trajet par le conducteur"""
    ride = get_object_or_404(Ride, pk=pk)
    
    # Vérifier que l'utilisateur est bien le conducteur du trajet
    if ride.driver != request.user:
        messages.error(request, 'Vous n\'êtes pas autorisé à valider ce trajet.')
        return redirect('rides:ride_detail', pk=pk)
    
    # Vérifier que le trajet est en attente de validation
    if ride.status != 'draft':
        messages.error(request, 'Ce trajet ne peut pas être validé.')
        return redirect('rides:ride_detail', pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':
            ride.status = 'confirmed'
            ride.save()
            messages.success(request, 'Le trajet a été validé avec succès.')
        elif action == 'cancel':
            ride.status = 'cancelled'
            ride.save()
            messages.success(request, 'Le trajet a été annulé.')
    
    return redirect('rides:ride_detail', pk=pk)

@login_required
def get_cities(request):
    """API pour l'autocomplétion des villes"""
    query = request.GET.get('q', '').lower()
    cities = [city for city in MOROCCAN_CITIES if query in city.lower()]
    return JsonResponse(cities, safe=False)

@login_required
def calculate_ride_price(request):
    """Calcule le prix estimé d'un trajet"""
    departure_city = request.GET.get('departure_city')
    arrival_city = request.GET.get('arrival_city')
    
    if not departure_city or not arrival_city:
        return JsonResponse({
            'error': 'Les villes de départ et d\'arrivée sont requises'
        }, status=400)
    
    distance = get_distance(departure_city, arrival_city)
    if distance is None:
        return JsonResponse({
            'error': 'Impossible de calculer la distance entre ces villes'
        }, status=400)
    
    price = calculate_price(distance)
    
    return JsonResponse({
        'distance_km': distance,
        'price': price,
        'driver_profit': round(price * 0.8, 2),  # 80% pour le conducteur
        'platform_fee': round(price * 0.2, 2),   # 20% pour la plateforme
        'currency': 'DH'
    })

@login_required
def vehicle_list(request):
    """Liste des véhicules du conducteur"""
    if not request.user.groups.filter(name='Conducteurs').exists():
        messages.error(request, 'Cette page est réservée aux conducteurs.')
        return redirect('rides:dashboard')
    
    vehicles = Vehicle.objects.filter(driver=request.user)
    return render(request, 'rides/vehicle_list.html', {'vehicles': vehicles})

@login_required
def vehicle_create(request):
    """Ajout d'un nouveau véhicule"""
    if not request.user.groups.filter(name='Conducteurs').exists():
        messages.error(request, 'Cette action est réservée aux conducteurs.')
        return redirect('rides:dashboard')
    
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.driver = request.user
            vehicle.save()
            messages.success(request, 'Votre véhicule a été ajouté avec succès.')
            return redirect('rides:vehicle_list')
    else:
        form = VehicleForm()
    
    return render(request, 'rides/vehicle_form.html', {'form': form, 'title': 'Ajouter un véhicule'})

@login_required
def vehicle_edit(request, pk):
    """Modification d'un véhicule"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if vehicle.driver != request.user:
        messages.error(request, 'Vous n\'êtes pas autorisé à modifier ce véhicule.')
        return redirect('rides:vehicle_list')
    
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Le véhicule a été modifié avec succès.')
            return redirect('rides:vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)
    
    return render(request, 'rides/vehicle_form.html', {
        'form': form,
        'vehicle': vehicle,
        'title': 'Modifier le véhicule'
    })

@login_required
def vehicle_delete(request, pk):
    """Suppression d'un véhicule"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if vehicle.driver != request.user:
        messages.error(request, 'Vous n\'êtes pas autorisé à supprimer ce véhicule.')
        return redirect('rides:vehicle_list')
    
    if request.method == 'POST':
        # Vérifier si le véhicule est utilisé dans des trajets futurs
        future_rides = Ride.objects.filter(
            vehicle=vehicle,
            departure_date__gte=timezone.now().date()
        ).exists()
        
        if future_rides:
            messages.error(request, 'Ce véhicule ne peut pas être supprimé car il est associé à des trajets futurs.')
            return redirect('rides:vehicle_list')
        
        vehicle.delete()
        messages.success(request, 'Le véhicule a été supprimé avec succès.')
        return redirect('rides:vehicle_list')
    
    return render(request, 'rides/vehicle_confirm_delete.html', {'vehicle': vehicle}) 