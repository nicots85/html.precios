# Guía de Despliegue - TechnoStore en Firebase

## Arquitectura

```
TechnoStore.xlsx (local)
        ↓ python backend/sync_excel_firestore.py
Firestore (base de datos)
        ↓
   ┌────────────────────────┐
   │  Cloud Functions       │
   │  /api/precios   → público  │
   │  /api/precios-admin → privado │
   └────────────────────────┘
        ↓                    ↓
  index.html (público)   Panel admin
  Firebase Hosting       URL secreta
```

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

Te abre el navegador para que autorices. Usá la cuenta de TechnoStore.

---

## Paso 3: Vincular al proyecto existente

```powershell
firebase use --add local-81a46
```

Elegí el alias `default`.

---

## Paso 4: Obtener credenciales de Firebase Admin

1. Andá a https://console.firebase.google.com/project/local-81a46/settings/serviceaccounts/adminsdk
2. Click en **"Generar nueva clave privada"**
3. Se descarga un JSON. Renombraselo a `firebase-credentials.json`
4. Copialo a la carpeta `backend/` de tu proyecto

⚠️ **NUNCA** subas este archivo a GitHub.

---

## Paso 5: Instalar dependencias del script de sync

```powershell
cd "C:\Users\Usuario\Desktop\listas de precios"
pip install firebase-admin openpyxl
```

---

## Paso 6: Subir datos del Excel a Firestore

```powershell
python backend/sync_excel_firestore.py
```

Esto lee `TechnoStore.xlsx` y crea/actualiza los documentos en Firestore. Vas a ver algo como:

```
Leyendo Excel: TechnoStore.xlsx
Productos encontrados: 1870

Inicializando Firestore...

[PGVJ] PGVJ - MODULOS GOSTTER (543 productos)
[PGVJ] PGVJ - MODULOS ORIGINALES (264 productos)
...

Sincronización completa: 1870 productos en Firestore
```

---

## Paso 7: Configurar la clave secreta del admin

Elegí una clave segura (ej: una contraseña larga). La vamos a guardar como "secreto" en Firebase:

```powershell
firebase functions:secrets:set ADMIN_SECRET
```

Te pide el valor, pegá tu clave. Anotala en un lugar seguro — la vas a necesitar para acceder al panel admin.

---

## Paso 8: Desplegar Cloud Functions

```powershell
firebase deploy --only functions
```

Esto sube las dos funciones (`precios` y `preciosAdmin`) a la región `southamerica-east1`.

---

## Paso 9: Desplegar el sitio público

```powershell
firebase deploy --only hosting
```

Tu sitio queda disponible en:
- `https://local-81a46.web.app` (URL principal)
- `https://local-81a46.firebaseapp.com` (alias)

---

## Paso 10: Probar que todo funciona

### Endpoint público (sin clave)
Abre en el navegador:
```
https://local-81a46.web.app/api/precios
```
Deberías ver un JSON con productos (sin costo ni margen).

### Sitio público
Abre:
```
https://local-81a46.web.app/
```

### Endpoint privado (con clave)
Reemplaza `TU_CLAVE_SECRETA` por la que elegiste en el paso 7:
```
https://local-81a46.web.app/api/precios-admin?clave=TU_CLAVE_SECRETA
```

---

## Uso cotidiano

### Actualizar precios

Cuando cambia un precio en el Excel:

1. Abrí `TechnoStore.xlsx` y modificá los precios
2. Ejecutá: `python backend/sync_excel_firestore.py`
3. La web se actualiza automáticamente (al recargar, consulta Firestore)

### Subir lista de proveedor nueva

1. Ejecutá la ingesta: `python -m ingesta.main "ruta\al\archivo.xlsx"`
2. Aprobá los cambios propuestos en el reporte
3. Re-ejecutá: `python backend/sync_excel_firestore.py`

---

## Estructura de archivos del proyecto

```
listas de precios/
├── index.html              # Web pública (se sube a Firebase Hosting)
├── config.json             # Configuración
├── productos.json          # (Legacy, ya no se usa)
├── TechnoStore.xlsx        # Excel maestro (NO se sube a Firebase)
├── servidor.bat            # (Legacy, para correr local)
│
├── ingesta/                # Sistema de ingesta de proveedores
│   ├── main.py
│   ├── ai_provider.py
│   ├── matcher.py
│   ├── normalizer.py
│   ├── excel_io.py
│   └── report.py
│
├── backend/                # Backend (NO se sube a Firebase Hosting)
│   ├── firebase-credentials.json   # ⚠️ NO subir a GitHub
│   ├── sync_excel_firestore.py     # Script de sincronización
│   └── functions/                  # Cloud Functions
│       ├── index.js
│       └── package.json
│
├── firebase.json           # Config de Firebase
├── firestore.rules         # Reglas de seguridad
└── firestore.indexes.json  # Índices de Firestore
```

---

## Costos estimados

- **Firebase Hosting:** gratis hasta 10 GB de transferencia/mes
- **Cloud Functions:** gratis hasta 2M invocaciones/mes
- **Firestore:** gratis hasta 1 GB de almacenamiento + 50K lecturas/día

Para una tienda como TechnoStore (unos pocos miles de visitas al mes), **todo queda en el tier gratuito**.

---

## Solución de problemas

### "No se encontró el archivo de credenciales"
Verificá que `backend/firebase-credentials.json` exista.

### "Permission denied" al subir datos
Las reglas de Firestore bloquean escritura directa desde el cliente. Eso es correcto — el script usa `firebase-admin` que tiene permisos de servidor.

### La web muestra "Error al cargar productos"
Verificá que las Cloud Functions estén desplegadas:
```powershell
firebase functions:list
```

### El admin no carga
Verificá que estés pasando la clave correcta en el query string `?clave=...`

---

## Próximos pasos

- [ ] Conectar con tu bot de Telegram/WhatsApp (cuando me pases los datos técnicos)
- [ ] Vigilar carpeta de proveedores automáticamente
- [ ] Implementar disparador automático de sync (cuando se sube archivo nuevo)
- [ ] Dashboard de cambios para revisar antes de aplicar
