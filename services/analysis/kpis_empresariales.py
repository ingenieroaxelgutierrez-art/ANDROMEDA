# ============================================================
# ANDROMEDA - KPIs EMPRESARIALES COMPLETOS
# Análisis de KPIs por categoría empresarial
# ============================================================
# Categorías:
#   - Comercial
#   - Talento (RH)
#   - Operaciones
#   - Tiendas
#   - Compras
# ============================================================

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

from app.logging_config import get_logger
logger = get_logger("services.analysis.kpis_empresariales")

# Agregar directorio raíz al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ============================================================
# ENUMS Y DATACLASSES
# ============================================================

class CategoriaKPI(Enum):
    """Categorías de KPIs empresariales."""
    COMERCIAL = "comercial"
    TALENTO = "talento"
    OPERACIONES = "operaciones"
    TIENDAS = "tiendas"
    COMPRAS = "compras"


class TipoAgrupacion(Enum):
    """Tipos de agrupación para análisis."""
    POR_MES = "mes"
    POR_SEMANA = "semana"
    POR_DIA = "dia"
    POR_CANAL = "canal"
    POR_MARCA = "marca"
    POR_CATEGORIA = "categoria"
    POR_TIENDA = "tienda"
    POR_VENDEDOR = "vendedor"
    POR_CLIENTE = "cliente"
    POR_PRODUCTO = "producto"
    POR_UBICACION = "ubicacion"


@dataclass
class ResultadoKPI:
    """Resultado de un análisis de KPI."""
    nombre: str
    categoria: CategoriaKPI
    valor: Any
    unidad: str = ""
    tendencia: str = ""  # "↑", "↓", "→"
    variacion_porcentual: float = 0.0
    periodo: str = ""
    detalles: Dict = field(default_factory=dict)
    datos: Optional[pd.DataFrame] = None
    alertas: List[str] = field(default_factory=list)
    recomendaciones: List[str] = field(default_factory=list)
    error: Optional[str] = None  # Mensaje de error si falló
    meta: Optional[float] = None  # Meta del KPI
    cumplimiento: Optional[float] = None  # Porcentaje de cumplimiento
    estado: str = ""  # Estado: 'bueno', 'regular', 'malo'
    variacion: Optional[float] = None  # Variación absoluta
    insights: List[str] = field(default_factory=list)  # Insights generados


@dataclass
class ConfigKPI:
    """Configuración para análisis de KPIs."""
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    tiendas: List[str] = field(default_factory=list)
    marcas: List[str] = field(default_factory=list)
    canales: List[str] = field(default_factory=list)
    vendedores: List[str] = field(default_factory=list)
    comparar_periodo_anterior: bool = True
    incluir_proyecciones: bool = False


# ============================================================
# MOTOR DE KPIs EMPRESARIALES
# ============================================================

