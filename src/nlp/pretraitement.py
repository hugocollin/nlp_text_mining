import pandas as pd
import re
import nltk

nltk.download('punkt_tab')
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from textblob import TextBlob

# Chargement des stopwords
STOP_WORDS_URL = "src/nlp/stopwords_fr.txt"
stop_words = pd.read_csv(STOP_WORDS_URL, header=None)[0].tolist()
   
# Définition de la classe NLPPretraitement
class NLPPretraitement:
    # Constructeur
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()

    # Méthode pour nettoyer un avis
    def nettoyer_avis(self, avis):
        avis = avis.lower()
        avis = re.sub(r'[0-9]', '', avis)
        tokens = word_tokenize(avis)
        tokens = [self.lemmatizer.lemmatize(word) for word in tokens]
        tokens = [word for word in tokens if word not in stop_words]
        tokens = [word for word in tokens if len(word) > 2]
        return ' '.join(tokens)

    # Méthode de prétraitement
    def preprocess(self, review):
        review = review.lower()
        tokens = word_tokenize(review)
        tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        return ' '.join(tokens)

    # Méthode pour prétraiter les avis
    def preprocess_reviews(self, df_reviews):
        df_reviews = df_reviews.dropna()
        df_reviews["review_cleaned"] = df_reviews["review"].apply(self.preprocess)
        return df_reviews

    # Méthode pour l'analyse de sentiment
    def sentiment_analysis(self, df_reviews):
        df_reviews["sentiment_rating"] = df_reviews["review_cleaned"].apply(lambda x: TextBlob(x).sentiment.polarity)
        df_reviews["sentiment"] = df_reviews["sentiment_rating"].apply(lambda x: "positive" if x >= 0 else "negative")
        print(df_reviews["sentiment"].value_counts())
        return df_reviews