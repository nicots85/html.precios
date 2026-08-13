"""
Punto de entrada del sistema de ingesta.
Orquesta: interpretar archivo → normalizar → comparar → generar reporte.
"""
import os
import sys
import json
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

from ingesta.ai_provider import AIProvider
from ingesta.normalizer import normalizar_lista, limpiar_texto
from ingesta.matcher import generar_clave, son_mismo_producto
from ingesta.excel_io import ExcelMaestro
from ingesta.report import ReporteCambios


def detectar_proveedor(productos, config, texto_archivo=""):
    """
    Detecta de qué proveedor viene una lista de productos.
    Busca palabras claves primero en el texto del archivo (header/footer)
    y después en los productos.

    Args:
        productos: lista de productos parseados
        config: configuración con info de proveedores
        texto_archivo: texto crudo del archivo (PDF/Excel)

    Returns:
        str o None: nombre del proveedor detectado
    """
    proveedores_config = config.get('proveedores', {})
    scores = {nombre: 0 for nombre in proveedores_config}

    # 1) Buscar en el texto crudo del archivo (header/footer)
    if texto_archivo:
        texto_upper = texto_archivo.upper()
        for nombre, info in proveedores_config.items():
            for palabra_clave in info.get('palabras_clave', []):
                if palabra_clave.upper() in texto_upper:
                    # Match en header/texto es muy fuerte
                    scores[nombre] += 50

    # 2) Buscar en los productos (menos peso)
    for producto in productos:
        texto = f"{producto.get('marca', '')} {producto.get('modelo', '')} {producto.get('calidad_o_color', '')}"
        texto = texto.upper()
        for nombre, info in proveedores_config.items():
            for palabra_clave in info.get('palabras_clave', []):
                if palabra_clave.upper() in texto:
                    scores[nombre] += 1

    if scores:
        mejor = max(scores, key=scores.get)
        if scores[mejor] > 0:
            return mejor

    return None


