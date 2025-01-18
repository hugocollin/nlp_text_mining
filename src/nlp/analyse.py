import pandas as pd
import numpy as np
import re

from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.functions_db import fill_sentiment_column, fill_resume_avis_column , get_restaurants_with_reviews_and_users
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor
from wordcloud import WordCloud
import umap
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import KMeans

class NLPAnalysis:
    def __init__(self, db_path='sqlite:///restaurant_reviews.db'):
        # Initialisation de la connexion à la base de données
        self.engine = create_engine(db_path)
        self.session = sessionmaker(bind=self.engine)()
        self.data = pd.DataFrame()
        self.model = None
        self.tokenizer = None

    def load_data(self):
        # Extraction et transformation des données
        raw_data = get_restaurants_with_reviews_and_users(self.session)
        data = []
        for restaurant in raw_data:
            for review in restaurant['reviews']:
                data.append({
                    'restaurant_id': review['restaurant_id'],
                    'user_id': review['user_id'],
                    'review_id': review['review_id'],
                    'restaurant': restaurant['restaurant'],
                    'restaurant_address': restaurant['restaurant_address'],
                    'title': review['title'],
                    'user_profile': review['user_profile'],
                    'date_review': review['date_review'],
                    'rating': review['rating'],
                    'type_visit': review['type_visit'],
                    'num_contributions': review['num_contributions'],
                    'review': review['review'],
                    'review_cleaned': review['review_cleaned']
                })
        self.data = pd.DataFrame(data)
        self.data['sentiment'] = self.data['rating'].apply(self._sentiment_class)

    @staticmethod
    def _sentiment_class(rating):
        return 2 if rating == 3 else (1 if rating >= 4 else 0)

    def preprocess_reviews(self):
        # Tokenisation et padding
        self.tokenizer = Tokenizer(num_words=10000)
        self.tokenizer.fit_on_texts(self.data['review_cleaned'])
        sequences = self.tokenizer.texts_to_sequences(self.data['review_cleaned'])
        return pad_sequences(sequences, padding='post', maxlen=200)

    def train_lstm_model(self):
        # Ajouter la colonne 'sentiment_rating' avec les valeurs Positif, Négatif, Neutre en fonction de 'rating'
        self.data['sentiment_rating'] = self.data['rating'].apply(
            lambda x: 'Positif' if x > 3 else ('Négatif' if x < 3 else 'Neutre')
        )
        
        # Convertir les ratings en 3 classes : Négatif (0), Positif (1), Neutre (2)
        self.data['sentiment'] = self.data['rating'].apply(
            lambda x: 1 if x >= 4 else (0 if x <= 2 else 2)
        )
        
        # Tokenisation des avis
        if self.tokenizer is None:
            self.tokenizer = Tokenizer(num_words=10000)
            self.tokenizer.fit_on_texts(self.data['review_cleaned'])
        
        sequences = self.tokenizer.texts_to_sequences(self.data['review_cleaned'])
        
        # Padding des séquences
        X_pad = pad_sequences(sequences, padding='post', maxlen=200)
        # Préparation des cibles (sentiment)
        y = self.data['sentiment']
        # Séparation en jeu d'entraînement et test
        X_train, X_test, y_train, y_test = train_test_split(X_pad, y, test_size=0.2, random_state=42)
        
        # Définition du modèle LSTM
        self.model = Sequential([
            Embedding(input_dim=10000, output_dim=128, input_length=200),  # Couche d'embedding
            LSTM(128, dropout=0.2, recurrent_dropout=0.2),  # Couche LSTM
            Dense(3, activation='softmax')  # Couche de sortie pour 3 classes
        ])
        
        # Compilation du modèle
        self.model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
        
        # Entraînement du modèle
        self.model.fit(X_train, y_train, epochs=5, batch_size=64, validation_data=(X_test, y_test), verbose=1)
        
        # Évaluation du modèle
        y_pred = np.argmax(self.model.predict(X_test), axis=1)  # Prédictions sur le jeu de test
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Précision du modèle LSTM : {accuracy * 100:.2f}%")







    def summarize_chunk(self,summarizer, chunk):
        return summarizer(chunk, max_length=100, min_length=20, do_sample=False)[0]['summary_text']

    def summarize_reviews(self, df):
        summarizer = pipeline("summarization", model="t5-small", tokenizer="t5-small")
        all_reviews = ' '.join(df['review_cleaned'].values)
        
        # Split the reviews into chunks of 512 tokens
        max_chunk_length = 512
        chunks = [all_reviews[i:i + max_chunk_length] for i in range(0, len(all_reviews), max_chunk_length)]
        
        # Summarize each chunk in parallel
        summaries = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_chunk = {executor.submit(self.summarize_chunk, summarizer, chunk): chunk for chunk in chunks}
            for future in as_completed(future_to_chunk):
                try:
                    summary = future.result()
                    summaries.append(summary)
                except Exception as e:
                    print(f"Erreur lors de la summarization du chunk: {e}")
        
        # Combine all summaries into a single summary
        final_summary = ' '.join(summaries)
        return final_summary












    def generate_wordcloud(self):
        tous_avis = ' '.join(self.data['review_cleaned'])
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(tous_avis)
        return wordcloud
    
    def sauvegarder_donnees(self):
        print("Sauvegarder sentiment...")
        try:
            fill_sentiment_column(self.data, self.session)

        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données: {e}")

    def sauvegarder_resume(self, resumes):
        print("Sauvegarder résumés...")
        try:
            fill_resume_avis_column(resumes, self.session)

        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données: {e}")

    def sauvegarder_sentiment_rating(self):
        try:
            fill_sentiment_column(self.data, self.session)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données: {e}")
        
# Exemple d'utilisation
if __name__ == "__main__":
    print("hey")

