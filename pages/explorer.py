import streamlit as st
import pydeck as pdk
import concurrent.futures
import plotly.express as px
import pandas as pd
import os
from dotenv import find_dotenv, load_dotenv
from src.pipeline import Transistor , Pipeline
from pages.resources.components import Navbar, get_personal_address, display_stars, process_restaurant, add_to_comparator, filter_restaurants_by_radius, display_restaurant_infos, AugmentedRAG, instantiate_bdd, stream_text, get_datetime, construct_horaires, display_michelin_stars, tcl_api, get_price_symbol

# Configuration de la page
st.set_page_config(page_title="SISE Ô Resto - Explorer", page_icon="🍽️", layout="wide")

# Récupération de la clé API Mistral
try:
    load_dotenv(find_dotenv())
    API_KEY = os.getenv("MISTRAL_API_KEY")
except FileNotFoundError:
    API_KEY = st.secrets["MISTRAL_API_KEY"]

# Initialisation du transistor
transistor = Transistor()

# Récupération des informations des restaurants
session = transistor.session
restaurants = transistor.get_all_restaurants()
   
# Récupération de l'adresse personnelle
personal_address, personal_latitude, personal_longitude = get_personal_address()

# Fonction pour afficher le popup d'ajout de restaurant
@st.dialog("Ajouter un restaurant")
def add_restaurant_dialog():
    if not API_KEY:
        st.error("**Fonctionnalité indisponible :** Vous n'avez pas rajouté votre clé API Mistral dans les fichiers de l'application. Veuillez ajouter le fichier `.env` à la racine du projet puis redémarrer l'application.", icon="⚠️")
        if st.button(label="Fermer"):
            st.rerun()
    else:
        # Filtrage sur les restaurants non scrappés
        pipe = Pipeline()
        restaurants = pipe.get_restaurants_non_scrapped()
        restaurant_names = {r.nom : r for r in restaurants}
        # Sélection du restaurant à ajouter
        selected_name = st.selectbox("Sélectionnez un restaurant", list(restaurant_names.keys()), placeholder="Sélectionnez un restaurant", key="restaurant_select")
    
        # Scapping du restaurant sélectionné
        if st.button(icon="➕", label="Ajouter le restaurant"):
            restau = restaurant_names[selected_name]
            st.info("L'obtention des informations du restaurant est en cours. Vous pouvez fermer cette fenêtre si vous le souhaitez, le processus se poursuivra en arrière-plan. Une notification vous sera envoyée dans le terminal une fois le restaurant ajouté, vous devrez alors rafraichir la page.", icon="ℹ️")
            pipe.add_new_restaurant(restau)

# Fonction pour afficher le popup d'informations sur un restaurant
@st.dialog("ℹ️ Informations sur le restaurant", width="large")
def restaurant_info_dialog():
    display_restaurant_infos( personal_address, personal_latitude, personal_longitude)

# Fonction pour afficher le popup de création de graphique
@st.dialog("Créer un graphique")
def create_chart_dialog(df):
    # Vérification du nombre de graphiques créés
    if len(st.session_state.charts) < 5:
        st.info("Cette fonctionnalité est expérimentale et peut ne pas fonctionner correctement", icon="ℹ️")

        # Choix du type de graphique
        chart_type = st.selectbox(
            "Type de graphique",
            ["Barres", "Barres empilées", "Histogramme", "Histogramme empilé", "Circulaire", "Nuage de points", "Carte proportionnelle"],
            key="chart_type"
        )
        
        # Sélection des colonnes en fonction du type de graphique
        if chart_type in ["Barres", "Barres empilées"]:
            x_col = st.selectbox("Sélectionnez le champ de l'axe X", options=df.columns, key="x_axis")
            y_col = st.selectbox("Sélectionnez le champ de l'axe Y", options=df.columns, key="y_axis")
            if chart_type in ["Barres empilées"]:
                stack_col = st.selectbox("Sélectionnez le champ pour empiler", options=df.columns, key="stack_axis")
        elif chart_type in ["Nuage de points"]:
            x_col = st.selectbox("Sélectionnez le champ de l'axe X", options=df.columns, key="x_axis")
            y_col = st.selectbox("Sélectionnez le champ de l'axe Y", options=df.columns, key="y_axis")
            size_col = st.selectbox("Sélectionnez le champ pour la taille des bulles", options=df.columns, key="size_axis")
        elif chart_type in ["Histogramme", "Histogramme empilé"]:
            x_col = st.selectbox("Sélectionnez le champ", options=df.columns, key="hist_axis")
            if chart_type == "Histogramme empilé":
                stack_col = st.selectbox("Sélectionnez le champ pour empiler", options=df.columns, key="stack_hist_axis")
            y_col = None
        elif chart_type == "Circulaire":
            names_col = st.selectbox("Sélectionnez le champ des labels", options=df.columns, key="pie_names")
            values_col = st.selectbox("Sélectionnez le champ des valeurs", options=df.columns, key="pie_values")
        
        if st.button(icon="📊", label="Créer le graphique"):
            # Génération automatique du nom du graphique
            chart_name = f"Graphique {chart_type}"
            
            # Stockage des paramètres du graphique
            chart_params = {
                "type": chart_type,
                "name": chart_name,
                "x": x_col if 'x_col' in locals() else None,
                "y": y_col if 'y_col' in locals() else None,
                "size": size_col if 'size_col' in locals() else None,
                "stack": stack_col if 'stack_col' in locals() else None,
                "names": names_col if 'names_col' in locals() else None,
                "values": values_col if 'values_col' in locals() else None
            }
            
            st.session_state.charts.append(chart_params)
            st.toast("Graphique créé avec succès", icon="📊")
            st.rerun()
    else:
        st.warning("Vous avez déjà créé 5 graphiques, veuillez en supprimer un pour en créer un nouveau", icon="⚠️")

        if st.button("Fermer"):
            st.rerun()

