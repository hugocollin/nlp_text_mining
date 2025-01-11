import streamlit as st
from pages.resources.components import Navbar, get_personal_address
from geopy.geocoders import Nominatim
import pydeck as pdk

# Configuration de la page
st.set_page_config(page_title="SISE Ô Resto", page_icon="🍽️", layout="wide")

# Fonction pour afficher le popup de paramétrage de l'adresse personnelle
@st.dialog("Paramétrer l'adresse personnelle", width="large")
def add_personal_address_dialog():
    # Récupération des informations de l'adresse personnelle
    personal_address, personal_latitude, personal_longitude = get_personal_address()

    # Initialisation des variables
    if 'address_search_done' not in st.session_state:
        st.session_state['address_search_done'] = False
    if 'found_location' not in st.session_state:
        st.session_state['found_location'] = None
    empty_address = False
    address_geo_failed = False
    
    # Paramétrage de l'adresse personnelle
    if personal_address:

        # Mise en page du header
        header_col1, header_col2 = st.columns([4, 3])

        # Affichage de l'adresse personnelle
        with header_col1:
            header_col1.write("Votre adresse personnelle actuelle est :")
            header_col1.write(f"{personal_address}")

        # Bouton pour supprimer l'adresse personnelle
        with header_col2:
            if header_col2.button(icon="🗑️", label="Supprimer l'adresse personnelle", key="delete_address"):
                st.session_state.pop('personal_address', None)
                st.session_state.pop('personal_latitude', None)
                st.session_state.pop('personal_longitude', None)
                st.session_state['personal_address_suppr'] = True
                st.rerun()
    else:
        header_col1, header_col2 = st.columns([4, 3])

        with header_col1:
            header_col1.write("Vous n'avez pas encore renseigné d'adresse personnelle.")

        with header_col2:
            header_col2.button(icon="🗑️", label="Supprimer l'adresse personnelle", disabled=True, key="delete_address")

        search_col1, search_col2 = st.columns([8, 1])

    # Mise en page de la recherche d'adresse
    search_col1, search_col2 = st.columns([8, 1])

    # Champ de recherche de l'adresse
    with search_col1:
        personal_address_input = search_col1.text_input(label="Renseignez votre adresse personnelle", label_visibility="collapsed", placeholder="Renseignez votre adresse personnelle", key="personal_address_input")

    # Bouton de recherche de l'adresse
    with search_col2:
        if search_col2.button(label="🔍", key="search_address"):
            if personal_address_input.strip() == "":
                empty_address = True
            else:
                # Récupération des coordonnées de l'adresse
                geolocator = Nominatim(user_agent="sise_o_resto")
                location = geolocator.geocode(f"{personal_address_input.strip()}, Rhône, France")
                
                if location:
                    # Stockage des informations de localisation
                    st.session_state['found_location'] = location
                    st.session_state['address_search_done'] = True
                else:
                    address_geo_failed = True

    # Affichage des messages d'erreur
    if empty_address:
        st.session_state['address_search_done'] = False
        st.session_state['found_location'] = None
        st.warning("L'adresse ne peut pas être vide.", icon="⚠️") 
    
    if address_geo_failed:
        st.session_state['address_search_done'] = False
        st.session_state['found_location'] = None
        st.warning("L'adresse renseignée n'est pas valide.", icon="⚠️")
        
    
    # Affichage de la carte et du bouton d'enregistrement si la recherche est réussie
    if st.session_state['address_search_done'] and st.session_state['found_location']:
        location = st.session_state['found_location']
        
        # Définition de la vue de la carte
        view = pdk.ViewState(
            latitude=location.latitude,
            longitude=location.longitude,
            zoom=13,
            pitch=0
        )

        # Définition de la couche de la carte
        layer = pdk.Layer(
            'ScatterplotLayer',
            data=[{'position': [location.longitude, location.latitude]}],
            get_position='position',
            get_color='[0, 0, 255]',
            get_radius=25,
            pickable=True,
            auto_highlight=True
        )

        # Paramètres de l'infos-bulle
        tooltip = {
            "html": "<b>Domicile</b>",
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

        # Bouton d'enregistrement de l'adresse personnelle
        if st.button(icon="💾", label="Enregistrer l'adresse personnelle", key="save_address"):
            st.session_state['personal_address'] = personal_address_input.strip()
            st.session_state['personal_latitude'] = location.latitude
            st.session_state['personal_longitude'] = location.longitude
            st.session_state['personal_address_added'] = True
            st.session_state['address_search_done'] = False
            st.session_state['found_location'] = None
            st.rerun()

def main():
    # Barre de navigation
    Navbar()

    # Titre de la page
    st.title("Bienvenue sur SISE Ô Resto !")

    # Mise en page du bouton pour ajouter l'adresse personnelle
    add_restaurant_btn_col1, add_restaurant_btn_col2 = st.columns([2, 1])

    # Bouton pour ajouter l'adresse personnelle
    with add_restaurant_btn_col2:
        if st.button(icon="🏡", label="Paramétrer l'adresse personnelle", key="add_personnal_address"):
            add_personal_address_dialog()
    
    # Affichage du message de succès
    if st.session_state.get('personal_address_added'):
        st.toast("Adresse personnelle enregistrée avec succès", icon="💾")
        st.session_state['personal_address_added'] = False

    # Affichage du message de suppression
    if st.session_state.get('personal_address_suppr'):
        st.toast("Adresse personnelle supprimée avec succès", icon="🗑️")
        st.session_state['personal_address_suppr'] = False

    # Description de l'application
    container = st.container()
    
    container.write("**Profitez d’une expérience culinaire optimisée et trouvez votre prochain repas à Lyon en toute simplicité avec SISE Ô Resto.**")
    container.write("Découvrez et explorez les meilleurs restaurants de Lyon grâce à notre application intuitive où vous pourrez :")
    
    container_col1_1, container_col1_2, container_col1_3 = container.columns(3, border=True)
    
    container_col1_1.write("**🔍 Explorez les restaurants**")
    container_col1_1.write("Parcourez une vaste sélection de restaurants à Lyon en filtrant par [...] pour trouver l'endroit idéal pour votre prochain repas.")
    container_col1_2.write("**ℹ️ Obtenez les informations détailllés des restaurants**")
    container_col1_2.write("Accédez aux fiches complètes comprenant [...] pour chaque restaurant.")
    container_col1_3.write("**🆚 Comparez les restaurants**")
    container_col1_3.write("Comparez facilement [...] et les caractéristiques des différents établissements pour prendre une décision éclairée.")
    
    container_col2_1, container_col2_2 = container.columns(2, border=True)

    container_col2_1.write("**📊 Statistiques détaillés des restaurants**")
    container_col2_1.write("Visualisez des statistiques pertinentes telles que [...] pour mieux comprendre chaque restaurant.")
    container_col2_2.write("**🗺️ Localiser les restaurants et obetnir un itinéraire en un clic**")
    container_col2_2.write("Utilisez la carte interactive pour localiser les restaurants proches de votre domicile et obtenez rapidement un itinéraire pour vous y rendre (veuillez renseigner votre adresse personelle via la page d'accueil pour accéder à cette fonctionnalité).")
    
    st.write("*Cette application a été développée par KPAMEGAN Falonne, KARAMOKO Awa, GABRYSCH Alexis et COLLIN Hugo, dans le cadre du Master 2 SISE.*")

if __name__ == '__main__':
    main()