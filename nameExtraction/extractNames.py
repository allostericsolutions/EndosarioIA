import re

def extractUppercaseNames(pdf_text):
    """
    Esta función extrae nombres en mayúsculas de un texto PDF, omitiendo ciertas frases redundantes.
    
    Args:
    pdf_text (str): Texto extraído de un PDF.

    Returns:
    dict: Diccionario con códigos alfanuméricos como llaves y nombres en mayúsculas como valores.
    """
    # Expresión regular para encontrar códigos alfanuméricos y nombres en mayúsculas
    pattern = re.compile(r'([A-Z]+\.\d+\.\d+)\s+([A-Z\s,]+)')
    matches = pattern.findall(pdf_text)
    
    namesByCode = {}
    for code, name in matches:
        # Limpiar nombres excluyendo las frases redundantes
        cleanedName = name.replace("MODIFICACIONES A DEFINICIONES", "").replace("MODIFICACIONES A CLAUSULAS GENERALES", "").strip()
        if code not in namesByCode and cleanedName:  # Para evitar duplicados y excluir texto redundante
            namesByCode[code] = cleanedName
    
    return namesByCode
