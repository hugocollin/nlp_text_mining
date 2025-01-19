import streamlit as st
import pydeck as pdk
import os
from dotenv import find_dotenv, load_dotenv
from pages.resources.components import Navbar, get_personal_address
from geopy.geocoders import Nominatim

# Configuration de la page
st.set_page_config(page_title="SISE Ô Resto", page_icon="🍽️", layout="wide")

# Récupération de la clé API Mistral
try:
    load_dotenv(find_dotenv())
    API_KEY = os.getenv("MISTRAL_API_KEY")
except FileNotFoundError:
    API_KEY = st.secrets["MISTRAL_API_KEY"]

# Réinitialisation de popup de vérification de l'adresse renseignée
if 'address_toast_shown' in st.session_state:
    del st.session_state['address_toast_shown']

# Fonction pour afficher le popup de paramétrage de l'adresse personnelle
@st.dialog("Paramétrer l'adresse personnelle", width="large")
def add_personal_address_dialog():

    # Affichage du message de confidentialité
    st.info("Pour des raisons de confidentialité, votre adresse personnelle n'est pas stockée et sera supprimée dès que vous fermerez l'application.", icon="🔒")

    # Récupération des informations de l'adresse personnelle
    personal_address, _personal_latitude, _personal_longitude = get_personal_address()

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
            header_col1.write(f"**{personal_address}**")

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
        st.warning("L'adresse ne peut pas être vide", icon="⚠️") 
    
    if address_geo_failed:
        st.session_state['address_search_done'] = False
        st.session_state['found_location'] = None
        st.warning("L'adresse renseignée n'est pas valide", icon="⚠️")
        
    
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

    # Vérification de la présence de la clé API Mistral
    if not API_KEY:
        if 'mistral_api_warning' not in st.session_state:
            st.toast("Vous n'avez pas rajouté votre clé API Mistral dans les fichiers de l'application. Veuillez ajouter le fichier `.env` à la racine du projet puis redémarrer l'application.", icon="⚠️")
            st.session_state['mistral_api_warning'] = True

    # Titre de la page
    st.title("Bienvenue sur SISE Ô Resto !")

    # Mise en page du bouton pour ajouter l'adresse personnelle
    _add_restaurant_btn_col1, add_restaurant_btn_col2 = st.columns([2, 1])

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
    
    container_col1_1, container_col1_2 = container.columns(2, border=True)
    container_col1_1.write("**🔍 Explorez les restaurants à Lyon**")
    container_col1_1.write("Découvrez une large sélection de restaurants à Lyon et trouvez l'endroit idéal pour votre prochain repas. Consultez rapidement le statut actuel de chaque établissement, le temps de trajet et accédez en un clic à des informations détaillées et à l'itinéraire.")
    container_col1_2.write("**ℹ️ Informations détaillées à portée de main**")
    container_col1_2.write("Accédez aux fiches complètes de chaque restaurant, incluant les informations pratiques, les avis clients et bien plus.")

    container_col2_1, container_col2_2, container_col2_3 = container.columns(3, border=True)
    container_col2_1.write("**🎨 Filtres avancés pour une recherche personnalisée**")
    container_col2_1.write("Utilisez 14 filtres différents pour affiner votre recherche et trouver l'endroit parfait selon vos préférences.")
    container_col2_2.write("**✨ Obtenez des recommandations personnalisées**")
    container_col2_2.write("Discutez avec notre IA pour des conseils sur les meilleurs restaurants à Lyon adaptés à vos goûts.")
    container_col2_3.write("**🗺️ Localisez les restaurants en un clin d'œil**")
    container_col2_3.write("Grâce à la carte interactive, repérez facilement les restaurants près de chez vous et explorez vos options.")

    container_col3_1, container_col3_2, container_col3_3 = container.columns(3, border=True)
    container_col3_1.write("**🆚 Comparez les établissements facilement**")
    container_col3_1.write("Comparez les caractéristiques des différents restaurants pour prendre une décision éclairée rapidement et sans effort.")
    container_col3_2.write("**📊 Visualisez vos graphiques de manière intuitive**")
    container_col3_2.write("Créez des graphiques personnalisés pour comparer et analyser les données des restaurants de Lyon facilement et rapidement.")
    container_col3_3.write("**➕ Ajoutez des restaurants à votre sélection en un clic**")
    container_col3_3.write("Ajoutez des restaurants à votre liste pour les comparer et les consulter en un instant.")
    
    st.write("*Cette application a été développée par [KPAMEGAN Falonne](https://github.com/marinaKpamegan), [KARAMOKO Awa](https://github.com/karamoko17), [GABRYSCH Alexis](https://github.com/AlexisGabrysch) et [COLLIN Hugo](https://github.com/hugocollin), dans le cadre du Master 2 SISE.*")

if __name__ == '__main__':
    main()