import streamlit as st
from utils.components import Navbar, get_personnal_address, get_coordinates, display_stars, tcl_api, multi_available_restaurants_options, add_restaurant_options
from db.models import get_all_restaurants
import pydeck as pdk
import webbrowser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import concurrent.futures

st.set_page_config(page_title="[Titre de l\'application] - Explorer", layout="wide")

# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()

@st.dialog("Ajouter un restaurant")
def add_restaurant_dialog():
    restaurant_select = st.selectbox(label="Sélectionner un restaurant à ajouter", label_visibility="collapsed", placeholder="Sélectionner un restaurant à ajouter", options=add_restaurant_options, key="restaurant_select")
    
    if st.button(icon="➕", label="Ajouter le restaurant"):
        if restaurant_select != "Sélectionner un restaurant":
            # Code pour rajouter le restaurant à la base de données
            st.session_state['restaurant_added'] = True
        st.rerun()

def main():
    Navbar()

    st.title('🔍 Explorer')

    add_restaurant_btn_col1, add_restaurant_btn_col2 = st.columns([3, 1])

    with add_restaurant_btn_col2:
        if st.button(icon="➕", label="Ajouter un restaurant", key="add_restaurant_btn"):
            add_restaurant_dialog()
    
    if st.session_state.get('restaurant_added'):
        st.toast("🍽️ Restaurant ajouté avec succès")
        st.session_state['restaurant_added'] = False

    header_container = st.container(border=True)

    header_col1, header_col2 = header_container.columns([3, 2])

    with header_col1:
        header_col1.write("Recherche")
        search_col1, search_col2 = header_col1.columns([4, 1])

        with search_col1:
            search_restaurant = search_col1.multiselect(label="Rechercher un restaurant", label_visibility="collapsed", placeholder="Rechercher un restaurant", options=multi_available_restaurants_options, key="search_restaurant")
            search_address = search_col1.text_input(label="Recherchez une adresse", label_visibility="collapsed", placeholder="Recherchez une adresse")
            radius = search_col1.slider("Rayon (km)", min_value=1, max_value=10, step=1, value=5)

        with search_col2:
            if search_col2.button(label="🔍", key="search_restaurant_btn"):
                if search_restaurant:
                    search_col2.toast("Les résultats seront disponibles dans une version ultérieure") # [TEMP]
                else:
                    search_col2.toast("⚠️ Veuillez renseigner le nom d'un restaurant à rechercher")

            if search_col2.button(label="🔍", key="search_address_btn"):
                if not search_address:
                    search_col2.toast("⚠️ Veuillez renseigner une adresse à rechercher")
    
    with header_col2:
        header_col2.write("Filtres")

    results_display_col1, results_display_col2 = st.columns(2)
    
    with results_display_col1:
        # Récupérer tous les restaurants depuis la base de données
        restaurants = get_all_restaurants(session)

        # Récupérer l'adresse personnelle depuis la session
        personal_address = get_personnal_address()

        if not personal_address:
            st.toast("⚠️ Veuillez définir votre adresse personnelle pour voir les temps de transport")

        # Fonction pour traiter chaque restaurant
        def process_restaurant(idx, restaurant):
            tcl_url, duration_public, duration_car, duration_soft, fastest_mode = tcl_api(personal_address, restaurant.adresse)
            return (idx, restaurant, tcl_url, fastest_mode)
        
        # Utiliser ThreadPoolExecutor pour paralléliser les appels
        with st.spinner("Chargement des restaurants..."):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_restaurant, idx, restaurant) for idx, restaurant in enumerate(restaurants)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Afficher les résultats
        for result in results:
            idx, restaurant, tcl_url, fastest_mode = result
            container = st.container(border=True)
            col1, col2 = container.columns([2, 1])
            
            with col1:
                col1.write(restaurant.nom)
                stars = display_stars(restaurants[idx].note_globale)
                col1.image(stars, width=20, clamp=True)
            
            with col2:
                if tcl_url:
                    emoji, fastest_duration = fastest_mode
                    bouton_label = f"{emoji} {fastest_duration}"
                    button_key = f"trajet_btn_{idx}"
                    if col2.button(bouton_label, key=button_key):
                        webbrowser.open_new_tab(tcl_url)
                else:
                    unique_key = f"trajet_indisponible_{idx}"
                    col2.button("Trajet indisponible", disabled=True, key=unique_key)
    
    with results_display_col2:
        # Coordonnées de Lyon
        lyon_lat = 45.7640
        lyon_lon = 4.8357
        
        # Obtenir les coordonnées de l'adresse recherchée
        addr_lat, addr_lon = get_coordinates(search_address) if search_address else (lyon_lat, lyon_lon)
        
        if addr_lat and addr_lon:
            # Définir la vue initiale de la carte
            view_state = pdk.ViewState(
                latitude=addr_lat,
                longitude=addr_lon,
                zoom=10,
                pitch=0
            )
            
            # Définir la couche pour l'adresse recherchée
            layers = [
                pdk.Layer(
                    'ScatterplotLayer',
                    data=[{"position": [addr_lon, addr_lat]}],
                    get_position='position',
                    get_color=[0, 255, 0],
                    get_radius=200,
                ),
            ]
            
            map = pdk.Deck(
                initial_view_state=view_state,
                layers=layers,
            )
            
            st.pydeck_chart(map)
        else:
            st.error("Adresse introuvable. Veuillez entrer une adresse valide.") # [TEMP]

if __name__ == '__main__':
    main()