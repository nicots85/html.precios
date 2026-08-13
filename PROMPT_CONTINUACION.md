# PROMPT DE CONTINUACIÃ“N DEL PROYECTO TECHNOSTORE

> Pegale este documento completo a la IA del sistema con el que quieras continuar.
> Le da todo el contexto del proyecto, lo que ya estÃ¡ hecho y lo que falta.

---

## CÃ“MO LEER ESTE DOCUMENTO PARA LA IA

Sos una IA que va a continuar el desarrollo de un sistema para TechnoStore, un negocio
de reventa y reparaciÃ³n de electrÃ³nica en Argentina. El dueÃ±o (usuario) NO SABE PROGRAMAR.
Todo paso que Ã©l deba ejecutar hay que explicÃ¡rselo en lenguaje simple, sin jerga tÃ©cnica.

LeÃ© TODO este documento antes de escribir/ejecutar nada.

---

## 1. CONTEXTO DEL NEGOCIO

- Negocio: reventa y reparaciÃ³n de electrÃ³nica en Argentina (TechnoStore).
- Tiene proveedores: ADRICELL, PGVJ y PIÃ‘AAPPLE (marca Apple).
- Fuente de verdad de precios: un Excel maestro llamado `TechnoStore.xlsx` con una
  pestaÃ±a por proveedor.
- El dueÃ±o jamÃ¡s edita el Excel a mano. Cuando cambian precios, vuelve a subir los
  archivos ORIGINALES de cada proveedor (Excel, PDF, foto o texto) y un sistema debe:
  1. Interpretarlo con IA.
  2. Comparar contra lo existente.
  3. Mostrarle un reporte de cambios propuestos ANTES de aplicar.
  4. Aplicar solo cuando Ã©l aprueba.

## 2. QUÃ‰ YA ESTÃ CONSTRUIDO (INVENTARIO ACTUAL DEL PROYECTO)

### Archivos raÃ­z (`C:\Users\Usuario\Desktop\listas de precios\`)

| Archivo | DescripciÃ³n |
|---------|-------------|
| `TechnoStore.xlsx` | Excel maestro de precios (fuente de verdad). 13 pestaÃ±as. |
| `productos.json` | Exportado del Excel. ~1.870 productos. Usado por la web. |
| `index.html` | Web pÃºblica que muestra precios de venta al cliente. |
| `servidor.bat` | Inicia un servidor local para ver la web (puerto 8081). |
| `config.json` | ConfiguraciÃ³n centralizada del sistema de ingesta. |
| `LEEME_INGESTA.md` | DocumentaciÃ³n de uso del sistema de ingesta. |

### Carpeta `ingesta/` (sistema de ingesta de listas de proveedores)

| Archivo | DescripciÃ³n |
|---------|-------------|
| `__init__.py` | Marcador de paquete Python. |
| `main.py` | Punto de entrada. Orquesta: interpretar â†’ normalizar â†’ comparar â†’ reporte. |
| `ai_provider.py` | Interfaz IA proveedor-agnÃ³stico (OpenAI-compatible). |
| `normalizer.py` | Normaliza datos crudos a estructura comÃºn. |
| `matcher.py` | Genera claves Ãºnicas y compara productos (similarity matching). |
| `excel_io.py` | Lee y escribe `TechnoStore.xlsx`. |
| `report.py` | Genera reportes de cambios propuestos (texto plano para Telegram/WhatsApp). |

## 3. DECISIONES DE ARQUITECTURA YA TOMADAS (NO CAMBIAR SIN EXPLICAR ANTES)

1. **Excel = fuente de verdad.** Todo cambio de costo/stock se hace SOLO en el Excel maestro.
2. **Base de datos privada:** Firestore en el proyecto Firebase existente `technostore-db`
   (regiÃ³n `southamerica-east1`). AllÃ­ tambiÃ©n corre el backend de ecommerce y la
   integraciÃ³n con AFIP del negocio.
3. **Backend:** Firebase Cloud Functions (mismo proyecto `technostore-db`). NO servidor propio.
   - Ruta pÃºblica `GET /precios`: sin auth. Devuelve SOLO categoria, marca, modelo,
     calidad, stock (binario disponible/sin stock), precio_venta. **NUNCA costo ni margen**.
   - Ruta privada `GET /precios-admin`: protegida por URL secreta (sin login complejo).
     Devuelve todo, incluyendo costo y margen.
