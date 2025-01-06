import streamlit as st
from geopy.geocoders import Nominatim
import geopy.exc

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

available_restaurants_options = ["Sélectionner un restaurant", "Restaurant 1", "Restaurant 2", "Restaurant 3", "Restaurant 4", "Restaurant 5"] # [TEMP] À remplacer par les restaurants de la base de données
multi_available_restaurants_options = ["Restaurant 1", "Restaurant 2", "Restaurant 3", "Restaurant 4", "Restaurant 5"] # [TEMP] À remplacer par les restaurants de la base de données
add_restaurant_options = ["Sélectionner un restaurant", "Restaurant 6", "Restaurant 7", "Restaurant 8", "Restaurant 9", "Restaurant 10"] # [TEMP] À remplacer par les restaurants de la base de données