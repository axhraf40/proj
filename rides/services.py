from decimal import Decimal

# Distances prédéfinies entre les principales villes marocaines (en km)
DISTANCES = {
    ('rabat', 'casablanca'): 87,
    ('casablanca', 'rabat'): 87,
    ('rabat', 'fes'): 207,
    ('fes', 'rabat'): 207,
    ('rabat', 'tanger'): 250,
    ('tanger', 'rabat'): 250,
    ('casablanca', 'marrakech'): 238,
    ('marrakech', 'casablanca'): 238,
    ('casablanca', 'agadir'): 460,
    ('agadir', 'casablanca'): 460,
    ('casablanca', 'tanger'): 337,
    ('tanger', 'casablanca'): 337,
    ('marrakech', 'agadir'): 256,
    ('agadir', 'marrakech'): 256,
    ('fes', 'meknes'): 65,
    ('meknes', 'fes'): 65,
    ('rabat', 'meknes'): 148,
    ('meknes', 'rabat'): 148,
    ('casablanca', 'el jadida'): 96,
    ('el jadida', 'casablanca'): 96,
}

def calculate_distance(departure_city, arrival_city):
    """Calcule la distance entre deux villes marocaines"""
    try:
        # Normaliser les noms des villes (minuscules)
        departure = departure_city.lower().strip()
        arrival = arrival_city.lower().strip()
        
        # Chercher la distance dans le dictionnaire
        distance = DISTANCES.get((departure, arrival))
        
        if distance is not None:
            return Decimal(str(distance))
        
        # Si la distance n'est pas trouvée, retourner None
        print(f"Distance non trouvée pour : {departure} → {arrival}")
        return None
        
    except Exception as e:
        print(f"Erreur lors du calcul de la distance : {str(e)}")
        return None 