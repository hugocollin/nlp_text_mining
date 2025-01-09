import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.components import Navbar, display_michelin_stars, display_stars
from db.models import get_all_restaurants

# Configuration de la page
st.set_page_config(page_title="SISE Ô Resto - Comparer", page_icon="🍽️", layout="wide")

# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()

# Récupération de tous les restaurants
restaurants = get_all_restaurants(session)

def main():
    # Barre de navigation
    Navbar()
    
    # Titre de la page
    st.title('🆚 Comparer')

    # Initialisation du comparateur dans session_state
    if 'comparator' not in st.session_state:
        st.session_state['comparator'] = []
    
    # Vérifier si le comparateur est vide
    if not st.session_state['comparator']:
        st.info("Aucun restaurant sélectionné pour la comparaison. Retournez à l'Explorateur pour ajouter des restaurants.")
        return
    
    # Bouton pour réinitialiser le comparateur
    if st.button("🔄 Réinitialiser le Comparateur"):
        st.session_state['comparator'] = []
        st.rerun()

    # Récupérer les restaurants sélectionnés
    selected_restaurants = [restaurant for restaurant in restaurants if restaurant.id_restaurant in st.session_state['comparator']]

    # Affichage des restaurants comparés
    cols = st.columns(len(selected_restaurants), border=True)
    for idx, restaurant in enumerate(selected_restaurants):
        with cols[idx]:
            st.header(restaurant.nom)
            michelin_stars = display_michelin_stars(restaurant.etoiles_michelin)
            if michelin_stars:
                st.image(michelin_stars, width=100)
            stars = display_stars(restaurant.note_globale)
            st.image(stars, width=20)
            st.write(f"**Adresse :** {restaurant.adresse}")
            st.write(f"**Cuisine :** {restaurant.cuisines}")
            st.write(f"**Prix :** {restaurant.prix_min} - {restaurant.prix_max}")
            st.write(f"**Repas :** {restaurant.repas}")
            st.write(f"**Note Globale :** {restaurant.note_globale}")
            st.write(f"**Qualité Prix :** {restaurant.qualite_prix_note}")
            st.write(f"**Cuisine :** {restaurant.cuisine_note}")
            st.write(f"**Service :** {restaurant.service_note}")
            st.write(f"**Ambiance :** {restaurant.ambiance_note}")
            
            # Bouton pour retirer du comparateur
            if st.button("❌ Retirer", key=f"remove_cmp_{restaurant.id_restaurant}"):
                st.session_state['comparator'].remove(restaurant.id_restaurant)
                st.rerun()

if __name__ == '__main__':
    main()