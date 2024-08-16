import re

def extraer_nombres_verificacion(texto):
    """Extrae los nombres asociados a los códigos del documento "Verificación".

    Args:
        texto (str): El texto completo del documento "Verificación".

    Returns:
        dict: Un diccionario donde las llaves son los códigos y los valores son los nombres.
    """
    nombres_codigos = {}
    for match in re.findall(r'CONDICION :\s+([A-Z]{2}\.\d{3}\.\d{3})\s+(.+?)(?=CONDICION :|$)', texto, re.DOTALL):
        codigo, nombre = match
        nombres_codigos[codigo] = nombre.strip()
    return nombres_codigos

