import streamlit as st
from db.models import get_user_and_review_from_restaurant_id 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pages.resources.components import display_stars


# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()

# Initialiser le nombre de reviews à afficher
if 'display_count' not in st.session_state:
    st.session_state['display_count'] = 10  # Afficher initialement 10 reviews

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
    
    # Modification des largeurs des colonnes
    col1, col2 = st.columns(2)  # 2 colonnes
    st.markdown("""
    <style>
    .review {
        font-size: 0.9em;
    }
    .user_name {
        font-weight: bold;
    }
    .date_review {
        color: #657786;
        font-size: 0.9em;
        
    }
    
    </style>
    """, unsafe_allow_html=True)
    with col1:
        st.markdown("<h2 style='text-align: center;'>Avis</h2>", unsafe_allow_html=True)
        with st.container(height=900):
            for i, r in enumerate(review[:st.session_state['display_count']]):
                # Initialize session state for this review if not exists
                if f"show_full_review_{i}" not in st.session_state:
                    st.session_state[f"show_full_review_{i}"] = False
                    
                review_text = r[1].review_text
                is_long_review = len(review_text) > 80
                
                # Display user name
                st.markdown(f"<div ><span class='user_name'>{r[0].user_name}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='date_review'>{r[1].date_review}</div>" , unsafe_allow_html=True)
                stars = display_stars(r[1].rating)
                st.image(stars, width=20)                
                # Display review text based on length and state
                if is_long_review:
                    if st.session_state[f"show_full_review_{i}"]:
                        st.markdown(f"<div class='review'>{review_text}</div>", unsafe_allow_html=True)
                        st.markdown("<div class='review-button'>", unsafe_allow_html=True)
                        if st.button("Voir moins", key=f"toggle_{i}"):
                            st.session_state[f"show_full_review_{i}"] = False
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='review'>{review_text[:80]}...</div>", unsafe_allow_html=True)
                        st.markdown("<div class='review-button'>", unsafe_allow_html=True)
                        if st.button("...Voir plus", key=f"toggle_{i}"):
                            st.session_state[f"show_full_review_{i}"] = True
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.write(review_text)
                    
                st.write("----")
        
            # Bouton pour charger plus de reviews
            if st.session_state['display_count'] < len(review):
                if st.button("Charger plus d'avis"):
                    st.session_state['display_count'] += 5
                    st.rerun()
    with col2:
        # affiche le leaderboard des utilisateurs avec le plus d'avis pour ce restaurant
        st.header("Top contributeurs")
        user_reviews_count = {}
        for user, _ in review:
            user_reviews_count[user.user_profile] = user_reviews_count.get(user.user_profile, 0) + 1
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
        # graphique bar chart horizontale
        st.bar_chart(rating_counts)
            
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
        st.bar_chart(month_counts)