4. **Sitio pÃºblico:** `index.html` alojado en Firebase Hosting (mismo proyecto).
   El cliente consulta la ruta pÃºblica. Esta es la URL que se comparte con clientes.
5. **Stock a clientes:** solo "Disponible" / "Sin stock". NUNCA el nÃºmero real.
6. **SincronizaciÃ³n Excel â†’ base:** se dispara SOLO cuando el dueÃ±o sube y aprueba una
   lista nueva. NO hay sincronizaciÃ³n por reloj/intervalo.
7. **Precio vivo:** el precio final al cliente se recalcula con la cotizaciÃ³n
   USDT/ARS del momento cada vez que alguien abre la pÃ¡gina.

## 4. PROVEEDORES Y MONEDAS

| Proveedor | PestaÃ±as | Moneda en el Excel consolidado |
|-----------|----------|-------------------------------|
| ADRICELL | `LISTA MODULO ADRICELL`, `BATERIAS ADRICELL`, `COMPONENTES ADRICELL` | Pesos (ARS) |
| PGVJ | `PGVJ - MODULOS GOSTTER`, `PGVJ - MODULOS ORIGINALES`, `PGVJ - REPUESTOS APPLE`, `PGVJ - PLACAS DE CARGA`, `PGVJ - BATERIAS`, `PGVJ - TAPAS`, `PGVJ - PLACAS MAIN`, `PGVJ - PARTES VARIAS`, `PGVJ - ACCESORIOS` | Pesos (ARS) |
| PIÃ‘AAPPLE | `PIÃ‘AAPPLE` | DÃ³lares (USD) â€” Ãºnica que carga precio directo en USD |

âš ï¸ IMPORTANTE: Las listas ORIGINALES de cada proveedor pueden venir en otra moneda que la
del Excel consolidado. Cuando se sube una lista cruda, hay que CONFIRMAR la moneda con el
dueÃ±o antes de asumir.

Stock: solo `LISTA MODULO ADRICELL` tiene columna de stock explÃ­cita. En las demÃ¡s
pestaÃ±as no hay stock. Hay que contemplar que los proveedores a veces NO mandan stock.

## 5. MÃRGENES CONFIGURADOS

- Margen general: **30%**.
- Productos baratos (precio < $30.000 ARS): **40%**.
- Umbral "producto barato": $30.000 ARS.
- Producto nuevo (sin revisiÃ³n previa): **30%** (margen general por defecto).

## 6. ESTRUCTURA COMÃšN DE PRODUCTO (normalizada)

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

Reglas de normalizaciÃ³n:
- Todo en mayÃºsculas.
- Sin caracteres raros (Ã±â†’n, acentos eliminados).
- Precio como nÃºmero puro (sin $, sin separadores).

## 7. CLAVE DE MATCHING (decide si producto es nuevo o actualizaciÃ³n)

Formato: `{categoria}_{marca}_{modelo}_{calidad}` â€” todo en minÃºsculas, sin caracteres
raros, separado por guiones bajos.

Ejemplo: `tapas_samsung_a13_con_lente_negro`

- Si la clave ya existe en la pestaÃ±a del proveedor â†’ es una ACTUALIZACIÃ“N.
- Si la clave NO existe â†’ es un PRODUCTO NUEVO (requiere aprobaciÃ³n manual del dueÃ±o).

## 8. FLUJO DEL PASO DE INGESTA (YA PROGRAMADO, PRIORIDAD MÃXIMA DEL PROYECTO)

```
PASO 1: El dueÃ±o sube el archivo crudo (Excel/PDF/foto/texto)
        â†“
PASO 2: El sistema detecta el archivo nuevo
        â†“
PASO 3: La IA interpreta el archivo â†’ estructura comÃºn
        - Excel: se lee con openpyxl + prompt a IA
        - PDF: se extrae texto con PyMuPDF + prompt a IA
        - Foto: se manda como imagen a la IA (visiÃ³n)
        - Texto: se manda a la IA
        â†“
PASO 4: DetecciÃ³n de proveedor
        - Por contenido (palabras clave tipo "PGVJ", "ADRICELL")
        - Si no puede, le pregunta al dueÃ±o
        â†“
PASO 5: ComparaciÃ³n contra Excel maestro por clave
        - Clasifica: actualizaciÃ³n / producto nuevo / sin cambios
        â†“
PASO 6: Genera reporte con cambios propuestos
        â†“
PASO 7: El dueÃ±o aprueba ("sÃ­" / "aplicar")
        â†“
PASO 8: Se actualiza TechnoStore.xlsx
        â†“
PASO 9: Se dispara la sincronizaciÃ³n Excel â†’ Firestore â†’ web pÃºblica actualizada
```

