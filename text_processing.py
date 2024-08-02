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
        r'G\.M\.M\. GRUPO PROPIA MEDICALIFE',
        r'02001\/M\d+',
        r'CONTRATANTE:\s*GBM\s*GRUPO\s*BURSATIL\s*MEXICANO,\s*S\.A\. DE C\.V\. CASA DE BOLSA',
        r'GO\-2\-021',
        r'\bCONDICION\s*:\s*',
        r'MODIFICACIONES\s*A\s*DEFINICIONES\s*PERIODO\s*DE\s*GRACIA',
        r'MODIFICACIONES\s*A\s*DEFINICIONES',
        r'MODIFICACIONES\s*A\s*DEFINICIONES',
        r'MODIFICACIONES',
        r'MODIFICACIONES\s*A\s*OTROS',
        r'A\s*CLAUSULAS\s*GENERALES\s*PAGO\s*DE\s*COMPLEMENTOS\s*ANTERIORES',
        r'A\s*GASTOS\s*CUBIERTOS\s*MATERNIDAD',
        r'A\s*EXCLUSIONES\s*MOTOCICLISMO',
        r'A\s*CLAUSULAS\s*ADICIONALES\s*OPCIO\s*CORRECCION\s*DE\s*LA\s*VISTA',
        r'A\s*GASTOS\s*CUBIERTOS\s*MATERNIDAD',
        r'A\s*EXCLUSIONES\s*MOTOCICLISMO',
        r'A\s*OTROS\s*HALLUX\s*VALGUS',
        r'A\s*GASTOS\s*CUBIERTOS\s*COBERTURA\s*DE\s*INFECCION\s*VIH\s*Y\/O\s*SIDA',
        r'A\s*GASTOS\s*CUBIERTOS\s*GASTOS\s*DEL\s*DONADOR\s*DE\s*ÓRGANOS\s*EN\s*TRASPLANTE',
        r'A\s*CLAUSULAS\s*GENERALES\s*MOVIMIENTOS\s*DE\s*ASEGURADOS\s*AUTOADMINISTRADA\s*\(INICIO\s*vs\s*RENOVACIÓN\)',  # Nuevo patrón agregado
        r'A\s*GASTOS\s*CUBIERTOS\s*PADECIMIENTOS\s*CONGENITOS',
        r'A\s*GASTOS\s*CUBIERTOS\s*HONORARIOS\s*MÉDICOS\s*Y\/O\s*QUIRÚRGICOS',
        r'A\s*GASTOS\s*CUBIERTOS\s*PADECIMIENTOS\s*PREEXISTENTES',
        r'A\s*GASTOS\s*CUBIERTOS\s*TRATAMIENTOS\s*DE\s*REHABILITACION',
        r'A\s*DEDUCIBLE\s*Y\s*COASEGURO\s*APLICACION\s*DE\s*DEDUCIBLE\s*Y\s*COASEGURO',
        r'A\s*GASTOS\s*CUBIERTOS\s*CIRCUNCISION\s*NO\s*PROFILACTICA',
        r'A\s*CLAUSULAS\s*ADICIONALES\s*OPCIO\s*CLAUSULA\s*DE\s*EMERGENCIA\s*EN\s*EL\s*EXTRANJERO',
        r'A\s*CLAUSULAS\s*ADICIONALES\s*OPCIO\s*CORRECCION\s*DE\s*LA\s*VISTA',
        r'EXCLUSION\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'EXCLUSIN\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'EXCLUSIN\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'EXCLUSIÓN\s*PRESTADORES\s*DE?\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'CON\s*PERIODO\s*DE\s*ESPERA',
        r'A\s*GASTOS\s*CUBIERTOS\s*CIRUGIA\s*DE\s*NARIZ\s*Y\s*SENOS\s*PARANASALES',
        r'A\s*OTROS\s*FRANJA\s*FRONTERIZA',
        r'RAZON\s*SOCIAL\s*DEL\s*CONTRATANTE',
        r'A\s*OTROS\s*CONVERSION\s*INDIVIDUAL\s*PARA\s*EL\s*SUBGRUPO1',
        r'A\s*GASTOS\s*CUBIERTOS\s*HERNIAS',
        r'A\s*GASTOS\s*CUBIERTOS\s*COBERTURA\s*DE\s*DAO\s*PSIQUIATRICO',
        r'A\s*GASTOS\s*CUBIERTOS\s*CIRCUNCISION',
        r'A\s*OTROS\s*REGISTRO\s*DE\s*CONDICIONES\s*GENERALES',
        r'A\s*OTROS\s*PADECIMIENTOS\s*CON\s*PERIODO\s*DE\s*ESPERA',
        r'A\s*GASTOS\s*CUBIERTOS\s*HONORARIOS\s*POR\s*CONSULTAS\s*MEDICAS',
        r'A\s*OTROS\s*LITOTRIPSIAS',
        r'A\s*EXCLUSIONES\s*RECIEN\s*NACIDO\s*SANO',
        r'A\s*OTROS\s*COLUMNA',
        r'O\s*JUANETES',
        r'ACCIDENTE',
        r'A\s*EXCLUSIONES\s*LEGRADO\s*POR\s*ABORTO',
        r'A\s*EXCLUSIONES\s*AVIACION\s*PARTICULAR',
        r'A\s*EXCLUSIONES\s*ASALTO',
        r'A\s*GASTOS\s*CUBIERTOS\s*TRANSPLANTE\s*DE\s*ORGANOS',
        r'EXCLUSIN\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO RECONOCIDOS,\s*FUERA\s*DE CONVENIO',
        r'EXCLUSION\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'A\s*GASTOS\s*CUBIERTOS\s*RECIEN\s*NACIDO\s*PREMATURO',
        r'COBERTURA\s*DE\s*DAO\s*PSIQUIATRICO',
        r'REGISTRO\s*DE\s*CONDICIONES\s*GENERALES',
        r'CLNICA\s*DE\s*LA\s*COLUMNA',
        r'CLÍNICA\s*DE\s*LA\s*COLUMNA',
        r'HERNIAS',
        r'A\s*OTROS\s*PADECIMIENTOS',
        r'A\s*GASTOS\s*CUBIERTOS\s*HONORARIOS\s*POR\s*CONSULTA\s*Y\s*PROCEDIMIENTOS\s*QUIRURGICOS',
        r'A\s*OTROS\s*CLNICA\s*DE\s*LA\s*COLUMNA',
        r'MODIFICACIONES\s*A\s*DEFINICIONES',
        r'EXCLUSIÓN\s*PRESTADORES\s*DE\s*SERVICIOS\s*MEDICOS\s*NO\s*RECONOCIDOS,\s*FUERA\s*DE\s*CONVENIO',
        r'A\s*OTROS\s*ENDOSO\s*DE\s*CONTINUIDAD\s*DE\s*NEGOCIO\s*POR\s*RENOVACIÓN',
        r'A\s*OTROS\s*ENDOSO\s*DE\s*CONTINUIDAD\s*DE\s*NEGOCIO\s*POR\s*CANCELACION\s*ANTICIPADA',
        r'MODIFICACIONES\s*A\s*GASTOS\s*CUBIERTOS\s*HONORARIOS\s*POR\s*CONSULTAS\s*MÉDICAS',
        r'MODIFICACIONES\s*A\s*GASTOS\s*CUBIERTOS\s*PADECIMIENTOS\s*PREEXISTENTES\s*CON\s*PERIODO\s*DE\s*ESPERA',
        r'MODIFICACIONES\s*A\s*OTROS\s*ESTRABISMO',
        r'A\s*EXCLUSIONES\s*DEPORTES\s*PELIGROSOS',
        r'A\s*EXCLUSIONES\s*AMPLIACION\s*COBERTURA\s*DE\s*S',
        r'A\s*EXCLUSIONES\s*MENOPAUSIA',
        r'A\s*OTROS\s*LESIONES\s*PIGMENTARIAS\s*Y\s*LUNARES',
        r'A\s*OTROS\s*ACNÉ',
        r'A\s*GASTOS\s*CUBIERTOS\s*COBERTURA\s*DE\s*DAÑO\s*PSIQUIATRICO',
        r'A\s*OTROS\s*AMIGDALAS\s*Y\s*ADENOIDES',
        r'A\s*GASTOS\s*CUBIERTOS\s*MEDICAMENTOS',
        r'A\s*EXCLUSIONES\s*ACUPUNTURISTAS',
        r'A\s*EXCLUSIONES\s*VITAMINAS\s*Y\s*COMPLEMENTOS\s*ALIMENTICIOS',
        r'MODIFICACIONES\s*A\s*GASTOS\s*CUBIERTOS',
        r'HONORARIOS\s*POR\s*CONSULTAS\s*MÉDICAS',
        r'HONORARIOS\s*POR\s*CONSULTAS\s*MEDICAS',
        r'A\s*GASTOS',
        r'HONORARIOS',
        r'POR\s*CONSULTAS',
        r'CUBIERTOS',
        r'GASTOS',
        r'ESTRBISMO',
        r'OTROS',
    ]

    # Eliminar patrones en mayúsculas
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


# Ejemplo de uso
# pdf_path = "ruta/al/archivo.pdf"
# resultado_texto, total_codigos, lista_codigos = extract_and_clean_text(pdf_path)
# print(resultado_texto)
# print("Total de códigos únicos encontrados:", total_codigos)
# print("Lista de códigos únicos:", lista_codigos)
