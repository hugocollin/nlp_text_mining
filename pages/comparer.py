import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pages.resources.components import Navbar, display_michelin_stars, display_stars, display_restaurant_infos, get_personnal_address, tcl_api
from pages.statistiques import display_restaurant_stats
from db.models import get_all_restaurants

# Configuration de la page
st.set_page_config(page_title="SISE Ô Resto - Comparer", page_icon="🍽️", layout="wide")

# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()

# Récupération de tous les restaurants
restaurants = get_all_restaurants(session)

# Récupération de l'adresse personnelle
personal_address = get_personnal_address()

# Fonction pour afficher le popup d'informations sur un restaurant
@st.dialog("Informations sur le restaurant", width="large")
def restaurant_info_dialog():
    display_restaurant_infos(personal_address)

def main():
    # Barre de navigation
    Navbar()

    # Vérification si un restaurant a été sélectionné pour afficher ses statistiques
    selected_stats = st.session_state.get('selected_stats_restaurant')
    if selected_stats:
        display_restaurant_stats(selected_stats)
        return
    
    # Titre de la page
    st.title('🆚 Comparer')

    # Initialisation du comparateur dans session_state
    if 'comparator' not in st.session_state:
        st.session_state['comparator'] = []
    
    # Vérification si le comparateur est vide
    if not st.session_state['comparator']:
        st.info("Aucun restaurant sélectionné pour la comparaison. Retournez à l'Explorateur pour ajouter des restaurants.")
        return
    
    # Mise en page du bouton pour réinitialiser le comparateur
    reinit_cmp_btn_col1, reinit_cmp_btn_col2 = st.columns([2, 1])
    
    # Bouton pour réinitialiser le comparateur
    if reinit_cmp_btn_col2.button("🔄 Réinitialiser le comparateur"):
        reinit_cmp_btn_col2.session_state['comparator'] = []
        reinit_cmp_btn_col2.rerun()

    # Récupération des restaurants sélectionnés
    selected_restaurants = [restaurant for restaurant in restaurants if restaurant.id_restaurant in st.session_state['comparator']]

    # Affichage des restaurants comparés
    cols = st.columns(len(selected_restaurants), border=True)
    for idx, restaurant in enumerate(selected_restaurants):
        with cols[idx]:
            
            # Récupération des informations de trajet
            tcl_url, duration_public, duration_car, duration_soft, fastest_mode = tcl_api(personal_address, restaurant.adresse)

            # Mise en page des boutons
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])

            with btn_col1:
                # Bouton pour afficher les informations détaillées
                if btn_col1.button("ℹ️", key=f"info_cmp_{restaurant.id_restaurant}"):
                    st.session_state['selected_restaurant'] = restaurant
                    restaurant_info_dialog()
            
            with btn_col2:
                # Bouton pour afficher les statistiques
                if btn_col2.button("📊", key=f"stats_btn_{restaurant.id_restaurant}"):
                    st.session_state['selected_stats_restaurant'] = restaurant
                    st.rerun()

            with btn_col3:
                # Bouton pour supprimer du comparateur
                if btn_col3.button("❌ Supprimer", key=f"remove_cmp_{restaurant.id_restaurant}"):
                    st.session_state['comparator'].remove(restaurant.id_restaurant)
                    st.rerun()

            st.header(restaurant.nom)
            michelin_stars = display_michelin_stars(restaurant.etoiles_michelin)
            if michelin_stars:
                st.image(michelin_stars, width=25)
            stars = display_stars(restaurant.note_globale)
            stars_html = ''.join([f'<img src="{star}" width="20">' for star in stars])
            st.html(f"<b>Note globale : </b>{stars_html}")
            st.write(f"- **Qualité Prix :** {restaurant.qualite_prix_note}")
            st.write(f"- **Cuisine :** {restaurant.cuisine_note}")
            st.write(f"- **Service :** {restaurant.service_note}")
            st.write(f"- **Ambiance :** {restaurant.ambiance_note}")
            st.write("**Informations complémentaires :**")
            st.write(f"- **Cuisine :** {restaurant.cuisines}")
            st.write(f"- **Repas :** {restaurant.repas}")
            st.write("**Temps de trajet :**")
            st.write(f"- 🚲 {duration_soft}")
            st.write(f"- 🚌 {duration_public}")
            st.write(f"- 🚗 {duration_car}")

if __name__ == '__main__':
    main()