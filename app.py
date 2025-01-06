import streamlit as st
from utils.components import Navbar, get_personnal_address, get_coordinates
import urllib.parse
import webbrowser

st.set_page_config(page_title="[Titre de l\'application]", layout="wide")

@st.dialog("Paramétrer son adresse personnelle", width="large")
def add_personal_address_dialog():
    personal_address = get_personnal_address()
    
    if personal_address:
        st.write(f"Votre adresse personnelle actuelle est : {personal_address}")
    else:
        st.write("Vous n'avez pas encore renseigné d'adresse personnelle.")
    
    personal_address_input = st.text_input(label="Renseignez votre adresse personnelle", label_visibility="collapsed", placeholder="Renseignez votre adresse personnelle", key="personal_address_input")
    
    dialog_col1, dialog_col2 = st.columns(2)

    with dialog_col1:
        if st.button(icon="💾", label="Enregistrer mon adresse personnelle"):
            if personal_address_input.strip() == "":
                st.toast("⚠️ L'adresse ne peut pas être vide")
            else:
                st.session_state['personal_address'] = personal_address_input.strip()
                st.session_state['personal_address_added'] = True
                st.rerun()
    
    with dialog_col2:
        if st.button(icon="🗑️", label="Supprimer mon adresse personnelle", disabled=(get_personnal_address() is None)):
            st.session_state.pop('personal_address', None)
            st.session_state['personal_address_suppr'] = True
            st.rerun()

def main():
    Navbar()

    st.title(f'[Titre de l\'application]')

    add_restaurant_btn_col1, add_restaurant_btn_col2 = st.columns([2, 1])

    with add_restaurant_btn_col2:
        if st.button(icon="🏡", label="Paramétrer son adresse personnelle", key="add_personnal_address"):
            add_personal_address_dialog()
    
    if st.session_state.get('personal_address_added'):
        st.toast("💾 Adresse personnelle enregistrée avec succès")
        st.session_state['personal_address_added'] = False

    if st.session_state.get('personal_address_suppr'):
        st.toast("🗑️ Adresse personnelle supprimée avec succès")
        st.session_state['personal_address_suppr'] = False

    st.write(f'[Description de l\'application]')
    st.write(f'[Affichage des recommandations (top restaurants)]')

    st.header("[TEMP] Rechercher un itinéraire de transport en commun")

    departure_address = st.text_input(label="Adresse de départ", label_visibility="collapsed", placeholder="Adresse de départ")
    arrival_address = st.text_input(label="Adresse d'arrivée", label_visibility="collapsed", placeholder="Adresse d'arrivée")
    
    if st.button("GO ! 🏎️"):
        if not departure_address or not arrival_address:
            st.toast("⚠️ Veuillez renseigner les adresses de départ et d'arrivée.")
        else:
            st.toast("⏳ Calcul de l'itinéraire en cours...")

            dep_lat, dep_lon = get_coordinates(departure_address)
            arr_lat, arr_lon = get_coordinates(arrival_address)
            
            if dep_lat and dep_lon and arr_lat and arr_lon:
                from_coord = f"{dep_lon};{dep_lat}"
                to_coord = f"{arr_lon};{arr_lat}"
                encoded_from = urllib.parse.quote(from_coord)
                encoded_to = urllib.parse.quote(to_coord)
                
                tcl_url = f"https://www.tcl.fr/itineraires?date=now&pmr=0&from={encoded_from}&to={encoded_to}"

                st.toast("🏁 Itinéraire calculé avec succès !")
                
                webbrowser.open_new_tab(tcl_url)
            else:
                st.error("Une ou plusieurs adresses sont invalides. Veuillez vérifier vos entrées.") # [TEMP]
    
if __name__ == '__main__':
    main()