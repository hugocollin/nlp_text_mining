import streamlit as st
import urllib.parse
import requests
import math
import base64
import pydeck as pdk
import functools
import litellm
import numpy as np
import time
import tqdm
import datetime
from zoneinfo import ZoneInfo
from src.db.models import Chunk, get_session, init_db
from sqlalchemy.orm import Session, sessionmaker
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from typing import List, Dict, Tuple
from pathlib import Path
from ecologits import EcoLogits
from litellm import ModelResponse
from src.pipeline import Transistor

# Instanciation d'un transistor
transistor = Transistor()

# Fonction pour afficher la barre de navigation
def Navbar():
    with st.sidebar:
        st.page_link('app.py', label='Accueil', icon='🏠')
        st.page_link('pages/explorer.py', label='Explorer', icon='🔍')
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

# Fonction pour obtenir le prix moyen d'un restaurant
def get_price_symbol(prix_min, prix_max):
    if prix_min and prix_max:
        prix_avg = (prix_min + prix_max) / 2

        if prix_avg < 20:
            return ':material/euro_symbol:'
        elif prix_avg < 30:
            return ':material/euro_symbol::material/euro_symbol:'
        elif prix_avg < 50:
            return ':material/euro_symbol::material/euro_symbol::material/euro_symbol:'
        else:
            return ':material/euro_symbol::material/euro_symbol::material/euro_symbol::material/euro_symbol:'
    else:
        return 'Non disponible'

# Fonction pour obtenir le temps actuel
def get_datetime():
    # Définition de la timezone
    tz = ZoneInfo('Europe/Paris')
    
    # Récupération de la date actuelle
    current_datetime = datetime.datetime.now(tz)

    # Récupération du jour actuel
    current_day_index = current_datetime.weekday()
    fr_days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    current_day = fr_days[current_day_index]
    
    return current_datetime, current_day

# Fonction pour construire les horaires d'ouverture d'un restaurant
def construct_horaires(horaires_str):
    if horaires_str is None:
        return {}
    fr_days = {
        'lundi': 'Lundi',
        'mardi': 'Mardi',
        'mercredi': 'Mercredi',
        'jeudi': 'Jeudi',
        'vendredi': 'Vendredi',
        'samedi': 'Samedi',
        'dimanche': 'Dimanche'
    }

    # Création d'un dictionnaire pour stocker les horaires
    horaires_dict = {jour: [] for jour in fr_days.values()}
    jours = horaires_str.split(";")
    jours = [jour.strip() for jour in jours if jour.strip()]

    # Parcours des jours
    for jour in jours:
        jour_nom, plages = jour.split(": ")

        # Si le restaurant est fermé
        if plages.lower() == "fermé":
            horaires_dict[jour_nom] = []
            continue
        plages = plages.split(", ")

        # Parcours des plages horaires
        for plage in plages:
            start_str, end_str = plage.split("-")
            start_time = datetime.datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.datetime.strptime(end_str, '%H:%M').time()
            
            # Gestion des horaires de nuit
            if end_time <= start_time:
                horaires_dict[jour_nom].append((start_time, datetime.time(23, 59)))
                
                index = list(fr_days.values()).index(jour_nom)
                jour_suivant = list(fr_days.values())[(index + 1) % 7]
                
                horaires_dict[jour_suivant].append((datetime.time(0, 0), end_time))
            else:
                horaires_dict[jour_nom].append((start_time, end_time))
    
    # Tri des horaires par ordre croissant
    for jour in horaires_dict:
        horaires_dict[jour].sort(key=lambda x: x[0])
    
    return horaires_dict

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

# Fonction pour afficher le texte progressivement
def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.03)

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
    tcl_url, _duration_public, _duration_car, _duration_soft, fastest_mode = tcl_api(personal_address, personal_latitude, personal_longitude, restaurant.latitude, restaurant.longitude)
    return (restaurant, tcl_url, fastest_mode)

