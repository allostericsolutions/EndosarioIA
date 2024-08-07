import streamlit as st
from pdfminer.high_level import extract_text
from fpdf import FPDF
import pandas as pd
import io
import re
import difflib
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarityimport openai
import streamlit as st
import random
import logging
import sys
import os

# Añadir la ruta del directorio raíz a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from chatbot import chatbot_interface  # Importar la interfaz del chatbot

# Configurar OpenAI
def configure_openai():
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
    if not OPENAI_API_KEY:
        st.error("Please add your OpenAI API key to the Streamlit secrets.toml file.")
        st.stop()
    openai.api_key = OPENAI_API_KEY
    return openai.OpenAI()

client = configure_openai()

# Configuración de la página de Streamlit
st.set_page_config(page_title="Ultrasound Quiz", page_icon="📚")  # Reinsertar icono de la página

# Listas de órganos, patologías, y condiciones asociadas
peritoneal_organs = [
    "Gallbladder", "Liver", "Ovaries", "Spleen", "Stomach", 
    "Appendix", "Transverse colon", "First part of the duodenum", 
    "Jejunum", "Ileum", "Sigmoid colon"
]
retroperitoneal_organs = [
    "Abdominal lymph nodes", "Adrenal glands", "Aorta", 
    "Ascending and descending colon", "Most of the duodenum", "IVC", 
    "Kidneys", "Pancreas", "Prostate gland", "Ureters", 
    "Urinary bladder", "Uterus"
]
echogenicity_order = [
    "Renal sinus", "Diaphragm", "Pancreas", "Spleen", "Liver", 
    "Renal cortex", "Renal pyramids", "Gallbladder"
]
pathologies_with_ascites = [
    "Abdominal trauma", "Acute cholecystitis", "Cirrhosis", 
    "Congestive heart failure", "Ectopic pregnancy", "Malignancy", 
    "Portal hypertension", "Ruptured abdominal aortic aneurysm"
]

# Funciones relevantes movidas aquí
def generate_questions(exam_type, num_questions=5):
    questions = []
    if exam_type == "Echogenicity":
        seen_organs = set()
        while len(questions) < num_questions:
            organ_pair = tuple(random.sample(echogenicity_order, 2))
            if organ_pair not in seen_organs:
                seen_organs.add(organ_pair)
                question_type = "more" if len(questions) % 2 == 0 else "less"
                question = f"Which organ is {question_type} echogenic: {organ_pair[0]} or {organ_pair[1]}?"
                questions.append((question, organ_pair))
    elif exam_type == "Peritoneal or Retroperitoneal":
        organs = peritoneal_organs + retroperitoneal_organs
        random.shuffle(organs)
        for organ in organs[:num_questions]:
            question = f"Is {organ} a peritoneal or retroperitoneal organ?"
            questions.append((question, organ))
    elif exam_type == "Pathologies associated with ascites":
        for _ in range(num_questions):
            correct_pathology = random.choice(pathologies_with_ascites)
            false_options = generate_false_options(client, correct_pathology, num_options=2)
            all_pathologies = [correct_pathology] + false_options
            random.shuffle(all_pathologies)
            question = f"Which of the following is a pathology associated with ascites?"
            questions.append((question, correct_pathology, all_pathologies))
    return questions

def generate_false_options(client, correct_pathology, num_options=2):
    prompt = f""" Generate a list of medically plausible conditions that could be mistakenly believed to be associated with ascites, but are not. These conditions should sound complex and be named in a way that could confuse even medical students, incorporating terms from advanced medical sciences. Some conditions can be entirely fictitious but should sound like potential real medical diagnoses. Provide {num_options} such conditions, distinct from: {correct_pathology}, providing only the name of each condition. """
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Cambiado a gpt-4o-mini
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,  # Cambiado a 300 tokens
        temperature=0.2,
    )
    false_options = [option.strip() for option in response.choices[0].message.content.split("\n") if option.strip()]
    return false_options

