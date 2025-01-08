import streamlit as st
from geopy.geocoders import Nominatim
import geopy.exc
import urllib.parse
import requests

# Fonction pour afficher la barre de navigation
def Navbar():
    with st.sidebar:
        st.page_link('app.py', label='Accueil', icon='🏠')
        st.page_link('pages/explorer.py', label='Explorer', icon='🔍')
        st.page_link('pages/comparer.py', label='Comparer', icon='📊')

# Fonction pour enregistrer l'adresse personnelle
def get_personnal_address():
    return st.session_state.get('personal_address')

# Fonction pour obtenir les coordonnées d'une adresse
def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="streamlit_app", timeout=10)
        location = geolocator.geocode(f"{address}, Rhône, France")
        if location:
            return location.latitude, location.longitude
    except geopy.exc.GeocoderServiceError:
        st.toast("❌ Service de cartographie indisponible. Veuillez réessayer plus tard.")
    return None, None

# Fonction pour obtenir les informations de trajet depuis le site TCL
def tcl_api(restaurant_address):
    personal_address = get_personnal_address()

    if personal_address:
        dep_lat, dep_lon = get_coordinates(personal_address)
        arr_lat, arr_lon = get_coordinates(restaurant_address)
                    
        if dep_lat and dep_lon and arr_lat and arr_lon:
            from_coord = f"{dep_lon};{dep_lat}"
            to_coord = f"{arr_lon};{arr_lat}"
            encoded_from = urllib.parse.quote(from_coord)
            encoded_to = urllib.parse.quote(to_coord)
            
            tcl_url = f"https://www.tcl.fr/itineraires?date=now&pmr=0&from={encoded_from}&to={encoded_to}"
            tcl_api_url = f"https://carte.tcl.fr/api/itinerary?datetime=now&from={encoded_from}&to={encoded_to}&params=departure,metro,funiculaire,tramway,bus,shuttle,bss,bike,car&walking=1.12&cycling=4.44"
        
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": f"https://carte.tcl.fr/route-calculation?date=now&from={encoded_from}&to={encoded_to}&lang=fr",
                "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "DNT": "1",
            }

            # Effectuer la requête GET à l'API
            response = requests.get(tcl_api_url, headers=headers, timeout=10)

            duration_public = "N/A"
            duration_car = "N/A"
            duration_soft = "N/A"
            fastest_mode = ("❌", "N/A")

            # Variables pour les durées en minutes
            duration_public_min = float('inf')
            duration_car_min = float('inf')
            duration_soft_min = float('inf')

            # Vérifier si la requête a réussi
            if response.status_code == 200:
                # Convertir la réponse en JSON
                data = response.json()
                
                # Extraire la durée depuis la première entrée des trajets publics
                if "journeys" in data and len(data["journeys"]) > 0:
                    duration_sec = data["journeys"][0].get("duration")
                    if duration_sec:
                        duration = duration_sec // 60
                        duration_public_min = duration
                        if duration > 59:
                            hours = duration // 60
                            minutes = duration % 60
                            if minutes == 0:
                                minutes = "00"
                            duration_public = f"{hours}h{minutes}"
                        else:
                            duration_public = f"{duration} min"
                
                # Extraire la durée depuis la première entrée des trajets en voiture
                if "journeysCar" in data and len(data["journeysCar"]) > 0:
                    duration_sec_car = data["journeysCar"][0].get("duration")
                    if duration_sec_car:
                        duration_car_minutes = duration_sec_car // 60
                        duration_car_min = duration_car_minutes
                        if duration_car_minutes > 59:
                            hours_car = duration_car_minutes // 60
                            minutes_car = duration_car_minutes % 60
                            if minutes_car == 0:
                                minutes_car = "00"
                            duration_car = f"{hours_car}h{minutes_car}"
                        else:
                            duration_car = f"{duration_car_minutes} min"
                
                # Extraire la durée depuis la première entrée des trajets en modes doux
                if "journeysSofts" in data and len(data["journeysSofts"]) > 0:
                    duration_sec_soft = data["journeysSofts"][0].get("duration")
                    if duration_sec_soft:
                        duration_soft_minutes = duration_sec_soft // 60
                        duration_soft_min = duration_soft_minutes
                        if duration_soft_minutes > 59:
                            hours_soft = duration_soft_minutes // 60
                            minutes_soft = duration_soft_minutes % 60
                            if minutes_soft == 0:
                                minutes_soft = "00"
                            duration_soft = f"{hours_soft}h{minutes_soft}"
                        else:
                            duration_soft = f"{duration_soft_minutes} min"

            # Déterminer le mode de transport le plus rapide
            durations = {
                "public": duration_public_min,
                "car": duration_car_min,
                "soft": duration_soft_min,
            }

            min_duration = min(durations.values())

            if min_duration == float('inf'):
                fastest_mode = ("❌", "N/A")
            else:
                if min_duration == durations["public"]:
                    fastest_mode = ("🚌", duration_public)
                elif min_duration == durations["car"]:
                    fastest_mode = ("🚗", duration_car)
                elif min_duration == durations["soft"]:
                    fastest_mode = ("🚲", duration_soft)

            # Vérifier si tcl_url a été défini
            if not tcl_url:
                return None, "N/A", "N/A", "N/A", ("❌", "N/A")

            return tcl_url, duration_public, duration_car, duration_soft, fastest_mode

    # Retourner None et "N/A" si les coordonnées sont manquantes
    return None, "N/A", "N/A", "N/A", ("❌", "N/A")

available_restaurants_options = ["Sélectionner un restaurant", "Restaurant 1", "Restaurant 2", "Restaurant 3", "Restaurant 4", "Restaurant 5"] # [TEMP] À remplacer par les restaurants de la base de données
multi_available_restaurants_options = ["Restaurant 1", "Restaurant 2", "Restaurant 3", "Restaurant 4", "Restaurant 5"] # [TEMP] À remplacer par les restaurants de la base de données
add_restaurant_options = ["Sélectionner un restaurant", "Restaurant 6", "Restaurant 7", "Restaurant 8", "Restaurant 9", "Restaurant 10"] # [TEMP] À remplacer par les restaurants de la base de données