from PIL import Image
import streamlit as st

def mostrar_imagen(image_path, caption, width=None, height=None):
    """
    Función para mostrar una imagen con tamaño ajustable en Streamlit.
    
    Parámetros:
    - image_path: Allosteric_Solutions.png.
    - caption: Título o descripción de la imagen.
    - width: Ancho deseado de la imagen (en píxeles).
    - height: Altura deseada de la imagen (en píxeles).
    """
    image = Image.open(image_path)
    st.image(image, caption=caption, use_column_width=False, width=width, height=height)
