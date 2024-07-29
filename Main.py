import streamlit as st
from pdf_utils import extract_pdf_text, clean_pdf_text
from comparison_utils import calculate_semantic_similarity, extract_numbers_with_context, calculate_numbers_similarity
from file_utils import create_file
from utils import preprocess_text, clean_text  # Importa las funciones generales
from gpt_config.openai_setup import initialize_openai
import re
from PIL import Image 

client = initialize_openai()  # Inicializa OpenAI al principio de la aplicación

# Función para preprocesar y normalizar el texto
# ... (Ya existente)

# Función para calcular la similitud semántica entre dos textos usando TF-IDF y Cosine Similarity
# ... (Ya existente)

# Función para extraer y limpiar el texto del PDF
def extract_and_clean_text(pdf_path):
    """Extrae y limpia el texto del PDF."""
    raw_text = extract_pdf_text(pdf_path)
    text_by_code, code_counts, unique_codes = clean_pdf_text(raw_text)
    return text_by_code, len(code_counts), unique_codes

# Función para limpiar caracteres ilegales
# ... (Ya existente)

# Función para agregar asteriscos según el porcentaje
# ... (Ya existente)

# Función para extraer y alinear los números y su contexto
# ... (Ya existente)

# Función para calcular la similitud de los números
# ... (Ya existente)

# Función para crear archivo Excel
# ... (Ya existente)

# Función para crear archivo CSV
# ... (Ya existente)

# Función para crear archivo TXT
# ... (Ya existente)

# Interfaz de usuario de Streamlit
st.title("Endosario Móvil")

# Mostrar la imagen al inicio de la aplicación
image_path = 'Allosteric_Solutions.png'
image = Image.open(image_path)
st.image(image, caption='Interesse', use_column_width=True)

# Subir los dos archivos PDF
uploaded_file_1 = st.file_uploader("Modelo", type=["pdf"], key="uploader1")
uploaded_file_2 = st.file_uploader("Verificación", type=["pdf"], key="uploader2")

# Variables para manejar el estado de los archivos subidos
archivo_subido_1 = False
archivo_subido_2 = False

if uploaded_file_1:
    archivo_subido_1 = True
    text_by_code_1, unique_code_count_1, codes_model = extract_and_clean_text(uploaded_file_1)

if uploaded_file_2:
    archivo_subido_2 = True
    text_by_code_2, unique_code_count_2, _ = extract_and_clean_text(uploaded_file_2)

# Botón para reiniciar la aplicación
if st.button("Reiniciar"):
    archivo_subido_1 = False
    archivo_subido_2 = False
    # ... Resto del código para mostrar la pantalla inicial ...

# Mostrar la sección de comparación de archivos solo si se han subido ambos archivos
if archivo_subido_1 and archivo_subido_2:
    # Obtener todos los códigos únicos
    all_codes = set(text_by_code_1.keys()).union(set(text_by_code_2.keys()))

    def handle_long_text(text, length=70):
        # ... (Ya existente)

    # Crear la tabla comparativa
    # ... (Ya existente)

    # Convertir la lista a DataFrame
    # ... (Ya existente)

    # Generar HTML para la tabla con títulos de columnas fijos y estilización adecuada
    def generate_html_table(df):
        # ... (Ya existente)

    # Convertir DataFrame a HTML con estilización CSS y HTML modificado
    table_html = generate_html_table(comparison_df)
    st.markdown("### Comparación de Documentos")
    st.markdown(table_html, unsafe_allow_html=True)

    # Mostrar el conteo de códigos
    # ... (Ya existente)

    # Botones para descargar los archivos
    # ... (Ya existente)

    # --- Sección para la IA ---
    # ... (Ya existente) 
