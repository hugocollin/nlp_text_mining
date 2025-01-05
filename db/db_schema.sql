-- Table des utilisateurs
CREATE TABLE dim_users (
    id_user INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL,
    user_profile TEXT,
    num_contributions INTEGER
);

-- Table des restaurants
CREATE TABLE dim_restaurants (
    id_restaurant INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    adresse TEXT,
    url_link TEXT,
    email TEXT,
    details TEXT,
    telephone TEXT,
    cuisines TEXT,    
    cuisine_note FLOAT,
    service_note FLOAT,
    qualite_prix_note FLOAT,
    ambiance_note FLOAT,
    regime_special TEXT,
    prix_min FLOAT,
    prix_max FLOAT,
    etoiles_michelin INTEGER,
    latitude FLOAT,
    longitude FLOAT
);

CREATE TABLE dim_geographie (
    id_geographie INTEGER PRIMARY KEY AUTOINCREMENT,
    quartier TEXT,
    ville TEXT NOT NULL,
    region TEXT,
    nombre_restaurants INTEGER,
    transports_proches TEXT,
    distance_parking FLOAT,
    densite_socio_eco FLOAT
);


-- Table des avis
CREATE TABLE fact_reviews (
    id_review INTEGER PRIMARY KEY AUTOINCREMENT,
    id_restaurant INTEGER NOT NULL,
    id_user INTEGER NOT NULL,
    date_review DATE,
    title_review TEXT,
    review_text TEXT,
    rating FLOAT,
    type_visit TEXT,
    FOREIGN KEY (id_restaurant) REFERENCES dim_restaurants(id_restaurant),
    FOREIGN KEY (id_user) REFERENCES dim_users(id_user)
);