def check_answer(exam_type, question_info, answer, question):
    if exam_type == "Echogenicity":
        organ_pair = question_info
        is_more = "more" in question
        correct_organ = organ_pair[0] if echogenicity_order.index(organ_pair[0]) < echogenicity_order.index(organ_pair[1]) else organ_pair[1]
        if not is_more:
            correct_organ = organ_pair[1] if correct_organ == organ_pair[0] else organ_pair[0]
        return answer.lower() == correct_organ.lower()
    elif exam_type == "Peritoneal or Retroperitoneal":
        organ = question_info
        is_peritoneal = organ in peritoneal_organs
        return (answer.lower() == "peritoneal" and is_peritoneal) or (answer.lower() == "retroperitoneal" and not is_peritoneal)
    elif exam_type == "Pathologies associated with ascites":
        correct_pathology = question_info
        return answer.lower() == correct_pathology.lower()

def get_explanation(client, exam_type, question_info, is_correct, question, user_answer=None):
    if exam_type == "Echogenicity":
        organ_pair = question_info
        is_more = "more" in question
        correct_organ = organ_pair[0] if echogenicity_order.index(organ_pair[0]) < echogenicity_order.index(organ_pair[1]) else organ_pair[1]
        if not is_more:
            correct_organ = organ_pair[1] if correct_organ == organ_pair[0] else organ_pair[0]
        with open("Prompts/echogenicity.txt", "r") as file:
            prompt_template = file.read()
        comparison_text = "more echogenic" if is_more else "less echogenic"
        prompt = f"{prompt_template}\n\nThe user's response was '{user_answer}'. The correct answer is '{correct_organ}'. Provide an explanation based on the information in this text about why '{correct_organ}' is {comparison_text} than '{user_answer}'."
    
    elif exam_type == "Peritoneal or Retroperitoneal":
        organ = question_info
        with open("Prompts/peritoneal.txt", "r") as file:
            prompt = file.read().format(organ=organ)
    
    elif exam_type == "Pathologies associated with ascites":
        correct_pathology = question_info
        prompt = (f"Provide a brief explanation about {correct_pathology} focusing on its relation with ascites or relevant ultrasound findings.")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.2,
    )
    explanation = response.choices[0].message.content.strip()
    explanation = explanation.replace(" - ", "\n - ")
    return explanation

