from PIL import Image
import streamlit as st

def mostrar_imagen(image_path, caption, width=None):
    """
    Función para mostrar una imagen con tamaño ajustable en Streamlit.

    Parámetros:
    - image_path: Ruta al archivo de imagen.
    - caption: Título o descripción de la imagen.
    - width: Ancho deseado de la imagen (en píxeles).
