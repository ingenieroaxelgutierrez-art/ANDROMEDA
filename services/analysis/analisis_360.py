# ============================================================
# ANÁLISIS 360° - ANDROMEDA PRO
# ============================================================
# Sistema de análisis integral por entidad (marca, producto,
# cliente, proveedor, vendedor, etc.)
# "¿Cómo va Immortale?" → Análisis completo de la marca
# ============================================================

import os
import sys
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd

from app.logging_config import get_logger
logger = get_logger("services.analysis.analisis_360")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TipoEntidad(Enum):
    """Tipos de entidades que podemos analizar."""
    MARCA = "marca"
    PRODUCTO = "producto"
    CLIENTE = "cliente"
    PROVEEDOR = "proveedor"
    VENDEDOR = "vendedor"
    CATEGORIA = "categoria"
    TIENDA = "tienda"
    DESCONOCIDO = "desconocido"


@dataclass
class EntidadDetectada:
    """Entidad detectada en la consulta."""
    tipo: TipoEntidad
    nombre: str
    id_odoo: Optional[int] = None
    confianza: float = 0.0
    datos_adicionales: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Analisis360:
    """Resultado de un análisis 360°."""
    entidad: EntidadDetectada
    ventas: Dict[str, Any] = field(default_factory=dict)
    inventario: Dict[str, Any] = field(default_factory=dict)
    compras: Dict[str, Any] = field(default_factory=dict)
    tendencias: Dict[str, Any] = field(default_factory=dict)
    metricas_clave: Dict[str, Any] = field(default_factory=dict)
    recomendaciones: List[str] = field(default_factory=list)
    alertas: List[str] = field(default_factory=list)


