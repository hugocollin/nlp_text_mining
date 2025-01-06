import streamlit as st
from utils.components import Navbar, get_coordinates
import pydeck as pdk

st.set_page_config(page_title="[Titre de l\'application] - Explorer", layout="wide")

def main():
    Navbar()

    st.title('🔍 Explorer')

    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Recherche par restaurant")
        restaurant_col1, restaurant_col2 = st.columns([4, 1])

        with restaurant_col1:
            search_restaurant = st.text_input(label="Rechercher un restaurant", label_visibility="collapsed", placeholder="Rechercher un restaurant")
        
        with restaurant_col2:
            if st.button("🔍", key="search_restaurant_btn"):
                if search_restaurant:
                    st.toast("Les résultats seront disponibles dans une version ultérieure") # [TEMP]
                else:
                    st.toast("⚠️ Veuillez renseigner le nom d'un restaurant à rechercher")

        st.write("Liste des restaurants")

        # [TEMP] Affichage des restaurants dès que la base de données sera disponible
    
    with col2:
        st.header("Recherche par adresse")
        address_col1, address_col2 = st.columns([4, 1])

        with address_col1:
            search_address = st.text_input(label="Recherchez une adresse", label_visibility="collapsed", placeholder="Recherchez une adresse")
        
        with address_col2:
            if st.button("🔍", key="search_address_btn"):
                if not search_address:
                    st.toast("⚠️ Veuillez renseigner une adresse à rechercher")

        radius = st.slider("Rayon (km)", min_value=1, max_value=10, step=1, value=5)
        
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
                pitch=0,
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