import streamlit as st
from pdfminer.high_level import extract_text
import pandas as pd
import re
from nameExtraction.extractNames import extractUppercaseNames  # Importar la nueva función
from text_processing import extract_and_clean_text
from file_utils.file_creators import create_excel, create_csv, create_txt
from file_utils.image_utils import mostrar_imagen
from gpt_config.openai_setup import initialize_openai
from file_utils.text_processing.text_processing import preprocess_text, calculate_semantic_similarity, extract_and_align_numbers_with_context, calculate_numbers_similarity

# Inicializar el cliente de OpenAI
client = initialize_openai()

# Configuración de la página de Streamlit
st.set_page_config(page_title="Endosario Móvil AI 2.0", page_icon="ícono robot.png")
st.title("Endosario Móvil AI 2.0")

# Información en la barra lateral
with st.sidebar.expander("Información", expanded=True):
    st.markdown("### Endosario Móvil AI 2.0")
    image_path = 'Allosteric_Solutions.png'
    caption = 'Interesse'
    width = 300
    mostrar_imagen(image_path, caption, width)

# Subida de archivos PDF
uploaded_file_1 = st.file_uploader("PEI", type=["pdf"], key="uploader1")
uploaded_file_2 = st.file_uploader("Metlife", type=["pdf"], key="uploader2")

archivo_subido_1 = False
archivo_subido_2 = False

# Procesar el archivo "PEI"
if uploaded_file_1:
    archivo_subido_1 = True
    text_by_code_1, unique_code_count_1, codes_model = extract_and_clean_text(uploaded_file_1)

# Procesar el archivo "Metlife"
if uploaded_file_2:
    archivo_subido_2 = True
    text_by_code_2, unique_code_count_2, _ = extract_and_clean_text(uploaded_file_2)
    
    # Extraer los nombres en mayúsculas del texto extraído de "Metlife"
    metlife_text = extract_text(uploaded_file_2)
    names_by_code = extractUppercaseNames(metlife_text)  # Guardar los nombres extraídos en un diccionario

# Botón para reiniciar
if st.sidebar.button("Reiniciar"):
    archivo_subido_1 = False
    archivo_subido_2 = False
    st.session_state.chat_history = []
    st.session_state.analysis_loaded = False
    st.session_state.saludo_enviado = False  # Reiniciar el estado del saludo

# Comparación de archivos
if archivo_subido_1 and archivo_subido_2:
    all_codes = set(text_by_code_1.keys()).union(set(text_by_code_2.keys()))

    def handle_long_text(text, length=70):
        if len(text) > length:
            return f'<details><summary>Endoso</summary>{text}</details>'
        else:
            return text

    comparison_data = []
    for code in all_codes:
        doc1_text = text_by_code_1.get(code, "Ausente")
        doc1_text_display = handle_long_text(doc1_text)
        doc2_text = text_by_code_2.get(code, "Ausente")
        doc2_text_display = handle_long_text(doc2_text)
        name = names_by_code.get(code, "")

        if doc1_text == "Ausente" or doc2_text == "Ausente":
            sim_percentage = 0
            similarity_str = "0.00%"
        else:
            sim_percentage = calculate_semantic_similarity(doc1_text, doc2_text)
            similarity_str = f'{sim_percentage:.2f}%'

        if doc1_text == "Ausente" or doc2_text == "Ausente":
            num_similarity_percentage = 0
            doc1_num_display = "Ausente"
            doc2_num_display = "Ausente"
        else:
            doc1_num, doc1_context, doc2_num, doc2_context = extract_and_align_numbers_with_context(doc1_text, doc2_text)
            doc1_num_display = f'<details><summary>{doc1_num}</summary><p>{doc1_context}</p></details>'
            doc2_num_display = f'<details><summary>{doc2_num}</summary><p>{doc2_context}</p></details>'
            num_similarity_percentage = calculate_numbers_similarity(doc1_num, doc2_num)

        row = {
            "Código": f'<b><span style="color:red;">{code}</span></b>',
            "Nombre del Código": name,  # Añadimos el nombre del código aquí
            "Documento PEI": doc1_text_display if doc1_text != "Ausente" else f'<b style="color:red;">Ausente</b>',
            "Valores numéricos PEI": f'<details><summary>Contexto</summary>{doc1_num_display}</details>',
            "Documento Metlife": doc2_text_display if doc2_text != "Ausente" else f'<b style="color:red;">Ausente</b>',
            "Valores numéricos Metlife": f'<details><summary>Contexto</summary>{doc2_num_display}</details>',
            "Similitud Texto": similarity_str,
            "Similitud Numérica": f'{num_similarity_percentage:.2f}%'
        }
        comparison_data.append(row)

    comparison_df = pd.DataFrame(comparison_data)

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
        html = html.replace(
            '<th>Documento PEI</th>',
            '<th style="font-size: 20px; font-weight: bold;">Documento PEI</th>'
        )
        html = html.replace(
            '<th>Documento Metlife</th>',
            '<th style="font-size: 20px; font-weight: bold;">Documento Metlife</th>'
        )
        df["Similitud Numérica"] = df["Similitud Numérica"].str.rstrip('%').astype(float)
        df["Similitud Numérica"] = df["Similitud Numérica"].apply(lambda x: f"{x:.2f}%")
        for i, row in df.iterrows():
            html = html.replace(
                f'<td class="fixed-width" style="border:1px solid black; padding:10px; text-align:left; vertical-align:top;">{row["Similitud Numérica"]}%</td>',
                f'<td class="fixed-width" style="border:1px solid black; padding:10px; text-align:left; vertical-align:top;">{row["Similitud Numérica"]}</td>'
            )
        return html

    table_html = generate_html_table(comparison_df)
    st.markdown("### Comparación de Documentos")
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("### Conteo de Códigos")
    st.write(f"**Documento PEI:** {unique_code_count_1} (Faltan: {', '.join(list(all_codes - set(codes_model)))})")
    st.write(f"**Documento Metlife:** {unique_code_count_2} (Faltan: {', '.join(list(all_codes - set(text_by_code_2.keys())))})")

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

