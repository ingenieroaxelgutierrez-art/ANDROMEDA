# ============================================================
# ANÁLISIS INTELIGENTE - ANDROMEDA 
# ============================================================
# Sistema de análisis flexible que detecta contexto y genera
# reportes dinámicos según la consulta del usuario.
# ============================================================

import os
import sys
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

from app.logging_config import get_logger
logger = get_logger("services.analysis.analisis_inteligente")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TipoAgrupacion(Enum):
    """Tipos de agrupación disponibles."""
    NINGUNA = "ninguna"
    POR_TIENDA = "por_tienda"
    POR_ALMACEN = "por_almacen"
    POR_UBICACION = "por_ubicacion"
    POR_MARCA = "por_marca"
    POR_CATEGORIA = "por_categoria"
    POR_VENDEDOR = "por_vendedor"
    POR_CLIENTE = "por_cliente"
    POR_EMPRESA = "por_empresa"
    POR_DIA = "por_dia"
    POR_SEMANA = "por_semana"
    POR_MES = "por_mes"
    POR_PRODUCTO = "por_producto"


class TipoComparativa(Enum):
    """Tipos de comparativa."""
    NINGUNA = "ninguna"
    VS_PERIODO_ANTERIOR = "vs_anterior"
    VS_PERIODO_ESPECIFICO = "vs_especifico"
    ENTRE_TIENDAS = "entre_tiendas"
    ENTRE_VENDEDORES = "entre_vendedores"
    ENTRE_PRODUCTOS = "entre_productos"


@dataclass
class ContextoConsulta:
    """Contexto extraído de la consulta del usuario."""
    # Tipo principal
    tipo_reporte: str = "ventas"
    
    # Agrupación
    agrupacion: TipoAgrupacion = TipoAgrupacion.NINGUNA
    
    # Comparativa
    comparativa: TipoComparativa = TipoComparativa.NINGUNA
    periodo_comparar_a: Dict[str, str] = field(default_factory=dict)
    periodo_comparar_b: Dict[str, str] = field(default_factory=dict)
    
    # Filtros
    filtro_tienda: Optional[str] = None
    filtro_marca: Optional[str] = None
    filtro_categoria: Optional[str] = None
    filtro_vendedor: Optional[str] = None
    filtro_cliente: Optional[str] = None
    filtro_empresa: Optional[str] = None
    filtro_ubicacion: Optional[str] = None
    
    # Períodos
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    
    # Parámetros
    limite: int = 20
    incluir_detalle: bool = False
    
    # Clarificación necesaria
    necesita_clarificacion: bool = False
    pregunta_clarificacion: str = ""
    opciones_clarificacion: List[str] = field(default_factory=list)


