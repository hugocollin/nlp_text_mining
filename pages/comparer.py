import streamlit as st
from utils.components import Navbar

st.set_page_config(page_title="[Titre de l\'application] - Comparer", layout="wide")

def main():
    Navbar()
    
    st.title('📊 Comparer')
    st.write('[Comparateur à 3 restaurants]')

if __name__ == '__main__':
    main()