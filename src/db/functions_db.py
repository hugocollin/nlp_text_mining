import ast
import locale
import os
import sqlite3
from contextlib import closing
from dateutil import parser
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker , joinedload
from src.db.models import Base , Restaurant , Review 

# Définition de la zone géographique pour les dates en français
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

# Définition du chemin vers le fichier de base de données SQLite
DATABASE_NAME = "restaurant_reviews.db" 

def init_db(db_path="sqlite:///restaurant_reviews.db"):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

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



def get_all_restaurants(session):
    """Récupère tous les restaurants depuis la base de données."""
    restaurants = session.query(Restaurant).all()
    return restaurants


def get_restaurants_with_reviews_and_users(session):
    # Utiliser EXISTS pour s'assurer qu'il y a au moins un avis pour chaque restaurant
    subquery = session.query(Review).filter(Review.id_restaurant == Restaurant.id_restaurant).exists()
    
    # Charger les restaurants qui ont des avis
    restaurants_with_reviews = session.query(Restaurant).\
        options(joinedload(Restaurant.avis).joinedload(Review.user)).\
        filter(subquery).\
        all()

    # Convertir les résultats en dictionnaires
    result = []
    for restaurant in restaurants_with_reviews:
        restaurant_data = {
            'restaurant': restaurant.nom,
            'restaurant_address': restaurant.adresse,
            'reviews': []
        }
        for review in restaurant.avis:
            review_data = {
                'restaurant_id': restaurant.id_restaurant,
                'user_id': review.user.id_user,
                'review_id': review.id_review,
                'title': review.title_review,
                'user_profile': review.user.user_profile,
                'date_review': review.date_review,
                'rating': review.rating,
                'type_visit': review.type_visit,
                'num_contributions': review.user.num_contributions,
                'review': review.review_text,
                'review_cleaned': review.review_cleaned
            }
            restaurant_data['reviews'].append(review_data)
        result.append(restaurant_data)

    return result

def get_user_and_review_from_restaurant_id(session, restaurant_id):
    """Récupère les utilisateurs et leurs avis pour un restaurant donné à partir de son ID."""
    reviews = session.query(Review).\
        filter(Review.id_restaurant == restaurant_id).\
        options(joinedload(Review.user)).\
        all()
    
    user_reviews = [(review.user, review) for review in reviews]
    return user_reviews

def parse_french_date(date_str):
    # Dictionnaire pour mapper les mois français aux mois anglais
    months = {
        "janvier": "January", "février": "February", "mars": "March",
        "avril": "April", "mai": "May", "juin": "June",
        "juillet": "July", "août": "August", "septembre": "September",
        "octobre": "October", "novembre": "November", "décembre": "December"
    }

    for fr, en in months.items():
        
        date_str = date_str.replace(fr, en)
        # print(date_str)

    try:
        parsed_date = parser.parse(date_str).date()
        return parsed_date
    except ValueError as e:
        print(f"Erreur de parsing pour la date '{date_str}': {e}")
        return None



def parse_to_dict(data_str):
    try:
        # Convertit la chaîne de type dictionnaire en dictionnaire Python
        data_dict = ast.literal_eval(data_str)
        return data_dict
    except (ValueError, SyntaxError) as e:
        print(f"Erreur lors de la conversion : {e}")
        return None
    
def safe_float(value):
    """Convertit une valeur en float si possible, sinon retourne None.
    Si la valeur est déjà un float, la retourne telle quelle.
    """
    if isinstance(value, float):
        return value
    try:
        # Si la valeur est une chaîne, on la convertit en float
        return float(value.replace(',', '.')) if value not in [None, 'N/A', ''] else None
    except (ValueError, AttributeError):
        return None
    
    
def get_restaurants_with_reviews():
    """
    Récupère la liste des restaurants ayant des avis dans la table review,
    avec uniquement leurs id et nom.
    
    Returns:
        list[dict]: Une liste de dictionnaires contenant les id et noms des restaurants.
    """
    query = """
        SELECT r.id_restaurant, r.nom
        FROM dim_restaurants r
        INNER JOIN fact_reviews rv ON r.id_restaurant = rv.id_restaurant
        GROUP BY r.id_restaurant, r.nom;
    """
    results = fetch_all(query)
    return [{"id": row[0], "nom": row[1]} for row in results]



