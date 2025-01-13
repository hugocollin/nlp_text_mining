import pandas as pd
import numpy as np
import re

import sys 
import os


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import get_restaurants_with_reviews_and_users
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
        # Préparation des données
        X_pad = self.preprocess_reviews()
        y = self.data['sentiment']
        X_train, X_test, y_train, y_test = train_test_split(X_pad, y, test_size=0.2, random_state=42)

        # Définition et entraînement du modèle LSTM
        self.model = Sequential([
            Embedding(input_dim=10000, output_dim=128, input_length=200),
            LSTM(128, dropout=0.2, recurrent_dropout=0.2),
            Dense(3, activation='softmax')
        ])
        self.model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
        self.model.fit(X_train, y_train, epochs=5, batch_size=64, validation_data=(X_test, y_test), verbose=1)

        # Évaluation du modèle
        y_pred = np.argmax(self.model.predict(X_test), axis=1)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Précision du modèle LSTM : {accuracy * 100:.2f}%")

    def summarize_reviews(self):
        summarizer = pipeline("summarization", model="t5-small", tokenizer="t5-small")
        
        def resumer_avis(avis):
            segments = [' '.join(avis.split()[i:i+200]) for i in range(0, len(avis.split()), 200)]
            return ' '.join(summarizer(segment, max_length=10, min_length=3, do_sample=False)[0]['summary_text'] for segment in segments)

        resultats = []
        with ThreadPoolExecutor() as executor:
            for restaurant, group in self.data.groupby("restaurant"):
                avis = ' '.join(group['review_cleaned'])
                resultats.append({"restaurant": restaurant, "resume_avis": executor.submit(resumer_avis, avis).result()})

        return pd.DataFrame(resultats)

    def generate_wordcloud(self):
        tous_avis = ' '.join(self.data['review_cleaned'])
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(tous_avis)
        return wordcloud

    def visualize_tokens_3d(self, num_clusters=5):
        # Assurez-vous que les données sont vectorisées
        if self.data.empty:
            raise ValueError("Data is not loaded or vectorized")

        # Utiliser UMAP pour réduire la dimensionnalité à 3D
        reducer = umap.UMAP(n_components=3)
        embeddings = reducer.fit_transform(self.data)

        # Utiliser KMeans pour le clustering
        kmeans = KMeans(n_clusters=num_clusters)
        clusters = kmeans.fit_predict(embeddings)

        # Visualiser les résultats en 3D
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        scatter = ax.scatter(embeddings[:, 0], embeddings[:, 1], embeddings[:, 2], c=clusters, cmap='viridis')

        # Ajouter une légende
        legend1 = ax.legend(*scatter.legend_elements(), title="Clusters")
        ax.add_artist(legend1)

        plt.show()

# Exemple d'utilisation
if __name__ == "__main__":
    print("hey")

