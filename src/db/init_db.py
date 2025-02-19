from src.db.functions_db import database_exists, create_schema, init_db, get_session

if __name__ == "__main__":
    DATABASE_NAME = "restaurant_reviews.db"

    # Vérification de l'existence de la base de données
    if not database_exists:
        print(f"La base de données {DATABASE_NAME} n'existe pas. Création en cours...")
        create_schema()
        print("Base de données créée avec succès.")

    # Initialisation de la base de données
    engine = init_db()
    session = get_session(engine)