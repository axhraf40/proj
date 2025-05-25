from django import forms
from .models import Ride, RideRequest, Booking, Vehicle, Rating, Profile, RideReport
from django.core.exceptions import ValidationError
from datetime import date
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime
from .cities import MOROCCAN_CITIES
import pytz

class SignUpForm(UserCreationForm):
    ROLE_CHOICES = [
        ('conducteur', 'Conducteur'),
        ('passager', 'Passager'),
    ]
    
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Rôle')
    
    email = forms.EmailField(max_length=254, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role')

class RideForm(forms.ModelForm):
    departure_city = forms.ChoiceField(
        choices=[(city, city) for city in MOROCCAN_CITIES],
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    arrival_city = forms.ChoiceField(
        choices=[(city, city) for city in MOROCCAN_CITIES],
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )

    class Meta:
        model = Ride
        fields = [
            'vehicle',
            'departure_city',
            'arrival_city',
            'departure_date',
            'departure_time',
            'available_seats',
            'description'
        ]
        widgets = {
            'departure_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'departure_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'available_seats': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'vehicle': forms.Select(attrs={'class': 'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        departure_date = cleaned_data.get('departure_date')
        departure_time = cleaned_data.get('departure_time')

        if departure_date and departure_time:
            # Créer un datetime combiné
            departure_datetime = datetime.combine(departure_date, departure_time)
            departure_datetime = pytz.timezone('Africa/Casablanca').localize(departure_datetime)
            
            # Obtenir la date et l'heure actuelles
            now = datetime.now(pytz.timezone('Africa/Casablanca'))
            
            # Vérifier si la date de départ est dans le futur
            if departure_datetime <= now:
                raise forms.ValidationError(
                    "La date et l'heure de départ doivent être dans le futur."
                )

        return cleaned_data

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['number_of_seats', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Message optionnel pour le conducteur'}),
        }
        
    def clean_number_of_seats(self):
        seats = self.cleaned_data.get('number_of_seats')
        if seats < 1:
            raise forms.ValidationError('Le nombre de places doit être au moins 1.')
        return seats

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['brand', 'model', 'color', 'license_plate', 'number_of_seats', 'comfort_features']

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'criteria', 'comment', 'is_anonymous']
        widgets = {
            'rating': forms.RadioSelect(),
            'criteria': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'rating': 'Note',
            'criteria': 'Critère',
            'comment': 'Commentaire',
            'is_anonymous': 'Rester anonyme'
        }
        help_texts = {
            'comment': 'Donnez plus de détails sur votre expérience',
            'is_anonymous': 'Votre nom ne sera pas visible publiquement si vous cochez cette case'
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'bio', 'photo']

class RideRequestForm(forms.ModelForm):
    number_of_seats = forms.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(8)
        ],
        widget=forms.NumberInput(attrs={'min': '1', 'max': '8'})
    )

    class Meta:
        model = RideRequest
        fields = ['number_of_seats', 'message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Message pour le conducteur (facultatif)'
            })
        }
        labels = {
            'number_of_seats': 'Nombre de places souhaitées',
            'message': 'Message'
        }

    def __init__(self, *args, ride=None, **kwargs):
        super().__init__(*args, **kwargs)
        if ride:
            self.fields['number_of_seats'].widget.attrs['max'] = ride.available_seats
            self.fields['number_of_seats'].validators[1].limit_value = ride.available_seats

class RideReportForm(forms.ModelForm):
    class Meta:
        model = RideReport
        fields = ['report_type', 'description', 'evidence', 'is_anonymous', 'requires_immediate_action']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'evidence': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'report_type': 'Type de signalement',
            'description': 'Description du problème',
            'evidence': 'Preuves (optionnel)',
            'is_anonymous': 'Rester anonyme',
            'requires_immediate_action': 'Action immédiate requise'
        }
        help_texts = {
            'description': 'Décrivez en détail la situation et pourquoi vous effectuez ce signalement',
            'evidence': 'Vous pouvez ajouter des photos ou documents pour appuyer votre signalement',
            'requires_immediate_action': 'Cochez cette case si la situation nécessite une intervention urgente'
        } 