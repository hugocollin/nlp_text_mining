import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pages.resources.components import Navbar, get_personal_address, display_stars, process_restaurant, add_to_comparator, filter_restaurants_by_radius, display_restaurant_infos
from pages.statistiques import display_restaurant_stats
from db.models import get_all_restaurants
import pydeck as pdk
import webbrowser
import concurrent.futures

# Configuration de la page
st.set_page_config(page_title="SISE Ô Resto - Explorer", page_icon="🍽️", layout="wide")

# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()

# Récupération de tous les restaurants
restaurants = get_all_restaurants(session)

# Récupération de l'adresse personnelle
personal_address, personal_latitude, personal_longitude = get_personal_address()

# Fonction pour afficher le popup d'ajout de restaurant
@st.dialog("Ajouter un restaurant")
def add_restaurant_dialog():
    # Filtrage sur les restaurants non scrappés
    scrapped_restaurants = [restaurant.nom for restaurant in restaurants if not restaurant.scrapped]
    options = ["Sélectionner un restaurant"] + scrapped_restaurants

    # Sélection du restaurant à ajouter
    restaurant_select = st.selectbox(label="Sélectionner un restaurant", label_visibility="collapsed", placeholder="Sélectionner un restaurant", options=options, key="restaurant_select")
    
    # Scapping du restaurant sélectionné
    if st.button(icon="➕", label="Ajouter le restaurant"):
        if restaurant_select != "Sélectionner un restaurant":
            # [TEMP] Code pour scrapper le restaurant sélectionné et ajouter les informations à la base de données
            st.session_state['restaurant_added'] = True
            st.rerun()
        else:
            st.warning("Veuillez sélectionner un restaurant", icon="⚠️")

# Fonction pour afficher le popup d'informations sur un restaurant
@st.dialog("Informations sur le restaurant", width="large")
def restaurant_info_dialog():
    display_restaurant_infos(personal_address, personal_latitude, personal_longitude)

