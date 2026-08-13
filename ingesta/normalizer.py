"""
Normalizador de datos.
Convierte productos crudos de la IA a estructura común limpia.
"""
import re
import unicodedata


def limpiar_texto(texto):
    """Limpia y normaliza un texto."""
    if not texto:
        return ''
    
    texto = str(texto).strip().upper()
    
    # Normalizar caracteres (ñ→n, acentos→vocales)
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    
    # Limpiar caracteres raros excepto espacios y guiones
    texto = re.sub(r'[^A-Z0-9\s\-\/\.]', '', texto)
    
    # Normalizar espacios
    texto = ' '.join(texto.split())
    
    return texto


def limpiar_precio(valor):
    """Extrae un número de precio desde cualquier formato."""
    if valor is None:
        return None
    
    if isinstance(valor, (int, float)):
        return float(valor)
    
    texto = str(valor).strip()
    
    # Quitar símbolos comunes
    texto = texto.replace('$', '').replace('U$S', '').replace('USD', '').replace('ARS', '')
    texto = texto.replace(' ', '')
    
    # Manejar formato numérico
    if ',' in texto and '.' in texto:
        # Determinar cuál es decimal
        if texto.rindex(',') > texto.rindex('.'):
            # Formato: 1.234,56
            texto = texto.replace('.', '').replace(',', '.')
        else:
            # Formato: 1,234.56
            texto = texto.replace(',', '')
    elif ',' in texto:
        # Puede ser decimal o separador de miles
        partes = texto.split(',')
        if len(partes[-1]) == 2 and len(partes) == 2:
            # Probable decimal: 1234,56
            texto = texto.replace(',', '.')
        else:
            # Separador de miles
            texto = texto.replace(',', '')
    
    try:
        return float(texto)
    except:
        return None


def normalizar_producto(producto_crudado, proveedor=None):
    """
    Normaliza un producto crudo de la IA a estructura común.
    
    Args:
        producto_crudado: dict con datos crudos
        proveedor: nombre del proveedor si ya se dedujo
    
    Returns:
        dict normalizado o None si es inválido
    """
    marca = limpiar_texto(producto_crudado.get('marca', ''))
    modelo = limpiar_texto(producto_crudado.get('modelo', ''))
    calidad = limpiar_texto(producto_crudado.get('calidad_o_color', ''))
    precio = limpiar_precio(producto_crudado.get('precio'))
    moneda = str(producto_crudado.get('moneda', 'ARS')).strip().upper()
    stock_raw = producto_crudado.get('stock', None)
    
    # Validaciones mínimas
    if not modelo and not marca:
        return None
    
    if precio is None or precio <= 0:
        return None
    
    if moneda not in ('ARS', 'USD'):
        moneda = 'ARS'
    
    # Stock
    stock = None
    if stock_raw is not None:
        try:
            stock = int(float(str(stock_raw).strip()))
        except:
            stock = None
    
    # Si la marca está vacía pero el modelo tiene marca conocida, separar
    marcas_conocidas = [
        'SAMSUNG', 'IPHONE', 'MOTOROLA', 'HUAWEI', 'LG', 'SONY',
        'NOKIA', 'TCL', 'ALCATEL', 'XIAOMI', 'ZTE', 'JBL', 'GOSTTER',
        'APPLE', 'INFINIX', 'REALME', 'OPPO', 'ONEPLUS', 'HONOR', 'NOTHING',
        'GOOGLE', 'ASUS', 'LENOVO', 'HP', 'DELL'
    ]

    if not marca and modelo:
        for m in marcas_conocidas:
            if modelo.startswith(m):
                marca = m
                modelo = modelo[len(m):].strip()
                break

    # Limpiar prefijos de tipo del modelo (ej: "MODULO J1 ACE" → "J1 ACE")
    prefijos_tipo = ['MODULO ', 'BATERIA ', 'TAPA ', 'PLACA ', 'CARGADOR ',
                     'FLEX ', 'CABLE ', 'ADAPTADOR ', 'AURICULAR ', 'VIDRIO ']
    for p in prefijos_tipo:
        if modelo.upper().startswith(p):
            modelo = modelo[len(p):].strip()
            break
    
    # Construir producto normalizado
    return {
        'proveedor': proveedor,
        'marca': marca or '',
        'modelo': modelo,
        'calidad_o_color': calidad,
        'precio': precio,
        'moneda': moneda,
        'stock': stock
    }


def normalizar_lista(productos_crudos, proveedor=None):
    """
    Normaliza una lista de productos crudos.
    
    Returns:
        list[dict]: productos válidos normalizados
    """
    resultados = []
    for p in productos_crudos:
        normalizado = normalizar_producto(p, proveedor)
        if normalizado:
            resultados.append(normalizado)
    return resultados
