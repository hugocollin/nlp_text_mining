import streamlit as st

from pages.resources.components import Navbar

import pandas as pd

from sqlalchemy import inspect, text 

from sqlalchemy.types import Integer, Float

from src.searchengine.trip_finder import SearchEngine, restaurant_info_extractor

import time


from src.pipeline import Pipeline , Transistor

transistor = Transistor()
session = transistor.session
# Configuration de la page
set_page_config = st.set_page_config(page_title="SISE Ô Resto - Admin", page_icon="🍽️", layout="wide")

# Réinitialisation de popup de vérification de l'adresse renseignée
if 'address_toast_shown' in st.session_state:
    del st.session_state['address_toast_shown']



# Récupération de tous les restaurants
restaurants = transistor.get_all_restaurants()

def get_column_type(inspector, table, column):
    """Helper function to get the data type of a column."""
    columns = inspector.get_columns(table)
    for col in columns:
        if col['name'] == column:
            return col['type']
    return None

def make_unique_columns(columns):
    """Helper function to make column names unique by appending suffixes."""
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

def display_restaurant_stats():
    # Calculer le nombre de restaurants scrappés
    st.header("Statistiques des Restaurants")
    nombre_scrapped = len([r for r in restaurants if r.scrapped == 1])

    # Afficher le résultat dans Streamlit
    st.write(f"Nombre de restaurants scrappés : {nombre_scrapped}")  
    nombre_restaurants = len(restaurants)
    st.write(f"Nombre total de restaurants : {nombre_restaurants}") 
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

    # Vérification des tables nécessaires pour les jointures
    if 'restaurant' in selected_tables and 'user' in selected_tables and 'review' not in selected_tables:
        st.warning("La table 'review' est requise pour joindre 'restaurant' et 'user'. Elle a été ajoutée automatiquement.")
        selected_tables.append('review')

    if not selected_tables:
        st.info("Veuillez sélectionner au moins une table pour exécuter une requête.")
        return

    # Sélection des colonnes à afficher
    selected_columns = []
    for table in selected_tables:
        columns = inspector.get_columns(table)
        column_names = [f"{column['name']}" for column in columns]
        selected_columns.extend(st.multiselect(f"Colonnes de '{table}'", options=column_names, default=column_names))
        
        selected_columns = [f'{table}.{col}' for col in selected_columns]
    
    
    
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

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                join_type = st.selectbox(f"Type de jointure pour '{right_table}'", options=join_types, key=f"join_type_{i}")

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

    # Option de Filtrage
    filter_clauses = []
    if st.checkbox("Ajouter une clause WHERE"):
        # Sélectionner les colonnes disponibles pour filtrer
        filter_columns = st.multiselect(
            "Sélectionnez les colonnes à filtrer",
            options=selected_columns,
            help="Sélectionnez les colonnes sur lesquelles appliquer le filtre."
        )

        for col in filter_columns:
            # gere le cas où il y a que une table
            if '.' in col:
                
                table, column = col.split('.')
            else:
                table = selected_tables[0]
                column = col
            column_type = get_column_type(inspector, table, column)

            st.markdown(f"**Filtrer par {col}**")
            if hasattr(column_type, 'python_type'):
                python_type = column_type.python_type
            else:
                python_type = str  # Default to string if type not found

            # Choisir le type de filtre
            filter_type = st.selectbox(
                f"Type de filtre pour '{col}'",
                options=["=", ">=", "<=", "IN", "CONTAINS"],
                key=f"filter_type_{col}"
            )

            if filter_type in ["=", ">=", "<="]:
                # Filtre avec un opérateur simple
                input_value = st.text_input(
                    f"Entrez la valeur pour '{col}'",
                    help=f"Entrez la valeur pour '{col}'.",
                    key=f"input_{col}"
                )
                if input_value:
                    try:
                        if python_type == int:
                            value = int(input_value)
                        elif python_type == float:
                            value = float(input_value)
                        else:
                            value = f"'{input_value}'"
                        filter_clauses.append(f"{col} {filter_type} {value}")
                    except ValueError:
                        st.error(f"Entrée invalide pour '{col}'. Veuillez entrer une valeur de type approprié.")
            elif filter_type == "IN":
                # Filtre avec une liste de valeurs
                input_values = st.text_input(
                    f"Entrez les valeurs pour '{col}' séparées par des virgules",
                    help=f"Entrez les valeurs pour '{col}' séparées par des virgules.",
                    key=f"in_input_{col}"
                )
                if input_values:
                    try:
                        if python_type == int:
                            values = [int(val.strip()) for val in input_values.split(',')]
                        elif python_type == float:
                            values = [float(val.strip()) for val in input_values.split(',')]
                        else:
                            values = [f"'{val.strip()}'" for val in input_values.split(',')]
                        formatted_values = ", ".join(map(str, values))
                        filter_clauses.append(f"{col} IN ({formatted_values})")
                    except ValueError:
                        st.error(f"Entrée invalide pour '{col}'. Veuillez entrer des valeurs de type approprié séparées par des virgules.")
            elif filter_type == "CONTAINS":
                # Filtre avec une condition LIKE
                input_value = st.text_input(
                    f"Entrez la chaîne pour '{col}'",
                    help=f"Entrer la sous-chaîne que '{col}' doit contenir.",
                    key=f"contains_input_{col}"
                )
                if input_value:
                    escaped_value = input_value.replace("'", "''")
                    filter_clauses.append(f"{col} LIKE '%{escaped_value}%'")

        # Test de la clause WHERE avant de construire la requête complète
        if filter_clauses:
            test_query = f"SELECT 1 FROM {selected_tables[0]}"
            for join in joins:
                test_query += f" {join['join_type']} {join['right_table']} ON {join['left_table']}.{join['left_column']} = {join['right_table']}.{join['right_column']}"
            test_query += " WHERE " + " AND ".join(filter_clauses)
            test_query += " LIMIT 1"

            try:
                # Exécution de la requête de test
                pd.read_sql_query(text(test_query), session.bind)
                st.success("Filtres valides. La requête peut être exécutée.")
            except Exception as e:
                st.error(f"Erreur dans les filtres WHERE : {e}. Veuillez ajuster vos filtres.")
                st.stop()  # Arrêter l'exécution si les filtres sont invalides

    # Construction de la requête SQL
    query = "SELECT " + ", ".join(selected_columns) + " FROM " + selected_tables[0]

    for join in joins:
        query += f" {join['join_type']} {join['right_table']} ON {join['left_table']}.{join['left_column']} = {join['right_table']}.{join['right_column']}"

    # Appliquer les filtres
    if filter_clauses:
        query += " WHERE " + " AND ".join(filter_clauses)

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
    st.write(f"**Requête SQL Finale:** `{query}`")

    # Bouton pour exécuter la requête
    if st.button("Exécuter la Requête"):
        try:
            # Exécution de la requête
            df = pd.read_sql_query(text(query), session.bind)
            for col in df.columns:
                if 'date' in col.lower():
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    

            # Appliquer la fonction pour rendre les noms de colonnes uniques
            df.columns = make_unique_columns(df.columns)

            st.success("Requête exécutée avec succès!")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Erreur lors de l'exécution de la requête: {e}")

