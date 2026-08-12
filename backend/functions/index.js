// Cloud Functions para TechnoStore
// Dos rutas:
//   GET /precios        → Pública (sin auth, sin costo)
//   GET /precios-admin  → Privada (requiere clave secreta, devuelve todo)

const { onRequest } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const admin = require("firebase-admin");

admin.initializeApp();
const db = admin.firestore();

// Clave secreta para el endpoint privado (la configurás al deployar)
const ADMIN_SECRET = defineSecret("ADMIN_SECRET");

/**
 * ENDPOINT PÚBLICO
 * GET /precios
 * 
 * Devuelve lista de productos SOLO con:
 *   - categoria, marca, modelo, calidad
 *   - stock (binario: 'disponible' / 'sin_stock')
 *   - precio_venta (calculado con costo * tasa * margen)
 * 
 * NUNCA devuelve: costo_pesos, costo_usd, margen
 */
exports.precios = onRequest(
  {
    region: "southamerica-east1",
    cors: true,
    memory: "512MiB",
  },
  async (req, res) => {
    try {
      const tasaUsdt = await obtenerTasaUsdt();
      const snapshot = await db.collection("productos").get();
      
      const productos = [];
      snapshot.forEach((doc) => {
        const data = doc.data();
        const precioVenta = calcularPrecioVenta(data, tasaUsdt);
        
        productos.push({
          id: doc.id,
          categoria: data.categoria || "",
          marca: data.marca || "",
          modelo: data.modelo || "",
          calidad: data.calidad || "",
          stock: (data.stock && data.stock > 0) ? "disponible" : "sin_stock",
          precio_venta: precioVenta,
        });
      });
      
      res.json({
        tasa_usdt: tasaUsdt,
        timestamp: new Date().toISOString(),
        total: productos.length,
        productos: productos,
      });
    } catch (error) {
      console.error("Error en /precios:", error);
      res.status(500).json({ error: "Error interno del servidor" });
    }
  }
);

/**
 * ENDPOINT PRIVADO (ADMIN)
 * GET /precios-admin?clave=TU_CLAVE_SECRETA
 * 
 * Devuelve TODO: costo, margen, stock real, etc.
 * Protegido por URL con clave secreta (sin login complejo).
 */
exports.preciosAdmin = onRequest(
  {
    region: "southamerica-east1",
    cors: true,
    memory: "512MiB",
    secrets: [ADMIN_SECRET],
  },
  async (req, res) => {
    try {
      const claveRecibida = req.query.clave || req.headers["x-admin-key"];
      const claveCorrecta = ADMIN_SECRET.value();
      
      if (!claveRecibida || claveRecibida !== claveCorrecta) {
        return res.status(401).json({ error: "No autorizado" });
      }
      
      const tasaUsdt = await obtenerTasaUsdt();
      const snapshot = await db.collection("productos").get();
      
      const productos = [];
      snapshot.forEach((doc) => {
        const data = doc.data();
        
        productos.push({
          id: doc.id,
          proveedor: data.proveedor || "",
          categoria: data.categoria || "",
          pestana: data.pestana || "",
          marca: data.marca || "",
          modelo: data.modelo || "",
          calidad: data.calidad || "",
          costo_pesos: data.costo_pesos || null,
          costo_usd: data.costo_usd || null,
          precio_venta: data.precio_venta || null,
          stock: data.stock || null,
          updated_at: data.updated_at || null,
        });
      });
      
      res.json({
        tasa_usdt: tasaUsdt,
        timestamp: new Date().toISOString(),
        total: productos.length,
        productos: productos,
      });
    } catch (error) {
      console.error("Error en /precios-admin:", error);
      res.status(500).json({ error: "Error interno del servidor" });
    }
  }
);

/**
 * Calcula el precio de venta aplicando márgenes.
 * - Productos bajo $30.000 ARS: 40% de margen
 * - Productos sobre $30.000 ARS: 30% de margen
 */
function calcularPrecioVenta(producto, tasaUsdt) {
  let costoPesos = producto.costo_pesos;
  
  // Si tiene costo en USD, convertir a pesos
  if (!costoPesos && producto.costo_usd) {
    costoPesos = producto.costo_usd * tasaUsdt;
  }
  
  if (!costoPesos) {
    return producto.precio_venta || 0;
  }
  
  const margen = costoPesos < 30000 ? 0.40 : 0.30;
  return Math.round(costoPesos * (1 + margen));
}

/**
 * Obtiene la tasa USDT/ARS actual.
 * Intenta primero Binance, luego fallback.
 */
async function obtenerTasaUsdt() {
  try {
    const response = await fetch("https://api.binance.com/api/v3/ticker/price?symbol=USDTARS");
    if (response.ok) {
      const data = await response.json();
      const precio = parseFloat(data.price);
      if (precio > 1000 && precio < 3000) {
        return precio;
      }
    }
  } catch (e) {
    console.warn("No se pudo obtener tasa de Binance");
  }
  
  return 1586; // Fallback
}
