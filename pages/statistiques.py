import streamlit as st
from db.models import get_user_and_review_from_restaurant_id 
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
    st.write(f"📧 {restaurant.id_restaurant}")
    review = get_user_and_review_from_restaurant_id(session, restaurant.id_restaurant)
    
    # Affichage des statistiques
    st.header("Statistiques")
    st.write(f"Nombre d'avis: {len(review)}")
    st.write(f"Note moyenne: {round(sum([r.rating for r in review]) / len(review), 2)}")
    st.write(f"Nombre de visites: {len(set([r.id_user for r in review]))}")
    st.write(f"Nombre d'utilisateurs ayant laissé un avis: {len(set([r.user.user_name for r in review]))}")
    
    # Affichage des 10 premiers avis
    st.header("Avis")
    for r in review[:10]:
        st.write(f"🔹 {r.user.user_name} ( - {r.rating}/5")
        st.write(f"\"{r.review_text}\"")
        st.write("----")

    # Bouton pour revenir en arrière
    if st.button("🔙 Retour"):
        st.session_state['selected_stats_restaurant'] = None
        st.rerun()