class DetectorEntidades:
    """Detecta entidades (marcas, productos, etc.) en las consultas."""
    
    def __init__(self):
        self.conector = None
        self.cache_marcas = {}
        self.cache_categorias = {}
        self.cache_productos = {}
        self.cache_clientes = {}
        self.cache_proveedores = {}
        self.cache_vendedores = {}
        self.cache_actualizado = None
    
    def set_conector(self, conector):
        """Configura el conector de Odoo."""
        self.conector = conector
        self._cargar_cache()
    
    def _cargar_cache(self):
        """Carga el cache de entidades desde Odoo."""
        if not self.conector or not self.conector.conectado:
            return
        
        try:
            # Cargar marcas (product.brand si existe)
            try:
                Brand = self.conector.odoo.env['product.brand']
                brand_ids = Brand.search([], limit=500)
                if brand_ids:
                    marcas = Brand.read(brand_ids, ['id', 'name'])
                    self.cache_marcas = {m['name'].lower(): m for m in marcas if m.get('name')}
            except Exception:
                pass
            
            # Cargar categorías
            try:
                Categ = self.conector.odoo.env['product.category']
                categ_ids = Categ.search([], limit=500)
                if categ_ids:
                    categorias = Categ.read(categ_ids, ['id', 'name', 'complete_name'])
                    self.cache_categorias = {c['name'].lower(): c for c in categorias if c.get('name')}
            except Exception:
                pass
            
            # Cargar algunos productos populares
            try:
                Product = self.conector.odoo.env['product.product']
                prod_ids = Product.search([('sale_ok', '=', True)], limit=1000)
                if prod_ids:
                    productos = Product.read(prod_ids, ['id', 'name', 'default_code'])
                    self.cache_productos = {p['name'].lower(): p for p in productos if p.get('name')}
            except Exception:
                pass
            
            # Cargar clientes principales
            try:
                Partner = self.conector.odoo.env['res.partner']
                partner_ids = Partner.search([('customer_rank', '>', 0)], limit=500)
                if partner_ids:
                    clientes = Partner.read(partner_ids, ['id', 'name'])
                    self.cache_clientes = {c['name'].lower(): c for c in clientes if c.get('name')}
            except Exception:
                pass
            
            # Cargar proveedores
            try:
                Partner = self.conector.odoo.env['res.partner']
                prov_ids = Partner.search([('supplier_rank', '>', 0)], limit=500)
                if prov_ids:
                    proveedores = Partner.read(prov_ids, ['id', 'name'])
                    self.cache_proveedores = {p['name'].lower(): p for p in proveedores if p.get('name')}
            except Exception:
                pass
            
            # Cargar vendedores
            try:
                User = self.conector.odoo.env['res.users']
                user_ids = User.search([('share', '=', False)], limit=100)
                if user_ids:
                    users = User.read(user_ids, ['id', 'name'])
                    self.cache_vendedores = {u['name'].lower(): u for u in users if u.get('name')}
            except Exception:
                pass
            
            self.cache_actualizado = datetime.now()
            print(f"📦 Cache cargado: {len(self.cache_marcas)} marcas, {len(self.cache_categorias)} categorías, {len(self.cache_productos)} productos")
            
        except Exception as e:
            logger.error(f"⚠️ Error cargando cache: {e}")
    
    def detectar(self, mensaje: str) -> Optional[EntidadDetectada]:
        """Detecta si el mensaje menciona alguna entidad conocida."""
        mensaje_lower = mensaje.lower().strip()
        
        # Patrones de consulta sobre entidades
        patrones_consulta = [
            r'c[oó]mo\s+(?:va|está|anda|le\s+va\s+a)\s+(.+?)(?:\?|$)',
            r'(?:análisis|reporte|informe)\s+(?:de|del|para)\s+(.+?)(?:\?|$)',
            r'qu[eé]\s+tal\s+(.+?)(?:\?|$)',
            r'dame\s+(?:info|información|datos)\s+(?:de|del|sobre)\s+(.+?)(?:\?|$)',
            r'(?:todo\s+sobre|360|completo)\s+(.+?)(?:\?|$)',
        ]
        
        # Extraer posible nombre de entidad
        nombre_buscar = None
        for patron in patrones_consulta:
            match = re.search(patron, mensaje_lower)
            if match:
                nombre_buscar = match.group(1).strip()
                break
        
        # Si no se detectó patrón, buscar después de "marca"
        if not nombre_buscar:
            match = re.search(r'marca\s+(.+?)(?:\s+|$)', mensaje_lower)
            if match:
                nombre_buscar = match.group(1).strip()
        
        if not nombre_buscar:
            return None
        
        # Buscar en caches por orden de prioridad
        # 1. Marcas (más probable)
        for marca_nombre, marca_data in self.cache_marcas.items():
            if nombre_buscar in marca_nombre or marca_nombre in nombre_buscar:
                return EntidadDetectada(
                    tipo=TipoEntidad.MARCA,
                    nombre=marca_data['name'],
                    id_odoo=marca_data['id'],
                    confianza=0.95
                )
        
        # 2. Categorías
        for categ_nombre, categ_data in self.cache_categorias.items():
            if nombre_buscar in categ_nombre or categ_nombre in nombre_buscar:
                return EntidadDetectada(
                    tipo=TipoEntidad.CATEGORIA,
                    nombre=categ_data['name'],
                    id_odoo=categ_data['id'],
                    confianza=0.90
                )
        
        # 3. Productos
        for prod_nombre, prod_data in self.cache_productos.items():
            if nombre_buscar in prod_nombre or prod_nombre in nombre_buscar:
                return EntidadDetectada(
                    tipo=TipoEntidad.PRODUCTO,
                    nombre=prod_data['name'],
                    id_odoo=prod_data['id'],
                    confianza=0.85
                )
        
        # 4. Clientes
        for cliente_nombre, cliente_data in self.cache_clientes.items():
            if nombre_buscar in cliente_nombre or cliente_nombre in nombre_buscar:
                return EntidadDetectada(
                    tipo=TipoEntidad.CLIENTE,
                    nombre=cliente_data['name'],
                    id_odoo=cliente_data['id'],
                    confianza=0.85
                )
        
        # 5. Proveedores
        for prov_nombre, prov_data in self.cache_proveedores.items():
            if nombre_buscar in prov_nombre or prov_nombre in nombre_buscar:
                return EntidadDetectada(
                    tipo=TipoEntidad.PROVEEDOR,
                    nombre=prov_data['name'],
                    id_odoo=prov_data['id'],
                    confianza=0.85
                )
        
        # 6. Vendedores
        for vend_nombre, vend_data in self.cache_vendedores.items():
            if nombre_buscar in vend_nombre or vend_nombre in nombre_buscar:
                return EntidadDetectada(
                    tipo=TipoEntidad.VENDEDOR,
                    nombre=vend_data['name'],
                    id_odoo=vend_data['id'],
                    confianza=0.85
                )
        
        # No encontrado - intentar búsqueda directa si hay conexión
        if self.conector and self.conector.conectado:
            return self._buscar_entidad_directa(nombre_buscar)
        
        return EntidadDetectada(
            tipo=TipoEntidad.DESCONOCIDO,
            nombre=nombre_buscar,
            confianza=0.3
        )
    
    def _buscar_entidad_directa(self, nombre: str) -> Optional[EntidadDetectada]:
        """Busca directamente en Odoo cuando no está en cache."""
        try:
            # Buscar en marcas
            try:
                Brand = self.conector.odoo.env['product.brand']
                brand_ids = Brand.search([('name', 'ilike', nombre)], limit=1)
                if brand_ids:
                    marca = Brand.read(brand_ids, ['id', 'name'])[0]
                    return EntidadDetectada(
                        tipo=TipoEntidad.MARCA,
                        nombre=marca['name'],
                        id_odoo=marca['id'],
                        confianza=0.95
                    )
            except Exception:
                pass
            
            # Buscar en categorías
            Categ = self.conector.odoo.env['product.category']
            categ_ids = Categ.search([('name', 'ilike', nombre)], limit=1)
            if categ_ids:
                categ = Categ.read(categ_ids, ['id', 'name'])[0]
                return EntidadDetectada(
                    tipo=TipoEntidad.CATEGORIA,
                    nombre=categ['name'],
                    id_odoo=categ['id'],
                    confianza=0.90
                )
            
            # Buscar en productos
            Product = self.conector.odoo.env['product.product']
            prod_ids = Product.search([('name', 'ilike', nombre)], limit=1)
            if prod_ids:
                prod = Product.read(prod_ids, ['id', 'name'])[0]
                return EntidadDetectada(
                    tipo=TipoEntidad.PRODUCTO,
                    nombre=prod['name'],
                    id_odoo=prod['id'],
                    confianza=0.85
                )
            
        except Exception as e:
            logger.error(f"Error en búsqueda directa: {e}")
        
        return EntidadDetectada(
            tipo=TipoEntidad.DESCONOCIDO,
            nombre=nombre,
            confianza=0.3
        )


