
# text_processing/pdf_utils.py

import streamlit as st # Importa streamlit
from text_processing import extract_and_clean_text 

def handle_pdf_uploads():
    """
    Maneja la subida de archivos PDF y la extracción de texto.

    Returns:
        tuple: Una tupla que contiene:
            - dict: Diccionario con códigos como claves y texto del archivo PEI.
            - int: Conteo de códigos únicos del archivo PEI.
            - list: Lista de códigos del archivo PEI.
            - dict: Diccionario con códigos como claves y texto del archivo Metlife.
            - int: Conteo de códigos únicos del archivo Metlife.
            - bool: True si se subieron ambos archivos, False en caso contrario.
    """
    # Subir los dos archivos PDF
    uploaded_file_1 = st.file_uploader("PEI", type=["pdf"], key="uploader1")
    uploaded_file_2 = st.file_uploader("Metlife", type=["pdf"], key="uploader2")

    # Variables para manejar el estado de los archivos subidos
    archivo_subido_1 = False
    archivo_subido_2 = False

    # Verificar si los archivos han sido subidos y extraer el texto
    if uploaded_file_1:
        archivo_subido_1 = True
        text_by_code_1, unique_code_count_1, codes_model = extract_and_clean_text(uploaded_file_1)
    else:
        text_by_code_1, unique_code_count_1, codes_model = {}, 0, []

    if uploaded_file_2:
        archivo_subido_2 = True
        text_by_code_2, unique_code_count_2, _ = extract_and_clean_text(uploaded_file_2)
    else:
        text_by_code_2, unique_code_count_2 = {}, 0

    return (text_by_code_1, unique_code_count_1, codes_model, 
            text_by_code_2, unique_code_count_2, 
            archivo_subido_1 and archivo_subido_2) 
