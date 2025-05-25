from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True)
    rating = models.FloatField(default=5.0)
    number_of_ratings = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil de {self.user.username}"

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"

class Vehicle(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    license_plate = models.CharField(max_length=10)
    number_of_seats = models.IntegerField(validators=[MinValueValidator(1)])
    comfort_features = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"

class PricingSettings(models.Model):
    """Paramètres de tarification pour les trajets"""
    base_price_per_km = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=0.50,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Prix de base par kilomètre"
    )
    driver_profit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=80.00,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Pourcentage du prix total qui revient au conducteur"
    )
    admin_profit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Pourcentage du prix total qui revient à l'administrateur"
    )
    min_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=5.00,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Prix minimum pour un trajet"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paramètre de tarification"
        verbose_name_plural = "Paramètres de tarification"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.driver_profit_percentage + self.admin_profit_percentage != 100:
            raise ValidationError("La somme des pourcentages de profit doit être égale à 100%")

    def __str__(self):
        return f"Tarification ({self.base_price_per_km}€/km)"

class Ride(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending', 'En attente de validation'),
        ('confirmed', 'Validé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]

    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides_as_driver')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True)
    departure_city = models.CharField(max_length=100)
    arrival_city = models.CharField(max_length=100)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    distance_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        help_text="Distance en kilomètres"
    )
    driver_profit = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        help_text="Part du conducteur"
    )
    admin_profit = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        help_text="Part de l'administrateur"
    )
    available_seats = models.IntegerField(validators=[MinValueValidator(1)])
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_price(self):
        """Calcule le prix du trajet et les profits associés"""
        if not self.distance_km:
            return

        # Récupérer les paramètres de tarification actuels
        pricing = PricingSettings.objects.first()
        if not pricing:
            return

        # Calculer le prix total
        base_price = self.distance_km * pricing.base_price_per_km
        self.price = max(base_price, pricing.min_price)

        # Calculer les profits
        self.driver_profit = (self.price * pricing.driver_profit_percentage / 100).quantize(Decimal('0.01'))
        self.admin_profit = (self.price * pricing.admin_profit_percentage / 100).quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        if self.distance_km and not self.price:
            self.calculate_price()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.departure_city} → {self.arrival_city} ({self.departure_date})"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente de confirmation'),
        ('confirmed', 'Confirmé par le conducteur'),
        ('rejected', 'Refusé par le conducteur'),
        ('cancelled_by_passenger', 'Annulé par le passager'),
        ('cancelled_by_driver', 'Annulé par le conducteur'),
        ('completed', 'Trajet terminé'),
    ]

    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_as_passenger')
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='bookings')
    number_of_seats = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, help_text="Message pour le conducteur")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['passenger', 'ride']

    def __str__(self):
        return f"Réservation de {self.passenger.username} pour {self.ride}"

class Rating(models.Model):
    RATING_CHOICES = [
        (1, '1 - Très mauvais'),
        (2, '2 - Mauvais'),
        (3, '3 - Moyen'),
        (4, '4 - Bon'),
        (5, '5 - Excellent'),
    ]

    RATING_CRITERIA = [
        ('general', 'Général'),
        ('punctuality', 'Ponctualité'),
        ('comfort', 'Confort'),
        ('cleanliness', 'Propreté'),
        ('communication', 'Communication'),
        ('driving', 'Conduite'),
    ]

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received')
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    criteria = models.CharField(max_length=20, choices=RATING_CRITERIA, default='general')
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False, help_text="L'évaluation restera anonyme")

    class Meta:
        unique_together = ['from_user', 'to_user', 'ride', 'criteria']
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"

    def __str__(self):
        return f"Note de {self.from_user.username} pour {self.to_user.username} - {self.get_criteria_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour la note moyenne du profil
        profile = Profile.objects.get(user=self.to_user)
        all_ratings = Rating.objects.filter(to_user=self.to_user)
        profile.rating = all_ratings.aggregate(models.Avg('rating'))['rating__avg']
        profile.number_of_ratings = all_ratings.count()
        profile.save()

class RideRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('accepted', 'Accepté'),
        ('rejected', 'Refusé'),
        ('cancelled', 'Annulé'),
    ]

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='requests')
    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ride_requests')
    number_of_seats = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Demande de {self.passenger.username} pour {self.ride}"

class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        # Le token est valide pendant 24 heures
        return (timezone.now() - self.created_at).days < 1

    def __str__(self):
        return f"Token de vérification pour {self.user.email}"

class RideReport(models.Model):
    REPORT_TYPES = [
        ('inappropriate_behavior', 'Comportement inapproprié'),
        ('safety_concern', 'Problème de sécurité'),
        ('no_show', 'Absence au rendez-vous'),
        ('wrong_vehicle', 'Véhicule différent'),
        ('dangerous_driving', 'Conduite dangereuse'),
        ('other', 'Autre'),
    ]

    REPORT_STATUS = [
        ('pending', 'En attente de traitement'),
        ('investigating', 'En cours d\'investigation'),
        ('resolved', 'Résolu'),
        ('closed', 'Fermé'),
    ]

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    description = models.TextField(help_text="Décrivez en détail le problème rencontré")
    evidence = models.FileField(upload_to='report_evidence/', blank=True, help_text="Photos, vidéos ou autres preuves")
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='pending')
    admin_notes = models.TextField(blank=True, help_text="Notes internes pour l'administration")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_anonymous = models.BooleanField(default=False, help_text="Le signalement restera anonyme")
    requires_immediate_action = models.BooleanField(default=False, help_text="Nécessite une action immédiate")

    class Meta:
        verbose_name = "Signalement"
        verbose_name_plural = "Signalements"
        ordering = ['-created_at']

    def __str__(self):
        return f"Signalement de {self.reporter.username} - {self.get_report_type_display()}"

    def save(self, *args, **kwargs):
        # Si c'est un nouveau signalement grave, notifier les administrateurs
        if self.requires_immediate_action and not self.pk:
            self.notify_admins()
        super().save(*args, **kwargs)

    def notify_admins(self):
        # Logique pour notifier les administrateurs
        subject = f'[URGENT] Nouveau signalement nécessitant une action immédiate'
        message = f"""
        Un nouveau signalement urgent a été créé :
        
        Type : {self.get_report_type_display()}
        Trajet : {self.ride}
        Signalé par : {self.reporter.username}
        Description : {self.description}
        
        Veuillez traiter ce signalement en priorité.
        """
        
        admin_emails = [admin[1] for admin in settings.ADMINS]
        if admin_emails:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=True
            ) 