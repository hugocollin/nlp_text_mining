from models import init_db, get_session, Geographie, Restaurant, Review

# Initialiser la base de données
engine = init_db()
print("Base de données créée avec succès.")
session = get_session(engine)

## Prochaine étape : remplir la base de données avec les données des fichier CSV