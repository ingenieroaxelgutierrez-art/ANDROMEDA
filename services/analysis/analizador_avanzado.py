# ============================================================
# ANALIZADOR AVANZADO - Múltiples Áreas de Negocio
# ============================================================
# Análisis completo para Ventas, POS, Facturación, Inventario,
# Compras, RH, CRM y más
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

from app.logging_config import get_logger
logger = get_logger("services.analysis.analizador_avanzado")


class AnalizadorAvanzado:
    """Motor de análisis avanzado para todas las áreas de Odoo."""
    
    def __init__(self, conector_odoo=None):
        self.odoo = conector_odoo
        self.cache = {}
    
    def set_conector(self, conector):
        """Asigna el conector de Odoo."""
        self.odoo = conector
    
    # ========================================================
    # ANÁLISIS DE VENTAS
    # ========================================================
    
    def analisis_ventas_completo(self, fecha_inicio: str, fecha_fin: str) -> Dict:
        """Análisis completo de ventas."""
        try:
            ventas = self.odoo.ventas_periodo(fecha_inicio, fecha_fin)
            if ventas.empty:
                return {'error': 'No hay ventas en el período'}
            
            resultado = {
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'resumen': {
                    'total_ordenes': len(ventas),
                    'monto_total': float(ventas['amount_total'].sum()),
                    'ticket_promedio': float(ventas['amount_total'].mean()),
                    'maximo': float(ventas['amount_total'].max()),
                    'minimo': float(ventas['amount_total'].min()),
                },
                'por_estado': {},
                'por_cliente': [],
                'por_vendedor': [],
                'por_dia': [],
                'tendencia': '',
                'insights': []
            }
            
            # Por estado
            if 'state' in ventas.columns:
                estados = ventas.groupby('state')['amount_total'].agg(['count', 'sum'])
                resultado['por_estado'] = estados.to_dict('index')
            
            # Por cliente (top 10)
            if 'partner_id' in ventas.columns:
                ventas['cliente'] = ventas['partner_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                )
                top_clientes = ventas.groupby('cliente')['amount_total'].agg(['count', 'sum'])\
                    .sort_values('sum', ascending=False).head(10)
                resultado['por_cliente'] = top_clientes.reset_index().to_dict('records')
            
            # Por vendedor (si existe)
            if 'user_id' in ventas.columns:
                ventas['vendedor'] = ventas['user_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                )
                top_vendedores = ventas.groupby('vendedor')['amount_total'].agg(['count', 'sum'])\
                    .sort_values('sum', ascending=False).head(10)
                resultado['por_vendedor'] = top_vendedores.reset_index().to_dict('records')
            
            # Por día
            if 'date_order' in ventas.columns:
                ventas['fecha'] = pd.to_datetime(ventas['date_order']).dt.date
                por_dia = ventas.groupby('fecha')['amount_total'].agg(['count', 'sum'])
                resultado['por_dia'] = por_dia.reset_index().to_dict('records')
                
                # Tendencia
                if len(por_dia) > 1:
                    valores = por_dia['sum'].values
                    if valores[-1] > valores[0]:
                        resultado['tendencia'] = 'alza'
                    elif valores[-1] < valores[0]:
                        resultado['tendencia'] = 'baja'
                    else:
                        resultado['tendencia'] = 'estable'
            
            # Insights automáticos
            resultado['insights'] = self._generar_insights_ventas(resultado)
            
            return resultado
            
        except Exception as e:
            return {'error': str(e)}
    
    def _generar_insights_ventas(self, datos: Dict) -> List[str]:
        """Genera insights automáticos de ventas."""
        insights = []
        resumen = datos.get('resumen', {})
        
        total = resumen.get('monto_total', 0)
        if total > 0:
            promedio = resumen.get('ticket_promedio', 0)
            ordenes = resumen.get('total_ordenes', 0)
            
            insights.append(f"Total generado: ${total:,.2f} en {ordenes} órdenes")
            insights.append(f"Ticket promedio: ${promedio:,.2f}")
            
            # Mejor cliente
            clientes = datos.get('por_cliente', [])
            if clientes:
                mejor = clientes[0]
                insights.append(f"Mejor cliente: {mejor.get('cliente', 'N/A')} (${mejor.get('sum', 0):,.2f})")
            
            # Tendencia
            tendencia = datos.get('tendencia', '')
            if tendencia == 'alza':
                insights.append("Tendencia: Las ventas van EN ALZA")
            elif tendencia == 'baja':
                insights.append("Tendencia: Las ventas van A LA BAJA")
        
        return insights
    
    def top_productos_vendidos(self, fecha_inicio: str, fecha_fin: str, limite: int = 20) -> Dict:
        """Top productos más vendidos."""
        try:
            lineas = self.odoo.buscar(
                'sale.order.line',
                filtro=[
                    ('order_id.date_order', '>=', fecha_inicio),
                    ('order_id.date_order', '<=', fecha_fin + " 23:59:59"),
                    ('order_id.state', 'in', ['sale', 'done'])
                ],
                campos=['product_id', 'product_uom_qty', 'price_subtotal', 'discount'],
                limite=5000
            )
            
            if lineas.empty:
                return {'error': 'No hay datos'}
            
            lineas['producto'] = lineas['product_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
            )
            
            agrupado = lineas.groupby('producto').agg({
                'product_uom_qty': 'sum',
                'price_subtotal': 'sum'
            }).sort_values('price_subtotal', ascending=False).head(limite)
            
            agrupado['margen_desc'] = lineas.groupby('producto')['discount'].mean()
            
            return {
                'productos': agrupado.reset_index().to_dict('records'),
                'total_productos': len(set(str(p) for p in lineas['producto'])),
                'total_unidades': int(lineas['product_uom_qty'].sum()),
                'total_ingresos': float(lineas['price_subtotal'].sum())
            }
        except Exception as e:
            return {'error': str(e)}
    
    def comparativa_periodos(self, tipo: str = 'dia') -> Dict:
        """Compara períodos (hoy vs ayer, semana actual vs anterior, etc.)."""
        hoy = datetime.now()
        
        if tipo == 'dia':
            actual_ini = actual_fin = hoy.strftime('%Y-%m-%d')
            anterior = hoy - timedelta(days=1)
            anterior_ini = anterior_fin = anterior.strftime('%Y-%m-%d')
            nombre_actual = "Hoy"
            nombre_anterior = "Ayer"
        
        elif tipo == 'semana':
            actual_ini = (hoy - timedelta(days=hoy.weekday())).strftime('%Y-%m-%d')
            actual_fin = hoy.strftime('%Y-%m-%d')
            sem_ant_inicio = hoy - timedelta(days=hoy.weekday() + 7)
            anterior_ini = sem_ant_inicio.strftime('%Y-%m-%d')
            anterior_fin = (sem_ant_inicio + timedelta(days=6)).strftime('%Y-%m-%d')
            nombre_actual = "Esta semana"
            nombre_anterior = "Semana pasada"
        
        elif tipo == 'mes':
            actual_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
            actual_fin = hoy.strftime('%Y-%m-%d')
            mes_ant = (hoy.replace(day=1) - timedelta(days=1))
            anterior_ini = mes_ant.replace(day=1).strftime('%Y-%m-%d')
            anterior_fin = mes_ant.strftime('%Y-%m-%d')
            nombre_actual = "Este mes"
            nombre_anterior = "Mes pasado"
        else:
            return {'error': 'Tipo no válido'}
        
        try:
            v_actual = self.odoo.ventas_periodo(actual_ini, actual_fin)
            v_anterior = self.odoo.ventas_periodo(anterior_ini, anterior_fin)
            
            total_actual = v_actual['amount_total'].sum() if not v_actual.empty else 0
            total_anterior = v_anterior['amount_total'].sum() if not v_anterior.empty else 0
            
            diferencia = total_actual - total_anterior
            porcentaje = (diferencia / total_anterior * 100) if total_anterior > 0 else 0
            
            return {
                'actual': {
                    'nombre': nombre_actual,
                    'inicio': actual_ini,
                    'fin': actual_fin,
                    'ordenes': len(v_actual),
                    'total': float(total_actual)
                },
                'anterior': {
                    'nombre': nombre_anterior,
                    'inicio': anterior_ini,
                    'fin': anterior_fin,
                    'ordenes': len(v_anterior),
                    'total': float(total_anterior)
                },
                'diferencia': float(diferencia),
                'porcentaje': float(porcentaje),
                'tendencia': 'alza' if diferencia > 0 else 'baja' if diferencia < 0 else 'igual'
            }
        except Exception as e:
            return {'error': str(e)}
    
    # ========================================================
    # ANÁLISIS DE POS
    # ========================================================
    
    def analisis_pos_completo(self, fecha_inicio: str, fecha_fin: str) -> Dict:
        """Análisis completo de punto de venta."""
        try:
            tickets = self.odoo.tickets_pos(fecha_inicio, fecha_fin)
            if tickets.empty:
                return {'error': 'No hay tickets POS'}
            
            resultado = {
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'resumen': {
                    'total_tickets': len(tickets),
                    'monto_total': float(tickets['amount_total'].sum()),
                    'ticket_promedio': float(tickets['amount_total'].mean()),
                    'maximo': float(tickets['amount_total'].max()),
                    'minimo': float(tickets['amount_total'].min() if tickets['amount_total'].min() > 0 else 0),
                },
                'por_hora': [],
                'por_sesion': [],
                'por_cajero': [],
                'metodos_pago': [],
                'insights': []
            }
            
            # Por hora del día
            if 'date_order' in tickets.columns:
                tickets['hora'] = pd.to_datetime(tickets['date_order']).dt.hour
                por_hora = tickets.groupby('hora')['amount_total'].agg(['count', 'sum'])
                resultado['por_hora'] = por_hora.reset_index().to_dict('records')
                
                # Hora pico
                hora_pico = por_hora['sum'].idxmax()
                resultado['hora_pico'] = int(hora_pico)
            
            # Por sesión
            if 'session_id' in tickets.columns:
                tickets['sesion'] = tickets['session_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                )
                por_sesion = tickets.groupby('sesion')['amount_total'].agg(['count', 'sum'])
                resultado['por_sesion'] = por_sesion.reset_index().head(10).to_dict('records')
            
            # Por cajero/usuario
            if 'user_id' in tickets.columns:
                tickets['cajero'] = tickets['user_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                )
                por_cajero = tickets.groupby('cajero')['amount_total'].agg(['count', 'sum'])
                resultado['por_cajero'] = por_cajero.reset_index().to_dict('records')
            
            # Insights
            resultado['insights'] = self._generar_insights_pos(resultado)
            
            return resultado
        except Exception as e:
            return {'error': str(e)}
    
    def _generar_insights_pos(self, datos: Dict) -> List[str]:
        """Genera insights de POS."""
        insights = []
        resumen = datos.get('resumen', {})
        
        total = resumen.get('monto_total', 0)
        tickets = resumen.get('total_tickets', 0)
        
        if total > 0:
            insights.append(f"{tickets:,} tickets procesados por ${total:,.2f}")
            insights.append(f"Ticket promedio: ${resumen.get('ticket_promedio', 0):,.2f}")
            
            hora_pico = datos.get('hora_pico')
            if hora_pico is not None:
                insights.append(f"Hora pico de ventas: {hora_pico}:00 hrs")
        
        return insights
    
    def analisis_metodos_pago_pos(self, fecha_inicio: str, fecha_fin: str) -> Dict:
        """Análisis de métodos de pago en POS."""
        try:
            pagos = self.odoo.buscar(
                'pos.payment',
                filtro=[
                    ('payment_date', '>=', fecha_inicio),
                    ('payment_date', '<=', fecha_fin + " 23:59:59")
                ],
                campos=['amount', 'payment_method_id'],
                limite=5000
            )
            
            if pagos.empty:
                return {'error': 'No hay datos de pagos'}
            
            pagos['metodo'] = pagos['payment_method_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) else 'Desconocido'
            )
            
            agrupado = pagos.groupby('metodo')['amount'].agg(['count', 'sum'])
            total = agrupado['sum'].sum()
            agrupado['porcentaje'] = (agrupado['sum'] / total * 100).round(2)
            
            return {
                'metodos': agrupado.reset_index().to_dict('records'),
                'total': float(total)
            }
        except Exception as e:
            return {'error': str(e)}
    
    # ========================================================
    # ANÁLISIS DE FACTURACIÓN
    # ========================================================
    
    def analisis_facturacion(self, fecha_inicio: str, fecha_fin: str, tipo: str = 'out_invoice') -> Dict:
        """Análisis de facturación."""
        try:
            filtro = [
                ('invoice_date', '>=', fecha_inicio),
                ('invoice_date', '<=', fecha_fin),
                ('move_type', '=', tipo),
                ('state', '=', 'posted')
            ]
            
            facturas = self.odoo.buscar(
                'account.move',
                filtro=filtro,
                campos=['name', 'partner_id', 'invoice_date', 'amount_total', 
                       'amount_residual', 'payment_state', 'invoice_user_id'],
                limite=2000
            )
            
            if facturas.empty:
                return {'error': 'No hay facturas en el período'}
            
            resultado = {
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'tipo': 'Facturas Cliente' if tipo == 'out_invoice' else 'Facturas Proveedor',
                'resumen': {
                    'total_facturas': len(facturas),
                    'monto_total': float(facturas['amount_total'].sum()),
                    'saldo_pendiente': float(facturas['amount_residual'].sum()),
                    'cobrado': float(facturas['amount_total'].sum() - facturas['amount_residual'].sum()),
                },
                'por_estado_pago': {},
                'por_cliente': [],
                'insights': []
            }
            
            # Por estado de pago
            if 'payment_state' in facturas.columns:
                estados = facturas.groupby('payment_state')['amount_total'].agg(['count', 'sum'])
                resultado['por_estado_pago'] = estados.to_dict('index')
            
            # Por cliente/proveedor
            if 'partner_id' in facturas.columns:
                facturas['partner'] = facturas['partner_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                )
                por_partner = facturas.groupby('partner').agg({
                    'amount_total': 'sum',
                    'amount_residual': 'sum'
                }).sort_values('amount_total', ascending=False).head(10)
                resultado['por_cliente'] = por_partner.reset_index().to_dict('records')
            
            # Calcular porcentaje cobrado
            total = resultado['resumen']['monto_total']
            cobrado = resultado['resumen']['cobrado']
            resultado['resumen']['porcentaje_cobrado'] = round(cobrado / total * 100, 2) if total > 0 else 0
            
            # Insights
            resultado['insights'] = [
                f"{len(facturas)} facturas por ${total:,.2f}",
                f"Cobrado: ${cobrado:,.2f} ({resultado['resumen']['porcentaje_cobrado']}%)",
                f"Pendiente: ${resultado['resumen']['saldo_pendiente']:,.2f}"
            ]
            
            return resultado
        except Exception as e:
            return {'error': str(e)}
    
    def cuentas_por_cobrar(self) -> Dict:
        """Análisis de cuentas por cobrar."""
        try:
            hoy = datetime.now()
            
            facturas = self.odoo.buscar(
                'account.move',
                filtro=[
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial'])
                ],
                campos=['name', 'partner_id', 'invoice_date', 'invoice_date_due', 
                       'amount_total', 'amount_residual'],
                limite=2000
            )
            
            if facturas.empty:
                return {'total': 0, 'vencido': 0, 'por_vencer': 0, 'clientes': []}
            
            # Calcular antigüedad
            facturas['fecha_venc'] = pd.to_datetime(facturas['invoice_date_due'])
            facturas['dias_vencido'] = (hoy - facturas['fecha_venc']).dt.days
            
            vencidas = facturas[facturas['dias_vencido'] > 0]
            por_vencer = facturas[facturas['dias_vencido'] <= 0]
            
            # Agrupación por antigüedad
            def clasificar_antiguedad(dias):
                if dias <= 0: return '0. Por vencer'
                elif dias <= 30: return '1. 1-30 días'
                elif dias <= 60: return '2. 31-60 días'
                elif dias <= 90: return '3. 61-90 días'
                else: return '4. +90 días'
            
            facturas['antiguedad'] = facturas['dias_vencido'].apply(clasificar_antiguedad)
            por_antiguedad = facturas.groupby('antiguedad')['amount_residual'].sum().to_dict()
            
            # Por cliente
            facturas['cliente'] = facturas['partner_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
            )
            por_cliente = facturas.groupby('cliente')['amount_residual'].sum()\
                .sort_values(ascending=False).head(15).to_dict()
            
            return {
                'total': float(facturas['amount_residual'].sum()),
                'vencido': float(vencidas['amount_residual'].sum()),
                'por_vencer': float(por_vencer['amount_residual'].sum()),
                'total_facturas': len(facturas),
                'facturas_vencidas': len(vencidas),
                'por_antiguedad': por_antiguedad,
                'por_cliente': [{'cliente': k, 'saldo': v} for k, v in list(por_cliente.items())[:10]]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def cuentas_por_pagar(self) -> Dict:
        """Análisis de cuentas por pagar."""
        try:
            hoy = datetime.now()
            
            facturas = self.odoo.buscar(
                'account.move',
                filtro=[
                    ('move_type', '=', 'in_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial'])
                ],
                campos=['name', 'partner_id', 'invoice_date', 'invoice_date_due', 
                       'amount_total', 'amount_residual'],
                limite=2000
            )
            
            if facturas.empty:
                return {'total': 0, 'vencido': 0, 'por_vencer': 0, 'proveedores': []}
            
            facturas['fecha_venc'] = pd.to_datetime(facturas['invoice_date_due'])
            facturas['dias_vencido'] = (hoy - facturas['fecha_venc']).dt.days
            
            vencidas = facturas[facturas['dias_vencido'] > 0]
            por_vencer = facturas[facturas['dias_vencido'] <= 0]
            
            # Por proveedor
            facturas['proveedor'] = facturas['partner_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
            )
            por_proveedor = facturas.groupby('proveedor')['amount_residual'].sum()\
                .sort_values(ascending=False).head(15).to_dict()
            
            return {
                'total': float(facturas['amount_residual'].sum()),
                'vencido': float(vencidas['amount_residual'].sum()),
                'por_vencer': float(por_vencer['amount_residual'].sum()),
                'total_facturas': len(facturas),
                'por_proveedor': [{'proveedor': k, 'saldo': v} for k, v in list(por_proveedor.items())[:10]]
            }
        except Exception as e:
            return {'error': str(e)}
    
    # ========================================================
    # ANÁLISIS DE INVENTARIO
    # ========================================================
    
    def analisis_inventario(self) -> Dict:
        """Análisis completo de inventario."""
        try:
            stock = self.odoo.stock_disponible()
            if stock.empty:
                return {'error': 'No hay datos de stock'}
            
            # Calcular valor si hay precio
            productos = self.odoo.buscar(
                'product.product',
                filtro=[('type', '=', 'product')],
                campos=['id', 'name', 'default_code', 'standard_price', 'categ_id', 'qty_available'],
                limite=5000
            )
            
            resultado = {
                'resumen': {
                    'total_productos': len(productos) if not productos.empty else len(stock),
                    'total_unidades': float(stock['quantity'].sum()) if 'quantity' in stock.columns else 0,
                    'ubicaciones': len(set(
                        x[0] if isinstance(x, (list, tuple)) else x 
                        for x in stock['location_id'].dropna()
                    )) if 'location_id' in stock.columns else 0
                },
                'productos_sin_stock': [],
                'productos_bajo_minimo': [],
                'productos_costo_cero': [],
                'productos_sin_categoria': [],
                'por_ubicacion': [],
                'por_categoria': [],
                'valoracion': 0
            }
            
            # Valor estimado del inventario
            if not productos.empty and 'standard_price' in productos.columns and 'qty_available' in productos.columns:
                productos['valor'] = productos['standard_price'] * productos['qty_available']
                resultado['valoracion'] = float(productos['valor'].sum())
                
                # Limpiar campos que pueden ser listas (many2one de Odoo)
                if 'categ_id' in productos.columns:
                    productos['categoria_nombre'] = productos['categ_id'].apply(
                        lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else (str(x) if x else 'Sin categoría')
                    )
                
                # Limpiar default_code que puede ser False
                if 'default_code' in productos.columns:
                    productos['codigo'] = productos['default_code'].apply(
                        lambda x: str(x) if x else ''
                    )
                else:
                    productos['codigo'] = ''
                
                # Productos sin stock - usar columnas limpias
                sin_stock = productos[productos['qty_available'] <= 0].copy()
                resultado['productos_sin_stock'] = [
                    {'name': row['name'], 'default_code': row['codigo'], 'standard_price': row['standard_price']}
                    for _, row in sin_stock.head(20).iterrows()
                ]
                resultado['resumen']['sin_stock'] = len(sin_stock)
                
                # Productos con costo cero
                costo_cero = productos[(productos['standard_price'] <= 0) & (productos['qty_available'] > 0)].copy()
                resultado['productos_costo_cero'] = [
                    {'name': row['name'], 'default_code': row['codigo'], 'qty_available': row['qty_available']}
                    for _, row in costo_cero.head(20).iterrows()
                ]
                resultado['resumen']['costo_cero'] = len(costo_cero)
                
                # Productos sin categoría
                if 'categoria_nombre' in productos.columns:
                    sin_categ = productos[productos['categoria_nombre'].isin(['Sin categoría', 'False', ''])].copy()
                    resultado['productos_sin_categoria'] = [
                        {'name': row['name'], 'default_code': row['codigo'], 'qty_available': row['qty_available']}
                        for _, row in sin_categ.head(20).iterrows()
                    ]
                    resultado['resumen']['sin_categoria'] = len(sin_categ)
                
                # Por categoría - usar categoria_nombre ya limpia
                if 'categoria_nombre' in productos.columns:
                    por_cat = productos.groupby('categoria_nombre').agg({
                        'qty_available': 'sum',
                        'valor': 'sum'
                    }).sort_values('valor', ascending=False)
                    resultado['por_categoria'] = por_cat.head(15).reset_index().rename(
                        columns={'categoria_nombre': 'categoria'}
                    ).to_dict('records')
            
            # Por ubicación
            if 'location_id' in stock.columns:
                stock['ubicacion'] = stock['location_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                )
                por_ubi = stock.groupby('ubicacion')['quantity'].sum()
                resultado['por_ubicacion'] = por_ubi.head(10).reset_index().to_dict('records')
            
            return resultado
        except Exception as e:
            return {'error': str(e)}
    
    def productos_mas_vendidos_vs_stock(self, dias: int = 30) -> Dict:
        """Compara productos más vendidos con stock disponible."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
            
            # Obtener ventas
            lineas = self.odoo.buscar(
                'sale.order.line',
                filtro=[
                    ('order_id.date_order', '>=', fecha_inicio),
                    ('order_id.state', 'in', ['sale', 'done'])
                ],
                campos=['product_id', 'product_uom_qty'],
                limite=5000
            )
            
            if lineas.empty:
                return {'error': 'No hay ventas'}
            
            # Extraer ID y nombre de forma segura para evitar unhashable
            lineas['producto_id'] = lineas['product_id'].apply(
                lambda x: int(x[0]) if isinstance(x, (list, tuple)) and x else (int(x) if x else 0)
            )
            lineas['producto'] = lineas['product_id'].apply(
                lambda x: str(x[1]) if isinstance(x, (list, tuple)) and len(x) > 1 else str(x)
            )
            
            # Agrupar solo por producto_id (int), luego obtener nombre
            ventas = lineas.groupby('producto_id').agg({
                'product_uom_qty': 'sum',
                'producto': 'first'
            }).reset_index()
            ventas.columns = ['id', 'vendido', 'nombre']
            ventas['promedio_diario'] = ventas['vendido'] / dias
            
            # Obtener stock
            productos = self.odoo.buscar(
                'product.product',
                filtro=[('id', 'in', ventas['id'].tolist())],
                campos=['id', 'qty_available'],
                limite=5000
            )
            
            if not productos.empty:
                ventas = ventas.merge(
                    productos[['id', 'qty_available']], 
                    on='id', 
                    how='left'
                )
                ventas['dias_stock'] = ventas['qty_available'] / ventas['promedio_diario']
                ventas['dias_stock'] = ventas['dias_stock'].fillna(0).replace([np.inf, -np.inf], 999)
                
                # Alertas
                criticos = ventas[ventas['dias_stock'] < 7].sort_values('dias_stock')
                
                return {
                    'productos': ventas.sort_values('vendido', ascending=False).head(20).to_dict('records'),
                    'criticos': criticos.head(10).to_dict('records'),
                    'total_analizado': len(ventas)
                }
            
            return {'productos': ventas.head(20).to_dict('records')}
        except Exception as e:
            return {'error': str(e)}
    
    # ========================================================
    # ANÁLISIS DE COMPRAS
    # ========================================================
    
    def analisis_compras(self, fecha_inicio: str, fecha_fin: str) -> Dict:
        """Análisis de órdenes de compra."""
        try:
            compras = self.odoo.buscar(
                'purchase.order',
                filtro=[
                    ('date_order', '>=', fecha_inicio),
                    ('date_order', '<=', fecha_fin + " 23:59:59"),
                    ('state', 'in', ['purchase', 'done'])
                ],
                campos=['name', 'partner_id', 'date_order', 'amount_total', 
                       'state', 'user_id', 'invoice_status'],
                limite=2000
            )
            
            if compras.empty:
                return {'error': 'No hay compras en el período'}
            
            resultado = {
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'resumen': {
                    'total_ordenes': len(compras),
                    'monto_total': float(compras['amount_total'].sum()),
                    'promedio': float(compras['amount_total'].mean()),
                },
                'por_proveedor': [],
                'por_comprador': [],
                'insights': []
            }
            
            # Por proveedor
            compras['proveedor'] = compras['partner_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
            )
            por_prov = compras.groupby('proveedor')['amount_total'].agg(['count', 'sum'])\
                .sort_values('sum', ascending=False)
            resultado['por_proveedor'] = por_prov.head(10).reset_index().to_dict('records')
            
            # Por comprador
            if 'user_id' in compras.columns:
                compras['comprador'] = compras['user_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                )
                por_comp = compras.groupby('comprador')['amount_total'].agg(['count', 'sum'])
                resultado['por_comprador'] = por_comp.reset_index().to_dict('records')
            
            # Insights
            total = resultado['resumen']['monto_total']
            mejor_prov = resultado['por_proveedor'][0] if resultado['por_proveedor'] else {}
            
            resultado['insights'] = [
                f"{len(compras)} órdenes de compra por ${total:,.2f}",
                f"Principal proveedor: {mejor_prov.get('proveedor', 'N/A')}"
            ]
            
            return resultado
        except Exception as e:
            return {'error': str(e)}
    
    def top_proveedores(self, meses: int = 6) -> Dict:
        """Ranking de proveedores."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=meses*30)).strftime('%Y-%m-%d')
            
            compras = self.odoo.buscar(
                'purchase.order',
                filtro=[
                    ('date_order', '>=', fecha_inicio),
                    ('state', 'in', ['purchase', 'done'])
                ],
                campos=['partner_id', 'amount_total', 'date_order'],
                limite=5000
            )
            
            if compras.empty:
                return {'error': 'No hay datos'}
            
            compras['proveedor'] = compras['partner_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
            )
            
            ranking = compras.groupby('proveedor').agg({
                'amount_total': ['sum', 'count', 'mean']
            }).round(2)
            ranking.columns = ['total', 'ordenes', 'promedio']
            ranking = ranking.sort_values('total', ascending=False)
            
            return {
                'ranking': ranking.head(20).reset_index().to_dict('records'),
                'total_proveedores': len(ranking)
            }
        except Exception as e:
            return {'error': str(e)}
    
    # ========================================================
    # ANÁLISIS DE RECURSOS HUMANOS
    # ========================================================
    
    def analisis_headcount(self) -> Dict:
        """Análisis de plantilla de empleados."""
        try:
            empleados = self.odoo.buscar(
                'hr.employee',
                filtro=[('active', '=', True)],
                campos=['name', 'department_id', 'job_id', 'work_email', 
                       'gender', 'birthday', 'company_id'],
                limite=5000
            )
            
            if empleados.empty:
                return {'error': 'No hay datos de empleados'}
            
            # Extraer IDs para evitar unhashable
            if 'department_id' in empleados.columns:
                empleados['dept_id_num'] = empleados['department_id'].apply(
                    lambda x: x[0] if isinstance(x, (list, tuple)) and x else 0
                )
            if 'job_id' in empleados.columns:
                empleados['job_id_num'] = empleados['job_id'].apply(
                    lambda x: x[0] if isinstance(x, (list, tuple)) and x else 0
                )
            
            resultado = {
                'resumen': {
                    'total_empleados': len(empleados),
                    'departamentos': empleados['dept_id_num'].nunique() if 'dept_id_num' in empleados.columns else 0,
                    'puestos': empleados['job_id_num'].nunique() if 'job_id_num' in empleados.columns else 0
                },
                'por_departamento': [],
                'por_puesto': [],
                'por_genero': {},
                'insights': []
            }
            
            # Por departamento
            if 'department_id' in empleados.columns:
                empleados['departamento'] = empleados['department_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else 'Sin asignar'
                )
                por_depto = empleados['departamento'].value_counts()
                resultado['por_departamento'] = por_depto.head(15).reset_index().to_dict('records')
            
            # Por puesto
            if 'job_id' in empleados.columns:
                empleados['puesto'] = empleados['job_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else 'Sin puesto'
                )
                por_puesto = empleados['puesto'].value_counts()
                resultado['por_puesto'] = por_puesto.head(15).reset_index().to_dict('records')
            
            # Por género
            if 'gender' in empleados.columns:
                por_genero = empleados['gender'].value_counts().to_dict()
                resultado['por_genero'] = por_genero
            
            resultado['insights'] = [
                f"{len(empleados)} empleados activos",
                f"{resultado['resumen']['departamentos']} departamentos",
                f"{resultado['resumen']['puestos']} puestos diferentes"
            ]
            
            return resultado
        except Exception as e:
            return {'error': str(e)}
    
    def analisis_asistencia(self, fecha_inicio: str, fecha_fin: str) -> Dict:
        """Análisis de asistencia de empleados."""
        try:
            asistencia = self.odoo.buscar(
                'hr.attendance',
                filtro=[
                    ('check_in', '>=', fecha_inicio),
                    ('check_in', '<=', fecha_fin + " 23:59:59")
                ],
                campos=['employee_id', 'check_in', 'check_out', 'worked_hours'],
                limite=10000
            )
            
            if asistencia.empty:
                return {'error': 'No hay registros de asistencia'}
            
            # Extraer IDs numéricos para evitar unhashable
            emp_ids_unicos = 0
            if 'employee_id' in asistencia.columns:
                emp_ids_unicos = len(set(
                    x[0] if isinstance(x, (list, tuple)) else x 
                    for x in asistencia['employee_id'].dropna()
                ))
            
            resultado = {
                'periodo': {'inicio': fecha_inicio, 'fin': fecha_fin},
                'resumen': {
                    'total_registros': len(asistencia),
                    'empleados_unicos': emp_ids_unicos,
                    'horas_totales': float(asistencia['worked_hours'].sum()) if 'worked_hours' in asistencia.columns else 0,
                    'promedio_horas': float(asistencia['worked_hours'].mean()) if 'worked_hours' in asistencia.columns else 0
                },
                'por_empleado': [],
                'insights': []
            }
            
            # Por empleado
            if 'employee_id' in asistencia.columns:
                asistencia['empleado'] = asistencia['employee_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                )
                por_emp = asistencia.groupby('empleado')['worked_hours'].agg(['count', 'sum', 'mean'])
                por_emp.columns = ['registros', 'horas_totales', 'promedio']
                resultado['por_empleado'] = por_emp.head(20).reset_index().to_dict('records')
            
            horas_total = resultado['resumen']['horas_totales']
            empleados = resultado['resumen']['empleados_unicos']
            
            resultado['insights'] = [
                f"{horas_total:,.1f} horas trabajadas en total",
                f"{empleados} empleados con registros",
                f"Promedio por registro: {resultado['resumen']['promedio_horas']:.1f} hrs"
            ]
            
            return resultado
        except Exception as e:
            return {'error': str(e)}
    
    def analisis_ausencias(self, anio: int = None) -> Dict:
        """Análisis de ausencias/vacaciones."""
        try:
            if anio is None:
                anio = datetime.now().year
            
            fecha_inicio = f"{anio}-01-01"
            fecha_fin = f"{anio}-12-31"
            
            ausencias = self.odoo.buscar(
                'hr.leave',
                filtro=[
                    ('date_from', '>=', fecha_inicio),
                    ('date_to', '<=', fecha_fin + " 23:59:59"),
                    ('state', '=', 'validate')
                ],
                campos=['employee_id', 'holiday_status_id', 'number_of_days', 
                       'date_from', 'date_to'],
                limite=5000
            )
            
            if ausencias.empty:
                return {'error': 'No hay ausencias registradas'}
            
            # Extraer IDs numéricos para evitar unhashable
            emp_ids_unicos = len(set(
                x[0] if isinstance(x, (list, tuple)) else x 
                for x in ausencias['employee_id'].dropna()
            )) if 'employee_id' in ausencias.columns else 0
            
            resultado = {
                'anio': anio,
                'resumen': {
                    'total_ausencias': len(ausencias),
                    'total_dias': float(ausencias['number_of_days'].sum()),
                    'empleados': emp_ids_unicos
                },
                'por_tipo': [],
                'por_empleado': [],
                'por_mes': []
            }
            
            # Por tipo de ausencia
            if 'holiday_status_id' in ausencias.columns:
                ausencias['tipo'] = ausencias['holiday_status_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else 'Otro'
                )
                por_tipo = ausencias.groupby('tipo')['number_of_days'].sum()
                resultado['por_tipo'] = por_tipo.reset_index().to_dict('records')
            
            # Por empleado (top ausentismo)
            if 'employee_id' in ausencias.columns:
                ausencias['empleado'] = ausencias['employee_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                )
                por_emp = ausencias.groupby('empleado')['number_of_days'].sum().sort_values(ascending=False)
                resultado['por_empleado'] = por_emp.head(15).reset_index().to_dict('records')
            
            return resultado
        except Exception as e:
            return {'error': str(e)}
    
    def analisis_nomina(self, mes: int = None, anio: int = None) -> Dict:
        """Análisis de nómina."""
        try:
            if anio is None:
                anio = datetime.now().year
            if mes is None:
                mes = datetime.now().month
            
            fecha_inicio = f"{anio}-{mes:02d}-01"
            if mes == 12:
                fecha_fin = f"{anio}-12-31"
            else:
                fecha_fin = f"{anio}-{mes+1:02d}-01"
            
            nominas = self.odoo.buscar(
                'hr.payslip',
                filtro=[
                    ('date_from', '>=', fecha_inicio),
                    ('date_to', '<', fecha_fin),
                    ('state', 'in', ['done', 'paid'])
                ],
                campos=['employee_id', 'net_wage', 'state', 'struct_id'],
                limite=5000
            )
            
            if nominas.empty:
                return {'error': 'No hay nóminas en el período'}
            
            resultado = {
                'periodo': f"{mes:02d}/{anio}",
                'resumen': {
                    'total_nominas': len(nominas),
                    'monto_total': float(nominas['net_wage'].sum()) if 'net_wage' in nominas.columns else 0,
                    'promedio': float(nominas['net_wage'].mean()) if 'net_wage' in nominas.columns else 0,
                },
                'por_empleado': [],
                'insights': []
            }
            
            total = resultado['resumen']['monto_total']
            resultado['insights'] = [
                f"Nómina total: ${total:,.2f}",
                f"{len(nominas)} recibos procesados",
                f"Promedio por empleado: ${resultado['resumen']['promedio']:,.2f}"
            ]
            
            return resultado
        except Exception as e:
            return {'error': str(e)}
    
    def contratos_por_vencer(self, dias: int = 30) -> Dict:
        """Contratos que vencen pronto."""
        try:
            fecha_limite = (datetime.now() + timedelta(days=dias)).strftime('%Y-%m-%d')
            hoy = datetime.now().strftime('%Y-%m-%d')
            
            contratos = self.odoo.buscar(
                'hr.contract',
                filtro=[
                    ('state', '=', 'open'),
                    ('date_end', '>=', hoy),
                    ('date_end', '<=', fecha_limite)
                ],
                campos=['name', 'employee_id', 'date_start', 'date_end', 'wage'],
                limite=500
            )
            
            if contratos.empty:
                return {'mensaje': f'No hay contratos por vencer en los próximos {dias} días', 'contratos': []}
            
            contratos['empleado'] = contratos['employee_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
            )
            contratos['dias_restantes'] = (pd.to_datetime(contratos['date_end']) - datetime.now()).dt.days
            
            return {
                'total': len(contratos),
                'alerta': f'{len(contratos)} contratos vencen en {dias} días',
                'contratos': contratos[['empleado', 'date_end', 'dias_restantes', 'wage']].to_dict('records')
            }
        except Exception as e:
            return {'error': str(e)}
    
    # ========================================================
    # ANÁLISIS DE USUARIOS
    # ========================================================
    
    def analisis_usuarios(self) -> Dict:
        """Análisis de usuarios del sistema."""
        try:
            usuarios = self.odoo.buscar(
                'res.users',
                filtro=[('active', '=', True), ('share', '=', False)],
                campos=['name', 'login', 'login_date', 'company_id', 'groups_id'],
                limite=1000
            )
            
            if usuarios.empty:
                return {'error': 'No hay usuarios'}
            
            hoy = datetime.now()
            
            # Analizar último login
            if 'login_date' in usuarios.columns:
                usuarios['ultimo_login'] = pd.to_datetime(usuarios['login_date'])
                usuarios['dias_sin_login'] = (hoy - usuarios['ultimo_login']).dt.days
                usuarios['dias_sin_login'] = usuarios['dias_sin_login'].fillna(999)
                
                activos_reciente = len(usuarios[usuarios['dias_sin_login'] <= 7])
                inactivos = len(usuarios[usuarios['dias_sin_login'] > 30])
            else:
                activos_reciente = 0
                inactivos = 0
            
            return {
                'total_usuarios': len(usuarios),
                'activos_7_dias': activos_reciente,
                'inactivos_30_dias': inactivos,
                'usuarios': usuarios[['name', 'login', 'login_date']].head(30).to_dict('records')
            }
        except Exception as e:
            return {'error': str(e)}
    
    # ========================================================
    # ANÁLISIS CRM
    # ========================================================
    
    def analisis_crm_pipeline(self) -> Dict:
        """Análisis del pipeline de CRM."""
        try:
            leads = self.odoo.buscar(
                'crm.lead',
                filtro=[('active', '=', True), ('type', '=', 'opportunity')],
                campos=['name', 'partner_id', 'stage_id', 'user_id', 
                       'expected_revenue', 'probability', 'create_date'],
                limite=2000
            )
            
            if leads.empty:
                return {'error': 'No hay oportunidades en el pipeline'}
            
            resultado = {
                'resumen': {
                    'total_oportunidades': len(leads),
                    'valor_total': float(leads['expected_revenue'].sum()) if 'expected_revenue' in leads.columns else 0,
                },
                'por_etapa': [],
                'por_vendedor': [],
                'insights': []
            }
            
            # Por etapa
            if 'stage_id' in leads.columns:
                leads['etapa'] = leads['stage_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                )
                por_etapa = leads.groupby('etapa').agg({
                    'expected_revenue': ['count', 'sum']
                })
                por_etapa.columns = ['cantidad', 'valor']
                resultado['por_etapa'] = por_etapa.reset_index().to_dict('records')
            
            # Por vendedor
            if 'user_id' in leads.columns:
                leads['vendedor'] = leads['user_id'].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                )
                por_vend = leads.groupby('vendedor')['expected_revenue'].agg(['count', 'sum'])
                por_vend.columns = ['oportunidades', 'valor']
                resultado['por_vendedor'] = por_vend.head(10).reset_index().to_dict('records')
            
            # Valor ponderado por probabilidad
            if 'probability' in leads.columns:
                leads['valor_ponderado'] = leads['expected_revenue'] * leads['probability'] / 100
                resultado['valor_ponderado'] = float(leads['valor_ponderado'].sum())
            
            total = resultado['resumen']['valor_total']
            resultado['insights'] = [
                f"{len(leads)} oportunidades activas",
                f"Valor total: ${total:,.2f}",
                f"Valor ponderado: ${resultado.get('valor_ponderado', 0):,.2f}"
            ]
            
            return resultado
        except Exception as e:
            return {'error': str(e)}
    
    # ========================================================
    # FORMATEO DE RESULTADOS
    # ========================================================
    
    def formatear_analisis_md(self, tipo: str, datos: Dict) -> str:
        """Formatea un análisis a Markdown."""
        if 'error' in datos:
            return f"Error: {datos['error']}"
        
        md = ""
        
        # Header según tipo
        titulos = {
            'ventas': 'Análisis de Ventas',
            'pos': 'Análisis POS',
            'facturacion': 'Análisis de Facturación',
            'cxc': 'Cuentas por Cobrar',
            'cxp': 'Cuentas por Pagar',
            'inventario': 'Análisis de Inventario',
            'compras': 'Análisis de Compras',
            'rh': 'Análisis de RH',
            'headcount': 'Headcount',
            'asistencia': 'Análisis de Asistencia',
            'ausencias': 'Análisis de Ausencias',
            'nomina': 'Análisis de Nómina',
            'contratos': 'Contratos',
            'usuarios': 'Usuarios del Sistema',
            'crm': 'Pipeline CRM',
            'comparativa': 'Comparativa'
        }
        
        md += f"## {titulos.get(tipo, 'Análisis')}\n\n"
        
        # Período si existe
        if 'periodo' in datos:
            p = datos['periodo']
            if isinstance(p, dict):
                md += f"*Período: {p.get('inicio', '')} a {p.get('fin', '')}*\n\n"
            else:
                md += f"*Período: {p}*\n\n"
        
        # Resumen
        if 'resumen' in datos:
            md += "### Resumen\n\n"
            md += "| Métrica | Valor |\n|---------|-------|\n"
            for k, v in datos['resumen'].items():
                nombre = k.replace('_', ' ').title()
                if isinstance(v, float):
                    if 'monto' in k or 'total' in k or 'promedio' in k or 'saldo' in k:
                        valor = f"${v:,.2f}"
                    elif 'porcentaje' in k:
                        valor = f"{v:.1f}%"
                    else:
                        valor = f"{v:,.2f}"
                elif isinstance(v, int):
                    valor = f"{v:,}"
                else:
                    valor = str(v)
                md += f"| {nombre} | **{valor}** |\n"
            md += "\n"
        
        # Insights
        if 'insights' in datos and datos['insights']:
            md += "### Insights\n\n"
            for insight in datos['insights']:
                md += f"- {insight}\n"
            md += "\n"
        
        # Tablas adicionales
        for key in ['por_cliente', 'por_proveedor', 'por_vendedor', 'por_departamento', 
                    'por_categoria', 'por_etapa', 'ranking', 'productos']:
            if key in datos and datos[key]:
                titulo = key.replace('_', ' ').title()
                md += f"### {titulo}\n\n"
                
                items = datos[key]
                if isinstance(items, list) and items:
                    # Crear tabla
                    cols = items[0].keys()
                    md += "| " + " | ".join(str(c).title() for c in cols) + " |\n"
                    md += "|" + "|".join("---" for _ in cols) + "|\n"
                    for item in items[:10]:
                        valores = []
                        for c in cols:
                            v = item.get(c, '')
                            if isinstance(v, float):
                                v = f"${v:,.2f}" if v > 100 else f"{v:.2f}"
                            valores.append(str(v)[:30])
                        md += "| " + " | ".join(valores) + " |\n"
                    md += "\n"
        
        return md
