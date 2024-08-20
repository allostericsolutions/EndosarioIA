# endosos_utils/extraction/extract_endoso.py

import re

def extract_endoso_names(text):
    """
    Extrae los nombres de endoso basados en un patrón específico de códigos alfanuméricos.
    
    Args:
        text (str): Texto del cual extraer los nombres de endoso.
    
    Returns:
        dict: Diccionario con códigos como claves y nombres de endoso como valores.
    """
    pattern = r'(\b[A-Z]{2}\.\d{3}\.\d{3}\b)\s+([A-Z\s]+)\n([A-Z\s]+)'
    matches = re.findall(pattern, text)
    endoso_names = {match[0]: match[2].strip().lower().capitalize() for match in matches}
    return endoso_names