def main():
    st.sidebar.title("Type of quiz")

    mode = st.sidebar.selectbox("Select Mode", ["Quiz", "Chatbot"])

    if mode == "Quiz":
        exam_type = st.sidebar.selectbox(
            "Select the type of quiz", 
            ("Echogenicity", "Peritoneal or Retroperitoneal", "Pathologies associated with ascites")
        )
        st.header("Ultrasound Quiz")
        
        if 'questions' not in st.session_state or st.session_state.exam_type != exam_type:
            st.session_state.exam_type = exam_type
            st.session_state.questions = generate_questions(exam_type)
            st.session_state.answers = [None] * len(st.session_state.questions)
            st.session_state.correct_count = 0
            st.session_state.feedback = ""
            st.session_state.explanations = []
            st.session_state.graded = False
        
        st.markdown(f"### {exam_type} Quiz")
        for idx, item in enumerate(st.session_state.questions):
            if exam_type == "Pathologies associated with ascites":
                question, correct_pathology, all_pathologies = item
                st.markdown(f"<h4 style='color: orange;'>{question}</h4>", unsafe_allow_html=True)
                if st.session_state.answers[idx] is None:
                    cols = st.columns(3)
                    with cols[0]:
                        if st.button(all_pathologies[0], key=f"{all_pathologies[0]}_{idx}"):
                            st.session_state.answers[idx] = all_pathologies[0]
                    with cols[1]:
                        if st.button(all_pathologies[1], key=f"{all_pathologies[1]}_{idx}"):
                            st.session_state.answers[idx] = all_pathologies[1]
                    with cols[2]:
                        if st.btn(all_pathologies[2], key=f"{all_pathologies[2]}_{idx}"):
                            st.session_state.answers[idx] = all_pathologies[2]
                else:
                    st.markdown(f"<b>Your answer:</b> <span style='color: blue;'>{st.session_state.answers[idx]}</span>", unsafe_allow_html=True)
            else:
                question, question_info = item
                formatted_question = question.replace(" (Yes/No)", "")
                st.markdown(f"<h4 style='color: orange;'>{formatted_question}</h4>", unsafe_allow_html=True)
                if st.session_state.answers[idx] is None:
                    col1, col2 = st.columns(2)
                    if exam_type == "Echogenicity":
                        with col1:
                            if st.button(question_info[0], key=f"{question_info[0]}_{idx}"):
                                st.session_state.answers[idx] = question_info[0]
                        with col2:
                            if st.button(question_info[1], key=f"{question_info[1]}_{idx}"):
                                st.session_state.answers[idx] = question_info[1]
                    elif exam_type == "Peritoneal or Retroperitoneal":
                        with col1:
                            if st.button("Peritoneal", key=f"Peritoneal_{idx}"):
                                st.session_state.answers[idx] = "peritoneal"
                        with col2:
                            if st.button("Retroperitoneal", key=f"Retroperitoneal_{idx}"):
                                st.session_state.answers[idx] = "retroperitoneal"
                else:
                    st.markdown(f"<b>Your answer:</b> <span style='color: blue;'>{st.session_state.answers[idx]}</span>", unsafe_allow_html=True)

        if all(answer is not None for answer in st.session_state.answers) and not st.session_state.graded:
            incorrect_questions = []
            correct_count = 0
            for i, item in enumerate(st.session_state.questions):
                if st.session_state.answers[i] is not None:
                    question_info = None
                    correct_pathology = None
                    if exam_type == "Pathologies associated with ascites":
                        question, correct_pathology, all_pathologies = item
                        correct = check_answer(exam_type, correct_pathology, st.session_state.answers[i], question)
                    else:
                        question, question_info = item
                        correct = check_answer(exam_type, question_info, st.session_state.answers[i], question)
                    if correct:
                        correct_count += 1
                    else:
                        explanation = get_explanation(client, exam_type, question_info if exam tipo != "Pathologies associated with ascites" else correct_pathology, correct, question, st.session_state.answers[i])
                        incorrect_questions.append((question, st.session_state.answers[i], explanation))
            st.session_state.correct_count = correct_count
            st.session_state.explanations = incorrect_questions
            st.session_state.graded = True

        total_questions = len(st.session_state.questions)
        score = (st.session_state.correct_count / total_questions) * 100
        st.markdown(f"### Tu puntaje es: {score:.2f}/100")
        if st.session_state.explanations:
            st.markdown("### Revisión de respuestas incorrectas:")
            for q, ans, exp in st.session_state.explanations:
                st.markdown(f"<b>**Pregunta:**</b> {q}", unsafe_allow_html=True)
                st.markdown(f"<b>**Your answer:**</b> <span style='color: blue;'>{ans}</span>", unsafe_allow_html=True)
                st.markdown(exp, unsafe_allow_html=True)

        if st.button("Reiniciar Quiz - Haz clic dos veces", key="reset", use_container_width=True, on_click=lambda: st.session_state.clear()):
            st.session_state.clear()
    elif mode == "Chatbot":
        # Mostrar la interfaz del chatbot
        chatbot_interface()

