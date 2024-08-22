# config/config.py

import streamlit as st
from gpt_config.openai_setup import initialize_openai
from file_utils.image_utils import mostrar_imagen
from file_utils.sidebar_utils import mostrar_readme

def configurar_aplicacion():
    client = initialize_openai()

    # Configurar los parámetros de la página, incluyendo el nuevo icono
    st.set_page_config(page_title="Endosario Móvil AI 2.2", page_icon="Allosteric_Solutions.png")

    # Título de la aplicación en la página principal
    st.title("Endosario Móvil AI 2.2")

    # Mostrar la imagen y el título en la barra lateral
    with st.sidebar.expander("Información", expanded=True):
        st.markdown("### Endosario Móvil AI 2.2")
        image_path = 'Allosteric_Solutions.png'
        caption = 'Interesse'
        width = 300
        mostrar_imagen(image_path, caption, width)

    # Mostrar el README en la barra lateral
    mostrar_readme()

    return client
