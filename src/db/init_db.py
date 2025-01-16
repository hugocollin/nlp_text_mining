
import sys
import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db.models import init_db, get_session, Restaurant, Review, User, get_all_restaurants, get_restaurants_with_reviews_and_users
import pandas as pd
import ast
from sqlalchemy import update, select, exists, create_engine, text, MetaData, Column, String, Integer, Float, Boolean
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
import re


from src.db.databases import execute_query, fetch_one, create_schema, database_exists, fetch_one_as_dict, fetch_all
from geopy.geocoders import Nominatim
import locale
from datetime import datetime
from dateutil import parser


# Définir la locale pour le français
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')


def insert_user(user_name, user_profile, num_contributions):
    """Insère un utilisateur dans la table dim_users et retourne son id."""
    query = """
        INSERT OR IGNORE INTO dim_users (user_name, user_profile, num_contributions)
        VALUES (?, ?, ?)
    """
    execute_query(query, params=[user_name, user_profile, num_contributions])

    # Récupérer l'id de l'utilisateur inséré
    result = fetch_one("SELECT id_user FROM dim_users WHERE user_name = ?", [user_name])
    return result[0]



def insert_restaurant(
    name,
    adresse=None,
    url=None,
    email=None,
    telephone=None,
    cuisines=None,
    note_globale=None,
    cuisine_note=None,
    service_note=None,
    qualite_prix_note=None,
    ambiance_note=None,
    prix_min=None,
    prix_max=None,
    etoiles_michelin=None,
    repas=None,
    latitude=None,
    longitude=None,
    scrapped=True,
    image=None
):
    """Insère un restaurant dans la table dim_restaurants et retourne son id."""
    # Vérifier si le restaurant existe déjà dans la base
    existing_restaurant = fetch_one(
        "SELECT id_restaurant FROM dim_restaurants WHERE nom = ?", [name]
    )

    if existing_restaurant:
        # Si le restaurant existe déjà, retourner son id
        return existing_restaurant[0]
    else:
        # Si le restaurant n'existe pas, l'insérer dans la base
        query = """
            INSERT INTO dim_restaurants (
                nom, adresse, url_link, email, telephone, cuisines, 
                note_globale, cuisine_note, service_note, qualite_prix_note, ambiance_note,
                prix_min, prix_max, etoiles_michelin, repas, latitude, longitude, scrapped, image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Extraire prix_min et prix_max depuis `prix_min` et `prix_max` si fournis en chaîne
        if isinstance(prix_min, str):
            prix_min = float(prix_min.replace(',', '.').replace('€', '').strip())
        if isinstance(prix_max, str):
            prix_max = float(prix_max.replace(',', '.').replace('€', '').strip())

        # Remplir les paramètres et exécuter l'insertion
        params = [
            name, adresse, url, email, telephone, cuisines,
            note_globale, cuisine_note, service_note, qualite_prix_note, ambiance_note,
            prix_min, prix_max, etoiles_michelin, repas, latitude, longitude, scrapped, image
        ]
        execute_query(query, params=params)

        # Récupérer l'id du restaurant nouvellement inséré
        new_restaurant = fetch_one(
            "SELECT id_restaurant FROM dim_restaurants WHERE nom = ?", [name]
        )
        return new_restaurant[0]


def insert_review(review, id_restaurant):
    """
    Insère un avis dans la table fact_reviews.
    Vérifie si l'utilisateur existe déjà dans la base. S'il n'existe pas, il est ajouté.
    """
    # Vérifier si l'utilisateur existe déjà
    query_user = "SELECT id_user FROM dim_users WHERE user_profile = ?"
    existing_user = fetch_one(query_user, [review['user_profile']])

    # Si l'utilisateur n'existe pas, l'insérer
    if not existing_user:
        insert_user_query = """
        INSERT INTO dim_users (user_name, user_profile, num_contributions)
        VALUES (?, ?, ?)
        """
        execute_query(insert_user_query, [
            review['user'], 
            review['user_profile'], 
            review.get('num_contributions', 0)
        ])
        # Récupérer l'ID de l'utilisateur inséré
        id_user = fetch_one(query_user, [review['user_profile']])[0]
    else:
        id_user = existing_user[0]

    review_date = parse_french_date(review.get('date', ''))
    if not review_date:
        print(f"Date invalide pour l'avis : {review.get('date', '')}")
        return

    # Insérer l'avis dans fact_reviews
    insert_review_query = """
    INSERT INTO fact_reviews (
        id_restaurant, 
        id_user, 
        date_review, 
        title_review, 
        review_text, 
        rating, 
        type_visit
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    execute_query(insert_review_query, [
        id_restaurant,
        id_user,
        review_date,
        review['title'],
        review['review'],
        review['rating'],
        review['type_visit']
    ])



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


def process_restaurant_csv(file_name):
    """Insère les restaurants depuis un fichier CSV situé dans le dossier parent 'data'."""

    # Construire le chemin absolu vers le fichier CSV
    # base_dir = os.path.dirname("Data")  # Répertoire actuel du script
    data_dir = os.path.join("Data", "..", "data")  # Chemin vers le dossier 'data'
    file_path = os.path.join(data_dir, file_name)  # Chemin complet vers le fichier CSV

    # Vérifier si le fichier existe
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier spécifié n'existe pas : {file_path}")

    # Lire le fichier CSV en DataFrame
    df = pd.read_csv(file_path, sep=';')

    # Parcourir chaque ligne du DataFrame pour insérer les restaurants
    for _, row in df.iterrows():
        # Assurez-vous que chaque colonne du DataFrame correspond aux champs nécessaires
        restaurant_data = parse_to_dict(row['info'])
        # print(restaurant_data['Emplacement et coordonnées'])
        latitude, longitude = get_coordinates(restaurant_data['Emplacement et coordonnées'].get('ADRESSE', None))

        # Insérer le restaurant dans la base de données
        restaurant_id = insert_restaurant(
        name=row['restaurant'],
        url=row['url'],
        adresse=restaurant_data['Emplacement et coordonnées'].get('ADRESSE', None),
        email=restaurant_data['Emplacement et coordonnées'].get('EMAIL', None),
        telephone=restaurant_data['Emplacement et coordonnées'].get('TELEPHONE', None),
        cuisines=restaurant_data['Détails'].get('CUISINES', None),
        note_globale=safe_float(restaurant_data['Notes et avis'].get('NOTE GLOBALE', '0')),
        cuisine_note=safe_float(restaurant_data['Notes et avis'].get('CUISINE', '0')),
        service_note=safe_float(restaurant_data['Notes et avis'].get('SERVICE', '0')),
        qualite_prix_note=safe_float(restaurant_data['Notes et avis'].get('RAPPORT QUALITÉ-PRIX', '0')),
        ambiance_note=safe_float(restaurant_data['Notes et avis'].get('AMBIANCE', '0')),
        prix_min=safe_float(restaurant_data['Détails'].get('FOURCHETTE DE PRIX', '').replace('\xa0€', '').split('-')[0]) if '-' in restaurant_data['Détails'].get('FOURCHETTE DE PRIX', '') else None,
        prix_max=safe_float(restaurant_data['Détails'].get('FOURCHETTE DE PRIX', '').replace('\xa0€', '').split('-')[1]) if '-' in restaurant_data['Détails'].get('FOURCHETTE DE PRIX', '') else None,
        etoiles_michelin = (
            int(restaurant_data['Détails'].get('ÉTOILES MICHELIN', 0))
            if isinstance(restaurant_data['Détails'].get('ÉTOILES MICHELIN'), str) and restaurant_data['Détails'].get('ÉTOILES MICHELIN', '').isdigit()
            else restaurant_data['Détails'].get('ÉTOILES MICHELIN', None) if isinstance(restaurant_data['Détails'].get('ÉTOILES MICHELIN'), int)
            else None
        ),
        repas=restaurant_data['Détails'].get('REPAS', None),
        latitude=latitude,
        longitude=longitude,
        image=restaurant_data['Détails'].get('IMAGE', None),
    )
        

def update_restaurant_coordinates(engine):
    """
    Met à jour les colonnes latitude et longitude dans la table dim_restaurants.
    """
    with Session(engine) as session:
        # Requête pour obtenir les restaurants sans latitude ou longitude
        restaurants_to_update = session.execute(
            select(Restaurant).where(
                (Restaurant.latitude.is_(None)) | (Restaurant.longitude.is_(None))
            )
        ).scalars()

        # Parcourir les restaurants sans coordonnées
        for restaurant in restaurants_to_update:
            if restaurant.adresse:  # Vérifier si l'adresse est disponible
                print(f"Recherche des coordonnées pour : {restaurant.nom}, {restaurant.adresse}")
                latitude, longitude = get_coordinates(restaurant.adresse)

                # Si les coordonnées sont trouvées, mettre à jour
                if latitude and longitude:
                    restaurant.latitude = latitude
                    restaurant.longitude = longitude
                    print(f"Coordonnées mises à jour : {latitude}, {longitude}")
                else:
                    print(f"Impossible d'obtenir les coordonnées pour : {restaurant.nom}")

        # Commit des modifications dans la base de données
        session.commit()
        print("Mise à jour des coordonnées terminée.")


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


#### Pour insérer des review pour un restaurant
def insert_restaurant_reviews(restaurant_id, reviews):
    # Insérer les avis pour le restaurant
    try:
        for review in reviews:
            review_data = {
                "user": review['user'],
                "user_profile": review['user_profile'],
                "num_contributions": review['num_contributions'],
                "date": review['date_review'],
                "title": review['title'],
                "review": review['review'],
                "rating": review['rating'],
                "type_visit": review['type_visit']
            }
            insert_review(review_data, restaurant_id)
            update_restaurant_columns(restaurant_id, {"scrapped": True}, session)
    except Exception as e:
        print(f"Erreur lors de l'insertion des avis pour le restaurant {restaurant_id} : {e}")


def get_restaurants_from_folder(scrapping_dir):
    
    # Ensemble pour garantir l'unicité des noms de restaurants
    restaurant_names = set()

    # Parcourir les fichiers dans le dossier
    for file_name in os.listdir(scrapping_dir):
        if not file_name.endswith(".csv"):
            continue  # Ignorer les fichiers qui ne sont pas des CSV
        
        # Extraire le nom du restaurant à partir du nom du fichier
        base_name, _ = os.path.splitext(file_name)
        parts = base_name.split("_")
        if len(parts) < 2:
            print(f"Fichier mal nommé ignoré : {file_name}")
            continue  # Ignorer les fichiers mal nommés

        restaurant_name = parts[0]  # Le premier élément est le nom du restaurant
        restaurant_names.add(restaurant_name)

    return sorted(restaurant_names)


def process_csv_files(scrapping_dir, session, with_reviews=True):
    # Recuperer les nom des restaurants dans le dossier scrapping
    restaurant_names = get_restaurants_from_folder(scrapping_dir)
    file_suffixes = ["details", "reviews", "avis", "location"] if with_reviews else ["details", "location", "avis"]

    for restaurant_name in restaurant_names:
        restaurant_data = {"Emplacement et coordonnées": {}, "Détails": {}, "Notes et avis": {}}
        reviews = None
        print(f"Traitement du restaurant : {restaurant_name}")
        restaurant = session.query(Restaurant).filter_by(nom=restaurant_name).first()
        
        if not restaurant:
            print(f"Restaurant {restaurant_name} non trouvé dans la base de données. Création...")
            restaurant = Restaurant(nom=restaurant_name)  # Crée un nouvel objet restaurant
            session.add(restaurant)  # Ajouter à la session
            session.commit()  # Sauvegarder dans la base de données pour obtenir un ID valide
            print(f"Restaurant {restaurant_name} ajouté à la base avec succès.")
        
        # Parcourir les fichiers dans le dossier pour ce restaurant
        for suffix in file_suffixes:
            file_name = f"{restaurant_name}_{suffix}.csv"
            file_path = os.path.join(scrapping_dir, file_name)

            if not os.path.exists(file_path):
                print(f"Fichier non trouvé : {file_name}")
                break  # Arrêter le traitement si un fichier est manquant

            # Charger le fichier CSV en DataFrame
            df = pd.read_csv(file_path)
            if suffix == "details":
                restaurant_data["Détails"] = df.to_dict(orient='records')[0]
            elif suffix == "reviews":
                reviews = df.to_dict(orient='records')
            elif suffix == "avis":
                restaurant_data["Notes et avis"] = df.to_dict(orient='records')[0]
                    
            elif suffix == "location":
                restaurant_data["Emplacement et coordonnées"] = df.to_dict(orient='records')[0]
        # print(restaurant_data)
        update_restaurant_data(restaurant_name, restaurant_data)
                
        if reviews is not None and with_reviews:
            print(f"Insertion des avis pour {restaurant_name}...")
            insert_restaurant_reviews(restaurant, reviews)
            # print(f"Avis insérés pour {reviews}.")
            update_restaurant_columns(restaurant_name, {"scrapped": True}, session)
        else:
            print(f"Warning #### : Aucun avis trouvé pour {restaurant_name}.")
            update_restaurant_columns(restaurant_name, {"scrapped": False}, session)
    

    session.commit()


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

def get_restaurants_with_reviews():
    """
    Récupère la liste des noms des restaurants ayant des avis dans la table review.
    
    Returns:
        list[str]: Une liste contenant les noms des restaurants.
    """
    query = """
        SELECT r.nom
        FROM dim_restaurants r
        INNER JOIN fact_reviews rv ON r.id_restaurant = rv.id_restaurant
        GROUP BY r.nom;
    """
    results = fetch_all(query)
    return [row[0] for row in results]


def get_scrapped_restaurants():
    """
    Récupère la liste des noms des restaurants dont scrapped = True.
    
    Returns:
        list[str]: Une liste contenant les noms des restaurants scrappés.
    """
    query = """
        SELECT nom
        FROM dim_restaurants
        WHERE scrapped = 1;
    """
    results = fetch_all(query)
    return [row[0] for row in results]


def update_scrapped_status_for_reviews(session, restaurant_names):
    """
    Met à jour la colonne scrapped pour les restaurants dans la liste des noms fournie
    en utilisant une session SQLAlchemy.

    Args:
        session (Session): La session SQLAlchemy pour interagir avec la base de données.
        restaurant_names (list[str]): Liste des noms des restaurants à mettre à jour.
    """
    if not restaurant_names:
        print("La liste des noms de restaurants est vide. Aucun traitement effectué.")
        return

    try:
        # Mise à jour en une seule requête (si la base de données supporte IN)
        session.query(Restaurant) \
            .filter(Restaurant.nom.in_(restaurant_names)) \
            .update({Restaurant.scrapped: True}, synchronize_session='fetch')

        session.commit()
        print(f"Colonne 'scrapped' mise à jour pour {len(restaurant_names)} restaurants.")
    except Exception as e:
        session.rollback()
        print("Une erreur s'est produite lors de la mise à jour.")
        print(f"Erreur : {e}")


def update_restaurant_columns(restaurant_id, updates, session):
    """
    Met à jour des colonnes spécifiques dans la table dim_restaurants pour un restaurant donné.
    
    Args:
        restaurant_id (int): L'id du restaurant à mettre à jour.
        updates (dict): Un dictionnaire contenant les colonnes à mettre à jour comme clés et leurs nouvelles valeurs.
        session (Session): La session SQLAlchemy à utiliser.
    
    Returns:
        bool: True si la mise à jour a réussi, False sinon.
    """
    if not updates:
        print("Aucune mise à jour spécifiée.")
        return False

    try:
        # Construire la requête d'update avec SQLAlchemy
        session.query(Restaurant).filter_by(id_restaurant=restaurant_id).update(updates)
        session.commit()
        print(f"Restaurant '{restaurant_id}' mis à jour avec succès.")
        return True
    except Exception as e:
        session.rollback()  # Annuler les changements en cas d'erreur
        print(f"Erreur lors de la mise à jour du restaurant '{restaurant_id}': {e}")
        return False
    

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



def add_columns_to_table(engine, table_name, columns):
    """
    Ajoute de nouvelles colonnes à une table existante dans une base de données SQLite.

    Args:
        engine: L'objet SQLAlchemy engine connecté à SQLite.
        table_name (str): Nom de la table à modifier.
        columns (dict): Un dictionnaire où la clé est le nom de la colonne et la valeur est le type SQLAlchemy.
            Exemple : {"new_column1": "TEXT", "new_column2": "INTEGER"}
    """
    with engine.connect() as connection:
        for column_name, column_type in columns.items():
            try:
                # Vérifier si la colonne existe déjà
                result = connection.execute(text(f"PRAGMA table_info({table_name});")).fetchall()
                existing_columns = [row[1] for row in result]
                if column_name in existing_columns:
                    print(f"La colonne '{column_name}' existe déjà dans la table '{table_name}'.")
                    continue

                # Ajouter la nouvelle colonne
                alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                connection.execute(text(alter_stmt))
                print(f"Colonne '{column_name}' ajoutée à la table '{table_name}'.")
            except Exception as e:
                print(f"Erreur lors de l'ajout de la colonne '{column_name}' : {e}")


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

def check_restaurants_in_db(resto_list, session):
    """
    Vérifie quels restaurants dans une liste sont présents ou absents dans la base de données.
    
    Args:
        resto_list (list): Liste de noms de restaurants à vérifier.
        session: Session SQLAlchemy connectée à la base de données.
        
    Returns:
        dict: Deux listes - 'present' et 'absent'.
    """
    # Requête pour récupérer tous les noms dans la base de données
    db_restaurants = session.query(Restaurant.nom).all()
    
    # Convertir le résultat en une liste de noms (tuple -> str)
    db_restaurant_names = {name[0] for name in db_restaurants}
    
    # Séparer les restaurants présents et absents
    present = [resto for resto in resto_list if resto in db_restaurant_names]
    absent = [resto for resto in resto_list if resto not in db_restaurant_names]
    
    return {'present': present, 'absent': absent}

def create_restaurants_from_csv(csv_path, session):
    #data_dir = os.path.join("Data", csv_path)  # Chemin vers le dossier 'data'
    file_path = os.path.join("Data", csv_path) 
    
    try:
        # Charger le fichier CSV dans un DataFrame
        df = pd.read_csv(file_path, sep=",")
        
        # Vérifier que le fichier contient les colonnes requises
        if 'name' not in df.columns or 'url' not in df.columns:
            raise ValueError("Le fichier CSV doit contenir les colonnes 'nom' et 'url'.")
        
        # Parcourir chaque ligne du DataFrame
        for _, row in df.iterrows():
            restaurant_name = row['name'].strip()
            restaurant_url = row['url'].strip()
            
            # Vérifier si le restaurant existe déjà dans la base
            existing_restaurant = session.query(Restaurant).filter_by(nom=restaurant_name).first()
            
            if existing_restaurant:
                print(f"Le restaurant '{restaurant_name}' existe déjà dans la base de données.")
            else:
                # Créer un nouveau restaurant
                new_restaurant = Restaurant(nom=restaurant_name, url_link=restaurant_url, scrapped=False)
                session.add(new_restaurant)
                print(f"Ajouté : {restaurant_name} avec l'URL {restaurant_url}")
        
        # Commit des changements dans la base de données
        session.commit()
        print("Tous les nouveaux restaurants ont été ajoutés avec succès.")
    
    except Exception as e:
        print(f"Erreur lors du traitement : {e}")



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



def get_restaurant_ids(folder_path):
    """
    Récupère tous les IDs de restaurants à partir des noms de fichiers dans un dossier.

    Args:
        folder_path (str): Chemin du dossier contenant les fichiers CSV.

    Returns:
        list: Une liste d'IDs uniques des restaurants.
    """
    # Liste de tous les fichiers CSV
    all_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    
    # Extraire les IDs des noms de fichiers
    restaurant_ids = set()
    for file_name in all_files:
        match = re.search(r'_(\d+)\.csv$', file_name)
        if match:
            restaurant_ids.add(int(match.group(1)))  # Ajouter l'ID extrait
    
    return sorted(restaurant_ids)


def load_files_for_restaurant(folder_path, restaurant_id):
    """
    Charge les fichiers associés à un restaurant en DataFrames.

    Args:
        folder_path (str): Chemin du dossier contenant les fichiers CSV.
        restaurant_id (int): ID du restaurant.

    Returns:
        dict: Un dictionnaire contenant les DataFrames des fichiers associés (avis, location, details).
    """
    data = {}
    file_types = ["avis", "location", "details"]
    
    for file_type in file_types:
        file_name = f"{file_type}_{restaurant_id}.csv"
        file_path = os.path.join(folder_path, file_name)
        
        if os.path.exists(file_path):
            # Charger le fichier CSV dans un DataFrame
            df = pd.read_csv(file_path)
            data[file_type] = df
            # print(f"Chargé : {data}")
        else:
            print(f"Fichier manquant : {file_name}")
    
    return data


def process_all_restaurants(folder_path):
    """
    Récupère tous les IDs des restaurants, charge leurs fichiers et les traite.

    Args:
        folder_path (str): Chemin du dossier contenant les fichiers CSV.
        process_restaurant_data (function): Fonction à appeler pour traiter les données d'un restaurant.
    """
    # Étape 1: Récupérer tous les IDs des restaurants
    restaurant_ids = get_restaurant_ids(folder_path)
    print(f"IDs des restaurants trouvés : {restaurant_ids}")

    # Étape 2: Parcourir chaque ID et charger les fichiers associés
    for restaurant_id in restaurant_ids:
        print(f"Traitement des fichiers pour le restaurant ID : {restaurant_id}")
        data = load_files_for_restaurant(folder_path, restaurant_id)
        
        if "avis" in data or "location" in data or "details" in data:
            # Étape 3: Envoyer les DataFrames à la fonction de traitement
            process_restaurant_data(data.get("avis"), data.get("location"), data.get("details"), restaurant_id)
        else:
            print(f"Aucun fichier valide trouvé pour le restaurant ID {restaurant_id}.")



if __name__ == "__main__":
    DATABASE_NAME = "restaurant_reviews.db"

    # Vérifier si la base de données existe, sinon la créer
    if not database_exists:
        print(f"La base de données {DATABASE_NAME} n'existe pas. Création en cours...")
        create_schema()
        print("Base de données créée avec succès.")


    # Initialiser la base de données
    engine = init_db()
    session = get_session(engine)
    
    # Insérer les restaurants
    restaurant_csv_file = "liste_restaurants.csv"

    # Mise à jour des coordonnées des restaurants
    # update_restaurant_coordinates(engine)

    # process_restaurant_csv(restaurant_csv_file)

    # restaurants_scrapped = session.query(Restaurant).all()
    
    # Parcourir et imprimer les restaurants

    
    """
    for restaurant in restaurants_scrapped:
        if restaurant.scrapped:
            print(f"Scrappé ID: {restaurant.id_restaurant}, Nom: {restaurant.nom}, Adresse: {restaurant.adresse}, latitude: {restaurant.latitude}, longitude: {restaurant.longitude}")

        else:
            print(f"Non scrappé ID: {restaurant.id_restaurant}, Nom: {restaurant.nom}, Adresse: {restaurant.adresse}")
    
restaurants = get_all_restaurants(session)
    for restaurant in restaurants:
        print(f"Restaurant ID: {restaurant.id_restaurant}, Name: {restaurant.nom}")


    with engine.connect() as connection:
        connection.execute(
            text("ALTER TABLE dim_restaurants ADD COLUMN google_map TEXT")
        )
    with engine.connect() as connection:
        connection.execute(
            text("ALTER TABLE dim_restaurants ADD COLUMN fonctionnalite TEXT")
        )
    with engine.connect() as connection:
        connection.execute(
            text("ALTER TABLE dim_restaurants ADD COLUMN horaires TEXT")
        )
    with engine.connect() as connection:
        connection.execute(
            text("ALTER TABLE dim_restaurants ADD COLUMN rank INTEGER")
        )"""
    
    
    """with Session(engine) as session:
        # Sous-requête pour vérifier si l'id_restaurant existe dans la table review
        subquery = select(Review.id_restaurant).distinct()

        # Requête de mise à jour
        session.execute(
            update(Restaurant)
            .where(Restaurant.id_restaurant.in_(subquery))
            .values(scrapped=True)
        )
        session.commit()

        print("Mise à jour effectuée avec succès.")
        
        
"""
    # recuperer les avis du restaurant 1
    """reviews = session.query(Review).filter(Review.id_restaurant == 1).all()
    for review in reviews:
        print(f"Review ID: {review.id_review}, User: {review.user.user_name}, Rating: {review.rating}")

### Update reviews date

    # Exemple d'utilisation
    
    reviews = session.query(Review).all()

    for review in reviews:
        # Étape 2 : Appliquer la fonction de parsing sur la date de chaque review
        print(f"Review ID: {review.id_review}, Date avant parsing : {review.date_review}")

"""

    # Récupérer tous les restaurants
    # restaurants = get_all_restaurants(session)
    # print(f"Nombre de restaurants : {len(restaurants)}")
    """restaurants = get_all_restaurants(session)
    for restaurant in restaurants:
        print(f"Restaurant ID: {restaurant.id_restaurant}, Name: {restaurant.nom}")
    # Récupérer tous les restaurants avec leurs avis et utilisateurs associés
    restaurants_with_reviews = get_restaurants_with_reviews_and_users(session)
    for restaurant in restaurants_with_reviews:
        print(f"Restaurant: {restaurant.nom}")
        for review in restaurant.avis:
            print(f"  Review by {review.user.user_profile} (Rating: {review.rating})")
        """
    
    # Récupérer les csv des restaurants dans le dossier Data/scrapping
    
    scrapping_dir = os.path.join("src", "data")
    # restaurants = get_restaurants_from_folder(scrapping_dir)
    # process_csv_files(scrapping_dir, session, with_reviews=False)
    # print(get_restaurants_from_folder(scrapping_dir))
    # restaurants = get_restaurants_with_reviews_and_users(session)

    # print(get_restaurants_with_reviews())
    # print(get_scrapped_restaurants())
    # scrapped_restaurants = get_restaurants_from_folder(scrapping_dir)
    # print(scrapped_restaurants)
    # print(update_scrapped_status_for_reviews(session, scrapped_restaurants))
    # latitude, longitude = get_coordinates("4 Place des Terreaux Entrée à gauche du Tabac, sonner et pousser fort, 2ème étage, 69001 Lyon France")
    # print(get_coordinates("4 Place des Terreaux Entrée à gauche du Tabac, sonner et pousser fort, 2ème étage, 69001 Lyon France"))
    # update_restaurant_columns("L'Étage", {"latitude": latitude, "longitude": longitude}, session)
    # restaurants = get_restaurants_with_reviews()
    # print(len(restaurants))
    
        # update_restaurant_columns(restaurant_name, {"scrapped": True}, session)
    # update_restaurant_columns(restaurant_name, {"url_link": url}, session)
    # print(get_restaurant(session=session, restaurant_name="L'Étage"))

    # print(check_restaurants_in_db(scrapped_restaurants, session))
    # create_restaurants_from_csv("liste_restaurants.csv", session)
    """resume_avis = "resume_avis_restaurants_1.xlsx"
    file_path = os.path.join("Data", resume_avis)

    df = pd.read_excel(file_path)

    for _, row in df.iterrows():
        # print(row['restaurant'], row['resume_avis'])
        update_restaurant_columns(row['restaurant'], {"resume_avis": row['resume_avis']}, session)

    """

    # process_all_restaurants(scrapping_dir)



    
    
