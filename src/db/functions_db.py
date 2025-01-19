import ast
import locale
import os
import sqlite3
from contextlib import closing
from dateutil import parser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker , joinedload
from src.db.models import Base , Restaurant , Review , User
import pandas as pd
# Définition de la zone géographique pour les dates en français
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

# Définition du chemin vers le fichier de base de données SQLite
DATABASE_NAME = "restaurant_reviews.db" 

# Fonction d'initialisation de la base de données
def init_db(db_path="sqlite:///restaurant_reviews.db"):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    return engine

# Fonction de création d'une session SQLAlchemy
def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

# Fonction de création du schéma de la base de données
def create_schema():
    # Chemin vers le fichier de schéma SQL
    base_dir = os.path.dirname(__file__)
    schema_path = os.path.join(base_dir, "db_schema.sql")

    # Lecture du schéma SQL
    with open(schema_path, "r") as f:
        schema = f.read()

    # Exécution du schéma SQL
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.executescript(schema)
            conn.commit()

    print("Schéma de la base de données appliqué avec succès.")

# Fonction de vérification de l'existence de la base de données
def database_exists():
    return os.path.exists(DATABASE_NAME)

# Fonction de connexion à la base de données
def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn

# Fonction d'exécution d'une requête SQL
def execute_query(query, params=None):
    params = params or []
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, params)
            conn.commit()

# Fonction de récupération de toutes les lignes d'une requête SELECT
def fetch_all(query, params=None):
    params = params or []
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

# Fonction de récupération d'une seule ligne d'une requête SELECT
def fetch_one(query, params=None):
    params = params or []
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()        

# Fonction de récupération de la liste des colonnes d'une table
def get_table_columns(table_name):
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            return [col[1] for col in columns_info]
        
# Fonction de récupération d'une seule ligne sous forme de dictionnaire
def fetch_one_as_dict(query, params=None, table_name=None):
    params = params or []
    result = fetch_one(query, params)
    if result and table_name:
        columns = get_table_columns(table_name)
        return dict(zip(columns, result))
    return None


def get_all_reviews_from_list_restaurants(session, list_restaurants):
    reviews = session.query(Review).filter(Review.id_restaurant.in_(list_restaurants)).all()
    data = []
    for review in reviews:
        data.append({
            'restaurant_id': review.id_restaurant,
            'user_id': review.id_user,
            'review_id': review.id_review,
            'title': review.title_review,
            'user_profile': review.user.user_profile,
            'date_review': review.date_review,
            'rating': review.rating,
            'type_visit': review.type_visit,
            'num_contributions': review.user.num_contributions,
            'review': review.review_text,
            'review_cleaned': review.review_cleaned
        })
    return pd.DataFrame(data)




def review_from_1_rest_as_df(session, restaurant_id):
    reviews = session.query(Review).filter(Review.id_restaurant == restaurant_id).all()
    data = []
    for review in reviews:
        data.append({
            'restaurant_id': review.id_restaurant,
            'user_id': review.id_user,
            'review_id': review.id_review,
            'title': review.title_review,
            'user_profile': review.user.user_profile,
            'date_review': review.date_review,
            'rating': review.rating,
            'type_visit': review.type_visit,
            'num_contributions': review.user.num_contributions,
            'review': review.review_text,
            'review_cleaned': review.review_cleaned
        })
    return pd.DataFrame(data)





# Fonction de récupération de tous les restaurants
def get_all_restaurants(session):
    restaurants = session.query(Restaurant).all()
    return restaurants

# Fonction de récupération des avis et des utilisateurs pour un restaurant donné
def get_restaurants_with_reviews_and_users(session):

    # Sous-requête pour vérifier si un restaurant a des avis
    subquery = session.query(Review).filter(Review.id_restaurant == Restaurant.id_restaurant).exists()
    
    # Chargement des avis et des utilisateurs associés aux restaurants
    restaurants_with_reviews = session.query(Restaurant).\
        options(joinedload(Restaurant.avis).joinedload(Review.user)).\
        filter(subquery).\
        all()

    # Convertion des résultats en dictionnaires
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

