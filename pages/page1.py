import streamlit as st
from utils.components import Navbar
import pydeck as pdk
from geopy.geocoders import Nominatim
import geopy.exc

def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="streamlit_app", timeout=10)
        # Limiter la recherche au département 69 en ajoutant "Rhône, France"
        location = geolocator.geocode(f"{address}, Rhône, France")
        if location:
            return location.latitude, location.longitude
    except geopy.exc.GeocoderServiceError:
        st.error("Service de géocodification indisponible. Veuillez réessayer plus tard.")
    return None, None

def main():
    Navbar()

    st.title('🍽️ Restaurants')

    col1, col2 = st.columns(2)
    
    with col1:
        search_restaurant = st.text_input("Rechercher un restaurant")
        st.write("Liste des restaurants")
        # ...code pour afficher la liste des restaurants...
    
    with col2:
        search_address = st.text_input("Entrez une adresse")
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
            st.error("Adresse introuvable. Veuillez entrer une adresse valide.")

if __name__ == '__main__':
    main()