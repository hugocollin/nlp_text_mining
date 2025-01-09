import re
import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer


import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix


# # Ensure necessary NLTK data packages are downloaded
# nltk.download('punkt_tab')
# nltk.download('stopwords')
# nltk.download('wordnet')


class TextProcessor:
    def __init__(
        self,
        text_column: str = 'review',
        cleaned_text_column: str = 'review_cleaned',
        date_column: str = 'date_review',
        max_features: int = 500,
        vectorizer_type: str = 'bow',
        output_csv: str = 'Data/avis_restaurants_cleaned.csv'
    ):
        """
        Initialize the TextProcessor with configurable parameters.

        :param text_column: Name of the column containing raw text.
        :param cleaned_text_column: Name of the column to store cleaned text.
        :param date_column: Name of the column containing date information.
        :param max_features: Maximum number of features for vectorization.
        :param vectorizer_type: Type of vectorizer ('bow' for Bag of Words, 'tfidf' for TF-IDF).
        :param output_csv: Path to save the cleaned DataFrame.
        """
        self.text_column = text_column
        self.cleaned_text_column = cleaned_text_column
        self.date_column = date_column
        self.max_features = max_features
        self.vectorizer_type = vectorizer_type.lower()
        self.output_csv = output_csv

        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = list(set(stopwords.words('french')))
        self.vectorizer = self._initialize_vectorizer()

    def _initialize_vectorizer(self):
        """
        Initialize the vectorizer based on the specified type.

        :return: Initialized vectorizer.
        """
        if self.vectorizer_type == 'bow':
            return CountVectorizer(
                max_features=self.max_features,
                stop_words=self.stop_words  # Utilisation de la liste de mots vides en français
                )
        elif self.vectorizer_type == 'tfidf':
            return TfidfVectorizer(
                max_features=self.max_features,
                stop_words=self.stop_words  # Utilisation de la liste de mots vides en français
            )
        else:
            raise ValueError("vectorizer_type must be either 'bow' or 'tfidf'")

    def nettoyer_avis(self, avis: str) -> str:
        """
        Clean the input text by removing special characters, lowercasing,
        tokenizing, lemmatizing, removing stopwords, and filtering short words.

        :param avis: Raw text review.
        :return: Cleaned text.
        """
        # Retirer les caractères spéciaux et convertir en minuscules
        avis = avis.lower()
        avis = re.sub(r'[^\w\s]', '', avis)

        # Retirer les chiffres
        avis = re.sub(r'[0-9]', '', avis)

        # Tokenisation
        tokens = word_tokenize(avis)

        # Lemmatisation
        tokens = [self.lemmatizer.lemmatize(word) for word in tokens]

        # Retirer les stopwords
        tokens = [word for word in tokens if word not in self.stop_words]

        # Retirer les termes de moins de 3 caractères
        tokens = [word for word in tokens if len(word) > 2]

        return ' '.join(tokens)

    def apply_text_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply text cleaning to the specified text column.

        :param df: Input DataFrame.
        :return: DataFrame with an added cleaned text column.
        """
        df[self.cleaned_text_column] = df[self.text_column].apply(self.nettoyer_avis)
        return df

    def vectorize_text(self, texts: pd.Series) -> pd.DataFrame:
        """
        Vectorize the input texts using the initialized vectorizer.

        :param texts: Pandas Series containing cleaned text.
        :return: DataFrame representation of vectorized texts.
        """
        X = self.vectorizer.fit_transform(texts)
        feature_names = self.vectorizer.get_feature_names_out()
        return pd.DataFrame(X.toarray(), columns=feature_names)

    def modify_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and convert the date column from French to datetime.
        Extracts year and month as separate columns.

        :param df: Input DataFrame.
        :return: DataFrame with modified date columns.
        """
        df[self.date_column] = df[self.date_column].str.strip()
        df[self.date_column] = df[self.date_column].str.replace(r'\s+', ' ', regex=True)

        mois_fr_en = {
            'janvier': 'January', 'février': 'February', 'mars': 'March', 'avril': 'April',
            'mai': 'May', 'juin': 'June', 'juillet': 'July', 'août': 'August',
            'septembre': 'September', 'octobre': 'October', 'novembre': 'November', 'décembre': 'December'
        }

        for fr, en in mois_fr_en.items():
            df[self.date_column] = df[self.date_column].str.replace(fr, en, regex=False)

        df[self.date_column] = pd.to_datetime(df[self.date_column], format='%d %B %Y', errors='coerce')
        df['year'] = df[self.date_column].dt.year
        df['month'] = df[self.date_column].dt.month

        df.to_csv(self.output_csv, index=False)
        return df

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Execute the full preprocessing pipeline:
        - Clean text
        - Vectorize text
        - Modify date

        :param df: Input DataFrame.
        :return: Processed DataFrame with vectorized text and modified date.
        """
        # Clean text
        df = self.apply_text_cleaning(df)

        # Vectorize text
        vectorized_df = self.vectorize_text(df[self.cleaned_text_column])

        # Combine vectorized features with the original DataFrame
        df = pd.concat([df, vectorized_df], axis=1)

        # Modify date
        df = self.modify_date(df)

        return df

    def save_vectorizer(self, filepath: str):
        """
        Save the fitted vectorizer to a file for future use.

        :param filepath: Path to save the vectorizer.
        """
        import joblib
        joblib.dump(self.vectorizer, filepath)
        print(f"Vectorizer saved to {filepath}")

    def load_vectorizer(self, filepath: str):
        """
        Load a pre-fitted vectorizer from a file.

        :param filepath: Path to load the vectorizer from.
        """
        import joblib
        self.vectorizer = joblib.load(filepath)
        print(f"Vectorizer loaded from {filepath}")


class TextAnalyser:
    def __init__(self, df: pd.DataFrame, cleaned_text_column: str = 'review_cleaned'):
        """
        Initialize the TextAnalyser with the processed DataFrame.

        :param df: Processed DataFrame containing cleaned text.
        :param cleaned_text_column: Name of the column containing cleaned text.
        """
        self.df = df
        self.cleaned_text_column = cleaned_text_column
        self.stop_words = list(set(stopwords.words('french')))

    def plot_rating_distribution(self):
        """
        Plot the distribution of ratings.
        """
        plt.figure(figsize=(8, 6))
        sns.countplot(x='rating', data=self.df, palette='viridis')
        plt.title('Distribution of Ratings')
        plt.xlabel('Rating')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.show()

    def generate_wordcloud(self, max_words: int = 100, background_color: str = 'white'):
        """
        Generate and display a word cloud from the cleaned text.

        :param max_words: Maximum number of words in the word cloud.
        :param background_color: Background color for the word cloud.
        """
        text = ' '.join(self.df[self.cleaned_text_column].dropna())
        wordcloud = WordCloud(width=800, height=400, max_words=max_words, background_color=background_color).generate(text)

        plt.figure(figsize=(15, 7.5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Word Cloud of Reviews', fontsize=20)
        plt.show()

    def perform_sentiment_analysis(self):
        """
        Perform sentiment analysis on the cleaned text using a simple polarity method.

        :return: DataFrame with an added 'sentiment' column.
        """
        from textblob import TextBlob
        nltk.download('averaged_perceptron_tagger')
        
        def get_sentiment(text):
            blob = TextBlob(text)
            return blob.sentiment.polarity

        self.df['sentiment'] = self.df[self.cleaned_text_column].apply(get_sentiment)
        return self.df

    def plot_sentiment_distribution(self):
        """
        Plot the distribution of sentiment scores.
        """
        plt.figure(figsize=(8, 6))
        sns.histplot(self.df['sentiment'], bins=30, kde=True, color='skyblue')
        plt.title('Sentiment Score Distribution')
        plt.xlabel('Sentiment Polarity')
        plt.ylabel('Frequency')
        plt.tight_layout()
        plt.show()

    def perform_topic_modeling(self, n_topics: int = 5):
        """
        Perform topic modeling using Latent Dirichlet Allocation (LDA).

        :param n_topics: Number of topics to identify.
        :return: Fitted LDA model and the feature names.
        """
        # Initialize CountVectorizer for LDA
        vectorizer = CountVectorizer(max_features=1000, stop_words=self.stop_words)
        X = vectorizer.fit_transform(self.df[self.cleaned_text_column].dropna())

        lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
        lda.fit(X)

        feature_names = vectorizer.get_feature_names_out()
        return lda, feature_names

    def display_topics(self, lda_model, feature_names, n_top_words: int = 10):
        """
        Display the top words for each topic.

        :param lda_model: Fitted LDA model.
        :param feature_names: List of feature names from the vectorizer.
        :param n_top_words: Number of top words to display per topic.
        """
        for topic_idx, topic in enumerate(lda_model.components_):
            print(f"Topic #{topic_idx + 1}:")
            print(" | ".join([feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]]))
            print()

    def plot_topic_distribution(self, lda_model):
        """
        Plot the distribution of topics across the corpus.

        :param lda_model: Fitted LDA model.
        """
        topic_distribution = lda_model.transform(
            CountVectorizer(max_features=1000, stop_words=self.stop_words).fit_transform(self.df[self.cleaned_text_column].dropna())
        )
        topic_labels = topic_distribution.argmax(axis=1)

        plt.figure(figsize=(10, 6))
        sns.countplot(x=topic_labels, palette='Set2')
        plt.title('Topic Distribution')
        plt.xlabel('Topic')
        plt.ylabel('Number of Reviews')
        plt.tight_layout()
        plt.show()

    def train_sentiment_classifier(self):
        """
        Train a simple logistic regression classifier for sentiment analysis.

        :return: Trained classifier and vectorizer.
        """
        # Ensure 'sentiment' column exists
        if 'sentiment' not in self.df.columns:
            self.perform_sentiment_analysis()
        
        # Define binary sentiment
        self.df['sentiment_binary'] = self.df['sentiment'].apply(lambda x: 1 if x > 0 else 0)

        X = self.df[self.cleaned_text_column]
        y = self.df['sentiment_binary']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        pipeline = Pipeline([
            ('vectorizer', CountVectorizer(max_features=1000, stop_words=self.stop_words)),
            ('classifier', LogisticRegression(max_iter=1000))
        ])

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        print("Classification Report:")
        print(classification_report(y_test, y_pred))

        print("Confusion Matrix:")
        sns.heatmap(confusion_matrix(y_test, y_pred), annot=True, fmt='d', cmap='Blues')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title('Confusion Matrix')
        plt.show()

        return pipeline

    def generate_report(self):
        """
        Generate a comprehensive report of the analyses.
        """
        self.plot_rating_distribution()
        self.generate_wordcloud()
        self.perform_sentiment_analysis()
        self.plot_sentiment_distribution()
        lda, feature_names = self.perform_topic_modeling()
        self.display_topics(lda, feature_names)
        self.plot_topic_distribution(lda)
        self.train_sentiment_classifier()
# Example Usage
if __name__ == "__main__":
    # Charger les données
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
    analyser.generate_report()