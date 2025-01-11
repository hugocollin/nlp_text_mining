import streamlit as st
from db.models import get_user_and_review_from_restaurant_id , get_all_restaurants
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pages.resources.components import Navbar
import pandas as pd

set_page_config = st.set_page_config(page_title="SISE Ô Resto - Admin", page_icon="🍽️", layout="wide")

# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()

# Récupération de tous les restaurants
restaurants = get_all_restaurants(session)

def display_restaurant_stats():
    # Calculer le nombre de restaurants scrappés
    col1 , col2 = st.columns(2)
    nombre_scrapped = len([r for r in restaurants if r.scrapped == 1])

    # Afficher le résultat dans Streamlit
    st.write(f"Nombre de restaurants scrappés : {nombre_scrapped}")   
    nom_scrapped = [r.nom for r in restaurants if r.scrapped == 1]
    st.write(f"Nom des restaurants scrappés : {nom_scrapped}")
    df = pd.DataFrame(nom_scrapped, columns = ['Nom des restaurants scrappés'])

    with col1:
        st.write("Liste des restaurants scrappés")
        st.write(df)
    with col2:
        st.write("Unique values")
        st.write(df.value_counts())
 

def main():
    # Barre de navigation
    Navbar()
    
    st.title("Administration")
    st.write("Bienvenue sur la page d'administration de l'application SISE Ô Resto.")
    st.write("Vous trouverez ci-dessous la liste de tous les restaurants scrappés :")
    
    # Afficher les statistiques pour tous les restaurants
    display_restaurant_stats()
if __name__ == '__main__':
    main()