import streamlit as st
from db.models import get_restaurants_with_reviews_and_users
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from Nlp.processing import TextProcessor
from Nlp.processing import TextAnalyser
import matplotlib.pyplot as plt


# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()


def display_restaurant_stats(restaurant):
    st.title(f"📊 {restaurant.nom}")
    st.write(f"📍 {restaurant.adresse}")
    st.write(f"📞 {restaurant.telephone}")
    avis_restaurants = pd.read_csv(
            'Data/avis_restaurants.csv',
            sep=';'
        )

    # Initialiser le processeur de texte pour la vectorisation BoW
    bow_processor = TextProcessor(
        text_column='review',
        cleaned_text_column='review_cleaned',
        date_column='date_review',
        max_features=500,
        vectorizer_type='bow',
        output_csv='Data/avis_restaurants_cleaned_bow.csv'
    )

    # Appliquer le pipeline de traitement
    processed_df_bow = bow_processor.process(avis_restaurants)
    print("Bag of Words Vectorization Completed.")

    # Sauvegarder le vectorizer BoW
    bow_processor.save_vectorizer('vectorizer_bow.joblib')

# Initialiser et appliquer le TextProcessor
    processor = TextProcessor(
        text_column='review',
        cleaned_text_column='review_cleaned',
        date_column='date_review',
        max_features=500,
        vectorizer_type='bow',
        output_csv='Data/avis_restaurants_cleaned.csv'
    )
    processed_df = processor.process(avis_restaurants)
    print("Text Processing Completed.")

    # Initialiser le TextAnalyser
    analyser = TextAnalyser(processed_df, cleaned_text_column='review_cleaned')

    # Générer le rapport d'analyse
    analyser.generate_wordcloud()
    
    # plot wordcloud in analyser.wordcloud
    st.write("📊 Nuage de mots")
    st.image(analyser.wordcloud.to_image(), use_column_width=True)
    


        



    # Bouton pour revenir en arrière
    if st.button("🔙 Retour"):
        st.session_state['selected_stats_restaurant'] = None
        st.rerun()