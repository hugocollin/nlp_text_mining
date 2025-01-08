import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.components import Navbar, get_personnal_address, get_coordinates, display_stars, process_restaurant, get_restaurant_coordinates
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
    # [TEMP] Filtrer sur les restaurant non scrappé
    restaurant_names = [restaurant.nom for restaurant in restaurants]
    options = ["Sélectionner un restaurant"] + restaurant_names

    # Sélection du restaurant à ajouter
    restaurant_select = st.selectbox(label="Sélectionner un restaurant", label_visibility="collapsed", placeholder="Sélectionner un restaurant", options=options, key="restaurant_select")
    
    # Scapping du restaurant sélectionné
    if st.button(icon="➕", label="Ajouter le restaurant"):
        if restaurant_select != "Sélectionner un restaurant":
            # [TEMP] Code pour scrapper le restaurant sélectionné et ajouter les informations à la base de données
            st.session_state['restaurant_added'] = True
        st.rerun()

def main():
    # Barre de navigation
    Navbar()

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
        st.toast("➕ Restaurant ajouté avec succès")
        st.session_state['restaurant_added'] = False

    # Conteneur pour la recherche et les filtres
    header_container = st.container(border=True)

    # Mise en page de la recherche et des filtres
    header_col1, header_col2 = header_container.columns([3, 2])

    # Colonne pour la recherche
    with header_col1:
        header_col1.write("Recherche")
        search_col1, search_col2 = header_col1.columns([4, 1])

        with search_col1:
            # [TEMP] Filtrer sur les restaurant scrappé
            restaurant_names = [restaurant.nom for restaurant in restaurants]
            options = ["Sélectionner un restaurant"] + restaurant_names

            search_restaurant = search_col1.multiselect(label="Rechercher un restaurant", label_visibility="collapsed", placeholder="Rechercher un restaurant", options=options, key="search_restaurant")
            search_address = search_col1.text_input(label="Recherchez une adresse", label_visibility="collapsed", placeholder="Recherchez une adresse")
            radius = search_col1.slider("Rayon (m)", min_value=1, max_value=1000, step=1, value=100)

        with search_col2:
            if search_col2.button(label="🔍", key="search_restaurant_btn"):
                if search_restaurant:
                    search_col2.toast("Les résultats seront disponibles dans une version ultérieure") # [TEMP]
                else:
                    search_col2.toast("⚠️ Veuillez renseigner le nom d'un restaurant à rechercher")

            if search_col2.button(label="🔍", key="search_address_btn"):
                if not search_address:
                    search_col2.toast("⚠️ Veuillez renseigner une adresse à rechercher")
    
    # Colonne pour les filtres
    with header_col2:
        header_col2.write("Filtres")

    # Mise en page des résultats
    results_display_col1, results_display_col2 = st.columns(2)
    
    # Affichage des résultats
    with results_display_col1:
        if not personal_address:
            st.toast("⚠️ Veuillez définir votre adresse personnelle pour voir les temps de transport")

        # Parallélisation du traitement des restaurants
        with st.spinner("Chargement des restaurants..."):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_restaurant, personal_address, restaurant) for restaurant in restaurants]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Filtrage des résultats en fonction des restaurants sélectionnés
        if search_restaurant:
            filtered_results = [result for result in results if result[0].nom in search_restaurant]
        else:
            filtered_results = results

        # Extraction des restaurants filtrés pour la carte
        filtered_restaurants = [(result[0].nom, result[0].adresse) for result in filtered_results if result[0] is not None]

        # Affichage uniquement des restaurants filtrés
        for result in filtered_results:
            restaurant, tcl_url, fastest_mode = result
            container = st.container(border=True)
            col1, col2 = container.columns([2, 1])
            
            with col1:
                col1.write(restaurant.nom)
                stars = display_stars(restaurant.note_globale)
                col1.image(stars, width=20)
            
            with col2:
                if tcl_url:
                    emoji, fastest_duration = fastest_mode
                    bouton_label = f"{emoji} {fastest_duration}"
                    button_key = f"trajet_btn_{restaurant.id_restaurant}"
                    if col2.button(bouton_label, key=button_key):
                        webbrowser.open_new_tab(tcl_url)
                else:
                    unique_key = f"trajet_indisponible_{restaurant.id_restaurant}"
                    col2.button("Trajet indisponible", disabled=True, key=unique_key)
    
    # Affichage de la carte
    with results_display_col2:
        with st.spinner("Chargement de la carte..."):
            # Récupération des coordonnées géographiques des restaurants
            map_data = get_restaurant_coordinates(filtered_restaurants)

            # Ajout des coordonnées du domicile s'il est défini
            if personal_address:
                home_lat, home_lon = get_coordinates(personal_address)
                if home_lat and home_lon:
                    map_data.append({
                        'name': 'Domicile',
                        'lat': home_lat,
                        'lon': home_lon
                    })

            # Définition de la vue de la carte
            if search_address:
                addr_lat, addr_lon = get_coordinates(search_address)
            else:
                addr_lat, addr_lon = 45.7640, 4.8357 # Coordonnées de Lyon

            view_state = pdk.ViewState(
                latitude=addr_lat,
                longitude=addr_lon,
                zoom=12,
                pitch=0
            )

            # Paramètres du point de l'adresse recherchée s'il y a une adresse recherchée (vert)
            if search_address:
                addr_lat, addr_lon = get_coordinates(search_address)

            searched_address_layer = pdk.Layer(
                'ScatterplotLayer',
                data=[{'name': 'Adresse recherchée', 'lat': addr_lat, 'lon': addr_lon}],
                get_position='[lon, lat]',
                get_color='[0, 255, 0, 50]',
                get_radius=radius,
                pickable=True,
                auto_highlight=True
            )

            # Paramètres du point du domicile (bleu)
            home_layer = pdk.Layer(
                'ScatterplotLayer',
                data=[point for point in map_data if point['name'] == 'Domicile'],
                get_position='[lon, lat]',
                get_color='[0, 0, 255]',
                get_radius=25,
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
            if search_address and addr_lat and addr_lon:
                layers.append(searched_address_layer)

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