## 9. REGLAS NO NEGOCIABLES (RESPETAR SIEMPRE)

1. **El costo y el margen jamÃ¡s deben ser visibles ni inferibles desde la pÃ¡gina
   pÃºblica** â€” ni en el HTML, ni en JS, ni en respuestas de red que el cliente pueda
   inspeccionar. Ante la duda, preguntar antes de implementar.
2. Todo texto de interfaz en espaÃ±ol.
3. Cualquier cambio automÃ¡tico al Excel debe quedar registrado y revisable por el dueÃ±o
   antes o despuÃ©s de aplicarse. No hay cambios silenciosos.
4. Explicar cada paso que el dueÃ±o deba ejecutar en lenguaje simple (no sabe programar).
5. Preferir reusar lo existente (Firebase `technostore-db`) antes que sumar servicios nuevos.
   Si algo nuevo es claramente mejor, explicar el trade-off.

## 10. ESTADO ACTUAL / QUÃ‰ FALTA

### Ya hecho y funcionando
- Sistema de ingesta completo (carpeta `ingesta/`).
- ConfiguraciÃ³n centralizada (`config.json`).
- DocumentaciÃ³n de uso (`LEEME_INGESTA.md`).

### Pendiente / prÃ³ximo paso sugerido
1. **Probar el sistema de ingesta** con un archivo de ejemplo una vez configurada la API
   de IA en `config.json` (campo `ai.api_key`).
2. **Configurar la API de IA** (proveedor-agnÃ³stico, OpenAI-compatible).
3. **Conectar el reporte a un bot existente** del dueÃ±o (Telegram y/o WhatsApp). El dueÃ±o
   tiene un bot propio ya programado; pasarÃ¡ sus datos tÃ©cnicos cuando corresponda.
4. **Vigilar la carpeta de entrada** (`proveedores/`) automÃ¡ticamente para detectar
   archivos nuevos (configurable, NO bloqueante â€” el canal principal de entrada serÃ¡ el bot).
5. **Script de sincronizaciÃ³n Excel â†’ Firestore.**
6. **Backend con las dos rutas** (`GET /precios` pÃºblico y `GET /precios-admin` privado).
7. **`index.html` actualizado** para consumir la ruta pÃºblica (hoy lee `productos.json`
   directo).
8. **PublicaciÃ³n en Firebase Hosting.**
9. **Panel admin privado** (puede ser la misma web corriendo local, que consume la ruta
   privada con la URL secreta).

## 11. TECNOLOGÃAS EN USO (resumen)

- Python 3 + openpyxl + PyMuPDF (sistema de ingesta, local).
- JSON estÃ¡tico (web actual, `productos.json`).
- Cualquier API de IA compatible con OpenAI (configurable en `config.json`).
- Firebase `technostore-db`, regiÃ³n `southamerica-east1` (Cloud Functions + Firestore +
  Hosting) para la etapa de publicaciÃ³n.

## 12. PENDIENTES DE RESPUESTA DEL DUEÃ‘O (preguntar antes de avanzar en esos temas)

1. Â¿CuÃ¡l API de IA va a usar? (No estÃ¡ definido aÃºn. El sistema es proveedor-agnÃ³stico.)
2. Datos tÃ©cnicos de su bot de Telegram/WhatsApp (los pasarÃ¡ cuando lleguemos a esa parte).
3. Preferencias de publicaciÃ³n (dominios, variables de entorno, claves).

---

## INSTRUCCIONES FINALES PARA LA IA QUE CONTINÃšA

1. LeÃ© este documento completo.
2. ReconocÃ© el contexto y el estado del proyecto.
3. Si vas a tocar el Excel maestro, primero mostrale al dueÃ±o QUÃ‰ vas a cambiar.
4. ExplicÃ¡ todo en lenguaje simple, en espaÃ±ol.
5. Si un tema requiere una decisiÃ³n del dueÃ±o que no estÃ¡ resuelta en este documento,
   preguntÃ¡lo ANTES de escribir cÃ³digo.