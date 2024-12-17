import streamlit as st
from utils.components import Navbar


def main():
    Navbar()

    st.title('View Tab 📊')
    st.write('This is the `View` page of the multi-page app.')
    st.write('See the sub-pages by clicking on the sidebar.')
    
    st.write('---')

if __name__ == '__main__':
    main()


