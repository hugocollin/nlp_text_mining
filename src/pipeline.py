

from src.db.update_db import insert_review , insert_user  , insert_restaurant, clear_reviews_of_restaurant , insert_restaurant_reviews , update_scrapped_status_for_reviews , update_restaurant_columns

from src.db.functions_db import   parse_french_date  , get_restaurant   , get_restaurants_with_reviews ,   process_restaurant_data, get_all_restaurants, get_user_and_review_from_restaurant_id, get_restaurants_with_reviews_and_users , parse_to_dict  , update_restaurant , update_restaurant_data  , get_session   , init_db, review_from_1_rest_as_df
import time
import pandas as pd
import litellm
from typing import Dict

from src.nlp.analyse import NLPAnalysis
from src.nlp.pretraitement import NLPPretraitement
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.searchengine.trip_finder import SearchEngine , restaurant_info_extractor

        
# class transitor that will be used to make the connection between the different classes and the database and the streamlit pages
class Transistor:
    def __init__(self):
        bdd = create_engine('sqlite:///restaurant_reviews.db')
        Session = sessionmaker(bind=bdd)
        self.session = Session()
        self.search_engine = None
        self.nlp_analysis = None
        self.nlp_pretraitement = None
        self.bdd = bdd
        self.restaurant_info_extractor = None
    
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

    

    
    def load_data(self):
        return self.nlp_analysis.load_data()
    
    def preprocess_reviews(self):
        return self.nlp_analysis.preprocess_reviews()
    
    def search(self, query):
        return self.search_engine.search(query)
    
    def get_restaurants_with_reviews_and_users(self):
        return self.nlp_analysis.get_restaurants_with_reviews_and_users()
    
    def insert_user(self, user):
        return insert_user(self.session, user)
    
    
    def load_data(self):
        return self.nlp_analysis.load_data()
    
    def init_db(self):
        return init_db()
    
    def get_session(self):
        return get_session(self.bdd)
    
    def get_session_chunk(self, bdd):
        return get_session(bdd)
    
    def preprocess_reviews(self):
        return self.nlp_analysis.preprocess_reviews()
    
    def search(self, query):
        return self.search_engine.search(query)
    
    def get_restaurants_with_reviews_and_users(self):
        return self.nlp_analysis.get_restaurants_with_reviews_and_users()
            
    def initiate_processing(self):
        self.nlp_pretraitement = NLPPretraitement()
    def initiate_analytic(self):
        self.nlp_analysis = NLPAnalysis()
        
    
    def initiate_search(self):
        self.search_engine = SearchEngine()
        
    def initiate_restaurant_info_extractor(self):
        self.restaurant_info_extractor = restaurant_info_extractor()
        return self.restaurant_info_extractor
    
    def clear(self):
        self.session.close()
        self.session = None
        self.search_engine = None
        self.nlp_analysis = None
        self.nlp_pretraitement = None
        self.bdd = None
    
    def initiate_search(self):
        self.search_engine = SearchEngine()
    
    def get_restaurants(self):
        return get_all_restaurants(self.session)

    def get_restaurants_non_scrapped(self):
        restaurants = self.get_restaurants()
        return [r for r in restaurants if r.scrapped == 0]
    
    def clear_reviews_of_restaurant(self, restaurant_id):
        return clear_reviews_of_restaurant(restaurant_id, self.session)

############################################################# INIT_DB.py #########################

    def insert_user(self, user_name, user_profile, num_contributions):
        """Redirect to init_db.insert_user"""
        return insert_user(user_name, user_profile, num_contributions)

    def insert_restaurant(self, name, **kwargs):
        """Redirect to init_db.insert_restaurant"""
        return insert_restaurant(name, **kwargs)

    def insert_review(self, review, id_restaurant):
        """Redirect to init_db.insert_review"""
        return insert_review(review, id_restaurant)

    def parse_french_date(self, date_str):
        """Redirect to init_db.parse_french_date"""
        return parse_french_date(date_str)

    def parse_to_dict(self, data_str):
        """Redirect to init_db.parse_to_dict"""
        return parse_to_dict(data_str)

    def review_from_1_rest_as_df(self, restaurant_id):
        """Redirect to function.review_from_1_rest_as_df"""
        return review_from_1_rest_as_df(self.session, restaurant_id)
    
    def update_restaurant(self, name, **kwargs):
        """Redirect to init_db.update_restaurant"""
        return update_restaurant(name, **kwargs)

    def update_restaurant_data(self, restaurant_name, restaurant_data):
        """Redirect to init_db.update_restaurant_data"""
        return update_restaurant_data(restaurant_name, restaurant_data)

    def insert_restaurant_reviews(self, restaurant_id, reviews):
        """Redirect to init_db.insert_restaurant_reviews"""
        return insert_restaurant_reviews(restaurant_id, reviews, self.session)

    def get_restaurants_with_reviews(self):
        """Redirect to init_db.get_restaurants_with_reviews"""
        return get_restaurants_with_reviews()

    def update_scrapped_status_for_reviews(self, restaurant_names):
        """Redirect to init_db.update_scrapped_status_for_reviews"""
        return update_scrapped_status_for_reviews(self.session, restaurant_names)

    def update_restaurant_columns(self, restaurant_name, updates):
        """Redirect to init_db.update_restaurant_columns"""
        return update_restaurant_columns(restaurant_name, updates, self.session)

    def get_restaurant(self, restaurant_id=None, restaurant_name=None):
        """Redirect to init_db.get_restaurant"""
        return get_restaurant(self.session, restaurant_id, restaurant_name)

    def process_restaurant_data(self, avis_df, location_df, details_df, restaurant_id):
        """Redirect to init_db.process_restaurant_data"""
        return process_restaurant_data(avis_df, location_df, details_df, restaurant_id)
    