# Récupération des informations du restaurant sélectionné
def display_restaurant_infos( personal_address, personal_latitude, personal_longitude):
    # Récupération de restaurant sélectionné
    selected_restaurant = st.session_state.get('selected_restaurant')

    # Récupération des informations de trajet
    tcl_url, duration_public, duration_car, duration_soft, fastest_mode = tcl_api(personal_address, personal_latitude, personal_longitude, selected_restaurant.latitude, selected_restaurant.longitude)

    if selected_restaurant:
        # Affichage de l'image du restaurant
        st.html(f"""
        <style>
        .background-section {{
            background-image: url("{selected_restaurant.image}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            padding: 20px;
            height: 300px;
            border-radius: 10px;
        }}
        </style>
        """)
        st.markdown('<div class="background-section">', unsafe_allow_html=True)

        # Affichage des étoiles Michelin
        michelin_stars = display_michelin_stars(selected_restaurant.etoiles_michelin)
        michelin_stars_html = ''
        if michelin_stars:
            if selected_restaurant.etoiles_michelin == 1:
                michelin_stars_html = f'<img src="{michelin_stars}" width="25">'
            elif selected_restaurant.etoiles_michelin == 2:
                michelin_stars_html = f'<img src="{michelin_stars}" width="45">'
            elif selected_restaurant.etoiles_michelin == 3:
                michelin_stars_html = f'<img src="{michelin_stars}" width="65">'
            
        st.html(f"<h1>{selected_restaurant.nom}   {michelin_stars_html}</h1>")

        # Tabs pour les informations
        presentation, avis = st.tabs(["🖼️ Présentation", "📝 Avis"])
        
        with presentation:
            # Mise en page des informations
            col1, col2 = st.columns([0.64, 0.36])

            # Affichage des informations de la colonne 1
            with col1:
                info_container = st.container()
                # Préparation des boutons
                if selected_restaurant.adresse:
                    gm = f"📍 {selected_restaurant.adresse}"
                    gm_link = selected_restaurant.google_map
                    disabled_adresse = ''
                else:
                    gm = "📍 Non disponible"
                    gm_link = "None"
                    disabled_adresse = 'disabled'

                if selected_restaurant.url_link:
                    tripadvisor = "🌐 Lien vers Tripadvisor"
                    tripadvisor_link = selected_restaurant.url_link
                    disabled_tripadvisor = ''
                else:
                    tripadvisor = "🌐 Non disponible"
                    tripadvisor_link = "None"
                    disabled_tripadvisor = 'disabled'

                if selected_restaurant.email:
                    email = f"📧 {selected_restaurant.email}"
                    email_link = f"mailto:{selected_restaurant.email}"
                    disabled_email = ''
                else:
                    email = "📧 Non disponible"
                    email_link = "None"
                    disabled_email = 'disabled'

                if selected_restaurant.telephone:
                    tel = f"📞 {selected_restaurant.telephone}"
                    tel_link = f"tel:{selected_restaurant.telephone}"
                    disabled_tel = ''
                else:
                    tel = "📞 Non disponible"
                    tel_link = "None"
                    disabled_tel = 'disabled'

                # Affichage des boutons pour les liens
                info_container.markdown(f'''
                    <style>
                        .custom-button {{
                            display: inline-block;
                            padding: 6px 12px;
                            margin-bottom: 15px;
                            color: #31333e;
                            border: 1px solid #d6d6d8;
                            border-radius: 8px;
                            cursor: pointer;
                            background-color: transparent;
                            transition: background-color 0.3s;
                        }}
                        .custom-button:hover {{
                            color: #FF4B4B;
                            border-color: #FF4B4B;
                        }}
                        .custom-button:active {{
                            background-color: #FF4B4B;
                        }}
                        .custom-button[disabled] {{
                            color: #adadb2;
                            cursor: not-allowed;
                        }}
                        @media (prefers-color-scheme: dark) {{
                            .custom-button {{
                                color: #fafafa;
                                border-color: #3e4044;
                                background-color: #14171f;
                            }}
                            .custom-button[disabled] {{
                                color: #6d6e71;
                                border-color: #3e4044;
                                background-color: transparent;
                            }}
                        }}
                    </style>
                    <div>
                        <a href="{gm_link}" target="_blank" style="text-decoration: none;">
                            <button class="custom-button" {disabled_adresse}>{gm}</button>
                        </a>
                    </div>
                    <div>
                        <a href="{tripadvisor_link}" target="_blank" style="text-decoration: none;">
                            <button class="custom-button" {disabled_tripadvisor}>{tripadvisor}</button>
                        </a>
                    </div>
                    <div>
                        <a href="{email_link}" target="_blank" style="text-decoration: none;">
                            <button class="custom-button" {disabled_email}>{email}</button>
                        </a>
                    </div>
                    <div>
                        <a href="{tel_link}" target="_blank" style="text-decoration: none;">
                            <button class="custom-button" {disabled_tel}>{tel}</button>
                        </a>
                    </div>
                ''', unsafe_allow_html=True)

                # Affichage des horaires d'ouverture
                horaires_container = st.container(border=True)
                horaires_container.write("**Horaires d'ouverture**")

                current_datetime, current_day = get_datetime()
                horaires_dict = construct_horaires(selected_restaurant.horaires)
                
                if not selected_restaurant.horaires:
                    horaires_container.info("Les horaires d'ouverture ne sont pas disponibles", icon="ℹ️")
                else:
                    plages_du_jour = horaires_dict.get(current_day, [])
                    if not plages_du_jour:
                        horaires_container.error("Fermé")
                    else:
                        ouvert = False
                        current_time = current_datetime.time()
                        for start, end in plages_du_jour:
                            if start <= end:
                                if start <= current_time <= end:
                                    ouvert = True
                                    break
                            else:
                                if current_time >= start or current_time <= end:
                                    ouvert = True
                                    break
                        if ouvert:
                            horaires_container.success("Ouvert")
                        else:
                            horaires_container.error("Fermé")

                    # Transformation des horaires en dictionnaire
                    horaires_dict = {}
                    parties = selected_restaurant.horaires.split(";")
                    for partie in parties:
                        if partie.strip():
                            jour, heures = partie.split(": ", 1)
                            horaires_dict[jour.strip()] = heures.strip()
                    
                    # Affichage des horaires d'ouverture
                    for jour in ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]:
                        if jour in horaires_dict:
                            heures = horaires_dict[jour]
                            if heures.lower() == "fermé":
                                horaires_container.write(f"- {jour} : Fermé")
                            else:
                                periods = [p.strip() for p in heures.split(",")]
                                formatted_periods = []
                                for p in periods:
                                    debut, fin = p.split("-", 1)
                                    debut = debut.strip().replace(":", "h")
                                    fin = fin.strip().replace(":", "h")
                                    formatted_periods.append(f"{debut} - {fin}")
                                horaires_container.write(f"- {jour} : {', '.join(formatted_periods)}")
                        else:
                            horaires_container.write(f"- {jour} : Horaires non disponibles")

                # Affichage du résumé du restaurant
                resume_container = st.container(border=True)
                resume_container.markdown("**Avis général**", help="✨ Ce texte a été généré automatiquement à partir des avis des utilisateurs sur Tripadvisor, grâce à un processus combinant le traitement du langage naturel (NLP) et l'intelligence artificielle (IA)")
                resume_container.write(f"{selected_restaurant.resume_avis}")

                # Affichage des informations complémentaires
                info_supp_container = st.container(border=True)
                info_supp_container.write("**Informations complémentaires**")
                if selected_restaurant.cuisines:
                    info_supp_container.write(f"**Cuisine :** {selected_restaurant.cuisines}")
                else:
                    info_supp_container.write("**Cuisine :** Non disponible")
                if selected_restaurant.repas:
                    info_supp_container.write(f"**Repas :** {selected_restaurant.repas}")
                else:
                    info_supp_container.write("**Repas :** Non disponible")
                if selected_restaurant.fonctionnalite:
                    functionalities = selected_restaurant.fonctionnalite.replace(';', ', ').rstrip(', ')
                    info_supp_container.write(f"**Fonctionnalités :** {functionalities}")
                else:
                    info_supp_container.write("**Fonctionnalités :** Non disponible")

            # Affichage des informations de la colonne 2
            with col2:
                # Affichage du rang
                rank_container = st.container(border=True)
                if selected_restaurant.rank == 1:
                    rank_container.markdown(f"**Rang :** {selected_restaurant.rank}<sup>er</sup> restaurant", unsafe_allow_html=True)
                else:
                    rank_container.markdown(f"**Rang :** {selected_restaurant.rank}<sup>ème</sup> restaurant", unsafe_allow_html=True)

                # Affichage de la fourchette de prix
                prix_container = st.container(border=True)
                prix_symbol = get_price_symbol(selected_restaurant.prix_min, selected_restaurant.prix_max)
                prix_container.write(f"**Prix :** {prix_symbol}")
                
                # Affichage des notations
                score_container = st.container(border=True)
                score_container.write("**Notations**")
                stars = display_stars(selected_restaurant.note_globale)
                stars_html = ''.join([f'<img src="{star}" width="20">' for star in stars])
                score_container.html(f"<b>Globale : </b>{stars_html}")
                if selected_restaurant.qualite_prix_note:
                    score_container.write(f"**Qualité Prix :** {selected_restaurant.qualite_prix_note}")
                else:
                    score_container.write("**Qualité Prix :** Non disponible")
                if selected_restaurant.cuisine_note:
                    score_container.write(f"**Cuisine :** {selected_restaurant.cuisine_note}")
                else:
                    score_container.write("**Cuisine :** Non disponible")
                if selected_restaurant.service_note:
                    score_container.write(f"**Service :** {selected_restaurant.service_note}")
                else:
                    score_container.write("**Service :** Non disponible")
                if selected_restaurant.ambiance_note:
                    score_container.write(f"**Ambiance :** {selected_restaurant.ambiance_note}")
                else:
                    score_container.write("**Ambiance :** Non disponible")
                
                # Affichage des temps de trajet
                journeys_container = st.container(border=True)
                journeys_container.write("**Temps de trajet**")
                journeys_container.write(f"🚲 {duration_soft}")
                journeys_container.write(f"🚌 {duration_public}")
                journeys_container.write(f"🚗 {duration_car}")
                if tcl_url:
                    journeys_container.markdown(f'''
                        <a href="{tcl_url}" target="_blank" style="text-decoration: none;">
                            <button class="custom-button">Consulter les itinéraires TCL</button>
                        </a>
                    ''', unsafe_allow_html=True)
                else:
                    emoji, fastest_duration = fastest_mode
                    bouton_label = f"{emoji} {fastest_duration}"
                    journeys_container.button(label=bouton_label, disabled=True)
                
                # Définition de la vue de la carte
                view = pdk.ViewState(
                    latitude=selected_restaurant.latitude,
                    longitude=selected_restaurant.longitude,
                    zoom=13,
                    pitch=0
                )

                # Définition de la couche de la carte
                layer = pdk.Layer(
                    'ScatterplotLayer',
                    data=[{'position': [selected_restaurant.longitude, selected_restaurant.latitude]}],
                    get_position='position',
                    get_color='[255, 0, 0]',
                    get_radius=25,
                    pickable=True,
                    auto_highlight=True
                )

                # Paramètres de l'infos-bulle
                tooltip = {
                    "html": f"<b>{selected_restaurant.nom}</b>",
                    "style": {
                        "backgroundColor": "white",
                        "color": "black"
                    }
                }

                # Définition du rendu PyDeck
                deck = pdk.Deck(
                    layers=layer,
                    initial_view_state=view,
                    tooltip=tooltip,
                    map_style='mapbox://styles/mapbox/light-v11'
                )

                # Affichage de la carte
                st.pydeck_chart(deck)

        with avis:
            # Initialisation du nombre de reviews à afficher
            if 'display_count' not in st.session_state:
                st.session_state['display_count'] = 10

            # Récupération des avis
            review = transistor.get_user_and_review_from_restaurant_id( selected_restaurant.id_restaurant)

            # Mise en page des informations
            col1, col2 = st.columns(2)

            # Affichage de la colonne de commentaires
            with col1:
                with st.container(height=1000, border=False):
                    for _i, r in enumerate(review[:st.session_state['display_count']]):
                        comment_container = st.container(border=True)
                        comment_col1, comment_col2 = comment_container.columns([0.6, 0.4])
                        with comment_col1:
                            st.markdown(f"**👤 {r[0].user_name}**", help=f"Nombre de contribution(s) : {r[0].num_contributions}")
                            stars = display_stars(r[1].rating)
                            stars_html = ''.join([f'<img src="{star}" width="20">' for star in stars])
                            st.html(stars_html)

                        with comment_col2:
                            st.write(f"📅 ***{r[1].date_review}***")
                            visit_mapping = {
                                "none": "",
                                "No information": "",
                                "business": "💼 Travail",
                                "couples": "❤️ Couple",
                                "family": "👨‍👩‍👧‍👦 Famille",
                                "friends": "👫 Amis",
                                "solo": "🧍 Seul"
                            }
                            st.write(f"{visit_mapping.get(r[1].type_visit, r[1].type_visit)}")
                        
                        comment_container.write(f"**{r[1].title_review}**")
                        comment_container.write(r[1].review_text)
                
                    # Bouton pour charger plus de reviews
                    if st.session_state['display_count'] < len(review):
                        if st.button("🔄️ Charger plus d'avis"):
                            st.session_state['display_count'] += 10
                            st.rerun(scope="fragment")
            
            with col2:
                # Affichage du nombre d'avis
                nb_avis_container = st.container(border=True)

                nb_avis_container.write(f"**Nombre d'avis : {len(review)}**")

                # Affichage du top contributeurs
                top_contrib_container = st.container(border=True)

                top_contrib_container.write("**Top contributeurs**")
                user_reviews_count = {}
                for user, _ in review:
                    user_reviews_count[user.user_profile] = user_reviews_count.get(user.user_profile, 0) + 1
                top_users = sorted(user_reviews_count.items(), key=lambda x: x[1], reverse=True)
                
                for rank, (user, count) in enumerate(top_users[:3], start=1):
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
                    top_contrib_container.write(f"{medal} 👤 {user} : {count} avis")

                # Affichage de la répartition des notes
                marks_container = st.container(border=True)

                marks_container.write("**Répartition des notes**")
                rating_counts = {}
                for _, r in review:
                    rating_counts[r.rating] = rating_counts.get(r.rating, 0) + 1
                marks_container.bar_chart(rating_counts, horizontal=True, color="#f6c944")

                # Affichage de la répartition des types de visite
                type_visit_container = st.container(border=True)

                type_visit_container.write("**Répartition des types de visite**")
                type_visit_counts = {}
                visit_mapping = {
                    "none": "Inconnue",
                    "No information": "Inconnue",
                    "business": "Travail",
                    "couples": "Couple",
                    "family": "Famille",
                    "friends": "Amis",
                    "solo": "Seul"
                }
                for _, r in review:
                    mapped_visit = visit_mapping.get(r.type_visit, r.type_visit)
                    type_visit_counts[mapped_visit] = type_visit_counts.get(mapped_visit, 0) + 1
                type_visit_container.bar_chart(type_visit_counts, horizontal=True, color="#f6c944")

                # Affichage de l'évolution du nombre d'avis dans le temps
                month_container = st.container(border=True)

                month_container.write("**Évolution du nombre d'avis dans le temps**")
                month_counts = {}
                for _, r in review:
                    month = r.date_review.strftime("%Y-%m")
                    month_counts[month] = month_counts.get(month, 0) + 1
                month_container.bar_chart(month_counts, color="#f6c944")