def get_restaurant(session, restaurant_id=None, restaurant_name=None):
    """
    Récupère un restaurant depuis la table dim_restaurants à partir de son id_restaurant ou de son nom.
    
    Args:
        session (Session): La session SQLAlchemy utilisée pour exécuter la requête.
        restaurant_id (int, optional): L'identifiant unique du restaurant. Prioritaire.
        restaurant_name (str, optional): Le nom du restaurant. Utilisé si restaurant_id est None.
    
    Returns:
        dict: Un dictionnaire contenant les colonnes et leurs valeurs du restaurant, ou None si non trouvé.
    """
    if not restaurant_id and not restaurant_name:
        print("Erreur : Vous devez spécifier soit un id_restaurant, soit un nom.")
        return None

    try:
        from models import Restaurant  # Assurez-vous que le modèle est importé correctement

        # Construire la requête basée sur les paramètres
        query = session.query(Restaurant)
        if restaurant_id:
            query = query.filter_by(id_restaurant=restaurant_id)
        elif restaurant_name:
            query = query.filter_by(nom=restaurant_name)
        
        # Récupérer le premier résultat correspondant
        restaurant = query.first()

        if not restaurant:
            print(f"Aucun restaurant trouvé avec {'id=' + str(restaurant_id) if restaurant_id else 'nom=' + restaurant_name}.")
            return None

        # Convertir l'objet en dictionnaire
        restaurant_dict = {
            column.name: getattr(restaurant, column.name)
            for column in Restaurant.__table__.columns
        }
        return restaurant_dict
    except Exception as e:
        print(f"Erreur lors de la récupération du restaurant : {e}")
        return None



def update_restaurant(
    id,
    **kwargs
):
    """
    Met à jour les champs spécifiés pour un restaurant dans la table dim_restaurants.

    Args:
        name (str): Nom du restaurant à mettre à jour.
        kwargs: Paires clé-valeur des colonnes à mettre à jour.
                Par exemple: adresse="Nouvelle Adresse", note_globale=4.5, etc.
    """
    # Vérifier si le restaurant existe dans la base
    existing_restaurant = fetch_one_as_dict("SELECT * FROM dim_restaurants WHERE id_restaurant = ?", [id], table_name="dim_restaurants")

    if not existing_restaurant:
        raise ValueError(f"Restaurant {id} non trouvé dans la base de données.")

    # Construire la requête de mise à jour dynamiquement
    update_query = "UPDATE dim_restaurants SET "
    update_fields = []
    params = []

    # Ajouter uniquement les colonnes fournies en kwargs
    for column, value in kwargs.items():
        update_fields.append(f"{column} = ?")
        params.append(value)

    # Si aucun champ n'est fourni, ne pas exécuter la requête
    if not update_fields:
        raise ValueError("Aucune colonne spécifiée pour la mise à jour.")

    # Ajouter les champs à la requête
    update_query += ", ".join(update_fields)
    update_query += " WHERE id_restaurant = ?"
    params.append(id)

    # Exécuter la requête
    execute_query(update_query, params=params)
    print(f"Restaurant '{id}' mis à jour avec succès avec les champs : {kwargs}.")



