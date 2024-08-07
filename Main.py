import openai
import streamlit as st
import random
import logging
import sys
import os

# Añadir la ruta del directorio raíz a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from chatbot import chatbot_interface  # Importar la interfaz del chatbot

# Configuración de la página de Streamlit
st.set_page_config(page_title="Ultrasound Quiz", page_icon="📚")  # Reinsertar icono de la página

# Configurar OpenAI
def configure_openai():
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
    if not OPENAI_API_KEY:
        st.error("Please add your OpenAI API key to the Streamlit secrets.toml file.")
        st.stop()
    openai.api_key = OPENAI_API_KEY
    return openai.OpenAI()

client = configure_openai()

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
    
    elif exam tipo == "Pathologies associated with ascites":
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
    st.sidebar.title("Navigation")

    # Selector de modo en la barra lateral
    mode = st.sidebar.radio("Select Mode", ["Quiz", "Chatbot"])

    if mode == "Quiz":
        exam_type = st.sidebar.selectbox(
            "Select the type of quiz", 
            ("Echogenicity", "Peritoneal or Retroperitoneal", "Pathologies associated with ascites"),
        )
        st.header(f"{exam_type} Quiz")
        
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
                        if st.button(all_pathologies[2], key=f"{all_pathologies[2]}_{idx}"):
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
                    if exam_type == "Pathologies associated with ascites":
                        question, correct_pathology, all_pathologies = item
                        correct = check_answer(exam_type, correct_pathology, st.session_state.answers[i], question)
                    else:
                        question, question_info = item
                        correct = check_answer(exam_type, question_info, st.session_state.answers[i], question)
                    if correct:
                        correct_count += 1
                    else:
                        explanation = get_explanation(client, exam_type, question_info if exam_type != "Pathologies associated with ascites" else correct_pathology, correct, question, st.session_state.answers[i])
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

        if st.btn("Reiniciar Quiz - Haz clic dos veces", key="reset", use_container_width=True, on_click=lambda: st.session_state.clear()):
            st.session_state.clear()
    elif mode == "Chatbot":
        # Mostrar la interfaz del chatbot
        chatbot_interface()

if __name__ == "__main__":
    main()
