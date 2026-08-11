# PROMPT DE CONTINUACIÓN DEL PROYECTO TECHNOSTORE

> Pegale este documento completo a la IA del sistema con el que quieras continuar.
> Le da todo el contexto del proyecto, lo que ya está hecho y lo que falta.

---

## CÓMO LEER ESTE DOCUMENTO PARA LA IA

Sos una IA que va a continuar el desarrollo de un sistema para TechnoStore, un negocio
de reventa y reparación de electrónica en Argentina. El dueño (usuario) NO SABE PROGRAMAR.
Todo paso que él deba ejecutar hay que explicárselo en lenguaje simple, sin jerga técnica.

Leé TODO este documento antes de escribir/ejecutar nada.

---

## 1. CONTEXTO DEL NEGOCIO

- Negocio: reventa y reparación de electrónica en Argentina (TechnoStore).
- Tiene proveedores: ADRICELL, PGVJ y PIÑAAPPLE (marca Apple).
- Fuente de verdad de precios: un Excel maestro llamado `TechnoStore.xlsx` con una
  pestaña por proveedor.
- El dueño jamás edita el Excel a mano. Cuando cambian precios, vuelve a subir los
  archivos ORIGINALES de cada proveedor (Excel, PDF, foto o texto) y un sistema debe:
  1. Interpretarlo con IA.
  2. Comparar contra lo existente.
  3. Mostrarle un reporte de cambios propuestos ANTES de aplicar.
  4. Aplicar solo cuando él aprueba.

## 2. QUÉ YA ESTÁ CONSTRUIDO (INVENTARIO ACTUAL DEL PROYECTO)

### Archivos raíz (`C:\Users\Usuario\Desktop\listas de precios\`)

| Archivo | Descripción |
|---------|-------------|
| `TechnoStore.xlsx` | Excel maestro de precios (fuente de verdad). 13 pestañas. |
| `productos.json` | Exportado del Excel. ~1.870 productos. Usado por la web. |
| `index.html` | Web pública que muestra precios de venta al cliente. |
| `servidor.bat` | Inicia un servidor local para ver la web (puerto 8081). |
| `config.json` | Configuración centralizada del sistema de ingesta. |
| `LEEME_INGESTA.md` | Documentación de uso del sistema de ingesta. |

### Carpeta `ingesta/` (sistema de ingesta de listas de proveedores)

| Archivo | Descripción |
|---------|-------------|
| `__init__.py` | Marcador de paquete Python. |
| `main.py` | Punto de entrada. Orquesta: interpretar → normalizar → comparar → reporte. |
| `ai_provider.py` | Interfaz IA proveedor-agnóstico (OpenAI-compatible). |
| `normalizer.py` | Normaliza datos crudos a estructura común. |
| `matcher.py` | Genera claves únicas y compara productos (similarity matching). |
| `excel_io.py` | Lee y escribe `TechnoStore.xlsx`. |
| `report.py` | Genera reportes de cambios propuestos (texto plano para Telegram/WhatsApp). |

## 3. DECISIONES DE ARQUITECTURA YA TOMADAS (NO CAMBIAR SIN EXPLICAR ANTES)

1. **Excel = fuente de verdad.** Todo cambio de costo/stock se hace SOLO en el Excel maestro.
2. **Base de datos privada:** Firestore en el proyecto Firebase existente `local-81a46`
   (región `southamerica-east1`). Allí también corre el backend de ecommerce y la
   integración con AFIP del negocio.
3. **Backend:** Firebase Cloud Functions (mismo proyecto `local-81a46`). NO servidor propio.
   - Ruta pública `GET /precios`: sin auth. Devuelve SOLO categoria, marca, modelo,
     calidad, stock (binario disponible/sin stock), precio_venta. **NUNCA costo ni margen**.
   - Ruta privada `GET /precios-admin`: protegida por URL secreta (sin login complejo).
     Devuelve todo, incluyendo costo y margen.