def update_restaurant_data(restaurant_id, restaurant_data):
    try:
        # Vérifiez que restaurant_data est un dictionnaire
        if not isinstance(restaurant_data, dict):
            raise ValueError("Les données du restaurant doivent être un dictionnaire.")

        # Vérifiez que les sections 'Détails' et 'Notes et avis' existent
        details = restaurant_data.get('Détails', {})
        notes_et_avis = restaurant_data.get('Notes et avis', {})

        # Vérifications supplémentaires pour éviter les erreurs d'accès
        cuisines = details.get('CUISINES', None)
        note_globale = safe_float(notes_et_avis.get('NOTE GLOBALE', '0'))
        cuisine_note = safe_float(notes_et_avis.get('CUISINE', '0'))
        service_note = safe_float(notes_et_avis.get('SERVICE', '0'))
        qualite_prix_note = safe_float(notes_et_avis.get('RAPPORT QUALITÉ-PRIX', '0'))
        ambiance_note = safe_float(notes_et_avis.get('AMBIANCE', '0'))

        # Traitement de la fourchette de prix avec vérification du type
        fourchette_prix = details.get('FOURCHETTE DE PRIX', '')
        if isinstance(fourchette_prix, str):
            fourchette_prix = fourchette_prix.replace('\xa0€', '')
            if '-' in fourchette_prix:
                prix_min, prix_max = map(
                    safe_float,
                    fourchette_prix.split('-')
                )
            else:
                prix_min, prix_max = None, None
        else:
            prix_min, prix_max = None, None
        
        # Étoiles Michelin
        etoiles_michelin = details.get('ÉTOILES MICHELIN', None)
        if isinstance(etoiles_michelin, str) and etoiles_michelin.isdigit():
            etoiles_michelin = int(etoiles_michelin)
        elif not isinstance(etoiles_michelin, int):
            etoiles_michelin = None

        rank = restaurant_data.get('Détails', {}).get('RANK', None)
        if rank is not None:
            rank = int(rank)

        # Mise à jour des données
        update_restaurant(
            
            id=restaurant_id,
            cuisines=cuisines,
            note_globale=note_globale,
            cuisine_note=cuisine_note,
            service_note=service_note,
            qualite_prix_note=qualite_prix_note,
            ambiance_note=ambiance_note,
            prix_min=prix_min,
            prix_max=prix_max,
            etoiles_michelin=etoiles_michelin,
            repas=details.get('REPAS', None),
            latitude=restaurant_data.get('Emplacement et coordonnées', {}).get('LATITUDE', None),
            longitude=restaurant_data.get('Emplacement et coordonnées', {}).get('LONGITUDE', None),
            google_map=restaurant_data.get('Emplacement et coordonnées', {}).get('GOOGLE MAP', None),
            rank = rank,
            horaires = restaurant_data.get('Détails', {}).get('HORAIRES', ''),
            fonctionnalite = restaurant_data.get('Détails', {}).get('FONCTIONNALITE', ''),
            image = restaurant_data.get('Détails', {}).get('IMAGE', None),
        )

        print(f"Mise à jour réussie pour {restaurant_id}.")

    except Exception as e:
        print(f"Erreur lors de la mise à jour du restaurant {restaurant_id} : {e}")



def process_restaurant_data(avis_df, location_df, details_df, restaurant_id):
    """
    Met à jour les données d'un restaurant dans la base de données à partir des DataFrames avis, location et details.

    Args:
        avis_df (pd.DataFrame): DataFrame contenant les avis du restaurant.
        location_df (pd.DataFrame): DataFrame contenant l'emplacement et les coordonnées du restaurant.
        details_df (pd.DataFrame): DataFrame contenant les détails du restaurant.
        restaurant_id (int): ID du restaurant à mettre à jour.
        session (SQLAlchemy session): Session pour interagir avec la base de données.

    Returns:
        None
    """
    try:
        # Convertir les données des DataFrames en dictionnaires
        avis_data = avis_df.to_dict(orient='records')[0]  # On suppose qu'il y a une seule ligne
        location_data = location_df.to_dict(orient='records')[0]
        details_data = details_df.to_dict(orient='records')[0]

        # Préparer les données consolidées pour la mise à jour
        restaurant_data = {
            'Détails': details_data,
            'Emplacement et coordonnées': location_data,
            'Notes et avis': avis_data,
        }

        print("#######################################")
        print(restaurant_data)

        # Mettre à jour les données du restaurant en appelant une fonction dédiée
        update_restaurant_data(restaurant_id, restaurant_data)

        print(f"Mise à jour réussie pour le restaurant avec ID {restaurant_id}.")
    
    except Exception as e:
        print(f"Erreur lors du traitement des données du restaurant avec ID {restaurant_id} : {e}")



