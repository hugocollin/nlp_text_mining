import streamlit as st
from utils.components import Navbar, get_coordinates
import pydeck as pdk

st.set_page_config(page_title="[Titre de l\'application] - Explorer", layout="wide")

if 'show_add_restaurant_dialog' not in st.session_state:
    st.session_state['show_add_restaurant_dialog'] = False

def main():
    Navbar()

    st.title('🔍 Explorer')

    add_restaurant_btn_col1, add_restaurant_btn_col2 = st.columns([3, 1])

    with add_restaurant_btn_col2:
        if st.button("➕ Ajouter un restaurant", key="add_restaurant_btn"):
            st.session_state['show_add_restaurant_dialog'] = True

    # Boîte de dialogue pour ajouter un restaurant
    if st.session_state['show_add_restaurant_dialog']:
        with st.container():
            st.markdown("### Ajouter un nouveau restaurant")
            with st.form("add_restaurant_form"):
                restaurant_name = st.text_input("Nom du restaurant", placeholder="Ex. : Le Bistro")
                restaurant_address = st.text_input("Adresse du restaurant", placeholder="Ex. : 12 Rue de la République")
                submit_button = st.form_submit_button("Ajouter")

                if submit_button:
                    # Ici, vous pouvez ajouter la logique pour sauvegarder le restaurant (base de données, fichier, etc.)
                    st.toast(f"Restaurant '{restaurant_name}' ajouté avec succès!")
                    st.session_state['show_add_restaurant_dialog'] = False  # Fermer la boîte de dialogue

    header_container = st.container(border=True)

    header_col1, header_col2 = header_container.columns([3, 2])

    with header_col1:
        header_col1.write("Recherche")
        search_col1, search_col2 = header_col1.columns([4, 1])

        with search_col1:
            search_restaurant = search_col1.text_input(label="Rechercher un restaurant", label_visibility="collapsed", placeholder="Rechercher un restaurant")
            search_address = search_col1.text_input(label="Recherchez une adresse", label_visibility="collapsed", placeholder="Recherchez une adresse")

        with search_col2:
            if search_col2.button("🔍", key="search_restaurant_btn"):
                if search_restaurant:
                    search_col2.toast("Les résultats seront disponibles dans une version ultérieure") # [TEMP]
                else:
                    search_col2.toast("⚠️ Veuillez renseigner le nom d'un restaurant à rechercher")

            if search_col2.button("🔍", key="search_address_btn"):
                if not search_address:
                    search_col2.toast("⚠️ Veuillez renseigner une adresse à rechercher")

        radius = search_col1.slider("Rayon (km)", min_value=1, max_value=10, step=1, value=5)
    
    with header_col2:
        header_col2.write("Filtres")

    results_display_col1, results_display_col2 = st.columns(2)
    
    with results_display_col1:
        st.write("[Liste des restaurants]")
    
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