4. **Sitio público:** `index.html` alojado en Firebase Hosting (mismo proyecto).
   El cliente consulta la ruta pública. Esta es la URL que se comparte con clientes.
5. **Stock a clientes:** solo "Disponible" / "Sin stock". NUNCA el número real.
6. **Sincronización Excel → base:** se dispara SOLO cuando el dueño sube y aprueba una
   lista nueva. NO hay sincronización por reloj/intervalo.
7. **Precio vivo:** el precio final al cliente se recalcula con la cotización
   USDT/ARS del momento cada vez que alguien abre la página.

## 4. PROVEEDORES Y MONEDAS

| Proveedor | Pestañas | Moneda en el Excel consolidado |
|-----------|----------|-------------------------------|
| ADRICELL | `LISTA MODULO ADRICELL`, `BATERIAS ADRICELL`, `COMPONENTES ADRICELL` | Pesos (ARS) |
| PGVJ | `PGVJ - MODULOS GOSTTER`, `PGVJ - MODULOS ORIGINALES`, `PGVJ - REPUESTOS APPLE`, `PGVJ - PLACAS DE CARGA`, `PGVJ - BATERIAS`, `PGVJ - TAPAS`, `PGVJ - PLACAS MAIN`, `PGVJ - PARTES VARIAS`, `PGVJ - ACCESORIOS` | Pesos (ARS) |
| PIÑAAPPLE | `PIÑAAPPLE` | Dólares (USD) — única que carga precio directo en USD |

⚠️ IMPORTANTE: Las listas ORIGINALES de cada proveedor pueden venir en otra moneda que la
del Excel consolidado. Cuando se sube una lista cruda, hay que CONFIRMAR la moneda con el
dueño antes de asumir.

Stock: solo `LISTA MODULO ADRICELL` tiene columna de stock explícita. En las demás
pestañas no hay stock. Hay que contemplar que los proveedores a veces NO mandan stock.

## 5. MÁRGENES CONFIGURADOS

- Margen general: **30%**.
- Productos baratos (precio < $30.000 ARS): **40%**.
- Umbral "producto barato": $30.000 ARS.
- Producto nuevo (sin revisión previa): **30%** (margen general por defecto).

## 6. ESTRUCTURA COMÚN DE PRODUCTO (normalizada)

```json
{
  "proveedor": "PGVJ",
  "marca": "SAMSUNG",
  "modelo": "A13",
  "calidad_o_color": "CON LENTE NEGRO",
  "precio": 11472,
  "moneda": "ARS",
  "stock": null
}
```

Reglas de normalización:
- Todo en mayúsculas.
- Sin caracteres raros (ñ→n, acentos eliminados).
- Precio como número puro (sin $, sin separadores).

## 7. CLAVE DE MATCHING (decide si producto es nuevo o actualización)

Formato: `{categoria}_{marca}_{modelo}_{calidad}` — todo en minúsculas, sin caracteres
raros, separado por guiones bajos.

Ejemplo: `tapas_samsung_a13_con_lente_negro`

- Si la clave ya existe en la pestaña del proveedor → es una ACTUALIZACIÓN.
- Si la clave NO existe → es un PRODUCTO NUEVO (requiere aprobación manual del dueño).

## 8. FLUJO DEL PASO DE INGESTA (YA PROGRAMADO, PRIORIDAD MÁXIMA DEL PROYECTO)

```
PASO 1: El dueño sube el archivo crudo (Excel/PDF/foto/texto)
        ↓
PASO 2: El sistema detecta el archivo nuevo
        ↓
PASO 3: La IA interpreta el archivo → estructura común
        - Excel: se lee con openpyxl + prompt a IA
        - PDF: se extrae texto con PyMuPDF + prompt a IA
        - Foto: se manda como imagen a la IA (visión)
        - Texto: se manda a la IA
        ↓
PASO 4: Detección de proveedor
        - Por contenido (palabras clave tipo "PGVJ", "ADRICELL")
        - Si no puede, le pregunta al dueño
        ↓
PASO 5: Comparación contra Excel maestro por clave
        - Clasifica: actualización / producto nuevo / sin cambios
        ↓
PASO 6: Genera reporte con cambios propuestos
        ↓
PASO 7: El dueño aprueba ("sí" / "aplicar")
        ↓
PASO 8: Se actualiza TechnoStore.xlsx
        ↓
PASO 9: Se dispara la sincronización Excel → Firestore → web pública actualizada
```