# Fonction de récupération des avis et des utilisateurs pour un restaurant donné
def get_user_and_review_from_restaurant_id(session, restaurant_id):
    reviews = session.query(Review).\
        filter(Review.id_restaurant == restaurant_id).\
        options(joinedload(Review.user)).\
        all()
    
    user_reviews = [(review.user, review) for review in reviews]
    return user_reviews

# Fonction de mise en forme d'une date en français
def parse_french_date(date_str):
    # Dictionnaire de mapping des mois en français vers l'anglais
    months = {
        "janvier": "January", "février": "February", "mars": "March",
        "avril": "April", "mai": "May", "juin": "June",
        "juillet": "July", "août": "August", "septembre": "September",
        "octobre": "October", "novembre": "November", "décembre": "December"
    }

    # Remplacement des mois en français par les mois en anglais 
    for fr, en in months.items():
        date_str = date_str.replace(fr, en)

    # Conversion de la date
    try:
        parsed_date = parser.parse(date_str).date()
        return parsed_date
    except ValueError as e:
        print(f"Erreur de parsing pour la date '{date_str}': {e}")
        return None

# Fonction de conversion d'une chaîne de type dictionnaire en dictionnaire Python
def parse_to_dict(data_str):
    try:
        data_dict = ast.literal_eval(data_str)
        return data_dict
    except (ValueError, SyntaxError) as e:
        print(f"Erreur lors de la conversion : {e}")
        return None

# Fonction de conversion d'une valeur en float
def safe_float(value):
    if isinstance(value, float):
        return value
    try:
        return float(value.replace(',', '.')) if value not in [None, 'N/A', ''] else None
    except (ValueError, AttributeError):
        return None
    
# Fonction de récupération des restaurants avec avis
def get_restaurants_with_reviews():
    # Requête pour récupérer les restaurants avec avis
    query = """
        SELECT r.id_restaurant, r.nom
        FROM dim_restaurants r
        INNER JOIN fact_reviews rv ON r.id_restaurant = rv.id_restaurant
        GROUP BY r.id_restaurant, r.nom;
    """
    results = fetch_all(query)
    return [{"id": row[0], "nom": row[1]} for row in results]

# Fonction de récupération d'un restaurant
def get_restaurant(session, restaurant_id=None, restaurant_name=None):
    if not restaurant_id and not restaurant_name:
        print("Erreur : Vous devez spécifier soit un id_restaurant, soit un nom.")
        return None

    try:
        # Création de la requête
        query = session.query(Restaurant)
        if restaurant_id:
            query = query.filter_by(id_restaurant=restaurant_id)
        elif restaurant_name:
            query = query.filter_by(nom=restaurant_name)
        
        # Récupération du restaurant
        restaurant = query.first()

        if not restaurant:
            print(f"Aucun restaurant trouvé avec {'id=' + str(restaurant_id) if restaurant_id else 'nom=' + restaurant_name}.")
            return None

        # Conversion en dictionnaire
        restaurant_dict = {
            column.name: getattr(restaurant, column.name)
            for column in Restaurant.__table__.columns
        }
        return restaurant_dict
    except Exception as e:
        print(f"Erreur lors de la récupération du restaurant : {e}")
        return None

# Fonction de mise à jour d'un restaurant
def update_restaurant(id, **kwargs):
    # Vérification de l'existence du restaurant
    existing_restaurant = fetch_one_as_dict("SELECT * FROM dim_restaurants WHERE id_restaurant = ?", [id], table_name="dim_restaurants")

    if not existing_restaurant:
        raise ValueError(f"Restaurant {id} non trouvé dans la base de données.")

    # Construction de la requête de mise à jour
    update_query = "UPDATE dim_restaurants SET "
    update_fields = []
    params = []

    # Ajouter les champs à mettre à jour
    for column, value in kwargs.items():
        update_fields.append(f"{column} = ?")
        params.append(value)

    if not update_fields:
        raise ValueError("Aucune colonne spécifiée pour la mise à jour.")

    # Ajout des champs à la requête
    update_query += ", ".join(update_fields)
    update_query += " WHERE id_restaurant = ?"
    params.append(id)

    # Exécution de la requête
    execute_query(update_query, params=params)
    print(f"Restaurant '{id}' mis à jour avec succès avec les champs : {kwargs}.")

