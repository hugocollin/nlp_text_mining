import sqlite3
from contextlib import closing
import os


DATABASE_NAME = "restaurant_reviews.db" 


def create_schema():
    """Applique le schéma de la base de données depuis le fichier db_schema.sql"""
    # Construire le chemin vers le fichier db_schema.sql
    base_dir = os.path.dirname(__file__)  # Répertoire actuel du fichier databases.py
    schema_path = os.path.join(base_dir, "db_schema.sql")

    # Lire le contenu du fichier de schéma
    with open(schema_path, "r") as f:
        schema = f.read()

    # Exécuter le schéma dans la base de données
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.executescript(schema)  # Utiliser executescript pour exécuter plusieurs requêtes SQL
            conn.commit()

    print("Schéma de la base de données appliqué avec succès.")

def database_exists():
    """Vérifie si le fichier de la base de données SQLite existe."""
    return os.path.exists(DATABASE_NAME)

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


def get_table_columns(table_name):
    """Récupère les noms des colonnes d'une table dans la base de données"""    
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            # Utilisation de PRAGMA table_info pour obtenir les colonnes
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            # La deuxième colonne contient les noms des colonnes
            return [col[1] for col in columns_info]
        

def fetch_one_as_dict(query, params=None, table_name=None):
    """
    Récupère une seule ligne d'une requête SELECT et la retourne sous forme de dictionnaire.
    """
    params = params or []
    result = fetch_one(query, params)
    if result and table_name:
        columns = get_table_columns(table_name)
        return dict(zip(columns, result))
    return None