# Fonction pour mesurer le temps de réponse de l'IA
def measure_latency(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        result = func(self, *args, **kwargs)
        end_time = time.time()
        latency = end_time - start_time
        self.last_latency = latency
        return result
    return wrapper

# Classe pour découper le texte en chunks et ajouter les embeddings à la base de données
class BDDChunks:
    # Initialise une instance de BDDChunks
    def __init__(self, embedding_model: str):
        self.embedding_model = embedding_model
        self.embeddings = SentenceTransformer(self.embedding_model)
        self.session: Session = get_session(init_db())

    # Fonction de découpage du texte en chunks de taille spécifiée
    def split_text_into_chunks(self, corpus: str) -> list[str]:
        chunks = corpus.split('|')
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        return chunks

    # Fonction pour ajouter les embeddings des chunks à la base de données
    def add_embeddings(self, list_chunks: list[str], batch_size: int = 100) -> None:
        for i in tqdm(range(0, len(list_chunks), batch_size), desc="Ajout des embeddings"):
            batch = list_chunks[i:i + batch_size]
            for chunk in batch:
                embedding = self.embeddings.encode(chunk).tolist()
                new_chunk = Chunk(text=chunk, embedding=embedding)
                self.session.add(new_chunk)
            self.session.commit()

    # Fonction pour exécuter le processus complet de découpage et ajout des embeddings
    def __call__(self, corpus: str) -> None:
        chunks = self.split_text_into_chunks(corpus=corpus)
        self.add_embeddings(list_chunks=chunks)

# Classe pour effectuer un processus RAG augmenté
class AugmentedRAG:
    # Initialise la classe AugmentedRAG avec les paramètres fournis
    def __init__(
        self,
        generation_model: str,
        role_prompt: str,
        bdd_chunks,
        max_tokens: int,
        temperature: float,
        top_n: int = 2,
    ) -> None:
        self.llm = generation_model
        self.bdd = bdd_chunks
        self.top_n = top_n
        self.role_prompt = role_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.engine = init_db()
        EcoLogits.init(providers="litellm", electricity_mix_zone="FRA")

    # Fonction pour calculer la similarité cosinus entre deux vecteurs
    def get_cosim(self, a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def get_top_similarity(
        self,
        embedding_query: np.ndarray,
        embedding_chunks: List[np.ndarray],
        corpus: List[str],
    ) -> List[str]:
        cos_sim_list = np.array(
            [self.get_cosim(embedding_query, emb) for emb in embedding_chunks]
        )
        top_indices = np.argsort(cos_sim_list)[-self.top_n:][::-1]
        return [corpus[i] for i in top_indices]
    
    # Fonction pour extraire l'utilisation énergétique et le GWP de la réponse du modèle
    def _get_energy_usage(self, response: ModelResponse) -> Tuple[float, float]:
        energy_usage = getattr(response.impacts.energy.value, "min", response.impacts.energy.value)
        gwp = getattr(response.impacts.gwp.value, "min", response.impacts.gwp.value)
        return energy_usage, gwp
    
    # Fonction pour construire un prompt pour l'IA
    def build_prompt(
        self, context: List[str], history: List[Dict[str, str]], query: str
    ) -> List[Dict[str, str]]:
        context_joined = "\n".join(context)
        system_prompt = self.role_prompt
        history_prompt = "\n".join(
            [f"{msg['role'].capitalize()}: {msg['content']}" for msg in history]
        )
        context_prompt = f"""
        Tu disposes de la section "Contexte" pour t'aider à répondre aux questions.
        # Contexte: 
        {context_joined}
        """
        query_prompt = f"""
        # Question:
        {query}

        # Réponse:
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": history_prompt},
            {"role": "system", "content": context_prompt},
            {"role": "user", "content": query_prompt},
        ]
    
    # Fonction pour générer une réponse à partir d'un prompt
    @measure_latency
    def _generate(self, prompt_dict: List[Dict[str, str]]) -> ModelResponse:
        response = litellm.completion(
            model=f"mistral/{self.llm}",
            messages=prompt_dict,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return response
    
    # Fonction pour calculer le coût d'une requête en fonction du nombre de tokens d'entrée et de sortie
    def _get_price_query(self, llm_name: str, input_tokens: int, output_tokens: int) -> float:
        pricing = {
            "mistral-large-latest": {"input": 1.95, "output": 5.85}
        }
        if llm_name not in pricing:
            raise ValueError(f"LLM {llm_name} not found in pricing database.")
        cost_input = (input_tokens / 1_000_000) * pricing[llm_name]["input"]
        cost_output = (output_tokens / 1_000_000) * pricing[llm_name]["output"]
        return cost_input + cost_output
    
    # Fonction pour appeler le modèle LLM avec un prompt donné et retourner la réponse avec les métriques
    def call_model(self, prompt_dict: List[Dict[str, str]]) -> Dict[str, any]:
        chat_response: ModelResponse = self._generate(prompt_dict=prompt_dict)
        input_tokens = chat_response.usage.prompt_tokens
        output_tokens = chat_response.usage.completion_tokens
        euro_cost = self._get_price_query(self.llm, input_tokens, output_tokens)
        energy_usage, gwp = self._get_energy_usage(chat_response)
        response_text = str(chat_response.choices[0].message.content)
        return {
            "response": response_text,
            "latency": getattr(self, 'last_latency', 0),
            "euro_cost": euro_cost,
            "energy_usage": energy_usage,
            "gwp": gwp
        }
    
    # Fonction pour traiter une requête et retourner une réponse basée sur l'historique fourni et la base de données
    def __call__(self, query: str, history: List[Dict[str, str]]) -> Dict[str, any]:
        SessionLocal = sessionmaker(bind=self.engine)
        session = SessionLocal()
        try:
            chunks = session.query(Chunk).all()
            chunks_embeddings = [np.array(chunk.embedding) for chunk in chunks]
            chunks_texts = [chunk.text for chunk in chunks]
            query_embedding = self._get_embedding(query)
            similarities = [self.get_cosim(query_embedding, emb) for emb in chunks_embeddings]
            top_indices = np.argsort(similarities)[-self.top_n:][::-1]
            relevant_chunks = [chunks_texts[i] for i in top_indices]
            prompt_rag = self.build_prompt(
                context=relevant_chunks,
                history=history,
                query=query
            )
            response = self.call_model(prompt_rag)

            return response

        finally:
            session.close()
    
    # Fonction pour calculer la similarité cosinus entre deux vecteurs
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    # Fonction pour obtenir l'embedding d'un texte donné
    def _get_embedding(self, text: str) -> np.ndarray:
        model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        embedding = model.encode(text)
        return embedding
    
# Fonction pour instancier BDDChunks
def instantiate_bdd() -> BDDChunks:
    # Instanciation de la classe BDDChunks
    bdd_chunks = BDDChunks(embedding_model="paraphrase-MiniLM-L6-v2")


    session = transistor.session

    try:
        # Supprimer les chunks existants pour éviter les doublons ou erreurs de type
        session.query(Chunk).delete()
        session.commit()

        # Récupération de tous les restaurants
        restaurants = transistor.get_all_restaurants()

        # Filtrage pour exclure les restaurants scrappés
        scrapped_restaurants = [restaurant for restaurant in restaurants if restaurant.scrapped]

        corpus = []

        for restaurant in scrapped_restaurants:
            restaurant_info = (
                f"Nom du restaurant : {restaurant.nom} | "
                f"Adresse du restaurant {restaurant.nom} : {restaurant.adresse} | "
                f"Lien TripAdvisor du restaurant {restaurant.nom} : {restaurant.url_link} | "
                f"Email du restaurant {restaurant.nom} : {restaurant.email} | "
                f"Téléphone du restaurant {restaurant.nom} : {restaurant.telephone} | "
                f"Horaires du restaurant {restaurant.nom} : {restaurant.horaires} | "
                f"Résumé de l'avis du restaurant {restaurant.nom} : {restaurant.resume_avis} | "
                f"Type de cuisine du restaurant {restaurant.nom} : {restaurant.cuisines} | "
                f"Type de repas du restaurant {restaurant.nom} : {restaurant.repas} | "
                f"Fonctionnalités du restaurant {restaurant.nom} : {restaurant.fonctionnalite} | "
                f"Rang du restaurant {restaurant.nom} : {restaurant.rank} | "
                f"Prix moyen du restaurant {restaurant.nom} : {restaurant.prix_min} - {restaurant.prix_max} | "
                f"Étoiles Michelin du restaurant {restaurant.nom} : {restaurant.etoiles_michelin} | "
                f"Note globale du restaurant {restaurant.nom} : {restaurant.note_globale} | "
                f"Note de cuisine du restaurant {restaurant.nom} : {restaurant.cuisine_note} | "
                f"Note de service du restaurant {restaurant.nom} : {restaurant.service_note} | "
                f"Note de qualité prix du restaurant {restaurant.nom} : {restaurant.qualite_prix_note} | "
                f"Note d'ambiance du restaurant {restaurant.nom} : {restaurant.ambiance_note} | "
            )
            corpus.append(restaurant_info)

        # Combiner tous les segments de texte en une seule chaîne
        corpus_combined = "\n".join(corpus)

        # Ajouter les embeddings en utilisant la classe BDDChunks
        bdd_chunks(corpus=corpus_combined)

    finally:
        session.close()

    return bdd_chunks