def main():
    # Barre de navigation
    Navbar()

    # Vérification si une adresse personelle a été renseignée
    if not personal_address:
            st.toast("Veuillez définir votre adresse personnelle pour voir les temps de trajet", icon="ℹ️")

    # Initialisation du comparateur dans session_state
    if 'comparator' not in st.session_state:
        st.session_state['comparator'] = []

    # Vérification si un restaurant a été sélectionné pour afficher ses statistiques
    selected_stats = st.session_state.get('selected_stats_restaurant')
    if selected_stats:
        display_restaurant_stats(selected_stats)
        return

    # Titre de la page
    st.title('🔍 Explorer')

    # Mise en page du bouton d'ajout de restaurant
    add_restaurant_btn_col1, add_restaurant_btn_col2 = st.columns([3, 1])

    # Bouton pour ajouter un restaurant
    with add_restaurant_btn_col2:
        if st.button(icon="➕", label="Ajouter un restaurant", key="add_restaurant_btn"):
            add_restaurant_dialog()
    
    # Popup de confirmation d'ajout de restaurant
    if st.session_state.get('restaurant_added'):
        st.toast("Restaurant ajouté avec succès", icon="➕")
        st.session_state['restaurant_added'] = False

    # Création d'une tab
    close_tab, filter_tab, ai_tab = st.tabs(["🔼", "🎨 Filtres", "✨ Discuter avec l'IA"])

    with close_tab:
        st.write("")
    
    with filter_tab:
        # Conteneur pour la recherche et les filtres
        header_container = filter_tab.container(border=True)

        # Mise en page de la recherche et des filtres
        header_col1, header_col2 = header_container.columns(2)
        
        # Colonne pour les filtres
        with header_col1:
            # Récupération des informations des restaurants scrappés
            scrapped_restaurants = [
                {
                    "nom": restaurant.nom,
                    "latitude": restaurant.latitude,
                    "longitude": restaurant.longitude,
                    "etoiles_michelin": restaurant.etoiles_michelin,
                    "note_globale": restaurant.note_globale,
                    "qualite_prix_note": restaurant.qualite_prix_note,
                    "cuisine_note": restaurant.cuisine_note,
                    "service_note": restaurant.service_note,
                    "ambiance_note": restaurant.ambiance_note,
                    "cuisines": restaurant.cuisines,
                    "repas": restaurant.repas
                }
                for restaurant in [restaurant for restaurant in restaurants if restaurant.scrapped]
            ]

            # Checkbox pour activer/désactiver le filtre par rayon
            container = header_col1.container(border=True)
            if personal_address:
                use_radius_filter = container.toggle(label="Recherche par distance autour du domicile", value=False, key="use_radius_filter")
                if use_radius_filter:
                    radius = container.slider("Distance de recherche autour du domicile (en mètres)", min_value=1, max_value=3000, step=1, value=500, key="radius_slider")
                
                    # Filtrage des restaurants par rayon si activé
                    filtered_restaurants = filter_restaurants_by_radius(scrapped_restaurants, personal_latitude, personal_longitude, radius)
                else:
                    radius = 1000000
                    filtered_restaurants = scrapped_restaurants
            else:
                use_radius_filter = container.toggle(label="Recherche par distance autour du domicile", value=False, key="use_radius_filter", disabled=True)
                radius = 1000000
                filtered_restaurants = scrapped_restaurants

            grades_col1, grades_col2 = st.columns(2)

            # Filtre par étoiles Michelin
            container = grades_col1.container(border=True)
            option_map = {
                1: ":material/asterisk:",
                2: ":material/asterisk::material/asterisk:",
                3: ":material/asterisk::material/asterisk::material/asterisk:",
            }
            selected_michelin_stars = container.pills(
                "Étoiles Michelin minimale",
                options=option_map.keys(),
                format_func=lambda option: option_map[option],
                selection_mode="single",
            )

            # Filtre par note globale
            container = grades_col2.container(border=True)
            container.write("Note globale minimale")
            global_rating = [1, 2, 3, 4, 5]
            global_rating_selected = container.feedback("stars", key="filter_global_stars")
            if global_rating_selected is None:
                global_rating_selected = 0

            # Filtre par note qualité-prix
            container = grades_col1.container(border=True)
            quality_price = container.slider(
                label="Note qualité prix minimale",
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                value=0.0,
                key="filter_quality_price"
            )

            # Filtre par temps de trajet
            if personal_address:
                container = st.container(border=True)
                time_travel = container.slider(
                    label="Temps de trajet maximal (en minutes)",
                    min_value=0,
                    max_value=120,
                    step=1,
                    value=120,
                    key="filter_time_travel"
                )
            else:
                container = st.container(border=True)
                time_travel = container.slider(
                    label="Temps de trajet maximal (en minutes)",
                    min_value=0,
                    max_value=120,
                    step=1,
                    value=120,
                    disabled=True,
                    key="filter_time_travel"
                )
        
        with header_col2:

            # Filtre par note cuisine
            container = grades_col2.container(border=True)
            cuisine_note = container.slider(
                label="Note cuisine minimale",
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                value=0.0,
                key="filter_cuisine_note"
            )

            # Filtre par note service
            container = grades_col1.container(border=True)
            service_note = container.slider(
                label="Note service minimale",
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                value=0.0,
                key="filter_service_note"
            )

            # Filtre par note ambiance
            container = grades_col2.container(border=True)
            ambiance_note = container.slider(
                label="Note ambiance minimale",
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                value=0.0,
                key="filter_ambiance_note"
            )

            # Filtre par cuisine
            container = st.container(border=True)
            cuisines = sorted(list(set([c.strip() for restaurant in scrapped_restaurants for c in restaurant["cuisines"].split(',') if c.strip()])))
            selected_cuisines = container.pills(
                label="Cuisine",
                options=cuisines,
                default=[],
                selection_mode = "multi",
                key="filter_cuisines"
            )

            # Filtre par type de repas
            container = st.container(border=True)
            meals = sorted(list(set([m.strip() for restaurant in scrapped_restaurants for m in restaurant["repas"].split(',') if m.strip()])))
            selected_meals = container.pills(
                label="Type de repas",
                options=meals,
                default=[],
                selection_mode = "multi",
                key="filter_meals"
            )

    # Colonne pour le chat avec l'IA [TEMP]
    with ai_tab:
        header_container = st.container(border=True)
        chat_container = header_container.container(height=500)
        if message := header_container.chat_input(placeholder="Rechercher avec l'IA ✨ [disponible ultérieurement]", key="search_restaurant_temp"):
            chat_container.chat_message(avatar="👤", name="User").write(message)
            chat_container.chat_message(avatar="✨", name="AI").write(f"Je ne suis actuellement pas disponible 😢")

    # Mise en page des résultats
    results_display_col1, results_display_col2 = st.columns([3, 2])
    
    # Affichage des résultats
    with results_display_col1:
        # Parallélisation du traitement des restaurants
        with st.spinner("Chargement des restaurants..."):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(process_restaurant, personal_address, personal_latitude, personal_longitude, restaurant)
                    for restaurant in restaurants
                    if restaurant.scrapped
                ]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Filtrage des résultats en fonction des filtres
        filtered_results = []
        for result in results:
            restaurant, tcl_url, fastest_mode = result

            # Filtrage par étoiles Michelin
            if selected_michelin_stars:
                if not (restaurant.etoiles_michelin >= selected_michelin_stars):
                    continue
            
            # Filtrage par note globale
            if not (global_rating[global_rating_selected] <= restaurant.note_globale):
                continue
            
            # Filtrage par note qualité-prix
            if quality_price > 0:
                if restaurant.qualite_prix_note is None or restaurant.qualite_prix_note < quality_price:
                    continue

            # Filtrage par note cuisine
            if cuisine_note > 0:
                if restaurant.cuisine_note is None or restaurant.cuisine_note < cuisine_note:
                    continue

            # Filtrage par note service
            if service_note > 0:
                if restaurant.service_note is None or restaurant.service_note < service_note:
                    continue

            # Filtrage par note ambiance
            if ambiance_note > 0:
                if restaurant.ambiance_note is None or restaurant.ambiance_note < ambiance_note:
                    continue
            
            # Filtrage par temps de trajet
            if tcl_url:
                duration_str = fastest_mode[1]
                if 'h' in duration_str:
                    parts = duration_str.split('h')
                    hours = int(parts[0])
                    minutes = int(parts[1].replace('min', '')) if parts[1] else 0
                    duration = hours * 60 + minutes
                else:
                    duration = int(duration_str.replace('min', ''))
                if not (duration <= time_travel):
                    continue
            
            # Filtrage par cuisine
            if selected_cuisines:
                restaurant_cuisines = [c.strip() for c in restaurant.cuisines.split(',')]
                if not any(cuisine in restaurant_cuisines for cuisine in selected_cuisines):
                    continue
            
            # Filtrage par type de repas
            if selected_meals:
                restaurant_meals = [m.strip() for m in restaurant.repas.split(',')]
                if not any(meal in restaurant_meals for meal in selected_meals):
                    continue
            filtered_results.append(result)

        # Extraction des restaurants filtrés pour la carte
        filtered_restaurants = [
            (
                result[0].nom,
                result[0].latitude,
                result[0].longitude
            )
            for result in filtered_results
            if result[0] is not None
        ]

        # Récupération des coordonnées des restaurants pour la carte
        map_data = []
        for restaurant in filtered_restaurants:
            nom, lat, lon = restaurant
            map_data.append({
                'name': nom,
                'latitude': lat,
                'longitude': lon
            })

        # Filtrage des restaurants par rayon
        if personal_address:
            map_data = filter_restaurants_by_radius(
                map_data,
                personal_latitude,
                personal_longitude,
                radius
            )
            # Obtention des noms des restaurants filtrés
            filtered_names = [restaurant['name'] for restaurant in map_data]
            # Filtrage des résultats en fonction des noms filtrés
            filtered_results = [result for result in filtered_results if result[0].nom in filtered_names]

        # Affichage uniquement des restaurants filtrés
        for result in filtered_results:
            restaurant, tcl_url, fastest_mode = result
            container = st.container(border=True)
            col1, col2, col3, col4, col5 = container.columns([3.5, 1, 1, 1, 2.5])
            
            # Affichage des informations du restaurant
            with col1:
                col1.write(restaurant.nom)
                stars = display_stars(restaurant.note_globale)
                col1.image(stars, width=20)

            # Affichage du bouton d'information
            with col2:
                if col2.button(label="ℹ️", key=f"info_btn_{restaurant.id_restaurant}"):
                    st.session_state['selected_restaurant'] = restaurant
                    restaurant_info_dialog()
            
            # Affichage du bouton de statistiques
            with col3:
                if col3.button("📊", key=f"stats_btn_{restaurant.id_restaurant}"):
                    st.session_state['selected_stats_restaurant'] = restaurant
                    st.rerun()

            # Affichage du bouton de comparaison
            with col4:
                if col4.button("🆚", key=f"compare_btn_{restaurant.id_restaurant}"):
                    add_to_comparator(restaurant)
            
            # Affichage du bouton de trajet
            with col5:
                emoji, fastest_duration = fastest_mode
                bouton_label = f"{emoji} {fastest_duration}"
                button_key = f"trajet_btn_{restaurant.id_restaurant}"
                if tcl_url:
                    if col5.button(bouton_label, key=button_key):
                        webbrowser.open_new_tab(tcl_url)
                else:
                    col5.button(bouton_label, key=button_key, disabled=True)
            
        # Affichage si aucun restaurant n'est trouvé
        if not filtered_results:
            st.info("ℹ️ Aucun restaurant trouvé, essayez de modifier vos critères de recherche.")
    
    # Affichage de la carte
    with results_display_col2:
        with st.spinner("Chargement de la carte..."):
            # Mise en forme du radius et de la couleur du domicile
            if radius == 1000000:
                radius = 25
                color = '[0, 0, 255]'
            else:
                color = '[0, 0, 255, 100]'

            # Ajout des coordonnées du domicile s'il est défini
            if personal_address:
                latitude = personal_latitude
                longitude = personal_longitude
                map_data.append({
                    'name': 'Domicile',
                    'latitude': personal_latitude,
                    'longitude': personal_longitude
                })
            else:
                latitude, longitude = 45.7640, 4.8357 # Coordonnées de Lyon

            view_state = pdk.ViewState(
                latitude=latitude,
                longitude=longitude,
                zoom=12,
                pitch=0
            )

            # Paramètres du point du domicile (bleu)
            home_layer = pdk.Layer(
                'ScatterplotLayer',
                data=[point for point in map_data if point['name'] == 'Domicile'],
                get_position='[longitude, latitude]',
                get_color=color,
                get_radius=radius,
                pickable=True,
                auto_highlight=True
            )

            # Paramètres des points des restaurants (rouge)
            restaurants_layer = pdk.Layer(
                'ScatterplotLayer',
                data=[point for point in map_data if point['name'] != 'Domicile'],
                get_position='[longitude, latitude]',
                get_color='[255, 0, 0]',
                get_radius=25,
                pickable=True,
                auto_highlight=True
            )

            # Ajout des points à afficher sur la carte
            layers = [restaurants_layer, home_layer]

            # Paramètres des infos-bulles
            tooltip = {
                "html": "<b>{name}</b>",
                "style": {
                    "backgroundColor": "white",
                    "color": "black"
                }
            }

            # Affichage de la carte
            deck = pdk.Deck(
                layers=layers,
                initial_view_state=view_state,
                tooltip=tooltip,
                map_style='mapbox://styles/mapbox/light-v11'
            )

            # Affichage de la carte
            st.pydeck_chart(deck)

if __name__ == '__main__':
    main()