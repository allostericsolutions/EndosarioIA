import streamlit as st

def mostrar_readme():
    with st.sidebar:
        with st.expander("README"):  # Crea la pestaña "README"
            st.markdown("---")
            st.markdown("***")
            st.markdown("### Un fragmento del Quijote:")
            st.markdown(
                "> *Y al fin, Sancho, dijo don Quijote, acuérdate de lo que te he dicho siempre: la virtud es su propia recompensa, y los que la siguen nunca quedan sin ella.*",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<font size='1'><i>(Don Quijote de la Mancha, Parte II)</i></font>",
                unsafe_allow_html=True,
            )
            st.markdown("***")
