import streamlit as st




def display_restaurant_stats(restaurant):
    st.title(f"📊 {restaurant.nom}")
    st.write(f"📍 {restaurant.nom}")

    # Bouton pour revenir en arrière
    if st.button("🔙 Retour"):
        st.session_state['selected_stats_restaurant'] = None
        st.rerun()