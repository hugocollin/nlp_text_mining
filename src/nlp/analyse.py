import pandas as pd
import numpy as np
from transformers import pipeline
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.feature_extraction.text import  TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

class NLPAnalysis:
    def __init__(self):
        
        self.vectorizer = TfidfVectorizer(max_features=10000)
        self.restaurant_features = None
        self.df = None
   
    def vectorize_reviews(self, df, df_restaurants, keyword = None):
        
        self.vectorizer = TfidfVectorizer(max_features=5000)
        X_tfidf = self.vectorizer .fit_transform(df["review_cleaned"])
        df["tfidf_vector"] = list(X_tfidf.toarray())
        # Ajouter les vecteurs TF-IDF agrégés par restaurant
        aggregated_tfidf = (
            df.groupby("restaurant_id")["tfidf_vector"]
            .apply(lambda x: np.mean(np.vstack(x), axis=0))  # Moyenne des vecteurs TF-IDF
            .reset_index()
        )
        aggregated_tfidf.columns = ["id_restaurant", "tfidf_vector"]
        df_restaurants = df_restaurants.merge(aggregated_tfidf, on="id_restaurant", how="left")

        # --- Étape 6 : Clustering avec KMeans ---
        features = ["prix_min", "prix_max", "note_globale", "qualite_prix_note", "cuisine_note", "service_note", "ambiance_note"]
        self.restaurant_features = pd.concat([df_restaurants[features], pd.DataFrame(aggregated_tfidf["tfidf_vector"].to_list())], axis=1)
        self.restaurant_features.columns = self.restaurant_features.columns.astype(str)
        # remove nan values
        self.restaurant_features = np.nan_to_num(self.restaurant_features)
        
        features_scaled = StandardScaler().fit_transform(self.restaurant_features)
        self.pca = PCA(n_components=3)
        features_3d = self.pca.fit_transform(features_scaled)
        self.features_3d = features_3d
        if keyword is not None:
            idx, sim = self.find_restaurant_by_keyword(df, df_restaurants, keyword)
            features_3d = None
        #make cluster insteaed of keyword
        else:
            df_restaurants , features_3d = self.cluster_restaurants(df_restaurants)
            idx = None
            sim = None
            
        return df_restaurants , features_3d , idx , sim


            
            
            
    def find_restaurant_by_keyword(self, df, df_restaurants, keyword):
        
        # --- Étape 5 : Vectorisation des avis avec TF-IDF ---
        X_tfidf = self.vectorizer.transform([keyword])
        keyword_vector = X_tfidf.toarray()
        
        # Create additional features (set to zero or appropriate defaults)
        additional_features = np.zeros((keyword_vector.shape[0], 7))
        
        # Concatenate tfidf_vector with additional features
        full_keyword_vector = np.concatenate([additional_features, keyword_vector], axis=1)
        
        # Apply PCA
        full_keyword_vector = self.pca.transform(full_keyword_vector)
        
        # Calculer la similarité cosinus entre le mot-clé et les restaurants
        similarities = cosine_similarity(full_keyword_vector, self.features_3d)
        best_match_idx = np.argmax(similarities)
        
        best_match = df_restaurants.iloc[best_match_idx]
        id_restaurant = best_match["id_restaurant"]
        similarity  = similarities[0][best_match_idx] 
        return  id_restaurant , similarity
    
            
            


















    def cluster_restaurants(self, df_restaurants):
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(self.restaurant_features)

        # Réduction de dimensions
        pca = PCA(n_components=3)
        # remove nan values
        features_scaled = np.nan_to_num(features_scaled)
        features_3d = pca.fit_transform(features_scaled)

        # Appliquer KMeans
        kmeans = KMeans(n_clusters=5, random_state=42)
        df_restaurants["cluster"] = kmeans.fit_predict(features_scaled)

        return df_restaurants , features_3d
        


 
    def summarize_reviews(self, df):
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        all_reviews = ' '.join(df['review'].values)
        
        # Split the reviews into chunks of 1024 tokens
        max_chunk_length = 1024
        chunks = [all_reviews[i:i + max_chunk_length] for i in range(0, len(all_reviews), max_chunk_length)]
        
        nbr_chunks = 20
        if len(chunks) < nbr_chunks:
            nbr_chunks = len(chunks)
        sample_of_chunks_alea = np.random.choice(chunks, nbr_chunks)
        
        # Summarize each chunk and combine the summaries
        summaries = []
        print("nb chunks : " , len(chunks))
        for id, chunk in enumerate(sample_of_chunks_alea):
            print(f"Summarizing chunk {id} ...")
            summary = summarizer(chunk, max_length=60, min_length=40, do_sample=True)
            summaries.append(summary[0]['summary_text'])
            print(summary[0]['summary_text'])
        
        summary = ' '.join(summaries)
        return summary
