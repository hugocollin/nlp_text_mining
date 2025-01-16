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
    -- details TEXT,
    telephone TEXT,
    cuisines TEXT, 
    note_globale FLOAT,   
    cuisine_note FLOAT,
    service_note FLOAT,
    qualite_prix_note FLOAT,
    ambiance_note FLOAT,
    prix_min FLOAT,
    prix_max FLOAT,
    etoiles_michelin INTEGER,
    repas TEXT,
    latitude FLOAT,
    longitude FLOAT,
    scrapped BOOLEAN,
    image TEXT
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

ALTER TABLE fact_reviews 
ADD COLUMN review_cleaned TEXT;

ALTER TABLE fact_reviews 
ADD COLUMN sentiment INTEGER;

ALTER TABLE fact_reviews 
ADD COLUMN sentiment_rating TEXT;

ALTER TABLE dim_restaurants 
ADD COLUMN resume_avis TEXT;

ALTER TABLE dim_restaurants 
ADD COLUMN fonctionnalite TEXT;

ALTER TABLE dim_restaurants 
ADD COLUMN google_map TEXT;

ALTER TABLE dim_restaurants 
ADD COLUMN horaires TEXT;

ALTER TABLE dim_restaurants 
ADD COLUMN rank INTEGER;