def edit_table(session):
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()

    st.header("Modification de la base de données")

    # Sélection de la table à modifier
    table_to_edit = st.selectbox(
        "Sélectionnez la table à modifier",
        options=tables,
        help="Choisissez la table où vous souhaitez modifier les données."
    )

    if not table_to_edit:
        st.info("Veuillez sélectionner une table pour continuer.")
        return

    # Récupération des colonnes de la table
    columns = inspector.get_columns(table_to_edit)
    column_names = [column['name'] for column in columns]

    # Identification des clés primaires
    primary_keys = [col['name'] for col in columns if col['primary_key']]
    if not primary_keys:
        st.error("Cette table n'a pas de clé primaire définie. Impossible de modifier les lignes.")
        return

    # Affichage des données de la table
    query = f"SELECT * FROM {table_to_edit}"
    try:
        df = pd.read_sql_query(text(query), session.bind)
        st.dataframe(df)
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données: {e}")
        return

    st.subheader("Modifier une Ligne")

    # Sélection de la ligne à modifier
    if df.empty:
        st.info("La table est vide.")
        return

    row_index = st.number_input(
        "Entrez l'index de la ligne à modifier (0 à {})".format(len(df)-1),
        min_value=0,
        max_value=len(df)-1,
        step=1,
        help="Entrez l'index de la ligne que vous souhaitez modifier."
    )

    selected_row = df.iloc[row_index]

    # Création des champs de saisie pour chaque colonne
    new_values = {}
    for col in column_names:
        new_values[col] = st.text_input(
            f"{col}",
            value=str(selected_row[col]),
            key=f"edit_{col}"
        )

    if st.button("Enregistrer les Modifications"):
        # Construction du filtre basé sur les clés primaires
        filter_conditions = []
        for pk in primary_keys:
            pk_value = selected_row[pk]
            if isinstance(pk_value, str):
                escaped_pk = pk_value.replace("'", "''")
                filter_conditions.append(f"{pk} = '{escaped_pk}'")
            else:
                filter_conditions.append(f"{pk} = {pk_value}")
        where_clause = " AND ".join(filter_conditions)

        # Construction de l'instruction UPDATE
        set_clause = []
        for col in column_names:
            if col in primary_keys:
                continue  # Ne pas modifier les clés primaires
            value = new_values[col]
            column_type = next((c['type'] for c in columns if c['name'] == col), None)

            if isinstance(column_type, Integer):
                if value.lower() == 'nan' or value == '':
                    set_clause.append(f"{col} = NULL")
                else:
                    try:
                        set_clause.append(f"{col} = {int(value)}")
                    except ValueError:
                        st.error(f"Valeur invalide pour {col}. Doit être un entier.")
                        return
            elif isinstance(column_type, Float):
                if value.lower() == 'nan' or value == '':
                    set_clause.append(f"{col} = NULL")
                else:
                    try:
                        set_clause.append(f"{col} = {float(value)}")
                    except ValueError:
                        st.error(f"Valeur invalide pour {col}. Doit être un nombre flottant.")
                        return
            else:
                if value.lower() == 'nan' or value == '':
                    set_clause.append(f"{col} = NULL")
                else:
                    escaped_value = value.replace("'", "''")
                    set_clause.append(f"{col} = '{escaped_value}'")

        if not set_clause:
            st.info("Aucune modification à appliquer.")
            return

        update_query = f"UPDATE {table_to_edit} SET {', '.join(set_clause)} WHERE {where_clause}"

        try:
            session.execute(text(update_query))
            session.commit()
            st.success("Ligne mise à jour avec succès.")
            
            time.sleep(1)
            # refresh les données edits
            st.rerun()
        except Exception as e:
            session.rollback()
            st.error(f"Erreur lors de la mise à jour de la ligne: {e}")

