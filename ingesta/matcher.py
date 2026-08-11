"""
Motor de matching por clave única.
Genera claves a partir de marca+modelo+calidad para identificar productos.
"""
import re
import unicodedata


def generar_clave(categoria, marca, modelo, calidad, separador='_'):
    """
    Genera una clave única para un producto.
    
    Formato: {categoria}_{marca}_{modelo}_{calidad}
    Todo en minúsculas, sin caracteres especiales.
    """
    partes = [categoria, marca, modelo, calidad]
    
    clave = separador.join(
        normalizar_para_clave(p) for p in partes if p
    )
    
    return clave


def normalizar_para_clave(texto):
    """Normaliza un texto para usar en una clave."""
    if not texto:
        return ''
    
    texto = str(texto).lower().strip()
    
    # Normalizar caracteres
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    
    # Reemplazar caracteres no alfanuméricos por guión
    texto = re.sub(r'[^a-z0-9]', separador, texto)
    
    # Colapsar guiones múltiples
    texto = re.sub(r'_+', '_', texto)
    
    return texto.strip('_')


def calcular_similitud(clave1, clave2):
    """
    Calcula similitud entre dos claves (0.0 a 1.0).
    Útil para detectar productos casi iguales.
    """
    if not clave1 or not clave2:
        return 0.0
    
    if clave1 == clave2:
        return 1.0
    
    # Jaccard similarity sobre tokens
    tokens1 = set(clave1.split('_'))
    tokens2 = set(clave2.split('_'))
    
    interseccion = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    
    if union == 0:
        return 0.0
    
    return interseccion / union


def son_mismo_producto(clave1, clave2, umbral=0.8):
    """
    Determina dos claves representan el mismo producto.
    
    Args:
        clave1, clave2: claves a comparar
        umbral: similitud mínima para considerar match
    
    Returns:
        bool
    """
    return calcular_similitud(clave1, clave2) >= umbral
