# Utilisation d'une image Python
FROM python:3.11-slim

# Copie des fichiers de configuration des dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Définition du répertoire de travail dans le conteneur
WORKDIR /app

# Copie des fichiers de l'application
COPY .env .
COPY *.py ./
COPY *.db ./
COPY .streamlit/ .streamlit/
COPY db/ db/
COPY pages/ pages/
COPY searchengine/ searchengine/

# Ouverture du port Streamlit
EXPOSE 8501

# Démarrage de l'application Streamlit
CMD ["streamlit", "run", "app.py"]