
from nlp.analyse import NLPAnalysis
def test_nlp_analysis():
    # Instanciation de la classe
    nlp_analysis = NLPAnalysis()

    # Chargement des données
    nlp_analysis.load_data()

    # Vérification du DataFrame
    #print("Aperçu des données :")
    #print(nlp_analysis.data.head().to_csv("apercu_data.csv"))

    nlp_analysis.preprocess_reviews()
    
    # Entraînement du modèle LSTM
    nlp_analysis.train_lstm_model()

    # Résumer les avis par restaurant
    summaries = nlp_analysis.summarize_reviews()
    #print("Aperçu des résumés :")
    #print(summaries.head())
    
    nlp_analysis.generate_wordcloud()
    
    # Génération du nuage  ;lde mots
    # wordcloud = nlp_analysis.generate_wordcloud()
    print("Nuage de mots généré avec succès.")
    # nlp_analysis.sauvegarder_donnees()
    nlp_analysis.sauvegarder_resume(summaries)
    nlp_analysis.sauvegarder_donnees()
    nlp_analysis.sauvegarder_sentiment_rating()


# Exécution du test
if __name__ == "__main__":
    test_nlp_analysis()
    