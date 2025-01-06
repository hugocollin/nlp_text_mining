import streamlit as st
def Navbar():
    with st.sidebar:
        st.page_link('app.py', label='Accueil', icon='🏠')
        st.page_link('pages/page1.py', label='Restaurants', icon='🍽️')
        st.page_link('pages/page2.py', label='Comparatif', icon='📊')
        
def Project_Structure():
    st.code('''
    .
    ├── README.md
    ├── requirements.txt
    ├── app.py
    ├── .streamlit/
    │   └── config.toml
    ├── pages/
    │   ├── page1.py
    │   └── page2.py
    ├── search-engine/
    │   ├── search_engine.py
    │   └── review_nb.ipynb
    └── utils/
        ├── components.py
        └── utils_geo.py
     '''   
   , language='bash')
    