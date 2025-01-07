from models import init_db, get_session, Restaurant, Review, User
import sys
import os
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
    scrapper = tf.RestaurantFinder()
    restaurants = scrapper.scrape_all_restaurants(max_pages=1)

    for restaurant in restaurants:
        print(restaurant)
        
        rest_info = tf.restaurant_info_extractor()
        restaurant_data, reviews = rest_info.scrape_restaurant(restaurant['url'])
        print(restaurant_data)

        restaurant_id = insert_restaurant(
            name=restaurant['name'],
            url=restaurant['url'],
            adresse=restaurant_data['Emplacement et coordonnées'].get('ADRESSE', None),
            email=restaurant_data['Emplacement et coordonnées'].get('EMAIL', None),
            telephone=restaurant_data['Emplacement et coordonnées'].get('TELEPHONE', None),
            cuisines=restaurant_data['Détails'].get('CUISINES', None),
            note_globale=float(restaurant_data['Notes et avis'].get('NOTE GLOBALE', '0').replace(',', '.')) if restaurant_data['Notes et avis'].get('NOTE GLOBALE', None) else None,
            cuisine_note=float(restaurant_data['Notes et avis'].get('CUISINE', '0').replace(',', '.')) if restaurant_data['Notes et avis'].get('CUISINE', None) else None,
            service_note=float(restaurant_data['Notes et avis'].get('SERVICE', '0').replace(',', '.')) if restaurant_data['Notes et avis'].get('SERVICE', None) else None,
            qualite_prix_note=float(restaurant_data['Notes et avis'].get('RAPPORT QUALITÉ-PRIX', '0').replace(',', '.')) if restaurant_data['Notes et avis'].get('RAPPORT QUALITÉ-PRIX', None) else None,
            ambiance_note=float(restaurant_data['Notes et avis'].get('AMBIANCE', '0').replace(',', '.')) if restaurant_data['Notes et avis'].get('AMBIANCE', None) else None,
            prix_min=float(restaurant_data['Détails'].get('FOURCHETTE DE PRIX', '').replace('\xa0€', '').split('-')[0].replace(',', '.')) if '-' in restaurant_data['Détails'].get('FOURCHETTE DE PRIX', '') else None,
            prix_max=float(restaurant_data['Détails'].get('FOURCHETTE DE PRIX', '').replace('\xa0€', '').split('-')[1].replace(',', '.')) if '-' in restaurant_data['Détails'].get('FOURCHETTE DE PRIX', '') else None,
            etoiles_michelin=int(restaurant_data['Détails'].get('ÉTOILES MICHELIN', 0)),
            repas=restaurant_data['Détails'].get('REPAS', None)
        )

        print("##################################################")
        print(reviews)

        for review in reviews:
            insert_review(review, restaurant_id)

