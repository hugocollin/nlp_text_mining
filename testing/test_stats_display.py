import streamlit as st
from db.models import Restaurant
from pages.statistiques import display_restaurant_stats
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configuration de la connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()

def main():
    # Créer un objet Restaurant factice
    mock_restaurant = Restaurant(
        nom="Restaurant Test",
        adresse="123 Avenue de Test",
        telephone="0123456789",
        id_restaurant=13,
        image = "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/23/63/53/44/caption.jpg"
    )

    # Afficher les statistiques pour le restaurant factice
    display_restaurant_stats(mock_restaurant)

if __name__ == "__main__":
    main()