def fill_review_cleaned_column(df, session):
    """
    Remplit la colonne `review_cleaned` dans la base de données à partir d'un DataFrame.

    Args:
        df (pd.DataFrame): DataFrame contenant `nom` (restaurant), `user_profile`, `review_cleaned`, `title`, `sentiment`, et `sentiment_rating`.
        session: La session SQLAlchemy pour interagir avec la base de données.
    """
    for _, row in df.iterrows():
        restaurant_name = row['restaurant']
        user_profile = row['user_profile']
        title = row['title']

        # Mettre à jour la base de données
        try:
            # Rechercher l'enregistrement correspondant dans la base
            review_entry = session.query(Review).\
                join(Restaurant, Review.id_restaurant == Restaurant.id_restaurant).\
                join(User, Review.id_user == User.id_user).\
                filter(
                    Restaurant.id_restaurant == row['restaurant_id'],
                    User.id_user == row['user_id'],
                    Review.id_review == row['review_id']
                ).first()

            if review_entry:
                # Mettre à jour les colonnes `review_cleaned`, `sentiment`, et `sentiment_rating`
                review_entry.review_cleaned = row['review_cleaned']
                # review_entry.sentiment = int(row['sentiment'])
                # review_entry.sentiment_rating = row['sentiment_rating']

                session.commit()
                print(f"Colonne review_cleaned mise à jour pour {restaurant_name}, {user_profile}.")
            else:
                print(f"Aucun avis trouvé pour {restaurant_name}, {user_profile}.")
        except Exception as e:
            session.rollback()  # Annuler la transaction en cas d'erreur
            print(f"Erreur lors de la mise à jour pour {restaurant_name}, {user_profile} : {e}")



def fill_sentiment_column(df, session):
    """
    Remplit la colonne `review_cleaned` dans la base de données à partir d'un DataFrame.

    Args:
        df (pd.DataFrame): DataFrame contenant `nom` (restaurant), `user_profile`, `review_cleaned`, `title`, `sentiment`, et `sentiment_rating`.
        session: La session SQLAlchemy pour interagir avec la base de données.
    """
    for _, row in df.iterrows():
        restaurant_name = row['restaurant']
        user_profile = row['user_profile']
        title = row['title']

        # Mettre à jour la base de données
        try:
            # Rechercher l'enregistrement correspondant dans la base
            review_entry = session.query(Review).\
                join(Restaurant, Review.id_restaurant == Restaurant.id_restaurant).\
                join(User, Review.id_user == User.id_user).\
                filter(
                    Restaurant.id_restaurant == row['restaurant_id'],
                    User.id_user == row['user_id'],
                    Review.id_review == row['review_id']
                ).first()

            if review_entry:
                # Mettre à jour les colonnes `review_cleaned`, `sentiment`, et `sentiment_rating`
                # review_entry.review_cleaned = row['review_cleaned']
                review_entry.sentiment = int(row['sentiment'])
                # review_entry.sentiment_rating = row['sentiment_rating']

                session.commit()
                print(f"Colonne sentiment mise à jour pour {restaurant_name}, {user_profile}.")
            else:
                print(f"Aucun avis trouvé pour {restaurant_name}, {user_profile}.")
        except Exception as e:
            session.rollback()  # Annuler la transaction en cas d'erreur
            print(f"Erreur lors de la mise à jour pour {restaurant_name}, {user_profile} : {e}")

def fill_resume_avis_column(df, session):
    """
    Remplit la colonne `resume_avis` dans la table des restaurants à partir d'un DataFrame.

    Args:
        df (pd.DataFrame): DataFrame contenant `nom` (nom du restaurant).
        session: La session SQLAlchemy pour interagir avec la base de données.
    """
    for _, row in df.iterrows():
        restaurant_name = row['restaurant'],
        resume_avis = row['resume_avis']
        
        try:
            # Rechercher le restaurant correspondant dans la base
            restaurant = session.query(Restaurant).filter_by(nom=restaurant_name).first()

            if not restaurant:
                print(f"Restaurant {restaurant_name} non trouvé dans la base de données. Ignoré.")
                continue

            # Mettre à jour la colonne `resume_avis`
            restaurant.resume_avis = resume_avis
            session.commit()

            print(f"Colonne resume_avis mise à jour pour {restaurant_name} : {resume_avis}")
        
        except Exception as e:
            print(f"Erreur lors de la mise à jour pour {restaurant_name} : {e}")