def procesar_archivo(ruta_archivo, config_path='config.json', moneda_forzada=None):
    """
    Procesa un archivo crudo de proveedor.
    
    Args:
        ruta_archivo: path al archivo
        config_path: path al config.json
        moneda_forzada: 'ARS', 'USD', o None para auto-detectar
    
    Returns:
        list[ReporteCambios]: reportes por pestaña
    """
    # Cargar config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Detectar tipo de archivo
    extension = os.path.splitext(ruta_archivo)[1].lower()
    
    if extension in ('.xlsx', '.xls'):
        tipo = 'excel'
    elif extension == '.pdf':
        tipo = 'pdf'
    elif extension in ('.png', '.jpg', '.jpeg'):
        tipo = 'imagen'
    elif extension == '.txt':
        tipo = 'texto'
    else:
        print(f"ERROR: Formato no soportado: {extension}")
        return []
    
    print(f"Procesando: {ruta_archivo}")
    print(f"Tipo: {tipo}")
    
    # Interpretar archivo con IA
    ai = AIProvider(config_path)
    
    if not ai.api_key or ai.api_key == 'TU_API_KEY_AQUI':
        print("ERROR: No se configuró la clave de IA en config.json")
        print("Editá config.json y poné tu API Key en 'ai.api_key'")
        return []
    
    print("Interpretando archivo con IA...")
    productos_crudos = ai.interpretar_archivo(ruta_archivo, tipo)
    
    if not productos_crudos:
        print("No se pudieron extraer productos del archivo.")
        return []
    
    print(f"Productos extraídos: {len(productos_crudos)}")

    # Detectar proveedor (usa texto crudo del archivo)
    texto_archivo = ai.obtener_texto_crudo(ruta_archivo, tipo)
    proveedor = detectar_proveedor(productos_crudos, config, texto_archivo)
    
    if proveedor:
        print(f"Proveedor detectado: {proveedor}")
    else:
        print("No se pudo detectar el proveedor automáticamente.")
        print("Los productos se procesarán pero necesitarás indicar el proveedor.")
        proveedor = None
    
    # Aplicar moneda forzada si corresponde
    if moneda_forzada:
        for p in productos_crudos:
            p['moneda'] = moneda_forzada
    
    # Normalizar productos
    productos_normalizados = normalizar_lista(productos_crudos, proveedor)
    print(f"Productos válidos: {len(productos_normalizados)}")
    
    if not productos_normalizados:
        print("No quedaron productos válidos después de normalizar.")
        return []
    
    # Comparar contra Excel maestro
    excel_path = config.get('excel_maestro', 'TechnoStore.xlsx')
    
    if not proveedor:
        print("\nNo se detectó proveedor automáticamente.")
        print("Usando proveedor por defecto: PGVJ")
        proveedor = 'PGVJ'
    
    pestanas = config.get('proveedores', {}).get(proveedor, {}).get('pestanas', [])
    
    if not pestanas:
        print(f"No hay pestañas configuradas para {proveedor}.")
        return []
    
    reportes = []
    
    with ExcelMaestro(excel_path, config_path) as excel:
        for pestana in pestanas:
            print(f"\nComparando con pestaña: {pestana}")
            
            # Leer productos existentes
            productos_existentes = excel.leer_pestana(pestana)
            print(f"  Existentes: {len(productos_existentes)}")
            
            # Generar claves para existentes
            existentes_por_clave = {}
            for prod in productos_existentes:
                clave = generar_clave('', prod.get('marca', ''), prod.get('modelo', ''), prod.get('calidad_o_color', ''))
                existentes_por_clave[clave] = prod
            
            # Crear reporte
            reporte = ReporteCambios(proveedor, pestana)
            
            # Comparar cada producto nuevo
            for prod_nuevo in productos_normalizados:
                clave_nuevo = generar_clave('', prod_nuevo.get('marca', ''), prod_nuevo.get('modelo', ''), prod_nuevo.get('calidad_o_color', ''))
                
                # Buscar match exacto
                if clave_nuevo in existentes_por_clave:
                    prod_existente = existentes_por_clave[clave_nuevo]
                    
                    # Comparar precios
                    cambios = {}
                    
                    precio_viejo = prod_existente.get('precio_pesos')
                    precio_nuevo = prod_nuevo.get('precio')
                    moneda_nuevo = prod_nuevo.get('moneda', 'ARS')
                    
                    # Convertir si es necesario
                    if moneda_nuevo == 'USD':
                        # Buscar tasa de cambio o usar la del config
                        precio_nuevo_ars = precio_nuevo * 1586  # TODO: tasa dinámica
                    else:
                        precio_nuevo_ars = precio_nuevo
                    
                    if precio_viejo and precio_nuevo_ars:
                        diferencia = abs(precio_viejo - precio_nuevo_ars)
                        if diferencia > 10:  # Margen de ruido
                            cambios['precio'] = (precio_viejo, precio_nuevo_ars)
                    
                    # Comparar stock
                    stock_viejo = prod_existente.get('stock')
                    stock_nuevo = prod_nuevo.get('stock')
                    
                    if stock_nuevo is not None and stock_viejo != stock_nuevo:
                        cambios['stock'] = (stock_viejo, stock_nuevo)
                    
                    if cambios:
                        reporte.agregar_actualizacion(prod_existente, prod_nuevo, cambios)
                    else:
                        reporte.sin_cambios.append(prod_nuevo)
                else:
                    # Producto nuevo
                    reporte.agregar_nuevo(prod_nuevo)
            
            if reporte.hay_cambios():
                reportes.append(reporte)
                print(f"  Cambios detectados: {len(reporte.actualizaciones)} actualizaciones, {len(reporte.productos_nuevos)} nuevos")
            else:
                print(f"  Sin cambios en esta pestaña.")
    
    return reportes