class DetectorContexto:
    """Detecta el contexto y la intención de la consulta."""
    
    def __init__(self):
        self._inicializar_patrones()
    
    def _inicializar_patrones(self):
        """Inicializa patrones de detección."""
        # Patrones de agrupación
        self.patrones_agrupacion = {
            TipoAgrupacion.POR_TIENDA: [
                r'por\s+tienda', r'de\s+tienda', r'tiendas', r'punto\s+de\s+venta',
                r'cada\s+tienda', r'por\s+sucursal', r'sucursales'
            ],
            TipoAgrupacion.POR_ALMACEN: [
                r'por\s+almac[eé]n', r'almacenes', r'por\s+bodega', r'bodegas'
            ],
            TipoAgrupacion.POR_UBICACION: [
                r'por\s+ubicaci[oó]n', r'ubicaciones', r'por\s+location',
                r'location_id', r'por\s+locaci[oó]n'
            ],
            TipoAgrupacion.POR_MARCA: [
                r'por\s+marca', r'marcas', r'por\s+brand', r'fabricante'
            ],
            TipoAgrupacion.POR_CATEGORIA: [
                r'por\s+categor[ií]a', r'categor[ií]as', r'por\s+tipo',
                r'por\s+familia', r'familias'
            ],
            TipoAgrupacion.POR_VENDEDOR: [
                r'por\s+vendedor', r'vendedores', r'por\s+asesor',
                r'por\s+empleado', r'por\s+usuario'
            ],
            TipoAgrupacion.POR_CLIENTE: [
                r'por\s+cliente', r'clientes', r'por\s+comprador'
            ],
            TipoAgrupacion.POR_EMPRESA: [
                r'por\s+empresa', r'empresas', r'por\s+compa[ñn][ií]a',
                r'por\s+company'
            ],
            TipoAgrupacion.POR_DIA: [
                r'por\s+d[ií]a', r'diario', r'cada\s+d[ií]a', r'diariamente'
            ],
            TipoAgrupacion.POR_SEMANA: [
                r'por\s+semana', r'semanal', r'cada\s+semana'
            ],
            TipoAgrupacion.POR_MES: [
                r'por\s+mes', r'mensual', r'cada\s+mes'
            ],
            TipoAgrupacion.POR_PRODUCTO: [
                r'por\s+producto', r'productos', r'por\s+art[ií]culo',
                r'por\s+sku', r'por\s+item'
            ],
        }
        
        # Patrones de comparativa
        self.patrones_comparativa = [
            r'comparar?\s+(?:con|vs|versus|contra)',
            r'(?:vs|versus)\s+',
            r'diferencia\s+entre',
            r'entre\s+(.+?)\s+y\s+(.+)',
            r'(\w+\s+\d{4})\s+(?:vs|versus|contra|y)\s+(\w+\s+\d{4})',
        ]
        
        # Patrones de tipo de reporte
        self.patrones_reporte = {
            'ventas': ['ventas', 'vendido', 'venta', 'sales', 'ordenes de venta'],
            'pos': ['pos', 'punto de venta', 'tickets', 'caja', 'mostrador'],
            'inventario': ['inventario', 'stock', 'existencias', 'almacén', 'disponible'],
            'facturas': ['facturas', 'facturación', 'cfdi', 'invoices'],
            'cxc': ['cxc', 'cuentas por cobrar', 'cartera', 'cobranza', 'por cobrar'],
            'cxp': ['cxp', 'cuentas por pagar', 'deudas', 'por pagar'],
            'clientes': ['clientes', 'compradores', 'customers'],
            'productos': ['productos', 'artículos', 'catálogo', 'items'],
            'compras': ['compras', 'órdenes de compra', 'purchases'],
        }
        
        # Meses para extraer períodos
        self.meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
    
    def detectar(self, mensaje: str) -> ContextoConsulta:
        """Detecta el contexto completo de la consulta."""
        mensaje_lower = mensaje.lower().strip()
        contexto = ContextoConsulta()
        
        # 1. Detectar tipo de reporte
        contexto.tipo_reporte = self._detectar_tipo_reporte(mensaje_lower)
        
        # 2. Detectar agrupación
        contexto.agrupacion = self._detectar_agrupacion(mensaje_lower)
        
        # 3. Detectar comparativa
        self._detectar_comparativa(mensaje_lower, contexto)
        
        # 4. Extraer períodos
        self._extraer_periodos(mensaje_lower, contexto)
        
        # 5. Extraer filtros específicos
        self._extraer_filtros(mensaje_lower, contexto)
        
        # 6. Determinar si necesita clarificación
        self._evaluar_clarificacion(mensaje_lower, contexto)
        
        return contexto
    
    def _detectar_tipo_reporte(self, mensaje: str) -> str:
        """Detecta el tipo de reporte solicitado."""
        # Prioridad: buscar primero los más específicos
        prioridad = ['inventario', 'pos', 'facturas', 'cxc', 'cxp', 'clientes', 'productos', 'compras', 'ventas']
        
        for tipo in prioridad:
            patrones = self.patrones_reporte.get(tipo, [])
            for patron in patrones:
                # Usar regex con word boundary para evitar falsos positivos
                if re.search(r'\b' + re.escape(patron) + r'\b', mensaje):
                    return tipo
        return 'ventas'  # Default
    
    def _detectar_agrupacion(self, mensaje: str) -> TipoAgrupacion:
        """Detecta el tipo de agrupación solicitada."""
        for agrupacion, patrones in self.patrones_agrupacion.items():
            for patron in patrones:
                if re.search(patron, mensaje):
                    return agrupacion
        return TipoAgrupacion.NINGUNA
    
    def _detectar_comparativa(self, mensaje: str, contexto: ContextoConsulta):
        """Detecta si hay una comparativa y extrae los períodos."""
        # Patrón: "enero 2025 vs enero 2026"
        patron_meses = r'(\w+)\s+(\d{4})\s+(?:vs|versus|contra|y|con)\s+(\w+)\s+(\d{4})'
        match = re.search(patron_meses, mensaje)
        
        if match:
            mes_a, año_a, mes_b, año_b = match.groups()
            
            if mes_a.lower() in self.meses and mes_b.lower() in self.meses:
                contexto.comparativa = TipoComparativa.VS_PERIODO_ESPECIFICO
                
                # Período A
                mes_num_a = self.meses[mes_a.lower()]
                año_num_a = int(año_a)
                primer_dia_a = datetime(año_num_a, mes_num_a, 1)
                if mes_num_a == 12:
                    ultimo_dia_a = datetime(año_num_a + 1, 1, 1) - timedelta(days=1)
                else:
                    ultimo_dia_a = datetime(año_num_a, mes_num_a + 1, 1) - timedelta(days=1)
                
                contexto.periodo_comparar_a = {
                    'inicio': primer_dia_a.strftime('%Y-%m-%d'),
                    'fin': ultimo_dia_a.strftime('%Y-%m-%d'),
                    'nombre': f'{mes_a.capitalize()} {año_a}'
                }
                
                # Período B
                mes_num_b = self.meses[mes_b.lower()]
                año_num_b = int(año_b)
                primer_dia_b = datetime(año_num_b, mes_num_b, 1)
                if mes_num_b == 12:
                    ultimo_dia_b = datetime(año_num_b + 1, 1, 1) - timedelta(days=1)
                else:
                    ultimo_dia_b = datetime(año_num_b, mes_num_b + 1, 1) - timedelta(days=1)
                
                contexto.periodo_comparar_b = {
                    'inicio': primer_dia_b.strftime('%Y-%m-%d'),
                    'fin': ultimo_dia_b.strftime('%Y-%m-%d'),
                    'nombre': f'{mes_b.capitalize()} {año_b}'
                }
                return
        
        # Detectar comparativa con período anterior
        if any(p in mensaje for p in ['vs anterior', 'comparar con anterior', 'vs mes pasado', 'vs año pasado']):
            contexto.comparativa = TipoComparativa.VS_PERIODO_ANTERIOR
    
    def _extraer_periodos(self, mensaje: str, contexto: ContextoConsulta):
        """Extrae períodos de fechas del mensaje."""
        hoy = datetime.now()
        
        # Si ya tiene comparativa con períodos específicos, no sobreescribir
        if contexto.comparativa == TipoComparativa.VS_PERIODO_ESPECIFICO:
            return
        
        # Buscar mes específico
        patron_mes = r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s*(?:de\s*)?(\d{4})?'
        match = re.search(patron_mes, mensaje)
        
        if match:
            nombre_mes = match.group(1).lower()
            año_match = match.group(2)
            
            mes_num = self.meses.get(nombre_mes, 1)
            año_num = int(año_match) if año_match else hoy.year
            
            # Si el mes es futuro y no se especificó año, asumir año anterior
            if not año_match and mes_num > hoy.month:
                año_num = hoy.year - 1
            
            primer_dia = datetime(año_num, mes_num, 1)
            if mes_num == 12:
                ultimo_dia = datetime(año_num + 1, 1, 1) - timedelta(days=1)
            else:
                ultimo_dia = datetime(año_num, mes_num + 1, 1) - timedelta(days=1)
            
            contexto.fecha_inicio = primer_dia.strftime('%Y-%m-%d')
            contexto.fecha_fin = ultimo_dia.strftime('%Y-%m-%d')
            return
        
        # Patrones relativos
        if 'hoy' in mensaje:
            contexto.fecha_inicio = contexto.fecha_fin = hoy.strftime('%Y-%m-%d')
        elif 'ayer' in mensaje:
            ayer = hoy - timedelta(days=1)
            contexto.fecha_inicio = contexto.fecha_fin = ayer.strftime('%Y-%m-%d')
        elif 'esta semana' in mensaje or 'semana actual' in mensaje:
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            contexto.fecha_inicio = inicio_semana.strftime('%Y-%m-%d')
            contexto.fecha_fin = hoy.strftime('%Y-%m-%d')
        elif 'este mes' in mensaje or 'mes actual' in mensaje:
            contexto.fecha_inicio = hoy.replace(day=1).strftime('%Y-%m-%d')
            contexto.fecha_fin = hoy.strftime('%Y-%m-%d')
        elif 'este año' in mensaje or 'año actual' in mensaje:
            contexto.fecha_inicio = hoy.replace(month=1, day=1).strftime('%Y-%m-%d')
            contexto.fecha_fin = hoy.strftime('%Y-%m-%d')
        
        # Últimos X días/semanas/meses
        match = re.search(r'[uú]ltimos?\s*(\d+)\s*(d[ií]as?|semanas?|meses?)', mensaje)
        if match:
            cantidad = int(match.group(1))
            unidad = match.group(2).lower()
            
            if 'día' in unidad or 'dia' in unidad:
                contexto.fecha_inicio = (hoy - timedelta(days=cantidad)).strftime('%Y-%m-%d')
            elif 'semana' in unidad:
                contexto.fecha_inicio = (hoy - timedelta(weeks=cantidad)).strftime('%Y-%m-%d')
            elif 'mes' in unidad:
                contexto.fecha_inicio = (hoy - timedelta(days=cantidad * 30)).strftime('%Y-%m-%d')
            
            contexto.fecha_fin = hoy.strftime('%Y-%m-%d')
    
    def _extraer_filtros(self, mensaje: str, contexto: ContextoConsulta):
        """Extrae filtros específicos del mensaje."""
        # Filtro por tienda específica
        match = re.search(r'tienda\s+["\']?([^"\']+)["\']?', mensaje)
        if match:
            contexto.filtro_tienda = match.group(1).strip()
        
        # Filtro por marca específica
        match = re.search(r'marca\s+["\']?([^"\']+)["\']?', mensaje)
        if match:
            contexto.filtro_marca = match.group(1).strip()
        
        # Filtro por vendedor específico
        match = re.search(r'vendedor\s+["\']?([^"\']+)["\']?', mensaje)
        if match:
            contexto.filtro_vendedor = match.group(1).strip()
        
        # Top N
        match = re.search(r'top\s*(\d+)', mensaje)
        if match:
            contexto.limite = int(match.group(1))
        
        # Detalle
        if any(p in mensaje for p in ['detallado', 'detalle', 'completo', 'todo']):
            contexto.incluir_detalle = True
    
    def _evaluar_clarificacion(self, mensaje: str, contexto: ContextoConsulta):
        """Evalúa si se necesita clarificación del usuario."""
        # Si pide solo "ventas" sin más contexto
        palabras = mensaje.split()
        
        if contexto.tipo_reporte == 'ventas' and len(palabras) <= 2:
            if contexto.agrupacion == TipoAgrupacion.NINGUNA:
                contexto.necesita_clarificacion = True
                contexto.pregunta_clarificacion = "¿Cómo deseas ver las ventas?"
                contexto.opciones_clarificacion = [
                    "Resumen general",
                    "Por tienda/sucursal",
                    "Por vendedor",
                    "Por producto",
                    "Por marca",
                    "Por día/semana/mes",
                    "Por empresa"
                ]
        
        # Si pide inventario sin especificar
        if contexto.tipo_reporte == 'inventario' and len(palabras) <= 2:
            if contexto.agrupacion == TipoAgrupacion.NINGUNA:
                contexto.necesita_clarificacion = True
                contexto.pregunta_clarificacion = "¿Cómo deseas ver el inventario?"
                contexto.opciones_clarificacion = [
                    "Resumen general",
                    "Por ubicación (location_id)",
                    "Por almacén/tienda",
                    "Por categoría",
                    "Stock crítico",
                    "Sin movimiento"
                ]


