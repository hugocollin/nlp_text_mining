# Utilisation d'une image Python
FROM python:3.11

# Définition du répertoire de travail dans le conteneur
WORKDIR /app

# Copie des fichiers de configuration des dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copie du reste du code de l'application dans le conteneur
COPY . .

# Ouverture du port Streamlit
EXPOSE 8501

# Définition des variables d'environnement nécessaires
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLECORS=false

# Démarrage de l'application Streamlit
CMD ["streamlit", "run", "app.py"]