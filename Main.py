import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
import io
import re
import difflib
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openpyxl.utils.exceptions import IllegalCharacterError
from text_processing import extract_and_clean_text
from file_utils.file_creators import create_excel, create_csv, create_txt
from file_utils.image_utils import mostrar_imagen
from gpt_config.openai_setup import initialize_openai
from file_utils.text_processing.text_processing import preprocess_text, calculate_semantic_similarity, extract_and_align_numbers_with_context, calculate_numbers_similarity
from endosos_utils.extraction.extract_metlife_endoso import extract_metlife_endoso_names  # Importar la nueva función

# Inicializar las configuraciones de OpenAI
client = initialize_openai()

# Configurar los parámetros de la página, incluyendo el nuevo icono
st.set_page_config(page_title="Endosario Móvil AI 2.1", page_icon="ícono robot.png")

# Título de la aplicación en la página principal
st.title("Endosario Móvil AI 2.1")

# Mostrar la imagen y el título en la barra lateral
with st.sidebar.expander("Información", expanded=True):
    st.markdown("### Endosario Móvil AI 2.1")
    image_path = 'Allosteric_Solutions.png'
    caption = 'Interesse'
    width = 300
    mostrar_imagen(image_path, caption, width)

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

if uploaded_file_2:
    archivo_subido_2 = True
    text_by_code_2, unique_code_count_2, _ = extract_and_clean_text(uploaded_file_2)

# Botón para reiniciar la aplicación
if st.sidebar.button("Reiniciar"):
    archivo_subido_1 = False
    archivo_subido_2 = False
    st.session_state.chat_history = []
    st.session_state.analysis_loaded = False
    st.session_state.saludo_enviado = False  # Reiniciar el estado del saludo

# Mostrar la sección de comparación de archivos solo si se han subido ambos archivos
if archivo_subido_1 and archivo_subido_2:
    
    # Obtener todos los códigos únicos presentes en ambos documentos
    all_codes = set(text_by_code_1.keys()).union(set(text_by_code_2.keys()))

    # Crear la tabla comparativa
    comparison_data = []
    for code in all_codes:
        doc1_text = text_by_code_1.get(code, "Ausente")
        doc2_text = text_by_code_2.get(code, "Ausente")

        # Si un texto no está presente, el porcentaje de similitud textual es 0
        if doc1_text == "Ausente" or doc2_text == "Ausente":
            sim_percentage = 0
            similarity_str = "0.00%"
        else:
            sim_percentage = calculate_semantic_similarity(doc1_text, doc2_text)
            similarity_str = f'{sim_percentage:.2f}%'

        # Agregar los datos a la tabla comparativa
        row = {
            "Código": code,
            "Documento PEI": doc1_text,
            "Documento Metlife": doc2_text,
            "Similitud Texto": similarity_str
        }
        comparison_data.append(row)

    # Convertir la lista a DataFrame
    comparison_df = pd.DataFrame(comparison_data)

    # Extraer nombres de endoso del texto del documento Metlife
    raw_text_metlife = extract_text(uploaded_file_2)
    endoso_names_metlife = extract_metlife_endoso_names(raw_text_metlife)

    # Añadir la columna de 'Nombre del Endoso' al DataFrame existente
    comparison_df['Nombre del Endoso Metlife'] = comparison_df['Código'].map(endoso_names_metlife)

    # Mostrar la tabla con los resultados
    st.write("Comparación de Documentos:")
    st.table(comparison_df)

if __name__ == "__main__":
    main()
