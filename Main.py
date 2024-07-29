import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from text_processing import extract_and_clean_text
from file_utils.file_creators import create_excel, create_csv, create_txt
from gpt_config.openai_setup import initialize_openai

# Inicializar el cliente OpenAI
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

# Función para extraer y alinear números con contexto
def extract_and_align_numbers_with_context(text1, text2, context_size=30):
    def extract_numbers_with_context(text):
        matches = re.finditer(r'\b\d+\b', text)
        numbers_with_context = []
        for match in matches:
            start = max(0, match.start() - context_size)
            end = min(len(text), match.end() + context_size)
            context = text[start:end].strip()
            numbers_with_context.append((match.group(), context))
        return numbers_with_context

    nums1_with_context = extract_numbers_with_context(text1)
    nums2_with_context = extract_numbers_with_context(text2)

    nums1 = [num for num, context in nums1_with_context] + [''] * max(0, len(nums2_with_context) - len(nums1_with_context))
    nums2 = [num for num, context in nums2_with_context] + [''] * max(0, len(nums1_with_context) - len(nums2_with_context))

    context1 = [context for num, context in nums1_with_context] + [''] * max(0, len(nums2_with_context) - len(nums1_with_context))
    context2 = [context for num, context in nums2_with_context] + [''] * max(0, len(nums1_with_context) - len(nums2_with_context))

    return ' '.join(nums1) if nums1 else 'N/A', ' '.join(context1) if context1 else 'N/A', ' '.join(nums2) if nums2 else 'N/A', ' '.join(context2) if context2 else 'N/A'

# Función para calcular la similitud de números
def calculate_numbers_similarity(nums1, nums2):
    nums1_list = nums1.split()
    nums2_list = nums2.split()
    matches = 0
    for n1, n2 in zip(nums1_list, nums2_list):
        if n1 == n2:
            matches += 1
    return (matches / len(nums1_list)) * 100 if nums1_list else 0

# Inicializar el historial de chat en session_state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Subir y analizar los documentos PDF
uploaded_file_1 = st.file_uploader("Modelo", type=["pdf"], key="uploader1")
uploaded_file_2 = st.file_uploader("Verificación", type=["pdf"], key="uploader2")

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
    st.session_state.chat_history = []

# Mostrar la imagen al inicio de la aplicación
image_path = 'Allosteric_Solutions.png'
image = Image.open(image_path)
st.image(image, caption='Interesse', use_column_width=True)

# Mostrar la sección de comparación de archivos solo si se han subido ambos archivos
if archivo_subido_1 and archivo_subido_2:
    
    # Obtener todos los códigos únicos
    all_codes = list(set(text_by_code_1.keys()).union(set(text_by_code_2.keys())))

    # Permitir al usuario seleccionar un código
    selected_code = st.selectbox("Selecciona un código:", all_codes)

    if selected_code:
        texto_modelo = text_by_code_1.get(selected_code, "Ausente")
        texto_verificacion = text_by_code_2.get(selected_code, "Ausente")

        # Crear el prompt base con los textos correspondientes
        prompt_base = (
            f"Documento Modelo:\n{texto_modelo}\n\n"
            f"Documento Verificación:\n{texto_verificacion}\n\n"
            "Responde a las preguntas del usuario sobre este análisis de documentos."
        )

        # Resetear el historial de chat si se selecciona un nuevo código
        if st.session_state.get("last_selected_code") != selected_code:
            st.session_state.chat_history = [{"role": "system", "content": prompt_base}]
            st.session_state.last_selected_code = selected_code

        # Mostrar interacción de chat
        st.markdown("### InteresseAssist Bot")

        # Mostrar historial de chat
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Obtener la pregunta del usuario
        if prompt := st.chat_input("Haz tu pregunta:"):
            # Añadir la pregunta al historial de chat
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            # Llamar al modelo GPT-3.5-turbo con el historial de chat actualizado
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.chat_history,
                max_tokens=1000,
                temperature=0.7,
            )

            # Añadir la respuesta al historial de chat
            st.session_state.chat_history.append(
                {"role": "assistant", "content": response.choices[0].message['content']}
            )

            # Mostrar la respuesta en la ventana de chat
            with st.chat_message("assistant"):
                st.write(response.choices[0].message['content'])

# Resto de las funcionalidades de generación y comparación de tablas
def handle_long_text(text, length=70):
    if len(text) > length:
        return f'<details><summary>Endoso</summary>{text}</details>'
    else:
        return text