#######################
def get_element_inspector_js():
 return """
    <script>
    let isInspecting = true;
    
    function cleanElement(element) {
        // Create a new element of the same type
        const clean = element.cloneNode(false);
        // Remove style attribute
        clean.removeAttribute('style');
        // Copy children recursively
        for (const child of element.childNodes) {
            if (child.nodeType === 1) { // Element node
                clean.appendChild(cleanElement(child));
            } else {
                clean.appendChild(child.cloneNode(true));
            }
        }
        return clean;
    }
    
    function getElementInfo(element) {
        // Get clean copy without styles
        const clean = cleanElement(element);
        
        // Escape HTML special characters
        const escaped = clean.outerHTML
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
            
        return `<pre class="code-display"><code>${escaped}</code></pre>`;
    }
    document.addEventListener('mouseover', function(e) {
        // Skip if element is part of selected-text or has code-display class
        if (!isInspecting || 
            e.target.closest('#selected-text') || 
            e.target.closest('.code-display')) return;
        e.target.style.outline = '2px solid red';
    });
  
    document.addEventListener('mouseout', function(e) {
        if (!isInspecting || 
            e.target.closest('#selected-text') || 
            e.target.closest('.code-display')) return;
        e.target.style.outline = '';
    });
    
    document.addEventListener('click', function(e) {
        if (!isInspecting || 
            e.target.closest('#selected-text') || 
            e.target.closest('.code-display')) return;
        e.preventDefault();
        e.stopPropagation();
        
        const html = getElementInfo(e.target);
        document.getElementById('selected-text').innerHTML = html;
    });
    </script>
    <style>
    #selected-text {
        position: fixed;
        bottom: 0;
        left: 0;
        background: white;
        padding: 10px;
        border: 1px solid black;
        user-select: text;
        -webkit-user-select: text;
        cursor: text;
        z-index: 9999;
    }
    .code-display {
        pointer-events: none;
    }
    .code-display * {
        pointer-events: none;
        outline: none !important;
    }
    </style>
    """
