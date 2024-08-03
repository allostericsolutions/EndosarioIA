# bot/chat_handler.py

import streamlit as st
from bot.config import initialize_openai, load_prompt

client = initialize_openai()

def handle_chat(selected_code, text_by_code_1, text_by_code_2):
    prompt_base = load_prompt()

    if selected_code and st.session_state.get("last_selected_code") != selected_code:
        st.session_state.chat_history = []
        st.session_state.last_selected_code = selected_code
        st.session_state.saludo_enviado = False  # Reiniciar el estado del saludo

    if selected_code:
        st.markdown("### Cargar Análisis de Documentos")
        texto_modelo = text_by_code_1.get(selected_code, "Ausente")
        texto_verificacion = text_by_code_2.get(selected_code, "Ausente")
        with st.expander("Mostrar Textos Filtrados"):
            st.markdown(f"**Documento Modelo:** {texto_modelo}")
            st.markdown(f"**Documento Verificación:** {texto_verificacion}")

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