## 9. REGLAS NO NEGOCIABLES (RESPETAR SIEMPRE)

1. **El costo y el margen jamás deben ser visibles ni inferibles desde la página
   pública** — ni en el HTML, ni en JS, ni en respuestas de red que el cliente pueda
   inspeccionar. Ante la duda, preguntar antes de implementar.
2. Todo texto de interfaz en español.
3. Cualquier cambio automático al Excel debe quedar registrado y revisable por el dueño
   antes o después de aplicarse. No hay cambios silenciosos.
4. Explicar cada paso que el dueño deba ejecutar en lenguaje simple (no sabe programar).
5. Preferir reusar lo existente (Firebase `local-81a46`) antes que sumar servicios nuevos.
   Si algo nuevo es claramente mejor, explicar el trade-off.

## 10. ESTADO ACTUAL / QUÉ FALTA

### Ya hecho y funcionando
- Sistema de ingesta completo (carpeta `ingesta/`).
- Configuración centralizada (`config.json`).
- Documentación de uso (`LEEME_INGESTA.md`).

### Pendiente / próximo paso sugerido
1. **Probar el sistema de ingesta** con un archivo de ejemplo una vez configurada la API
   de IA en `config.json` (campo `ai.api_key`).
2. **Configurar la API de IA** (proveedor-agnóstico, OpenAI-compatible).
3. **Conectar el reporte a un bot existente** del dueño (Telegram y/o WhatsApp). El dueño
   tiene un bot propio ya programado; pasará sus datos técnicos cuando corresponda.
4. **Vigilar la carpeta de entrada** (`proveedores/`) automáticamente para detectar
   archivos nuevos (configurable, NO bloqueante — el canal principal de entrada será el bot).
5. **Script de sincronización Excel → Firestore.**
6. **Backend con las dos rutas** (`GET /precios` público y `GET /precios-admin` privado).
7. **`index.html` actualizado** para consumir la ruta pública (hoy lee `productos.json`
   directo).
8. **Publicación en Firebase Hosting.**
9. **Panel admin privado** (puede ser la misma web corriendo local, que consume la ruta
   privada con la URL secreta).

## 11. TECNOLOGÍAS EN USO (resumen)

- Python 3 + openpyxl + PyMuPDF (sistema de ingesta, local).
- JSON estático (web actual, `productos.json`).
- Cualquier API de IA compatible con OpenAI (configurable en `config.json`).
- Firebase `local-81a46`, región `southamerica-east1` (Cloud Functions + Firestore +
  Hosting) para la etapa de publicación.

## 12. PENDIENTES DE RESPUESTA DEL DUEÑO (preguntar antes de avanzar en esos temas)

1. ¿Cuál API de IA va a usar? (No está definido aún. El sistema es proveedor-agnóstico.)
2. Datos técnicos de su bot de Telegram/WhatsApp (los pasará cuando lleguemos a esa parte).
3. Preferencias de publicación (dominios, variables de entorno, claves).

---

## INSTRUCCIONES FINALES PARA LA IA QUE CONTINÚA

1. Leé este documento completo.
2. Reconocé el contexto y el estado del proyecto.
3. Si vas a tocar el Excel maestro, primero mostrale al dueño QUÉ vas a cambiar.
4. Explicá todo en lenguaje simple, en español.
5. Si un tema requiere una decisión del dueño que no está resuelta en este documento,
   preguntálo ANTES de escribir código.