class Analizador360:
    """Genera análisis 360° completos de cualquier entidad."""
    
    def __init__(self):
        self.conector = None
        self.detector = DetectorEntidades()
    
    def set_conector(self, conector):
        """Configura el conector de Odoo."""
        self.conector = conector
        self.detector.set_conector(conector)
    
    def analizar_entidad(self, mensaje: str) -> Optional[Analisis360]:
        """Analiza una entidad detectada en el mensaje."""
        entidad = self.detector.detectar(mensaje)
        
        if not entidad:
            return None
        
        if entidad.tipo == TipoEntidad.DESCONOCIDO:
            return Analisis360(
                entidad=entidad,
                alertas=[f"No se encontró información sobre '{entidad.nombre}'"]
            )
        
        # Ejecutar análisis según tipo
        if entidad.tipo == TipoEntidad.MARCA:
            return self._analisis_marca(entidad)
        elif entidad.tipo == TipoEntidad.PRODUCTO:
            return self._analisis_producto(entidad)
        elif entidad.tipo == TipoEntidad.CLIENTE:
            return self._analisis_cliente(entidad)
        elif entidad.tipo == TipoEntidad.PROVEEDOR:
            return self._analisis_proveedor(entidad)
        elif entidad.tipo == TipoEntidad.VENDEDOR:
            return self._analisis_vendedor(entidad)
        elif entidad.tipo == TipoEntidad.CATEGORIA:
            return self._analisis_categoria(entidad)
        
        return None
    
    def _analisis_marca(self, entidad: EntidadDetectada) -> Analisis360:
        """Análisis 360° de una marca."""
        resultado = Analisis360(entidad=entidad)
        
        try:
            # 1. Obtener productos de la marca
            Product = self.conector.odoo.env['product.product']
            
            # Intentar con product_brand_id o categ_id
            producto_ids = []
            try:
                producto_ids = Product.search([
                    ('product_brand_id', '=', entidad.id_odoo),
                    ('active', '=', True)
                ], limit=1000)
            except Exception:
                # Si no hay campo brand, buscar por nombre en descripción
                producto_ids = Product.search([
                    '|',
                    ('name', 'ilike', entidad.nombre),
                    ('description', 'ilike', entidad.nombre)
                ], limit=500)
            
            if not producto_ids:
                resultado.alertas.append(f"No se encontraron productos para la marca {entidad.nombre}")
                return resultado
            
            productos = Product.read(producto_ids, [
                'id', 'name', 'default_code', 'qty_available', 
                'list_price', 'standard_price', 'categ_id'
            ])
            
            # === INVENTARIO ===
            total_stock = sum(p.get('qty_available', 0) for p in productos)
            valor_inventario = sum(
                p.get('qty_available', 0) * p.get('standard_price', 0) 
                for p in productos
            )
            productos_sin_stock = [p for p in productos if p.get('qty_available', 0) <= 0]
            productos_bajo_stock = [p for p in productos if 0 < p.get('qty_available', 0) < 5]
            
            resultado.inventario = {
                'total_productos': len(productos),
                'total_unidades': total_stock,
                'valor_estimado': valor_inventario,
                'productos_sin_stock': len(productos_sin_stock),
                'productos_bajo_stock': len(productos_bajo_stock),
                'productos_criticos': [p['name'] for p in productos_sin_stock[:10]],
                'productos': productos[:20]
            }
            
            # === VENTAS (últimos 3 meses) ===
            fecha_inicio = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            
            SaleOrderLine = self.conector.odoo.env['sale.order.line']
            line_ids = SaleOrderLine.search([
                ('product_id', 'in', producto_ids),
                ('order_id.state', 'in', ['sale', 'done']),
                ('order_id.date_order', '>=', fecha_inicio)
            ], limit=5000)
            
            if line_ids:
                lineas = SaleOrderLine.read(line_ids, [
                    'product_id', 'price_subtotal', 'product_uom_qty', 'order_id'
                ])
                
                total_ventas = sum(l.get('price_subtotal', 0) for l in lineas)
                total_unidades_vendidas = sum(l.get('product_uom_qty', 0) for l in lineas)
                
                # Ventas por producto
                ventas_por_producto = {}
                for linea in lineas:
                    prod_id = linea['product_id'][0] if isinstance(linea.get('product_id'), (list, tuple)) else 0
                    prod_nombre = linea['product_id'][1] if isinstance(linea.get('product_id'), (list, tuple)) else 'Desconocido'
                    
                    if prod_id not in ventas_por_producto:
                        ventas_por_producto[prod_id] = {'nombre': prod_nombre, 'total': 0, 'unidades': 0}
                    
                    ventas_por_producto[prod_id]['total'] += linea.get('price_subtotal', 0)
                    ventas_por_producto[prod_id]['unidades'] += linea.get('product_uom_qty', 0)
                
                # Top 10 productos más vendidos
                top_productos = sorted(
                    ventas_por_producto.values(), 
                    key=lambda x: x['total'], 
                    reverse=True
                )[:10]
                
                # Ventas mensuales
                ventas_mensuales = self._calcular_ventas_mensuales(lineas)
                
                resultado.ventas = {
                    'total_90_dias': total_ventas,
                    'unidades_vendidas': total_unidades_vendidas,
                    'num_ordenes': len(set(l.get('order_id', [0])[0] if isinstance(l.get('order_id'), (list, tuple)) else 0 for l in lineas)),
                    'ticket_promedio': total_ventas / len(line_ids) if line_ids else 0,
                    'top_productos': top_productos,
                    'ventas_mensuales': ventas_mensuales
                }
            else:
                resultado.ventas = {
                    'total_90_dias': 0,
                    'unidades_vendidas': 0,
                    'num_ordenes': 0,
                    'mensaje': 'Sin ventas en los últimos 90 días'
                }
            
            # === COMPRAS (últimos 3 meses) ===
            try:
                PurchaseOrderLine = self.conector.odoo.env['purchase.order.line']
                purchase_line_ids = PurchaseOrderLine.search([
                    ('product_id', 'in', producto_ids),
                    ('order_id.state', 'in', ['purchase', 'done']),
                    ('order_id.date_order', '>=', fecha_inicio)
                ], limit=3000)
                
                if purchase_line_ids:
                    compras = PurchaseOrderLine.read(purchase_line_ids, [
                        'product_id', 'price_subtotal', 'product_qty'
                    ])
                    
                    total_compras = sum(c.get('price_subtotal', 0) for c in compras)
                    total_unidades_compradas = sum(c.get('product_qty', 0) for c in compras)
                    
                    resultado.compras = {
                        'total_90_dias': total_compras,
                        'unidades_compradas': total_unidades_compradas,
                        'num_ordenes': len(purchase_line_ids)
                    }
                else:
                    resultado.compras = {
                        'total_90_dias': 0,
                        'unidades_compradas': 0,
                        'mensaje': 'Sin compras en los últimos 90 días'
                    }
            except Exception:
                resultado.compras = {'mensaje': 'Módulo de compras no disponible'}
            
            # === MÉTRICAS CLAVE ===
            resultado.metricas_clave = {
                'margen_promedio': self._calcular_margen_promedio(productos),
                'rotacion_estimada': (resultado.ventas.get('unidades_vendidas', 0) / total_stock * 30) if total_stock > 0 else 0,
                'dias_inventario': (total_stock / (resultado.ventas.get('unidades_vendidas', 0) / 90)) if resultado.ventas.get('unidades_vendidas', 0) > 0 else 999
            }
            
            # === RECOMENDACIONES ===
            if resultado.inventario['productos_sin_stock'] > 0:
                resultado.recomendaciones.append(
                    f"Hay {resultado.inventario['productos_sin_stock']} productos sin stock. Considera reabastecer."
                )
            
            if resultado.metricas_clave['dias_inventario'] > 60:
                resultado.recomendaciones.append(
                    f"El inventario tiene rotación lenta ({resultado.metricas_clave['dias_inventario']:.0f} días). Evalúa promociones."
                )
            elif resultado.metricas_clave['dias_inventario'] < 15:
                resultado.recomendaciones.append(
                    f"Rotación muy alta ({resultado.metricas_clave['dias_inventario']:.0f} días). Aumenta el inventario para evitar quiebres."
                )
            
            if resultado.ventas.get('total_90_dias', 0) > resultado.compras.get('total_90_dias', 0) * 1.5:
                resultado.recomendaciones.append(
                    "Las ventas superan significativamente las compras. La marca tiene buena demanda."
                )
            
        except Exception as e:
            resultado.alertas.append(f"Error en análisis: {str(e)}")
        
        return resultado
    
    def _calcular_ventas_mensuales(self, lineas: List[Dict]) -> List[Dict]:
        """Calcula ventas agrupadas por mes."""
        try:
            # Necesitamos obtener las fechas de los pedidos
            order_ids = list(set(
                l['order_id'][0] if isinstance(l.get('order_id'), (list, tuple)) else 0 
                for l in lineas if l.get('order_id')
            ))
            
            SaleOrder = self.conector.odoo.env['sale.order']
            orders = SaleOrder.read(order_ids, ['id', 'date_order'])
            
            # Mapa de order_id -> fecha
            mapa_fechas = {o['id']: o['date_order'] for o in orders}
            
            # Agrupar por mes
            por_mes = {}
            for linea in lineas:
                order_id = linea['order_id'][0] if isinstance(linea.get('order_id'), (list, tuple)) else 0
                fecha_str = mapa_fechas.get(order_id, '')
                
                if fecha_str:
                    fecha = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')) if isinstance(fecha_str, str) else fecha_str
                    mes_key = fecha.strftime('%Y-%m')
                    
                    if mes_key not in por_mes:
                        por_mes[mes_key] = {'mes': mes_key, 'total': 0, 'unidades': 0}
                    
                    por_mes[mes_key]['total'] += linea.get('price_subtotal', 0)
                    por_mes[mes_key]['unidades'] += linea.get('product_uom_qty', 0)
            
            # Ordenar por mes
            return sorted(por_mes.values(), key=lambda x: x['mes'])
            
        except Exception as e:
            return []
    
    def _calcular_margen_promedio(self, productos: List[Dict]) -> float:
        """Calcula el margen promedio de los productos."""
        margenes = []
        for p in productos:
            precio = p.get('list_price', 0)
            costo = p.get('standard_price', 0)
            if precio > 0 and costo > 0:
                margen = ((precio - costo) / precio) * 100
                margenes.append(margen)
        
        return sum(margenes) / len(margenes) if margenes else 0
    
    def _analisis_producto(self, entidad: EntidadDetectada) -> Analisis360:
        """Análisis 360° de un producto específico."""
        resultado = Analisis360(entidad=entidad)
        
        try:
            Product = self.conector.odoo.env['product.product']
            producto = Product.read([entidad.id_odoo], [
                'name', 'default_code', 'qty_available', 'virtual_available',
                'list_price', 'standard_price', 'categ_id', 'product_brand_id'
            ])[0]
            
            resultado.inventario = {
                'codigo': producto.get('default_code', ''),
                'cantidad_disponible': producto.get('qty_available', 0),
                'cantidad_virtual': producto.get('virtual_available', 0),
                'precio_venta': producto.get('list_price', 0),
                'costo': producto.get('standard_price', 0),
                'margen': ((producto.get('list_price', 0) - producto.get('standard_price', 0)) / producto.get('list_price', 1)) * 100 if producto.get('list_price', 0) > 0 else 0
            }
            
            # Ventas del producto
            fecha_inicio = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            SaleOrderLine = self.conector.odoo.env['sale.order.line']
            line_ids = SaleOrderLine.search([
                ('product_id', '=', entidad.id_odoo),
                ('order_id.state', 'in', ['sale', 'done']),
                ('order_id.date_order', '>=', fecha_inicio)
            ])
            
            if line_ids:
                lineas = SaleOrderLine.read(line_ids, ['price_subtotal', 'product_uom_qty'])
                resultado.ventas = {
                    'total_90_dias': sum(l.get('price_subtotal', 0) for l in lineas),
                    'unidades_vendidas': sum(l.get('product_uom_qty', 0) for l in lineas)
                }
            
        except Exception as e:
            resultado.alertas.append(f"Error: {str(e)}")
        
        return resultado
    
    def _analisis_cliente(self, entidad: EntidadDetectada) -> Analisis360:
        """Análisis 360° de un cliente."""
        resultado = Analisis360(entidad=entidad)
        
        try:
            # Info del cliente
            Partner = self.conector.odoo.env['res.partner']
            cliente = Partner.read([entidad.id_odoo], [
                'name', 'email', 'phone', 'credit', 'debit', 'credit_limit'
            ])[0]
            
            resultado.metricas_clave = {
                'nombre': cliente.get('name', ''),
                'email': cliente.get('email', ''),
                'telefono': cliente.get('phone', ''),
                'credito': cliente.get('credit', 0),
                'debito': cliente.get('debit', 0),
                'limite_credito': cliente.get('credit_limit', 0)
            }
            
            # Ventas al cliente
            fecha_inicio = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            SaleOrder = self.conector.odoo.env['sale.order']
            order_ids = SaleOrder.search([
                ('partner_id', '=', entidad.id_odoo),
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', fecha_inicio)
            ])
            
            if order_ids:
                ordenes = SaleOrder.read(order_ids, ['amount_total', 'date_order'])
                resultado.ventas = {
                    'total_anual': sum(o.get('amount_total', 0) for o in ordenes),
                    'num_ordenes': len(ordenes),
                    'ticket_promedio': sum(o.get('amount_total', 0) for o in ordenes) / len(ordenes)
                }
            
        except Exception as e:
            resultado.alertas.append(f"Error: {str(e)}")
        
        return resultado
    
    def _analisis_proveedor(self, entidad: EntidadDetectada) -> Analisis360:
        """Análisis 360° de un proveedor."""
        resultado = Analisis360(entidad=entidad)
        # Similar a cliente pero con compras
        return resultado
    
    def _analisis_vendedor(self, entidad: EntidadDetectada) -> Analisis360:
        """Análisis 360° de un vendedor."""
        resultado = Analisis360(entidad=entidad)
        
        try:
            fecha_inicio = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            SaleOrder = self.conector.odoo.env['sale.order']
            
            order_ids = SaleOrder.search([
                ('user_id', '=', entidad.id_odoo),
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', fecha_inicio)
            ])
            
            if order_ids:
                ordenes = SaleOrder.read(order_ids, ['amount_total', 'partner_id'])
                
                resultado.ventas = {
                    'total_90_dias': sum(o.get('amount_total', 0) for o in ordenes),
                    'num_ordenes': len(ordenes),
                    'clientes_atendidos': len(set(
                        o['partner_id'][0] if isinstance(o.get('partner_id'), (list, tuple)) else 0 
                        for o in ordenes
                    )),
                    'ticket_promedio': sum(o.get('amount_total', 0) for o in ordenes) / len(ordenes)
                }
            
        except Exception as e:
            resultado.alertas.append(f"Error: {str(e)}")
        
        return resultado
    
    def _analisis_categoria(self, entidad: EntidadDetectada) -> Analisis360:
        """Análisis 360° de una categoría."""
        # Similar a marca pero con categ_id
        resultado = Analisis360(entidad=entidad)
        # Implementar similar a _analisis_marca
        return resultado
    
    def ventas_mensuales_por_marca(self, meses: int = 6) -> Dict[str, Any]:
        """Obtiene las ventas mensuales desglosadas por marca."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=meses * 30)).strftime('%Y-%m-%d')
            
            SaleOrderLine = self.conector.odoo.env['sale.order.line']
            line_ids = SaleOrderLine.search([
                ('order_id.state', 'in', ['sale', 'done']),
                ('order_id.date_order', '>=', fecha_inicio)
            ], limit=20000)
            
            if not line_ids:
                return {'error': 'No hay ventas en el período'}
            
            lineas = SaleOrderLine.read(line_ids, [
                'product_id', 'price_subtotal', 'product_uom_qty', 'order_id'
            ])
            
            # Obtener productos con sus marcas
            product_ids = list(set(
                l['product_id'][0] if isinstance(l.get('product_id'), (list, tuple)) else 0
                for l in lineas if l.get('product_id')
            ))
            
            Product = self.conector.odoo.env['product.product']
            productos = Product.read(product_ids, ['id', 'product_brand_id', 'categ_id'])
            
            # Mapa producto -> marca
            mapa_marcas = {}
            for p in productos:
                marca = p.get('product_brand_id')
                if isinstance(marca, (list, tuple)) and marca:
                    mapa_marcas[p['id']] = marca[1]
                else:
                    categ = p.get('categ_id')
                    mapa_marcas[p['id']] = categ[1] if isinstance(categ, (list, tuple)) else 'Sin categoría'
            
            # Obtener fechas de órdenes
            order_ids = list(set(
                l['order_id'][0] if isinstance(l.get('order_id'), (list, tuple)) else 0
                for l in lineas if l.get('order_id')
            ))
            
            SaleOrder = self.conector.odoo.env['sale.order']
            orders = SaleOrder.read(order_ids, ['id', 'date_order'])
            mapa_fechas = {o['id']: o['date_order'] for o in orders}
            
            # Agrupar por marca y mes
            por_marca_mes = {}
            for linea in lineas:
                prod_id = linea['product_id'][0] if isinstance(linea.get('product_id'), (list, tuple)) else 0
                order_id = linea['order_id'][0] if isinstance(linea.get('order_id'), (list, tuple)) else 0
                
                marca = mapa_marcas.get(prod_id, 'Sin marca')
                fecha_str = mapa_fechas.get(order_id, '')
                
                if fecha_str:
                    try:
                        fecha = datetime.fromisoformat(str(fecha_str).replace('Z', '+00:00')) if isinstance(fecha_str, str) else fecha_str
                        mes_key = fecha.strftime('%Y-%m')
                        
                        if marca not in por_marca_mes:
                            por_marca_mes[marca] = {}
                        
                        if mes_key not in por_marca_mes[marca]:
                            por_marca_mes[marca][mes_key] = {'total': 0, 'unidades': 0}
                        
                        por_marca_mes[marca][mes_key]['total'] += linea.get('price_subtotal', 0)
                        por_marca_mes[marca][mes_key]['unidades'] += linea.get('product_uom_qty', 0)
                    except Exception:
                        continue
            
            # Convertir a formato de salida
            resultado = []
            for marca, meses_data in por_marca_mes.items():
                total_marca = sum(m['total'] for m in meses_data.values())
                resultado.append({
                    'marca': marca,
                    'total_periodo': total_marca,
                    'meses': [
                        {'mes': k, 'total': v['total'], 'unidades': v['unidades']}
                        for k, v in sorted(meses_data.items())
                    ]
                })
            
            # Ordenar por total
            resultado.sort(key=lambda x: x['total_periodo'], reverse=True)
            
            return {
                'tipo': 'ventas_mensuales_marca',
                'periodo_meses': meses,
                'marcas': resultado[:20],
                'total_marcas': len(resultado),
                'total_general': sum(m['total_periodo'] for m in resultado)
            }
            
        except Exception as e:
            return {'error': str(e)}


class Formateador360:
    """Formatea resultados de análisis 360° a Markdown."""
    
    @staticmethod
    def formatear(analisis: Analisis360) -> str:
        """Formatea un análisis 360° completo."""
        entidad = analisis.entidad
        
        md = f"""## Análisis 360° - {entidad.nombre}

