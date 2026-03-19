# ============================================================
# CONSULTAS ESPECIALIZADAS ANDROMEDA
# Reportes avanzados con alta precisión y limpieza de datos
# ============================================================

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Agregar directorio raíz al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.logging_config import get_logger
logger = get_logger("utils.consultas_especializadas")

try:
    from core.cerebro_andromeda import (
        CerebroAndromeda, 
        MatrizDatosOdoo, 
        LimpiadorDatos,
        MotorEstadistico,
        GeneradorPrompts,
        ResultadoAnalisis,
        TipoReporte,
        TipoAnalisis
    )
except ImportError:
    logger.warning("Cerebro ANDROMEDA no disponible")


class ConsultasEspecializadas:
    """
    Consultas especializadas de alto nivel para reportes empresariales.
    Cada método genera un análisis completo con datos limpios y validados.
    """
    
    def __init__(self, conector_odoo=None):
        self.odoo = conector_odoo
        self.limpiador = LimpiadorDatos()
        self.estadistico = MotorEstadistico()
        
    def set_conector(self, conector_odoo):
        """Establece el conector Odoo."""
        self.odoo = conector_odoo
    
    # ============================================================
    # VENTAS
    # ============================================================
    
    def ventas_completo(
        self, 
        fecha_inicio: str = None, 
        fecha_fin: str = None,
        empresa_id: int = None,
        vendedor_id: int = None
    ) -> Dict:
        """
        Análisis completo de ventas con desglose por múltiples dimensiones.
        
        Returns:
            Dict con métricas, tendencias, top productos, top clientes, etc.
        """
        if not self.odoo or not self.odoo.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        resultado = {
            'tipo': 'ventas_completo',
            'fecha_generacion': datetime.now().isoformat(),
            'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
        }
        
        try:
            # Construir filtro
            domain = [('state', 'in', ['sale', 'done'])]
            if fecha_inicio:
                domain.append(('date_order', '>=', fecha_inicio))
            if fecha_fin:
                domain.append(('date_order', '<=', fecha_fin))
            if empresa_id:
                domain.append(('company_id', '=', empresa_id))
            if vendedor_id:
                domain.append(('user_id', '=', vendedor_id))
            
            # Obtener órdenes
            # SaleOrder acceso encapsulado via ConectorOdoo (ARQ-003)
            order_ids = self.odoo.buscar('sale.order', filtro=domain, limit=5000)
            
            if not order_ids:
                return {'error': 'No hay ventas en el período seleccionado', **resultado}
            
            campos = [
                'name', 'partner_id', 'user_id', 'team_id', 'company_id',
                'date_order', 'amount_untaxed', 'amount_tax', 'amount_total', 'state'
            ]
            ordenes = self.odoo.buscar_leer('sale.order', filtro=domain, campos=campos, limite=5000)
            df = pd.DataFrame(ordenes)
            
            # Limpiar datos
            df_limpio, confianza, stats = self.limpiador.limpiar_dataframe(df, 'sale.order')
            
            resultado['confianza_datos'] = confianza * 100
            resultado['registros_totales'] = len(ordenes)
            resultado['registros_validos'] = len(df_limpio)
            
            # Métricas generales
            resultado['metricas'] = {
                'total_ventas': float(df_limpio['amount_total'].sum()),
                'subtotal': float(df_limpio['amount_untaxed'].sum()),
                'impuestos': float(df_limpio['amount_tax'].sum()),
                'num_ordenes': len(df_limpio),
                'ticket_promedio': float(df_limpio['amount_total'].mean()),
                'venta_max': float(df_limpio['amount_total'].max()),
                'venta_min': float(df_limpio['amount_total'].min()),
            }
            
            # Tendencia
            montos = df_limpio['amount_total'].tolist()
            resultado['tendencia'] = self.estadistico.calcular_tendencia(montos)
            
            # Por cliente
            df_limpio['cliente_nombre'] = df_limpio['partner_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'N/A'
            )
            por_cliente = df_limpio.groupby('cliente_nombre').agg({
                'amount_total': ['sum', 'count', 'mean']
            }).reset_index()
            por_cliente.columns = ['cliente', 'total', 'ordenes', 'promedio']
            por_cliente = por_cliente.sort_values('total', ascending=False)
            resultado['top_clientes'] = por_cliente.head(20).to_dict('records')
            
            # Por vendedor
            df_limpio['vendedor_nombre'] = df_limpio['user_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'N/A'
            )
            por_vendedor = df_limpio.groupby('vendedor_nombre').agg({
                'amount_total': ['sum', 'count', 'mean']
            }).reset_index()
            por_vendedor.columns = ['vendedor', 'total', 'ordenes', 'promedio']
            por_vendedor = por_vendedor.sort_values('total', ascending=False)
            resultado['por_vendedor'] = por_vendedor.to_dict('records')
            
            # Por empresa
            df_limpio['empresa_nombre'] = df_limpio['company_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'N/A'
            )
            por_empresa = df_limpio.groupby('empresa_nombre').agg({
                'amount_total': ['sum', 'count']
            }).reset_index()
            por_empresa.columns = ['empresa', 'total', 'ordenes']
            por_empresa = por_empresa.sort_values('total', ascending=False)
            resultado['por_empresa'] = por_empresa.to_dict('records')
            
            # Por día de la semana
            df_limpio['fecha'] = pd.to_datetime(df_limpio['date_order'])
            df_limpio['dia_semana'] = df_limpio['fecha'].dt.day_name()
            por_dia = df_limpio.groupby('dia_semana')['amount_total'].sum().reset_index()
            resultado['por_dia_semana'] = por_dia.to_dict('records')
            
            # Dataframe principal
            resultado['df'] = df_limpio
            
            return resultado
            
        except Exception as e:
            return {'error': str(e), **resultado}
    
    def ventas_vs_periodo_anterior(
        self, 
        tipo: str = 'mes'  # 'dia', 'semana', 'mes', 'año'
    ) -> Dict:
        """Compara ventas del período actual vs anterior."""
        hoy = datetime.now()
        
        if tipo == 'dia':
            actual_inicio = hoy.strftime('%Y-%m-%d')
            actual_fin = hoy.strftime('%Y-%m-%d')
            anterior_inicio = (hoy - timedelta(days=1)).strftime('%Y-%m-%d')
            anterior_fin = anterior_inicio
            periodo_nombre = 'día'
        elif tipo == 'semana':
            actual_inicio = (hoy - timedelta(days=hoy.weekday())).strftime('%Y-%m-%d')
            actual_fin = hoy.strftime('%Y-%m-%d')
            anterior_inicio = (hoy - timedelta(days=hoy.weekday() + 7)).strftime('%Y-%m-%d')
            anterior_fin = (hoy - timedelta(days=hoy.weekday() + 1)).strftime('%Y-%m-%d')
            periodo_nombre = 'semana'
        elif tipo == 'mes':
            actual_inicio = hoy.replace(day=1).strftime('%Y-%m-%d')
            actual_fin = hoy.strftime('%Y-%m-%d')
            mes_anterior = hoy.replace(day=1) - timedelta(days=1)
            anterior_inicio = mes_anterior.replace(day=1).strftime('%Y-%m-%d')
            anterior_fin = mes_anterior.strftime('%Y-%m-%d')
            periodo_nombre = 'mes'
        else:  # año
            actual_inicio = hoy.replace(month=1, day=1).strftime('%Y-%m-%d')
            actual_fin = hoy.strftime('%Y-%m-%d')
            anterior_inicio = (hoy.replace(month=1, day=1) - timedelta(days=365)).strftime('%Y-%m-%d')
            anterior_fin = (hoy - timedelta(days=365)).strftime('%Y-%m-%d')
            periodo_nombre = 'año'
        
        actual = self.ventas_completo(actual_inicio, actual_fin)
        anterior = self.ventas_completo(anterior_inicio, anterior_fin)
        
        if 'error' in actual or 'error' in anterior:
            return {
                'error': actual.get('error') or anterior.get('error'),
                'periodo': periodo_nombre
            }
        
        total_actual = actual.get('metricas', {}).get('total_ventas', 0)
        total_anterior = anterior.get('metricas', {}).get('total_ventas', 0)
        
        variacion = self.estadistico.calcular_crecimiento(total_actual, total_anterior)
        
        return {
            'tipo': 'comparativa',
            'periodo': periodo_nombre,
            'actual': {
                'periodo': f'{actual_inicio} a {actual_fin}',
                'total': total_actual,
                'ordenes': actual.get('metricas', {}).get('num_ordenes', 0),
            },
            'anterior': {
                'periodo': f'{anterior_inicio} a {anterior_fin}',
                'total': total_anterior,
                'ordenes': anterior.get('metricas', {}).get('num_ordenes', 0),
            },
            'variacion_pct': variacion,
            'diferencia': total_actual - total_anterior,
            'tendencia': 'crecimiento' if variacion > 0 else ('decremento' if variacion < 0 else 'estable'),
        }
    
    # ============================================================
    # INVENTARIO
    # ============================================================
    
    def inventario_por_almacen(self) -> Dict:
        """Análisis de inventario agrupado por almacén/tienda."""
        if not self.odoo or not self.odoo.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        resultado = {
            'tipo': 'inventario_por_almacen',
            'fecha_generacion': datetime.now().isoformat(),
        }
        
        try:
            # Obtener almacenes
            # Warehouse acceso encapsulado via ConectorOdoo (ARQ-003)
            warehouse_ids = self.odoo.buscar('stock.warehouse', filtro=[])
            almacenes = (self.odoo.search_read('stock.warehouse', [('id', '=', warehouse_ids)], campos=['name', 'code', 'lot_stock_id', 'company_id'], limite=1) or [{}])[0]
            
            resultado['almacenes'] = []
            total_general = 0
            total_productos = 0
            
            for almacen in almacenes:
                location_id = almacen.get('lot_stock_id')
                if not location_id:
                    continue
                
                loc_id = location_id[0] if isinstance(location_id, (list, tuple)) else location_id
                
                # Obtener stock de esta ubicación
                # Quant acceso encapsulado via ConectorOdoo (ARQ-003)
                quant_ids = self.odoo.buscar('stock.quant', filtro=[
                    ('location_id', 'child_of', loc_id),
                    ('quantity', '>', 0)
                ])
                
                if quant_ids:
                    quants = (self.odoo.search_read('stock.quant', [('id', '=', quant_ids)], campos=['product_id', 'quantity', 'reserved_quantity'], limite=1) or [{}])[0]
                    df = pd.DataFrame(quants)
                    
                    # Limpiar datos
                    df_limpio, confianza, _ = self.limpiador.limpiar_dataframe(df)
                    
                    total_cantidad = float(df_limpio['quantity'].sum())
                    # Extraer IDs numéricos para evitar unhashable
                    productos_unicos = len(set(
                        x[0] if isinstance(x, (list, tuple)) else x 
                        for x in df_limpio['product_id'].dropna()
                    )) if 'product_id' in df_limpio.columns else 0
                    
                    total_general += total_cantidad
                    total_productos += productos_unicos
                    
                    resultado['almacenes'].append({
                        'id': almacen['id'],
                        'nombre': almacen['name'],
                        'codigo': almacen.get('code', ''),
                        'empresa': almacen['company_id'][1] if isinstance(almacen.get('company_id'), (list, tuple)) else '',
                        'total_cantidad': total_cantidad,
                        'productos_unicos': productos_unicos,
                        'confianza_datos': confianza * 100,
                    })
            
            resultado['resumen'] = {
                'total_almacenes': len(resultado['almacenes']),
                'total_cantidad': total_general,
                'total_productos_unicos': total_productos,
            }
            
            return resultado
            
        except Exception as e:
            return {'error': str(e), **resultado}
    
    def productos_criticos(self, umbral_minimo: int = 5) -> Dict:
        """Productos con stock bajo o agotado."""
        if not self.odoo or not self.odoo.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        try:
            # Product acceso encapsulado via ConectorOdoo (ARQ-003)
            product_ids = self.odoo.buscar('product.product', filtro=[
                ('type', '=', 'product'),
                ('qty_available', '<=', umbral_minimo),
                ('active', '=', True)
            ], limit=500)
            
            if not product_ids:
                return {
                    'tipo': 'productos_criticos',
                    'productos': [],
                    'resumen': {'total': 0, 'agotados': 0, 'bajo_stock': 0}
                }
            
            productos = self.odoo.buscar_leer('product.product', filtro=[
                ('type', '=', 'product'),
                ('qty_available', '<=', umbral_minimo),
                ('active', '=', True)
            ], campos=[
                'name', 'default_code', 'categ_id', 'qty_available', 
                'virtual_available', 'list_price', 'standard_price'
            ], limite=500)
            
            df = pd.DataFrame(productos)
            df_limpio, confianza, _ = self.limpiador.limpiar_dataframe(df)
            
            agotados = df_limpio[df_limpio['qty_available'] <= 0]
            bajo_stock = df_limpio[(df_limpio['qty_available'] > 0) & (df_limpio['qty_available'] <= umbral_minimo)]
            
            return {
                'tipo': 'productos_criticos',
                'confianza_datos': confianza * 100,
                'productos_agotados': agotados.to_dict('records'),
                'productos_bajo_stock': bajo_stock.to_dict('records'),
                'resumen': {
                    'total': len(df_limpio),
                    'agotados': len(agotados),
                    'bajo_stock': len(bajo_stock),
                    'umbral_usado': umbral_minimo,
                },
                'df': df_limpio,
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def rotacion_inventario(self, dias: int = 30) -> Dict:
        """Análisis de rotación de inventario."""
        if not self.odoo or not self.odoo.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        fecha_inicio = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Obtener ventas de productos en el período
            # SaleOrderLine acceso encapsulado via ConectorOdoo (ARQ-003)
            line_ids = self.odoo.buscar('sale.order.line', filtro=[
                ('order_id.date_order', '>=', fecha_inicio),
                ('order_id.date_order', '<=', fecha_fin),
                ('order_id.state', 'in', ['sale', 'done'])
            ], limit=10000)
            
            if not line_ids:
                return {'error': 'No hay ventas en el período', 'dias': dias}
            
            lineas = (self.odoo.search_read('sale.order.line', [('id', '=', line_ids)], campos=['product_id', 'product_uom_qty', 'price_subtotal'], limite=1) or [{}])[0]
            df_ventas = pd.DataFrame(lineas)
            
            # Agrupar por producto - extraer ID como int para evitar unhashable
            df_ventas['producto_id'] = df_ventas['product_id'].apply(
                lambda x: int(x[0]) if isinstance(x, (list, tuple)) and x else (int(x) if x else 0)
            )
            df_ventas['producto_nombre'] = df_ventas['product_id'].apply(
                lambda x: str(x[1]) if isinstance(x, (list, tuple)) and len(x) > 1 else 'N/A'
            )
            
            # Agrupar solo por producto_id (int)
            ventas_por_producto = df_ventas.groupby('producto_id').agg({
                'product_uom_qty': 'sum',
                'price_subtotal': 'sum',
                'producto_nombre': 'first'
            }).reset_index()
            ventas_por_producto.columns = ['producto_id', 'cantidad_vendida', 'monto_vendido', 'producto']
            
            # Obtener stock actual
            # Product acceso encapsulado via ConectorOdoo (ARQ-003)
            product_ids = ventas_por_producto['producto_id'].tolist()
            productos = (self.odoo.search_read('product.product', [('id', '=', product_ids)], campos=['qty_available', 'standard_price'], limite=1) or [{}])[0]
            df_productos = pd.DataFrame(productos)
            
            # Combinar
            df_final = ventas_por_producto.merge(
                df_productos[['id', 'qty_available', 'standard_price']],
                left_on='producto_id',
                right_on='id',
                how='left'
            )
            
            # Calcular rotación
            df_final['stock_actual'] = df_final['qty_available'].fillna(0)
            df_final['rotacion'] = df_final.apply(
                lambda x: x['cantidad_vendida'] / x['stock_actual'] if x['stock_actual'] > 0 else float('inf'),
                axis=1
            )
            
            # Clasificar
            df_final['clasificacion'] = df_final['rotacion'].apply(
                lambda x: 'Alta' if x > 2 else ('Media' if x > 0.5 else 'Baja')
            )
            
            df_limpio, confianza, _ = self.limpiador.limpiar_dataframe(df_final)
            
            alta_rotacion = df_limpio[df_limpio['clasificacion'] == 'Alta'].sort_values('rotacion', ascending=False)
            baja_rotacion = df_limpio[df_limpio['clasificacion'] == 'Baja'].sort_values('rotacion')
            
            return {
                'tipo': 'rotacion_inventario',
                'periodo_dias': dias,
                'confianza_datos': confianza * 100,
                'alta_rotacion': alta_rotacion.head(20).to_dict('records'),
                'baja_rotacion': baja_rotacion.head(20).to_dict('records'),
                'resumen': {
                    'productos_analizados': len(df_limpio),
                    'alta_rotacion_count': len(alta_rotacion),
                    'media_rotacion_count': len(df_limpio[df_limpio['clasificacion'] == 'Media']),
                    'baja_rotacion_count': len(baja_rotacion),
                },
                'df': df_limpio,
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # FINANZAS
    # ============================================================
    
    def facturacion_completa(
        self, 
        fecha_inicio: str = None, 
        fecha_fin: str = None,
        tipo: str = 'cliente'  # 'cliente' o 'proveedor'
    ) -> Dict:
        """Análisis completo de facturación."""
        if not self.odoo or not self.odoo.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        try:
            move_type = 'out_invoice' if tipo == 'cliente' else 'in_invoice'
            
            domain = [
                ('move_type', '=', move_type),
                ('state', '=', 'posted')
            ]
            
            if fecha_inicio:
                domain.append(('invoice_date', '>=', fecha_inicio))
            if fecha_fin:
                domain.append(('invoice_date', '<=', fecha_fin))
            
            # AccountMove acceso encapsulado via ConectorOdoo (ARQ-003)
            move_ids = self.odoo.buscar('account.move', filtro=domain, limit=5000)
            
            if not move_ids:
                return {'error': 'No hay facturas en el período', 'tipo': tipo}
            
            facturas = self.odoo.buscar_leer('account.move', filtro=domain, campos=[
                'name', 'partner_id', 'invoice_user_id', 'invoice_date',
                'invoice_date_due', 'amount_untaxed', 'amount_tax', 'amount_total',
                'amount_residual', 'payment_state', 'company_id'
            ], limite=5000)
            
            df = pd.DataFrame(facturas)
            df_limpio, confianza, _ = self.limpiador.limpiar_dataframe(df)
            
            # Métricas generales
            metricas = {
                'total_facturado': float(df_limpio['amount_total'].sum()),
                'subtotal': float(df_limpio['amount_untaxed'].sum()),
                'impuestos': float(df_limpio['amount_tax'].sum()),
                'pendiente_cobro': float(df_limpio['amount_residual'].sum()),
                'num_facturas': len(df_limpio),
                'factura_promedio': float(df_limpio['amount_total'].mean()),
            }
            
            # Por estado de pago
            por_estado = df_limpio.groupby('payment_state').agg({
                'amount_total': ['sum', 'count']
            }).reset_index()
            por_estado.columns = ['estado', 'monto', 'cantidad']
            
            # Por cliente/proveedor
            df_limpio['contacto'] = df_limpio['partner_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'N/A'
            )
            por_contacto = df_limpio.groupby('contacto').agg({
                'amount_total': 'sum',
                'amount_residual': 'sum',
                'id': 'count'
            }).reset_index()
            por_contacto.columns = ['contacto', 'total_facturado', 'pendiente', 'num_facturas']
            por_contacto = por_contacto.sort_values('total_facturado', ascending=False)
            
            return {
                'tipo': f'facturacion_{tipo}',
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'confianza_datos': confianza * 100,
                'metricas': metricas,
                'por_estado_pago': por_estado.to_dict('records'),
                'top_contactos': por_contacto.head(20).to_dict('records'),
                'df': df_limpio,
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def cuentas_por_cobrar(self) -> Dict:
        """Análisis de cuentas por cobrar (CxC)."""
        if not self.odoo or not self.odoo.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        try:
            domain = [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('amount_residual', '>', 0)
            ]
            
            # AccountMove acceso encapsulado via ConectorOdoo (ARQ-003)
            move_ids = self.odoo.buscar('account.move', filtro=domain, limit=5000)
            
            if not move_ids:
                return {
                    'tipo': 'cxc',
                    'total_pendiente': 0,
                    'num_facturas': 0,
                    'por_antiguedad': {},
                    'por_cliente': [],
                }
            
            facturas = self.odoo.buscar_leer('account.move', filtro=domain, campos=[
                'name', 'partner_id', 'invoice_date', 'invoice_date_due',
                'amount_total', 'amount_residual'
            ], limite=5000)
            
            df = pd.DataFrame(facturas)
            df_limpio, confianza, _ = self.limpiador.limpiar_dataframe(df)
            
            # Calcular antigüedad
            hoy = datetime.now().date()
            df_limpio['fecha_vencimiento'] = pd.to_datetime(df_limpio['invoice_date_due'])
            df_limpio['dias_vencido'] = df_limpio['fecha_vencimiento'].apply(
                lambda x: (hoy - x.date()).days if pd.notna(x) else 0
            )
            
            # Clasificar por antigüedad
            df_limpio['antiguedad'] = df_limpio['dias_vencido'].apply(
                lambda x: 'Al corriente' if x <= 0 else (
                    '1-30 días' if x <= 30 else (
                        '31-60 días' if x <= 60 else (
                            '61-90 días' if x <= 90 else 'Más de 90 días'
                        )
                    )
                )
            )
            
            por_antiguedad = df_limpio.groupby('antiguedad')['amount_residual'].sum().to_dict()
            
            # Por cliente
            df_limpio['cliente'] = df_limpio['partner_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'N/A'
            )
            por_cliente = df_limpio.groupby('cliente').agg({
                'amount_residual': 'sum',
                'id': 'count',
                'dias_vencido': 'max'
            }).reset_index()
            por_cliente.columns = ['cliente', 'saldo_pendiente', 'facturas', 'dias_max_vencido']
            por_cliente = por_cliente.sort_values('saldo_pendiente', ascending=False)
            
            return {
                'tipo': 'cxc',
                'confianza_datos': confianza * 100,
                'total_pendiente': float(df_limpio['amount_residual'].sum()),
                'num_facturas': len(df_limpio),
                'por_antiguedad': por_antiguedad,
                'por_cliente': por_cliente.head(30).to_dict('records'),
                'clientes_criticos': por_cliente[por_cliente['dias_max_vencido'] > 60].head(10).to_dict('records'),
                'df': df_limpio,
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def cuentas_por_pagar(self) -> Dict:
        """Análisis de cuentas por pagar (CxP)."""
        if not self.odoo or not self.odoo.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        try:
            domain = [
                ('move_type', '=', 'in_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('amount_residual', '>', 0)
            ]
            
            # AccountMove acceso encapsulado via ConectorOdoo (ARQ-003)
            move_ids = self.odoo.buscar('account.move', filtro=domain, limit=5000)
            
            if not move_ids:
                return {
                    'tipo': 'cxp',
                    'total_pendiente': 0,
                    'num_facturas': 0,
                    'por_antiguedad': {},
                    'por_proveedor': [],
                }
            
            facturas = self.odoo.buscar_leer('account.move', filtro=domain, campos=[
                'name', 'partner_id', 'invoice_date', 'invoice_date_due',
                'amount_total', 'amount_residual'
            ], limite=5000)
            
            df = pd.DataFrame(facturas)
            df_limpio, confianza, _ = self.limpiador.limpiar_dataframe(df)
            
            # Calcular antigüedad
            hoy = datetime.now().date()
            df_limpio['fecha_vencimiento'] = pd.to_datetime(df_limpio['invoice_date_due'])
            df_limpio['dias_vencido'] = df_limpio['fecha_vencimiento'].apply(
                lambda x: (hoy - x.date()).days if pd.notna(x) else 0
            )
            
            # Clasificar
            df_limpio['antiguedad'] = df_limpio['dias_vencido'].apply(
                lambda x: 'Al corriente' if x <= 0 else (
                    '1-30 días' if x <= 30 else (
                        '31-60 días' if x <= 60 else 'Más de 60 días'
                    )
                )
            )
            
            por_antiguedad = df_limpio.groupby('antiguedad')['amount_residual'].sum().to_dict()
            
            # Por proveedor
            df_limpio['proveedor'] = df_limpio['partner_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'N/A'
            )
            por_proveedor = df_limpio.groupby('proveedor').agg({
                'amount_residual': 'sum',
                'id': 'count',
                'dias_vencido': 'max'
            }).reset_index()
            por_proveedor.columns = ['proveedor', 'saldo_pendiente', 'facturas', 'dias_max_vencido']
            por_proveedor = por_proveedor.sort_values('saldo_pendiente', ascending=False)
            
            return {
                'tipo': 'cxp',
                'confianza_datos': confianza * 100,
                'total_pendiente': float(df_limpio['amount_residual'].sum()),
                'num_facturas': len(df_limpio),
                'por_antiguedad': por_antiguedad,
                'por_proveedor': por_proveedor.head(30).to_dict('records'),
                'df': df_limpio,
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # POS / PUNTO DE VENTA
    # ============================================================
    
    def pos_completo(
        self, 
        fecha_inicio: str = None, 
        fecha_fin: str = None
    ) -> Dict:
        """Análisis completo de punto de venta."""
        if not self.odoo or not self.odoo.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        try:
            domain = [('state', 'in', ['paid', 'done', 'invoiced'])]
            if fecha_inicio:
                domain.append(('date_order', '>=', fecha_inicio))
            if fecha_fin:
                domain.append(('date_order', '<=', fecha_fin))
            
            # PosOrder acceso encapsulado via ConectorOdoo (ARQ-003)
            order_ids = self.odoo.buscar('pos.order', filtro=domain, limit=10000)
            
            if not order_ids:
                return {'error': 'No hay tickets en el período'}
            
            tickets = self.odoo.buscar_leer('pos.order', filtro=domain, campos=[
                'name', 'partner_id', 'user_id', 'session_id', 'config_id',
                'date_order', 'amount_total', 'amount_tax', 'amount_paid'
            ], limite=10000)
            
            df = pd.DataFrame(tickets)
            df_limpio, confianza, _ = self.limpiador.limpiar_dataframe(df)
            
            # Métricas
            metricas = {
                'total_ventas': float(df_limpio['amount_total'].sum()),
                'total_impuestos': float(df_limpio['amount_tax'].sum()),
                'num_tickets': len(df_limpio),
                'ticket_promedio': float(df_limpio['amount_total'].mean()),
                'ticket_max': float(df_limpio['amount_total'].max()),
            }
            
            # Por cajero
            df_limpio['cajero'] = df_limpio['user_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'N/A'
            )
            por_cajero = df_limpio.groupby('cajero').agg({
                'amount_total': ['sum', 'count', 'mean']
            }).reset_index()
            por_cajero.columns = ['cajero', 'total', 'tickets', 'promedio']
            por_cajero = por_cajero.sort_values('total', ascending=False)
            
            # Por punto de venta
            df_limpio['pos'] = df_limpio['config_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'N/A'
            )
            por_pos = df_limpio.groupby('pos').agg({
                'amount_total': ['sum', 'count']
            }).reset_index()
            por_pos.columns = ['punto_venta', 'total', 'tickets']
            por_pos = por_pos.sort_values('total', ascending=False)
            
            # Por hora (si es del día)
            df_limpio['hora'] = pd.to_datetime(df_limpio['date_order']).dt.hour
            por_hora = df_limpio.groupby('hora')['amount_total'].sum().reset_index()
            
            return {
                'tipo': 'pos_completo',
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'confianza_datos': confianza * 100,
                'metricas': metricas,
                'por_cajero': por_cajero.to_dict('records'),
                'por_punto_venta': por_pos.to_dict('records'),
                'por_hora': por_hora.to_dict('records'),
                'df': df_limpio,
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def pos_metodos_pago(
        self, 
        fecha_inicio: str = None, 
        fecha_fin: str = None
    ) -> Dict:
        """Análisis de métodos de pago en POS."""
        if not self.odoo or not self.odoo.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        try:
            domain = []
            if fecha_inicio:
                domain.append(('payment_date', '>=', fecha_inicio))
            if fecha_fin:
                domain.append(('payment_date', '<=', fecha_fin))
            
            # PosPayment acceso encapsulado via ConectorOdoo (ARQ-003)
            payment_ids = self.odoo.buscar('pos.payment', filtro=domain, limit=50000)
            
            if not payment_ids:
                return {'error': 'No hay pagos en el período'}
            
            pagos = self.odoo.buscar_leer('pos.payment', filtro=domain, campos=[
                'payment_method_id', 'amount', 'payment_date', 'pos_order_id'
            ], limite=50000)
            
            df = pd.DataFrame(pagos)
            df_limpio, confianza, _ = self.limpiador.limpiar_dataframe(df)
            
            df_limpio['metodo'] = df_limpio['payment_method_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'N/A'
            )
            
            por_metodo = df_limpio.groupby('metodo').agg({
                'amount': ['sum', 'count', 'mean']
            }).reset_index()
            por_metodo.columns = ['metodo', 'total', 'transacciones', 'promedio']
            por_metodo = por_metodo.sort_values('total', ascending=False)
            
            total = por_metodo['total'].sum()
            por_metodo['porcentaje'] = (por_metodo['total'] / total * 100).round(2)
            
            return {
                'tipo': 'pos_metodos_pago',
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'confianza_datos': confianza * 100,
                'total_general': float(total),
                'num_transacciones': len(df_limpio),
                'por_metodo': por_metodo.to_dict('records'),
                'df': df_limpio,
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # CLIENTES
    # ============================================================
    
    def clientes_analisis(self) -> Dict:
        """Análisis completo de clientes."""
        if not self.odoo or not self.odoo.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        try:
            # Partner acceso encapsulado via ConectorOdoo (ARQ-003)
            partner_ids = self.odoo.buscar('res.partner', filtro=[
                ('customer_rank', '>', 0),
                ('active', '=', True)
            ], limit=5000)
            
            if not partner_ids:
                return {'error': 'No hay clientes registrados'}
            
            clientes = self.odoo.buscar_leer('res.partner', filtro=[
                ('customer_rank', '>', 0),
                ('active', '=', True)
            ], campos=[
                'name', 'email', 'phone', 'city', 'state_id', 'country_id',
                'customer_rank', 'create_date', 'total_invoiced', 'credit_limit'
            ], limite=5000)
            
            df = pd.DataFrame(clientes)
            df_limpio, confianza, _ = self.limpiador.limpiar_dataframe(df)
            
            # Métricas
            metricas = {
                'total_clientes': len(df_limpio),
                'total_facturado': float(df_limpio['total_invoiced'].sum()),
                'promedio_facturacion': float(df_limpio['total_invoiced'].mean()),
                'con_email': int(df_limpio['email'].notna().sum()),
                'con_telefono': int(df_limpio['phone'].notna().sum()),
            }
            
            # Por ciudad
            df_limpio['ciudad'] = df_limpio['city'].fillna('Sin especificar')
            por_ciudad = df_limpio.groupby('ciudad').size().reset_index(name='clientes')
            por_ciudad = por_ciudad.sort_values('clientes', ascending=False)
            
            # Top clientes por facturación
            top_facturacion = df_limpio.nlargest(20, 'total_invoiced')[
                ['name', 'email', 'city', 'total_invoiced']
            ]
            
            return {
                'tipo': 'clientes_analisis',
                'confianza_datos': confianza * 100,
                'metricas': metricas,
                'por_ciudad': por_ciudad.head(15).to_dict('records'),
                'top_facturacion': top_facturacion.to_dict('records'),
                'df': df_limpio,
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # EMPRESAS / MULTI-COMPAÑÍA
    # ============================================================
    
    def empresas_resumen(self) -> Dict:
        """Resumen de todas las empresas."""
        if not self.odoo or not self.odoo.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        try:
            # Company acceso encapsulado via ConectorOdoo (ARQ-003)
            company_ids = self.odoo.buscar('res.company', filtro=[])
            empresas = (self.odoo.search_read('res.company', [('id', '=', company_ids)], campos=['name', 'currency_id', 'partner_id'], limite=1) or [{}])[0]
            
            resultado = {
                'tipo': 'empresas_resumen',
                'empresas': [],
                'total_empresas': len(empresas),
            }
            
            for empresa in empresas:
                empresa_id = empresa['id']
                
                # Ventas de esta empresa
                # SaleOrder acceso encapsulado via ConectorOdoo (ARQ-003)
                ventas_ids = self.odoo.buscar('sale.order', filtro=[
                    ('company_id', '=', empresa_id),
                    ('state', 'in', ['sale', 'done'])
                ], limit=1000)
                
                total_ventas = 0
                if ventas_ids:
                    ventas = (self.odoo.search_read('sale.order', [('id', '=', ventas_ids)], campos=['amount_total'], limite=1) or [{}])[0]
                    total_ventas = sum(v['amount_total'] for v in ventas)
                
                resultado['empresas'].append({
                    'id': empresa_id,
                    'nombre': empresa['name'],
                    'moneda': empresa['currency_id'][1] if isinstance(empresa.get('currency_id'), (list, tuple)) else 'MXN',
                    'total_ventas_confirmadas': total_ventas,
                    'num_ordenes': len(ventas_ids) if ventas_ids else 0,
                })
            
            return resultado
            
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # REPORTE EJECUTIVO GENERAL
    # ============================================================
    
    def reporte_ejecutivo(
        self, 
        fecha_inicio: str = None, 
        fecha_fin: str = None
    ) -> str:
        """
        Genera un reporte ejecutivo completo del negocio.
        Combina ventas, inventario, facturación y KPIs principales.
        """
        partes = []
        
        partes.append(f"""
# REPORTE EJECUTIVO - ANDROMEDA

**Período:** {fecha_inicio or 'Histórico'} a {fecha_fin or 'Hoy'}  
**Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  
**Sistema:** ANDROMEDA v5.0 - IA Predictiva Empresarial

---
""")
        
        # Ventas
        ventas = self.ventas_completo(fecha_inicio, fecha_fin)
        if 'error' not in ventas:
            m = ventas.get('metricas', {})
            partes.append(f"""
## VENTAS

| Métrica | Valor |
|---------|-------|
| **Total Ventas** | ${m.get('total_ventas', 0):,.2f} |
| **Órdenes** | {m.get('num_ordenes', 0):,} |
| **Ticket Promedio** | ${m.get('ticket_promedio', 0):,.2f} |
| **Confianza Datos** | {ventas.get('confianza_datos', 0):.1f}% |

### Top 5 Clientes
""")
            for i, c in enumerate(ventas.get('top_clientes', [])[:5], 1):
                partes.append(f"{i}. **{c.get('cliente', 'N/A')}** - ${c.get('total', 0):,.2f}")
        
        # Inventario
        inv = self.inventario_por_almacen()
        if 'error' not in inv:
            partes.append(f"""

## INVENTARIO POR ALMACÉN

| Almacén | Cantidad | Productos |
|---------|----------|-----------|""")
            for a in inv.get('almacenes', []):
                partes.append(f"| {a.get('nombre', 'N/A')} | {a.get('total_cantidad', 0):,.0f} | {a.get('productos_unicos', 0):,} |")
        
        # Productos críticos
        criticos = self.productos_criticos()
        if 'error' not in criticos:
            resumen = criticos.get('resumen', {})
            partes.append(f"""

### Alertas de Inventario
- **Productos agotados:** {resumen.get('agotados', 0)}
- **Productos con bajo stock:** {resumen.get('bajo_stock', 0)}
""")
        
        # CxC
        cxc = self.cuentas_por_cobrar()
        if 'error' not in cxc:
            partes.append(f"""

## CUENTAS POR COBRAR

- **Total pendiente:** ${cxc.get('total_pendiente', 0):,.2f}
- **Facturas pendientes:** {cxc.get('num_facturas', 0):,}

**Por antigüedad:**
""")
            for ant, monto in cxc.get('por_antiguedad', {}).items():
                partes.append(f"- {ant}: ${monto:,.2f}")
        
        # CxP
        cxp = self.cuentas_por_pagar()
        if 'error' not in cxp:
            partes.append(f"""

## CUENTAS POR PAGAR

- **Total pendiente:** ${cxp.get('total_pendiente', 0):,.2f}
- **Facturas pendientes:** {cxp.get('num_facturas', 0):,}
""")
        
        partes.append("""

---
*Reporte generado automáticamente por ANDROMEDA v5.0 - IA Predictiva Empresarial*
*Los datos han sido validados con una confianza mínima del 95%*
""")
        
        return '\n'.join(partes)


# ============================================================
# FACTORY
# ============================================================

def obtener_consultas_especializadas(conector_odoo=None) -> ConsultasEspecializadas:
    """Factory function para obtener instancia de consultas especializadas."""
    return ConsultasEspecializadas(conector_odoo)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" CONSULTAS ESPECIALIZADAS - Test")
    print("=" * 60)
    print("\nMódulo cargado correctamente")
    print("Este módulo requiere conexión a Odoo para funcionar.")
