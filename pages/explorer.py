import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pages.resources.components import Navbar, get_personnal_address, get_coordinates, display_michelin_stars, display_stars, process_restaurant, get_restaurant_coordinates, get_google_maps_link, tcl_api, add_to_comparator, filter_restaurants_by_radius
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
    restaurant_names = [restaurant.nom for restaurant in restaurants if not restaurant.scrapped]
    options = ["Sélectionner un restaurant"] + restaurant_names

    # Sélection du restaurant à ajouter
    restaurant_select = st.selectbox(label="Sélectionner un restaurant", label_visibility="collapsed", placeholder="Sélectionner un restaurant", options=options, key="restaurant_select")
    
    # Scapping du restaurant sélectionné
    if st.button(icon="➕", label="Ajouter le restaurant"):
        if restaurant_select != "Sélectionner un restaurant":
            # [TEMP] Code pour scrapper le restaurant sélectionné et ajouter les informations à la base de données
            st.session_state['restaurant_added'] = True
        st.rerun()

# Fonction pour afficher le popup d'informations sur un restaurant
@st.dialog("Informations sur le restaurant", width="large")
def restaurant_info_dialog():
    # Récupération des informations du restaurant sélectionné
    selected_restaurant = st.session_state.get('selected_restaurant')
    tcl_url, duration_public, duration_car, duration_soft, fastest_mode = tcl_api(personal_address, selected_restaurant.adresse)

    if selected_restaurant:
        # Mise en page du header
        title_col1, title_col2 = st.columns([0.9, 0.1], vertical_alignment = "bottom")
        
        # Affichage du nom
        with title_col1:
            title_col1.header(selected_restaurant.nom)

        # Affichage des étoiles Michelin
        with title_col2:
            michelin_stars = display_michelin_stars(selected_restaurant.etoiles_michelin)
            if michelin_stars:
                title_col2.image(michelin_stars, width=25)
        
        # Mise en page des informations
        container = st.container()
        col1, col2 = container.columns(2)

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
            score_col1, score_col2 = score_container.columns([0.5, 0.5])

            with score_col1:
                score_col1.write("**Note globale :**")
                score_col1.write(f"**Note qualité prix :** {selected_restaurant.qualite_prix_note}")
                score_col1.write(f"**Note cuisine :** {selected_restaurant.cuisine_note}")
                score_col1.write(f"**Note service :** {selected_restaurant.service_note}")
                score_col1.write(f"**Note ambiance :** {selected_restaurant.ambiance_note}")
            with score_col2:
                stars = display_stars(selected_restaurant.note_globale)
                score_col2.image(stars, width=20)
            
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
        st.toast("➕ Restaurant ajouté avec succès")
        st.session_state['restaurant_added'] = False

    # Conteneur pour la recherche et les filtres
    header_container = st.container(border=True)

    # Mise en page de la recherche et des filtres
    header_col1, header_col2 = header_container.columns(2)

    # Colonne pour la recherche
    with header_col1:
        # Filtrage sur les restaurants scrappés
        restaurant_names = [restaurant.nom for restaurant in restaurants if restaurant.scrapped]
        options = ["Sélectionner un restaurant"] + restaurant_names

        search_restaurant = header_col1.multiselect(label="Rechercher un restaurant", label_visibility="collapsed", placeholder="Rechercher un restaurant", options=options, key="search_restaurant")
        if personal_address:
            use_radius_filter = header_col1.checkbox(label="Activer le filtre de recherche par distance autour du domicile", value=False, key="use_radius_filter")
            if use_radius_filter:
                radius = header_col1.slider("Rayon (m)", min_value=1, max_value=3000, step=1, value=500)
            else:
                radius = 1000000
        else:
            use_radius_filter = header_col1.checkbox(label="Activer le filtre de recherche par distance autour du domicile", value=False, key="use_radius_filter", disabled=True)
            radius = 1000000
    
    # Colonne pour les filtres
    with header_col2:

        # [TEMP] Ajouter des filtres
        header_col2.write("[Les filtres seront ajoutés ultérieurement]")

    # Mise en page des résultats
    results_display_col1, results_display_col2 = st.columns([3, 2])
    
    # Affichage des résultats
    with results_display_col1:
        if not personal_address:
            st.toast("ℹ️ Veuillez définir votre adresse personnelle pour voir les temps de trajet")

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
    
    # Affichage de la carte
    with results_display_col2:
        with st.spinner("Chargement de la carte..."):
            # Récupération des coordonnées géographiques des restaurants
            map_data = get_restaurant_coordinates(filtered_restaurants)

            # Mise en forme du radius
            if radius == 1000000:
                radius = 25

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
                get_color='[0, 0, 255, 100]',
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