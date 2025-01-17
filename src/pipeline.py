# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.db.models import  get_all_restaurants , get_user_and_review_from_restaurant_id , get_restaurants_with_reviews_and_users

from src.db.init_db import insert_user , insert_restaurant , insert_review , parse_french_date, parse_to_dict , process_restaurant_csv , update_restaurant , update_restaurant_data , insert_restaurant_reviews ,get_restaurants_from_folder , process_csv_files , get_restaurants_with_reviews , update_scrapped_status_for_reviews , update_restaurant_columns , get_restaurant , add_columns_to_table , fill_review_cleaned_column , fill_sentiment_column , fill_resume_avis_column , check_restaurants_in_db , create_restaurants_from_csv , process_restaurant_data , clear_reviews_of_restaurant 

# from src.nlp.analyse import NLPAnalysis
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
    
    def insert_user(self, user):
        return insert_user(self.session, user)
    
    def nettoyer_avis(self, avis):
        return self.nlp_pretraitement.nettoyer_avis(avis)
    
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
    
    def nettoyer_avis(self, avis):
        return self.nlp_pretraitement.nettoyer_avis(avis)
    
    def load_data(self):
        return self.nlp_analysis.load_data()
    
    def preprocess_reviews(self):
        return self.nlp_analysis.preprocess_reviews()
    
    def search(self, query):
        return self.search_engine.search(query)
    
    def get_restaurants_with_reviews_and_users(self):
        return self.nlp_analysis.get_restaurants_with_reviews_and_users()
            
    def initiate_processing(self):
        self.nlp_pretraitement = NLPPretraitement()
        
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

    def process_restaurant_csv(self, file_name):
        """Redirect to init_db.process_restaurant_csv"""
        return process_restaurant_csv(file_name)

    def update_restaurant(self, name, **kwargs):
        """Redirect to init_db.update_restaurant"""
        return update_restaurant(name, **kwargs)

    def update_restaurant_data(self, restaurant_name, restaurant_data):
        """Redirect to init_db.update_restaurant_data"""
        return update_restaurant_data(restaurant_name, restaurant_data)

    def insert_restaurant_reviews(self, restaurant_id, reviews):
        """Redirect to init_db.insert_restaurant_reviews"""
        return insert_restaurant_reviews(restaurant_id, reviews, self.session)

    def get_restaurants_from_folder(self, scrapping_dir):
        """Redirect to init_db.get_restaurants_from_folder"""
        return get_restaurants_from_folder(scrapping_dir)

    def process_csv_files(self, scrapping_dir, with_reviews=True):
        """Redirect to init_db.process_csv_files"""
        return process_csv_files(scrapping_dir, self.session, with_reviews)

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

    def add_columns_to_table(self, table_name, columns):
        """Redirect to init_db.add_columns_to_table"""
        return add_columns_to_table(self.bdd, table_name, columns)

    def fill_review_cleaned_column(self, df):
        """Redirect to init_db.fill_review_cleaned_column"""
        return fill_review_cleaned_column(df, self.session)

    def fill_sentiment_column(self, df):
        """Redirect to init_db.fill_sentiment_column"""
        return fill_sentiment_column(df, self.session)

    def fill_resume_avis_column(self, df):
        """Redirect to init_db.fill_resume_avis_column"""
        return fill_resume_avis_column(df, self.session)

    def check_restaurants_in_db(self, resto_list):
        """Redirect to init_db.check_restaurants_in_db"""
        return check_restaurants_in_db(resto_list, self.session)

    def create_restaurants_from_csv(self, csv_path):
        """Redirect to init_db.create_restaurants_from_csv"""
        return create_restaurants_from_csv(csv_path, self.session)
    
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
        self.restaurant_info_extractor.to_csv()
        self.process_restaurant_data(df_avis, df_location, df_details,restaurant.id_restaurant )
        print("Info processed")
        self.insert_restaurant_reviews(restaurant.id_restaurant, df_reviews)
        print("Reviews inserted")
        print("Restaurant added")
    
    
    
    
    
    
    
    
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

