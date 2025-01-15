
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

    pretraitement.extraction_donnees()
    pretraitement.appliquer_nettoyage()
    pretraitement.vectorisation()
    df = pretraitement.afficher_dataframe_complet()
    print("Aperçu des données :")
    print(df.head().to_csv("apercu_data.csv"))
    pretraitement.sauvegarder_donnees()
    # Exécution du test
if __name__ == "__main__":
    test_pretraitement()