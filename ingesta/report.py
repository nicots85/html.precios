"""
Generador de reportes de cambios propuestos.
Crea un resumen legible para que el dueño revise antes de aprobar.
"""
import json


class ReporteCambios:
    """Genera y gestiona reportes de cambios propuestos."""
    
    def __init__(self, proveedor, pestana):
        self.proveedor = proveedor
        self.pestana = pestana
        self.actualizaciones = []
        self.productos_nuevos = []
        self.sin_cambios = []
        self.errores = []
    
    def agregar_actualizacion(self, producto_viejo, producto_nuevo, cambios):
        """
        Registra una actualización de precio/stock.
        
        Args:
            producto_viejo: dict con datos actuales
            producto_nuevo: dict con datos nuevos
            cambios: dict con {campo: (valor_viejo, valor_nuevo)}
        """
        self.actualizaciones.append({
            'producto_viejo': producto_viejo,
            'producto_nuevo': producto_nuevo,
            'cambios': cambios
        })
    
    def agregar_nuevo(self, producto):
        """Registra un producto nuevo."""
        self.productos_nuevos.append(producto)
    
    def agregar_error(self, descripcion):
        """Registra un error de procesamiento."""
        self.errores.append(descripcion)
    
    def hay_cambios(self):
        """Determina si hay cambios para mostrar."""
        return len(self.actualizaciones) > 0 or len(self.productos_nuevos) > 0
    
    def generar_texto(self):
        """
        Genera un reporte en texto plano (para Telegram/WhatsApp).
        
        Returns:
            str: reporte formateado
        """
        lineas = []
        lineas.append(f"{'='*40}")
        lineas.append(f"REPORTE DE CAMBIOS")
        lineas.append(f"Proveedor: {self.proveedor}")
        lineas.append(f"Pestaña: {self.pestana}")
        lineas.append(f"{'='*40}")
        lineas.append("")
        
        if self.actualizaciones:
            lineas.append(f"ACTUALIZACIONES ({len(self.actualizaciones)}):")
            lineas.append("-" * 30)
            
            for item in self.actualizaciones:
                producto = item['producto_viejo']
                nombre = f"{producto.get('marca', '')} {producto.get('modelo', '')}".strip()
                if producto.get('calidad_o_color'):
                    nombre += f" ({producto['calidad_o_color']})"
                
                lineas.append(f"  {nombre}")
                
                for campo, (viejo, nuevo) in item['cambios'].items():
                    if campo == 'precio':
                        viejo_str = f"${viejo:,.0f}" if viejo else "N/A"
                        nuevo_str = f"${nuevo:,.0f}" if nuevo else "N/A"
                        
                        if viejo and nuevo:
                            pct = ((nuevo - viejo) / viejo) * 100
                            signo = "+" if pct > 0 else ""
                            lineas.append(f"    Precio: {viejo_str} → {nuevo_str} ({signo}{pct:.1f}%)")
                        else:
                            lineas.append(f"    Precio: {viejo_str} → {nuevo_str}")
                    elif campo == 'stock':
                        viejo_str = str(viejo) if viejo is not None else "N/A"
                        nuevo_str = str(nuevo) if nuevo is not None else "N/A"
                        lineas.append(f"    Stock: {viejo_str} → {nuevo_str}")
                
                lineas.append("")
        
        if self.productos_nuevos:
            lineas.append(f"PRODUCTOS NUEVOS ({len(self.productos_nuevos)}):")
            lineas.append("-" * 30)
            
            for producto in self.productos_nuevos:
                nombre = f"{producto.get('marca', '')} {producto.get('modelo', '')}".strip()
                if producto.get('calidad_o_color'):
                    nombre += f" ({producto['calidad_o_color']})"
                
                precio = producto.get('precio', 0)
                moneda = producto.get('moneda', 'ARS')
                lineas.append(f"  {nombre}")
                lineas.append(f"    Precio: ${precio:,.0f} {moneda}")
                
                if producto.get('stock'):
                    lineas.append(f"    Stock: {producto['stock']}")
                
                lineas.append("")
        
        if not self.hay_cambios():
            lineas.append("No se detectaron cambios.")
            lineas.append("")
        
        if self.errores:
            lineas.append(f"ERRORES ({len(self.errores)}):")
            lineas.append("-" * 30)
            for error in self.errores:
                lineas.append(f"  ⚠ {error}")
            lineas.append("")
        
        lineas.append("─" * 30)
        lineas.append("¿Aplicar cambios?")
        lineas.append("Respondé 'si' para aplicar, 'no' para cancelar.")
        
        return "\n".join(lineas)
    
    def generar_dict(self):
        """Genera el reporte como dict (para guardar en archivo)."""
        return {
            'proveedor': self.proveedor,
            'pestana': self.pestana,
            'actualizaciones': self.actualizaciones,
            'productos_nuevos': self.productos_nuevos,
            'errores': self.errores,
            'resumen': {
                'total_actualizaciones': len(self.actualizaciones),
                'total_nuevos': len(self.productos_nuevos),
                'total_errores': len(self.errores)
            }
        }
    
    def guardar_json(self, ruta):
        """Guarda el reporte en un archivo JSON."""
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(self.generar_dict(), f, ensure_ascii=False, indent=2)
