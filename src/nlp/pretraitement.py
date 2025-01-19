import pandas as pd
import re
import nltk
#download nltk data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer


class NLPPretraitement:
    def __init__(self):

        self.session = self.Session()
        self.lemmatizer = WordNetLemmatizer()
        # Initialiser le DataFrame
        self.avis_restaurants = None


    def nettoyer_avis(self, avis):
        avis = avis.lower()
        avis = re.sub(r'[^\w\s]', '', avis)
        avis = re.sub(r'[0-9]', '', avis)
        tokens = word_tokenize(avis)
        tokens = [self.lemmatizer.lemmatize(word) for word in tokens]
        tokens = [word for word in tokens if word not in stopwords.words('french')]
        tokens = [word for word in tokens if len(word) > 2]
        return ' '.join(tokens)

    def vectorisation(self, methode='bow', max_features=500):
        print("Vectorisation avis...")
        vectorizer = CountVectorizer(max_features=max_features) if methode == 'bow' else TfidfVectorizer(max_features=max_features)
        vecteurs = vectorizer.fit_transform(self.avis_restaurants['review_cleaned'])
        return pd.DataFrame(vecteurs.toarray(), columns=vectorizer.get_feature_names_out())
