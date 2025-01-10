import streamlit as st
from pages.resources.components import Navbar, get_personnal_address

# Configuration de la page
st.set_page_config(page_title="SISE Ô Resto", page_icon="🍽️", layout="wide")

# Fonction pour afficher le popup de paramétrage de l'adresse personnelle
@st.dialog("Paramétrer son adresse personnelle", width="large")
def add_personal_address_dialog():
    personal_address = get_personnal_address()
    
    # Paramétrage de l'adresse personnelle
    if personal_address:
        st.write(f"Votre adresse personnelle actuelle est :")
        personal_address_input = st.text_input(label="Renseignez votre adresse personnelle", label_visibility="collapsed", placeholder="Renseignez votre adresse personnelle", key="personal_address_input", value=personal_address)
    else:
        st.write("Vous n'avez pas encore renseigné d'adresse personnelle.")
        personal_address_input = st.text_input(label="Renseignez votre adresse personnelle", label_visibility="collapsed", placeholder="Renseignez votre adresse personnelle", key="personal_address_input")
    
    dialog_col1, dialog_col2 = st.columns(2)

    # Boutons pour enregistrer l'adresse personnelle
    with dialog_col1:
        if st.button(icon="💾", label="Enregistrer mon adresse personnelle"):
            if personal_address_input.strip() == "":
                st.toast("⚠️ L'adresse ne peut pas être vide")
            else:
                st.session_state['personal_address'] = personal_address_input.strip()
                st.session_state['personal_address_added'] = True
                st.rerun()
    
    # Bouton pour supprimer l'adresse personnelle
    with dialog_col2:
        if st.button(icon="🗑️", label="Supprimer mon adresse personnelle", disabled=(get_personnal_address() is None)):
            st.session_state.pop('personal_address', None)
            st.session_state['personal_address_suppr'] = True
            st.rerun()

def main():
    # Barre de navigation
    Navbar()

    # Titre de la page
    st.title(f'Bienvenue sur SISE Ô Resto ! ')

    # Mise en page du bouton pour ajouter l'adresse personnelle
    add_restaurant_btn_col1, add_restaurant_btn_col2 = st.columns([2, 1])

    # Bouton pour ajouter l'adresse personnelle
    with add_restaurant_btn_col2:
        if st.button(icon="🏡", label="Paramétrer son adresse personnelle", key="add_personnal_address"):
            add_personal_address_dialog()
    
    # Affichage du message de succès
    if st.session_state.get('personal_address_added'):
        st.toast("💾 Adresse personnelle enregistrée avec succès")
        st.session_state['personal_address_added'] = False

    # Affichage du message de suppression
    if st.session_state.get('personal_address_suppr'):
        st.toast("🗑️ Adresse personnelle supprimée avec succès")
        st.session_state['personal_address_suppr'] = False

    # Description de l'application
    container = st.container()
    
    container.write("**Profitez d’une expérience culinaire optimisée et trouvez votre prochain repas à Lyon en toute simplicité avec SISE Ô Resto.**")
    container.write("Découvrez et explorez les meilleurs restaurants de Lyon grâce à notre application intuitive où vous pourrez :")
    
    container_col1_1, container_col1_2, container_col1_3 = container.columns(3, border=True)
    
    container_col1_1.write("**🔍 Explorez les restaurants**")
    container_col1_1.write("Parcourez une vaste sélection de restaurants à Lyon en filtrant par [...] pour trouver l'endroit idéal pour votre prochain repas.")
    container_col1_2.write("**ℹ️ Obtenez les informations détailllés des restaurants**")
    container_col1_2.write("Accédez aux fiches complètes comprenant [...] pour chaque restaurant.")
    container_col1_3.write("**🆚 Comparez les restaurants**")
    container_col1_3.write("Comparez facilement [...] et les caractéristiques des différents établissements pour prendre une décision éclairée.")
    
    container_col2_1, container_col2_2 = container.columns(2, border=True)

    container_col2_1.write("**📊 Statistiques détaillés des restaurants**")
    container_col2_1.write("Visualisez des statistiques pertinentes telles que [...] pour mieux comprendre chaque restaurant.")
    container_col2_2.write("**🗺️ Localiser les restaurants et obetnir un itinéraire en un clic**")
    container_col2_2.write("Utilisez la carte interactive pour localiser les restaurants proches de votre domicile et obtenez rapidement un itinéraire pour vous y rendre (veuillez renseigner votre adresse personelle en amont via la page d'accueil).")
    
    st.write("*Cette application a été développée par KPAMEGAN Falonne, KARAMOKO Awa, GABRYSCH Alexis et COLLIN Hugo, dans le cadre du Master 2 SISE.*")

if __name__ == '__main__':
    main()