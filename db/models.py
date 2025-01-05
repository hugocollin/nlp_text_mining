from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Restaurant(Base):
    __tablename__ = 'dim_restaurants'

    id_restaurant = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String, nullable=False)
    url_link = Column(String, nullable=False)
    adresse = Column(String)
    cuisine_note = Column(Float)
    service_note = Column(Float)
    quality_price_note = Column(Float)
    ambiance_note = Column(Float)
    id_geographie = Column(Integer, ForeignKey('dim_geographie.id_geographie'))

    geographie = relationship("Geographie", back_populates="restaurants")
    avis = relationship("Review", back_populates="restaurant")

class Geographie(Base):
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
    cuisine_note = Column(Float)
    service_note = Column(Float)
    quality_price_note = Column(Float)
    ambiance_note = Column(Float)

    restaurant = relationship("Restaurant", back_populates="avis")
    user = relationship("User", back_populates="avis")

class User(Base):
    __tablename__ = 'dim_users'

    id_user = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    profile = Column(String)
    num_contributions = Column(Integer)

    avis = relationship("Review", back_populates="user")

def init_db(db_path="sqlite:///restaurant_reviews.db"):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
