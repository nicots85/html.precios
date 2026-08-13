# Guía de Despliegue - TechnoStore en Firebase

## Arquitectura (hosting estático)

```
TechnoStore.xlsx (local)
        ↓ python backend/generar_productos.py
productos.json (catálogo con precios de venta, sin costos)
        ↓
   Firebase Hosting  (https://technostore-db.web.app)
         index.html  →  productos.json
```

> El hosting es **estático** (no requiere plan Blaze ni Firestore).
> Cuando cambian precios en el Excel, regenerás productos.json y re-desplegás.

## Flujo de actualización de precios

1. Modificar `TechnoStore.xlsx` (o aplicar una ingesta de proveedor)
2. Regenerar el catálogo: `python backend/generar_productos.py`
3. Re-desplegar: `firebase deploy --only hosting`

La ingesta integra esto: tras aprobar cambios,
`python -m ingesta.main <archivo> --aplicar`
actualiza el Excel **y** regenera `productos.json` automáticamente.

---

## Paso 1: Instalar Firebase CLI (una sola vez)

Abrí PowerShell como administrador y ejecutá:

```powershell
npm install -g firebase-tools
```

Si no tenés Node.js, instalalo desde: https://nodejs.org/

---

## Paso 2: Login en Firebase

```powershell
firebase login
```

Te abre el navegador para que autorices. Usá la cuenta de TechnoStore (tsbarrionorte@gmail.com).

---

## Paso 3: Vincular al proyecto

```powershell
firebase use technostore-db
```

⚠️ NO tocar el proyecto `local-81a46`.

---

## Paso 4: Regenerar el catálogo

```powershell
python backend/generar_productos.py
```

Esto lee `TechnoStore.xlsx` y crea `productos.json` en la raíz. Solo incluye
productos con precio de venta válido y nunca expone costos ni márgenes.

---

## Paso 5: Desplegar el sitio público

```powershell
firebase deploy --only hosting
```

Tu sitio queda disponible en:
- `https://technostore-db.web.app` (URL principal)
- `https://technostore-db.firebaseapp.com` (alias)

---

## Paso 6: Probar que todo funciona

Abre en el navegador:

```
https://technostore-db.web.app/
```

Deberías ver el catálogo con productos. También podés verificar los datos:

```
https://technostore-db.web.app/productos.json
```

---

## Uso cotidiano

### Actualizar precios

Cuando cambia un precio en el Excel:

1. Abrí `TechnoStore.xlsx` y modificá los precios
2. Ejecutá: `python backend/generar_productos.py`
3. Re-desplegá: `firebase deploy --only hosting`

### Subir lista de proveedor nueva

1. Ejecutá la ingesta: `python -m ingesta.main "ruta\al\archivo.pdf"`
2. Revisá el reporte de cambios
3. Si querés aplicar: `python -m ingesta.main "ruta\al\archivo.pdf" --aplicar`
4. Re-desplegá: `firebase deploy --only hosting`

---

## Estructura de archivos del proyecto

```
listas de precios/
├── index.html              # Web pública (se sube a Firebase Hosting)
├── admin.html              # Panel admin (se sube)
├── logo.jpg                # Logo
├── productos.json          # Catálogo generado (se sube, NO se edita a mano)
├── config.json             # Configuración (NO se sube)
├── TechnoStore.xlsx        # Excel maestro (NO se sube)
│
├── backend/
│   ├── generar_productos.py        # Genera productos.json desde el Excel
│   ├── sync_excel_firestore.py     # (Legacy, para Firestore - requiere Blaze)
│   └── functions/                  # (Legacy, Cloud Functions - requiere Blaze)
│
├── ingesta/                # Sistema de ingesta de proveedores
│   ├── main.py
│   ├── ai_provider.py
│   ├── matcher.py
│   ├── normalizer.py
│   ├── excel_io.py
│   └── report.py
│
├── firebase.json           # Config de Firebase
├── firestore.rules         # (Legacy)
└── firestore.indexes.json  # (Legacy)
```

---

## Costos

- **Firebase Hosting:** gratis hasta 10 GB de transferencia/mes
- La opción estática **no necesita plan Blaze ni tarjeta**

---

## Solución de problemas

### "La web no muestra productos"
Verificá que `productos.json` se haya generado y esté subido:

```powershell
python backend/generar_productos.py
firebase deploy --only hosting
```

### "Error al cargar productos"
Probablemente `productos.json` está vacío o mal generado. Revisá el paso 4.

### El admin no carga
`admin.html` funciona con `productos.json` local; no depende del backend.

---

## Próximos pasos

- [ ] Conectar con tu bot de Telegram/WhatsApp (cuando me pases los datos técnicos)
- [ ] Vigilar carpeta de proveedores automáticamente
- [ ] Dashboard de cambios para revisar antes de aplicar
- [ ] (Opcional) Migrar a Firestore + Cloud Functions si algún día se pasa a plan Blaze