**Tipo:** {entidad.tipo.value.capitalize()} | **Confianza:** {entidad.confianza:.0%}

---

"""
        
        # Alertas primero
        if analisis.alertas:
            md += "### Alertas\n"
            for alerta in analisis.alertas:
                md += f"- {alerta}\n"
            md += "\n"
        
        # Métricas clave
        if analisis.metricas_clave:
            md += "### Métricas Clave\n"
            md += "| Métrica | Valor |\n|---------|-------|\n"
            for k, v in analisis.metricas_clave.items():
                if isinstance(v, float):
                    md += f"| {k.replace('_', ' ').title()} | {v:,.2f} |\n"
                else:
                    md += f"| {k.replace('_', ' ').title()} | {v} |\n"
            md += "\n"
        
        # Inventario
        if analisis.inventario:
            md += "### Inventario\n"
            inv = analisis.inventario
            md += "| Métrica | Valor |\n|---------|-------|\n"
            md += f"| Total Productos | **{inv.get('total_productos', 0):,}** |\n"
            md += f"| Total Unidades | **{inv.get('total_unidades', 0):,.0f}** |\n"
            md += f"| Valor Estimado | **${inv.get('valor_estimado', 0):,.2f}** |\n"
            md += f"| Sin Stock | **{inv.get('productos_sin_stock', 0)}** |\n"
            md += f"| Stock Bajo | **{inv.get('productos_bajo_stock', 0)}** |\n"
            md += "\n"
            
            if inv.get('productos_criticos'):
                md += "**Productos Críticos (sin stock):**\n"
                for p in inv['productos_criticos'][:5]:
                    md += f"- {p}\n"
                md += "\n"
        
        # Ventas
        if analisis.ventas:
            md += "### Ventas (Últimos 90 días)\n"
            v = analisis.ventas
            md += "| Métrica | Valor |\n|---------|-------|\n"
            md += f"| Total Ventas | **${v.get('total_90_dias', 0):,.2f}** |\n"
            md += f"| Unidades Vendidas | **{v.get('unidades_vendidas', 0):,.0f}** |\n"
            md += f"| Núm. Órdenes | **{v.get('num_ordenes', 0):,}** |\n"
            if v.get('ticket_promedio'):
                md += f"| Ticket Promedio | **${v.get('ticket_promedio', 0):,.2f}** |\n"
            md += "\n"
            
            # Ventas mensuales
            if v.get('ventas_mensuales'):
                md += "**Ventas Mensuales:**\n"
                md += "| Mes | Total | Unidades |\n|-----|-------|----------|\n"
                for m in v['ventas_mensuales']:
                    md += f"| {m['mes']} | ${m['total']:,.2f} | {m['unidades']:,.0f} |\n"
                md += "\n"
            
            # Top productos
            if v.get('top_productos'):
                md += "**Top Productos:**\n"
                md += "| Producto | Total | Unidades |\n|----------|-------|----------|\n"
                for p in v['top_productos'][:5]:
                    md += f"| {p['nombre'][:35]} | ${p['total']:,.2f} | {p['unidades']:,.0f} |\n"
                md += "\n"
        
        # Compras
        if analisis.compras and not analisis.compras.get('mensaje'):
            md += "### Compras (Últimos 90 días)\n"
            c = analisis.compras
            md += "| Métrica | Valor |\n|---------|-------|\n"
            md += f"| Total Compras | **${c.get('total_90_dias', 0):,.2f}** |\n"
            md += f"| Unidades Compradas | **{c.get('unidades_compradas', 0):,.0f}** |\n"
            md += "\n"
        
        # Tendencias
        if analisis.tendencias:
            md += "### Tendencias\n"
            # Formatear tendencias
            md += "\n"
        
        # Recomendaciones
        if analisis.recomendaciones:
            md += "### Recomendaciones\n"
            for rec in analisis.recomendaciones:
                md += f"- {rec}\n"
            md += "\n"
        
        return md
    
    @staticmethod
    def formatear_ventas_mensuales_marca(datos: Dict) -> str:
        """Formatea ventas mensuales por marca."""
        if 'error' in datos:
            return f"## {datos['error']}"
        
        marcas = datos.get('marcas', [])
        total = datos.get('total_general', 0)
        
        md = f"""## Ventas Mensuales por Marca

