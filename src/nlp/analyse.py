import pandas as pd
import numpy as np
from transformers import pipeline
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import  TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# Définition de la classe NLPAnalysis
class NLPAnalysis:
    # Constructeur
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.restaurant_features = None
        self.df = None

    # Méthode pour vectoriser les avis
    def vectorize_reviews(self, df, df_restaurants, keyword=None):
        self.vectorizer = TfidfVectorizer(max_features=10000)
        X_tfidf = self.vectorizer.fit_transform(df["review_cleaned"])
        df["tfidf_vector"] = list(X_tfidf.toarray())
        
        # Ajout des vecteurs TF-IDF moyens pour chaque restaurant
        aggregated_tfidf = (
            df.groupby("restaurant_id")["tfidf_vector"]
            .apply(lambda x: np.mean(np.vstack(x), axis=0))
            .reset_index()
        )
        aggregated_tfidf.columns = ["id_restaurant", "tfidf_vector"]
        df_restaurants = df_restaurants.merge(aggregated_tfidf, on="id_restaurant", how="left")
        
        # Clustering des restaurants avec KMeans
        features = ["prix_min", "prix_max", "note_globale", "qualite_prix_note", "cuisine_note", "service_note", "ambiance_note"]
        self.restaurant_features = pd.concat(
            [df_restaurants[features], pd.DataFrame(aggregated_tfidf["tfidf_vector"].to_list())],
            axis=1
        )
        self.restaurant_features = np.nan_to_num(self.restaurant_features)

        # Mise à l'échelle et réduction dimensionnelle
        features_scaled = StandardScaler().fit_transform(self.restaurant_features)
        self.pca = PCA(n_components=3)
        self.features_3d = self.pca.fit_transform(features_scaled)
        
        if keyword is not None:
            idx, sim = self.find_restaurant_by_keyword(df, df_restaurants, keyword)
            return df_restaurants, None, idx, sim
        else:
            df_restaurants, features_3d = self.cluster_restaurants(df_restaurants)
            return df_restaurants, features_3d, None, None

    # Méthode pour trouver le restaurant le plus proche d'un mot-clé
    def find_restaurant_by_keyword(self, df, df_restaurants, keyword):
        # Vectorisation du mot-clé
        keyword_vector = self.vectorizer.transform([keyword]).toarray()

        # Calcul de la similarité cosinus entre le mot-clé et les avis
        df["similarity"] = df["tfidf_vector"].apply(lambda x: cosine_similarity([x], keyword_vector)[0][0])

        # Identification de l'avis le plus similaire
        best_match = df.loc[df["similarity"].idxmax()]
        best_restaurant_id = best_match["restaurant_id"]
        similarity_score = best_match["similarity"]
        
        print(f"Restaurant trouvé : {best_restaurant_id}, Similarité : {similarity_score:.4f}")
        return best_restaurant_id, similarity_score

    # Méthode pour clusteriser les restaurants
    def cluster_restaurants(self, df_restaurants):
        # Mise à l'échelle des features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(self.restaurant_features)

        # Réduction de dimensions
        pca = PCA(n_components=3)
        features_scaled = np.nan_to_num(features_scaled)
        features_3d = pca.fit_transform(features_scaled)

        # Application de l'algorithme KMeans
        kmeans = KMeans(n_clusters=5, random_state=42)
        df_restaurants["cluster"] = kmeans.fit_predict(features_scaled)

        return df_restaurants , features_3d

    # Méthode pour résumer les avis
    def summarize_reviews(self, df):
        # Initialisation du modèle de résumé
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        all_reviews = ' '.join(df['review'].values)
        
        # Découpage des avis en chunks
        max_chunk_length = 1024
        chunks = [all_reviews[i:i + max_chunk_length] for i in range(0, len(all_reviews), max_chunk_length)]
        nbr_chunks = 20
        if len(chunks) < nbr_chunks:
            nbr_chunks = len(chunks)
        sample_of_chunks_alea = np.random.choice(chunks, nbr_chunks)
        
        # Création d'un résumé pour chaque chunk
        summaries = []
        print("nb chunks : " , len(chunks))
        for id, chunk in enumerate(sample_of_chunks_alea):
            print(f"Summarizing chunk {id} ...")
            summary = summarizer(chunk, max_length=60, min_length=40, do_sample=True)
            summaries.append(summary[0]['summary_text'])
            print(summary[0]['summary_text'])
      
        summary = ' '.join(summaries)
        return summary