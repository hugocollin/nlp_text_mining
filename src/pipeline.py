import time
import litellm
import pandas as pd
from src.searchengine.trip_finder import SearchEngine, restaurant_info_extractor
from src.nlp.analyse import NLPAnalysis
from src.nlp.pretraitement import NLPPretraitement
from typing import Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.update_db import insert_review, insert_user, insert_restaurant, clear_reviews_of_restaurant, insert_restaurant_reviews, update_scrapped_status_for_reviews, update_restaurant_columns
from src.db.functions_db import parse_french_date, get_every_reviews, get_restaurant, get_restaurants_with_reviews, process_restaurant_data, get_all_restaurants, get_user_and_review_from_restaurant_id, get_restaurants_with_reviews_and_users, parse_to_dict, update_restaurant, update_restaurant_data, get_session, init_db, review_from_1_rest_as_df, add_resume_avis_to_restaurant, get_all_reviews_from_list_restaurants

# Définition de la classe Transistor  
class Transistor:
    # Constructor
    def __init__(self):
        bdd = create_engine('sqlite:///restaurant_reviews.db')
        Session = sessionmaker(bind=bdd)
        self.session = Session()
        self.search_engine = None
        self.nlp_analysis = None
        self.nlp_pretraitement = None
        self.bdd = bdd
        self.restaurant_info_extractor = None

    # Méthode d'affichage
    def __str__(self):
        print("Transistor")
        if self.session:
            print("Session: ", self.session)
        if self.search_engine:
            print("Search Engine: ", self.search_engine)
        if self.nlp_analysis:
            print("NLP Analysis: ", self.nlp_analysis)
        if self.nlp_pretraitement:
            print("NLP Pretraitement: ", self.nlp_pretraitement)
        if self.bdd:
            print("BDD: ", self.bdd)
        return ""

    # Méthode de nettoyage
    def clear(self):
        self.session.close()
        self.session = None
        self.search_engine = None
        self.nlp_analysis = None
        self.nlp_pretraitement = None
        self.bdd = None

    # Méthode d'initialisation du moteur de recherche
    def initiate_search(self):
        self.search_engine = SearchEngine()

    # Méthode d'initialisation de l'extraction d'informations
    def initiate_restaurant_info_extractor(self):
        self.restaurant_info_extractor = restaurant_info_extractor()
        return self.restaurant_info_extractor

    # Méthode d'initialisation du traitement NLP
    def initiate_processing(self):
        self.nlp_pretraitement = NLPPretraitement()

    # Méthode d'initialisation de l'analyse NLP
    def initiate_analytic(self):
        self.nlp_analysis = NLPAnalysis()
    
    # Méthode d'initialisation de la base de données
    def init_db(self):
        return init_db()
    
    # Méthode de récupération de la session
    def get_session(self):
        return get_session(self.bdd)
    
    # Méthode de récupération d'un chunk de session
    def get_session_chunk(self, bdd):
        return get_session(bdd)

    # Méthode de récupération de tous les restaurants  
    def get_restaurants(self):
        return get_all_restaurants(self.session)

    # Méthode de récupération des restaurants non scrappés
    def get_restaurants_non_scrapped(self):
        restaurants = self.get_restaurants()
        return [r for r in restaurants if r.scrapped == 0]
    
    # Méthode de récupération des résumés d'avis nettoyés pour un restaurant
    def clear_reviews_of_restaurant(self, restaurant_id):
        return clear_reviews_of_restaurant(restaurant_id, self.session)

    # Méthode d'insertion d'un utilisateur
    def insert_user(self, user_name, user_profile, num_contributions):
        return insert_user(user_name, user_profile, num_contributions)

    # Méthode d'insertion d'un restaurant
    def insert_restaurant(self, name, **kwargs):
        return insert_restaurant(name, **kwargs)

    # Méthode d'insertion d'un avis
    def insert_review(self, review, id_restaurant):
        return insert_review(review, id_restaurant)

    # Méthode de parsing d'une date en français
    def parse_french_date(self, date_str):
        return parse_french_date(date_str)

    # Méthode de parsing d'une chaîne de caractères en dictionnaire
    def parse_to_dict(self, data_str):
        return parse_to_dict(data_str)

    # Méthode de récupération des avis d'un restaurant
    def review_from_1_rest_as_df(self, restaurant_id):
        return review_from_1_rest_as_df(self.session, restaurant_id)
    
    # Méthode de mise à jour d'un restaurant
    def update_restaurant(self, name, **kwargs):
        return update_restaurant(name, **kwargs)

    # Méthode de mise à jour des données d'un restaurant
    def update_restaurant_data(self, restaurant_name, restaurant_data):
        return update_restaurant_data(restaurant_name, restaurant_data)

    # Méthode d'insertion des avis d'un restaurant
    def insert_restaurant_reviews(self, restaurant_id, reviews):
        return insert_restaurant_reviews(restaurant_id, reviews, self.session)

    # Méthode de récupération des restaurants avec avis
    def get_restaurants_with_reviews(self):
        return get_restaurants_with_reviews()

    # Méthode de mise à jour du statut scrappé des avis
    def update_scrapped_status_for_reviews(self, restaurant_names):
        return update_scrapped_status_for_reviews(self.session, restaurant_names)

    # Méthode de mise à jour des colonnes d'un restaurant
    def update_restaurant_columns(self, restaurant_name, updates):
        return update_restaurant_columns(restaurant_name, updates, self.session)

    # Méthode de récupération d'un restaurant
    def get_restaurant(self, restaurant_id=None, restaurant_name=None):
        return get_restaurant(self.session, restaurant_id, restaurant_name)

    # Méthode de traitement des données d'un restaurant
    def process_restaurant_data(self, avis_df, location_df, details_df, restaurant_id):
        return process_restaurant_data(avis_df, location_df, details_df, restaurant_id)
    
    # Méthode de récupération de tous les restaurants
    def get_all_restaurants(self):
        return get_all_restaurants(self.session)
    
    # Méthode de récupération des avis et utilisateurs d'un restaurant à partir de son ID
    def get_user_and_review_from_restaurant_id(self, restaurant_id):
        return get_user_and_review_from_restaurant_id( self.session, restaurant_id)
    
    # Méthode de récupération des restaurants avec avis et utilisateurs
    def get_restaurants_with_reviews_and_users(self):
        return get_restaurants_with_reviews_and_users(self.session)

    # Méthode d'ajout d'un résumé d'avis à un restaurant
    def add_resume_avis_to_restaurant(self, restaurant_id, resume):
        return add_resume_avis_to_restaurant( self.session, restaurant_id, resume)

    # Méthode de récupération de tous les avis
    def get_every_reviews(self):
        return get_every_reviews(self.session)
    
    # Méthode de récupération de tous les avis d'une liste de restaurants
    def get_all_reviews_from_list_restaurants(self, list_restaurants):
        return get_all_reviews_from_list_restaurants(self.session, list_restaurants)