def aplicar_cambios(reportes, config_path='config.json'):
    """
    Aplica los cambios aprobados al Excel maestro.
    
    Args:
        reportes: lista de ReporteCambios aprobados
        config_path: path al config.json
    
    Returns:
        bool: True si se aplicaron correctamente
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    excel_path = config.get('excel_maestro', 'TechnoStore.xlsx')
    
    config_margenes = config.get('margenes', {})
    margen_general = config_margenes.get('general', 0.30)

    with ExcelMaestro(excel_path, config_path) as excel:
        for reporte in reportes:
            pestana = reporte.pestana
            ws = excel.wb[pestana] if pestana in excel.wb.sheetnames else None
            cols = excel._find_columns(ws, excel._find_header_row(ws)) if ws else {}
            
            # Aplicar actualizaciones
            for item in reporte.actualizaciones:
                prod_viejo = item['producto_viejo']
                fila = prod_viejo['fila']
                prod_nuevo = item['producto_nuevo']
                
                for campo, (viejo, nuevo) in item['cambios'].items():
                    if campo == 'precio':
                        # Actualizar columna de precio correspondiente
                        moneda_nuevo = prod_nuevo.get('moneda', 'ARS')
                        if moneda_nuevo == 'USD' and 'precio_dolar' in cols:
                            excel.actualizar_producto(pestana, fila, cols['precio_dolar'], nuevo)
                        elif 'precio_pesos' in cols:
                            excel.actualizar_producto(pestana, fila, cols['precio_pesos'], nuevo)
                        # Recalcular venta con margen general
                        if 'venta' in cols:
                            excel.actualizar_producto(pestana, fila, cols['venta'], round(nuevo * (1 + margen_general)))
                    elif campo == 'stock':
                        if 'stock' in cols:
                            excel.actualizar_producto(pestana, fila, cols['stock'], nuevo)
            
            # Agregar productos nuevos
            for prod_nuevo in reporte.productos_nuevos:
                excel.agregar_producto(pestana, prod_nuevo)
        
        # Guardar cambios
        excel.guardar()
    
    print("Cambios aplicados correctamente.")
    return True


def regenerar_productos_json(config_path='config.json'):
    """
    Regenera productos.json desde el Excel maestro actualizado.
    Así la web (hosting estático) refleja los nuevos precios.
    """
    try:
        import subprocess
        res = subprocess.run(
            [sys.executable, 'backend/generar_productos.py'],
            capture_output=True, text=True, encoding='utf-8'
        )
        if res.returncode == 0:
            print("productos.json regenerado correctamente.")
            return True
        else:
            print(f"Error generando productos.json: {res.stderr}")
            return False
    except Exception as e:
        print(f"Error al regenerar productos.json: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python -m ingesta.main <archivo> [moneda]")
        print("  archivo: ruta al Excel/PDF/imagen del proveedor")
        print("  moneda: ARS o USD (opcional, si no se detecta)")
        sys.exit(1)
    
    archivo = sys.argv[1]
    moneda = sys.argv[2].upper() if len(sys.argv) > 2 else None
    
    if not os.path.exists(archivo):
        print(f"No se encontró el archivo: {archivo}")
        sys.exit(1)
    
    reportes = procesar_archivo(archivo, moneda_forzada=moneda)
    
    if reportes:
        print("\n" + "="*50)
        print("RESUMEN DE CAMBIOS")
        print("="*50)
        
        for reporte in reportes:
            print(reporte.generar_texto())
            print()

        # Aplicar cambios si vienen aprobados (flag --aplicar)
        if '--aplicar' in sys.argv:
            exito = aplicar_cambios(reportes)
            if exito:
                regenerar_productos_json()
                print("\nSe regeneró productos.json. Re-desplegá el hosting:")
                print("  firebase deploy --only hosting")
        else:
            print("\nPara aplicar los cambios al Excel y regenerar productos.json:")
            print("  python -m ingesta.main <archivo> --aplicar")
    else:
        print("\nNo se generaron reportes.")
