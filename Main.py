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

from gpt_config.openai_setup import initialize_openai
client = initialize_openai() 

# Función para preprocesar y normalizar el texto
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s.]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Función para calcular la similitud semántica 
def calculate_semantic_similarity(text1, text2):
    text1 = preprocess_text(text1)
    text2 = preprocess_text(text2)
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    cosine_sim = cosine_similarity(vectors)
    return cosine_sim[0, 1] * 100

# Función para extraer y limpiar el texto del PDF
def extract_and_clean_text(pdf_path):
    raw_text = extract_text(pdf_path)

    patterns_to_remove = [
        r'HOJA\s*:\s*\d+',
        r'G\.M\.M\. GRUPO PROPIA MEDICALIFE', 
        r'02001\/M\d+',
        r'CONTRATANTE:\s*GBM\s*GRUPO\s*BURSATIL\s*MEXICANO,\s*S\.A\. DE C\.V\. CASA DE BOLSA', 
        r'GO\-2\-021', 
        r'\bCONDICION\s*:\s*',
        r'MODIFICACIONES\s*A\s*DEFINICIONES\s*PERIODO\s*DE\s*GRACIA',
        # ... (resto de tus patrones)
    ]

    for pattern in patterns_to_remove:
        raw_text = re.sub(pattern, '', raw_text)

    raw_text = re.sub(r'"\s*[A-Z\s]+\s*"\s*', '', raw_text)

    code_pattern = r'\b[A-Z]{2}\.\d{3}\.\d{3}\b'
    text_by_code = {}
    paragraphs = raw_text.split('\n')
    current_code = None
    code_counts = set()

    for paragraph in paragraphs:
        code_match = re.search(code_pattern, paragraph)
        if code_match:
            current_code = code_match.group(0)
            paragraph = re.sub(code_pattern, '', paragraph).strip()
            if current_code not in text_by_code:
                text_by_code[current_code] = paragraph
            else:
                text_by_code[current_code] += " " + paragraph
            code_counts.add(current_code) 
        elif current_code:
            text_by_code[current_code] += " " + paragraph

    return text_by_code, len(code_counts), list(code_counts) 

# Función para limpiar caracteres ilegales
def clean_text(text):
    return ''.join(filter(lambda x: x in set(chr(i) for i in range(32, 127)), text))

# Función para agregar asteriscos según el porcentaje
def get_asterisks(similarity_percentage):
    if similarity_percentage > 95:
        return "" 
    elif 90 <= similarity_percentage <= 94:
        return "*"
    else:
        return "**" 

# ... (resto de las funciones: extract_and_align_numbers_with_context, calculate_numbers_similarity, create_excel, create_csv, create_txt)

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

# Mostrar la sección de comparación de archivos solo si se han subido ambos archivos
if archivo_subido_1 and archivo_subido_2:
    # Obtener todos los códigos únicos
    all_codes = set(text_by_code_1.keys()).union(set(text_by_code_2.keys()))

    def handle_long_text(text, length=70):
        if len(text) > length:
            return f'<details><summary>Endoso</summary>{text}</details>'
        else:
            return text

    # Crear la tabla comparativa
    comparison_data = []
    for code in all_codes:
        # ... (Tu código para generar la tabla de comparación - sin cambios)

    # Convertir la lista a DataFrame
    comparison_df = pd.DataFrame(comparison_data)

    # ... (Tu código para mostrar la tabla de comparación - sin cambios)

    # ... (Tu código para mostrar el conteo de códigos - sin cambios)

    # ... (Tu código para los botones de descarga - sin cambios)

    # --- Sección para la IA ---
    st.markdown("### Chat con IA")

    # Inicializar el historial de chat en session_state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Cargar el prompt base desde el archivo
    with open("gpt_config/prompt.txt", "r") as f:
        prompt_base = f.read()

    # Combinar el texto de ambos documentos (si ya existen)
    if 'text_by_code_1' in locals() and 'text_by_code_2' in locals():
        texto_documentos = f"Documento Modelo:\n{text_by_code_1}\n\nDocumento Verificación:\n{text_by_code_2}"
    else:
        texto_documentos = "Aún no se han cargado documentos para analizar."

    # Crear el diccionario con la información del análisis
    info_analisis = {
        "texto_documentos": texto_documentos,
        "tabla_comparacion": comparison_df.to_string(),
        "codigos_faltantes_modelo": ', '.join(list(all_codes - set(codes_model))),
        "codigos_faltantes_verificacion": ', '.join(list(all_codes - set(text_by_code_2.keys()))),
    }

    # Crear el prompt final con la información del análisis
    prompt_final = prompt_base.format(**info_analisis)
    st.session_state.chat_history.append({"role": "system", "content": prompt_final})

    # Mostrar la ventana de chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Obtener la pregunta del usuario
    if prompt := st.chat_input("Escribe tu pregunta:"):
        # Agregar la pregunta al historial de chat
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Llamar a GPT-3 con el prompt final
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.chat_history,
            max_tokens=100,
            temperature=0.7,
        )

        # Agregar la respuesta al historial de chat
        st.session_state.chat_history.append({"role": "assistant", "content": response.choices[0].message.content})

        # Mostrar la respuesta en la ventana de chat
        with st.chat_message("assistant"):
            st.write(response.choices[0].message.content) 

