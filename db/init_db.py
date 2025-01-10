from models import init_db, get_session, Restaurant, Review, User, get_all_restaurants
import sys
import os
import pandas as pd
import ast
from sqlalchemy import update, select, exists, create_engine, text
from sqlalchemy.orm import Session
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from databases import execute_query, fetch_one, create_schema, database_exists
from searchengine import trip_finder as tf
from geopy.geocoders import Nominatim
import locale
from datetime import datetime



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
    repas=None
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
                prix_min, prix_max, etoiles_michelin, repas
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            prix_min, prix_max, etoiles_michelin, repas
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
        
        date_str = date_str.replace(fr, en, regex=False)
        print(date_str)

    try:
        parsed_date = datetime.strptime(date_str, "%d %B %Y").date()
        print("parsed date")
        print(parsed_date)
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
    """Convertit une valeur en float si possible, sinon retourne None."""
    try:
        return float(value.replace(',', '.')) if value not in [None, 'N/A', ''] else None
    except ValueError:
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
        print(restaurant_data['Emplacement et coordonnées'])

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
        repas=restaurant_data['Détails'].get('REPAS', None)
    )
        


def get_coordinates(address):
    """
    Obtenir les coordonnées (latitude, longitude) d'une adresse en utilisant Nominatim.
    Nettoie et tente de nouveau si la géolocalisation échoue.
    """
    geolocator = Nominatim(user_agent="sise_o_resto", timeout=15)
    current_address = address
    attempts = 0  # Compteur pour éviter une boucle infinie

    while attempts < 5:  # Limite le nombre de tentatives pour éviter une boucle infinie
        try:
            location = geolocator.geocode(f"{current_address}, Rhône, France")
            print(f"Tentative avec adresse : {current_address}")
            if location:
                print(f"Adresse trouvée : {location.address}")
                return location.latitude, location.longitude

            # Si la géolocalisation échoue, nettoyer l'adresse
            if ',' in current_address:
                print("Nettoyage de l'adresse...")
                before_comma, after_comma = current_address.split(',', 1)
                before_words = before_comma.strip().split(' ')
                if len(before_words) > 1:
                    # Retirer le dernier mot avant la virgule
                    before_words = before_words[:-1]
                    new_before = ' '.join(before_words)
                    current_address = f"{new_before}, {after_comma.strip()}"
                else:
                    # Utiliser uniquement la partie après la virgule si le segment avant la virgule est trop court
                    current_address = after_comma.strip()
            else:
                # Si l'adresse est trop courte ou mal formée, arrêter
                print("Impossible de nettoyer davantage l'adresse.")
                break
        except Exception as e:
            print(f"Erreur lors de la géolocalisation : {e}")
            break  # Arrêter en cas d'erreur inattendue
        finally:
            attempts += 1

    print("Coordonnées introuvables après plusieurs tentatives.")
    return None, None


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
    restaurant_csv_file = "info_restaurants_plus.csv"

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
            text("ALTER TABLE dim_restaurants ADD COLUMN scrapped BOOLEAN DEFAULT 0")
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
"""
### Update reviews date

    # Exemple d'utilisation
    date_str = "16 décembre 2024"
    parsed_date = parse_french_date(date_str)
    print(parsed_date)  # Affiche : 2024-12-16


       