def generate_html_table(df):
    html = df.to_html(index=False, escape=False, render_links=True)
    html = html.replace(
        '<table border="1" class="dataframe">',
        '<table border="1" class="dataframe" style="width:100%; border-collapse:collapse;">'
    ).replace(
        '<thead>',
        '<thead style="position: sticky; top: 0; z-index: 1; background: #fff;">'
    ).replace(
        '<th>',
        '<th class="fixed-width" style="background-color:#f2f2f2; padding:10px; text-align:left; z-index: 1;">'
    ).replace(
        '<td>',
        '<td class="fixed-width" style="border:1px solid black; padding:10px; text-align:left; vertical-align:top;">'
    )

    # Aplica estilos a "Documento Modelo" y "Documento Verificación"
    html = html.replace(
        '<th>Documento Modelo</th>',
        '<th style="font-size: 20px; font-weight: bold;">Documento Modelo</th>'
    )
    html = html.replace(
        '<th>Documento Verificación</th>',
        '<th style="font-size: 20px; font-weight: bold;">Documento Verificación</th>'
    )

    # Agrega estilos CSS para las celdas de similitud numérica
    df["Similitud Numérica"] = df["Similitud Numérica"].str.rstrip('%').astype(float)
    df["Similitud Numérica"] = df["Similitud Numérica"].apply(lambda x: f"{x:.2f}%")

    for i, row in df.iterrows():
        html = html.replace(
            f'<td class="fixed-width" style="border:1px solid black; padding:10px; text-align:left; vertical-align:top;">{row["Similitud Numérica"]}%</td>',
            f'<td class="fixed-width" style="border:1px solid black; padding:10px; text-align:left; vertical-align:top;">{row["Similitud Numérica"]}</td>'
        )

    return html

if archivo_subido_1 and archivo_subido_2:
    # Obtener todos los códigos únicos
    all_codes = set(text_by_code_1.keys()).union(set(text_by_code_2.keys()))

    # Crear la tabla comparativa
    comparison_data = []
    for code in all_codes:
        doc1_text = text_by_code_1.get(code, "Ausente")
        doc1_text_display = handle_long_text(doc1_text)
        doc2_text = text_by_code_2.get(code, "Ausente")
        doc2_text_display = handle_long_text(doc2_text)

        # Si un texto no está presente, el porcentaje de similitud textual es 0
        if doc1_text == "Ausente" or doc2_text == "Ausente":
            sim_percentage = 0
            similarity_str = "0.00%"
        else:
            sim_percentage = calculate_semantic_similarity(doc1_text, doc2_text)
            similarity_str = f'{sim_percentage:.2f}%'

        # Si un número no está presente, el porcentaje de similitud numérica es 0
        if doc1_text == "Ausente" or doc2_text == "Ausente":
            num_similarity_percentage = 0
            doc1_num_display = "Ausente"
            doc2_num_display = "Ausente"
        else:
            doc1_num, doc1_context, doc2_num, doc2_context = extract_and_align_numbers_with_context(
                doc1_text, doc2_text)
            doc1_num_display = f'<details><summary>{doc1_num}</summary><p>{doc1_context}</p></details>'
            doc2_num_display = f'<details><summary>{doc2_num}</summary><p>{doc2_context}</p></details>'

            num_similarity_percentage = calculate_numbers_similarity(doc1_num, doc2_num)

        row = {
            "Código": f'<b><span style="color:red;">{code}</span></b>',
            "Documento Modelo": doc1_text_display if doc1_text != "Ausente" else f'<b style="color:red;">Ausente</b>',
            "Valores numéricos Modelo": f'<details><summary>Contexto</summary>{doc1_num_display}</details>',
            "Documento Verificación": doc2_text_display if doc2_text != "Ausente" else f'<b style="color:red;">Ausente</b>',
            "Valores numéricos Verificación": f'<details><summary>Contexto</summary>{doc2_num_display}</details>',
            "Similitud Texto": similarity_str,
            "Similitud Numérica": f'{num_similarity_percentage:.2f}%'
        }
        comparison_data.append(row)

    # Convertir la lista a DataFrame
    comparison_df = pd.DataFrame(comparison_data)

    # Convertir DataFrame a HTML con estilización CSS y HTML modificado
    table_html = generate_html_table(comparison_df)
    st.markdown("### Comparación de Documentos")
    st.markdown(table_html, unsafe_allow_html=True)

    # Mostrar el conteo de códigos
    st.markdown("### Conteo de Códigos")
    st.write(f"**Documento Modelo:** {unique_code_count_1} (Faltan: {', '.join(list(all_codes - set(codes_model)))})")
    st.write(
        f"**Documento Verificación:** {unique_code_count_2} (Faltan: {', '.join(list(all_codes - set(text_by_code_2.keys())))})")

    # Botones para descargar los archivos
    col1, col2, col3 = st.columns(3)
    with col1:
        download_excel = st.button("Download Comparison Excel")
        if download_excel:
            excel_buffer = create_excel(comparison_df)
            st.download_button(
                label="Descarga Excel",
                data=excel_buffer,
                file_name="comparison.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    with col2:
        download_csv = st.button("Download Comparison CSV")
        if download_csv:
            csv_buffer = create_csv(comparison_df)
            st.download_button(
                label="Descarga CSV",
                data=csv_buffer,
                file_name="comparison.csv",
                mime="text/csv"
            )
    with col3:
        download_txt = st.button("Download Comparison TXT")
        if download_txt:
            txt_buffer = create_txt(comparison_df, unique_code_count_1, unique_code_count_2)
            st.download_button(
                label="Descarga TXT",
                data=txt_buffer,
                file_name="comparison.txt",
                mime="text/plain"
            )
