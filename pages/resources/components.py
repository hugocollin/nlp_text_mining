import streamlit as st
import urllib.parse
import requests
from pathlib import Path
import math
import base64
import webbrowser

# Fonction pour afficher la barre de navigation
def Navbar():
    with st.sidebar:
        st.page_link('app.py', label='Accueil', icon='🏠')
        st.page_link('pages/explorer.py', label='Explorer', icon='🔍')
        st.page_link('pages/comparer.py', label='Comparer', icon='🆚')
        st.page_link('pages/admin.py', label='Admin', icon='🔒')

# Fonction pour calculer la distance entre deux points
def haversine(lat1, lon1, lat2, lon2):
    # Rayon moyen de la Terre en mètres
    R = 6371000

    # Conversion des degrés en radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Différences des coordonnées
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Formule de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance en mètres
    distance = R * c
    return distance

# Fonction pour enregistrer l'adresse personnelle
def get_personal_address():
    personal_address = st.session_state.get('personal_address')
    personal_latitude = st.session_state.get('personal_latitude')
    personal_longitude = st.session_state.get('personal_longitude')
    return personal_address, personal_latitude, personal_longitude

# Fonction pour filtrer les restaurants par rayon
def filter_restaurants_by_radius(restaurants, personal_latitude, personal_longitude, radius):
    filtered = []
    for restaurant in restaurants:
        distance = haversine(personal_latitude, personal_longitude, restaurant["latitude"], restaurant["longitude"])
        if distance <= radius:
            filtered.append(restaurant)
    return filtered

# Fonction pour obtenir le lien Google Maps d'une adresse
def get_google_maps_link(address):
    # Mise en forme de l'adresse
    parts = address.split(',')
    if len(parts) > 1 and parts[-1].strip().lower() == 'france':
        address = ','.join(parts[:-1])

    # Encodage de l'adresse
    encoded_address = urllib.parse.quote_plus(address)
    google_maps_url = f"https://www.google.com/maps/place/{encoded_address}"

    return google_maps_url

# Fonction pour convertir une image en chaîne base64
def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Fonction pour afficher les étoiles Michelin
def display_michelin_stars(rating):
    # Définition des chemins des images des étoiles
    base_path = Path(__file__).parent / 'images'
    one_star = base_path / 'one_star.svg'
    two_stars = base_path / 'two_stars.svg'
    three_stars = base_path / 'three_stars.svg'

    # Sélection de l'image en fonction de la note
    if rating == 1:
        star_path = one_star
    elif rating == 2:
        star_path = two_stars
    elif rating == 3:
        star_path = three_stars
    else:
        return ""

    # Convertion de l'image en base64
    star_base64 = image_to_base64(star_path)
    if star_base64:
        # Création de la data URI
        star_data_uri = f"data:image/svg+xml;base64,{star_base64}"
        return star_data_uri
    else:
        return ""

# Fonction pour afficher les étoiles des notes
def display_stars(rating):
    # Définition des chemins des images des étoiles
    base_path = Path(__file__).parent / 'images'
    full_star = base_path / 'full_star_icon.svg'
    half_star = base_path / 'half_star_icon.svg'
    empty_star = base_path / 'empty_star_icon.svg'
    
    # Création de la liste des étoiles
    stars = []
    for i in range(1, 6):
        if rating >= i:
            star_path = full_star
        elif rating >= i - 0.5:
            star_path = half_star
        else:
            star_path = empty_star

        star_base64 = image_to_base64(star_path)
        if star_base64:
            # Création de la data URI
            star_data_uri = f"data:image/svg+xml;base64,{star_base64}"
            stars.append(star_data_uri)
        else:
            # Utilisation d'une étoile vide par défaut en cas d'erreur
            empty_star_path = empty_star
            star_base64_default = image_to_base64(empty_star_path)
            if star_base64_default:
                star_data_uri_default = f"data:image/svg+xml;base64,{star_base64_default}"
                stars.append(star_data_uri_default)
            else:
                stars.append("")
    return stars

# Fonction pour ajouter un restaurant au comparateur
def add_to_comparator(restaurant):
    comparator = st.session_state['comparator']
    if restaurant.id_restaurant not in comparator:
        if len(comparator) < 3:
            comparator.append(restaurant.id_restaurant)
            st.session_state['comparator'] = comparator
            st.toast(f"Le restaurant {restaurant.nom} a été ajouté au comparateur", icon="🆚")
        else:
            st.toast("Le comparateur est plein, veuillez retirer un restaurant avant d'en ajouter un autre", icon="ℹ️")
    else:
        st.toast(f"Le restaurant {restaurant.nom} est déjà dans le comparateur", icon="ℹ️")