def main():
    # Barre de navigation
    Navbar()

    # Vérification si une adresse personelle a été renseignée
    if not personal_address:
        if 'address_toast_shown' not in st.session_state:
            st.toast("Veuillez définir votre adresse personnelle pour voir les temps de trajet", icon="ℹ️")
            st.session_state['address_toast_shown'] = True

    # Initialisation du comparateur dans session_state
    if 'comparator' not in st.session_state:
        st.session_state['comparator'] = []

    # Initialisation de la liste des graphiques
    if "charts" not in st.session_state:
        st.session_state.charts = []

    # Titre de la page
    st.title('🔍 Explorer')

    # Mise en page du bouton d'ajout de restaurant
    _add_restaurant_btn_col1, add_restaurant_btn_col2 = st.columns([3, 1])

    # Bouton pour ajouter un restaurant
    with add_restaurant_btn_col2:
        if st.button(icon="➕", label="Ajouter un restaurant", key="add_restaurant_btn"):
            add_restaurant_dialog()

    # Création d'une tab
    close_tab, filter_tab, ai_tab = st.tabs(["🔼", "🎨 Filtres", "✨ Discuter avec l'IA"])

    with close_tab:
        st.write("")
    
    with filter_tab:
        # Conteneur pour la recherche et les filtres
        header_container = filter_tab.container(border=True)

        # Mise en page de la recherche et des filtres
        header_col1, header_col2 = header_container.columns(2)
        
        # Colonne pour les filtres
        with header_col1:
            # Récupération des informations des restaurants scrappés
            scrapped_restaurants = [
                {
                    "nom": restaurant.nom,
                    "latitude": restaurant.latitude,
                    "longitude": restaurant.longitude,
                    "rank": restaurant.rank,
                    "prix_min": restaurant.prix_min,
                    "prix_max": restaurant.prix_max,
                    "etoiles_michelin": restaurant.etoiles_michelin,
                    "note_globale": restaurant.note_globale,
                    "qualite_prix_note": restaurant.qualite_prix_note,
                    "cuisine_note": restaurant.cuisine_note,
                    "service_note": restaurant.service_note,
                    "ambiance_note": restaurant.ambiance_note,
                    "cuisines": restaurant.cuisines,
                    "repas": restaurant.repas,
                    "fonctionnalite": restaurant.fonctionnalite,
                }
                for restaurant in [restaurant for restaurant in restaurants if restaurant.scrapped]
            ]

            # Checkbox pour activer/désactiver le filtre par rayon
            container = header_col1.container(border=True)
            if personal_address:
                use_radius_filter = container.toggle(label="Recherche par distance autour du domicile", value=False, key="use_radius_filter")
                if use_radius_filter:
                    radius = container.slider("Distance de recherche autour du domicile (en mètres)", min_value=1, max_value=3000, step=1, value=500, key="radius_slider")
                
                    # Filtrage des restaurants par rayon si activé
                    filtered_restaurants = filter_restaurants_by_radius(scrapped_restaurants, personal_latitude, personal_longitude, radius)
                else:
                    radius = 1000000
                    filtered_restaurants = scrapped_restaurants
            else:
                use_radius_filter = container.toggle(label="Recherche par distance autour du domicile", value=False, key="use_radius_filter", disabled=True)
                radius = 1000000
                filtered_restaurants = scrapped_restaurants

            # Filtre par rang
            container = header_col1.container(border=True)
            rank_max = 3500
            rank = container.slider(
                    label="Rang maximal",
                    min_value=1,
                    max_value=rank_max,
                    step=1,
                    value=3500,
                    key="filter_rank"
                )
            
            grades_col1, grades_col2 = st.columns(2)

            # Filtre par ouverture actuelle
            container = grades_col1.container(border=True)
            only_open_now = container.toggle(
                label="Afficher seulement les restaurants ouverts maintenant",
                value=False,
                key="only_open_now"
            )

            # Filtre par prix
            container = grades_col2.container(border=True)
            option_map = {
                1: ":material/euro_symbol:",
                2: ":material/euro_symbol::material/euro_symbol:",
                3: ":material/euro_symbol::material/euro_symbol::material/euro_symbol:",
                4: ":material/euro_symbol::material/euro_symbol::material/euro_symbol::material/euro_symbol:",
            }
            selected_price = container.pills(
                "Prix",
                options=option_map.keys(),
                format_func=lambda option: option_map[option],
                selection_mode="multi",
                key="filter_price"
            )

            # Filtre par étoiles Michelin
            container = grades_col1.container(border=True)
            option_michelin = {
                1: ":material/asterisk:",
                2: ":material/asterisk::material/asterisk:",
                3: ":material/asterisk::material/asterisk::material/asterisk:",
            }
            selected_michelin_stars = container.pills(
                "Étoiles Michelin",
                options=option_michelin.keys(),
                format_func=lambda option: option_michelin[option],
                selection_mode="multi",
                key="filter_michelin_stars"
            )

            # Filtre par note globale
            container = grades_col2.container(border=True)
            container.write("Note globale minimale")
            global_rating = [1, 2, 3, 4, 5]
            global_rating_selected = container.feedback("stars", key="filter_global_stars")
            if global_rating_selected is None:
                global_rating_selected = 0

            # Filtre par note qualité-prix
            container = grades_col1.container(border=True)
            quality_price = container.slider(
                label="Note qualité prix minimale",
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                value=0.0,
                key="filter_quality_price"
            )

            # Filtre par temps de trajet
            if personal_address:
                container = st.container(border=True)
                time_travel = container.slider(
                    label="Temps de trajet maximal (en minutes)",
                    min_value=0,
                    max_value=120,
                    step=1,
                    value=120,
                    key="filter_time_travel"
                )
            else:
                container = st.container(border=True)
                time_travel = container.slider(
                    label="Temps de trajet maximal (en minutes)",
                    min_value=0,
                    max_value=120,
                    step=1,
                    value=120,
                    disabled=True,
                    key="filter_time_travel"
                )
        
        with header_col2:

            # Filtre par note cuisine
            container = grades_col2.container(border=True)
            cuisine_note = container.slider(
                label="Note cuisine minimale",
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                value=0.0,
                key="filter_cuisine_note"
            )

            # Filtre par note service
            container = grades_col1.container(border=True)
            service_note = container.slider(
                label="Note service minimale",
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                value=0.0,
                key="filter_service_note"
            )

            # Filtre par note ambiance
            container = grades_col2.container(border=True)
            ambiance_note = container.slider(
                label="Note ambiance minimale",
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                value=0.0,
                key="filter_ambiance_note"
            )

            # Filtre par cuisine
            container = st.container(border=True)
            cuisines = sorted(list(set([c.strip() for restaurant in scrapped_restaurants for c in (restaurant["cuisines"] or "").split(',') if c.strip()])))
            selected_cuisines = container.pills(
                label="Cuisine",
                options=cuisines,
                default=[],
                selection_mode = "multi",
                key="filter_cuisines"
            )

            # Filtre par type de repas
            container = st.container(border=True)
            meals = sorted(list(set([m.strip() for restaurant in scrapped_restaurants for m in (restaurant["repas"] or "").split(',') if m.strip()])))
            selected_meals = container.pills(
                label="Type de repas",
                options=meals,
                default=[],
                selection_mode = "multi",
                key="filter_meals"
            )

            # Filtres par fonctionnalités
            container = st.container(border=True)
            functionalities = sorted(list(set([f.strip() for restaurant in scrapped_restaurants for f in (restaurant["fonctionnalite"] or "").split(';') if f.strip()])))
            selected_functionalities = container.pills(
                label="Fonctionnalités",
                options=functionalities,
                default=[],
                selection_mode = "multi",
                key="filter_functionalities"
            )

    # Tab pour le chat avec l'IA
    with ai_tab:
        # Mise en page du chat avec l'IA
        header_container = st.container(border=True)
        chat_container = header_container.container(height=500)

        # Sécurité si la clé API Mistral n'est pas présente
        if not API_KEY:
            header_container.error("**Fonctionnalité indisponible :** Vous n'avez pas rajouté votre clé API Mistral dans les fichiers de l'application. Veuillez ajouter le fichier `.env` à la racine du projet puis redémarrer l'application.", icon="⚠️")
            st.session_state['found_mistral_api'] = False
        else:
            st.session_state['found_mistral_api'] = True

        # Vérification si l'historique de la conversation est initialisé
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Initialisation du modèle d'IA
        role_prompt="""
        Vous êtes un assistant intelligent spécialisé dans la recommandation de restaurants Lyonnais. Utilisez uniquement les données disponibles sur le site pour fournir des recommandations précises et pertinentes. Votre rôle est d'aider les utilisateurs à trouver des établissements répondant à leurs préférences et besoins spécifiques.

        Fonctionnalités principales :
        1. **Compréhension des Préférences Utilisateur** : Analysez les préférences exprimées par l'utilisateur concernant le type de cuisine, le budget, l'emplacement, les options végétariennes/vegan, et d'autres critères pertinents.
        2. **Recommandations Personnalisées** : Proposez des listes de restaurants adaptés aux critères de l'utilisateur, en fournissant des informations telles que le nom, l'adresse, le type de cuisine, les avis clients, les prix et les heures d'ouverture basées sur les données disponibles.
        3. **Gestion des Contraintes** : Tenez compte des contraintes comme les restrictions alimentaires, la distance maximale, les méthodes de réservation disponibles et les exigences spécifiques (par exemple, accès handicapés).
        4. **Mises à Jour en Temps Réel** : Fournissez des informations actualisées sur la disponibilité des tables, les événements spéciaux, et les changements de menu en fonction des données du site.
        5. **Interaction Naturelle** : Communiquez de manière claire et concise, en posant des questions supplémentaires si nécessaire pour affiner les recommandations.
        6. **Respect de la Confidentialité** : Assurez-vous que toutes les interactions respectent la vie privée des utilisateurs et que les données sensibles ne sont pas divulguées.
        7. **Recherche Flexible** : Si l'utilisateur fournit une partie du nom d'un restaurant, essayez de trouver le restaurant le plus pertinent dans la base de données qui correspond à cette partie du nom.

        Objectif :
        Aider les utilisateurs à découvrir et à choisir des restaurants qui correspondent parfaitement à leurs attentes, en offrant une expérience utilisateur fluide et personnalisée basée sur les informations disponibles sur le site.

        Consignes supplémentaires :
        - Soyez courtois et professionnel dans vos réponses.
        - Fournissez des informations vérifiées et évitez les recommandations basées sur des données obsolètes.
        - Adaptez votre ton en fonction des préférences exprimées par l'utilisateur.
        - Si un des champs de restaurant est vide, None, etc... dans la base de données, indiquez que l'information n'est pas disponible et proposez de vérifier sur internet si nécessaire, en précisant la source des informations.
        """

        # Affichage de l'histoire de la conversation
        for message in st.session_state.messages:
            if message["role"] == "User":
                with chat_container.chat_message(message["role"], avatar="👤"):
                    st.write(message["content"])

            elif message["role"] == "assistant":
                with chat_container.chat_message(message["role"], avatar="✨"):
                    st.markdown(message["content"])
                    metrics = message["metrics"]
                    st.markdown(
                        f"📶 *Latence : {metrics['latency']:.2f} secondes* | "
                        f"💲 *Coût : {metrics['euro_cost']:.6f} €* | "
                        f"⚡ *Utilisation énergétique : {metrics['energy_usage']} kWh* | "
                        f"🌡️ *Potentiel de réchauffement global : {metrics['gwp']} kgCO2eq*"
                    )

        # Text input pour le chat avec l'IA
        if message := header_container.chat_input(placeholder="Écrivez votre message", key="search_restaurant_temp", disabled=not st.session_state.get('found_mistral_api', False)):
            if message.strip():

                # Affichage du message de l'utilisateur
                with chat_container.chat_message("user", avatar="👤"):
                    st.write(message)

                # Ajout du message de l'utilisateur à l'historique de la conversation
                st.session_state.messages.append({"role": "User", "content": message})

                with header_container:
                    # Initialisation des connaissances de l'IA si nécessaire
                    if 'bdd_chunks' not in st.session_state:
                        with st.spinner("Démarrage de l'IA..."):
                            st.session_state['bdd_chunks'] = instantiate_bdd()

                    if 'llm' not in st.session_state:
                        st.session_state['llm'] = AugmentedRAG(
                            role_prompt=role_prompt,
                            generation_model="mistral-large-latest",
                            bdd_chunks=st.session_state['bdd_chunks'],
                            top_n=3,
                            max_tokens=3000,
                            temperature=0.3,
                        )

                    llm = st.session_state['llm']

                # Récupération de la réponse de l'IA
                response = llm(
                    query=message,
                    history=st.session_state.messages,
                )

                # Affichage de la réponse de l'IA
                with chat_container.chat_message("AI", avatar="✨"):
                    st.write_stream(stream_text(response["response"]))
                    st.markdown(
                        f"📶 *Latence : {response['latency']:.2f} secondes* | "
                        f"💲 *Coût : {response['euro_cost']:.6f} €* | "
                        f"⚡ *Utilisation énergétique : {response['energy_usage']} kWh* | "
                        f"🌡️ *Potentiel de réchauffement global : {response['gwp']} kgCO2eq*"
                    )

                # Ajout de la réponse de l'IA à l'historique de la conversation
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["response"],
                    "metrics": {
                        "latency": response["latency"],
                        "euro_cost": response["euro_cost"],
                        "energy_usage": response["energy_usage"],
                        "gwp": response["gwp"]
                    }
                })

    # Tab pour l'affichage de la page Explorer ou Comparer
    restaurants_tab, comparer_tab, visualisation_tab = st.tabs(["🍽️ Restaurants", "🆚 Comparer", "📊 Visualiser"])

    with restaurants_tab:

        # Mise en page des résultats
        results_display_col1, results_display_col2 = st.columns([3, 2])
        
        # Affichage des résultats
        with results_display_col1:
            
            # Parallélisation du traitement des restaurants
            with st.spinner("Chargement des restaurants..."):
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    futures = {executor.submit(process_restaurant, personal_address, personal_latitude, personal_longitude, restaurant): restaurant for restaurant in restaurants if restaurant.scrapped}
                    results = sorted([future.result() for future in concurrent.futures.as_completed(futures)], key=lambda x: x[0].nom)

            # Filtrage des résultats en fonction des filtres
            filtered_results = []
            for result in results:
                restaurant, tcl_url, fastest_mode = result

                # Filtrage par rang
                if hasattr(restaurant, 'rank') and restaurant.rank is not None:
                    if restaurant.rank > rank:
                        continue
                else:
                    if rank != rank_max:
                        continue

                # Filtrage par ouverture actuelle
                if only_open_now:
                    current_datetime, current_day = get_datetime()
                    horaires_dict = construct_horaires(restaurant.horaires)
                    current_time = current_datetime.time()
                    if not (horaires_dict.get(current_day) and any(
                        start_time <= current_time <= end_time
                        for start_time, end_time in horaires_dict[current_day]
                    )):
                        continue

                # Filtrage par prix
                if selected_price:
                    if restaurant.prix_min and restaurant.prix_max:
                        prix_avg = (restaurant.prix_min + restaurant.prix_max) / 2

                        if not (
                            (1 in selected_price and prix_avg < 20) or
                            (2 in selected_price and 20 <= prix_avg < 30) or
                            (3 in selected_price and 30 <= prix_avg < 50) or
                            (4 in selected_price and 50 <= prix_avg)
                        ):
                            continue
                    else:
                        continue

                # Filtrage par étoiles Michelin
                if selected_michelin_stars:
                    if restaurant.etoiles_michelin not in selected_michelin_stars:
                        continue
                
                # Filtrage par note globale
                if restaurant.note_globale:
                    if (global_rating[global_rating_selected] > restaurant.note_globale):
                        continue
                
                # Filtrage par note qualité-prix
                if quality_price > 0:
                    if restaurant.qualite_prix_note is None or restaurant.qualite_prix_note < quality_price:
                        continue

                # Filtrage par note cuisine
                if cuisine_note > 0:
                    if restaurant.cuisine_note is None or restaurant.cuisine_note < cuisine_note:
                        continue

                # Filtrage par note service
                if service_note > 0:
                    if restaurant.service_note is None or restaurant.service_note < service_note:
                        continue

                # Filtrage par note ambiance
                if ambiance_note > 0:
                    if restaurant.ambiance_note is None or restaurant.ambiance_note < ambiance_note:
                        continue
                
                # Filtrage par temps de trajet
                if tcl_url:
                    duration_str = fastest_mode[1]
                    if 'h' in duration_str:
                        parts = duration_str.split('h')
                        hours = int(parts[0])
                        minutes = int(parts[1].replace('min', '')) if parts[1] else 0
                        duration = hours * 60 + minutes
                    else:
                        duration = int(duration_str.replace('min', ''))
                    if not (duration <= time_travel):
                        continue
                
                # Filtrage par cuisine
                if selected_cuisines:
                    if restaurant.cuisines:
                        restaurant_cuisines = [c.strip() for c in restaurant.cuisines.split(',')]
                    else:
                        restaurant_cuisines = []
                    if not all(cuisine in restaurant_cuisines for cuisine in selected_cuisines):
                        continue
                
                # Filtrage par type de repas
                if selected_meals:
                    if restaurant.repas:
                        restaurant_meals = [m.strip() for m in restaurant.repas.split(',')]
                    else:
                        restaurant_meals = []
                    if not all(meal in restaurant_meals for meal in selected_meals):
                        continue

                # Filtrage par fonctionnalités
                if selected_functionalities:
                    if restaurant.fonctionnalite:
                        restaurant_functionalities = [f.strip() for f in restaurant.fonctionnalite.split(';')]
                    else:
                        restaurant_functionalities = []
                    if not all(functionality in restaurant_functionalities for functionality in selected_functionalities):
                        continue
                
                # Application des filtres
                filtered_results.append(result)

            # Extraction des restaurants filtrés pour la carte
            filtered_restaurants = [
                (
                    result[0].nom,
                    result[0].latitude,
                    result[0].longitude
                )
                for result in filtered_results
                if result[0] is not None
            ]

            # Récupération des coordonnées des restaurants pour la carte
            map_data = []
            for restaurant in filtered_restaurants:
                nom, lat, lon = restaurant
                map_data.append({
                    'name': nom,
                    'latitude': lat,
                    'longitude': lon
                })

            # Filtrage des restaurants par rayon
            if personal_address:
                map_data = [
                    restaurant for restaurant in map_data
                    if restaurant.get('latitude') is not None and restaurant.get('longitude') is not None
                ]
                map_data = filter_restaurants_by_radius(
                    map_data,
                    personal_latitude,
                    personal_longitude,
                    radius
                )
                # Obtention des noms des restaurants filtrés
                filtered_names = [restaurant['name'] for restaurant in map_data]
                # Filtrage des résultats en fonction des noms filtrés
                filtered_results = [result for result in filtered_results if result[0].nom in filtered_names]

            # Affichage du nombre de restaurants trouvés
            if not filtered_results:
                st.info("Aucun restaurant trouvé, essayez de modifier vos critères de recherche", icon="ℹ️")
            elif (filtered_results and len(filtered_results) == 1):
                st.info("1 restaurant trouvé", icon="ℹ️")
            else:
                st.info(f"{len(filtered_results)} restaurants trouvés", icon="ℹ️")
            
            container = st.container(height=1000, border=False)

            with container:

                # Récupération du temps actuel
                current_datetime, current_day = get_datetime()

                # Affichage uniquement des restaurants filtrés
                for result in filtered_results:
                    restaurant, tcl_url, fastest_mode = result
                    container = st.container(border=True)
                    col1, col2, col3, col4, col5 = container.columns([3.5, 1.7, 1, 1, 2.5])
                    
                    # Affichage des informations du restaurant
                    with col1:
                        col1.write(restaurant.nom)
                        stars = display_stars(restaurant.note_globale)
                        col1.image(stars, width=20)

                    # Affichage du statut du restaurant
                    with col2:
                        current_datetime, current_day = get_datetime()
                        horaires_dict = construct_horaires(restaurant.horaires)
                        
                        if not restaurant.horaires:
                            col2.info("Indisponible")
                        else:
                            horaires_dict = construct_horaires(restaurant.horaires)
                            plages_du_jour = horaires_dict.get(current_day, [])
                            if not plages_du_jour:
                                col2.error("Fermé")
                            else:
                                ouvert = False
                                current_time = current_datetime.time()
                                for start, end in plages_du_jour:
                                    if start <= end:
                                        if start <= current_time <= end:
                                            ouvert = True
                                            break
                                    else:
                                        if current_time >= start or current_time <= end:
                                            ouvert = True
                                            break
                                if ouvert:
                                    col2.success("Ouvert")
                                else:
                                    col2.error("Fermé")

                    # Affichage du bouton d'information
                    with col3:
                        if col3.button(label="ℹ️", key=f"info_btn_{restaurant.id_restaurant}"):
                            st.session_state['selected_restaurant'] = restaurant
                            restaurant_info_dialog()

                    # Affichage du bouton de comparaison
                    with col4:
                        if col4.button("🆚", key=f"compare_btn_{restaurant.id_restaurant}"):
                            add_to_comparator(restaurant)
                    
                    # Affichage du bouton de trajet
                    with col5:
                        emoji, fastest_duration = fastest_mode
                        bouton_label = f"{emoji} {fastest_duration}"
                        button_key = f"trajet_btn_{restaurant.id_restaurant}"
                        if tcl_url:
                            col5.markdown(f'''
                                <style>
                                    .custom-button {{
                                        display: block;
                                        padding: 6px 12px;
                                        margin-bottom: 15px;
                                        color: #31333e;
                                        border: 1px solid #d6d6d8;
                                        border-radius: 8px;
                                        cursor: pointer;
                                        background-color: transparent;
                                        transition: background-color 0.3s;
                                    }}
                                    .custom-button:hover {{
                                        color: #FF4B4B;
                                        border-color: #FF4B4B;
                                    }}
                                    .custom-button:active {{
                                        background-color: #FF4B4B;
                                    }}
                                    @media (prefers-color-scheme: dark) {{
                                        .custom-button {{
                                            color: #fafafa;
                                            border-color: #3e4044;
                                            background-color: #14171f;
                                        }}
                                    }}
                                </style>
                                <a href="{tcl_url}" target="_blank" style="text-decoration: none;">
                                    <button class="custom-button">{bouton_label}</button>
                                </a>
                            ''', unsafe_allow_html=True)
                        else:
                            col5.button(bouton_label, key=button_key, disabled=True)
        
        # Affichage de la carte
        with results_display_col2:
            with st.spinner("Chargement de la carte..."):
                # Mise en forme du radius et de la couleur du domicile
                if (radius == 1000000):
                    radius = 25
                    color = '[0, 0, 255]'
                else:
                    color = '[0, 0, 255, 100]'

                # Ajout des coordonnées du domicile s'il est défini
                if personal_address:
                    latitude = personal_latitude
                    longitude = personal_longitude
                    map_data.append({
                        'name': 'Domicile',
                        'latitude': personal_latitude,
                        'longitude': personal_longitude
                    })
                else:
                    latitude, longitude = 45.7640, 4.8357 # Coordonnées de Lyon

                view_state = pdk.ViewState(
                    latitude=latitude,
                    longitude=longitude,
                    zoom=12,
                    pitch=0
                )

                # Paramètres du point du domicile (bleu)
                home_layer = pdk.Layer(
                    'ScatterplotLayer',
                    data=[point for point in map_data if point['name'] == 'Domicile'],
                    get_position='[longitude, latitude]',
                    get_color=color,
                    get_radius=radius,
                    pickable=True,
                    auto_highlight=True
                )

                # Paramètres des points des restaurants (rouge)
                restaurants_layer = pdk.Layer(
                    'ScatterplotLayer',
                    data=[point for point in map_data if point['name'] != 'Domicile'],
                    get_position='[longitude, latitude]',
                    get_color='[255, 0, 0]',
                    get_radius=25,
                    pickable=True,
                    auto_highlight=True
                )

                # Ajout des points à afficher sur la carte
                layers = [restaurants_layer, home_layer]

                # Paramètres des infos-bulles
                tooltip = {
                    "html": "<b>{name}</b>",
                    "style": {
                        "backgroundColor": "white",
                        "color": "black"
                    }
                }

                # Affichage de la carte
                deck = pdk.Deck(
                    layers=layers,
                    initial_view_state=view_state,
                    tooltip=tooltip,
                    map_style='mapbox://styles/mapbox/light-v11'
                )

                # Affichage de la carte
                st.pydeck_chart(deck)

    with comparer_tab:

        # Initialisation du comparateur dans session_state
        if 'comparator' not in st.session_state:
            st.session_state['comparator'] = []

        # Vérification du nombre de restaurants sélectionnés
        comparator_empty = len(st.session_state['comparator']) == 0
        
        # Mise en page du bouton pour réinitialiser le comparateur
        _reinit_cmp_btn_col1, reinit_cmp_btn_col2 = st.columns([2, 1])
        
        # Bouton pour réinitialiser le comparateur
        if reinit_cmp_btn_col2.button("♻️ Réinitialiser le comparateur", disabled=comparator_empty):
            st.session_state['comparator'] = []
            st.rerun()

        # Récupération des restaurants sélectionnés
        selected_restaurants = [restaurant for restaurant in restaurants if restaurant.id_restaurant in st.session_state['comparator'][:3]]

        # Mise en page des colonnes pour afficher les restaurants comparés
        cols = st.columns(3, border=True)

        # Affichage des restaurants comparés
        for idx in range(3):
            with cols[idx]:
                if idx < len(selected_restaurants):
                    restaurant = selected_restaurants[idx]
                
                    # Récupération des informations de trajet
                    tcl_url, duration_public, duration_car, duration_soft, fastest_mode = tcl_api(personal_address, personal_latitude, personal_longitude, restaurant.latitude, restaurant.longitude)

                    # Mise en page des boutons
                    btn_col1, btn_col2 = st.columns(2)

                    with btn_col1:
                        # Bouton pour afficher les informations détaillées
                        if btn_col1.button("ℹ️", key=f"info_cmp_{restaurant.id_restaurant}"):
                            st.session_state['selected_restaurant'] = restaurant
                            restaurant_info_dialog()

                    with btn_col2:
                        # Bouton pour supprimer du comparateur
                        if btn_col2.button("🗑️ Supprimer", key=f"remove_cmp_{restaurant.id_restaurant}"):
                            st.session_state['comparator'].remove(restaurant.id_restaurant)
                            st.rerun()

                    # Affichage du nom du restaurant
                    st.header(restaurant.nom)

                    # Affichage des horaires d'ouverture
                    current_datetime, current_day = get_datetime()
                    horaires_dict = construct_horaires(restaurant.horaires)
                    
                    if not restaurant.horaires:
                        st.info("Indisponible")
                    else:
                        plages_du_jour = horaires_dict.get(current_day, [])
                        if not plages_du_jour:
                            st.error("Fermé")
                        else:
                            ouvert = False
                            current_time = current_datetime.time()
                            for start, end in plages_du_jour:
                                if start <= end:
                                    if start <= current_time <= end:
                                        ouvert = True
                                        break
                                else:
                                    if current_time >= start or current_time <= end:
                                        ouvert = True
                                        break
                            if ouvert:
                                st.success("Ouvert")
                            else:
                                st.error("Fermé")

                    # Affichage du rang
                    rank_container = st.container(border=True)
                    if restaurant.rank:
                        if restaurant.rank == 1:
                            rank_container.markdown(f"**Rang :** {restaurant.rank}<sup>er</sup> restaurant", unsafe_allow_html=True)
                        else:
                            rank_container.markdown(f"**Rang :** {restaurant.rank}<sup>ème</sup> restaurant", unsafe_allow_html=True)
                    else:
                        rank_container.write("**Rang :** Indisponible")

                    # Affichage du prix
                    prix_container = st.container(border=True)
                    if restaurant.prix_min and restaurant.prix_max:
                        prix_symbol = get_price_symbol(restaurant.prix_min, restaurant.prix_max)
                        prix_container.write(f"**Prix :** {prix_symbol}")
                    else:
                        prix_container.write("**Prix :** Indisponible")

                    # Affichage des notations
                    mark_container = st.container(border=True)
                    mark_container.write("**Notations**")
                    if restaurant.etoiles_michelin:
                        michelin_stars = display_michelin_stars(restaurant.etoiles_michelin)
                        michelin_stars_html = ' Aucune'
                        if michelin_stars:
                            if restaurant.etoiles_michelin == 1:
                                michelin_stars_html = f'<img src="{michelin_stars}" width="25">'
                            elif restaurant.etoiles_michelin == 2:
                                michelin_stars_html = f'<img src="{michelin_stars}" width="45">'
                            elif restaurant.etoiles_michelin == 3:
                                michelin_stars_html = f'<img src="{michelin_stars}" width="65">'
                    else:
                        michelin_stars_html = ' Indisponible'
                    mark_container.html(f"<b>Étoiles Michelin :</b>{michelin_stars_html}")
                    if restaurant.note_globale:
                        stars = display_stars(restaurant.note_globale)
                        stars_html = ''.join([f'<img src="{star}" width="20">' for star in stars])
                    else:
                        stars_html = 'Indisponible'
                    mark_container.html(f"<b> Globale : </b>{stars_html}")
                    if restaurant.qualite_prix_note:
                        mark_container.write(f"**Qualité Prix :** {restaurant.qualite_prix_note}")
                    else:
                        mark_container.write(f"**Qualité Prix :** Indisponible")
                    if restaurant.cuisine_note:
                        mark_container.write(f"**Cuisine :** {restaurant.cuisine_note}")
                    else:
                        mark_container.write(f"**Cuisine :** Indisponible")
                    if restaurant.service_note:
                        mark_container.write(f"**Service :** {restaurant.service_note}")
                    else:
                        mark_container.write(f"**Service :** Indisponible")
                    if restaurant.ambiance_note:
                        mark_container.write(f"**Ambiance :** {restaurant.ambiance_note}")
                    else:
                        mark_container.write(f"**Ambiance :** Indisponible")

                    # Affichage des informations complémentaires
                    info_supp_container = st.container(border=True)
                    info_supp_container.write("**Informations complémentaires**")
                    if restaurant.cuisines:
                        info_supp_container.write(f"**Cuisine :** {restaurant.cuisines}")
                    else:
                        info_supp_container.write("**Cuisine :** Indisponible")
                    if restaurant.repas:
                        info_supp_container.write(f"**Repas :** {restaurant.repas}")
                    else:
                        info_supp_container.write("**Repas :** Indisponible")
                    if restaurant.fonctionnalite:
                        functionalities = restaurant.fonctionnalite.replace(';', ', ').rstrip(', ')
                        info_supp_container.write(f"**Fonctionnalités :** {functionalities}")
                    else:
                        info_supp_container.write("**Fonctionnalités :** Indisponible")

                    # Affichage des temps de trajet
                    trajet_container = st.container(border=True)
                    trajet_container.write("**Temps de trajet**")
                    trajet_container.write(f"🚲 {duration_soft}")
                    trajet_container.write(f"🚌 {duration_public}")
                    trajet_container.write(f"🚗 {duration_car}")
                else:
                    # Message si aucun restaurant n'est sélectionné
                    st.info("Sélectionnez un restaurant depuis l'onglet 🍽️ Restaurants en cliquant sur le bouton 🆚, afin de l'ajouter au comparateur.", icon="ℹ️")

    # Tab pour la visualisation des données
    with visualisation_tab:
        # Affichage des graphiques
        if filtered_results:

            # Extraction des données filtrées
            filtered_data = [
                {
                    "nom": restaurant.nom,
                    "rank": restaurant.rank,
                    "prix_min": restaurant.prix_min,
                    "prix_max": restaurant.prix_max,
                    "etoiles_michelin": restaurant.etoiles_michelin,
                    "note_globale": restaurant.note_globale,
                    "qualite_prix_note": restaurant.qualite_prix_note,
                    "cuisine_note": restaurant.cuisine_note,
                    "service_note": restaurant.service_note,
                    "ambiance_note": restaurant.ambiance_note,
                    "cuisines": restaurant.cuisines,
                    "repas": restaurant.repas,
                    "fonctionnalite": restaurant.fonctionnalite,
                }
                for restaurant, _, _ in filtered_results
            ]

            # Création d'un DataFrame global à partir des données filtrées
            df_filtered = pd.DataFrame(filtered_data)

            # Calcul du prix moyen
            df_filtered['prix_moyen'] = (df_filtered['prix_min'] + df_filtered['prix_max']) / 2

            # Suppression des colonnes avec un nom vide
            df_filtered = df_filtered.loc[:, df_filtered.columns != ' ']

            # Renommage des colonnes
            df_filtered.rename(columns={
                "nom": "Nom [STRING]",
                "rank": "Rang [INT]",
                "prix_min": "Prix minimum [FLOAT]",
                "prix_max": "Prix maximum [FLOAT]",
                "prix_moyen": "Prix moyen [FLOAT]",
                "etoiles_michelin": "Étoiles Michelin [INT]",
                "note_globale": "Note globale [FLOAT]",
                "qualite_prix_note": "Note qualité prix [FLOAT]",
                "cuisine_note": "Note cuisine [FLOAT]",
                "service_note": "Note service [FLOAT]",
                "ambiance_note": "Note ambiance [FLOAT]",
                "cuisines": "Cuisines [STRING : COUNT]",
                "repas": "Repas [STRING : COUNT]",
                "fonctionnalite": "Fonctionnalités [STRING : COUNT]",
            }, inplace=True)

            # Mise en page du bouton de création de graphique
            _create_chart_btn_col1, create_chart_btn_col2, delete_all_btn_col3 = st.columns([2, 1, 1.5])

            # Affichage du bouton pour créer un graphique
            if create_chart_btn_col2.button(icon="📊", label="Créer un graphique", key="create_chart_btn"):
                create_chart_dialog(df_filtered)

            # Affichage du bouton pour supprimer tous les graphiques
            if delete_all_btn_col3.button(icon="🗑️", label="Supprimer tous les graphiques", key="delete_all_charts_btn", disabled=len(st.session_state.charts) == 0):
                st.session_state.charts = []
                st.rerun()

            # Affichage des graphiques
            if st.session_state.charts:
                for idx, chart in enumerate(st.session_state.charts):
                    with st.container(border=True):
                        _chart_col1, chart_col2 = st.columns([3, 1])
                        with chart_col2:
                            if st.button("🗑️ Supprimer", key=f"delete_chart_{idx}"):
                                st.session_state.charts.pop(idx)
                                st.rerun()
                        
                        # Transformation des colonnes textuelles séparées par virgule ou point-virgule
                        text_columns = ["Cuisines [STRING : COUNT]", "Repas [STRING : COUNT]", "Fonctionnalités [STRING : COUNT]"]
                        x_data = chart["x"]
                        y_data = chart["y"]
                        stack_data = chart.get("stack")
                        
                        if x_data in text_columns:
                            df_plot = df_filtered[x_data].dropna().str.split('[,;]', expand=True).stack().str.strip().value_counts().reset_index()
                            df_plot.columns = [x_data, "Nombre"]
                            x_plot = x_data
                            y_plot = "Nombre"
                        elif y_data in text_columns:
                            df_plot = df_filtered[y_data].dropna().str.split('[,;]', expand=True).stack().str.strip().value_counts().reset_index()
                            df_plot.columns = [y_data, "Nombre"]
                            x_plot = y_data
                            y_plot = "Nombre"
                        else:
                            df_plot = df_filtered
                            x_plot = x_data
                            y_plot = y_data

                        if stack_data and stack_data in text_columns:
                            df_plot = df_filtered[stack_data].dropna().str.split('[,;]', expand=True).stack().str.strip().value_counts().reset_index()
                            stack_plot = stack_data
                        else:
                            stack_plot = None

                        # Génération dynamique du graphique en fonction des filtres actuels
                        try:
                            if chart["type"] == "Barres":
                                fig = px.bar(df_plot, x=x_plot, y=y_plot if y_plot else None, title=chart["name"])
                            elif chart["type"] == "Barres empilées":
                                if stack_plot:
                                    fig = px.bar(df_plot, x=x_plot, y=y_plot, color=stack_plot, title=chart["name"], barmode='stack')
                                else:
                                    fig = px.bar(df_plot, x=x_plot, y=y_plot, title=chart["name"])
                            elif chart["type"] == "Histogramme":
                                fig = px.histogram(df_plot, x=x_plot, title=chart["name"])
                            elif chart["type"] == "Histogramme empilé":
                                if stack_plot:
                                    fig = px.histogram(df_plot, x=x_plot, color=stack_plot, title=chart["name"], barmode='stack')
                                else:
                                    fig = px.histogram(df_plot, x=x_plot, title=chart["name"])
                            elif chart["type"] == "Circulaire":
                                fig = px.pie(df_plot, names=x_plot, values=y_plot if y_plot else None, title=chart["name"])
                            elif chart["type"] == "Nuage de points":
                                fig = px.scatter(df_plot, x=x_plot, y=y_plot, size=chart.get("size"), title=chart["name"])
                            elif chart["type"] == "Carte proportionnelle":
                                fig = px.treemap(df_plot, path=[x_plot], values=y_plot, title=chart["name"])
                            st.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}")
                        except ValueError:
                            st.warning(f"Impossible de générer un graphique {chart['type']} avec les paramètres de données sélectionnés", icon="⚠️")
                            continue

            else:
                st.info("Aucun graphique n'a été créé. Pour créer un graphique, cliquez sur le bouton 📊 Créer un graphique.", icon="ℹ️")

        else:
            # Mise en page du bouton de création de graphique
            _create_chart_btn_col1, create_chart_btn_col2 = st.columns([3, 1])

            # Affichage du bouton pour créer un graphique
            create_chart_btn_col2.button(icon="📊", label="Créer un graphique", key="create_chart_btn", disabled=True)

            # Affichage d'un message d'information
            st.info("Fonctionnalité indisponible, car aucun restaurant n'a été trouvé, essayez de modifier vos critères de recherche.", icon="ℹ️")

            # Réinitialisation des graphiques affichés
            st.session_state.charts = []

if __name__ == '__main__':
    main()