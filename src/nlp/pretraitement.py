
import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.functions_db import get_restaurants_with_reviews_and_users , fill_review_cleaned_column
from sqlalchemy import Table, MetaData
from sqlalchemy.dialects.sqlite import insert


class NLPPretraitement:
    def __init__(self, db_url='sqlite:///restaurant_reviews.db'):
        # Connexion à la base de données
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.lemmatizer = WordNetLemmatizer()
        
        # Initialiser le DataFrame
        self.avis_restaurants = None

    def extraction_donnees(self):
        print("Extraction...")
        avis_restaurants_data = get_restaurants_with_reviews_and_users(self.session)
        data = []
        for restaurant in avis_restaurants_data:
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
                    'review': review['review']
                })
        self.avis_restaurants = pd.DataFrame(data)

    def nettoyer_avis(self, avis):
        avis = avis.lower()
        avis = re.sub(r'[^\w\s]', '', avis)
        avis = re.sub(r'[0-9]', '', avis)
        tokens = word_tokenize(avis)
        tokens = [self.lemmatizer.lemmatize(word) for word in tokens]
        tokens = [word for word in tokens if word not in stopwords.words('french')]
        tokens = [word for word in tokens if len(word) > 2]
        return ' '.join(tokens)

    def appliquer_nettoyage(self):
        print("Nettoyer avis...")
        self.avis_restaurants['review_cleaned'] = self.avis_restaurants['review'].apply(self.nettoyer_avis)

    def vectorisation(self, methode='bow', max_features=500):
        print("Vectorisation avis...")
        vectorizer = CountVectorizer(max_features=max_features) if methode == 'bow' else TfidfVectorizer(max_features=max_features)
        vecteurs = vectorizer.fit_transform(self.avis_restaurants['review_cleaned'])
        return pd.DataFrame(vecteurs.toarray(), columns=vectorizer.get_feature_names_out())

    def afficher_dataframe_complet(self):
        return self.avis_restaurants
    
    def sauvegarder_donnees(self):
        print("Sauvegarder avis...")
        try:
            fill_review_cleaned_column(self.avis_restaurants, self.session)

        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données: {e}")
