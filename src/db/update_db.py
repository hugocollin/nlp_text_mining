from src.db.functions_db import  parse_french_date, execute_query, fetch_one 
from src.db.models import Restaurant 
from sqlalchemy import text
import locale



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


#### Pour insérer des review pour un restaurant
def insert_restaurant_reviews(restaurant_id,df, session):
    # Insérer les avis pour le restaurant à partir d'un DataFrame
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
                'review_cleaned': review['review_cleaned']  # Ajout de la colonne nettoyée
            }
            insert_review(review_data, int(restaurant_id))
            update_restaurant_columns(int(restaurant_id), {"scrapped": True}, session)
            print(f"Avis inséré pour {restaurant_id}.")
        session.commit()
    except Exception as e:
        print(f"Erreur lors de l'insertion des avis pour le restaurant {restaurant_id} : {e}")
        session.rollback()



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

def clear_reviews_of_restaurant(restaurant_id, session):
    """Efface tous les avis pour un restaurant donné et mets le champs scrapped = 0."""
    query = "DELETE FROM fact_reviews WHERE id_restaurant = ?"
    execute_query(query, [restaurant_id])
    update_restaurant_columns(restaurant_id, {"scrapped": False} , session  )
    print(f"Avis effacés pour le restaurant {restaurant_id}.")
