import streamlit as st
from utils.components import Navbar


def main():
    Navbar()

    st.title(f'🏠 Accueil') 
    
if __name__ == '__main__':
    main()