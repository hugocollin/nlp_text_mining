import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import get_restaurants_with_reviews_and_users

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

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
        avis_restaurants_data = get_restaurants_with_reviews_and_users(self.session)
        data = []
        for restaurant in avis_restaurants_data:
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
        self.avis_restaurants['review_cleaned'] = self.avis_restaurants['review'].apply(self.nettoyer_avis)

    def vectorisation(self, methode='bow', max_features=500):
        vectorizer = CountVectorizer(max_features=max_features) if methode == 'bow' else TfidfVectorizer(max_features=max_features)
        vecteurs = vectorizer.fit_transform(self.avis_restaurants['review_cleaned'])
        return pd.DataFrame(vecteurs.toarray(), columns=vectorizer.get_feature_names_out())

    def nettoyage_dates(self):
        self.avis_restaurants['date_review'] = self.avis_restaurants['date_review'].astype(str).str.strip()
        mois_fr_en = {
            'janvier': 'January', 'février': 'February', 'mars': 'March', 'avril': 'April',
            'mai': 'May', 'juin': 'June', 'juillet': 'July', 'août': 'August',
            'septembre': 'September', 'octobre': 'October', 'novembre': 'November', 'décembre': 'December'
        }
        for fr, en in mois_fr_en.items():
            self.avis_restaurants['date_review'] = self.avis_restaurants['date_review'].str.replace(fr, en, regex=False)
        self.avis_restaurants['date_review'] = pd.to_datetime(self.avis_restaurants['date_review'], errors='coerce', dayfirst=True)

    def extraire_annee_mois_jour(self):
        self.avis_restaurants['year'] = self.avis_restaurants['date_review'].dt.year
        self.avis_restaurants['month'] = self.avis_restaurants['date_review'].dt.month
        self.avis_restaurants['day'] = self.avis_restaurants['date_review'].dt.day

    def afficher_dataframe_complet(self):
        print(self.avis_restaurants.head())
        return self.avis_restaurants
    
    


# Exemple d'utilisation
#pretraitement = NLPPretraitement()
#pretraitement.extraction_donnees()
#pretraitement.appliquer_nettoyage()
#pretraitement.nettoyage_dates()
#pretraitement.extraire_annee_mois_jour()

# Affichage final du DataFrame
#df_final = pretraitement.afficher_dataframe_complet()
#df_final