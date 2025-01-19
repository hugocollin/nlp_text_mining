import pandas as pd
import re
import nltk
#download nltk data
nltk.download('punkt_tab')
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')


from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from textblob import TextBlob


STOP_WORDS_URL = "src/nlp/stopwords_fr.txt"
stop_words = pd.read_csv(STOP_WORDS_URL, header=None)[0].tolist()
   

class NLPPretraitement:
    def __init__(self):

        self.lemmatizer = WordNetLemmatizer()
        


    def nettoyer_avis(self, avis):
        avis = avis.lower()
        avis = re.sub(r'[0-9]', '', avis)
        tokens = word_tokenize(avis)
        tokens = [self.lemmatizer.lemmatize(word) for word in tokens]
        tokens = [word for word in tokens if word not in stop_words]
        tokens = [word for word in tokens if len(word) > 2]
        return ' '.join(tokens)
    
    def preprocess(self, review):
        """Nettoie, tokenize, et lemmatise un texte tout en supprimant les stopwords."""
        review = review.lower()
        tokens = word_tokenize(review)
        tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        return ' '.join(tokens)


    def preprocess_reviews(self, df_reviews):
        """Applique la fonction preprocess à une colonne de texte d'un DataFrame."""
        df_reviews = df_reviews.dropna()
        df_reviews["review_cleaned"] = df_reviews["review"].apply(self.preprocess)
        return df_reviews

    def sentiment_analysis(self, df_reviews):
        """Analyse le sentiment d'un texte."""
        # --- Étape 3 : Analyse des sentiments ---
        
        df_reviews["sentiment_rating"] = df_reviews["review_cleaned"].apply(lambda x: TextBlob(x).sentiment.polarity)
        df_reviews["sentiment"] = df_reviews["sentiment_rating"].apply(lambda x: "positive" if x >= 0 else "negative")
        print(df_reviews["sentiment"].value_counts())
        return df_reviews
