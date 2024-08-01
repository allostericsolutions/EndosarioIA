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

# Inicializar las configuraciones de OpenAI
client = initialize_openai()

# Configurar los parámetros de la página, incluyendo el nuevo icono
st.set_page_config(page_title="Endosario Móvil AI 2.0", page_icon="ícono robot.png")

# Título de la aplicación en la página principal
st.title("Endosario Móvil AI 2.0")

# Mostrar la imagen y el título en la barra lateral
with st.sidebar.expander("Información", expanded=True):
    st.markdown("### Endosario Móvil AI 2.0")
    image_path = 'Allosteric_Solutions.png'
    caption = 'Interesse'
    width = 300
    mostrar_imagen(image_path, caption, width)

# Subir los dos archivos PDF
uploaded_file_1 = st.file_uploader("Modelo", type=["pdf"], key="uploader1")
uploaded_file_2 = st.file_uploader("Verificación", type=["pdf"], key="uploader2")

# Variables para manejar el estado de los archivos subidos
archivo_subido_1 = False
archivo_subido_2 = False

# Función cacheada para extraer y limpiar texto (si el contenido del archivo no cambia con frecuencia)
@st.cache_data
def cache_extract_and_clean_text(uploaded_file):
    return extract_and_clean_text(uploaded_file)

# Verificar si los archivos han sido subidos y extraer el texto
if uploaded_file_1:
    archivo_subido_1 = True
    text_by_code_1, unique_code_count_1, codes_model = cache_extract_and_clean_text(uploaded_file_1)

if uploaded_file_2:
    archivo_subido_2 = True
    text_by_code_2, unique_code_count_2, _ = cache_extract_and_clean_text(uploaded_file_2)

# Botón para reiniciar la aplicación
if st.sidebar.button("Reiniciar"):
    archivo_subido_1 = False
    archivo_subido_2 = False
    st.session_state.chat_history = []
    st.session_state.analysis_loaded = False

# Función para cargar el prompt desde un archivo
def load_prompt():
    with open("gpt_config/prompt.txt", "r") as f:
        return f.read()

# Función para gestionar la conversación
def chat_with_bot(prompt):
    st.session_state.chat_history.append({"role": "system", "content": prompt})
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state.chat_history,
        max_tokens=1200,
        temperature=0.2,
    )
    return response.choices[0].message.content

# Inicializar el historial de chat en session_state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # Simular un "hola" automático del usuario para iniciar la conversación
    st.session_state.chat_history.append({"role": "user", "content": "Hola"})
    st.session_state.analysis_loaded = False

# Verificar si ambos archivos han sido subidos antes de proceder
if archivo_subido_1 and archivo_subido_2:
    # Obtener códigos comunes a ambos documentos
    filtered_codes = list(set(text_by_code_1.keys()) & set(text_by_code_2.keys()))

    # Filtro de códigos para la selección en la interfaz
    selected_code = st.selectbox("Selecciona un código:", filtered_codes, key="selected_code")

    # Limpiar conversación del chat al seleccionar un nuevo código
    if selected_code and st.session_state.get("last_selected_code") != selected_code:
        st.session_state.chat_history = []
        st.session_state.chat_history.append({"role": "user", "content": "Hola"})  # Simular un "hola" automático del usuario
        st.session_state.last_selected_code = selected_code

    if selected_code:
        # Mostrar los textos filtrados de forma oculta (opcional, puedes eliminar esta sección si no quieres mostrar los textos)
        texto_modelo = text_by_code_1.get(selected_code, "Ausente")
        texto_verificacion = text_by_code_2.get(selected_code, "Ausente")
        with st.expander("Mostrar Textos Filtrados", expanded=False):
            st.markdown(f"**Documento Modelo:** {texto_modelo}")
            st.markdown(f"**Documento Verificación:** {texto_verificacion}")

        # Incluir el código en los textos antes de enviarlos para análisis
        texto_modelo_con_codigo = f"Código: {selected_code}\n\n{texto_modelo}"
        texto_verificacion_con_codigo = f"Código: {selected_code}\n\n{texto_verificacion}"

        # Cargar el prompt desde el archivo
        prompt_base = load_prompt()

        # Crear el prompt inicial con el texto de los documentos y el código
        info_analisis = {
            "texto_modelo": texto_modelo_con_codigo,
            "texto_verificacion": texto_verificacion_con_codigo,
            "fila_comparacion": "",  # No se necesita en este caso
        }
        prompt_final = prompt_base.format(**info_analisis)

        # Iniciar el chat para cargar el análisis
        if st.button("Enviar para Análisis"):
            response = chat_with_bot(prompt_final)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.session_state.analysis_loaded = True
            st.write(response)

    # Verificar si el análisis ha sido cargado y gestionar las interacciones siguientes
    if st.session_state.analysis_loaded:
        # Botón para limpiar la conversación colocado en la barra lateral
        if st.sidebar.button("Limpiar Conversación"):
            st.session_state.chat_history = [{"role": "system", "content": prompt_final}]
            st.session_state.analysis_loaded = False

        # Mostrar la ventana de chat excluyendo el prompt del sistema
        for idx, message in enumerate(st.session_state.chat_history[1:]):
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Obtener la pregunta del usuario
        if prompt := st.chat_input("Haz tu pregunta:"):
            # Agregar la pregunta al historial de chat
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            # Llamar a GPT-3 con el historial de chat actualizado
            response = chat_with_bot(prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": response})

            # Mostrar la respuesta en la ventana de chat
            with st.chat_message("assistant"):
                st.write(response)
else:
    st.write("Por favor, sube ambos archivos PDF para proceder con el análisis.")
