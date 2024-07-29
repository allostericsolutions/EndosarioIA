from pdfminer.high_level import extract_text
from endosarioia.pdf_utils.patterns import patterns_to_remove # Ruta absoluta

def extract_pdf_text(pdf_path):
    """Extrae el texto de un archivo PDF."""
    raw_text = extract_text(pdf_path)
    return raw_text

def clean_pdf_text(raw_text):
    """Limpia y normaliza el texto extraído del PDF."""
    # Eliminar solo si la frase está completamente en mayúsculas
    for pattern in patterns_to_remove:
        raw_text = re.sub(pattern, '', raw_text)

    # Eliminar la parte en mayúsculas entre comillas
    raw_text = re.sub(r'"\s*[A-Z\s]+\s*"\s*', '', raw_text)

    # Agrupar y resaltar códigos alfanuméricos
    code_pattern = r'\b[A-Z]{2}\.\d{3}\.\d{3}\b'
    text_by_code = {}
    paragraphs = raw_text.split('\n')
    current_code = None

    # Contar códigos por documento (únicos)
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
