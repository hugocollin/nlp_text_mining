from sqlalchemy import  Column, Integer, String, Float, Text, ForeignKey, Date, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class Restaurant(Base):
    __tablename__ = 'dim_restaurants'

     # Colonnes de la table
    id_restaurant = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String, nullable=False)
    adresse = Column(String)
    url_link = Column(String)
    email = Column(String)
    # details = Column(String)  # Pour stocker des informations comme 'FOURCHETTE DE PRIX', etc.
    telephone = Column(String)
    cuisines = Column(String)
    note_globale = Column(Float)  # NOTE GLOBALE
    cuisine_note = Column(Float)
    service_note = Column(Float)
    qualite_prix_note = Column(Float)
    ambiance_note = Column(Float)
    prix_min = Column(Float)
    prix_max = Column(Float)
    etoiles_michelin = Column(Integer)
    repas = Column(String)  # POUR 'REPAS' (Déjeuner, Dîner, etc.)

    
    avis = relationship("Review", back_populates="restaurant")
    scrapped = Column(Boolean, default=False)  
    latitude = Column(Float)
    longitude = Column(Float)
    resume_avis = Column(Text)
    image = Column(String)
    fonctionnalite = Column(Text)
    horaires = Column(Text)
    google_map = Column(String)
    rank = Column(Integer)


"""class Geographie(Base):
    __tablename__ = 'dim_geographie'

    id_geographie = Column(Integer, primary_key=True, autoincrement=True)
    quartier = Column(String)
    ville = Column(String, nullable=False)
    region = Column(String)
    nombre_restaurants = Column(Integer)
    transports_proches = Column(Text)
    distance_parking = Column(Float)
    densite_socio_eco = Column(Float)
    population = Column(Integer)

    restaurants = relationship("Restaurant", back_populates="geographie")
"""
class Review(Base):
    __tablename__ = 'fact_reviews'

    id_review = Column(Integer, primary_key=True, autoincrement=True)
    id_restaurant = Column(Integer, ForeignKey('dim_restaurants.id_restaurant'))
    id_user = Column(Integer, ForeignKey('dim_users.id_user'))
    date_review = Column(Date, nullable=False)
    title_review = Column(String)
    review_text = Column(Text)
    rating = Column(Float)
    type_visit = Column(String)
    review_cleaned = Column(Text)
    sentiment = Column(Integer)
    sentiment_rating = Column(String)


    restaurant = relationship("Restaurant", back_populates="avis")
    user = relationship("User", back_populates="avis")

class User(Base):
    __tablename__ = 'dim_users'

    id_user = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String, nullable=False)
    user_profile = Column(String, nullable=False, unique=True)
    num_contributions = Column(Integer)

    avis = relationship("Review", back_populates="user")

class Chunk(Base):
    __tablename__ = 'chunks'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)




















