
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys 
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.models import get_user_and_review_from_restaurant_id
from pretraitement import NLPPretraitement
# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()

def test_pretraitement():
    # recuerer les reviews du 1er restaurant
    pretraitement = NLPPretraitement ()

    review = get_user_and_review_from_restaurant_id(session, 1)
    tokens = pretraitement.nettoyer_avis(review[0][1].review_text)
    print(tokens)
    # Exécution du test
if __name__ == "__main__":
    test_pretraitement()