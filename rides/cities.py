MOROCCAN_CITIES = [
    "Casablanca",
    "Rabat",
    "Fès",
    "Tanger",
    "Marrakech",
    "Agadir",
    "Meknès",
    "Oujda",
    "Kénitra",
    "Tétouan",
    "El Jadida",
    "Safi",
    "Mohammedia",
    "Khouribga",
    "Béni Mellal",
    "Nador",
    "Taza",
    "Settat",
    "Berrechid",
    "Khémisset",
    "Larache",
    "Ksar El Kébir",
    "Essaouira",
    "Ouarzazate",
    "Chefchaouen"
]

# Distances approximatives entre les principales villes (en km)
CITY_DISTANCES = {
    ('Casablanca', 'Rabat'): 87,
    ('Casablanca', 'Marrakech'): 238,
    ('Casablanca', 'Agadir'): 460,
    ('Casablanca', 'Fès'): 295,
    ('Casablanca', 'Tanger'): 337,
    ('Rabat', 'Fès'): 207,
    ('Rabat', 'Tanger'): 250,
    ('Marrakech', 'Agadir'): 256,
    ('Fès', 'Meknès'): 65,
    ('Tanger', 'Tétouan'): 60,
    ('Casablanca', 'El Jadida'): 96,
    ('Rabat', 'Kénitra'): 40,
    ('Casablanca', 'Mohammedia'): 25,
    ('Fès', 'Taza'): 120,
    ('Marrakech', 'Essaouira'): 177,
    ('Casablanca', 'Settat'): 72,
    ('Agadir', 'Essaouira'): 173,
    ('Fès', 'Oujda'): 360,
    ('Rabat', 'Meknès'): 148,
    ('Marrakech', 'Ouarzazate'): 195
}

def get_distance(city1, city2):
    """
    Retourne la distance entre deux villes.
    Si la distance directe n'existe pas, essaie de la calculer via des villes intermédiaires.
    """
    # Normaliser les noms des villes
    city1 = city1.title()
    city2 = city2.title()
    
    # Vérifier la distance directe
    if (city1, city2) in CITY_DISTANCES:
        return CITY_DISTANCES[(city1, city2)]
    elif (city2, city1) in CITY_DISTANCES:
        return CITY_DISTANCES[(city2, city1)]
    
    return None

def calculate_price(distance):
    """
    Calcule le prix du trajet en fonction de la distance.
    Prix = 0.5 DH/km avec un minimum de 20 DH
    """
    if distance is None:
        return None
        
    base_price = distance * 0.5  # 0.5 DH par kilomètre
    min_price = 20  # Prix minimum de 20 DH
    
    return max(base_price, min_price) 