**Total General:** ${total:,.2f} | **Marcas:** {datos.get('total_marcas', 0)} | **Período:** {datos.get('periodo_meses', 6)} meses

---

"""
        
        for i, marca in enumerate(marcas[:15], 1):
            pct = (marca['total_periodo'] / total * 100) if total > 0 else 0
            md += f"### {i}. {marca['marca']} - ${marca['total_periodo']:,.2f} ({pct:.1f}%)\n\n"
            
            if marca.get('meses'):
                md += "| Mes | Ventas | Unidades |\n|-----|--------|----------|\n"
                for m in marca['meses']:
                    md += f"| {m['mes']} | ${m['total']:,.2f} | {m['unidades']:,.0f} |\n"
                md += "\n"
        
        return md


# Instancias globales
analizador_360 = Analizador360()
formateador_360 = Formateador360()


def set_conector_360(conector):
    """Configura el conector para el analizador 360°."""
    analizador_360.set_conector(conector)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" ANÁLISIS 360° - Test de Detección de Entidades")
    print("=" * 60)
    
    detector = DetectorEntidades()
    
    pruebas = [
        "cómo va Immortale?",
        "cómo está la marca Trek?",
        "análisis de Giant",
        "qué tal Specialized?",
        "dame info de Shimano",
        "todo sobre Cannondale",
    ]
    
    for consulta in pruebas:
        print(f"\nConsulta: '{consulta}'")
        entidad = detector.detectar(consulta)
        if entidad:
            print(f"   Tipo: {entidad.tipo.value}")
            print(f"   Nombre: {entidad.nombre}")
            print(f"   Confianza: {entidad.confianza:.0%}")
        else:
            print("   No se detectó entidad")