# Fonction de mise à jour des données d'un restaurant
def update_restaurant_data(restaurant_id, restaurant_data):
    try:
        if not isinstance(restaurant_data, dict):
            raise ValueError("Les données du restaurant doivent être un dictionnaire.")

        # Extraction des données
        details = restaurant_data.get('Détails', {})
        notes_et_avis = restaurant_data.get('Notes et avis', {})
        cuisines = details.get('CUISINES', None)
        note_globale = safe_float(notes_et_avis.get('NOTE GLOBALE', '0'))
        cuisine_note = safe_float(notes_et_avis.get('CUISINE', '0'))
        service_note = safe_float(notes_et_avis.get('SERVICE', '0'))
        qualite_prix_note = safe_float(notes_et_avis.get('RAPPORT QUALITÉ-PRIX', '0'))
        ambiance_note = safe_float(notes_et_avis.get('AMBIANCE', '0'))

        # Traitement de la fourchette de prix
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
        
        # Traitement des étoiles Michelin
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


def add_resume_avis_to_restaurant(session, restaurant_id, resume_avis):
    try:
        # Recherche du restaurant dans la base de données
        restaurant = session.query(Restaurant).filter_by(id_restaurant=restaurant_id).first()

        if not restaurant:
            print(f"Restaurant {restaurant_id} non trouvé dans la base de données. Ignoré.")
            return

        # Mise à jour de la colonne `resume_avis`
        restaurant.resume_avis = resume_avis
        session.commit()

        print(f"Colonne resume_avis mise à jour pour {restaurant_id} : {resume_avis}")
    
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la mise à jour pour {restaurant_id} : {e}")

# Fonction d'actualisation des données d'un restaurant dans la base de données
def process_restaurant_data(avis_df, location_df, details_df, restaurant_id):
    try:
        # Convertion des données en dictionnaires
        avis_data = avis_df.to_dict(orient='records')[0]
        location_data = location_df.to_dict(orient='records')[0]
        details_data = details_df.to_dict(orient='records')[0]

        # Préparation des données pour la mise à jour
        restaurant_data = {
            'Détails': details_data,
            'Emplacement et coordonnées': location_data,
            'Notes et avis': avis_data,
        }

        print("#######################################")
        print(restaurant_data)

        # Mise à jour des données du restaurant
        update_restaurant_data(restaurant_id, restaurant_data)

        print(f"Mise à jour réussie pour le restaurant avec ID {restaurant_id}.")
    
    except Exception as e:
        print(f"Erreur lors du traitement des données du restaurant avec ID {restaurant_id} : {e}")

# Fonction de remplissage de la colonne `resume_avis` dans la base de données
def fill_resume_avis_column(df, session):
    for _, row in df.iterrows():
        restaurant_name = row['restaurant'],
        resume_avis = row['resume_avis']
        
        try:
            # Recherche du restaurant dans la base de données
            restaurant = session.query(Restaurant).filter_by(nom=restaurant_name).first()

            if not restaurant:
                print(f"Restaurant {restaurant_name} non trouvé dans la base de données. Ignoré.")
                continue

            # Mise à jour de la colonne `resume_avis`
            restaurant.resume_avis = resume_avis
            session.commit()

            print(f"Colonne resume_avis mise à jour pour {restaurant_name} : {resume_avis}")
        
        except Exception as e:
            session.rollback()
            print(f"Erreur lors de la mise à jour pour {restaurant_name} : {e}")
            
            
            
            
def get_every_reviews(session):
    reviews = session.query(Review).all()
    data = []
    for review in reviews:
        data.append({
            'restaurant_id': review.id_restaurant,
            'user_id': review.id_user,
            'review_id': review.id_review,
            'title': review.title_review,
            'user_profile': review.user.user_profile,
            'date_review': review.date_review,
            'rating': review.rating,
            'type_visit': review.type_visit,
            'num_contributions': review.user.num_contributions,
            'review': review.review_text,
            'review_cleaned': review.review_cleaned
        })
    return pd.DataFrame(data)