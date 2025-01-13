
import sys 
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analyse import NLPAnalysis

def test_nlp_analysis():
    # Instanciation de la classe
    nlp_analysis = NLPAnalysis()

    # Chargement des données
    nlp_analysis.load_data()

    # Vérification du DataFrame
    print("Aperçu des données :")
    print(nlp_analysis.data.head())

    # Entraînement du modèle LSTM
    nlp_analysis.train_lstm_model()

    # Résumer les avis par restaurant
    summaries = nlp_analysis.summarize_reviews()
    print("Aperçu des résumés :")
    print(summaries.head())

    # Génération du nuage de mots
    wordcloud = nlp_analysis.generate_wordcloud()
    print("Nuage de mots généré avec succès.")

# Exécution du test
if __name__ == "__main__":
    test_nlp_analysis()
    