########################## MODELS.py #########################


    def get_all_restaurants(self):
        """Redirect to models.get_all_restaurants"""
        return get_all_restaurants(self.session)
    
    def get_user_and_review_from_restaurant_id(self, restaurant_id):
        """Redirect to models.get_user_and_review_from_restaurant_id"""
        return get_user_and_review_from_restaurant_id( self.session, restaurant_id)
    
    def get_restaurants_with_reviews_and_users(self):
        """Redirect to models.get_restaurants_with_reviews_and_users"""
        return get_restaurants_with_reviews_and_users(self.session)






############################################################# PIPELINE #########################

    
class Pipeline(Transistor):
    def __init__(self):
        super().__init__()
        self.url = None
        
    def __str__(self):
        print("Pipeline")
        return ""

    
    def add_new_restaurant(self, restaurant):
        print("Adding new restaurant")
        
        self.url = restaurant.url_link
        print("url : " , self.url)
        self.initiate_restaurant_info_extractor()
        print("Restaurant info extractor initiated")
        self.restaurant_info_extractor.scrape_info(self.url)
        print("Restaurant info scraped")
        self.restaurant_info_extractor.scrape_restaurant(self.url)
        print("Restaurant Reviews scraped")
        df_avis, df_details, df_location, df_reviews = self.restaurant_info_extractor.to_dataframe()
        print("Dataframes created")
        self.process_restaurant_data(df_avis, df_location, df_details,restaurant.id_restaurant )
        print("Info processed")
        
        self.initiate_processing()
        self.initiate_analytic()
        print("Processing initiated")
        df_reviews = self.clean_reviews_a_la_volée(df_reviews)
        
        print("Reviews cleaned")
        resume = self.make_analyse_resume(df_reviews)
        print(resume)
        print("Reviews analysed")
        
        # API MISTRAL
        role_prompt = "Tu es un assistant qui résume les avis des clients pour un restaurant. À partir des commentaires suivants, fournis un résumé concis des avis afin de se faire une idée générale du restaurant."
        query = "Hello World" # à changer
        response = self.api_Mistral(query, role_prompt)
        print(response["response"]) # à changer
        
        time.sleep(10)
        self.insert_restaurant_reviews(restaurant.id_restaurant, df_reviews)
        print("Reviews inserted")
        print("Restaurant added")
        self.clear()
          
    
    def clean_reviews_a_la_volée(self, df_reviews):
        df_reviews['review_cleaned'] = ""
        print("Processing initiated")
        for index, row in df_reviews.iterrows():
                review = row['review']
                net = self.nlp_pretraitement.nettoyer_avis(review)

                
                df_reviews.at[index, 'review_cleaned'] = net
        print("Reviews cleaned")
        print(df_reviews)
        return df_reviews
        
    
    def make_analyse_resume(self, df_reviews):
        self.initiate_analytic()
        resume = self.nlp_analysis.summarize_reviews(df_reviews)
        print("Reviews analysed")
        return resume
    
    def clean_reviews(self, restaurant_id):
        self.initiate_processing()
        self.initiate_analytic()
        print("Processing initiated")
        
        # make avis a datframe
        df =review_from_1_rest_as_df(self.session, restaurant_id)
        
    
    
     
        df_review = self.clean_reviews_a_la_volée(df)
        print("Reviews cleaned")
        resume = self.make_analyse_resume(df_review)
        print(resume)
        time.sleep(5)
        
    def api_Mistral(self, query, role_prompt, generation_model: str = "mistral-large-latest", max_tokens: int = 50, temperature: float = 0.7) -> Dict[str, str]:
        query_prompt = f"""
        # Question:
        {query}

        # Réponse:
        """
        prompt = [
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": query_prompt},
        ]
        response = litellm.completion(
            model=f"mistral/{generation_model}",
            messages=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        response_text = str(response.choices[0].message.content)
        return {"response": response_text}
    
    def clean_reviews_test(self, restaurant_id):
        self.initiate_processing()
        print("Processing initiated")
        avis = self.get_user_and_review_from_restaurant_id(restaurant_id)
        print("Avis recupérés")
        print(avis[0][1].review_text)
        net = self.nlp_pretraitement.nettoyer_avis(avis[0][1].review_text)
        print(net)
  
    
    
    
    
    
    
    
# def insert_restaurant_reviews(restaurant, reviews):
#     # Insérer les avis pour le restaurant
#     try:
#         for review in reviews:
#             review_data = {
#                 "user": review['user'],
#                 "user_profile": review['user_profile'],
#                 "num_contributions": review['num_contributions'],
#                 "date": review['date_review'],
#                 "title": review['title'],
#                 "review": review['review'],
#                 "rating": review['rating'],
#                 "type_visit": review['type_visit']
#             }
#             insert_review(review_data, restaurant.id_restaurant)
#     except Exception as e:
#         print(f"Erreur lors de l'insertion des avis pour le restaurant {restaurant.nom} : {e}")