if __name__ == "__main__":
    main()
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

    # Función para manejar texto largo en el campo del endoso
    def handle_long_text(text, length=70):
        if len(text) > length:
            return f'<details><summary>Endoso</summary>{text}</details>'
        else:
            return text

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
            doc1_num, doc1_context, doc2_num, doc2_context = extract_and_align_numbers_with_context(doc1_text, doc2_text)
            doc1_num_display = f'<details><summary>{doc1_num}</summary><p>{doc1_context}</p></details>'
            doc2_num_display = f'<details><summary>{doc2_num}</summary><p>{doc2_context}</p></details>'
            num_similarity_percentage = calculate_numbers_similarity(doc1_num, doc2_num)

        # Agregar los datos a la tabla comparativa
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

    # Generar HTML para la tabla con estilización CSS
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

    # Convertir DataFrame a HTML con estilización CSS y HTML modificado
    table_html = generate_html_table(comparison_df)
    st.markdown("### Comparación de Documentos")
    st.markdown(table_html, unsafe_allow_html=True)

    # Mostrar el conteo de códigos únicos en cada documento
    st.markdown("### Conteo de Códigos")
    st.write(f"**Documento Modelo:** {unique_code_count_1} (Faltan: {', '.join(list(all_codes - set(codes_model)))})")
    st.write(f"**Documento Verificación:** {unique_code_count_2} (Faltan: {', '.join(list(all_codes - set(text_by_code_2.keys())))})")

    # Botones para descargar los archivos de comparación en diferentes formatos
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

    # --- Sección para la IA ---
    st.markdown("### InteresseAssist Bot")

    # Inicializar el historial de chat en session_state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "analysis_loaded" not in st.session_state:
        st.session_state.analysis_loaded = False
    if "saludo_enviado" not in st.session_state:
        st.session_state.saludo_enviado = False

    # Simular el saludo si no ha sido enviado
    if not st.session_state.saludo_enviado:
        st.session_state.chat_history.append({"role": "user", "content": "Hola"})
        st.session_state.chat_history.append({"role": "assistant", "content": "Hola, soy InteresseAssist Bot. ¿En qué puedo ayudarte?"})
        st.session_state.saludo_enviado = True

    # Cargar el prompt desde el archivo de configuración
    with open("gpt_config/prompt.txt", "r") as f:
        prompt_base = f.read()

    # Verificación mediante impresión del prompt cargado
    print(f"prompt_base: {prompt_base}")

    # Obtener códigos comunes a ambos documentos
    filtered_codes = list(set(text_by_code_1.keys()) & set(text_by_code_2.keys()))

    # Filtro de códigos para la selección en la interfaz
    selected_code = st.selectbox("Selecciona un código:", filtered_codes, key="selected_code")

    # Limpiar conversación del chat al seleccionar un nuevo código
    if selected_code and st.session_state.get("last_selected_code") != selected_code:
        st.session_state.chat_history = []
        st.session_state.last_selected_code = selected_code
        st.session_state.saludo_enviado = False  # Reiniciar el estado del saludo

    if selected_code:
        # Sección para el chat con GPT para cargar el análisis de documentos
        st.markdown("### Cargar Análisis de Documentos")

        # Mostrar los textos filtrados de forma oculta
        texto_modelo = text_by_code_1.get(selected_code, "Ausente")
        texto_verificacion = text_by_code_2.get(selected_code, "Ausente")
        with st.expander("Mostrar Textos Filtrados"):
            st.markdown(f"**Documento Modelo:** {texto_modelo}")
            st.markdown(f"**Documento Verificación:** {texto_verificacion}")

        # Incluir el código en los textos antes de enviarlos para análisis
        texto_modelo_con_codigo = f"Código: {selected_code}\n\n{texto_modelo}"
        texto_verificacion_con_codigo = f"Código: {selected_code}\n\n{texto_verificacion}"

        # Crear el prompt inicial con el texto de los documentos y el código
        info_analisis = {
            "texto_modelo": texto_modelo_con_codigo,
            "texto_verificacion": texto_verificacion_con_codigo,
            "fila_comparacion": "",  # No se necesita en este caso
        }
        prompt_final = prompt_base.format(**info_analisis)

        # Iniciar el chat para cargar el análisis
        if st.button("Enviar para Análisis"):
            st.session_state.chat_history = [{"role": "system", "content": prompt_final}]
            st.session_state.analysis_loaded = True

    # Verificar si el análisis ha sido cargado
    if st.session_state.analysis_loaded:
        st.markdown("### Interactuar con InteresseAssist Bot")

        # Botón para limpiar la conversación colocado en la barra lateral
        if st.sidebar.button("Limpiar Conversación"):
            st.session_state.chat_history = [{"role": "system", "content": prompt_final}]
            st.session_state.saludo_enviado = False  # Reiniciar el estado del saludo

        # Mostrar la ventana de chat excluyendo el prompt del sistema
        for idx, message in enumerate(st.session_state.chat_history[1:]):
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Obtener la pregunta del usuario
        if prompt := st.chat_input("Haz tu pregunta:"):
            # Agregar la pregunta al historial de chat
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            # Llamar a gpt-4o-mini con el historial de chat actualizado
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.chat_history,
                max_tokens=1200,
                temperature=0.2,
            )

            # Agregar la respuesta al historial de chat
            st.session_state.chat_history.append(
                {"role": "assistant", "content": response.choices[0].message.content}
            )

            # Mostrar la respuesta en la ventana de chat
            with st.chat_message("assistant"):
                st.write(response.choices[0].message.content)
