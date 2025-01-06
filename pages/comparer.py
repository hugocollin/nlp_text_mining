import streamlit as st
from utils.components import Navbar, available_restaurants_options

st.set_page_config(page_title="[Titre de l\'application] - Comparer", layout="wide")

def main():
    Navbar()
    
    st.title('📊 Comparer')

    col1, col2, col3 = st.columns(3, border=True)

    with col1:
        restaurant_select1 = col1.selectbox(label="Sélectionner un restaurant", label_visibility="collapsed", placeholder="Sélectionner un restaurant", options=available_restaurants_options, key="restaurant_select1")

    with col2:
        restaurant_select2 = col2.selectbox(label="Sélectionner un restaurant", label_visibility="collapsed", placeholder="Sélectionner un restaurant", options=available_restaurants_options, key="restaurant_select2")
    
    with col3:
        restaurant_select3 = col3.selectbox(label="Sélectionner un restaurant", label_visibility="collapsed", placeholder="Sélectionner un restaurant", options=available_restaurants_options, key="restaurant_select3")

if __name__ == '__main__':
    main()