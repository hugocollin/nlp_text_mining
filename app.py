import streamlit as st
from utils.components import Navbar, get_coordinates
import urllib.parse
import webbrowser

st.set_page_config(page_title="[Titre de l\'application]")

def main():
    Navbar()

    st.title(f'[Titre de l\'application]')
    st.write(f'[Description de l\'application]')
    st.write(f'[Paramètrage de l\'adresse personnelle]')
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

                st.toast("✅ Itinéraire calculé avec succès !")
                
                webbrowser.open_new_tab(tcl_url)
            else:
                st.error("Une ou plusieurs adresses sont invalides. Veuillez vérifier vos entrées.") # [TEMP]
    
if __name__ == '__main__':
    main()