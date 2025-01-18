from searchengine import trip_finder as tf
from db.models import  get_all_restaurants
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from searchengine.trip_finder import SearchEngine, restaurant_info_extractor
import time
import pandas as pd

# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()

restaurants = get_all_restaurants(session)



restaurants_scrapped = [r for r in restaurants if r.scrapped == 1]

df_total = pd.DataFrame()

for res in restaurants_scrapped:

    time.sleep(2)
    print(res.nom)
    print(res.url_link)
    print(res.id_restaurant)
    mod = restaurant_info_extractor()
    mod.scrape_info(res.url_link)
    df_avis, df_details, df_location, _ = mod.to_dataframe()
    df_avis['restaurant_id'] = res.id_restaurant
    df_avis['url_restaurant'] = res.url_link
    df_details['restaurant_id'] = res.id_restaurant
    df_details['url_restaurant'] = res.url_link
    df_location['restaurant_id'] = res.id_restaurant
    df_location['url_restaurant'] = res.url_link
    
    df_avis.to_csv(f'data/avis_{res.id_restaurant}.csv')
    df_details.to_csv(f'data/details_{res.id_restaurant}.csv')
    df_location.to_csv(f'data/location_{res.id_restaurant}.csv')
    