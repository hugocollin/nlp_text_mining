import locale
from src.db.functions_db import  parse_french_date, execute_query, fetch_one 
from src.db.models import Restaurant

# Définition de la zone géographique pour les dates en français
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'C')

# Fonction d'insertion d'un restaurant dans la base de données
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
    # Vérification si le restaurant existe déjà
    existing_restaurant = fetch_one(
        "SELECT id_restaurant FROM dim_restaurants WHERE nom = ?", [name]
    )

    if existing_restaurant:
        # Renvoi de l'id du restaurant s'il existe déjà
        return existing_restaurant[0]
    else:
        # Insertion d'un nouveau restaurant s'il n'existe pas
        query = """
            INSERT INTO dim_restaurants (
                nom, adresse, url_link, email, telephone, cuisines, 
                note_globale, cuisine_note, service_note, qualite_prix_note, ambiance_note,
                prix_min, prix_max, etoiles_michelin, repas, latitude, longitude, scrapped, image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Extraction du prix min et max si les valeurs sont des chaînes de caractères
        if isinstance(prix_min, str):
            prix_min = float(prix_min.replace(',', '.').replace('€', '').strip())
        if isinstance(prix_max, str):
            prix_max = float(prix_max.replace(',', '.').replace('€', '').strip())

        # Enregistrement des données dans la base de données
        params = [
            name, adresse, url, email, telephone, cuisines,
            note_globale, cuisine_note, service_note, qualite_prix_note, ambiance_note,
            prix_min, prix_max, etoiles_michelin, repas, latitude, longitude, scrapped, image
        ]
        execute_query(query, params=params)

        # Récupération de l'id du restaurant inséré
        new_restaurant = fetch_one(
            "SELECT id_restaurant FROM dim_restaurants WHERE nom = ?", [name]
        )
        return new_restaurant[0]

# Fonction d'insertion d'un utilisateur dans la base de données
def insert_user(user_name, user_profile, num_contributions):
    # Enregistrement des données dans la base de données
    query = """
        INSERT OR IGNORE INTO dim_users (user_name, user_profile, num_contributions)
        VALUES (?, ?, ?)
    """
    execute_query(query, params=[user_name, user_profile, num_contributions])

    # Récupération de l'id de l'utilisateur inséré
    result = fetch_one("SELECT id_user FROM dim_users WHERE user_name = ?", [user_name])
    return result[0]

# Fonction d'insertion d'un avis dans la base de données
def insert_review(review, id_restaurant):
    # Vérification si l'utilisateur existe déjà
    query_user = "SELECT id_user FROM dim_users WHERE user_profile = ?"
    existing_user = fetch_one(query_user, [review['user_profile']])

    # Insertion de l'utilisateur s'il n'existe pas
    if not existing_user:
        # Enregistrement des données dans la base de données
        insert_user_query = """
        INSERT INTO dim_users (user_name, user_profile, num_contributions)
        VALUES (?, ?, ?)
        """
        execute_query(insert_user_query, [
            review['user'], 
            review['user_profile'], 
            review.get('num_contributions', 0)
        ])
        # Récupération de l'id de l'utilisateur inséré
        id_user = fetch_one(query_user, [review['user_profile']])[0]
    else:
        id_user = existing_user[0] # Renvoi de l'ID de l'utilisateur s'il existe déjà

    # Conversion de la date de l'avis
    review_date = parse_french_date(review.get('date', ''))
    if not review_date:
        print(f"Date invalide pour l'avis : {review.get('date', '')}")
        return

    # Enregistrement de l'avis dans la base de données
    insert_review_query = """
    INSERT INTO fact_reviews (
        id_restaurant, 
        id_user, 
        date_review, 
        title_review, 
        review_text, 
        rating, 
        type_visit,
        review_cleaned
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    execute_query(insert_review_query, [
        id_restaurant,
        id_user,
        review_date,
        review['title'],
        review['review'],
        review['rating'],
        review['type_visit'],
        review['review_cleaned']
    ])

# Fonction d'insertion des avis pour un restaurant
def insert_restaurant_reviews(restaurant_id,df, session):
    # Itération sur chaque avis pour le restaurant
    try:
        for _, review in df.iterrows():
            review_data = {
                "user": review['user'],
                "user_profile": review['user_profile'],
                "num_contributions": review['num_contributions'],
                "date": review['date_review'],
                "title": review['title'],
                "review": review['review'],
                "rating": review['rating'],
                "type_visit": review['type_visit'],
                'review_cleaned': review['review_cleaned']
            }

            # Insertion de l'avis dans la base de données
            insert_review(review_data, int(restaurant_id))

            # Mise à jour du statut scrapped du restaurant
            update_restaurant_columns(int(restaurant_id), {"scrapped": True}, session)

            print(f"Avis inséré pour {restaurant_id}.")
        session.commit()
    except Exception as e:
        print(f"Erreur lors de l'insertion des avis pour le restaurant {restaurant_id} : {e}")
        session.rollback()

# Fonction de mise à jour du statut scrapped pour les restaurants
def update_scrapped_status_for_reviews(session, restaurant_names):
    # Vérification si la liste des noms de restaurants est vide
    if not restaurant_names:
        print("La liste des noms de restaurants est vide. Aucun traitement effectué.")
        return

    # Mise à jour du statut scrapped pour les restaurants
    try:
        session.query(Restaurant) \
            .filter(Restaurant.nom.in_(restaurant_names)) \
            .update({Restaurant.scrapped: True}, synchronize_session='fetch')

        session.commit()
        print(f"Colonne 'scrapped' mise à jour pour {len(restaurant_names)} restaurants.")
    except Exception as e:
        session.rollback()
        print("Une erreur s'est produite lors de la mise à jour.")
        print(f"Erreur : {e}")

# Fonction de mise à jour des colonnes d'un restaurant
def update_restaurant_columns(restaurant_id, updates, session):
    # Vérification si des mises à jour sont spécifiées
    if not updates:
        print("Aucune mise à jour spécifiée.")
        return False

    # Mise à jour des colonnes du restaurant
    try:
        session.query(Restaurant).filter_by(id_restaurant=restaurant_id).update(updates)
        session.commit()
        print(f"Restaurant '{restaurant_id}' mis à jour avec succès.")
        return True
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de la mise à jour du restaurant '{restaurant_id}': {e}")
        return False

# Fonction de suppression des avis pour un restaurant
def clear_reviews_of_restaurant(restaurant_id, session):
    # Suppression des avis pour le restaurant
    query = "DELETE FROM fact_reviews WHERE id_restaurant = ?"
    execute_query(query, [restaurant_id])

    # Mise à jour du statut scrapped du restaurant
    update_restaurant_columns(restaurant_id, {"scrapped": False} , session )

    print(f"Avis effacés pour le restaurant {restaurant_id}.")