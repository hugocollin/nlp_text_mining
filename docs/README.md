# README : NLP Text Mining

## Table des matières
- [Description](#description)
- [Fonctionnalités principales](#fonctionnalités-principales)
- [Structure du projet](#structure-du-projet)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Contribution](#contribution)
- [Auteurs](#auteurs)

## Description

Profitez d’une expérience culinaire optimisée et trouvez votre prochain repas à Lyon en toute simplicité avec SISE Ô Resto.

Ce projet offre également un ensemble d’outils d’analyse et de comparaison pour faciliter la recherche et la sélection d’établissements. Grâce à des filtres avancés, vous pouvez cibler rapidement les restaurants qui correspondent le mieux à vos goûts, puis visualiser leurs caractéristiques sous forme de graphiques pour un aperçu clair et rapide. Enfin, l’intégration d’une IA conversationnelle permet d’obtenir des recommandations personnalisées et d’explorer facilement les avis clients.

### Fonctionnalités principales

- Explorez les restaurants à Lyon : Découvrez une large sélection de restaurants à Lyon et trouvez l'endroit idéal pour votre prochain repas. Consultez rapidement le statut actuel de chaque établissement, le temps de trajet et accédez en un clic à des informations détaillées et à l'itinéraire.

- Informations détaillées à portée de main : Accédez aux fiches complètes de chaque restaurant, incluant les informations pratiques, les avis clients et bien plus.

- Filtres avancés pour une recherche personnalisée : Utilisez 14 filtres différents pour affiner votre recherche et trouver l'endroit parfait selon vos préférences.

- btenez des recommandations personnalisées : Discutez avec notre IA pour des conseils sur les meilleurs restaurants à Lyon adaptés à vos goûts.

- Localisez les restaurants en un clin d'œil : Grâce à la carte interactive, repérez facilement les restaurants près de chez vous et explorez vos options.

- Comparez les établissements facilement : Comparez les caractéristiques des différents restaurants pour prendre une décision éclairée rapidement et sans effort.

- Visualisez vos graphiques de manière intuitive : Créez des graphiques personnalisés pour comparer et analyser les données des restaurants de Lyon facilement et rapidement.

- Ajoutez des restaurants à votre sélection en un clic : Ajoutez des restaurants à votre liste pour les comparer et les consulter en un instant.

### Structure du projet

```bash
├── .streamlit
│    └── config.toml
├── docs
│   ├── rapport.pdf
│   └── README.md
├── pages
│   ├── resources
│   │    ├── images
│   │    │   └──...
│   │    └── components.py
│   ├── admin.py
│   └── explorer.py   
├── src
│   ├── db
│   │   ├── __init__.py
│   │   ├── db_schema.sql
│   │   ├── functions_db.py
│   │   ├── init_db.py
│   │   ├── models.py
│   │   └── update_db.py
│   ├── nlp
│   │   ├── __init__.py
│   │   ├── analyse.py
│   │   ├── pretraitement.py
│   │   └── stopwords_fr.txt
│   ├── searchengine
│   │   ├── __init__.py
│   │   └── trip_finder.py
│   ├── __init__.py
│   └── pipeline.py
├── .dockerignore
├── .env # Placez le fichier .env à la racine du projet
├── .gitignore
├── app.py
├── docker-compose.yml
├── dockerfile
├── requirements.txt
└── restaurant_reviews.db
```

## Installation

Pour installer ce projet :

1. Clonez le dépôt sur votre machine locale, en utilisant la commande suivante :

```bash
git clone https://github.com/hugocollin/nlp_text_mining
```

2. Puis récupérez le fichier `.env` (qui vous a été envoyé par mail) contenant la clé API Mistral et placez-le à la racine du projet (comme indiqué dans la [Structure du projet](#structure-du-projet)).

## Utilisation

Pour utiliser cette application vous avez 3 méthodes :

### I. Utilisez l'application avec Docker

1. Installez et demarrez [Docker Desktop](https://www.docker.com/products/docker-desktop/) sur votre machine.

2. Ouvrez votre terminal et déplacez-vous à la racine du projet.

3. Exécutez la commande suivante pour construire l'image Docker :

```bash
docker-compose up --build
```
*Cette étape peut prendre entre 10 à 20 minutes. En raison de la taille de l'image Docker générée (> 20 Go), nous ne fournissons l'image Docker pré-construite que sur demande.*

4. Ouvrez votre navigateur et accédez à l'adresse suivante : [http://localhost:8501](http://localhost:8501)

### II. Utilisez l'application en local

1. Installez et activez un environnement Python avec une version 3.11.

2. Ouvrez votre terminal et déplacez-vous à la racine du projet.

3. Exécutez la commande suivante pour installer les dépendances du projet :

```bash
pip install -r requirements.txt
```

4. Exécutez la commande suivante pour lancer l'application :

```bash
streamlit run app.py
```

5. Ouvrez votre navigateur et accédez à l'adresse suivante : [http://localhost:8501](http://localhost:8501)

### III. Utilisez l'application en ligne

Ouvrez votre navigateur et accédez à l'adresse suivante : [https://sise-o-resto.streamlit.app](https://sise-o-resto.streamlit.app)

## Contribution

Toutes les contributions sont les bienvenues ! Voici comment vous pouvez contribuer :

1. Forkez le projet.
2. Créez votre branche de fonctionnalité  (`git checkout -b feature/AmazingFeature`).
3. Commitez vos changements (`git commit -m 'Add some AmazingFeature'`).
4. Pushez sur la branche (`git push origin feature/AmazingFeature`).
5. Ouvrez une Pull Request. 

## Auteurs

Cette application a été développée par [KPAMEGAN Falonne](https://github.com/marinaKpamegan), [KARAMOKO Awa](https://github.com/karamoko17), [GABRYSCH Alexis](https://github.com/AlexisGabrysch) et [COLLIN Hugo](https://github.com/hugocollin), dans le cadre du Master 2 SISE.