# Définition de la classe Pipeline héritant de Transistor    
class Pipeline(Transistor):
    # Constructeur
    def __init__(self):
        super().__init__()
        self.url = None

    # Méthode d'affichage
    def __str__(self):
        print("Pipeline")
        return ""

    # Méthode d'ajout d'un nouveau restaurant (méthode principale du pipeline)
    def add_new_restaurant(self, restaurant):

        # Initialisation du moteur de recherche
        print("Adding new restaurant")
        self.url = restaurant.url_link
        print("url : " , self.url)
        self.initiate_restaurant_info_extractor()
        print("Restaurant info extractor initiated")

        # Extraction des informations du restaurant
        self.restaurant_info_extractor.scrape_info(self.url)
        print("Restaurant info scraped")

        # Extraction des avis du restaurant
        self.restaurant_info_extractor.scrape_restaurant(self.url)
        print("Restaurant Reviews scraped")
        df_avis, df_details, df_location, df_reviews = self.restaurant_info_extractor.to_dataframe()
        print("Dataframes created")

        # Vérification des colonnes
        if 'review' not in df_reviews.columns:
            print("Error: 'review' column is missing from df_reviews")
            return
        
        # Processing des données du restaurant
        self.process_restaurant_data(df_avis, df_location, df_details,restaurant.id_restaurant )
        print("Info processed")

        # Nettoyage des avis
        self.initiate_processing()

        # Initialisation de l'analyse NLP
        self.initiate_analytic()
        print("Processing initiated")

        # Nettoyage des avis
        df_reviews = self.clean_reviews_a_la_volée(df_reviews)

        # Analyse du sentiment des avis
        df_reviews = self.nlp_pretraitement.sentiment_analysis(df_reviews)
        print(df_reviews["sentiment"].value_counts())
        print("Reviews cleaned")

        # Création du résumé des avis
        resume = self.make_analyse_resume(df_reviews)
        print("Reviews analysed")

        # Insertion du restaurant et des avis dans la base de données
        self.insert_restaurant_reviews(restaurant.id_restaurant, df_reviews)
        print("Reviews inserted")

        # Appel de l'API Mistral
        role_prompt = "Tu es un assistant spécialisé dans l'analyse d'avis clients. À partir du texte suivant, rédige un résumé clair et concis qui met en évidence les aspects récurrents mentionnés par les clients. L'objectif est de fournir une vue d'ensemble générale qui reflète les impressions générales afin de l'afficher sur un site internet sous la forme d'une phrase. La réponse doit être limité à 50 mots."
        query = resume
        response = self.api_Mistral(query, role_prompt)

        # Ajout du résumé d'avis au restaurant
        self.add_resume_avis_to_restaurant(restaurant.id_restaurant, response["response"])
        
        print("[INFO] Le restaurant a été ajouté avec succès, vous pouvez maintenant rafraichir la page")
        time.sleep(2)
        self.clear()
     
    # Méthode de nettoyage des avis
    def clean_reviews_a_la_volée(self, df_reviews):
        df_reviews['review_cleaned'] = ""
        print("Processing initiated")
        for index, row in df_reviews.iterrows():
                review = row['review']
                net = self.nlp_pretraitement.nettoyer_avis(review)
                df_reviews.at[index, 'review_cleaned'] = net
        print("Reviews cleaned")

        return df_reviews
        
    # Méthode d'analyse du résumé des avis
    def make_analyse_resume(self, df_reviews):

        # Initialisation de l'analyse NLP
        self.initiate_analytic()

        # Création du résumé des avis
        resume = self.nlp_analysis.summarize_reviews(df_reviews)
        print("Reviews analysed")
        return resume
    
    # Méthode de nettoyage des avis
    def clean_reviews(self, restaurant_id):

        # Initialisation du traitement NLP
        self.initiate_processing()

        # Initialisation de l'analyse NLP
        self.initiate_analytic()
        print("Processing initiated")

        # Récupération des avis du restaurant
        df = review_from_1_rest_as_df(self.session, restaurant_id)

        # Nettoyage des avis
        df_review = self.clean_reviews_a_la_volée(df)
        print("Reviews cleaned")

        # Création du résumé des avis
        resume = self.make_analyse_resume(df_review)

        # Appel de l'API Mistral
        role_prompt = "Tu es un assistant spécialisé dans l'analyse d'avis clients. À partir du texte suivant, rédige un résumé clair et concis qui met en évidence les aspects récurrents mentionnés par les clients. L'objectif est de fournir une vue d'ensemble générale qui reflète les impressions générales afin de l'afficher sur un site internet sous la forme d'une phrase. La réponse doit être limité à 50 mots."
        query = resume
        response = self.api_Mistral(query, role_prompt)
        
        # Ajout du résumé d'avis au restaurant
        self.add_resume_avis_to_restaurant(restaurant_id, response["response"])
        print("Reviews inserted")
        print("Restaurant added")
        self.clear()
        time.sleep(2)
        
    # Méthode de vectorisation des avis
    def vectorize_reviews(self, keyword):
        df_review  = self.get_every_reviews()
        restaurants = self.get_all_restaurants()
        df_restaurants = pd.DataFrame([{
            "id_restaurant": r.id_restaurant,
            "nom": r.nom,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "rank": r.rank,
            "prix_min": r.prix_min,
            "prix_max": r.prix_max,
            "etoiles_michelin": r.etoiles_michelin,
            "note_globale": r.note_globale,
            "qualite_prix_note": r.qualite_prix_note,
            "cuisine_note": r.cuisine_note,
            "service_note": r.service_note,
            "ambiance_note": r.ambiance_note,
            "cuisines": r.cuisines
        } for r in restaurants if r.scrapped == 1])

        # Jointure des avis et des restaurants
        df_review = pd.merge(df_review, df_restaurants, left_on="restaurant_id", right_on="id_restaurant", how="inner")
        
        # Initialisation du traitement NLP
        self.initiate_analytic()
        print("Processing initiated")
        
        # Prétraitement des avis
        self.initiate_processing()
        df_review = df_review.dropna()

        # Processing des avis
        df = self.nlp_pretraitement.preprocess_reviews(df_review)
        print("Preprocessing done")

        # Vectorisation des avis
        df_restaurants , features_3d , idx , sim = self.nlp_analysis.vectorize_reviews(df, df_restaurants, keyword)
        print("Processing done") 
        print(idx , sim)
        return df_restaurants, features_3d , idx , sim 
        
    # Méthode de connexion et de mise en forme de l'appel à l'API Mistral
    def api_Mistral(self, query, role_prompt, generation_model: str = "mistral-large-latest", max_tokens: int = 100, temperature: float = 0.7) -> Dict[str, str]:

        # Construction de la requête
        query_prompt = f"""
        # Question:
        {query}

        # Réponse:
        """

        # Mise en forme de la requête
        prompt = [
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": query_prompt},
        ]

        # Appel à l'API Mistral
        response = litellm.completion(
            model=f"mistral/{generation_model}",
            messages=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Récupération de la réponse
        response_text = str(response.choices[0].message.content)

        return {"response": response_text}