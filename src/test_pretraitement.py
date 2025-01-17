
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys 
import os

import db.models as models
from nlp.pretraitement import NLPPretraitement
# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()


def test_pretraitement():
    # recuerer les reviews du 1er restaurant
    pretraitement = NLPPretraitement ()
    
    # Initialiser le DataFrame
    pretraitement.extraction_donnees()
    
    # nettoyage des donnees
    review = models.get_user_and_review_from_restaurant_id(session, 1)
    pretraitement.nettoyer_avis(review[0][1].review_text)

    #Appliqué le nettoyage
    pretraitement.appliquer_nettoyage()
    
    #vectorisation
    pretraitement.vectorisation()
    
    #afficher dataframe
    #tokens = 
    df = pretraitement.afficher_dataframe_complet()
    #print(tokens)
    
    print("Aperçu des données :")
    print(df.head().to_csv("apercu_data.csv"))
    pretraitement.sauvegarder_donnees()

    # Exécution du test
if __name__ == "__main__":
    test_pretraitement()
    
