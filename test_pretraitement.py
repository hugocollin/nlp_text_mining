from NlpPretraitement import NLPPretraitement

def test_pretraitement():
    # Instanciation de la classe
    pretraitement = NLPPretraitement()

    # Extraction des données
    pretraitement.extraction_donnees()

    # Nettoyage des avis
    pretraitement.appliquer_nettoyage()

    # Nettoyage des dates
    pretraitement.nettoyage_dates()

    # Extraction de l'année, du mois et du jour
    pretraitement.extraire_annee_mois_jour()

    # Affichage et vérification du DataFrame final
    df_final = pretraitement.afficher_dataframe_complet()
    print("Colonnes du DataFrame :", df_final.columns)
    print("Aperçu des données :", df_final.head())

# Exécution du test
if __name__ == "__main__":
    test_pretraitement()
