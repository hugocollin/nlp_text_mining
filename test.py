
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


import src.db.models as models
import src.nlp.pretraitement as pretraitement
# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()

def test_pretraitement():
    # recuerer les reviews du 1er restaurant
    pretraitementbis = pretraitement.NLPPretraitement ()

    review = models.get_user_and_review_from_restaurant_id(session, 1)
    tokens = pretraitementbis.nettoyer_avis(review[0][1].review_text)
    print(tokens)
    # Exécution du test
if __name__ == "__main__":
    test_pretraitement()