def scrape_and_embed_tripadvisor():
    st.header("Affichage html des élements HTML d'un restaurant")
    # Récupérer les restaurants non scrappés
    restaurants = transistor.get_all_restaurants()
    if not restaurants:
        st.warning("Aucun restaurant n'a été trouvé.")
    else:
        
 
        restaurant_names = {r.nom : r for r in restaurants}
        selected_name = st.selectbox("Sélectionnez un restaurant à scrappé", list(restaurant_names.keys()) , key="select_html_rest")
        # Get selected restaurant object
        restaurant = restaurant_names[selected_name]
        st.write(f"Vous avez sélectionné le restaurant : {restaurant.nom}")
        
        if st.button("Scraper le restaurant"):
                with st.spinner("Récupération des données TripAdvisor..."):
                    url = restaurant.url_link
                    search = SearchEngine()
                    search.run(url)
                
                if 'selected_html' not in st.session_state:
                    st.session_state.selected_html = None
                st.session_state.inspecting = True
                    
                # Add text area for element info
                element_info = st.empty()
                
                # Embed page with inspector
                html_content = search.soup.prettify()
                html_with_inspector = f"""
                            {get_element_inspector_js()}
                            <div id="content">
                                {html_content}
                            </div>
                            <div id="selected-text" 
                                style="position:fixed;bottom:0;left:0;
                                        background:white;padding:10px;
                                        border:1px solid black;">
                                Cliquez sur un élément pour voir son contenu
                            </div>
                        """
                            
                st.components.v1.html(
                            html_with_inspector,
                            height=800,
                            scrolling=True
                        )
    
    
    
    # pour plus tard 
    #     # Récupérer les restaurants non scrappés
    # st.header("Scraper les informations des restaurants")
    # restaurants = get_all_restaurants(session)
    # # Filtrer les restaurants non scrappés
    # non_scrapped_restaurants = [r for r in restaurants if r.scrapped == 0]
    # if not non_scrapped_restaurants:
    #     st.warning("Tous les restaurants ont déjà été scrappés.")
    # else:
    #     restaurant_names = {r.nom: r for r in non_scrapped_restaurants}
    #     selected_name = st.selectbox("Sélectionnez un restaurant à scrappé", list(restaurant_names.keys()))
    # # Get selected restaurant object
    #     restaurant = restaurant_names[selected_name]
    #     st.write(f"Vous avez sélectionné le restaurant : {restaurant.nom}")
        
def scrape_restaurant_informations():
    # Récupérer les restaurants non scrappés
    st.header("Scraper les informations des restaurants")
    restaurants = transistor.get_all_restaurants()
    # Filtrer les restaurants non scrappés
    
    restaurant_names = {r.nom : r for r in restaurants}
    selected_name = st.selectbox("Sélectionnez un restaurant à scrappé", list(restaurant_names.keys()))
# Get selected restaurant object
    restaurant = restaurant_names[selected_name]
    st.write(f"Vous avez sélectionné le restaurant : {restaurant.nom}")
    
    if st.button("Scraper le restaurant", key="scrape_info"):
            with st.spinner("Récupération des données TripAdvisor..."):
                url = restaurant.url_link
                search = restaurant_info_extractor()
                search.scrape_info(url)
                df_avis, df_details, df_location, _ = search.to_dataframe()
            st.write("Les données ont été scrappées avec succès.")
            st.write("----")
            col1,col2, col3 = st.columns(3)
            with col1:
                st.write("Détails du restaurant")
                st.write(df_details)
            with col2:
                st.write("Localisation")
                st.write(df_location)
            with col3:
                st.write("Avis")
                st.write(df_avis)
    
            
            
