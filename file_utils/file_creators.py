import io
import pandas as pd

# Función para limpiar caracteres ilegales (debes moverla también a este archivo)
def clean_text(text):
    return ''.join(filter(lambda x: x in set(chr(i) for i in range(32, 127)), text))


# Función para crear archivo Excel
def create_excel(data):
    buffer = io.BytesIO()
    df = pd.DataFrame(data)
    for column in df.columns:
        df[column] = df[column].apply(clean_text)
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    return buffer


# Función para crear archivo CSV
def create_csv(data):
    buffer = io.BytesIO()
    df = pd.DataFrame(data)
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer


# Función para crear archivo TXT
def create_txt(data, code_counts_1, unique_code_count_2):
    buffer = io.BytesIO()
    buffer.write("## Comparación de Documentos\n\n".encode('utf-8'))
    buffer.write(data.to_string(index=False, header=True).encode('utf-8'))
    buffer.write("\n\n## Conteo de Códigos\n\n".encode('utf-8'))
    buffer.write(
        f"**Documento Modelo:** {code_counts_1} (Faltan: {', '.join(list(all_codes - set(codes_model)))})\n".encode(
            'utf-8'))
    buffer.write(
        f"**Documento Verificación:** {unique_code_count_2} (Faltan: {', '.join(list(all_codes - set(text_by_code_2.keys())))})\n".encode(
            'utf-8'))
    buffer.seek(0)
    return buffer
