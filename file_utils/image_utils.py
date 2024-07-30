from PIL import Image
import streamlit as st

def mostrar_imagen(image_path, caption, width=None):
    """
    Función para mostrar una imagen con tamaño ajustable en Streamlit.

    Parámetros:
    - image_path: Ruta al archivo de imagen.
    - caption: Título o descripción de la imagen.
    - width: Ancho deseado de la imagen (en píxeles).
    """
    try:
        # Verificar y abrir la imagen
        if not isinstance(image_path, str):
            raise TypeError("`image_path` debe ser una cadena de texto que represente la ruta de la imagen")
        image = Image.open(image_path)
        
        # Verificar el tipo de caption
        if not isinstance(caption, str):
            raise TypeError("`caption` debe ser una cadena de texto")
        
        # Verificar el tipo de width
        if width is not None and not isinstance(width, int):
            raise TypeError("`width` debe ser un número entero o None")
        
        st.image(image, caption=caption, use_column_width=False, width=width)
    except Exception as e:
        st.error(f"Error al mostrar la imagen: {e}")