class AnalizadorInteligente:
    """Ejecuta análisis basados en el contexto detectado."""
    
    def __init__(self):
        self.conector = None
        self.detector = DetectorContexto()
    
    def set_conector(self, conector):
        """Configura el conector de Odoo."""
        self.conector = conector
    
    def analizar(self, mensaje: str) -> Dict[str, Any]:
        """Analiza la consulta y genera el reporte correspondiente."""
        contexto = self.detector.detectar(mensaje)
        
        # Si necesita clarificación, retornar opciones
        if contexto.necesita_clarificacion:
            return {
                'tipo': 'clarificacion',
                'pregunta': contexto.pregunta_clarificacion,
                'opciones': contexto.opciones_clarificacion,
                'contexto_parcial': contexto
            }
        
        # Ejecutar análisis según tipo
        if contexto.tipo_reporte == 'ventas':
            return self._analizar_ventas(contexto)
        elif contexto.tipo_reporte == 'inventario':
            return self._analizar_inventario(contexto)
        elif contexto.tipo_reporte == 'pos':
            return self._analizar_pos(contexto)
        elif contexto.tipo_reporte == 'facturas':
            return self._analizar_facturas(contexto)
        elif contexto.tipo_reporte == 'productos':
            return self._analizar_productos(contexto)
        else:
            return self._analizar_generico(contexto)
    
    def _analizar_ventas(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Análisis de ventas según contexto."""
        if not self.conector or not self.conector.conectado:
            return {'error': 'Sin conexión a Odoo'}
        
        # Si es comparativa entre períodos
        if contexto.comparativa == TipoComparativa.VS_PERIODO_ESPECIFICO:
            return self._comparar_ventas_periodos(contexto)
        
        # Análisis según agrupación
        if contexto.agrupacion == TipoAgrupacion.POR_TIENDA:
            return self._ventas_por_tienda(contexto)
        elif contexto.agrupacion == TipoAgrupacion.POR_MARCA:
            return self._ventas_por_marca(contexto)
        elif contexto.agrupacion == TipoAgrupacion.POR_VENDEDOR:
            return self._ventas_por_vendedor(contexto)
        elif contexto.agrupacion == TipoAgrupacion.POR_CLIENTE:
            return self._ventas_por_cliente(contexto)
        elif contexto.agrupacion == TipoAgrupacion.POR_EMPRESA:
            return self._ventas_por_empresa(contexto)
        elif contexto.agrupacion == TipoAgrupacion.POR_PRODUCTO:
            return self._ventas_por_producto(contexto)
        elif contexto.agrupacion in [TipoAgrupacion.POR_DIA, TipoAgrupacion.POR_SEMANA, TipoAgrupacion.POR_MES]:
            return self._ventas_por_periodo(contexto)
        else:
            return self._ventas_resumen(contexto)
    
    def _ventas_resumen(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Resumen general de ventas."""
        try:
            df = self.conector.ventas_periodo(contexto.fecha_inicio, contexto.fecha_fin)
            
            if df.empty:
                return {'error': 'No hay ventas en el período', 'tipo': 'ventas_resumen'}
            
            resultado = {
                'tipo': 'ventas_resumen',
                'periodo': {
                    'inicio': contexto.fecha_inicio,
                    'fin': contexto.fecha_fin
                },
                'metricas': {
                    'total_ventas': float(df['amount_total'].sum()),
                    'num_ordenes': len(df),
                    'ticket_promedio': float(df['amount_total'].mean()),
                    'venta_maxima': float(df['amount_total'].max()),
                    'venta_minima': float(df['amount_total'].min()),
                },
                'datos': df
            }
            
            return resultado
            
        except Exception as e:
            return {'error': str(e)}
    
    def _ventas_por_tienda(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Ventas agrupadas por tienda/sucursal (usando pos.config - unidad operativa)."""
        try:
            POSOrder = self.conector.odoo.env['pos.order']
            POSSession = self.conector.odoo.env['pos.session']
            POSConfig = self.conector.odoo.env['pos.config']
            
            domain = [('state', 'in', ['paid', 'done', 'invoiced'])]
            if contexto.fecha_inicio:
                domain.append(('date_order', '>=', contexto.fecha_inicio))
            if contexto.fecha_fin:
                domain.append(('date_order', '<=', contexto.fecha_fin + ' 23:59:59'))
            
            order_ids = POSOrder.search(domain, limit=5000)
            if not order_ids:
                return {'error': 'No hay ventas POS en el período', 'tipo': 'ventas_tienda'}
            
            ordenes = POSOrder.read(order_ids, ['name', 'amount_total', 'session_id', 'date_order'])
            
            # Obtener mapeo de sesiones a configs (unidades operativas)
            session_ids = list(set(o.get('session_id', [0])[0] for o in ordenes 
                                   if o.get('session_id') and isinstance(o.get('session_id'), (list, tuple))))
            
            # Mapear session_id → config_id (unidad operativa)
            session_to_config = {}
            if session_ids:
                sessions = POSSession.read(session_ids, ['config_id'])
                for s in sessions:
                    config = s.get('config_id', [0, 'Sin tienda'])
                    session_to_config[s['id']] = config[1] if isinstance(config, (list, tuple)) else str(config)
            
            # Agrupar por unidad operativa (config_id)
            por_tienda = {}
            for orden in ordenes:
                session = orden.get('session_id', [0, 'Sin sesión'])
                session_id = session[0] if isinstance(session, (list, tuple)) else 0
                
                # Obtener nombre de la unidad operativa
                tienda = session_to_config.get(session_id, session[1] if isinstance(session, (list, tuple)) else 'Sin tienda')
                
                if tienda not in por_tienda:
                    por_tienda[tienda] = {'total': 0, 'ordenes': 0}
                
                por_tienda[tienda]['total'] += orden.get('amount_total', 0)
                por_tienda[tienda]['ordenes'] += 1
            
            # Convertir a lista ordenada
            tiendas_lista = [
                {'tienda': k, 'total': v['total'], 'ordenes': v['ordenes']}
                for k, v in por_tienda.items()
            ]
            tiendas_lista.sort(key=lambda x: x['total'], reverse=True)
            
            return {
                'tipo': 'ventas_tienda',
                'periodo': {'inicio': contexto.fecha_inicio, 'fin': contexto.fecha_fin},
                'tiendas': tiendas_lista[:contexto.limite],
                'total_tiendas': len(tiendas_lista),
                'total_general': sum(t['total'] for t in tiendas_lista)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _ventas_por_marca(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Ventas agrupadas por marca de producto."""
        try:
            SaleOrderLine = self.conector.odoo.env['sale.order.line']
            
            domain = [('order_id.state', 'in', ['sale', 'done'])]
            if contexto.fecha_inicio:
                domain.append(('order_id.date_order', '>=', contexto.fecha_inicio))
            if contexto.fecha_fin:
                domain.append(('order_id.date_order', '<=', contexto.fecha_fin))
            
            line_ids = SaleOrderLine.search(domain, limit=10000)
            if not line_ids:
                return {'error': 'No hay líneas de venta', 'tipo': 'ventas_marca'}
            
            lineas = SaleOrderLine.read(line_ids, ['product_id', 'price_subtotal', 'product_uom_qty'])
            
            # Obtener productos con sus marcas
            product_ids = list(set(
                l['product_id'][0] if isinstance(l.get('product_id'), (list, tuple)) else l.get('product_id', 0)
                for l in lineas if l.get('product_id')
            ))
            
            Product = self.conector.odoo.env['product.product']
            productos = Product.read(product_ids, ['id', 'name', 'product_brand_id', 'categ_id'])
            
            # Crear mapa de producto -> marca
            mapa_marcas = {}
            for prod in productos:
                prod_id = prod['id']
                marca = prod.get('product_brand_id')
                if isinstance(marca, (list, tuple)) and marca:
                    mapa_marcas[prod_id] = marca[1]
                else:
                    # Usar categoría como alternativa
                    categ = prod.get('categ_id')
                    mapa_marcas[prod_id] = categ[1] if isinstance(categ, (list, tuple)) else 'Sin categoría'
            
            # Agrupar ventas por marca
            por_marca = {}
            for linea in lineas:
                prod_id = linea['product_id'][0] if isinstance(linea.get('product_id'), (list, tuple)) else 0
                marca = mapa_marcas.get(prod_id, 'Sin marca')
                
                if marca not in por_marca:
                    por_marca[marca] = {'total': 0, 'unidades': 0, 'productos': set()}
                
                por_marca[marca]['total'] += linea.get('price_subtotal', 0)
                por_marca[marca]['unidades'] += linea.get('product_uom_qty', 0)
                por_marca[marca]['productos'].add(prod_id)
            
            # Convertir a lista
            marcas_lista = [
                {
                    'marca': k,
                    'total': v['total'],
                    'unidades': v['unidades'],
                    'productos_unicos': len(v['productos'])
                }
                for k, v in por_marca.items()
            ]
            marcas_lista.sort(key=lambda x: x['total'], reverse=True)
            
            return {
                'tipo': 'ventas_marca',
                'periodo': {'inicio': contexto.fecha_inicio, 'fin': contexto.fecha_fin},
                'marcas': marcas_lista[:contexto.limite],
                'total_marcas': len(marcas_lista),
                'total_general': sum(m['total'] for m in marcas_lista)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _ventas_por_vendedor(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Ventas agrupadas por vendedor."""
        try:
            df = self.conector.ventas_periodo(contexto.fecha_inicio, contexto.fecha_fin)
            
            if df.empty:
                return {'error': 'No hay ventas', 'tipo': 'ventas_vendedor'}
            
            # Extraer nombre de vendedor
            df['vendedor'] = df['user_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'Sin vendedor'
            )
            
            por_vendedor = df.groupby('vendedor').agg({
                'amount_total': ['sum', 'count', 'mean']
            }).reset_index()
            por_vendedor.columns = ['vendedor', 'total', 'ordenes', 'promedio']
            por_vendedor = por_vendedor.sort_values('total', ascending=False)
            
            return {
                'tipo': 'ventas_vendedor',
                'periodo': {'inicio': contexto.fecha_inicio, 'fin': contexto.fecha_fin},
                'vendedores': por_vendedor.head(contexto.limite).to_dict('records'),
                'total_vendedores': len(por_vendedor),
                'total_general': float(df['amount_total'].sum())
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _ventas_por_cliente(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Ventas agrupadas por cliente."""
        try:
            df = self.conector.ventas_periodo(contexto.fecha_inicio, contexto.fecha_fin)
            
            if df.empty:
                return {'error': 'No hay ventas', 'tipo': 'ventas_cliente'}
            
            df['cliente'] = df['partner_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'Sin cliente'
            )
            
            por_cliente = df.groupby('cliente').agg({
                'amount_total': ['sum', 'count', 'mean']
            }).reset_index()
            por_cliente.columns = ['cliente', 'total', 'ordenes', 'promedio']
            por_cliente = por_cliente.sort_values('total', ascending=False)
            
            return {
                'tipo': 'ventas_cliente',
                'periodo': {'inicio': contexto.fecha_inicio, 'fin': contexto.fecha_fin},
                'clientes': por_cliente.head(contexto.limite).to_dict('records'),
                'total_clientes': len(por_cliente),
                'total_general': float(df['amount_total'].sum())
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _ventas_por_empresa(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Ventas agrupadas por empresa."""
        try:
            df = self.conector.ventas_periodo(contexto.fecha_inicio, contexto.fecha_fin)
            
            if df.empty:
                return {'error': 'No hay ventas', 'tipo': 'ventas_empresa'}
            
            df['empresa'] = df['company_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'Sin empresa'
            )
            
            por_empresa = df.groupby('empresa').agg({
                'amount_total': ['sum', 'count']
            }).reset_index()
            por_empresa.columns = ['empresa', 'total', 'ordenes']
            por_empresa = por_empresa.sort_values('total', ascending=False)
            
            return {
                'tipo': 'ventas_empresa',
                'periodo': {'inicio': contexto.fecha_inicio, 'fin': contexto.fecha_fin},
                'empresas': por_empresa.to_dict('records'),
                'total_empresas': len(por_empresa),
                'total_general': float(df['amount_total'].sum())
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _ventas_por_producto(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Ventas agrupadas por producto."""
        try:
            SaleOrderLine = self.conector.odoo.env['sale.order.line']
            
            domain = [('order_id.state', 'in', ['sale', 'done'])]
            if contexto.fecha_inicio:
                domain.append(('order_id.date_order', '>=', contexto.fecha_inicio))
            if contexto.fecha_fin:
                domain.append(('order_id.date_order', '<=', contexto.fecha_fin))
            
            line_ids = SaleOrderLine.search(domain, limit=10000)
            if not line_ids:
                return {'error': 'No hay líneas de venta', 'tipo': 'ventas_producto'}
            
            lineas = SaleOrderLine.read(line_ids, ['product_id', 'price_subtotal', 'product_uom_qty'])
            
            por_producto = {}
            for linea in lineas:
                prod = linea.get('product_id', [0, 'Desconocido'])
                prod_id = prod[0] if isinstance(prod, (list, tuple)) else prod
                prod_nombre = prod[1] if isinstance(prod, (list, tuple)) and len(prod) > 1 else str(prod)
                
                if prod_id not in por_producto:
                    por_producto[prod_id] = {'nombre': prod_nombre, 'total': 0, 'unidades': 0}
                
                por_producto[prod_id]['total'] += linea.get('price_subtotal', 0)
                por_producto[prod_id]['unidades'] += linea.get('product_uom_qty', 0)
            
            productos_lista = [
                {'producto': v['nombre'], 'total': v['total'], 'unidades': v['unidades']}
                for v in por_producto.values()
            ]
            productos_lista.sort(key=lambda x: x['total'], reverse=True)
            
            return {
                'tipo': 'ventas_producto',
                'periodo': {'inicio': contexto.fecha_inicio, 'fin': contexto.fecha_fin},
                'productos': productos_lista[:contexto.limite],
                'total_productos': len(productos_lista),
                'total_general': sum(p['total'] for p in productos_lista)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _ventas_por_periodo(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Ventas agrupadas por día/semana/mes."""
        try:
            df = self.conector.ventas_periodo(contexto.fecha_inicio, contexto.fecha_fin)
            
            if df.empty:
                return {'error': 'No hay ventas', 'tipo': 'ventas_periodo'}
            
            df['fecha'] = pd.to_datetime(df['date_order'])
            
            if contexto.agrupacion == TipoAgrupacion.POR_DIA:
                df['periodo'] = df['fecha'].dt.strftime('%Y-%m-%d')
            elif contexto.agrupacion == TipoAgrupacion.POR_SEMANA:
                df['periodo'] = df['fecha'].dt.strftime('%Y-W%U')
            else:  # POR_MES
                df['periodo'] = df['fecha'].dt.strftime('%Y-%m')
            
            por_periodo = df.groupby('periodo').agg({
                'amount_total': ['sum', 'count']
            }).reset_index()
            por_periodo.columns = ['periodo', 'total', 'ordenes']
            
            return {
                'tipo': 'ventas_periodo',
                'agrupacion': contexto.agrupacion.value,
                'periodo': {'inicio': contexto.fecha_inicio, 'fin': contexto.fecha_fin},
                'periodos': por_periodo.to_dict('records'),
                'total_general': float(df['amount_total'].sum())
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _comparar_ventas_periodos(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Compara ventas entre dos períodos específicos."""
        try:
            # Período A
            df_a = self.conector.ventas_periodo(
                contexto.periodo_comparar_a['inicio'],
                contexto.periodo_comparar_a['fin']
            )
            
            # Período B
            df_b = self.conector.ventas_periodo(
                contexto.periodo_comparar_b['inicio'],
                contexto.periodo_comparar_b['fin']
            )
            
            total_a = float(df_a['amount_total'].sum()) if not df_a.empty else 0
            total_b = float(df_b['amount_total'].sum()) if not df_b.empty else 0
            ordenes_a = len(df_a)
            ordenes_b = len(df_b)
            
            # Calcular variación
            if total_a > 0:
                variacion = ((total_b - total_a) / total_a) * 100
            else:
                variacion = 100 if total_b > 0 else 0
            
            return {
                'tipo': 'comparativa_ventas',
                'periodo_a': {
                    'nombre': contexto.periodo_comparar_a['nombre'],
                    'inicio': contexto.periodo_comparar_a['inicio'],
                    'fin': contexto.periodo_comparar_a['fin'],
                    'total': total_a,
                    'ordenes': ordenes_a,
                    'ticket_promedio': total_a / ordenes_a if ordenes_a > 0 else 0
                },
                'periodo_b': {
                    'nombre': contexto.periodo_comparar_b['nombre'],
                    'inicio': contexto.periodo_comparar_b['inicio'],
                    'fin': contexto.periodo_comparar_b['fin'],
                    'total': total_b,
                    'ordenes': ordenes_b,
                    'ticket_promedio': total_b / ordenes_b if ordenes_b > 0 else 0
                },
                'variacion_porcentaje': variacion,
                'diferencia_absoluta': total_b - total_a,
                'tendencia': 'crecimiento' if variacion > 0 else ('decremento' if variacion < 0 else 'estable'),
                'insights': self._generar_insights_comparativa(total_a, total_b, ordenes_a, ordenes_b, 
                                                               contexto.periodo_comparar_a['nombre'],
                                                               contexto.periodo_comparar_b['nombre'])
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _generar_insights_comparativa(self, total_a, total_b, ordenes_a, ordenes_b, nombre_a, nombre_b) -> List[str]:
        """Genera insights de la comparativa."""
        insights = []
        
        if total_b > total_a:
            pct = ((total_b - total_a) / total_a * 100) if total_a > 0 else 100
            insights.append(f"Las ventas de {nombre_b} superan a {nombre_a} por ${total_b - total_a:,.2f} (+{pct:.1f}%)")
        elif total_a > total_b:
            pct = ((total_a - total_b) / total_a * 100) if total_a > 0 else 0
            insights.append(f"Las ventas de {nombre_b} están por debajo de {nombre_a} en ${total_a - total_b:,.2f} (-{pct:.1f}%)")
        else:
            insights.append(f"Las ventas son similares en ambos períodos")
        
        # Comparar órdenes
        if ordenes_b > ordenes_a:
            insights.append(f"Más transacciones en {nombre_b}: {ordenes_b} vs {ordenes_a}")
        elif ordenes_a > ordenes_b:
            insights.append(f"Menos transacciones en {nombre_b}: {ordenes_b} vs {ordenes_a}")
        
        # Ticket promedio
        ticket_a = total_a / ordenes_a if ordenes_a > 0 else 0
        ticket_b = total_b / ordenes_b if ordenes_b > 0 else 0
        if ticket_b > ticket_a:
            insights.append(f"Ticket promedio mayor en {nombre_b}: ${ticket_b:,.2f} vs ${ticket_a:,.2f}")
        elif ticket_a > ticket_b:
            insights.append(f"Ticket promedio menor en {nombre_b}: ${ticket_b:,.2f} vs ${ticket_a:,.2f}")
        
        return insights
    
    def _analizar_inventario(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Análisis de inventario según contexto."""
        if contexto.agrupacion == TipoAgrupacion.POR_UBICACION:
            return self._inventario_por_ubicacion(contexto)
        elif contexto.agrupacion == TipoAgrupacion.POR_ALMACEN:
            return self._inventario_por_almacen(contexto)
        elif contexto.agrupacion == TipoAgrupacion.POR_CATEGORIA:
            return self._inventario_por_categoria(contexto)
        else:
            return self._inventario_resumen(contexto)
    
    def _inventario_por_ubicacion(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Inventario desglosado por location_id."""
        try:
            Quant = self.conector.odoo.env['stock.quant']
            quant_ids = Quant.search([('quantity', '>', 0)], limit=10000)
            
            if not quant_ids:
                return {'error': 'No hay stock', 'tipo': 'inventario_ubicacion'}
            
            quants = Quant.read(quant_ids, ['product_id', 'location_id', 'quantity', 'reserved_quantity'])
            
            por_ubicacion = {}
            for quant in quants:
                loc = quant.get('location_id', [0, 'Sin ubicación'])
                loc_id = loc[0] if isinstance(loc, (list, tuple)) else loc
                loc_nombre = loc[1] if isinstance(loc, (list, tuple)) and len(loc) > 1 else str(loc)
                
                if loc_id not in por_ubicacion:
                    por_ubicacion[loc_id] = {
                        'nombre': loc_nombre,
                        'cantidad': 0,
                        'reservado': 0,
                        'productos': set()
                    }
                
                por_ubicacion[loc_id]['cantidad'] += quant.get('quantity', 0)
                por_ubicacion[loc_id]['reservado'] += quant.get('reserved_quantity', 0)
                
                prod = quant.get('product_id', [0])
                prod_id = prod[0] if isinstance(prod, (list, tuple)) else prod
                por_ubicacion[loc_id]['productos'].add(prod_id)
            
            ubicaciones_lista = [
                {
                    'location_id': k,
                    'ubicacion': v['nombre'],
                    'cantidad_total': v['cantidad'],
                    'cantidad_reservada': v['reservado'],
                    'cantidad_disponible': v['cantidad'] - v['reservado'],
                    'productos_unicos': len(v['productos'])
                }
                for k, v in por_ubicacion.items()
            ]
            ubicaciones_lista.sort(key=lambda x: x['cantidad_total'], reverse=True)
            
            return {
                'tipo': 'inventario_ubicacion',
                'ubicaciones': ubicaciones_lista[:contexto.limite],
                'total_ubicaciones': len(ubicaciones_lista),
                'total_cantidad': sum(u['cantidad_total'] for u in ubicaciones_lista)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _inventario_por_almacen(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Inventario desglosado por almacén."""
        try:
            Warehouse = self.conector.odoo.env['stock.warehouse']
            warehouse_ids = Warehouse.search([])
            almacenes = Warehouse.read(warehouse_ids, ['name', 'code', 'lot_stock_id', 'company_id'])
            
            resultado = []
            Quant = self.conector.odoo.env['stock.quant']
            
            for almacen in almacenes:
                location_id = almacen.get('lot_stock_id')
                if not location_id:
                    continue
                
                loc_id = location_id[0] if isinstance(location_id, (list, tuple)) else location_id
                
                quant_ids = Quant.search([
                    ('location_id', 'child_of', loc_id),
                    ('quantity', '>', 0)
                ])
                
                total_cantidad = 0
                productos_unicos = set()
                
                if quant_ids:
                    quants = Quant.read(quant_ids, ['product_id', 'quantity'])
                    for q in quants:
                        total_cantidad += q.get('quantity', 0)
                        prod = q.get('product_id', [0])
                        prod_id = prod[0] if isinstance(prod, (list, tuple)) else prod
                        productos_unicos.add(prod_id)
                
                empresa = almacen.get('company_id')
                resultado.append({
                    'almacen': almacen['name'],
                    'codigo': almacen.get('code', ''),
                    'empresa': empresa[1] if isinstance(empresa, (list, tuple)) else '',
                    'cantidad_total': total_cantidad,
                    'productos_unicos': len(productos_unicos)
                })
            
            resultado.sort(key=lambda x: x['cantidad_total'], reverse=True)
            
            return {
                'tipo': 'inventario_almacen',
                'almacenes': resultado,
                'total_almacenes': len(resultado),
                'total_cantidad': sum(a['cantidad_total'] for a in resultado)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _inventario_por_categoria(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Inventario desglosado por categoría de producto."""
        try:
            Product = self.conector.odoo.env['product.product']
            product_ids = Product.search([
                ('type', '=', 'product'),
                ('qty_available', '>', 0)
            ], limit=5000)
            
            if not product_ids:
                return {'error': 'No hay productos con stock', 'tipo': 'inventario_categoria'}
            
            productos = Product.read(product_ids, ['categ_id', 'qty_available', 'standard_price'])
            
            por_categoria = {}
            for prod in productos:
                categ = prod.get('categ_id', [0, 'Sin categoría'])
                categ_id = categ[0] if isinstance(categ, (list, tuple)) else categ
                categ_nombre = categ[1] if isinstance(categ, (list, tuple)) and len(categ) > 1 else str(categ)
                
                if categ_id not in por_categoria:
                    por_categoria[categ_id] = {'nombre': categ_nombre, 'cantidad': 0, 'valor': 0, 'productos': 0}
                
                por_categoria[categ_id]['cantidad'] += prod.get('qty_available', 0)
                por_categoria[categ_id]['valor'] += prod.get('qty_available', 0) * prod.get('standard_price', 0)
                por_categoria[categ_id]['productos'] += 1
            
            categorias_lista = [
                {'categoria': v['nombre'], 'cantidad': v['cantidad'], 'valor_estimado': v['valor'], 'productos': v['productos']}
                for v in por_categoria.values()
            ]
            categorias_lista.sort(key=lambda x: x['cantidad'], reverse=True)
            
            return {
                'tipo': 'inventario_categoria',
                'categorias': categorias_lista[:contexto.limite],
                'total_categorias': len(categorias_lista),
                'total_cantidad': sum(c['cantidad'] for c in categorias_lista),
                'valor_total_estimado': sum(c['valor_estimado'] for c in categorias_lista)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _inventario_resumen(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Resumen general de inventario."""
        try:
            stock = self.conector.stock_disponible()
            
            if stock.empty:
                return {'error': 'No hay datos de stock', 'tipo': 'inventario_resumen'}
            
            return {
                'tipo': 'inventario_resumen',
                'metricas': {
                    'total_items': len(stock),
                    'total_unidades': float(stock['quantity'].sum()) if 'quantity' in stock.columns else 0,
                    'productos_sin_stock': len(stock[stock['quantity'] <= 0]) if 'quantity' in stock.columns else 0,
                    'productos_bajo_stock': len(stock[stock['quantity'] < 5]) if 'quantity' in stock.columns else 0
                },
                'datos': stock
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analizar_pos(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Análisis de POS según contexto."""
        # Similar a ventas pero para POS
        return self._ventas_por_tienda(contexto)
    
    def _analizar_facturas(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Análisis de facturas."""
        try:
            df = self.conector.facturas_periodo(contexto.fecha_inicio, contexto.fecha_fin)
            
            if df.empty:
                return {'error': 'No hay facturas en el período', 'tipo': 'facturas_resumen'}
            
            return {
                'tipo': 'facturas_resumen',
                'periodo': {'inicio': contexto.fecha_inicio, 'fin': contexto.fecha_fin},
                'metricas': {
                    'total_facturado': float(df['amount_total'].sum()),
                    'num_facturas': len(df),
                    'promedio_factura': float(df['amount_total'].mean())
                },
                'datos': df
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analizar_productos(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Análisis de productos."""
        try:
            Product = self.conector.odoo.env['product.product']
            product_ids = Product.search([('active', '=', True)], limit=1000)
            productos = Product.read(product_ids, ['name', 'default_code', 'categ_id', 'qty_available', 'list_price'])
            
            return {
                'tipo': 'productos_resumen',
                'total_productos': len(productos),
                'productos': productos[:contexto.limite]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analizar_generico(self, contexto: ContextoConsulta) -> Dict[str, Any]:
        """Análisis genérico cuando no hay coincidencia específica."""
        return {
            'tipo': 'generico',
            'mensaje': 'No se pudo determinar el tipo de análisis. Por favor especifica qué deseas analizar.',
            'sugerencias': [
                'ventas de este mes',
                'inventario por ubicación',
                'ventas por tienda',
                'comparar enero 2025 vs enero 2026',
                'ventas por marca',
                'top 20 productos vendidos'
            ]
        }


class FormateadorInteligente:
    """Formatea resultados de análisis inteligente a Markdown."""
    
    @staticmethod
    def formatear(resultado: Dict[str, Any]) -> str:
        """Formatea el resultado según su tipo."""
        tipo = resultado.get('tipo', 'generico')
        
        if tipo == 'clarificacion':
            return FormateadorInteligente._formatear_clarificacion(resultado)
        elif tipo == 'error':
            return f"## Error\n\n{resultado.get('error', 'Error desconocido')}"
        elif 'error' in resultado:
            return f"## Error\n\n{resultado['error']}"
        elif tipo == 'ventas_resumen':
            return FormateadorInteligente._formatear_ventas_resumen(resultado)
        elif tipo == 'ventas_tienda':
            return FormateadorInteligente._formatear_ventas_tienda(resultado)
        elif tipo == 'ventas_marca':
            return FormateadorInteligente._formatear_ventas_marca(resultado)
        elif tipo == 'ventas_vendedor':
            return FormateadorInteligente._formatear_ventas_vendedor(resultado)
        elif tipo == 'ventas_cliente':
            return FormateadorInteligente._formatear_ventas_cliente(resultado)
        elif tipo == 'ventas_empresa':
            return FormateadorInteligente._formatear_ventas_empresa(resultado)
        elif tipo == 'ventas_producto':
            return FormateadorInteligente._formatear_ventas_producto(resultado)
        elif tipo == 'ventas_periodo':
            return FormateadorInteligente._formatear_ventas_periodo(resultado)
        elif tipo == 'comparativa_ventas':
            return FormateadorInteligente._formatear_comparativa(resultado)
        elif tipo == 'inventario_ubicacion':
            return FormateadorInteligente._formatear_inventario_ubicacion(resultado)
        elif tipo == 'inventario_almacen':
            return FormateadorInteligente._formatear_inventario_almacen(resultado)
        elif tipo == 'inventario_categoria':
            return FormateadorInteligente._formatear_inventario_categoria(resultado)
        elif tipo == 'inventario_resumen':
            return FormateadorInteligente._formatear_inventario_resumen(resultado)
        else:
            return FormateadorInteligente._formatear_generico(resultado)
    
    @staticmethod
    def _formatear_clarificacion(resultado: Dict) -> str:
        """Formatea pregunta de clarificación."""
        md = f"## {resultado['pregunta']}\n\n"
        md += "Selecciona una opción:\n\n"
        for i, opcion in enumerate(resultado['opciones'], 1):
            md += f"{i}. {opcion}\n"
        md += "\n_Escribe el número o describe lo que necesitas_"
        return md
    
    @staticmethod
    def _formatear_ventas_resumen(resultado: Dict) -> str:
        """Formatea resumen de ventas."""
        m = resultado.get('metricas', {})
        periodo = resultado.get('periodo', {})
        
        return f"""## Resumen de Ventas

**Período:** {periodo.get('inicio', 'N/A')} a {periodo.get('fin', 'N/A')}

| Métrica | Valor |
|---------|-------|
| Total Ventas | **${m.get('total_ventas', 0):,.2f}** |
| Órdenes | **{m.get('num_ordenes', 0):,}** |
| Ticket Promedio | **${m.get('ticket_promedio', 0):,.2f}** |
| Venta Máxima | **${m.get('venta_maxima', 0):,.2f}** |
| Venta Mínima | **${m.get('venta_minima', 0):,.2f}** |

_Si necesitas más detalle, pregunta por: ventas por tienda, por vendedor, por producto, etc._
"""
    
    @staticmethod
    def _formatear_ventas_tienda(resultado: Dict) -> str:
        """Formatea ventas por tienda."""
        tiendas = resultado.get('tiendas', [])
        total = resultado.get('total_general', 0)
        
        md = f"""## Ventas por Tienda

**Total General:** ${total:,.2f} | **Tiendas:** {resultado.get('total_tiendas', 0)}

| # | Tienda | Total | Órdenes | % |
|---|--------|-------|---------|---|
"""
        for i, t in enumerate(tiendas, 1):
            pct = (t['total'] / total * 100) if total > 0 else 0
            md += f"| {i} | {str(t['tienda'])[:30]} | ${t['total']:,.2f} | {t['ordenes']} | {pct:.1f}% |\n"
        
        return md
    
    @staticmethod
    def _formatear_ventas_marca(resultado: Dict) -> str:
        """Formatea ventas por marca."""
        marcas = resultado.get('marcas', [])
        total = resultado.get('total_general', 0)
        
        md = f"""## Ventas por Marca

**Total General:** ${total:,.2f} | **Marcas:** {resultado.get('total_marcas', 0)}

| # | Marca | Total | Unidades | % |
|---|-------|-------|----------|---|
"""
        for i, m in enumerate(marcas, 1):
            pct = (m['total'] / total * 100) if total > 0 else 0
            md += f"| {i} | {str(m['marca'])[:30]} | ${m['total']:,.2f} | {m['unidades']:,.0f} | {pct:.1f}% |\n"
        
        return md
    
    @staticmethod
    def _formatear_ventas_vendedor(resultado: Dict) -> str:
        """Formatea ventas por vendedor."""
        vendedores = resultado.get('vendedores', [])
        total = resultado.get('total_general', 0)
        
        md = f"""## Ventas por Vendedor

**Total General:** ${total:,.2f} | **Vendedores:** {resultado.get('total_vendedores', 0)}

| # | Vendedor | Total | Órdenes | Promedio | % |
|---|----------|-------|---------|----------|---|
"""
        for i, v in enumerate(vendedores, 1):
            pct = (v['total'] / total * 100) if total > 0 else 0
            md += f"| {i} | {str(v['vendedor'])[:25]} | ${v['total']:,.2f} | {v['ordenes']} | ${v['promedio']:,.2f} | {pct:.1f}% |\n"
        
        return md
    
    @staticmethod
    def _formatear_ventas_cliente(resultado: Dict) -> str:
        """Formatea ventas por cliente."""
        clientes = resultado.get('clientes', [])
        total = resultado.get('total_general', 0)
        
        md = f"""## Ventas por Cliente

**Total General:** ${total:,.2f} | **Clientes:** {resultado.get('total_clientes', 0)}

| # | Cliente | Total | Órdenes | % |
|---|---------|-------|---------|---|
"""
        for i, c in enumerate(clientes, 1):
            pct = (c['total'] / total * 100) if total > 0 else 0
            md += f"| {i} | {str(c['cliente'])[:30]} | ${c['total']:,.2f} | {c['ordenes']} | {pct:.1f}% |\n"
        
        return md
    
    @staticmethod
    def _formatear_ventas_empresa(resultado: Dict) -> str:
        """Formatea ventas por empresa."""
        empresas = resultado.get('empresas', [])
        total = resultado.get('total_general', 0)
        
        md = f"""## Ventas por Empresa

**Total General:** ${total:,.2f} | **Empresas:** {resultado.get('total_empresas', 0)}

| # | Empresa | Total | Órdenes | % |
|---|---------|-------|---------|---|
"""
        for i, e in enumerate(empresas, 1):
            pct = (e['total'] / total * 100) if total > 0 else 0
            md += f"| {i} | {str(e['empresa'])[:30]} | ${e['total']:,.2f} | {e['ordenes']} | {pct:.1f}% |\n"
        
        return md
    
    @staticmethod
    def _formatear_ventas_producto(resultado: Dict) -> str:
        """Formatea ventas por producto."""
        productos = resultado.get('productos', [])
        total = resultado.get('total_general', 0)
        
        md = f"""## Ventas por Producto

**Total General:** ${total:,.2f} | **Productos:** {resultado.get('total_productos', 0)}

| # | Producto | Total | Unidades | % |
|---|----------|-------|----------|---|
"""
        for i, p in enumerate(productos, 1):
            pct = (p['total'] / total * 100) if total > 0 else 0
            md += f"| {i} | {str(p['producto'])[:35]} | ${p['total']:,.2f} | {p['unidades']:,.0f} | {pct:.1f}% |\n"
        
        return md
    
    @staticmethod
    def _formatear_ventas_periodo(resultado: Dict) -> str:
        """Formatea ventas por período."""
        periodos = resultado.get('periodos', [])
        total = resultado.get('total_general', 0)
        
        md = f"""## Ventas por Período

**Total General:** ${total:,.2f}

| Período | Total | Órdenes | % |
|---------|-------|---------|---|
"""
        for p in periodos:
            pct = (p['total'] / total * 100) if total > 0 else 0
            md += f"| {p['periodo']} | ${p['total']:,.2f} | {p['ordenes']} | {pct:.1f}% |\n"
        
        return md
    
    @staticmethod
    def _formatear_comparativa(resultado: Dict) -> str:
        """Formatea comparativa entre períodos."""
        a = resultado.get('periodo_a', {})
        b = resultado.get('periodo_b', {})
        var = resultado.get('variacion_porcentaje', 0)
        
        emoji_tendencia = '📈' if var > 0 else '📉' if var < 0 else '➡️'
        color_var = '+' if var > 0 else ''
        
        md = f"""## Comparativa: {a.get('nombre')} vs {b.get('nombre')}

### Resumen
| Métrica | {a.get('nombre')} | {b.get('nombre')} | Diferencia |
|---------|-------------------|-------------------|------------|
|  Total | ${a.get('total', 0):,.2f} | ${b.get('total', 0):,.2f} | {emoji_tendencia} {color_var}{var:.1f}% |
|  Órdenes | {a.get('ordenes', 0):,} | {b.get('ordenes', 0):,} | {b.get('ordenes', 0) - a.get('ordenes', 0):+,} |
|  Ticket Prom. | ${a.get('ticket_promedio', 0):,.2f} | ${b.get('ticket_promedio', 0):,.2f} | - |

###  Insights
"""
        for insight in resultado.get('insights', []):
            md += f"- {insight}\n"
        
        return md
    
    @staticmethod
    def _formatear_inventario_ubicacion(resultado: Dict) -> str:
        """Formatea inventario por ubicación."""
        ubicaciones = resultado.get('ubicaciones', [])
        total = resultado.get('total_cantidad', 0)
        
        md = f"""##  Inventario por Ubicación (location_id)

**Total Unidades:** {total:,.0f} | **Ubicaciones:** {resultado.get('total_ubicaciones', 0)}

| # | Location ID | Ubicación | Cantidad | Disponible | Productos | % |
|---|-------------|-----------|----------|------------|-----------|---|
"""
        for i, u in enumerate(ubicaciones, 1):
            pct = (u['cantidad_total'] / total * 100) if total > 0 else 0
            md += f"| {i} | {u['location_id']} | {str(u['ubicacion'])[:25]} | {u['cantidad_total']:,.0f} | {u['cantidad_disponible']:,.0f} | {u['productos_unicos']} | {pct:.1f}% |\n"
        
        return md
    
    @staticmethod
    def _formatear_inventario_almacen(resultado: Dict) -> str:
        """Formatea inventario por almacén."""
        almacenes = resultado.get('almacenes', [])
        total = resultado.get('total_cantidad', 0)
        
        md = f"""##  Inventario por Almacén

**Total Unidades:** {total:,.0f} | **Almacenes:** {resultado.get('total_almacenes', 0)}

| # | Almacén | Empresa | Cantidad | Productos | % |
|---|---------|---------|----------|-----------|---|
"""
        for i, a in enumerate(almacenes, 1):
            pct = (a['cantidad_total'] / total * 100) if total > 0 else 0
            md += f"| {i} | {str(a['almacen'])[:20]} | {str(a['empresa'])[:15]} | {a['cantidad_total']:,.0f} | {a['productos_unicos']} | {pct:.1f}% |\n"
        
        return md
    
    @staticmethod
    def _formatear_inventario_categoria(resultado: Dict) -> str:
        """Formatea inventario por categoría."""
        categorias = resultado.get('categorias', [])
        total = resultado.get('total_cantidad', 0)
        
        md = f"""##  Inventario por Categoría

**Total Unidades:** {total:,.0f} | **Categorías:** {resultado.get('total_categorias', 0)}

| # | Categoría | Cantidad | Valor Est. | Productos | % |
|---|-----------|----------|------------|-----------|---|
"""
        for i, c in enumerate(categorias, 1):
            pct = (c['cantidad'] / total * 100) if total > 0 else 0
            md += f"| {i} | {str(c['categoria'])[:25]} | {c['cantidad']:,.0f} | ${c['valor_estimado']:,.2f} | {c['productos']} | {pct:.1f}% |\n"
        
        return md
    
    @staticmethod
    def _formatear_inventario_resumen(resultado: Dict) -> str:
        """Formatea resumen de inventario."""
        m = resultado.get('metricas', {})
        
        return f"""##  Resumen de Inventario

| Métrica | Valor |
|---------|-------|
|  Total Items | **{m.get('total_items', 0):,}** |
|  Total Unidades | **{m.get('total_unidades', 0):,.0f}** |
|  Sin Stock | **{m.get('productos_sin_stock', 0)}** |
|  Bajo Stock (<5) | **{m.get('productos_bajo_stock', 0)}** |

_Para más detalle: inventario por ubicación, por almacén, por categoría_
"""
    
    @staticmethod
    def _formatear_generico(resultado: Dict) -> str:
        """Formatea resultado genérico."""
        if 'sugerencias' in resultado:
            md = f"## 💡 {resultado.get('mensaje', 'Sugerencias')}\n\n"
            md += "Prueba con:\n"
            for sug in resultado['sugerencias']:
                md += f"- {sug}\n"
            return md
        
        return f"## Resultado\n\n{resultado}"


# Instancias globales
analizador_inteligente = AnalizadorInteligente()
formateador_inteligente = FormateadorInteligente()
detector_contexto = DetectorContexto()


# Función de exportación
def set_conector_analisis(conector):
    """Configura el conector para el analizador inteligente."""
    analizador_inteligente.set_conector(conector)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" ANÁLISIS INTELIGENTE - Test de Detección de Contexto")
    print("=" * 60)
    
    detector = DetectorContexto()
    
    pruebas = [
        "ventas",
        "ventas de enero 2025",
        "ventas por tienda",
        "ventas por marca este mes",
        "comparar ventas enero 2025 vs enero 2026",
        "inventario por ubicación",
        "inventario",
        "top 10 productos vendidos",
        "ventas de diciembre 2024 por vendedor",
    ]
    
    for consulta in pruebas:
        print(f"\nConsulta: '{consulta}'")
        ctx = detector.detectar(consulta)
        print(f"   Tipo: {ctx.tipo_reporte}")
        print(f"   Agrupación: {ctx.agrupacion.value}")
        print(f"   Comparativa: {ctx.comparativa.value}")
        print(f"   Fechas: {ctx.fecha_inicio} - {ctx.fecha_fin}")
        if ctx.necesita_clarificacion:
            print(f"   Pregunta: {ctx.pregunta_clarificacion}")