class MotorKPIsEmpresariales:
    """
    Motor principal de KPIs empresariales para ANDROMEDA.
    
    Integra análisis de:
    - KPIs Comerciales
    - KPIs de Talento (RH)
    - KPIs de Operaciones
    - KPIs de Tiendas
    - KPIs de Compras
    """
    
    def __init__(self, conector_odoo=None):
        """
        Inicializa el motor de KPIs.
        
        Args:
            conector_odoo: Conector a Odoo para obtener datos
        """
        self.conector = conector_odoo
        self.cache = {}
        
        # Mapeo de intenciones a métodos
        self.kpis_disponibles = {
            # === COMERCIAL ===
            'ventas_mensuales': self.kpi_ventas_mensuales,
            'ventas_por_canal': self.kpi_ventas_por_canal,
            'ventas_por_marca': self.kpi_ventas_por_marca,
            'ventas_por_categoria': self.kpi_ventas_por_categoria,
            'subtotal_cliente': self.kpi_subtotal_cliente,
            'clientes_atendidos': self.kpi_clientes_atendidos,
            'subtotal_vendedor': self.kpi_subtotal_vendedor,
            'meta_tendencia_canal': self.kpi_meta_tendencia_canal,
            'cliente_ciudad_marca': self.kpi_cliente_ciudad_marca,
            'crecimiento_anual': self.kpi_crecimiento_anual,
            
            # === TALENTO (RH) ===
            'rotacion_personal': self.kpi_rotacion_personal,
            'porcentaje_mensual_acumulado': self.kpi_porcentaje_mensual_acumulado,
            'cumplimiento_pago': self.kpi_cumplimiento_pago,
            'variacion_salarial': self.kpi_variacion_salarial,
            'equidad_genero': self.kpi_equidad_genero,
            
            # === OPERACIONES ===
            'pedidos_surtidos': self.kpi_pedidos_surtidos,
            'facturacion_mensual': self.kpi_facturacion_mensual,
            'gasto_paqueteria': self.kpi_gasto_paqueteria,
            
            # === TIENDAS ===
            'ventas_tienda': self.kpi_ventas_tienda,
            'utilidad_tienda': self.kpi_utilidad_tienda,
            'inventario_marcas': self.kpi_inventario_marcas,
            'mix_marca_venta': self.kpi_mix_marca_venta,
            'obsoletos': self.kpi_obsoletos,
            'ticket_promedio': self.kpi_ticket_promedio,
            'articulo_ticket': self.kpi_articulo_ticket,
            'decremento_inventario': self.kpi_decremento_inventario,
            'incidencias_financieras': self.kpi_incidencias_financieras,
            'ranking_ventas': self.kpi_ranking_ventas,
            'rotacion_inventario_tienda': self.kpi_rotacion_inventario_tienda,
            
            # === COMPRAS ===
            'cuentas_gasto': self.kpi_cuentas_gasto,
            'faltantes': self.kpi_faltantes,
            'costeo_real': self.kpi_costeo_real,
            'comparativa_fletes': self.kpi_comparativa_fletes,
            'rotacion_producto': self.kpi_rotacion_producto,
            'maximos_minimos': self.kpi_maximos_minimos,
            'picking_cedis': self.kpi_picking_cedis,
        }
        
        print("Motor de KPIs Empresariales cargado")
    
    def set_conector(self, conector):
        """Establece el conector a Odoo."""
        self.conector = conector
    
    def listar_kpis(self, categoria: CategoriaKPI = None) -> Dict[str, List[str]]:
        """Lista todos los KPIs disponibles por categoría."""
        kpis = {
            CategoriaKPI.COMERCIAL.value: [
                "Ventas mensuales por canal, fecha, marca y categoría",
                "Subtotal por cliente",
                "Cantidad de clientes atendidos por mes",
                "Subtotal por vendedor, canal, marca y mes",
                "Meta, tendencia y alcance por canal",
                "Cliente, ciudad, marca y subtotal",
                "Crecimiento global anual (2020-2025)"
            ],
            CategoriaKPI.TALENTO.value: [
                "Rotación de personal",
                "Porcentaje mensual y acumulado",
                "Cumplimiento de pago puntual",
                "Porcentaje de variación salarial anual",
                "Equidad interna (brecha salarial por género)"
            ],
            CategoriaKPI.OPERACIONES.value: [
                "Pedidos surtidos",
                "Facturación mensual",
                "Gasto mensual paquetería"
            ],
            CategoriaKPI.TIENDAS.value: [
                "Ventas por tienda",
                "Utilidad por tienda",
                "Inventario por marcas",
                "Mix de marca en venta",
                "Porcentaje de crecimiento de obsoletos",
                "Ticket promedio",
                "Artículo por ticket",
                "Decremento de inventario",
                "Incidencias financieras",
                "Ranking de ventas (dinero y piezas)",
                "Rotación de inventarios por tienda"
            ],
            CategoriaKPI.COMPRAS.value: [
                "Reporte de cuentas de gasto, almacenaje y demoras",
                "Faltantes",
                "Costeo contra costo real",
                "Comparativa de fletes",
                "Tablero de rotación de producto",
                "Máximos y mínimos por tienda",
                "Picking de productos CEDIS"
            ]
        }
        
        if categoria:
            return {categoria.value: kpis.get(categoria.value, [])}
        return kpis
    
    def ejecutar_kpi(self, nombre_kpi: str, fecha_inicio=None, fecha_fin=None, params: Dict = None) -> ResultadoKPI:
        """
        Ejecuta un KPI específico por nombre.
        
        Args:
            nombre_kpi: Nombre del KPI a ejecutar (ej: 'kpi_ventas_por_canal')
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            params: Parámetros adicionales
        
        Returns:
            ResultadoKPI con los datos
        """
        # Remover prefijo 'kpi_' si existe
        nombre_limpio = nombre_kpi.replace('kpi_', '') if nombre_kpi.startswith('kpi_') else nombre_kpi
        
        # Buscar método correspondiente
        metodo = self.kpis_disponibles.get(nombre_limpio)
        
        if not metodo:
            return ResultadoKPI(
                nombre=nombre_kpi,
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                error=f"KPI '{nombre_kpi}' no encontrado. Disponibles: {list(self.kpis_disponibles.keys())}"
            )
        
        try:
            config = ConfigKPI(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                **(params or {})
            )
            return metodo(config)
        except Exception as e:
            return ResultadoKPI(
                nombre=nombre_kpi,
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                error=str(e)
            )
    
    def ejecutar_categoria(self, categoria: CategoriaKPI, fecha_inicio=None, fecha_fin=None) -> List[ResultadoKPI]:
        """
        Ejecuta todos los KPIs de una categoría.
        
        Args:
            categoria: Categoría de KPIs a ejecutar
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
        
        Returns:
            Lista de ResultadoKPI con los datos
        """
        resultados = []
        
        # Mapear categorías a sus KPIs
        kpis_por_categoria = {
            CategoriaKPI.COMERCIAL: ['ventas_mensuales', 'ventas_por_canal', 'ventas_por_marca', 
                                     'ventas_por_categoria', 'clientes_atendidos', 'crecimiento_anual'],
            CategoriaKPI.TALENTO: ['rotacion_personal', 'porcentaje_mensual_acumulado', 
                                   'cumplimiento_pago', 'equidad_genero'],
            CategoriaKPI.OPERACIONES: ['pedidos_surtidos', 'facturacion_mensual', 'gasto_paqueteria'],
            CategoriaKPI.TIENDAS: ['ventas_tienda', 'utilidad_tienda', 'ticket_promedio', 
                                   'articulo_ticket', 'ranking_ventas', 'rotacion_inventario_tienda'],
            CategoriaKPI.COMPRAS: ['faltantes', 'costeo_real', 'comparativa_fletes', 
                                   'rotacion_producto', 'maximos_minimos', 'picking_cedis']
        }
        
        kpis_a_ejecutar = kpis_por_categoria.get(categoria, [])
        
        for nombre_kpi in kpis_a_ejecutar:
            try:
                resultado = self.ejecutar_kpi(nombre_kpi, fecha_inicio, fecha_fin)
                if resultado:
                    resultados.append(resultado)
            except Exception as e:
                resultados.append(ResultadoKPI(
                    nombre=nombre_kpi,
                    categoria=categoria,
                    valor=0,
                    error=str(e)
                ))
        
        return resultados
    
    def generar_dashboard_completo(self, fecha_inicio=None, fecha_fin=None) -> Dict:
        """
        Genera un dashboard con todos los KPIs principales de todas las categorías.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
        
        Returns:
            Dict con resultados agrupados por categoría
        """
        dashboard = {
            'titulo': 'Dashboard de KPIs Empresariales',
            'fecha_generacion': datetime.now().isoformat(),
            'periodo': {
                'inicio': fecha_inicio.isoformat() if fecha_inicio else None,
                'fin': fecha_fin.isoformat() if fecha_fin else None
            },
            'categorias': {}
        }
        
        for categoria in CategoriaKPI:
            try:
                resultados = self.ejecutar_categoria(categoria, fecha_inicio, fecha_fin)
                dashboard['categorias'][categoria.value] = {
                    'nombre': categoria.value,
                    'emoji': self._emoji_categoria(categoria),
                    'kpis': [self._resultado_a_dict(r) for r in resultados],
                    'total_kpis': len(resultados),
                    'kpis_exitosos': len([r for r in resultados if not r.error])
                }
            except Exception as e:
                dashboard['categorias'][categoria.value] = {
                    'nombre': categoria.value,
                    'error': str(e)
                }
        
        return dashboard
    
    def _emoji_categoria(self, categoria: CategoriaKPI) -> str:
        """Retorna emoji para cada categoría."""
        emojis = {
            CategoriaKPI.COMERCIAL: '📈',
            CategoriaKPI.TALENTO: '👥',
            CategoriaKPI.OPERACIONES: '⚙️',
            CategoriaKPI.TIENDAS: '🏪',
            CategoriaKPI.COMPRAS: '📦'
        }
        return emojis.get(categoria, '📊')
    
    def _resultado_a_dict(self, resultado: ResultadoKPI) -> Dict:
        """Convierte un ResultadoKPI a diccionario."""
        return {
            'nombre': resultado.nombre,
            'valor': resultado.valor,
            'unidad': resultado.unidad,
            'tendencia': resultado.tendencia,
            'variacion': resultado.variacion,
            'meta': resultado.meta,
            'cumplimiento': resultado.cumplimiento,
            'estado': resultado.estado,
            'periodo': resultado.periodo,
            'datos': resultado.datos,
            'insights': resultado.insights,
            'error': resultado.error
        }
    
    # ================================================================
    # KPIs COMERCIALES
    # ================================================================
    
    def kpi_ventas_mensuales(self, config: ConfigKPI = None) -> ResultadoKPI:
        """
        Ventas mensuales por canal, fecha, marca y categoría.
        """
        config = config or ConfigKPI()
        
        try:
            # Obtener datos de ventas
            fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=365))
            fecha_fin = config.fecha_fin or datetime.now()
            
            if self.conector and self.conector.conectado:
                # Consultar POS y ventas
                filtros = [
                    ('date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                pos_data = self.conector.buscar_leer(
                    'pos.order',
                    filtros,
                    ['name', 'date_order', 'amount_total', 'session_id', 'partner_id']
                )
                
                if pos_data:
                    df = pd.DataFrame(pos_data)
                    df['date_order'] = pd.to_datetime(df['date_order'])
                    df['mes'] = df['date_order'].dt.to_period('M')
                    
                    # Agrupar por mes
                    ventas_mes = df.groupby('mes').agg({
                        'amount_total': 'sum',
                        'name': 'count'
                    }).reset_index()
                    ventas_mes.columns = ['Mes', 'Ventas Total', 'Cantidad Órdenes']
                    
                    total_ventas = df['amount_total'].sum()
                    promedio_mensual = total_ventas / max(len(ventas_mes), 1)
                    
                    # Calcular tendencia
                    if len(ventas_mes) >= 2:
                        ultimo = ventas_mes['Ventas Total'].iloc[-1]
                        penultimo = ventas_mes['Ventas Total'].iloc[-2]
                        if penultimo > 0:
                            variacion = ((ultimo - penultimo) / penultimo * 100)
                        elif ultimo > 0:
                            variacion = 999.99  # Crecimiento desde cero (nuevo)
                        else:
                            variacion = 0
                        tendencia = "↑" if variacion > 0 else "↓" if variacion < 0 else "→"
                    else:
                        variacion = 0
                        tendencia = "→"
                    
                    return ResultadoKPI(
                        nombre="Ventas Mensuales",
                        categoria=CategoriaKPI.COMERCIAL,
                        valor=total_ventas,
                        unidad="MXN",
                        tendencia=tendencia,
                        variacion_porcentual=variacion,
                        periodo=f"{fecha_inicio.strftime('%Y-%m')} a {fecha_fin.strftime('%Y-%m')}",
                        detalles={
                            'promedio_mensual': promedio_mensual,
                            'total_ordenes': len(df),
                            'meses_analizados': len(ventas_mes)
                        },
                        datos=ventas_mes
                    )
            
            # Respuesta sin datos
            return ResultadoKPI(
                nombre="Ventas Mensuales",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=["No hay conexión a Odoo o no hay datos disponibles"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Ventas Mensuales",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=[f"Error al calcular: {str(e)}"]
            )
    
    def kpi_ventas_por_canal(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Ventas desglosadas por canal de venta."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                # POS orders (tienda física)
                filtros_pos = [
                    ('date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                pos_data = self.conector.buscar_leer(
                    'pos.order', filtros_pos, ['name', 'amount_total', 'session_id']
                )
                
                # Sale orders (ventas online/mostrador)
                filtros_sale = [
                    ('date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', 'in', ['sale', 'done'])
                ]
                
                sale_data = self.conector.buscar_leer(
                    'sale.order', filtros_sale, ['name', 'amount_total', 'team_id']
                )
                
                canales = {
                    'POS (Tienda Física)': sum(p.get('amount_total', 0) for p in pos_data) if pos_data else 0,
                    'Ventas (Online/Mostrador)': sum(s.get('amount_total', 0) for s in sale_data) if sale_data else 0
                }
                
                total = sum(canales.values())
                
                df_canales = pd.DataFrame([
                    {'Canal': k, 'Ventas': v, 'Porcentaje': (v/total*100) if total > 0 else 0}
                    for k, v in canales.items()
                ])
                
                return ResultadoKPI(
                    nombre="Ventas por Canal",
                    categoria=CategoriaKPI.COMERCIAL,
                    valor=total,
                    unidad="MXN",
                    periodo=f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}",
                    detalles=canales,
                    datos=df_canales
                )
            
            return ResultadoKPI(
                nombre="Ventas por Canal",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=["Sin conexión a Odoo"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Ventas por Canal",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_ventas_por_marca(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Ventas desglosadas por marca de producto."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                # Obtener líneas de POS con productos
                filtros = [
                    ('order_id.date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('order_id.date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('order_id.state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                lineas = self.conector.buscar_leer(
                    'pos.order.line',
                    filtros,
                    ['product_id', 'price_subtotal', 'qty']
                )
                
                if lineas:
                    # Obtener información de productos
                    product_ids = list(set(l['product_id'][0] for l in lineas if l.get('product_id')))
                    
                    productos = self.conector.buscar_leer(
                        'product.product',
                        [('id', 'in', product_ids)],
                        ['id', 'name', 'product_brand_id', 'categ_id']
                    )
                    
                    prod_dict = {p['id']: p for p in productos}
                    
                    marcas = {}
                    for linea in lineas:
                        if linea.get('product_id'):
                            prod_id = linea['product_id'][0]
                            prod = prod_dict.get(prod_id, {})
                            marca = prod.get('product_brand_id', ['', 'Sin Marca'])
                            marca_nombre = marca[1] if isinstance(marca, (list, tuple)) and len(marca) > 1 else 'Sin Marca'
                            
                            if marca_nombre not in marcas:
                                marcas[marca_nombre] = {'ventas': 0, 'unidades': 0}
                            
                            marcas[marca_nombre]['ventas'] += linea.get('price_subtotal', 0)
                            marcas[marca_nombre]['unidades'] += linea.get('qty', 0)
                    
                    total = sum(m['ventas'] for m in marcas.values())
                    
                    df_marcas = pd.DataFrame([
                        {
                            'Marca': k,
                            'Ventas': v['ventas'],
                            'Unidades': v['unidades'],
                            'Porcentaje': (v['ventas']/total*100) if total > 0 else 0
                        }
                        for k, v in sorted(marcas.items(), key=lambda x: x[1].get('ventas', 0), reverse=True)
                    ])
                    
                    return ResultadoKPI(
                        nombre="Ventas por Marca",
                        categoria=CategoriaKPI.COMERCIAL,
                        valor=total,
                        unidad="MXN",
                        periodo=f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}",
                        detalles={'total_marcas': len(marcas)},
                        datos=df_marcas
                    )
            
            return ResultadoKPI(
                nombre="Ventas por Marca",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=["Sin datos disponibles"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Ventas por Marca",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_ventas_por_categoria(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Ventas desglosadas por categoría de producto."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                filtros = [
                    ('order_id.date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('order_id.date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('order_id.state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                lineas = self.conector.buscar_leer(
                    'pos.order.line',
                    filtros,
                    ['product_id', 'price_subtotal', 'qty']
                )
                
                if lineas:
                    product_ids = list(set(l['product_id'][0] for l in lineas if l.get('product_id')))
                    
                    productos = self.conector.buscar_leer(
                        'product.product',
                        [('id', 'in', product_ids)],
                        ['id', 'categ_id']
                    )
                    
                    prod_dict = {p['id']: p for p in productos}
                    
                    categorias = {}
                    for linea in lineas:
                        if linea.get('product_id'):
                            prod_id = linea['product_id'][0]
                            prod = prod_dict.get(prod_id, {})
                            categ = prod.get('categ_id', ['', 'Sin Categoría'])
                            categ_nombre = categ[1] if isinstance(categ, (list, tuple)) and len(categ) > 1 else 'Sin Categoría'
                            
                            if categ_nombre not in categorias:
                                categorias[categ_nombre] = {'ventas': 0, 'unidades': 0}
                            
                            categorias[categ_nombre]['ventas'] += linea.get('price_subtotal', 0)
                            categorias[categ_nombre]['unidades'] += linea.get('qty', 0)
                    
                    total = sum(c['ventas'] for c in categorias.values())
                    
                    df_categorias = pd.DataFrame([
                        {
                            'Categoría': k,
                            'Ventas': v['ventas'],
                            'Unidades': v['unidades'],
                            'Porcentaje': (v['ventas']/total*100) if total > 0 else 0
                        }
                        for k, v in sorted(categorias.items(), key=lambda x: x[1].get('ventas', 0), reverse=True)
                    ])
                    
                    return ResultadoKPI(
                        nombre="Ventas por Categoría",
                        categoria=CategoriaKPI.COMERCIAL,
                        valor=total,
                        unidad="MXN",
                        datos=df_categorias
                    )
            
            return ResultadoKPI(
                nombre="Ventas por Categoría",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Ventas por Categoría",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_subtotal_cliente(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Subtotal de ventas por cliente."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                filtros = [
                    ('date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                ordenes = self.conector.buscar_leer(
                    'pos.order',
                    filtros,
                    ['partner_id', 'amount_total']
                )
                
                if ordenes:
                    clientes = {}
                    for orden in ordenes:
                        partner = orden.get('partner_id')
                        if partner:
                            cliente_nombre = partner[1] if isinstance(partner, (list, tuple)) else 'Cliente General'
                        else:
                            cliente_nombre = 'Cliente General'
                        
                        if cliente_nombre not in clientes:
                            clientes[cliente_nombre] = {'ventas': 0, 'ordenes': 0}
                        
                        clientes[cliente_nombre]['ventas'] += orden.get('amount_total', 0)
                        clientes[cliente_nombre]['ordenes'] += 1
                    
                    total = sum(c['ventas'] for c in clientes.values())
                    
                    df_clientes = pd.DataFrame([
                        {
                            'Cliente': k,
                            'Total Ventas': v['ventas'],
                            'Órdenes': v['ordenes'],
                            'Ticket Promedio': v['ventas'] / v['ordenes'] if v['ordenes'] > 0 else 0
                        }
                        for k, v in sorted(clientes.items(), key=lambda x: x[1].get('ventas', 0), reverse=True)[:50]  # Top 50
                    ])
                    
                    return ResultadoKPI(
                        nombre="Subtotal por Cliente",
                        categoria=CategoriaKPI.COMERCIAL,
                        valor=total,
                        unidad="MXN",
                        detalles={
                            'total_clientes': len(clientes),
                            'cliente_top': df_clientes.iloc[0]['Cliente'] if len(df_clientes) > 0 else 'N/A'
                        },
                        datos=df_clientes
                    )
            
            return ResultadoKPI(
                nombre="Subtotal por Cliente",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Subtotal por Cliente",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_clientes_atendidos(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Cantidad de clientes atendidos por mes."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=365))
                fecha_fin = config.fecha_fin or datetime.now()
                
                filtros = [
                    ('date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                ordenes = self.conector.buscar_leer(
                    'pos.order',
                    filtros,
                    ['partner_id', 'date_order']
                )
                
                if ordenes:
                    df = pd.DataFrame(ordenes)
                    df['date_order'] = pd.to_datetime(df['date_order'])
                    df['mes'] = df['date_order'].dt.to_period('M')
                    df['partner_id'] = df['partner_id'].apply(
                        lambda x: x[0] if isinstance(x, (list, tuple)) else x
                    )
                    
                    # Contar clientes únicos por mes
                    clientes_mes = df.groupby('mes')['partner_id'].nunique().reset_index()
                    clientes_mes.columns = ['Mes', 'Clientes Únicos']
                    
                    total_clientes = df['partner_id'].nunique()
                    promedio_mensual = clientes_mes['Clientes Únicos'].mean()
                    
                    return ResultadoKPI(
                        nombre="Clientes Atendidos por Mes",
                        categoria=CategoriaKPI.COMERCIAL,
                        valor=total_clientes,
                        unidad="clientes",
                        detalles={
                            'promedio_mensual': round(promedio_mensual, 0),
                            'mejor_mes': clientes_mes.loc[clientes_mes['Clientes Únicos'].idxmax(), 'Mes'].strftime('%Y-%m') if len(clientes_mes) > 0 else 'N/A'
                        },
                        datos=clientes_mes
                    )
            
            return ResultadoKPI(
                nombre="Clientes Atendidos por Mes",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Clientes Atendidos por Mes",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_subtotal_vendedor(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Subtotal por vendedor, canal, marca y mes."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                # Obtener órdenes POS con usuario/vendedor
                filtros = [
                    ('date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                ordenes = self.conector.buscar_leer(
                    'pos.order',
                    filtros,
                    ['user_id', 'amount_total', 'session_id', 'date_order']
                )
                
                if ordenes:
                    vendedores = {}
                    for orden in ordenes:
                        user = orden.get('user_id')
                        vendedor_nombre = user[1] if isinstance(user, (list, tuple)) else 'Sin Vendedor'
                        
                        if vendedor_nombre not in vendedores:
                            vendedores[vendedor_nombre] = {'ventas': 0, 'ordenes': 0}
                        
                        vendedores[vendedor_nombre]['ventas'] += orden.get('amount_total', 0)
                        vendedores[vendedor_nombre]['ordenes'] += 1
                    
                    total = sum(v['ventas'] for v in vendedores.values())
                    
                    df_vendedores = pd.DataFrame([
                        {
                            'Vendedor': k,
                            'Ventas': v['ventas'],
                            'Órdenes': v['ordenes'],
                            'Ticket Promedio': v['ventas'] / v['ordenes'] if v['ordenes'] > 0 else 0,
                            'Porcentaje': (v['ventas'] / total * 100) if total > 0 else 0
                        }
                        for k, v in sorted(vendedores.items(), key=lambda x: x[1].get('ventas', 0), reverse=True)
                    ])
                    
                    return ResultadoKPI(
                        nombre="Subtotal por Vendedor",
                        categoria=CategoriaKPI.COMERCIAL,
                        valor=total,
                        unidad="MXN",
                        detalles={
                            'total_vendedores': len(vendedores),
                            'top_vendedor': df_vendedores.iloc[0]['Vendedor'] if len(df_vendedores) > 0 else 'N/A'
                        },
                        datos=df_vendedores
                    )
            
            return ResultadoKPI(
                nombre="Subtotal por Vendedor",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Subtotal por Vendedor",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_meta_tendencia_canal(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Meta, tendencia y alcance por canal."""
        config = config or ConfigKPI()
        # Este KPI requiere configuración de metas en Odoo
        # Por ahora retorna un placeholder
        return ResultadoKPI(
            nombre="Meta, Tendencia y Alcance por Canal",
            categoria=CategoriaKPI.COMERCIAL,
            valor=0,
            alertas=["Requiere configuración de metas en el sistema"],
            recomendaciones=["Configurar metas de ventas por canal en Odoo"]
        )
    
    def kpi_cliente_ciudad_marca(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Análisis de cliente por ciudad, marca y subtotal."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                filtros = [
                    ('date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                ordenes = self.conector.buscar_leer(
                    'pos.order',
                    filtros,
                    ['partner_id', 'amount_total']
                )
                
                if ordenes:
                    # Obtener info de clientes
                    partner_ids = list(set(
                        o['partner_id'][0] for o in ordenes 
                        if o.get('partner_id') and isinstance(o['partner_id'], (list, tuple))
                    ))
                    
                    if partner_ids:
                        partners = self.conector.buscar_leer(
                            'res.partner',
                            [('id', 'in', partner_ids)],
                            ['id', 'name', 'city', 'state_id']
                        )
                        
                        partner_dict = {p['id']: p for p in partners}
                        
                        ciudades = {}
                        for orden in ordenes:
                            if orden.get('partner_id'):
                                partner_id = orden['partner_id'][0]
                                partner = partner_dict.get(partner_id, {})
                                ciudad = partner.get('city', 'Sin Ciudad') or 'Sin Ciudad'
                                
                                if ciudad not in ciudades:
                                    ciudades[ciudad] = {'ventas': 0, 'clientes': set()}
                                
                                ciudades[ciudad]['ventas'] += orden.get('amount_total', 0)
                                ciudades[ciudad]['clientes'].add(partner_id)
                        
                        df_ciudades = pd.DataFrame([
                            {
                                'Ciudad': k,
                                'Ventas': v['ventas'],
                                'Clientes': len(v['clientes'])
                            }
                            for k, v in sorted(ciudades.items(), key=lambda x: x[1].get('ventas', 0), reverse=True)
                        ])
                        
                        return ResultadoKPI(
                            nombre="Cliente por Ciudad y Subtotal",
                            categoria=CategoriaKPI.COMERCIAL,
                            valor=sum(c['ventas'] for c in ciudades.values()),
                            unidad="MXN",
                            datos=df_ciudades
                        )
            
            return ResultadoKPI(
                nombre="Cliente por Ciudad y Subtotal",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Cliente por Ciudad y Subtotal",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_crecimiento_anual(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Crecimiento global anual (histórico)."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                # Obtener últimos 5 años de datos
                fecha_inicio = datetime(datetime.now().year - 5, 1, 1)
                fecha_fin = datetime.now()
                
                filtros = [
                    ('date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                ordenes = self.conector.buscar_leer(
                    'pos.order',
                    filtros,
                    ['date_order', 'amount_total']
                )
                
                if ordenes:
                    df = pd.DataFrame(ordenes)
                    df['date_order'] = pd.to_datetime(df['date_order'])
                    df['año'] = df['date_order'].dt.year
                    
                    ventas_año = df.groupby('año')['amount_total'].sum().reset_index()
                    ventas_año.columns = ['Año', 'Ventas']
                    
                    # Calcular crecimiento YoY
                    ventas_año['Crecimiento %'] = ventas_año['Ventas'].pct_change() * 100
                    ventas_año['Crecimiento %'] = ventas_año['Crecimiento %'].fillna(0).round(2)
                    
                    crecimiento_promedio = ventas_año['Crecimiento %'].mean()
                    
                    return ResultadoKPI(
                        nombre="Crecimiento Global Anual",
                        categoria=CategoriaKPI.COMERCIAL,
                        valor=crecimiento_promedio,
                        unidad="%",
                        tendencia="↑" if crecimiento_promedio > 0 else "↓",
                        variacion_porcentual=crecimiento_promedio,
                        detalles={
                            'años_analizados': len(ventas_año),
                            'mejor_año': int(ventas_año.loc[ventas_año['Ventas'].idxmax(), 'Año']) if len(ventas_año) > 0 else 'N/A'
                        },
                        datos=ventas_año
                    )
            
            return ResultadoKPI(
                nombre="Crecimiento Global Anual",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=["Sin datos históricos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Crecimiento Global Anual",
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    # ================================================================
    # KPIs TALENTO (RH)
    # ================================================================
    
    def kpi_rotacion_personal(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Rotación de personal."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                # Buscar empleados
                empleados_activos = self.conector.buscar_leer(
                    'hr.employee',
                    [('active', '=', True)],
                    ['id', 'name', 'department_id', 'job_id']
                )
                
                empleados_inactivos = self.conector.buscar_leer(
                    'hr.employee',
                    [('active', '=', False)],
                    ['id', 'name', 'department_id']
                )
                
                total_activos = len(empleados_activos) if empleados_activos else 0
                total_bajas = len(empleados_inactivos) if empleados_inactivos else 0
                
                # Tasa de rotación = (Bajas / Promedio empleados) * 100
                promedio = (total_activos + total_bajas) / 2 if (total_activos + total_bajas) > 0 else 1
                tasa_rotacion = (total_bajas / promedio) * 100
                
                return ResultadoKPI(
                    nombre="Rotación de Personal",
                    categoria=CategoriaKPI.TALENTO,
                    valor=round(tasa_rotacion, 2),
                    unidad="%",
                    tendencia="↓" if tasa_rotacion < 10 else "↑",
                    detalles={
                        'empleados_activos': total_activos,
                        'bajas_registradas': total_bajas
                    },
                    alertas=["Alta rotación" if tasa_rotacion > 20 else "Rotación normal"],
                    recomendaciones=["Revisar clima laboral" if tasa_rotacion > 15 else "Mantener políticas actuales"]
                )
            
            return ResultadoKPI(
                nombre="Rotación de Personal",
                categoria=CategoriaKPI.TALENTO,
                valor=0,
                alertas=["Módulo HR no disponible o sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Rotación de Personal",
                categoria=CategoriaKPI.TALENTO,
                valor=0,
                alertas=[f"Error o módulo HR no instalado: {str(e)}"]
            )
    
    def kpi_porcentaje_mensual_acumulado(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Porcentaje mensual y acumulado de métricas RH."""
        return ResultadoKPI(
            nombre="Porcentaje Mensual y Acumulado RH",
            categoria=CategoriaKPI.TALENTO,
            valor=0,
            alertas=["Requiere módulo HR completo"],
            recomendaciones=["Configurar métricas de RH en Odoo"]
        )
    
    def kpi_cumplimiento_pago(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Cumplimiento de pago puntual de nómina."""
        return ResultadoKPI(
            nombre="Cumplimiento de Pago Puntual",
            categoria=CategoriaKPI.TALENTO,
            valor=100,  # Asumimos 100% por defecto
            unidad="%",
            alertas=["Requiere módulo de nómina"],
            recomendaciones=["Integrar con módulo hr_payroll"]
        )
    
    def kpi_variacion_salarial(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Porcentaje de variación salarial anual."""
        return ResultadoKPI(
            nombre="Variación Salarial Anual",
            categoria=CategoriaKPI.TALENTO,
            valor=0,
            unidad="%",
            alertas=["Requiere histórico de contratos"],
            recomendaciones=["Configurar histórico salarial en hr.contract"]
        )
    
    def kpi_equidad_genero(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Equidad interna (brecha salarial por género)."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                empleados = self.conector.buscar_leer(
                    'hr.employee',
                    [('active', '=', True)],
                    ['id', 'name', 'gender', 'department_id']
                )
                
                if empleados:
                    generos = {}
                    for emp in empleados:
                        genero = emp.get('gender', 'other') or 'other'
                        if genero not in generos:
                            generos[genero] = 0
                        generos[genero] += 1
                    
                    df_genero = pd.DataFrame([
                        {'Género': k, 'Cantidad': v, 'Porcentaje': v / len(empleados) * 100}
                        for k, v in generos.items()
                    ])
                    
                    return ResultadoKPI(
                        nombre="Equidad de Género",
                        categoria=CategoriaKPI.TALENTO,
                        valor=len(empleados),
                        unidad="empleados",
                        detalles=generos,
                        datos=df_genero,
                        recomendaciones=["Para brecha salarial se requiere módulo de nómina"]
                    )
            
            return ResultadoKPI(
                nombre="Equidad de Género",
                categoria=CategoriaKPI.TALENTO,
                valor=0,
                alertas=["Sin datos de empleados"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Equidad de Género",
                categoria=CategoriaKPI.TALENTO,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    # ================================================================
    # KPIs OPERACIONES
    # ================================================================
    
    def kpi_pedidos_surtidos(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Pedidos surtidos completamente."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                # Buscar pickings completados
                filtros = [
                    ('date_done', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_done', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', '=', 'done'),
                    ('picking_type_id.code', '=', 'outgoing')
                ]
                
                pickings = self.conector.buscar_leer(
                    'stock.picking',
                    filtros,
                    ['name', 'date_done', 'state', 'partner_id']
                )
                
                total_surtidos = len(pickings) if pickings else 0
                
                return ResultadoKPI(
                    nombre="Pedidos Surtidos",
                    categoria=CategoriaKPI.OPERACIONES,
                    valor=total_surtidos,
                    unidad="pedidos",
                    periodo=f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}",
                    detalles={'pickings_completados': total_surtidos}
                )
            
            return ResultadoKPI(
                nombre="Pedidos Surtidos",
                categoria=CategoriaKPI.OPERACIONES,
                valor=0,
                alertas=["Sin conexión"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Pedidos Surtidos",
                categoria=CategoriaKPI.OPERACIONES,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_facturacion_mensual(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Facturación mensual."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=365))
                fecha_fin = config.fecha_fin or datetime.now()
                
                filtros = [
                    ('invoice_date', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('invoice_date', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', '=', 'posted'),
                    ('move_type', 'in', ['out_invoice', 'out_refund'])
                ]
                
                facturas = self.conector.buscar_leer(
                    'account.move',
                    filtros,
                    ['name', 'invoice_date', 'amount_total', 'move_type']
                )
                
                if facturas:
                    df = pd.DataFrame(facturas)
                    df['invoice_date'] = pd.to_datetime(df['invoice_date'])
                    df['mes'] = df['invoice_date'].dt.to_period('M')
                    
                    # Ajustar por notas de crédito
                    df['monto_ajustado'] = df.apply(
                        lambda x: -x['amount_total'] if x['move_type'] == 'out_refund' else x['amount_total'],
                        axis=1
                    )
                    
                    facturacion = df.groupby('mes')['monto_ajustado'].sum().reset_index()
                    facturacion.columns = ['Mes', 'Facturación']
                    
                    total = facturacion['Facturación'].sum()
                    promedio = facturacion['Facturación'].mean()
                    
                    return ResultadoKPI(
                        nombre="Facturación Mensual",
                        categoria=CategoriaKPI.OPERACIONES,
                        valor=total,
                        unidad="MXN",
                        detalles={
                            'promedio_mensual': promedio,
                            'total_facturas': len(facturas)
                        },
                        datos=facturacion
                    )
            
            return ResultadoKPI(
                nombre="Facturación Mensual",
                categoria=CategoriaKPI.OPERACIONES,
                valor=0,
                alertas=["Sin datos de facturación"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Facturación Mensual",
                categoria=CategoriaKPI.OPERACIONES,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_gasto_paqueteria(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Gasto mensual en paquetería."""
        config = config or ConfigKPI()
        
        return ResultadoKPI(
            nombre="Gasto Mensual Paquetería",
            categoria=CategoriaKPI.OPERACIONES,
            valor=0,
            unidad="MXN",
            alertas=["Requiere configuración de cuenta contable de paquetería"],
            recomendaciones=["Configurar cuenta analítica para gastos de envío"]
        )
    
    # ================================================================
    # KPIs TIENDAS
    # ================================================================
    
    def kpi_ventas_tienda(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Ventas por tienda/sucursal."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                filtros = [
                    ('date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                ordenes = self.conector.buscar_leer(
                    'pos.order',
                    filtros,
                    ['session_id', 'amount_total', 'name']
                )
                
                if ordenes:
                    # Obtener info de sesiones y tiendas
                    session_ids = list(set(
                        o['session_id'][0] for o in ordenes 
                        if o.get('session_id')
                    ))
                    
                    sesiones = self.conector.buscar_leer(
                        'pos.session',
                        [('id', 'in', session_ids)],
                        ['id', 'config_id']
                    )
                    
                    session_dict = {s['id']: s for s in sesiones}
                    
                    # Obtener configs (tiendas)
                    config_ids = list(set(
                        s['config_id'][0] for s in sesiones 
                        if s.get('config_id')
                    ))
                    
                    configs = self.conector.buscar_leer(
                        'pos.config',
                        [('id', 'in', config_ids)],
                        ['id', 'name']
                    )
                    
                    config_dict = {c['id']: c['name'] for c in configs}
                    
                    tiendas = {}
                    for orden in ordenes:
                        if orden.get('session_id'):
                            session_id = orden['session_id'][0]
                            session = session_dict.get(session_id, {})
                            if session.get('config_id'):
                                config_id = session['config_id'][0]
                                tienda_nombre = config_dict.get(config_id, 'Sin Tienda')
                                
                                if tienda_nombre not in tiendas:
                                    tiendas[tienda_nombre] = {'ventas': 0, 'ordenes': 0}
                                
                                tiendas[tienda_nombre]['ventas'] += orden.get('amount_total', 0)
                                tiendas[tienda_nombre]['ordenes'] += 1
                    
                    total = sum(t['ventas'] for t in tiendas.values())
                    
                    df_tiendas = pd.DataFrame([
                        {
                            'Tienda': k,
                            'Ventas': v['ventas'],
                            'Órdenes': v['ordenes'],
                            'Ticket Promedio': v['ventas'] / v['ordenes'] if v['ordenes'] > 0 else 0,
                            'Porcentaje': (v['ventas'] / total * 100) if total > 0 else 0
                        }
                        for k, v in sorted(tiendas.items(), key=lambda x: x[1].get('ventas', 0), reverse=True)
                    ])
                    
                    return ResultadoKPI(
                        nombre="Ventas por Tienda",
                        categoria=CategoriaKPI.TIENDAS,
                        valor=total,
                        unidad="MXN",
                        detalles={
                            'total_tiendas': len(tiendas),
                            'tienda_top': df_tiendas.iloc[0]['Tienda'] if len(df_tiendas) > 0 else 'N/A'
                        },
                        datos=df_tiendas
                    )
            
            return ResultadoKPI(
                nombre="Ventas por Tienda",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Ventas por Tienda",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_utilidad_tienda(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Utilidad por tienda."""
        config = config or ConfigKPI()
        
        return ResultadoKPI(
            nombre="Utilidad por Tienda",
            categoria=CategoriaKPI.TIENDAS,
            valor=0,
            unidad="MXN",
            alertas=["Requiere datos de costo en líneas de venta"],
            recomendaciones=["Configurar precio de costo en productos"]
        )
    
    def kpi_inventario_marcas(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Inventario desglosado por marcas."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                # Obtener stock actual
                quants = self.conector.buscar_leer(
                    'stock.quant',
                    [('quantity', '>', 0), ('location_id.usage', '=', 'internal')],
                    ['product_id', 'quantity', 'location_id']
                )
                
                if quants:
                    product_ids = list(set(q['product_id'][0] for q in quants if q.get('product_id')))
                    
                    productos = self.conector.buscar_leer(
                        'product.product',
                        [('id', 'in', product_ids)],
                        ['id', 'name', 'product_brand_id', 'list_price']
                    )
                    
                    prod_dict = {p['id']: p for p in productos}
                    
                    marcas = {}
                    for quant in quants:
                        if quant.get('product_id'):
                            prod_id = quant['product_id'][0]
                            prod = prod_dict.get(prod_id, {})
                            marca = prod.get('product_brand_id')
                            marca_nombre = marca[1] if isinstance(marca, (list, tuple)) and len(marca) > 1 else 'Sin Marca'
                            
                            if marca_nombre not in marcas:
                                marcas[marca_nombre] = {'unidades': 0, 'valor': 0}
                            
                            qty = quant.get('quantity', 0)
                            precio = prod.get('list_price', 0)
                            marcas[marca_nombre]['unidades'] += qty
                            marcas[marca_nombre]['valor'] += qty * precio
                    
                    total_unidades = sum(m['unidades'] for m in marcas.values())
                    total_valor = sum(m['valor'] for m in marcas.values())
                    
                    df_marcas = pd.DataFrame([
                        {
                            'Marca': k,
                            'Unidades': v['unidades'],
                            'Valor Inventario': v['valor'],
                            '% Unidades': (v['unidades'] / total_unidades * 100) if total_unidades > 0 else 0
                        }
                        for k, v in sorted(marcas.items(), key=lambda x: x[1].get('valor', 0), reverse=True)
                    ])
                    
                    return ResultadoKPI(
                        nombre="Inventario por Marcas",
                        categoria=CategoriaKPI.TIENDAS,
                        valor=total_valor,
                        unidad="MXN",
                        detalles={
                            'total_unidades': total_unidades,
                            'total_marcas': len(marcas)
                        },
                        datos=df_marcas
                    )
            
            return ResultadoKPI(
                nombre="Inventario por Marcas",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=["Sin datos de inventario"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Inventario por Marcas",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_mix_marca_venta(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Mix de marca en venta (proporción de ventas por marca)."""
        # Reutiliza kpi_ventas_por_marca
        resultado = self.kpi_ventas_por_marca(config)
        resultado.nombre = "Mix de Marca en Venta"
        return resultado
    
    def kpi_obsoletos(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Porcentaje de crecimiento de productos obsoletos."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                # Productos sin movimiento en 180 días
                fecha_limite = datetime.now() - timedelta(days=180)
                
                # Obtener todos los productos con stock
                quants = self.conector.buscar_leer(
                    'stock.quant',
                    [('quantity', '>', 0), ('location_id.usage', '=', 'internal')],
                    ['product_id', 'quantity']
                )
                
                if quants:
                    product_ids = list(set(q['product_id'][0] for q in quants))
                    
                    # Buscar movimientos recientes
                    moves = self.conector.buscar_leer(
                        'stock.move',
                        [
                            ('product_id', 'in', product_ids),
                            ('date', '>=', fecha_limite.strftime('%Y-%m-%d')),
                            ('state', '=', 'done')
                        ],
                        ['product_id']
                    )
                    
                    productos_con_movimiento = set(m['product_id'][0] for m in moves if m.get('product_id'))
                    productos_sin_movimiento = set(product_ids) - productos_con_movimiento
                    
                    total_productos = len(product_ids)
                    obsoletos = len(productos_sin_movimiento)
                    porcentaje = (obsoletos / total_productos * 100) if total_productos > 0 else 0
                    
                    return ResultadoKPI(
                        nombre="Productos Obsoletos",
                        categoria=CategoriaKPI.TIENDAS,
                        valor=porcentaje,
                        unidad="%",
                        tendencia="↑" if porcentaje > 10 else "→",
                        detalles={
                            'productos_obsoletos': obsoletos,
                            'total_productos': total_productos,
                            'dias_sin_movimiento': 180
                        },
                        alertas=["Alto nivel de obsoletos" if porcentaje > 20 else "Nivel aceptable"],
                        recomendaciones=["Revisar política de compras" if porcentaje > 15 else "Monitorear mensualmente"]
                    )
            
            return ResultadoKPI(
                nombre="Productos Obsoletos",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Productos Obsoletos",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_ticket_promedio(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Ticket promedio de venta."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                filtros = [
                    ('date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                ordenes = self.conector.buscar_leer(
                    'pos.order',
                    filtros,
                    ['amount_total']
                )
                
                if ordenes:
                    total_ventas = sum(o.get('amount_total', 0) for o in ordenes)
                    total_ordenes = len(ordenes)
                    ticket_promedio = total_ventas / total_ordenes if total_ordenes > 0 else 0
                    
                    return ResultadoKPI(
                        nombre="Ticket Promedio",
                        categoria=CategoriaKPI.TIENDAS,
                        valor=round(ticket_promedio, 2),
                        unidad="MXN",
                        detalles={
                            'total_ventas': total_ventas,
                            'total_ordenes': total_ordenes
                        }
                    )
            
            return ResultadoKPI(
                nombre="Ticket Promedio",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Ticket Promedio",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_articulo_ticket(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Promedio de artículos por ticket."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                filtros = [
                    ('order_id.date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('order_id.date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('order_id.state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                lineas = self.conector.buscar_leer(
                    'pos.order.line',
                    filtros,
                    ['order_id', 'qty']
                )
                
                if lineas:
                    ordenes = {}
                    for linea in lineas:
                        order_id = linea['order_id'][0] if linea.get('order_id') else None
                        if order_id:
                            if order_id not in ordenes:
                                ordenes[order_id] = 0
                            ordenes[order_id] += linea.get('qty', 0)
                    
                    total_articulos = sum(ordenes.values())
                    total_ordenes = len(ordenes)
                    promedio = total_articulos / total_ordenes if total_ordenes > 0 else 0
                    
                    return ResultadoKPI(
                        nombre="Artículos por Ticket",
                        categoria=CategoriaKPI.TIENDAS,
                        valor=round(promedio, 2),
                        unidad="artículos",
                        detalles={
                            'total_articulos': total_articulos,
                            'total_tickets': total_ordenes
                        }
                    )
            
            return ResultadoKPI(
                nombre="Artículos por Ticket",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Artículos por Ticket",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_decremento_inventario(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Decremento de inventario (mermas, pérdidas)."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                # Buscar ajustes de inventario negativos
                filtros = [
                    ('date', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', '=', 'done'),
                    ('location_dest_id.usage', '=', 'inventory')
                ]
                
                moves = self.conector.buscar_leer(
                    'stock.move',
                    filtros,
                    ['product_id', 'product_uom_qty', 'date']
                )
                
                if moves:
                    total_perdidas = sum(m.get('product_uom_qty', 0) for m in moves)
                    
                    return ResultadoKPI(
                        nombre="Decremento de Inventario",
                        categoria=CategoriaKPI.TIENDAS,
                        valor=total_perdidas,
                        unidad="unidades",
                        detalles={'movimientos_ajuste': len(moves)},
                        alertas=["Revisar mermas" if total_perdidas > 100 else "Nivel normal"]
                    )
            
            return ResultadoKPI(
                nombre="Decremento de Inventario",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=["Sin ajustes de inventario"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Decremento de Inventario",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_incidencias_financieras(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Incidencias financieras (diferencias en caja, etc.)."""
        config = config or ConfigKPI()
        
        return ResultadoKPI(
            nombre="Incidencias Financieras",
            categoria=CategoriaKPI.TIENDAS,
            valor=0,
            unidad="incidencias",
            alertas=["Requiere módulo de control de caja"],
            recomendaciones=["Configurar cierre de caja en POS"]
        )
    
    def kpi_ranking_ventas(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Ranking de ventas (dinero y piezas)."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                filtros = [
                    ('order_id.date_order', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('order_id.date_order', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('order_id.state', 'in', ['paid', 'done', 'invoiced'])
                ]
                
                lineas = self.conector.buscar_leer(
                    'pos.order.line',
                    filtros,
                    ['product_id', 'qty', 'price_subtotal']
                )
                
                if lineas:
                    productos = {}
                    for linea in lineas:
                        if linea.get('product_id'):
                            prod_id = linea['product_id'][0]
                            prod_nombre = linea['product_id'][1]
                            
                            if prod_id not in productos:
                                productos[prod_id] = {'nombre': prod_nombre, 'piezas': 0, 'dinero': 0}
                            
                            productos[prod_id]['piezas'] += linea.get('qty', 0)
                            productos[prod_id]['dinero'] += linea.get('price_subtotal', 0)
                    
                    # Top 20 por dinero
                    ranking = sorted(productos.values(), key=lambda x: x['dinero'], reverse=True)[:20]
                    
                    df_ranking = pd.DataFrame([
                        {
                            'Producto': p['nombre'],
                            'Piezas Vendidas': p['piezas'],
                            'Ventas (MXN)': p['dinero']
                        }
                        for p in ranking
                    ])
                    
                    return ResultadoKPI(
                        nombre="Ranking de Ventas",
                        categoria=CategoriaKPI.TIENDAS,
                        valor=len(productos),
                        unidad="productos",
                        detalles={'top_producto': ranking[0]['nombre'] if ranking else 'N/A'},
                        datos=df_ranking
                    )
            
            return ResultadoKPI(
                nombre="Ranking de Ventas",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Ranking de Ventas",
                categoria=CategoriaKPI.TIENDAS,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_rotacion_inventario_tienda(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Rotación de inventarios por tienda."""
        config = config or ConfigKPI()
        
        return ResultadoKPI(
            nombre="Rotación de Inventario por Tienda",
            categoria=CategoriaKPI.TIENDAS,
            valor=0,
            alertas=["Requiere cálculo complejo con histórico"],
            recomendaciones=["Configurar ubicaciones por tienda en stock"]
        )
    
    # ================================================================
    # KPIs COMPRAS
    # ================================================================
    
    def kpi_cuentas_gasto(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Reporte de cuentas de gasto, almacenaje y demoras."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                # Buscar facturas de proveedor
                filtros = [
                    ('invoice_date', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('invoice_date', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', '=', 'posted'),
                    ('move_type', '=', 'in_invoice')
                ]
                
                facturas = self.conector.buscar_leer(
                    'account.move',
                    filtros,
                    ['name', 'partner_id', 'amount_total', 'invoice_date']
                )
                
                if facturas:
                    total_gastos = sum(f.get('amount_total', 0) for f in facturas)
                    
                    return ResultadoKPI(
                        nombre="Cuentas de Gasto",
                        categoria=CategoriaKPI.COMPRAS,
                        valor=total_gastos,
                        unidad="MXN",
                        detalles={'total_facturas': len(facturas)}
                    )
            
            return ResultadoKPI(
                nombre="Cuentas de Gasto",
                categoria=CategoriaKPI.COMPRAS,
                valor=0,
                alertas=["Sin datos de gastos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Cuentas de Gasto",
                categoria=CategoriaKPI.COMPRAS,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_faltantes(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Productos faltantes (stock en cero o negativo)."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                # Productos con stock 0 o negativo
                productos = self.conector.buscar_leer(
                    'product.product',
                    [('qty_available', '<=', 0), ('type', '=', 'product')],
                    ['name', 'default_code', 'qty_available', 'categ_id']
                )
                
                if productos:
                    df_faltantes = pd.DataFrame([
                        {
                            'Producto': p['name'],
                            'Código': p.get('default_code', 'N/A'),
                            'Stock': p.get('qty_available', 0),
                            'Categoría': p.get('categ_id', [0, 'Sin categoría'])[1] if p.get('categ_id') else 'Sin categoría'
                        }
                        for p in productos[:100]  # Limitar a 100
                    ])
                    
                    return ResultadoKPI(
                        nombre="Productos Faltantes",
                        categoria=CategoriaKPI.COMPRAS,
                        valor=len(productos),
                        unidad="productos",
                        tendencia="↑" if len(productos) > 50 else "→",
                        alertas=["Revisar reabastecimiento" if len(productos) > 20 else "Nivel controlado"],
                        datos=df_faltantes
                    )
            
            return ResultadoKPI(
                nombre="Productos Faltantes",
                categoria=CategoriaKPI.COMPRAS,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Productos Faltantes",
                categoria=CategoriaKPI.COMPRAS,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_costeo_real(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Costeo contra costo real de productos."""
        config = config or ConfigKPI()
        
        return ResultadoKPI(
            nombre="Costeo vs Costo Real",
            categoria=CategoriaKPI.COMPRAS,
            valor=0,
            alertas=["Requiere módulo de costos"],
            recomendaciones=["Configurar método de costeo en productos"]
        )
    
    def kpi_comparativa_fletes(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Comparativa de costos de fletes."""
        config = config or ConfigKPI()
        
        return ResultadoKPI(
            nombre="Comparativa de Fletes",
            categoria=CategoriaKPI.COMPRAS,
            valor=0,
            unidad="MXN",
            alertas=["Requiere registro de fletes por proveedor"],
            recomendaciones=["Configurar productos de tipo servicio para fletes"]
        )
    
    def kpi_rotacion_producto(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Tablero de rotación de producto."""
        config = config or ConfigKPI()
        
        return ResultadoKPI(
            nombre="Rotación de Producto",
            categoria=CategoriaKPI.COMPRAS,
            valor=0,
            alertas=["Requiere análisis de movimientos históricos"],
            recomendaciones=["Calcular con datos de 6-12 meses"]
        )
    
    def kpi_maximos_minimos(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Máximos y mínimos de stock por tienda."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                # Buscar reglas de reordenamiento
                reglas = self.conector.buscar_leer(
                    'stock.warehouse.orderpoint',
                    [('active', '=', True)],
                    ['product_id', 'product_min_qty', 'product_max_qty', 'warehouse_id']
                )
                
                if reglas:
                    df_reglas = pd.DataFrame([
                        {
                            'Producto': r['product_id'][1] if r.get('product_id') else 'N/A',
                            'Mínimo': r.get('product_min_qty', 0),
                            'Máximo': r.get('product_max_qty', 0),
                            'Almacén': r['warehouse_id'][1] if r.get('warehouse_id') else 'N/A'
                        }
                        for r in reglas
                    ])
                    
                    return ResultadoKPI(
                        nombre="Máximos y Mínimos",
                        categoria=CategoriaKPI.COMPRAS,
                        valor=len(reglas),
                        unidad="reglas",
                        datos=df_reglas
                    )
            
            return ResultadoKPI(
                nombre="Máximos y Mínimos",
                categoria=CategoriaKPI.COMPRAS,
                valor=0,
                alertas=["Sin reglas de reordenamiento configuradas"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Máximos y Mínimos",
                categoria=CategoriaKPI.COMPRAS,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    def kpi_picking_cedis(self, config: ConfigKPI = None) -> ResultadoKPI:
        """Picking de productos CEDIS (Centro de Distribución)."""
        config = config or ConfigKPI()
        
        try:
            if self.conector and self.conector.conectado:
                fecha_inicio = config.fecha_inicio or (datetime.now() - timedelta(days=30))
                fecha_fin = config.fecha_fin or datetime.now()
                
                # Buscar pickings de salida
                filtros = [
                    ('date_done', '>=', fecha_inicio.strftime('%Y-%m-%d')),
                    ('date_done', '<=', fecha_fin.strftime('%Y-%m-%d')),
                    ('state', '=', 'done'),
                    ('picking_type_id.code', '=', 'outgoing')
                ]
                
                pickings = self.conector.buscar_leer(
                    'stock.picking',
                    filtros,
                    ['name', 'date_done', 'move_ids_without_package']
                )
                
                total_pickings = len(pickings) if pickings else 0
                
                return ResultadoKPI(
                    nombre="Picking CEDIS",
                    categoria=CategoriaKPI.COMPRAS,
                    valor=total_pickings,
                    unidad="operaciones",
                    periodo=f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
                )
            
            return ResultadoKPI(
                nombre="Picking CEDIS",
                categoria=CategoriaKPI.COMPRAS,
                valor=0,
                alertas=["Sin datos"]
            )
            
        except Exception as e:
            return ResultadoKPI(
                nombre="Picking CEDIS",
                categoria=CategoriaKPI.COMPRAS,
                valor=0,
                alertas=[f"Error: {str(e)}"]
            )
    
    # ================================================================
    # MÉTODOS AUXILIARES
    # ================================================================
    
    def analizar_kpi(self, nombre_kpi: str, config: ConfigKPI = None) -> ResultadoKPI:
        """
        Ejecuta un KPI específico por nombre.
        
        Args:
            nombre_kpi: Nombre del KPI a ejecutar
            config: Configuración opcional
            
        Returns:
            ResultadoKPI con los datos del análisis
        """
        if nombre_kpi in self.kpis_disponibles:
            return self.kpis_disponibles[nombre_kpi](config)
        else:
            return ResultadoKPI(
                nombre=nombre_kpi,
                categoria=CategoriaKPI.COMERCIAL,
                valor=0,
                alertas=[f"KPI '{nombre_kpi}' no encontrado"],
                recomendaciones=[f"KPIs disponibles: {list(self.kpis_disponibles.keys())}"]
            )
    
    def dashboard_categoria(self, categoria: CategoriaKPI, config: ConfigKPI = None) -> List[ResultadoKPI]:
        """
        Genera un dashboard completo de una categoría.
        
        Args:
            categoria: Categoría de KPIs
            config: Configuración opcional
            
        Returns:
            Lista de ResultadoKPI
        """
        resultados = []
        
        kpis_por_categoria = {
            CategoriaKPI.COMERCIAL: [
                'ventas_mensuales', 'ventas_por_canal', 'ventas_por_marca',
                'subtotal_cliente', 'clientes_atendidos', 'subtotal_vendedor',
                'crecimiento_anual'
            ],
            CategoriaKPI.TALENTO: [
                'rotacion_personal', 'equidad_genero'
            ],
            CategoriaKPI.OPERACIONES: [
                'pedidos_surtidos', 'facturacion_mensual'
            ],
            CategoriaKPI.TIENDAS: [
                'ventas_tienda', 'inventario_marcas', 'ticket_promedio',
                'articulo_ticket', 'ranking_ventas', 'obsoletos'
            ],
            CategoriaKPI.COMPRAS: [
                'cuentas_gasto', 'faltantes', 'maximos_minimos', 'picking_cedis'
            ]
        }
        
        for kpi_nombre in kpis_por_categoria.get(categoria, []):
            try:
                resultado = self.analizar_kpi(kpi_nombre, config)
                resultados.append(resultado)
            except Exception as e:
                resultados.append(ResultadoKPI(
                    nombre=kpi_nombre,
                    categoria=categoria,
                    valor=0,
                    alertas=[f"Error: {str(e)}"]
                ))
        
        return resultados


# ============================================================
# FORMATEADOR DE RESULTADOS
# ============================================================

class FormateadorKPIs:
    """Formatea los resultados de KPIs para mostrar en la interfaz."""
    
    @staticmethod
    def formatear_resultado(resultado: ResultadoKPI) -> str:
        """Formatea un ResultadoKPI a Markdown."""
        
        # Emoji de tendencia
        tendencia_emoji = {
            "↑": "📈",
            "↓": "📉",
            "→": "➡️"
        }.get(resultado.tendencia, "📊")
        
        # Formatear valor
        if isinstance(resultado.valor, (int, float)):
            if resultado.unidad == "%":
                valor_fmt = f"{resultado.valor:.2f}%"
            elif resultado.unidad == "MXN":
                valor_fmt = f"${resultado.valor:,.2f} MXN"
            else:
                valor_fmt = f"{resultado.valor:,.0f} {resultado.unidad}"
        else:
            valor_fmt = str(resultado.valor)
        
        # Construir respuesta
        md = f"## {tendencia_emoji} {resultado.nombre}\n\n"
        md += f"**Valor:** {valor_fmt}\n"
        
        if resultado.variacion_porcentual != 0:
            signo = "+" if resultado.variacion_porcentual > 0 else ""
            md += f"**Variación:** {signo}{resultado.variacion_porcentual:.2f}%\n"
        
        if resultado.periodo:
            md += f"**Período:** {resultado.periodo}\n"
        
        # Detalles
        if resultado.detalles:
            md += "\n### Detalles\n"
            for key, value in resultado.detalles.items():
                key_fmt = key.replace('_', ' ').title()
                if isinstance(value, float):
                    value_fmt = f"{value:,.2f}"
                else:
                    value_fmt = str(value)
                md += f"- **{key_fmt}:** {value_fmt}\n"
        
        # Alertas
        if resultado.alertas:
            md += "\n### Alertas\n"
            for alerta in resultado.alertas:
                md += f"- {alerta}\n"
        
        # Recomendaciones
        if resultado.recomendaciones:
            md += "\n### Recomendaciones\n"
            for rec in resultado.recomendaciones:
                md += f"- {rec}\n"
        
        # Tabla de datos
        if resultado.datos is not None and len(resultado.datos) > 0:
            md += "\n### Datos\n"
            md += resultado.datos.to_markdown(index=False)
        
        return md
    
    @staticmethod
    def formatear_dashboard(resultados, titulo: str = "Dashboard") -> str:
        """Formatea múltiples KPIs en un dashboard."""
        
        md = f"# {titulo}\n\n"
        md += f"*Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n\n"
        md += "---\n\n"
        
        # Si es un diccionario (dashboard completo)
        if isinstance(resultados, dict):
            if 'categorias' in resultados:
                for cat_name, cat_data in resultados['categorias'].items():
                    emoji = cat_data.get('emoji', '📊')
                    md += f"## {emoji} {cat_name}\n\n"
                    
                    if 'error' in cat_data:
                        md += f"Error: {cat_data['error']}\n\n"
                    else:
                        kpis = cat_data.get('kpis', [])
                        for kpi in kpis:
                            if isinstance(kpi, dict):
                                valor = kpi.get('valor', 'N/A')
                                unidad = kpi.get('unidad', '')
                                nombre = kpi.get('nombre', 'KPI')
                                tendencia = kpi.get('tendencia', '→')
                                estado = kpi.get('estado', '')
                                
                                # Formatear valor
                                if isinstance(valor, (int, float)):
                                    if unidad == '%':
                                        valor_fmt = f"{valor:.2f}%"
                                    elif unidad == 'MXN':
                                        valor_fmt = f"${valor:,.2f}"
                                    else:
                                        valor_fmt = f"{valor:,.0f} {unidad}".strip()
                                else:
                                    valor_fmt = str(valor)
                                
                                tendencia_emoji = {"↑": "📈", "↓": "📉", "→": "➡️"}.get(tendencia, "📊")
                                md += f"- {tendencia_emoji} **{nombre}:** {valor_fmt}"
                                if estado:
                                    md += f" ({estado})"
                                md += "\n"
                    
                    md += "\n---\n\n"
            return md
        
        # Si es una lista de ResultadoKPI
        if isinstance(resultados, list):
            for resultado in resultados:
                if isinstance(resultado, ResultadoKPI):
                    md += FormateadorKPIs.formatear_resultado(resultado)
                    md += "\n---\n\n"
            return md
        
        return md
    
    @staticmethod
    def formatear_categoria(categoria: CategoriaKPI, resultados: List[ResultadoKPI]) -> str:
        """Formatea los KPIs de una categoría específica."""
        
        emojis = {
            CategoriaKPI.COMERCIAL: '📈',
            CategoriaKPI.TALENTO: '👥',
            CategoriaKPI.OPERACIONES: '⚙️',
            CategoriaKPI.TIENDAS: '🏪',
            CategoriaKPI.COMPRAS: '📦'
        }
        
        emoji = emojis.get(categoria, '📊')
        md = f"# {emoji} KPIs de {categoria.value}\n\n"
        md += f"*Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n\n"
        md += "---\n\n"
        
        # Resumen rápido
        exitosos = len([r for r in resultados if not r.error])
        md += f"**Total KPIs analizados:** {len(resultados)} | **Exitosos:** {exitosos}\n\n"
        
        for resultado in resultados:
            if resultado.error:
                md += f"### {resultado.nombre}\n"
                md += f"Error: {resultado.error}\n\n"
            else:
                md += FormateadorKPIs.formatear_resultado(resultado)
            md += "\n---\n\n"
        
        return md


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

motor_kpis = MotorKPIsEmpresariales()

def set_conector_kpis(conector):
    """Establece el conector de Odoo para los KPIs."""
    motor_kpis.set_conector(conector)


# ============================================================
# EXPORTACIONES
# ============================================================

__all__ = [
    'MotorKPIsEmpresariales',
    'FormateadorKPIs',
    'ResultadoKPI',
    'ConfigKPI',
    'CategoriaKPI',
    'TipoAgrupacion',
    'motor_kpis',
    'set_conector_kpis'
]
