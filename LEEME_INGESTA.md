# TechnoStore - Sistema de Ingesta de Listas de Proveedores

## ¿Qué es esto?

Un sistema que toma un archivo crudo de un proveedor (Excel, PDF, foto o texto),
lo interpreta con IA, lo compara contra tu `TechnoStore.xlsx`, y te muestra
un reporte de cambios propuestos antes de tocar nada.

## Estructura

```
ingesta/
├── __init__.py
├── main.py           # Punto de entrada: procesá un archivo
├── ai_provider.py    # Interfaz IA (cambiás el proveedor en config.json)
├── normalizer.py     # Normaliza datos a estructura común
├── matcher.py        # Genera claves y compara productos
├── excel_io.py       # Lee y escribe el Excel maestro
└── report.py         # Genera reportes de cambios
config.json           # Configuración centralizada
```

## Configuración inicial

1. **Editá `config.json`** con tus datos:
   - Clave de API de IA (`ai.api_key`)
   - Proveedores y pestañas
   - Márgenes

2. **Instalá dependencias** (si no las tenés):
   ```
   pip install openpyxl pymupdf
   ```

## Uso

### Procesar un archivo de proveedor

```bash
python -m ingesta.main "C:\Downloads\lista_pgvj.xlsx"
```

Si el archivo está en dólares:

```bash
python -m ingesta.main "C:\Downloads\lista_pinaapple.pdf" USD
```

### Aplicar los cambios (actualizar el Excel + productos.json)

Sin el flag solo genera el reporte (no toca nada). Para aplicar:

```bash
python -m ingesta.main "C:\Downloads\lista_pgvj.xlsx" --aplicar
```

Esto:
1. Actualiza precio y stock en `TechnoStore.xlsx`
2. Agrega los productos nuevos
3. Regenera `productos.json` (catálogo de la web)

Después re-desplegá el hosting:

```bash
firebase deploy --only hosting
```

### ¿Qué pasa cuando lo corrés?

1. El sistema detecta el tipo de archivo (Excel/PDF/imagen/texto)
2. La IA interpreta los productos
3. Se detecta el proveedor (o te pregunta)
4. Se compara contra el Excel maestro
5. Se genera un reporte con:
   - Precios que cambiaron
   - Productos nuevos
   - Errores si los hubiera

### Ejemplo de salida

```
========================================
REPORTE DE CAMBIOS
Proveedor: PGVJ
Pestaña: PGVJ - MODULOS GOSTTER
========================================

ACTUALIZACIONES (2):
------------------------------
  SAMSUNG A13 (CON LENTE NEGRO)
    Precio: $9,520 → $10,000 (+5.0%)

  MOTOROLA EDGE 50 FUSION (ORIGINAL)
    Precio: $45,000 → $42,000 (-6.7%)

PRODUCTOS NUEVOS (1):
------------------------------
  SAMSUNG S25 ULTRA (CON LENTE AZUL)
    Precio: $85,000 ARS

──────────────────────────────
¿Aplicar cambios?
Respondé 'si' para aplicar, 'no' para cancelar.
```

## Cambiar el proveedor de IA

En `config.json`, cambiá:

```json
"ai": {
  "provider": "openai",
  "api_key": "TU_CLAVE",
  "api_base": "https://api.openai.com/v1",
  "model": "gpt-4o"
}
```

Funciona con cualquier API compatible con OpenAI (OpenAI, Together, Groq, etc.)

## Próximos pasos (futuro)

- [ ] Conectar con bot de Telegram/WhatsApp
- [ ] Vigilar carpeta automáticamente
- [ ] Panel web de administración
- [ ] (Opcional) Migrar a Firestore + Cloud Functions con plan Blaze
