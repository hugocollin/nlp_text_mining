import streamlit as st
from db.models import get_user_and_review_from_restaurant_id 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()


def display_restaurant_stats(restaurant):
    # Bouton pour revenir en arrière
    if st.button("🔙 Retour"):
        st.session_state['selected_stats_restaurant'] = None
        st.rerun()
    st.title(f"📊 {restaurant.nom}")
    st.write(f"📍 {restaurant.adresse}")
    st.write(f"📞 {restaurant.telephone}")
    st.write(f"📧 {restaurant.id_restaurant}")
    review = get_user_and_review_from_restaurant_id(session, restaurant.id_restaurant)
    
    # Affichage des statistiques
    st.header("Statistiques")
    st.write(f"Nombre d'avis: {len(review)}")
    
    # Affichage des 10 premiers avis
    st.header("Avis")
    for r in review[:10]:
        st.write(r[0].user_name + " a écrit:")
        st.write(r[1].review_text)
        st.write("----")
        
    # affiche le leaderboard des utilisateurs avec le plus d'avis pour ce restaurant
    st.header("Top contributeurs")
    user_reviews_count = {}
    for user, _ in review:
        user_reviews_count[user.user_name] = user_reviews_count.get(user.user_name, 0) + 1
    top_users = sorted(user_reviews_count.items(), key=lambda x: x[1], reverse=True)
    for user, count in top_users[:5]:
        st.write(f"{user} ({count} avis)")
        
    # affiche le nombre d'avis par note
    st.header("Répartition des notes")
    rating_counts = {}
    for _, r in review:
        rating_counts[r.rating] = rating_counts.get(r.rating, 0) + 1
    for rating, count in rating_counts.items():
        st.write(f"{rating} étoiles: {count} avis")
        
    # affiche le nombre d'avis par type de visite
    st.header("Répartition des types de visite")
    type_visit_counts = {}
    for _, r in review:
        type_visit_counts[r.type_visit] = type_visit_counts.get(r.type_visit, 0) + 1
    for type_visit, count in type_visit_counts.items():
        st.write(f"{type_visit}: {count} avis")
        
    # affiche le nombre d'avis par mois et fait un graphique
    st.header("Répartition des avis par mois")
    month_counts = {}
    for _, r in review:
        month = r.date_review.strftime("%Y-%m")
        month_counts[month] = month_counts.get(month, 0) + 1
    for month, count in month_counts.items():
        st.write(f"{month}: {count} avis")
    st.bar_chart(month_counts)
    

    