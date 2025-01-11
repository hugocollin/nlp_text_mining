import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pages.resources.components import Navbar, get_personnal_address, get_coordinates, display_michelin_stars, display_stars, process_restaurant, get_restaurant_coordinates, get_google_maps_link, tcl_api, add_to_comparator, filter_restaurants_by_radius, display_restaurant_infos
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
personal_address = get_personnal_address()

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
    display_restaurant_infos(personal_address)

def main():
    # Barre de navigation
    Navbar()

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

    # Conteneur pour la recherche et les filtres
    header_container = st.container(border=True)

    # Mise en page de la recherche et des filtres
    header_col1, header_col2 = header_container.columns(2)

    # Colonne pour la recherche
    with header_col1:
        # Filtrage sur les restaurants scrappés
        scrapped_restaurants = [restaurant for restaurant in restaurants if restaurant.scrapped]
        
        # Checkbox pour activer/désactiver le filtre par rayon
        if personal_address:
            use_radius_filter = header_col1.checkbox(label="Activer le filtre de recherche par distance autour du domicile", value=False, key="use_radius_filter")
            if use_radius_filter:
                radius = header_col1.slider("Distance de recherche autour du domicile (m)", min_value=1, max_value=3000, step=1, value=500, key="radius_slider")
            else:
                radius = 1000000
        else:
            use_radius_filter = header_col1.checkbox(label="Activer le filtre de recherche par distance autour du domicile", value=False, key="use_radius_filter", disabled=True)
            radius = 1000000

        # Filtrage des restaurants par rayon si activé
        if use_radius_filter and personal_address:
            center_coords = get_coordinates(personal_address)
            if center_coords:
                center_lat, center_lon = center_coords
                
                # Récupération des coordonnées des restaurants scrappés
                restaurant_coords = get_restaurant_coordinates([(r.nom, r.adresse) for r in scrapped_restaurants])
                
                # Filtrage des restaurants dans le rayon
                restaurant_coords_filtered = filter_restaurants_by_radius(restaurant_coords, center_lat, center_lon, radius)
                
                # Obtention des noms des restaurants filtrés
                filtered_names = [restaurant['name'] for restaurant in restaurant_coords_filtered]
                
                # Filtrage des restaurants scrappés par les noms filtrés
                filtered_restaurants = [r for r in scrapped_restaurants if r.nom in filtered_names]
            else:
                filtered_restaurants = scrapped_restaurants
        else:
            filtered_restaurants = scrapped_restaurants

        # Construction de la liste des noms pour la multiselect
        restaurant_names = [restaurant.nom for restaurant in filtered_restaurants]
        options = ["Sélectionner un restaurant"] + restaurant_names

        # Création du multiselect avec les options filtrées
        search_restaurant = header_col1.multiselect(label="Rechercher un restaurant", label_visibility="collapsed", placeholder="Rechercher un restaurant", options=options, key="search_restaurant")

        # [TEMP]
        header_col1.text_input(label="Rechercher avec l'IA", label_visibility="collapsed", placeholder="Rechercher avec l'IA ✨ [disponible ultérieurement]", key="search_restaurant_temp", disabled=True)
    # Colonne pour les filtres
    with header_col2:

        # [TEMP] Ajouter des filtres
        header_col2.write("[Les filtres seront ajoutés ultérieurement]")

    # Mise en page des résultats
    results_display_col1, results_display_col2 = st.columns([3, 2])
    
    # Affichage des résultats
    with results_display_col1:
        if not personal_address:
            st.toast("Veuillez définir votre adresse personnelle pour voir les temps de trajet", icon="ℹ️")

        # Parallélisation du traitement des restaurants
        with st.spinner("Chargement des restaurants..."):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_restaurant, personal_address, restaurant) for restaurant in restaurants if restaurant.scrapped]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Filtrage des résultats en fonction des restaurants sélectionnés
        if search_restaurant:
            filtered_results = [result for result in results if result[0].nom in search_restaurant]
        else:
            filtered_results = results

        # Extraction des restaurants filtrés pour la carte
        filtered_restaurants = [(result[0].nom, result[0].adresse) for result in filtered_results if result[0] is not None]

        # Récupérer les coordonnées des restaurants filtrés
        restaurant_coords = get_restaurant_coordinates(filtered_restaurants)

        # Filtrer les restaurants par rayon
        if personal_address:
            center_lat, center_lon = get_coordinates(personal_address)
            if center_lat and center_lon:
                restaurant_coords_filtered = filter_restaurants_by_radius(restaurant_coords, center_lat, center_lon, radius)
                # Obtenir les noms des restaurants filtrés
                filtered_names = [restaurant['name'] for restaurant in restaurant_coords_filtered]
                # Filtrer les résultats en fonction des noms filtrés
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

            # Affichage du bouton d'informations
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
            # Récupération des coordonnées géographiques des restaurants
            map_data = get_restaurant_coordinates(filtered_restaurants)

            # Mise en forme du radius et de la couleur du domicile
            if radius == 1000000:
                radius = 25
                color = '[0, 0, 255]'
            else:
                color = '[0, 0, 255, 100]'

            # Ajout des coordonnées du domicile s'il est défini
            if personal_address:
                addr_lat, addr_lon = get_coordinates(personal_address)
                if addr_lat and addr_lon:
                    map_data.append({
                        'name': 'Domicile',
                        'lat': addr_lat,
                        'lon': addr_lon
                    })
            else:
                addr_lat, addr_lon = 45.7640, 4.8357 # Coordonnées de Lyon

            view_state = pdk.ViewState(
                latitude=addr_lat,
                longitude=addr_lon,
                zoom=12,
                pitch=0
            )

            # Paramètres du point du domicile (bleu)
            home_layer = pdk.Layer(
                'ScatterplotLayer',
                data=[point for point in map_data if point['name'] == 'Domicile'],
                get_position='[lon, lat]',
                get_color=color,
                get_radius=radius,
                pickable=True,
                auto_highlight=True
            )

            # Paramètres des points des restaurants (rouge)
            restaurants_layer = pdk.Layer(
                'ScatterplotLayer',
                data=[point for point in map_data if point['name'] != 'Domicile'],
                get_position='[lon, lat]',
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

            st.pydeck_chart(deck)

if __name__ == '__main__':
    main()