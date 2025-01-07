import streamlit as st
from geopy.geocoders import Nominatim
import geopy.exc
import urllib.parse
import requests

def Navbar():
    with st.sidebar:
        st.page_link('app.py', label='Accueil', icon='🏠')
        st.page_link('pages/explorer.py', label='Explorer', icon='🔍')
        st.page_link('pages/comparer.py', label='Comparer', icon='📊')

def get_personnal_address():
    return st.session_state.get('personal_address')

def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="streamlit_app", timeout=10)
        location = geolocator.geocode(f"{address}, Rhône, France")
        if location:
            return location.latitude, location.longitude
    except geopy.exc.GeocoderServiceError:
        st.toast("❌ Service de cartographie indisponible. Veuillez réessayer plus tard.")
    return None, None

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
        
            # Headers pour simuler un navigateur
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
                "DNT": "1",  # Do Not Track
            }

            # Effectuer la requête GET à l'API
            response = requests.get(tcl_api_url, headers=headers)

            duration = "N/A"

            # Vérifier si la requête a réussi
            if response.status_code == 200:
                # Convertir la réponse en JSON
                data = response.json()
                
                # Extraire la durée depuis la première entrée des trajets
                if "journeys" in data and len(data["journeys"]) > 0:
                    duration = data["journeys"][0]["duration"]
                    # Conversion de la durée en minutes et si plus de 60 minutes, en heures
                    duration = duration // 60
                    if duration > 60:
                        hours = duration // 60
                        minutes = duration % 60
                        duration = f"{hours}h{minutes}"
                    else:
                        duration = f"{duration} min"
        
            # Vérifier si tcl_url a été défini
            if not tcl_url:
                return None, "N/A"

            return tcl_url, duration

    # Retourner None et "N/A" si les coordonnées sont manquantes
    return None, "N/A"

available_restaurants_options = ["Sélectionner un restaurant", "Restaurant 1", "Restaurant 2", "Restaurant 3", "Restaurant 4", "Restaurant 5"] # [TEMP] À remplacer par les restaurants de la base de données
multi_available_restaurants_options = ["Restaurant 1", "Restaurant 2", "Restaurant 3", "Restaurant 4", "Restaurant 5"] # [TEMP] À remplacer par les restaurants de la base de données
add_restaurant_options = ["Sélectionner un restaurant", "Restaurant 6", "Restaurant 7", "Restaurant 8", "Restaurant 9", "Restaurant 10"] # [TEMP] À remplacer par les restaurants de la base de données