# InteresseAssist Bot

st.markdown("### InteresseAssist Bot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "analysis_loaded" not in st.session_state:
    st.session_state.analysis_loaded = False
if "saludo_enviado" not in st.session_state:
    st.session_state.saludo_enviado = False

if not st.session_state.saludo_enviado:
    st.session_state.chat_history.append({"role": "user", "content": "Hola"})
    st.session_state.chat_history.append({"role": "assistant", "content": "Hola, soy InteresseAssist Bot. ¿En qué puedo ayudarte?"})
    st.session_state.saludo_enviado = True

with open("gpt_config/prompt.txt", "r") as f:
    prompt_base = f.read()

print(f"prompt_base: {prompt_base}")

filtered_codes = list(set(text_by_code_1.keys()) & set(text_by_code_2.keys()))

selected_code = st.selectbox("Selecciona un código:", filtered_codes, key="selected_code")

if selected_code and st.session_state.get("last_selected_code") != selected_code:
    st.session_state.chat_history = []
    st.session_state.last_selected_code = selected_code
    st.session_state.saludo_enviado = False  # Reiniciar el estado del saludo

if selected_code:
    st.markdown("### Cargar Análisis de Documentos")

    texto_modelo = text_by_code_1.get(selected_code, "Ausente")
    texto_verificacion = text_by_code_2.get(selected_code, "Ausente")
    with st.expander("Mostrar Textos Filtrados"):
        st.markdown(f"**Documento PEI:** {texto_modelo}")
        st.markdown(f"**Documento Metlife:** {texto_verificacion}")

    texto_modelo_con_codigo = f"Código: {selected_code}\n\n{texto_modelo}"
    texto_verificacion_con_codigo = f"Código: {selected_code}\n\n{texto_verificacion}"

    info_analisis = {
        "texto_modelo": texto_modelo_con_codigo,
        "texto_verificacion": texto_verificacion_con_codigo,
        "fila_comparacion": "",  # No se necesita en este caso
    }
    prompt_final = prompt_base.format(**info_analisis)

    if st.button("Enviar para Análisis"):
        st.session_state.chat_history = [{"role": "system", "content": prompt_final}]
        st.session_state.analysis_loaded = True

if st.session_state.analysis_loaded:
    st.markdown("### Interactuar con InteresseAssist Bot")

    if st.sidebar.button("Limpiar Conversación"):
        st.session_state.chat_history = [{"role": "system", "content": prompt_final}]
        st.session_state.saludo_enviado = False  # Reiniciar el estado del saludo

    for idx, message in enumerate(st.session_state.chat_history[1:]):
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input("Haz tu pregunta:"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.chat_history,
            max_tokens=1200,
            temperature=0.2,
        )

        st.session_state.chat_history.append(
            {"role": "assistant", "content": response.choices[0].message.content}
        )

        with st.chat_message("assistant"):
            st.write(response.choices[0].message.content)