def pipeline_processing():
    
    # Récupérer les restaurants non scrappés
    pipe = Pipeline()
    st.header("Scraper les informations des restaurants")

    restaurants = pipe.get_restaurants_non_scrapped()
    restaurant_names = {r.nom : r for r in restaurants}
    selected_name = st.selectbox("Sélectionnez un restaurant à scrappé", list(restaurant_names.keys()))
    # Get selected restaurant object
    restau = restaurant_names[selected_name]
    if st.button("Scrapper ", key="scrape_everything" , help="Scrapper les informations du restaurant sélectionné"  ):  #, disabled=True
        pipe.add_new_restaurant(restau)
        st.success("Les informations ont été scrappées avec succès.")
        st.rerun()
    

def clear_reviews_one_restaurant():
    # Récupérer les restaurants non scrappés
    pipe = Pipeline()
    st.header("Supprimer les avis d'un restaurant")

    # Récupérer les ids des restaurants et print le nom de celui selectionné
    restaurants = pipe.get_restaurants()
    restaurant_names = {r.nom : r for r in restaurants}
    selected_name = st.selectbox("Sélectionnez un restaurant à vider", list(restaurant_names.keys()))
    # Get selected restaurant object
    restau = restaurant_names[selected_name]
    if st.button("Vider les avis", key="clear_reviews" , help="Vider les avis du restaurant sélectionné"  ):  #, disabled=True
        pipe.clear_reviews_of_restaurant(restau.id_restaurant)
       
        st.success("Les avis ont été supprimés avec succès.")
        time.sleep(2)
        st.rerun()



def try_prep_analysis_on_restaurant():
    
    # Récupérer les restaurants non scrappés
    pipe = Pipeline()
    st.header("Préparation de l'analyse des avis")

    # Récupérer les ids des restaurants et print le nom de celui selectionné
    restaurants = pipe.get_restaurants()
    restaurants = [r for r in restaurants if r.scrapped == 1]
    restaurant_names = {r.nom : r for r in restaurants}
    selected_name = st.selectbox("Sélectionnez un restaurant à analyser", list(restaurant_names.keys()))
    # Get selected restaurant object
    restau = restaurant_names[selected_name]
    if st.button("Préparer l'analyse", key="prep_analysis" , help="Préparer les avis du restaurant sélectionné pour l'analyse"  ):  #, disabled=True
        pipe.clean_reviews(restau.id_restaurant)
        st.success("Les avis ont été préparés avec succès.")
        time.sleep(2)
        st.rerun()

def clean_reviews_pipeline():
    # Récupérer les restaurants non scrappés
    pipe = Pipeline()
    st.header("Nettoyer les avis des restaurants")

    # Récupérer les ids des restaurants et print le nom de celui selectionné
    restaurants = pipe.get_restaurants()
    restaurant_names = {r.nom : r for r in restaurants}
    selected_name = st.selectbox("Sélectionnez un restaurant à nettoyer", list(restaurant_names.keys()))
    # Get selected restaurant object
    restau = restaurant_names[selected_name]
    if st.button("Nettoyer les avis", key="clean_reviews" , help="Nettoyer les avis du restaurant sélectionné"  ):  #, disabled=True
        pipe.clean_reviews(restau.id_restaurant)
        st.success("Les avis ont été nettoyés avec succès.")

def main():
    # Barre de navigation
    
    Navbar()
    
    st.title("Administration")
    st.write("Bienvenue sur la page d'administration de l'application SISE Ô Resto.")
    
    try_prep_analysis_on_restaurant()
    
    st.write("----")
    
    clean_reviews_pipeline()
    st.write("----")
    pipeline_processing()
    
    st.write("----")
 
    clear_reviews_one_restaurant()
    
    st.write("----")
    scrape_and_embed_tripadvisor()
    st.write("----")
    scrape_restaurant_informations()
    # Exécuter la requête SQL personnalisée
    execute_sql_query(session)
    st.write("----")

      # Option pour éditer une table
    st.header("Modifier une Table")
    if st.checkbox("Check to Edit"):
        edit_table(session)
    st.write("----")
    # Afficher les statistiques pour tous les restaurants
    display_restaurant_stats()
    
    st.write("----")

    
  

if __name__ == '__main__':
    main()