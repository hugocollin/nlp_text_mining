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
        review['date_review'],
        review['title'],
        review['review'],
        review['rating'],
        review['type_visit']
    ])

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


    ## Prochaine étape : remplir la base de données avec les données scrapper
    # Insérer les restaurants
    restaurant_csv_file = "info_restaurants_plus.csv"

    # process_restaurant_csv(restaurant_csv_file)

    restaurants_scrapped = session.query(Restaurant).all()
    
    # Parcourir et imprimer les restaurants
    
    for restaurant in restaurants_scrapped:
        if restaurant.scrapped:
            print(f"Scrappé ID: {restaurant.id_restaurant}, Nom: {restaurant.nom}, Adresse: {restaurant.adresse}")
        else:
            print(f"Non scrappé ID: {restaurant.id_restaurant}, Nom: {restaurant.nom}, Adresse: {restaurant.adresse}")
    

    """restaurants = get_all_restaurants(session)
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
       

