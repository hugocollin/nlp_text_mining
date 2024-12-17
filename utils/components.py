import streamlit as st
def Navbar():
    with st.sidebar:
        st.page_link('app.py', label='Home', icon='🏠')
        st.page_link('pages/page1.py', label='View Tab', icon='📊')
        st.page_link('pages/page2.py', label='Recommendation Tab', icon='📈')
        
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
    