# Fonction pour obtenir les informations de trajet depuis le site TCL
@st.cache_data(ttl=300, show_spinner=False)
def tcl_api(personal_address, personal_latitude, personal_longitude, restaurant_latitude, restaurant_longitude):
    
    if personal_address:
        # Si les coordonnées sont valides
        if personal_latitude and personal_longitude and restaurant_latitude and restaurant_longitude:
            from_coord = f"{personal_longitude};{personal_latitude}"
            to_coord = f"{restaurant_longitude};{restaurant_latitude}"
            encoded_from = urllib.parse.quote(from_coord)
            encoded_to = urllib.parse.quote(to_coord)
            
            # Création des URLs pour les requêtes
            tcl_url = f"https://www.tcl.fr/itineraires?date=now&pmr=0&from={encoded_from}&to={encoded_to}"
            tcl_api_url = f"https://carte.tcl.fr/api/itinerary?datetime=now&from={encoded_from}&to={encoded_to}&params=departure,metro,funiculaire,tramway,bus,shuttle,bss,bike,car&walking=1.12&cycling=4.44"

            # En-têtes de la requête
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

            # Récupération des données de transport
            try:
                response = requests.get(tcl_api_url, headers=headers, timeout=10)
            except requests.RequestException:
                st.toast("Erreur lors de la récupération des données de transport.", icon="❌")
                return None, "Trajet indisponible", "Trajet indisponible", "Trajet indisponible", ("❌", "Trajet indisponible")

            duration_public = "Trajet indisponible"
            duration_car = "Trajet indisponible"
            duration_soft = "Trajet indisponible"
            fastest_mode = ("❌", "Trajet indisponible")

            duration_public_min = float('inf')
            duration_car_min = float('inf')
            duration_soft_min = float('inf')

            if response.status_code == 200:
                data = response.json()
                
                # Récupération de la durée du trajet en transport en commun
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
                
                # Récupération de la durée du trajet en voiture
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
                
                # Réupération de la durée du trajet en vélo
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

            # Calcul du mode de transport le plus rapide
            durations = {
                "public": duration_public_min,
                "car": duration_car_min,
                "soft": duration_soft_min,
            }

            min_duration = min(durations.values())

            if min_duration == float('inf'):
                fastest_mode = ("❌", "Trajet indisponible")
            else:
                if min_duration == durations["public"]:
                    fastest_mode = ("🚌", duration_public)
                elif min_duration == durations["car"]:
                    fastest_mode = ("🚗", duration_car)
                elif min_duration == durations["soft"]:
                    fastest_mode = ("🚲", duration_soft)

            if not tcl_url:
                return None, "Trajet indisponible", "Trajet indisponible", "Trajet indisponible", ("❌", "Trajet indisponible")

            return tcl_url, duration_public, duration_car, duration_soft, fastest_mode

    return None, "Trajet indisponible", "Trajet indisponible", "Trajet indisponible", ("❌", "Trajet indisponible")

# Fonction de traitement des restaurants
def process_restaurant(personal_address, personal_latitude, personal_longitude, restaurant):
    tcl_url, duration_public, duration_car, duration_soft, fastest_mode = tcl_api(personal_address, personal_latitude, personal_longitude, restaurant.latitude, restaurant.longitude)
    return (restaurant, tcl_url, fastest_mode)

# Récupération des informations du restaurant sélectionné
def display_restaurant_infos(personal_address, personal_latitude, personal_longitude):
    selected_restaurant = st.session_state.get('selected_restaurant')
    tcl_url, duration_public, duration_car, duration_soft, fastest_mode = tcl_api(personal_address, personal_latitude, personal_longitude, selected_restaurant.latitude, selected_restaurant.longitude)

    if selected_restaurant:
        # Affichage de l'image du restaurant
        st.image(selected_restaurant.image)

        # Commencer la section avec l'image de fond
        st.markdown('<div class="background-section">', unsafe_allow_html=True)
        michelin_stars = display_michelin_stars(selected_restaurant.etoiles_michelin)
        if michelin_stars:
            michelin_stars_html = f'<img src="{michelin_stars}" width="25">'
        else:
            michelin_stars_html = ''
        st.html(f"<h1>{selected_restaurant.nom}   {michelin_stars_html}</h1>")
        
        # Mise en page des informations
        container = st.container()
        col1, col2 = container.columns([0.64, 0.36])

        # Affichage des informations de la colonne 1
        with col1:
            info_container = st.container()
            if info_container.button(icon="📍", label=selected_restaurant.adresse):
                lien_gm = get_google_maps_link(selected_restaurant.adresse)
                webbrowser.open_new_tab(lien_gm)
            if info_container.button(icon="🌐", label="Lien vers Tripadvisor"):
                webbrowser.open_new_tab(selected_restaurant.url_link)
            if info_container.button(icon="📧", label=selected_restaurant.email):
                webbrowser.open_new_tab(f"mailto:{selected_restaurant.email}")
            if info_container.button(icon="📞", label=selected_restaurant.telephone):
                webbrowser.open_new_tab(f"tel:{selected_restaurant.telephone}")
            
            info_supp_container = st.container(border=True)
            info_supp_container.write("**Informations complémentaires**")
            info_supp_container.write(f"**Cuisine :** {selected_restaurant.cuisines}")
            info_supp_container.write(f"**Repas :** {selected_restaurant.repas}")

        # Affichage des informations de la colonne 2
        with col2:
            score_container = st.container(border=True)

            score_container.write("**Notations**")
            stars = display_stars(selected_restaurant.note_globale)
            stars_html = ''.join([f'<img src="{star}" width="20">' for star in stars])
            score_container.html(f"<b>Globale : </b>{stars_html}")
            score_container.write(f"**Qualité Prix :** {selected_restaurant.qualite_prix_note}")
            score_container.write(f"**Cuisine :** {selected_restaurant.cuisine_note}")
            score_container.write(f"**Service :** {selected_restaurant.service_note}")
            score_container.write(f"**Ambiance :** {selected_restaurant.ambiance_note}")
            
            journeys_container = st.container(border=True)
            journeys_container.write("**Temps de trajet**")
            journeys_container.write(f"🚲 {duration_soft}")
            journeys_container.write(f"🚌 {duration_public}")
            journeys_container.write(f"🚗 {duration_car}")
            if tcl_url:
                if journeys_container.button(label="Consulter les itinéraires TCL"):
                    webbrowser.open_new_tab(tcl_url)
            else:
                emoji, fastest_duration = fastest_mode
                bouton_label = f"{emoji} {fastest_duration}"
                journeys_container.button(label=bouton_label, disabled=True)