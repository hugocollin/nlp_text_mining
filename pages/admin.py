import streamlit as st
from db.models import get_user_and_review_from_restaurant_id , get_all_restaurants
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pages.resources.components import Navbar
import pandas as pd
from sqlalchemy import inspect
from sqlalchemy.sql import text


set_page_config = st.set_page_config(page_title="SISE Ô Resto - Admin", page_icon="🍽️", layout="wide")

# Connexion à la base de données
engine = create_engine('sqlite:///restaurant_reviews.db')
Session = sessionmaker(bind=engine)
session = Session()

# Récupération de tous les restaurants
restaurants = get_all_restaurants(session)

def display_restaurant_stats():
    # Calculer le nombre de restaurants scrappés
    
    nombre_scrapped = len([r for r in restaurants if r.scrapped == 1])

    # Afficher le résultat dans Streamlit
    st.write(f"Nombre de restaurants scrappés : {nombre_scrapped}")   
    nom_scrapped = [r.nom for r in restaurants if r.scrapped == 1]

    df = pd.DataFrame(nom_scrapped, columns = ['Nom des restaurants scrappés'])
    col1 , col2 = st.columns(2)
    with col1:
        st.write("Liste des restaurants scrappés")
        st.write(df)
    with col2:
        st.write("Unique values")
        st.write(df.value_counts())
 
def execute_sql_query(session):
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()

    st.header("Exécuter une requête SQL avec Jointure")

    # Sélection des tables
    selected_tables = st.multiselect("Sélectionnez les tables à joindre", options=tables)

    if not selected_tables:
        st.info("Veuillez sélectionner au moins une table pour exécuter une requête.")
        return

    # Sélection des colonnes à afficher
    selected_columns = []
    for table in selected_tables:
        columns = inspector.get_columns(table)
        column_names = [f"{table}.{column['name']}" for column in columns]
        cols = st.multiselect(f"Sélectionnez les colonnes de la table '{table}'", options=column_names, default=column_names)
        selected_columns.extend(cols)

    if not selected_columns:
        st.warning("Veuillez sélectionner au moins une colonne à afficher.")
        return

    # Gestion des jointures
    join_types = ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL OUTER JOIN"]
    joins = []

    if len(selected_tables) > 1:
        st.subheader("Configurer les Jointures")

        for i in range(1, len(selected_tables)):
            st.markdown(f"**Jointure {i}**")
            left_table = selected_tables[i - 1]
            right_table = selected_tables[i]

            col1, col2, col3 = st.columns(3)

            with col1:
                join_type = st.selectbox(f"Type de jointure pour {right_table}", options=join_types, key=f"join_type_{i}")

            with col2:
                left_columns = inspector.get_columns(left_table)
                left_col_names = [column['name'] for column in left_columns]
                left_join_column = st.selectbox(
                    f"Colonne de jointure dans '{left_table}'",
                    options=left_col_names,
                    key=f"left_join_col_{i}"
                )

            with col3:
                right_columns = inspector.get_columns(right_table)
                right_col_names = [column['name'] for column in right_columns]
                right_join_column = st.selectbox(
                    f"Colonne de jointure dans '{right_table}'",
                    options=right_col_names,
                    key=f"right_join_col_{i}"
                )

            # Ajouter la jointure à la liste
            joins.append({
                "join_type": join_type,
                "left_table": left_table,
                "right_table": right_table,
                "left_column": left_join_column,
                "right_column": right_join_column
            })
            
    # Construction de la requête SQL avec alias pour éviter les noms de colonnes dupliqués
    select_clause = []
    for col in selected_columns:
        alias = col.replace('.', '_')
        select_clause.append(f"{col} AS {alias}")

    # Construction de la requête SQL
    query = "SELECT " + ", ".join(selected_columns) + " FROM " + selected_tables[0]

    for join in joins:
        query += f" {join['join_type']} {join['right_table']} ON {join['left_table']}.{join['left_column']} = {join['right_table']}.{join['right_column']}"


    # Option de Group By
    group_by_columns = []
    if st.checkbox("Ajouter une clause GROUP BY"):
        group_by_columns = st.multiselect(
            "Sélectionnez les colonnes pour GROUP BY",
            options=selected_columns,
            help="Sélectionnez les colonnes sur lesquelles grouper les résultats."
        )
        if group_by_columns:
            query += f" GROUP BY {', '.join(group_by_columns)}"
# Option de Sort By
    sort_by_columns = []
    if st.checkbox("Ajouter une clause ORDER BY"):
        sort_by_columns = st.multiselect(
            "Sélectionnez les colonnes pour ORDER BY",
            options=selected_columns,
            help="Sélectionnez les colonnes par lesquelles trier les résultats."
        )
        if sort_by_columns:
            # Sélection de l'ordre de tri pour chaque colonne
            sort_orders = {}
            for col in sort_by_columns:
                sort_orders[col] = st.selectbox(
                    f"Ordre pour '{col}'",
                    options=["ASC", "DESC"],
                    key=f"sort_order_{col}"
                )
            order_clause = ", ".join([f"{col} {order}" for col, order in sort_orders.items()])
            query += f" ORDER BY {order_clause}"

    # Option de Limitation des Résultats
    add_limit = st.checkbox("Limiter le nombre de lignes retournées", value=True)
    limit = 100  # Valeur par défaut
    if add_limit:
        limit = st.number_input(
            "Nombre de lignes à retourner",
            min_value=1,
            max_value=10000,
            value=100,
            step=1,
            help="Limitez le nombre de lignes retournées par la requête."
        )
        query += f" LIMIT {limit}"
    st.write(f"**Requête SQL:** `{query}`")

    # Bouton pour exécuter la requête
    if st.button("Exécuter la Requête"):
        try:
            # Exécution de la requête
            df = pd.read_sql_query(text(query), session.bind)

            # Fonction pour rendre les noms de colonnes uniques si des duplications existent
            def make_unique_columns(columns):
                counts = {}
                new_columns = []
                for col in columns:
                    if col in counts:
                        counts[col] += 1
                        new_columns.append(f"{col}_{counts[col]}")
                    else:
                        counts[col] = 1
                        new_columns.append(col)
                return new_columns

            # Appliquer la fonction pour rendre les noms de colonnes uniques
            df.columns = make_unique_columns(df.columns)

            st.success("Requête exécutée avec succès!")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Erreur lors de l'exécution de la requête: {e}")

def main():
    # Barre de navigation
    Navbar()
    
    st.title("Administration")
    st.write("Bienvenue sur la page d'administration de l'application SISE Ô Resto.")
    
    # Exécuter la requête SQL personnalisée
    execute_sql_query(session)
    st.write("----")

    # Afficher les statistiques pour tous les restaurants
    display_restaurant_stats()
    
    st.write("----")
    

if __name__ == '__main__':
    main()