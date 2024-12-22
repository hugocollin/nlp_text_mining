import sqlite3
from contextlib import closing

DATABASE_NAME = "mydatabase.db"  # Remplacez par le nom de votre base de données

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
