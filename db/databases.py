import sqlite3
from contextlib import closing

DATABASE_NAME = "restaurant_reviews.db" 


def create_schema():
    """Applique le schéma de la base de données depuis le fichier db_schema.py"""
    with open("db_schema.sql", "r") as f:
        schema = f.read()

    # Exécuter le schéma dans la base de données
    execute_query(schema)
    print("Schéma de la base de données appliqué avec succès.")


def get_connection():
    """Retourne une connexion à la base de données SQLite"""
    conn = sqlite3.connect(DATABASE_NAME)
    return conn

def execute_query(query, params=None):
    """Exécute une requête SQL (INSERT, UPDATE, DELETE, SELECT)"""
    params = params or []
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, params)
            conn.commit()

def fetch_all(query, params=None):
    """Récupère toutes les lignes d'une requête SELECT"""
    params = params or []
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

def fetch_one(query, params=None):
    """Récupère une seule ligne d'une requête SELECT"""
    params = params or []
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()


if __name__ == "__main__":
    create_schema()