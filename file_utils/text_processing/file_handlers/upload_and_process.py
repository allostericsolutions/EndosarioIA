import streamlit as st
from file_utils.text_processing.text_processing import extract_and_clean_text

def upload_and_process_files():
    # Subir los dos archivos PDF
    uploaded_file_1 = st.file_uploader("Modelo", type=["pdf"], key="uploader1")
    uploaded_file_2 = st.file_uploader("Verificación", type=["pdf"], key="uploader2")

    # Variables para manejar el estado de los archivos subidos
    archivo_subido_1 = False
    archivo_subido_2 = False

    if uploaded_file_1:
        archivo_subido_1 = True
        text_by_code_1, unique_code_count_1, codes_model = extract_and_clean_text(uploaded_file_1)
    else:
        text_by_code_1 = unique_code_count_1 = codes_model = None

    if uploaded_file_2:
        archivo_subido_2 = True
        text_by_code_2, unique_code_count_2, _ = extract_and_clean_text(uploaded_file_2)
    else:
        text_by_code_2 = unique_code_count_2 = None

    return {
        'archivo_subido_1': archivo_subido_1,
        'archivo_subido_2': archivo_subido_2,
        'text_by_code_1': text_by_code_1,
        'unique_code_count_1': unique_code_count_1,
        'codes_model': codes_model,
        'text_by_code_2': text_by_code_2,
        'unique_code_count_2': unique_code_count_2
    }
