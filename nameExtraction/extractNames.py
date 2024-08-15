import re
from pdfminer.high_level import extract_text

def extract_and_clean_text(pdf_path):
    """Extrae el texto de un PDF y lo limpia eliminando patrones específicos.

    Args:
        pdf_path (str): La ruta al archivo PDF.

    Returns:
        tuple: Una tupla que contiene:
            - dict: Un diccionario donde las claves son códigos alfanuméricos
              y los valores son el texto asociado a cada código.
            - int: El número total de códigos únicos encontrados.
            - list: Una lista de todos los códigos únicos encontrados.
    """
    raw_text = extract_text(pdf_path)

    patterns_to_remove = [
        r'HOJA\s*:\s*\d+', 
        # Añadir aquí todos los patrones que mencionaste antes
        ...
        r'MODIFICACIONES\s*A\s*DEFINICIONES',  # Mantenido solo una vez
        r'MODIFICACIONES\s*A\s*CLAUSULAS\s*GENERALES',  # Mantenido solo una vez
    ]

    for pattern in patterns_to_remove:
        raw_text = re.sub(pattern, '', raw_text)

    # Eliminar texto en mayúsculas entre comillas
    raw_text = re.sub(r'"\s*[A-Z\s]+\s*"\s*', '', raw_text)

    # Agrupar texto por código alfanumérico
    code_pattern = r'\b[A-Z]{2}\.\d{3}\.'  # Patrón para encontrar el código alfanumérico
    text_by_code = {}
    paragraphs = raw_text.split('\n')
    current_code = None

    # Contar códigos únicos
    code_counts = set()

    for paragraph in paragraphs:
        code_match = re.search(code_pattern, paragraph)
        if code_match:
            current_code = code_match.group(0)
            # Reemplazar partes
            paragraph = re.sub(code_pattern, current_code, paragraph).strip()

            # Aquí eliminamos los tres caracteres que siguen al código
            paragraph = re.sub(r'(?<=\b[A-Z]{2}\.\d{3}\.)\s*[A-Za-z0-9]{3}\s*', '', paragraph).strip()

            if current_code not in text_by_code:
                text_by_code[current_code] = paragraph
            else:
                text_by_code[current_code] += " " + paragraph

            code_counts.add(current_code)
        elif current_code:
            text_by_code[current_code] += " " + paragraph

    return text_by_code, len(code_counts), list(code_counts)
