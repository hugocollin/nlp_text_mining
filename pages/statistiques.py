import streamlit as st
from db.models import get_restaurants_with_reviews_and_users
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()


def display_restaurant_stats(restaurant):
    st.title(f"📊 {restaurant.nom}")
    st.write(f"📍 {restaurant.adresse}")
    st.write(f"📞 {restaurant.telephone}")
   

    # Bouton pour revenir en arrière
    if st.button("🔙 Retour"):
        st.session_state['selected_stats_restaurant'] = None
        st.rerun()