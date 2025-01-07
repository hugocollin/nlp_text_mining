from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Restaurant, Review, User

# Créer l'engine et la session
engine = create_engine('sqlite:///restaurant_reviews.db')  # Remplacez par votre URI de base de données
Session = sessionmaker(bind=engine)
session = Session()

# Récupérer tous les restaurants
restaurants = get_all_restaurants(session)
for restaurant in restaurants:
    print(f"Restaurant ID: {restaurant.id_restaurant}, Name: {restaurant.nom}")

# Récupérer tous les restaurants avec leurs avis et utilisateurs associés
restaurants_with_reviews = get_restaurants_with_reviews_and_users(session)
for restaurant in restaurants_with_reviews:
    print(f"Restaurant: {restaurant.nom}")
    for review in restaurant.avis:
        print(f"  Review by {review.user.user_profile} (Rating: {review.rating})")

# Fermer la session
session.close()
