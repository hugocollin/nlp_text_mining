import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.functions_db import  get_restaurants_with_reviews_and_users

from transformers import pipeline
from wordcloud import WordCloud

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

 
    def summarize_reviews(self, df):
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        all_reviews = ' '.join(df['review'].values)
        
        # Split the reviews into chunks of 1024 tokens
        max_chunk_length = 1024
        chunks = [all_reviews[i:i + max_chunk_length] for i in range(0, len(all_reviews), max_chunk_length)]
        
        percent = int(len(chunks) * 0.07)
        if percent < 1:
            percent = len(chunks)
        sample_of_chunks_alea = np.random.choice(chunks, percent)
        
        # Summarize each chunk and combine the summaries
        summaries = []
        print(len(chunks))
        for id, chunk in enumerate(sample_of_chunks_alea):
            print(f"Summarizing chunk of {id} characters...")
            summary = summarizer(chunk, max_length=50, min_length=30, do_sample=True)
            summaries.append(summary[0]['summary_text'])
            print(summary[0]['summary_text'])
        
        summary = ' '.join(summaries)
        return summary



    def generate_wordcloud(self):
        tous_avis = ' '.join(self.data['review_cleaned'])
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(tous_avis)
        return wordcloud
    

