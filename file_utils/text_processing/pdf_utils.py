import streamlit as st
from text_processing import extract_and_clean_text

def subir_archivos():
    # Subir los dos archivos PDF
    uploaded_file_1 = st.file_uploader("PEI", type=["pdf"], key="uploader1")
    uploaded_file_2 = st.file_uploader("Metlife", type=["pdf"], key="uploader2")
    return uploaded_file_1, uploaded_file_2

def verificar_archivos(uploaded_file_1, uploaded_file_2):
    # Variables para manejar el estado de los archivos subidos
    archivo_subido_1 = False
    archivo_subido_2 = False

    # Verificar si los archivos han sido subidos y extraer el texto
    text_by_code_1, unique_code_count_1, codes_model = None, None, None
    text_by_code_2, unique_code_count_2 = None, None

    if uploaded_file_1:
        archivo_subido_1 = True
        text_by_code_1, unique_code_count_1, codes_model = extract_and_clean_text(uploaded_file_1)
    if uploaded_file_2:
        archivo_subido_2 = True
        text_by_code_2, unique_code_count_2, _ = extract_and_clean_text(uploaded_file_2)

    return archivo_subido_1, archivo_subido_2, text_by_code_1, unique_code_count_1, codes_model, text_by_code_2, unique_code_count_2
