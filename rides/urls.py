from django.urls import path
from . import views
from . import payment_views

app_name = 'rides'

urlpatterns = [
    # Liste et recherche des trajets
    path('', views.ride_list, name='ride_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.ride_search, name='ride_search'),
    
    # Création et gestion des trajets
    path('create/', views.ride_create, name='ride_create'),
    path('<int:pk>/', views.ride_detail, name='ride_detail'),
    path('<int:pk>/edit/', views.ride_edit, name='ride_edit'),
    path('<int:pk>/delete/', views.ride_delete, name='ride_delete'),
    path('<int:pk>/validate/', views.ride_validate, name='ride_validate'),
    path('request/<int:pk>/<str:action>/', views.request_action, name='request_action'),
    
    # Gestion des réservations
    path('<int:ride_id>/book/', views.booking_request, name='booking_request'),
    path('booking/<int:booking_id>/<str:action>/', views.booking_action, name='booking_action'),
    
    # Vue personnelle des trajets
    path('my-rides/', views.my_rides, name='my_rides'),
    
    # Profil utilisateur
    path('profile/', views.profile_view, name='profile'),
    
    # Notation
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('calculate-price/', views.calculate_ride_price, name='calculate_price'),
    
    # Évaluations
    path('booking/<int:booking_id>/rate/', views.rate_ride, name='rate_ride'),
    
    # Signalements
    path('<int:ride_id>/report/', views.report_ride, name='report_ride'),
    path('my-reports/', views.my_reports, name='my_reports'),
    
    # Gestion des véhicules
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/create/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('vehicles/<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),
    path('api/cities/', views.get_cities, name='get_cities'),
    path('api/calculate-price/', views.calculate_ride_price, name='calculate_price'),
    path('booking/<int:booking_id>/payment/', payment_views.initiate_payment, name='initiate_payment'),
    path('booking/<int:booking_id>/validate-payment/', payment_views.validate_payment, name='validate_payment'),
] 