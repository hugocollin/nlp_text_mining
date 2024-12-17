import streamlit as st
from utils.components import Navbar , Project_Structure


def main():
    Navbar()

    st.title(f'🏠 Home Page') 

    st.write('This is the `Home` page of the multi-page app.')
    st.write('See the sub-pages by clicking on the sidebar.')

    st.write('---')

    st.write('### Lancement de l\'application Streamlit :rocket:')  
    st.code(""" streamlit run app.py""" , language='bash')

    st.write('---')
    
    # affiche l'architecture du projet
    st.write('### Structure du projet')
    Project_Structure()
    

if __name__ == '__main__':
    main()