# ============================================================
# MOTOR NLP AVANZADO - COMPRENSIÓN INTELIGENTE
# ============================================================
# Sistema de procesamiento de lenguaje natural mejorado
# Integrado con CerebroNLP para análisis semántico profundo
# ============================================================

import re
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Normalizador de prompts para entender al usuario sin importar cómo escriba
try:
    from utils.normalizador_prompt import obtener_normalizador, NormalizadorPrompt
    NORMALIZADOR_DISPONIBLE = True
except ImportError:
    NORMALIZADOR_DISPONIBLE = False

from app.logging_config import get_logger
logger = get_logger("services.nlp.nlp_avanzado")

# Importar Cerebro NLP Inteligente
try:
    from services.nlp.cerebro_nlp import (
        CerebroNLP, 
        IntencionSmart, 
        TipoConsulta,
        NivelEspecificidad,
        obtener_cerebro_nlp
    )
    CEREBRO_DISPONIBLE = True
except ImportError:
    CEREBRO_DISPONIBLE = False
    logger.warning("CerebroNLP no disponible, usando modo básico")

# Motor de Embeddings Semánticos
try:
    from services.nlp.motor_embeddings import obtener_motor_embeddings, EMBEDDINGS_DISPONIBLE
except ImportError:
    EMBEDDINGS_DISPONIBLE = False
    obtener_motor_embeddings = None


# Intenciones BI/avanzadas que el sistema tradicional detecta bien
# y NO deben ser sobrescritas por CerebroNLP genérico
_INTENCIONES_BI_AVANZADAS = {
    'bi_dashboard', 'bi_reporte', 'bi_auditoria', 'bi_anomalias',
    'bi_riesgos', 'salud_negocio', 'estacionalidad', 'flujo_caja',
    'prediccion_ventas_inteligente', 'prediccion_inventario_inteligente',
    'score_morosos', 'dashboard_automatico', 'ventas_por_marca',
    'ventas_por_tienda', 'kpis_por_tienda', 'analisis_inteligente',
    'analisis_360', 'inventario_prediccion',
}


@dataclass
class ConsultaEntendida:
    """Representa una consulta entendida del usuario."""
    intencion_principal: str
    confianza: float
    entidades: Dict[str, Any]
    parametros: Dict[str, Any]
    temporalidad: Dict[str, str]  # fecha_inicio, fecha_fin
    modificadores: List[str]  # top, mejor, peor, etc.
    contexto: str  # original
    accion_sugerida: str
    respuesta_tipo: str  # analisis, consulta, prediccion, ayuda
    subintenciones: List[str]
    formato_solicitado: str = "auto"  # tabla, grafica, lista, resumen, auto


class MotorNLPAvanzado:
    """Motor NLP avanzado con comprensión contextual e inteligencia semántica."""
    
    def __init__(self, usar_cerebro: bool = True):
        self.historial_contexto = []
        self.ultimo_modelo = None
        self.ultimo_tema = None
        
        # Cerebro NLP inteligente (si está disponible)
        self.cerebro = None
        if usar_cerebro and CEREBRO_DISPONIBLE:
            try:
                self.cerebro = obtener_cerebro_nlp()
                print("Motor NLP con Cerebro Inteligente activado")
            except Exception as e:
                logger.error(f"Error inicializando CerebroNLP: {e}")
        
        # Patrones de entidades
        self._inicializar_patrones()
        
        # Sinónimos y variantes
        self._inicializar_sinonimos()
        
        # Intenciones expandidas
        self._inicializar_intenciones()
        
        # Motor de Embeddings Semánticos (carga lazy en background)
        self.motor_embeddings = None
        if EMBEDDINGS_DISPONIBLE and obtener_motor_embeddings:
            try:
                self.motor_embeddings = obtener_motor_embeddings(self.intenciones_map)
                if self.motor_embeddings and self.motor_embeddings.disponible:
                    print("✓ Motor de Embeddings Semánticos activado")
                else:
                    self.motor_embeddings = None
            except Exception as e:
                logger.warning(f"Embeddings no disponibles: {e}")
                self.motor_embeddings = None
    
    def _inicializar_patrones(self):
        """Inicializa patrones de reconocimiento."""
        
        # Patrones temporales
        self.patrones_tiempo = {
            'hoy': (0, 0),
            'ayer': (-1, -1),
            'anteayer': (-2, -2),
            'esta semana': ('semana_actual', None),
            'semana pasada': ('semana_pasada', None),
            'este mes': ('mes_actual', None),
            'mes pasado': ('mes_pasado', None),
            'este año': ('año_actual', None),
            'año pasado': ('año_pasado', None),
            'últimos 7 días': (-7, 0),
            'últimos 15 días': (-15, 0),
            'últimos 30 días': (-30, 0),
            'último mes': (-30, 0),
            'últimos 3 meses': (-90, 0),
            'último trimestre': (-90, 0),
            'últimos 6 meses': (-180, 0),
            'primer trimestre': ('q1', None),
            'segundo trimestre': ('q2', None),
            'tercer trimestre': ('q3', None),
            'cuarto trimestre': ('q4', None),
        }
        
        # Patrones numéricos
        self.patron_numero = re.compile(r'\b(\d+(?:,\d{3})*(?:\.\d+)?)\b')
        self.patron_top = re.compile(r'(?:top|mejores?|primeros?|principales?)\s*(\d+)?', re.IGNORECASE)
        self.patron_ultimos = re.compile(r'[uú]ltimos?\s*(\d+)\s*(d[ií]as?|semanas?|meses?)', re.IGNORECASE)
        
        # Patrones de comparación
        self.patron_vs = re.compile(r'(\w+)\s+(?:vs|versus|contra|comparado?\s+con)\s+(\w+)', re.IGNORECASE)
        self.patron_mayor = re.compile(r'(?:mayor|más|superior|encima)\s*(?:de|que|a)?\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)', re.IGNORECASE)
        self.patron_menor = re.compile(r'(?:menor|menos|inferior|debajo)\s*(?:de|que|a)?\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)', re.IGNORECASE)
        
        # Patrones de fechas específicas
        self.patron_fecha = re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})')
        self.patron_mes_año = re.compile(r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s*(?:de\s*)?(\d{4})?', re.IGNORECASE)
    
    def _inicializar_sinonimos(self):
        """Inicializa diccionario de sinónimos."""
        self.sinonimos = {
            # Ventas
            'ventas': ['ventas', 'vendido', 'venta', 'ordenes', 'pedidos', 'sales', 'facturado'],
            'pos': ['pos', 'punto de venta', 'caja', 'tickets', 'ticket', 'mostrador', 'tienda'],
            
            # Productos
            'productos': ['productos', 'artículos', 'items', 'mercancía', 'sku', 'referencias'],
            'inventario': ['inventario', 'stock', 'existencias', 'almacén', 'bodega', 'disponible'],
            
            # Finanzas
            'facturas': ['facturas', 'facturación', 'cfdi', 'comprobantes', 'invoices'],
            'cxc': ['cxc', 'cuentas por cobrar', 'cartera', 'cobranza', 'receivables', 'pendiente cobro'],
            'cxp': ['cxp', 'cuentas por pagar', 'deuda', 'payables', 'pendiente pago', 'proveedores'],
            'pagos': ['pagos', 'cobros', 'payments', 'transacciones'],
            
            # RH
            'empleados': ['empleados', 'personal', 'trabajadores', 'staff', 'equipo', 'colaboradores'],
            'nomina': ['nómina', 'nomina', 'payroll', 'salarios', 'sueldos'],
            'asistencia': ['asistencia', 'checadas', 'entradas', 'salidas', 'attendance'],
            'ausencias': ['ausencias', 'faltas', 'permisos', 'vacaciones', 'incapacidades'],
            
            # CRM
            'crm': ['crm', 'oportunidades', 'leads', 'prospectos', 'pipeline'],
            'clientes': ['clientes', 'customers', 'compradores', 'partners'],
            
            # Compras
            'compras': ['compras', 'adquisiciones', 'purchases', 'órdenes de compra'],
            'proveedores': ['proveedores', 'suppliers', 'vendors'],
            
            # Análisis
            'analisis': ['análisis', 'analisis', 'analizar', 'estudiar', 'revisar', 'evaluar', 'valorar'],
            'reporte': ['reporte', 'informe', 'report', 'excel', 'pdf', 'exportar'],
            'prediccion': ['predicción', 'prediccion', 'proyección', 'forecast', 'estimar', 'futuro'],
            'comparar': ['comparar', 'comparativa', 'versus', 'vs', 'contra', 'diferencia'],
            'tendencia': ['tendencia', 'trend', 'evolución', 'histórico', 'comportamiento'],
        }
        
        # Invertir para búsqueda rápida
        self.sinonimos_inv = {}
        for key, valores in self.sinonimos.items():
            for v in valores:
                self.sinonimos_inv[v.lower()] = key
    
    def _inicializar_intenciones(self):
        """Inicializa mapeo de intenciones."""
        self.intenciones_map = {
            # === VENTAS ===
            'ventas_basico': {
                'triggers': ['ventas', 'vendido', 'órdenes de venta', 'total ventas'],
                'modelo': 'sale.order',
                'accion': 'consultar_ventas',
                'tipo_respuesta': 'consulta'
            },
            'ventas_analisis': {
                'triggers': ['analizar ventas', 'análisis de ventas', 'como van las ventas', 'situación ventas'],
                'modelo': 'sale.order',
                'accion': 'analisis_ventas',
                'tipo_respuesta': 'analisis'
            },
            'ventas_top_productos': {
                'triggers': ['productos más vendidos', 'top productos', 'mejores productos', 'qué se vende más'],
                'modelo': 'sale.order.line',
                'accion': 'top_productos',
                'tipo_respuesta': 'ranking'
            },
            'ventas_top_clientes': {
                'triggers': ['mejores clientes', 'top clientes', 'principales clientes', 'quién compra más'],
                'modelo': 'res.partner',
                'accion': 'top_clientes',
                'tipo_respuesta': 'ranking'
            },
            'ventas_vendedor': {
                'triggers': ['ventas por vendedor', 'ranking vendedores', 'comisiones', 'productividad'],
                'modelo': 'sale.order',
                'accion': 'ventas_vendedor',
                'tipo_respuesta': 'ranking'
            },
            'ventas_tendencia': {
                'triggers': ['tendencia ventas', 'evolución ventas', 'histórico ventas', 'cómo van'],
                'modelo': 'sale.order',
                'accion': 'tendencia',
                'tipo_respuesta': 'tendencia'
            },
            'ventas_prediccion': {
                'triggers': ['predecir ventas', 'proyección ventas', 'forecast ventas', 'cuánto venderemos'],
                'modelo': 'sale.order',
                'accion': 'predecir_ventas',
                'tipo_respuesta': 'prediccion'
            },
            'ventas_comparativa': {
                'triggers': ['comparar ventas', 'hoy vs ayer', 'este mes vs', 'variación'],
                'modelo': 'sale.order',
                'accion': 'comparar_periodos',
                'tipo_respuesta': 'comparativa'
            },
            
            # === POS ===
            'pos_basico': {
                'triggers': ['pos', 'tickets', 'punto de venta', 'caja'],
                'modelo': 'pos.order',
                'accion': 'consultar_pos',
                'tipo_respuesta': 'consulta'
            },
            'pos_analisis': {
                'triggers': ['análisis pos', 'analizar pos', 'cómo va la caja'],
                'modelo': 'pos.order',
                'accion': 'analisis_pos',
                'tipo_respuesta': 'analisis'
            },
            'pos_metodos_pago': {
                'triggers': ['métodos de pago', 'formas de pago', 'efectivo tarjeta', 'cómo pagan'],
                'modelo': 'pos.payment',
                'accion': 'metodos_pago',
                'tipo_respuesta': 'desglose'
            },
            'pos_sesiones': {
                'triggers': ['sesiones', 'arqueo', 'corte de caja', 'cierre'],
                'modelo': 'pos.session',
                'accion': 'sesiones_pos',
                'tipo_respuesta': 'lista'
            },
            
            # === FACTURACIÓN ===
            'facturas_basico': {
                'triggers': ['facturas', 'facturación', 'cfdi', 'comprobantes'],
                'modelo': 'account.move',
                'accion': 'consultar_facturas',
                'tipo_respuesta': 'consulta'
            },
            'facturas_analisis': {
                'triggers': ['análisis facturación', 'revenue', 'ingresos facturados'],
                'modelo': 'account.move',
                'accion': 'analisis_facturacion',
                'tipo_respuesta': 'analisis'
            },
            'cxc': {
                'triggers': ['cuentas por cobrar', 'cxc', 'cartera', 'pendiente cobro', 'deudores'],
                'modelo': 'account.move',
                'accion': 'cuentas_por_cobrar',
                'tipo_respuesta': 'cartera'
            },
            'cxp': {
                'triggers': ['cuentas por pagar', 'cxp', 'deudas', 'pendiente pago', 'acreedores'],
                'modelo': 'account.move',
                'accion': 'cuentas_por_pagar',
                'tipo_respuesta': 'cartera'
            },
            
            # === INVENTARIO ===
            'inventario_basico': {
                'triggers': ['inventario', 'stock', 'existencias', 'qué hay'],
                'modelo': 'stock.quant',
                'accion': 'consultar_inventario',
                'tipo_respuesta': 'consulta'
            },
            'inventario_analisis': {
                'triggers': ['análisis inventario', 'estado del stock', 'salud inventario'],
                'modelo': 'stock.quant',
                'accion': 'analisis_inventario',
                'tipo_respuesta': 'analisis'
            },
            'inventario_critico': {
                'triggers': ['productos agotados', 'sin stock', 'faltantes', 'cero inventario'],
                'modelo': 'stock.quant',
                'accion': 'productos_sin_stock',
                'tipo_respuesta': 'alerta'
            },
            'inventario_rotacion': {
                'triggers': ['rotación', 'movimiento inventario', 'productos lentos', 'días inventario'],
                'modelo': 'stock.quant',
                'accion': 'rotacion_inventario',
                'tipo_respuesta': 'analisis'
            },
            'inventario_valoracion': {
                'triggers': ['valor inventario', 'valoración', 'cuánto vale el stock'],
                'modelo': 'stock.quant',
                'accion': 'valoracion_inventario',
                'tipo_respuesta': 'resumen'
            },
            'inventario_prediccion': {
                'triggers': ['cuándo se agota', 'se van a agotar', 'agotar', 'productos que faltan', 'qué se agota', 'predicción stock', 'alerta inventario', 'reorder'],
                'modelo': 'stock.quant',
                'accion': 'predecir_agotamiento',
                'tipo_respuesta': 'prediccion'
            },
            
            # === COMPRAS ===
            'compras_basico': {
                'triggers': ['compras', 'órdenes de compra', 'pedidos proveedor'],
                'modelo': 'purchase.order',
                'accion': 'consultar_compras',
                'tipo_respuesta': 'consulta'
            },
            'compras_analisis': {
                'triggers': ['análisis compras', 'gasto proveedores', 'costos'],
                'modelo': 'purchase.order',
                'accion': 'analisis_compras',
                'tipo_respuesta': 'analisis'
            },
            'compras_proveedores': {
                'triggers': ['top proveedores', 'principales proveedores', 'a quién compramos'],
                'modelo': 'purchase.order',
                'accion': 'top_proveedores',
                'tipo_respuesta': 'ranking'
            },
            
            # === RH ===
            'rh_empleados': {
                'triggers': ['empleados', 'personal', 'headcount', 'plantilla'],
                'modelo': 'hr.employee',
                'accion': 'consultar_empleados',
                'tipo_respuesta': 'consulta'
            },
            'rh_departamentos': {
                'triggers': ['por departamento', 'áreas', 'organigrama'],
                'modelo': 'hr.department',
                'accion': 'departamentos',
                'tipo_respuesta': 'desglose'
            },
            'rh_asistencia': {
                'triggers': ['asistencia', 'checadas', 'puntualidad', 'retardos'],
                'modelo': 'hr.attendance',
                'accion': 'asistencia',
                'tipo_respuesta': 'analisis'
            },
            'rh_ausencias': {
                'triggers': ['ausencias', 'faltas', 'vacaciones', 'permisos', 'incapacidades'],
                'modelo': 'hr.leave',
                'accion': 'ausencias',
                'tipo_respuesta': 'analisis'
            },
            'rh_nomina': {
                'triggers': ['nómina', 'payroll', 'salarios', 'sueldos'],
                'modelo': 'hr.payslip',
                'accion': 'nomina',
                'tipo_respuesta': 'analisis'
            },
            'rh_contratos': {
                'triggers': ['contratos', 'vencimientos', 'renovaciones'],
                'modelo': 'hr.contract',
                'accion': 'contratos',
                'tipo_respuesta': 'alerta'
            },
            
            # === CRM ===
            'crm_pipeline': {
                'triggers': ['crm', 'oportunidades', 'leads', 'pipeline', 'prospectos'],
                'modelo': 'crm.lead',
                'accion': 'analisis_crm',
                'tipo_respuesta': 'analisis'
            },
            
            # === USUARIOS ===
            'usuarios': {
                'triggers': ['usuarios', 'sistema', 'accesos', 'logins'],
                'modelo': 'res.users',
                'accion': 'consultar_usuarios',
                'tipo_respuesta': 'consulta'
            },
            
            # === PREDICCIONES ===
            'prediccion_general': {
                'triggers': ['predicción', 'proyección', 'forecast', 'qué pasará', 'futuro'],
                'modelo': None,
                'accion': 'predecir',
                'tipo_respuesta': 'prediccion'
            },
            'flujo_caja': {
                'triggers': ['flujo de caja', 'cash flow', 'liquidez', 'efectivo',
                            'predice el flujo', 'predicción de caja', 'proyección de caja',
                            'flujo caja', 'predecir flujo', 'flujo proyectado',
                            'predice flujo de caja'],
                'modelo': 'account.move',
                'accion': 'flujo_caja',
                'tipo_respuesta': 'prediccion'
            },
            'salud_negocio': {
                'triggers': ['salud del negocio', 'score', 'diagnóstico', 'cómo estamos'],
                'modelo': None,
                'accion': 'salud_negocio',
                'tipo_respuesta': 'score'
            },
            'estacionalidad': {
                'triggers': ['estacionalidad', 'patrones', 'mejores días', 'temporadas'],
                'modelo': 'sale.order',
                'accion': 'estacionalidad',
                'tipo_respuesta': 'analisis'
            },
            
            # === REPORTES ===
            'reporte_excel': {
                'triggers': ['excel', 'exportar excel', 'descargar datos', 'xlsx'],
                'modelo': None,
                'accion': 'generar_excel',
                'tipo_respuesta': 'reporte'
            },
            'reporte_pdf': {
                'triggers': ['pdf', 'exportar pdf', 'imprimir'],
                'modelo': None,
                'accion': 'generar_pdf',
                'tipo_respuesta': 'reporte'
            },
            'pdf_contextual': {
                'triggers': ['esos datos en pdf', 'esto en pdf', 'generame eso en pdf',
                            'lo anterior en pdf', 'pasalo a pdf', 'sacame el pdf',
                            'hazme un pdf', 'convierte a pdf', 'pdf de esto',
                            'exporta esto', 'pdf profesional'],
                'modelo': None,
                'accion': 'generar_pdf_profesional',
                'tipo_respuesta': 'reporte'
            },
            
            # === SISTEMA ===
            'ayuda': {
                'triggers': ['ayuda', 'help', 'qué puedes', 'cómo funciona', 'comandos',
                           'qué sabes', 'que sabes', 'qué conoces', 'que conoces',
                           'qué puedes hacer', 'que puedes hacer', 'para qué sirves',
                           'para que sirves', 'cuéntame de ti', 'cuentame de ti',
                           'qué eres', 'que eres', 'quién eres', 'quien eres'],
                'modelo': None,
                'accion': 'ayuda',
                'tipo_respuesta': 'ayuda'
            },
            'info_odoo': {
                'triggers': ['qué sabes de odoo', 'que sabes de odoo', 'sobre odoo',
                           'acerca de odoo', 'información de odoo', 'info odoo',
                           'cómo funciona odoo', 'como funciona odoo', 'qué es odoo',
                           'que es odoo', 'manual de odoo', 'documentación odoo'],
                'modelo': None,
                'accion': 'consultar_manual',
                'tipo_respuesta': 'manual'
            },
            'conexion': {
                'triggers': ['conexión', 'servidor', 'status', 'conectado'],
                'modelo': None,
                'accion': 'info_conexion',
                'tipo_respuesta': 'info'
            },
            
            # === BUSINESS INTELLIGENCE EXPERTO ===
            'bi_reporte': {
                'triggers': ['reporte bi', 'business intelligence', 'reporte ejecutivo', 'análisis bi'],
                'modelo': None,
                'accion': 'reporte_bi',
                'tipo_respuesta': 'reporte_bi'
            },
            'bi_auditoria': {
                'triggers': ['auditoría', 'fraude', 'auditoría fraude', 'detectar fraude', 'riesgos fraude'],
                'modelo': None,
                'accion': 'auditoria_fraude',
                'tipo_respuesta': 'auditoria'
            },
            'bi_dashboard': {
                'triggers': ['dashboard', 'kpis', 'indicadores', 'métricas', 'tablero'],
                'modelo': None,
                'accion': 'dashboard_kpis',
                'tipo_respuesta': 'dashboard'
            },
            'kpis_por_tienda': {
                'triggers': ['indicadores de tiendas', 'kpis por tienda', 'indicadores por tienda',
                            'indicadores tiendas', 'dashboard tiendas', 'rendimiento tiendas',
                            'resultados por tienda', 'comparativa tiendas', 'kpis tiendas',
                            'métricas por tienda', 'performance tiendas'],
                'modelo': 'pos.order',
                'accion': 'kpis_por_tienda',
                'tipo_respuesta': 'dashboard'
            },
            'bi_anomalias': {
                'triggers': ['anomalías', 'irregularidades', 'patrones sospechosos', 'detectar anomalías'],
                'modelo': None,
                'accion': 'detectar_anomalias',
                'tipo_respuesta': 'anomalias'
            },
            'bi_riesgos': {
                'triggers': ['análisis de riesgos', 'riesgos financieros', 'evaluar riesgos', 'score riesgo'],
                'modelo': None,
                'accion': 'analisis_riesgos',
                'tipo_respuesta': 'riesgos'
            },
            
            # === CONSULTAS ESPECIALIZADAS (CEREBRO ANDROMEDA) ===
            'reporte_ejecutivo_completo': {
                'triggers': ['reporte ejecutivo completo', 'reporte total', 'reporte general', 'resumen ejecutivo'],
                'modelo': None,
                'accion': 'reporte_ejecutivo',
                'tipo_respuesta': 'reporte_ejecutivo'
            },
            'ventas_especializado': {
                'triggers': ['análisis completo ventas', 'ventas completas', 'ventas especializado', 'análisis profundo ventas'],
                'modelo': 'sale.order',
                'accion': 'ventas_completo',
                'tipo_respuesta': 'analisis'
            },
            'ventas_empresa': {
                'triggers': ['ventas por empresa', 'ventas compañía', 'ventas por compañía', 'por empresa'],
                'modelo': 'sale.order',
                'accion': 'ventas_por_empresa',
                'tipo_respuesta': 'analisis'
            },
            'inventario_almacen': {
                'triggers': ['inventario por almacén', 'inventario por tienda', 'stock por almacén', 
                           'existencias por tienda', 'por almacén', 'por sucursal'],
                'modelo': 'stock.quant',
                'accion': 'inventario_por_tienda',
                'tipo_respuesta': 'inventario'
            },
            'productos_criticos_avanzado': {
                'triggers': ['productos críticos', 'stock crítico', 'por agotarse', 'urgencia inventario',
                           'productos agotados', 'sin stock'],
                'modelo': 'stock.quant',
                'accion': 'productos_criticos',
                'tipo_respuesta': 'inventario'
            },
            'rotacion_avanzada': {
                'triggers': ['rotación avanzada', 'análisis rotación', 'abc inventario', 'clasificación abc',
                           'rotación completa', 'análisis abc'],
                'modelo': 'stock.quant',
                'accion': 'rotacion_inventario_avanzado',
                'tipo_respuesta': 'analisis'
            },
            'cxc_especializado': {
                'triggers': ['cxc completo', 'cartera clientes', 'cuentas cobrar análisis', 'deudores completo',
                           'cartera vencida detalle', 'análisis cxc'],
                'modelo': 'account.move',
                'accion': 'cxc_analisis',
                'tipo_respuesta': 'finanzas'
            },
            'cxp_especializado': {
                'triggers': ['cxp completo', 'cuentas pagar análisis', 'proveedores por pagar',
                           'pasivos detalle', 'análisis cxp'],
                'modelo': 'account.move',
                'accion': 'cxp_analisis',
                'tipo_respuesta': 'finanzas'
            },
            'pos_especializado': {
                'triggers': ['pos completo', 'punto venta análisis', 'análisis pos', 'tickets análisis',
                           'tpv completo', 'ventas mostrador'],
                'modelo': 'pos.order',
                'accion': 'pos_completo',
                'tipo_respuesta': 'pos'
            },
            'comparativa_ventas': {
                'triggers': ['comparar ventas', 'comparativa períodos', 'vs mes anterior', 'vs año anterior',
                           'comparar período', 'variación ventas'],
                'modelo': 'sale.order',
                'accion': 'comparativa_periodos',
                'tipo_respuesta': 'comparativa'
            },
            'clientes_especializado': {
                'triggers': ['análisis clientes', 'clientes completo', 'cartera clientes análisis',
                           'segmentación clientes', 'top clientes análisis'],
                'modelo': 'res.partner',
                'accion': 'clientes_analisis',
                'tipo_respuesta': 'analisis'
            },
            'empresas_sistema': {
                'triggers': ['empresas sistema', 'compañías odoo', 'multiempresa', 'todas las empresas',
                           'resumen empresas'],
                'modelo': 'res.company',
                'accion': 'empresas_resumen',
                'tipo_respuesta': 'analisis'
            },
            
            # === PREDICCIÓN INTELIGENTE ===
            'prediccion_ventas_inteligente': {
                'triggers': ['predicción ventas inteligente', 'forecast ventas', 'proyección inteligente',
                           'predecir ventas detallado', 'predicción avanzada ventas', 'analizar tendencia ventas',
                           'predicción de ventas', 'predecir ventas', 'pronóstico ventas', 'proyección ventas',
                           'cuánto venderemos', 'prediccion ventas', 'ventas futuras', 'tendencia ventas'],
                'modelo': 'sale.order',
                'accion': 'prediccion_ventas_inteligente',
                'tipo_respuesta': 'prediccion'
            },
            'prediccion_inventario_inteligente': {
                'triggers': ['predicción inventario', 'forecast inventario', 'recomendaciones reposición',
                           'qué productos reponer', 'sugerencias stock', 'reposición inteligente',
                           'inventario por ubicación', 'stock por ubicación', 'inventario ubicación',
                           'stock crítico', 'productos a reponer', 'alertas inventario'],
                'modelo': 'stock.quant',
                'accion': 'prediccion_inventario_inteligente',
                'tipo_respuesta': 'prediccion'
            },
            'score_morosos': {
                'triggers': ['score morosos', 'clientes morosos', 'análisis morosidad', 'deudores riesgo',
                           'cartera morosa', 'quién debe más', 'clientes que no pagan', 'riesgo cobranza'],
                'modelo': 'account.move',
                'accion': 'score_morosos',
                'tipo_respuesta': 'finanzas'
            },
            'dashboard_automatico': {
                'triggers': ['dashboard automático', 'tablero completo', 'resumen total', 'estado negocio',
                           'dashboard inteligente', 'panorama completo', 'visión general negocio'],
                'modelo': None,
                'accion': 'dashboard_automatico',
                'tipo_respuesta': 'dashboard'
            },
            
            # === ANÁLISIS INTELIGENTE (NUEVO) ===
            'ventas_por_tienda': {
                'triggers': ['ventas por tienda', 'ventas por sucursal', 'ventas tiendas', 'ventas sucursales',
                           'de tiendas', 'por punto de venta', 'ventas por local'],
                'modelo': 'pos.order',
                'accion': 'ventas_por_tienda',
                'tipo_respuesta': 'analisis'
            },
            'ventas_por_marca': {
                'triggers': ['ventas por marca', 'ventas marcas', 'por fabricante', 'ventas brand',
                           'cuánto vende cada marca', 'marcas vendidas'],
                'modelo': 'sale.order.line',
                'accion': 'ventas_por_marca',
                'tipo_respuesta': 'analisis'
            },
            'comparar_periodos_especificos': {
                'triggers': ['enero vs', 'febrero vs', 'marzo vs', 'abril vs', 'mayo vs', 'junio vs',
                           'julio vs', 'agosto vs', 'septiembre vs', 'octubre vs', 'noviembre vs', 
                           'diciembre vs', 'vs enero', 'vs febrero', 'vs marzo', 'vs abril', 'vs mayo',
                           'vs junio', 'vs julio', 'vs agosto', 'vs septiembre', 'vs octubre', 'vs noviembre',
                           'vs diciembre', '2024 vs 2025', '2025 vs 2026', 'comparar enero', 'comparar febrero',
                           'comparativa enero', 'comparativa febrero', 'vs 2024', 'vs 2025', 'vs 2026'],
                'modelo': 'sale.order',
                'accion': 'comparar_periodos_especificos',
                'tipo_respuesta': 'comparativa'
            },
            'inventario_por_ubicacion': {
                'triggers': ['inventario por ubicación', 'inventario ubicación', 'stock por ubicación',
                           'por location_id', 'location id', 'existencias ubicación', 'inventario location'],
                'modelo': 'stock.quant',
                'accion': 'inventario_por_ubicacion',
                'tipo_respuesta': 'inventario'
            },
            'inventario_por_almacen_nuevo': {
                'triggers': ['inventario por almacén', 'inventario almacén', 'stock por almacén',
                           'inventario por bodega', 'existencias por almacén', 'inventory warehouse'],
                'modelo': 'stock.quant',
                'accion': 'inventario_por_almacen',
                'tipo_respuesta': 'inventario'
            },
            'analisis_inteligente': {
                'triggers': ['análisis inteligente', 'análisis completo', 'analiza esto', 'que opinas de',
                           'dame análisis', 'analizar todo', 'análisis general'],
                'modelo': None,
                'accion': 'analisis_inteligente',
                'tipo_respuesta': 'analisis'
            },
            
            # === ANÁLISIS 360° ===
            'analisis_360': {
                'triggers': ['cómo va', 'como va', 'cómo está', 'como está', 'qué tal', 'que tal',
                           'cómo le va', 'como le va', 'cómo anda', 'como anda', 'dame info de',
                           'todo sobre', '360', 'análisis completo de', 'reporte de marca',
                           'análisis de la marca', 'cómo vamos con'],
                'modelo': None,
                'accion': 'analisis_360',
                'tipo_respuesta': 'analisis_360'
            },
            'ventas_mensuales_marca': {
                'triggers': ['ventas mensuales por marca', 'ventas por marca mensual', 
                           'ventas mensuales marca', 'mensual por marca', 'marcas mensual',
                           'evolución ventas marca', 'tendencia ventas marca'],
                'modelo': 'sale.order.line',
                'accion': 'ventas_mensuales_marca',
                'tipo_respuesta': 'analisis'
            },
            
            # === MACHINE LEARNING ===
            'prediccion_ml': {
                'triggers': ['predecir ventas', 'predicción ml', 'prediccion ml', 'forecast ventas',
                           'proyección ventas', 'pronosticar', 'machine learning', 'random forest',
                           'predice ventas', 'cuánto venderemos', 'estimación ventas',
                           'predicción inteligente', 'proyecta ventas'],
                'modelo': None,
                'accion': 'prediccion_ml',
                'tipo_respuesta': 'prediccion_ml'
            },
            'segmentacion_clientes': {
                'triggers': ['segmentar clientes', 'segmentación', 'clasificar clientes', 'tipos de clientes',
                           'rfm', 'clusters clientes', 'agrupar clientes', 'segmentos',
                           'categorizar clientes', 'perfiles de clientes'],
                'modelo': None,
                'accion': 'segmentacion_clientes',
                'tipo_respuesta': 'segmentacion'
            },
            'anomalias_ml': {
                'triggers': ['detectar anomalías', 'anomalías', 'datos atípicos', 'outliers',
                           'comportamiento anormal', 'detectar irregularidades', 'días raros',
                           'ventas anormales', 'picos extraños'],
                'modelo': None,
                'accion': 'anomalias_ml',
                'tipo_respuesta': 'anomalias'
            },
            'tendencias_ml': {
                'triggers': ['analizar tendencias', 'tendencias ml', 'patrones de ventas',
                           'tendencia general', 'análisis tendencias', 'hacia dónde van las ventas',
                           'tendencia de', 'como van las ventas en general'],
                'modelo': None,
                'accion': 'tendencias_ml',
                'tipo_respuesta': 'tendencias'
            },
            
            # === LSTM NEURAL NETWORK ===
            'prediccion_lstm': {
                'triggers': ['lstm', 'red neuronal', 'neural network', 'deep learning',
                           'pytorch', 'predicción lstm', 'prediccion neuronal',
                           'predicción avanzada', 'prediccion avanzada', 'usa lstm',
                           'con redes neuronales', 'predicción profunda'],
                'modelo': None,
                'accion': 'prediccion_lstm',
                'tipo_respuesta': 'prediccion_lstm'
            },
            
            # === KPIS EMPRESARIALES ===
            'dashboard_kpis_empresariales': {
                'triggers': ['dashboard kpis', 'dashboard empresarial', 'todos los kpis',
                           'kpis completos', 'indicadores empresariales', 'panel kpis',
                           'resumen kpis', 'kpis generales'],
                'modelo': None,
                'accion': 'dashboard_kpis_empresariales',
                'tipo_respuesta': 'dashboard'
            },
            'kpis_comerciales': {
                'triggers': ['kpis comerciales', 'indicadores comerciales', 'kpis de ventas',
                           'métricas comerciales', 'indicadores de venta', 'performance comercial',
                           'ventas por canal', 'ventas por marca', 'ticket promedio'],
                'modelo': None,
                'accion': 'kpis_comerciales',
                'tipo_respuesta': 'kpis'
            },
            'kpis_talento': {
                'triggers': ['kpis talento', 'kpis recursos humanos', 'indicadores rh',
                           'kpis empleados', 'métricas personal', 'plantilla', 'headcount',
                           'rotación personal', 'ausentismo', 'productividad empleados'],
                'modelo': None,
                'accion': 'kpis_talento',
                'tipo_respuesta': 'kpis'
            },
            'kpis_operaciones': {
                'triggers': ['kpis operaciones', 'indicadores operativos', 'métricas operativas',
                           'eficiencia operativa', 'picking', 'cedis', 'logística',
                           'tiempos entrega', 'almacén operaciones'],
                'modelo': None,
                'accion': 'kpis_operaciones',
                'tipo_respuesta': 'kpis'
            },
            'kpis_tiendas': {
                'triggers': ['kpis tiendas', 'indicadores tienda', 'métricas tiendas',
                           'performance tiendas', 'rendimiento tiendas', 'sucursales',
                           'ventas por tienda', 'conversión tienda', 'venta por m2'],
                'modelo': None,
                'accion': 'kpis_tiendas',
                'tipo_respuesta': 'kpis'
            },
            'kpis_compras': {
                'triggers': ['kpis compras', 'indicadores compras', 'métricas compras',
                           'performance compras', 'lead time', 'fill rate', 'proveedores',
                           'tiempo entrega proveedor', 'cumplimiento proveedores'],
                'modelo': None,
                'accion': 'kpis_compras',
                'tipo_respuesta': 'kpis'
            },
            # KPIs específicos
            'kpi_ventas_canal': {
                'triggers': ['ventas por canal', 'canales de venta', 'canal de ventas'],
                'modelo': None,
                'accion': 'kpi_ventas_por_canal',
                'tipo_respuesta': 'kpi'
            },
            'kpi_ventas_marca': {
                'triggers': ['ventas por marca', 'marca más vendida', 'ranking marcas'],
                'modelo': None,
                'accion': 'kpi_ventas_por_marca',
                'tipo_respuesta': 'kpi'
            },
            'kpi_ticket_promedio': {
                'triggers': ['ticket promedio', 'ticket medio', 'venta promedio', 'promedio por ticket'],
                'modelo': None,
                'accion': 'kpi_ticket_promedio',
                'tipo_respuesta': 'kpi'
            },
            'kpi_rotacion_inventario': {
                'triggers': ['rotación inventario', 'rotacion stock', 'días inventario',
                           'vueltas inventario', 'inventario rotación'],
                'modelo': None,
                'accion': 'kpi_rotacion_inventario',
                'tipo_respuesta': 'kpi'
            },
            'kpi_faltantes': {
                'triggers': ['faltantes', 'productos agotados', 'sin stock', 'stockout',
                           'desabasto', 'quiebre stock'],
                'modelo': None,
                'accion': 'kpi_faltantes',
                'tipo_respuesta': 'kpi'
            },
            'kpi_picking': {
                'triggers': ['picking', 'preparación pedidos', 'surtido', 'picking cedis'],
                'modelo': None,
                'accion': 'kpi_picking_cedis',
                'tipo_respuesta': 'kpi'
            },
            
            # === MANUAL DE ODOO / BASE DE CONOCIMIENTO ===
            'consultar_manual': {
                'triggers': ['cómo se hace', 'como se hace', 'cómo hago', 'como hago',
                           'cómo puedo', 'como puedo', 'dónde está', 'donde esta',
                           'manual', 'tutorial', 'pasos para', 'procedimiento',
                           'cómo crear', 'como crear', 'cómo hacer', 'como hacer',
                           'ayuda con', 'explícame', 'explicame', 'cómo funciona',
                           'como funciona', 'cómo uso', 'como uso', 'guía', 'guia',
                           'instrucciones', 'paso a paso', 'cómo abro', 'como abro',
                           'cómo registro', 'como registro', 'cómo cancelo', 'como cancelo'],
                'modelo': None,
                'accion': 'consultar_manual',
                'tipo_respuesta': 'manual'
            },
            'manual_facturacion': {
                'triggers': ['facturar en odoo', 'hacer factura', 'crear factura', 
                           'timbrar factura', 'cfdi', 'facturación odoo',
                           'cómo facturo', 'como facturo', 'emitir factura'],
                'modelo': None,
                'accion': 'consultar_manual',
                'tipo_respuesta': 'manual'
            },
            'manual_pos': {
                'triggers': ['usar punto de venta', 'abrir caja', 'cerrar caja',
                           'corte caja', 'vender en pos', 'cobrar en caja',
                           'ticket pos', 'nuevo ticket', 'arqueo'],
                'modelo': None,
                'accion': 'consultar_manual',
                'tipo_respuesta': 'manual'
            },
            'manual_inventario': {
                'triggers': ['hacer traspaso', 'solicitar traspaso', 'kardex odoo',
                           'ajuste inventario', 'etiquetas odoo', 'imprimir etiquetas',
                           'inventario cierre', 'cierre de mes', 'cierre mes', 'fin de mes',
                           'cómo hacer inventario', 'como hacer inventario',
                           'cómo se hace inventario', 'como se hace inventario',
                           'hacer inventario', 'hacer el inventario', 'sacar inventario',
                           'sacar el inventario', 'inventario de fin', 'inventario de cierre',
                           'inventario físico', 'inventario fisico',
                           'toma de inventario', 'toma física', 'toma fisica',
                           'conteo de inventario', 'conteo físico', 'conteo fisico',
                           'cómo cuento inventario', 'como cuento inventario'],
                'modelo': None,
                'accion': 'consultar_manual',
                'tipo_respuesta': 'manual'
            },
            'manual_compras': {
                'triggers': ['crear compra', 'orden compra', 'recibir mercancía',
                           'recepción compra', 'dar entrada', 'alta producto'],
                'modelo': None,
                'accion': 'consultar_manual',
                'tipo_respuesta': 'manual'
            },
            'manual_devoluciones': {
                'triggers': ['hacer devolución', 'devolución cliente', 'nota crédito',
                           'devolver producto', 'reembolso', 'cancelar venta'],
                'modelo': None,
                'accion': 'consultar_manual',
                'tipo_respuesta': 'manual'
            },
            
            # === AUDITORÍA INTELIGENTE ===
            'auditoria_nocturna': {
                'triggers': ['auditoría nocturna', 'auditoria nocturna', 'auditoría completa', 
                           'auditoría base de datos', 'revisar base de datos', 'chequeo nocturno',
                           'revisión nocturna', 'audit completo', 'auditar sistema'],
                'modelo': None,
                'accion': 'auditoria_nocturna',
                'tipo_respuesta': 'auditoria'
            },
            'semaforo_salud': {
                'triggers': ['semáforo salud', 'semaforo salud', 'semáforo operativo', 'estado operativo',
                           'dashboard semáforo', 'semáforo de salud', 'semaforo de salud', 'indicadores semáforo',
                           'salud operativa', 'estado general del negocio', 'semaforo'],
                'modelo': None,
                'accion': 'semaforo_salud',
                'tipo_respuesta': 'dashboard'
            },
            'detectar_pagos_fantasma': {
                'triggers': ['pagos fantasma', 'pagos fantasmas', 'movimientos sospechosos',
                           'facturas pagadas sin flujo', 'pagos sin caja', 'pagos irregulares',
                           'detectar pagos fantasma', 'pagos falsos'],
                'modelo': None,
                'accion': 'detectar_pagos_fantasma',
                'tipo_respuesta': 'auditoria'
            },
            'analizar_churn': {
                'triggers': ['churn clientes', 'churn de clientes', 'abandono clientes', 'abandono de clientes',
                           'riesgo churn', 'clientes perdidos', 'clientes que van a dejar', 
                           'deserción clientes', 'fuga de clientes', 'clientes en riesgo', 
                           'análisis churn', 'riesgo de abandono', 'analizar churn', 'predicción churn'],
                'modelo': None,
                'accion': 'analizar_churn',
                'tipo_respuesta': 'prediccion'
            },
            'reposicion_jit': {
                'triggers': ['reposición jit', 'reposicion jit', 'just in time', 'reposición justo a tiempo',
                           'qué reponer', 'productos a reponer', 'reposición inventario',
                           'calcular reposición', 'sugerir compras', 'pedido óptimo'],
                'modelo': None,
                'accion': 'reposicion_jit',
                'tipo_respuesta': 'inventario'
            },
            'stock_lento': {
                'triggers': ['stock lento', 'inventario lento', 'productos lentos', 'stock muerto',
                           'inventario muerto', 'sin rotación', 'productos sin venta',
                           'ventas muertas', 'productos estancados', 'inventario sin movimiento'],
                'modelo': None,
                'accion': 'stock_lento',
                'tipo_respuesta': 'inventario'
            },
            'clientes_olvidados': {
                'triggers': ['clientes olvidados', 'clientes inactivos', 'clientes dormidos',
                           'clientes que dejaron de comprar', 'clientes sin actividad',
                           'reactivar clientes', 'clientes perdidos'],
                'modelo': None,
                'accion': 'clientes_olvidados',
                'tipo_respuesta': 'analisis'
            },
            'diferencias_centavos': {
                'triggers': ['diferencias centavos', 'diferencias de centavos', 'residuales',
                           'facturas con centavos', 'diferencias pequeñas', 'ajustes menores',
                           'centavos pendientes', 'residuos facturas'],
                'modelo': None,
                'accion': 'diferencias_centavos',
                'tipo_respuesta': 'auditoria'
            },
            'diagnosticar_error': {
                'triggers': ['diagnosticar error', 'diagnóstico error', 'error odoo', 'problema odoo',
                           'no puedo facturar', 'error al guardar', 'error sistema',
                           'me sale error', 'falla al', 'no funciona'],
                'modelo': None,
                'accion': 'diagnosticar_error',
                'tipo_respuesta': 'diagnostico'
            },
            'generar_reporte_auditoria': {
                'triggers': ['reporte auditoría pdf', 'pdf auditoría', 'generar reporte auditoría',
                           'exportar auditoría', 'imprimir auditoría', 'reporte acción correctiva'],
                'modelo': None,
                'accion': 'generar_reporte_auditoria',
                'tipo_respuesta': 'reporte'
            },
            'auditoria_calidad_datos': {
                'triggers': ['auditoría calidad', 'auditoria calidad', 'calidad de datos',
                           'calidad datos', 'datos basura', 'datos incompletos',
                           'procesos huérfanos', 'procesos huerfanos', 'registros zombi',
                           'registros zombie', 'incoherencias', 'inconsistencias datos',
                           'triple validación', 'triple validacion', 'auditoría de calidad de datos',
                           'auditoria de calidad de datos', 'datos confiables', 'incertidumbre datos',
                           'procesos inconclusos', 'errores datos', 'limpieza datos',
                           'estado vs vinculo', 'sla datos', 'datos zombi'],
                'modelo': None,
                'accion': 'auditoria_calidad_datos',
                'tipo_respuesta': 'auditoria'
            },
        }

        # Integrar patrones regex de INTENCIONES_EXTENDIDAS (v2)
        self._integrar_intenciones_extendidas()

    def _integrar_intenciones_extendidas(self):
        """
        Integra INTENCIONES_EXTENDIDAS al motor NLP:
        - Compila sus patrones regex en self.patrones_extendidos (ordenados por prioridad)
        - Agrega a intenciones_map las acciones no definidas aún, para que el lookup de
          tipo_respuesta y modelo funcione cuando se resuelva la intención.
        """
        try:
            from utils.intenciones_extendidas import INTENCIONES_EXTENDIDAS
        except ImportError:
            self.patrones_extendidos = []
            return

        self.patrones_extendidos = []

        for nombre, config in INTENCIONES_EXTENDIDAS.items():
            accion = config.get('accion', nombre)
            prioridad = config.get('prioridad', 5)
            patrones_compilados = []
            for p in config.get('patrones', []):
                try:
                    patrones_compilados.append(re.compile(p, re.IGNORECASE))
                except re.error:
                    pass

            if patrones_compilados:
                self.patrones_extendidos.append({
                    'nombre': nombre,
                    'accion': accion,
                    'prioridad': prioridad,
                    'patrones': patrones_compilados,
                })

            # Agregar a intenciones_map si la acción aún no está mapeada
            if nombre not in self.intenciones_map:
                self.intenciones_map[nombre] = {
                    'triggers': [],
                    'modelo': None,
                    'accion': accion,
                    'tipo_respuesta': 'analisis',
                }

        # Ordenar de mayor a menor prioridad para que las más específicas ganen primero
        self.patrones_extendidos.sort(key=lambda x: x['prioridad'], reverse=True)
        logger.debug(f"INTENCIONES_EXTENDIDAS integradas: {len(self.patrones_extendidos)} grupos de patrones")

    def entender(self, mensaje: str) -> ConsultaEntendida:
        """
        Entiende un mensaje del usuario con análisis semántico inteligente.
        
        Usa el CerebroNLP para análisis profundo y luego mapea a acciones.
        Pre-normaliza el input para tolerar typos, abreviaciones y coloquialismos.
        """
        # =====================================================
        # PRE-NORMALIZACIÓN DEL PROMPT
        # =====================================================
        mensaje_normalizado = mensaje
        if NORMALIZADOR_DISPONIBLE:
            try:
                norm = obtener_normalizador()
                resultado_norm = norm.normalizar(mensaje)
                mensaje_normalizado = resultado_norm.texto_normalizado
            except Exception:
                mensaje_normalizado = mensaje

        mensaje_lower = mensaje_normalizado.lower().strip()
        
        # =====================================================
        # ANÁLISIS INTELIGENTE CON CEREBRONLP
        # =====================================================
        intencion_cerebro = None
        if self.cerebro:
            try:
                intencion_cerebro = self.cerebro.analizar(mensaje)
            except Exception as e:
                logger.error(f"Error en CerebroNLP: {e}")
        
        # =====================================================
        # ANÁLISIS TRADICIONAL (como fallback y complemento)
        # =====================================================
        
        # 1. Detectar intención principal (método tradicional)
        intencion_trad, confianza_trad = self._detectar_intencion(mensaje_lower)
        
        # 2. Extraer entidades
        entidades = self._extraer_entidades(mensaje_lower)
        
        # 3. Extraer temporalidad
        temporalidad = self._extraer_temporalidad(mensaje, mensaje_lower)
        
        # 4. Extraer parámetros y modificadores
        parametros = self._extraer_parametros(mensaje_lower)
        modificadores = self._extraer_modificadores(mensaje_lower)
        
        # 5. Detectar subintenciones
        subintenciones = self._detectar_subintenciones(mensaje_lower, intencion_trad)
        
        # =====================================================
        # FUSIÓN INTELIGENTE DE RESULTADOS
        # =====================================================
        
        # Intenciones de auditoría que tienen prioridad absoluta
        intenciones_auditoria = [
            'auditoria_nocturna', 'semaforo_salud', 'detectar_pagos_fantasma',
            'analizar_churn', 'reposicion_jit', 'stock_lento', 'clientes_olvidados',
            'diferencias_centavos', 'diagnosticar_error', 'generar_reporte_auditoria',
            'auditoria_calidad_datos'
        ]
        
        # Intenciones de manual que tienen prioridad sobre el CerebroNLP
        intenciones_manual = [
            'consultar_manual', 'manual_facturacion', 'manual_pos', 
            'manual_inventario', 'manual_compras', 'manual_devoluciones',
            'info_odoo', 'ayuda'
        ]
        
        # Si la intención tradicional es de auditoría, darle prioridad absoluta
        if intencion_trad in intenciones_auditoria and confianza_trad > 0.3:
            intencion_final = intencion_trad
            confianza = max(confianza_trad, 0.85)  # Alta confianza para auditoría
        # Si la intención tradicional es de manual, darle prioridad sobre CerebroNLP
        elif intencion_trad in intenciones_manual and confianza_trad > 0.5:
            intencion_final = intencion_trad
            confianza = max(confianza_trad, 0.85)  # Alta confianza para manual
        # BI/avanzado: el sistema tradicional tiene triggers específicos
        elif intencion_trad in _INTENCIONES_BI_AVANZADAS and confianza_trad > 0.4:
            intencion_final = intencion_trad
            confianza = max(confianza_trad, 0.75)
        elif intencion_cerebro and intencion_cerebro.confianza > 0.55:
            # Cerebro con alta confianza Y supera al tradicional
            if confianza_trad > 0.5 and intencion_trad != 'consulta_general':
                # Tradicional tiene buena detección — preferir si cerebro no es claramente mejor
                if intencion_cerebro.confianza > confianza_trad + 0.1:
                    # Cerebro significativamente más seguro → usar cerebro
                    accion_cerebro = intencion_cerebro.accion_principal
                    intencion_final = self._mapear_accion_a_intencion(accion_cerebro)
                    confianza = intencion_cerebro.confianza
                else:
                    # Tradicional es competitivo → preferir tradicional
                    intencion_final = intencion_trad
                    confianza = confianza_trad
            else:
                # Tradicional débil → usar cerebro
                accion_cerebro = intencion_cerebro.accion_principal
                intencion_final = self._mapear_accion_a_intencion(accion_cerebro)
                confianza = intencion_cerebro.confianza
            
            # Enriquecer parámetros con entidades del cerebro
            if intencion_cerebro.entidades:
                entidades_cerebro = intencion_cerebro.entidades
                for ent in entidades_cerebro:
                    if ent.tipo == 'periodo' and 'periodo' not in parametros:
                        parametros['periodo'] = ent.valor
                    elif ent.tipo == 'ranking':
                        parametros['limite'] = ent.valor
                    elif ent.tipo == 'tienda':
                        parametros['tienda'] = ent.valor
                    elif ent.tipo == 'periodo_mes':
                        parametros['mes'] = ent.valor.get('mes')
                        parametros['año'] = ent.valor.get('año')
                    elif ent.tipo == 'horizonte':
                        parametros['limite'] = ent.valor
                    elif ent.tipo == 'periodo_prediccion' and isinstance(ent.valor, dict):
                        parametros['limite'] = ent.valor.get('dias', 30)
                        parametros['mes_prediccion'] = ent.valor.get('mes')
                        parametros['año_prediccion'] = ent.valor.get('año')
                entidades['_cerebro'] = entidades_cerebro
            
            # Actualizar temporalidad si el cerebro la detectó
            if intencion_cerebro.parametros.get('periodo'):
                periodo_cerebro = intencion_cerebro.parametros['periodo']
                if isinstance(periodo_cerebro, dict):
                    nuevas_fechas = self._convertir_periodo_a_fechas(periodo_cerebro)
                    if nuevas_fechas:
                        temporalidad.update(nuevas_fechas)
        else:
            # Usar análisis tradicional
            intencion_final = intencion_trad
            confianza = confianza_trad
        
        # =====================================================
        # DETERMINAR ACCIÓN FINAL
        # =====================================================
        
        # Buscar configuración de la intención
        config_intencion = self.intenciones_map.get(intencion_final, {})
        accion = config_intencion.get('accion', 'consulta_general')
        tipo_respuesta = config_intencion.get('tipo_respuesta', 'consulta')
        
        # Acciones de auditoría que NO deben ser sobrescritas
        acciones_auditoria = [
            'auditoria_nocturna', 'semaforo_salud', 'detectar_pagos_fantasma',
            'analizar_churn', 'reposicion_jit', 'stock_lento', 'clientes_olvidados',
            'diferencias_centavos', 'diagnosticar_error', 'generar_reporte_auditoria',
            'auditoria_calidad_datos'
        ]
        
        # Acciones de manual que NO deben ser sobrescritas
        acciones_manual = ['consultar_manual', 'ayuda']
        
        # Acciones BI/avanzadas que NO deben ser sobrescritas
        acciones_bi = [
            'dashboard_kpis', 'salud_negocio', 'estacionalidad', 'reporte_bi',
            'auditoria_fraude', 'detectar_anomalias', 'analisis_riesgos',
            'flujo_caja', 'predecir_ventas', 'prediccion_ventas_inteligente',
            'ventas_por_marca', 'ventas_por_tienda', 'predecir_agotamiento',
            'analisis_inteligente', 'analisis_360',
        ]
        
        # Acciones protegidas (no sobrescribir con CerebroNLP)
        acciones_protegidas = acciones_auditoria + acciones_manual + acciones_bi
        
        # Si el cerebro tiene acción específica, usarla (excepto para acciones protegidas)
        # Condición adicional: solo sobrescribir si la confianza del cerebro supera
        # a la del análisis tradicional, evitando que CerebroNLP descarte detecciones
        # de alta confianza como las que vienen de INTENCIONES_EXTENDIDAS (0.92).
        if (intencion_cerebro
                and intencion_cerebro.confianza > 0.6
                and accion not in acciones_protegidas
                and intencion_cerebro.confianza > confianza + 0.1):
            accion = intencion_cerebro.accion_principal
            
            # Mapear tipo de consulta a tipo de respuesta
            tipo_map = {
                'CONSULTA_DATOS': 'consulta',
                'ANALISIS': 'analisis',
                'COMPARATIVA': 'comparativa',
                'PREDICCION': 'prediccion',
                'REPORTE': 'reporte',
                'MANUAL': 'manual',
                'AYUDA': 'ayuda',
                'CONVERSACIONAL': 'chat'
            }
            tipo_respuesta = tipo_map.get(
                intencion_cerebro.tipo_consulta.name, 
                tipo_respuesta
            )
        
        # =====================================================
        # AJUSTE POR CONTEXTO CONVERSACIONAL
        # =====================================================
        
        if self.ultimo_tema and confianza < 0.4:
            # Confianza muy baja - usar contexto anterior
            intencion_final = self.ultimo_tema
            config_intencion = self.intenciones_map.get(intencion_final, {})
            accion = config_intencion.get('accion', 'consulta_general')
            confianza = 0.5  # Confianza media por contexto
        
        # =====================================================
        # ACTUALIZAR CONTEXTO PARA PRÓXIMAS CONSULTAS
        # =====================================================
        
        self.historial_contexto.append({
            'mensaje': mensaje,
            'intencion': intencion_final,
            'accion': accion,
            'confianza': confianza,
            'cerebro_usado': intencion_cerebro is not None,
            'timestamp': datetime.now().isoformat()
        })
        
        # Solo actualizar tema si hay buena confianza
        if confianza > 0.5:
            self.ultimo_tema = intencion_final
            self.ultimo_modelo = config_intencion.get('modelo')
        
        # Limitar historial
        if len(self.historial_contexto) > 20:
            self.historial_contexto = self.historial_contexto[-20:]
        
        return ConsultaEntendida(
            intencion_principal=intencion_final,
            confianza=confianza,
            entidades=entidades,
            parametros=parametros,
            temporalidad=temporalidad,
            modificadores=modificadores,
            contexto=mensaje,
            accion_sugerida=accion,
            respuesta_tipo=tipo_respuesta,
            subintenciones=subintenciones,
            formato_solicitado=parametros.get('formato', 'auto'),
        )
    
    def _detectar_intencion(self, mensaje: str) -> Tuple[str, float]:
        """Detecta la intención principal del mensaje con análisis robusto."""
        mejor_match = None
        mejor_score = 0
        
        # Intenciones que deben tener prioridad (más específicas)
        intenciones_prioritarias = [
            'auditoria_nocturna', 'semaforo_salud', 'detectar_pagos_fantasma',
            'analizar_churn', 'reposicion_jit', 'stock_lento', 'clientes_olvidados',
            'diferencias_centavos', 'diagnosticar_error', 'generar_reporte_auditoria',
            'auditoria_calidad_datos'
        ]
        
        mensaje_lower = mensaje.lower()

        # ═══════════════════════════════════════════════════════════
        # CLASIFICACIÓN INTELIGENTE DE "CÓMO" (DATOS vs MANUAL)
        # ═══════════════════════════════════════════════════════════
        es_pregunta_como = any(mensaje_lower.startswith(p) for p in [
            'cómo', 'como', 'cómo se', 'como se', 'cómo hago', 'como hago',
            'cómo hacer', 'como hacer', 'cómo puedo', 'como puedo',
            'pasos para', 'procedimiento para', 'guía para', 'guia para'
        ])
        
        es_pregunta_que = any(mensaje_lower.startswith(p) for p in [
            'qué sabes', 'que sabes', 'qué conoces', 'que conoces',
            'qué es', 'que es', 'qué puedes', 'que puedes'
        ])
        
        if es_pregunta_como:
            # Usar normalizador para clasificar correctamente
            tipo_como = 'ambiguo'
            if NORMALIZADOR_DISPONIBLE:
                try:
                    norm = obtener_normalizador()
                    tipo_como = norm.clasificar_tipo_como(mensaje_lower)
                except Exception:
                    tipo_como = 'ambiguo'

            if tipo_como == 'ambiguo':
                # Heurística rápida: si tiene palabras de datos, es datos
                palabras_datos = {'ventas', 'venta', 'inventario', 'stock', 'facturas',
                                  'clientes', 'productos', 'compras', 'empleados', 'pos',
                                  'tickets', 'marca', 'marcas', 'tienda', 'sucursal',
                                  'tendencia', 'predicción', 'prediccion', 'ingresos'}
                if any(pd in mensaje_lower for pd in palabras_datos):
                    tipo_como = 'datos'
                else:
                    tipo_como = 'manual'

            if tipo_como == 'datos':
                # NO buscar en manual; dejar que el flujo normal detecte la intención
                pass
            elif tipo_como == 'manual':
                # Buscar en intenciones de manual
                intenciones_manual = ['consultar_manual', 'manual_facturacion', 'manual_pos', 
                                     'manual_inventario', 'manual_compras', 'manual_devoluciones',
                                     'info_odoo', 'ayuda']
                for nombre in intenciones_manual:
                    config = self.intenciones_map.get(nombre, {})
                    triggers = config.get('triggers', [])
                    for trigger in triggers:
                        if trigger.lower() in mensaje_lower:
                            score = len(trigger) / len(mensaje) if len(mensaje) > 0 else 0
                            score += 0.6
                            if score > mejor_score:
                                mejor_score = score
                                mejor_match = nombre
                if mejor_score > 0.25:
                    return (mejor_match, min(mejor_score + 0.3, 1.0))

        elif es_pregunta_que:
            # Las preguntas "qué" van a ayuda/info (no a datos)
            intenciones_info = ['info_odoo', 'ayuda']
            for nombre in intenciones_info:
                config = self.intenciones_map.get(nombre, {})
                triggers = config.get('triggers', [])
                for trigger in triggers:
                    if trigger.lower() in mensaje_lower:
                        score = len(trigger) / len(mensaje) if len(mensaje) > 0 else 0
                        score += 0.6
                        if score > mejor_score:
                            mejor_score = score
                            mejor_match = nombre
            if mejor_score > 0.25:
                return (mejor_match, min(mejor_score + 0.3, 1.0))

        # ═══════════════════════════════════════════════════════════
        # PRIORIDAD 0.5: Patrones regex de INTENCIONES_EXTENDIDAS
        # Se evalúan antes que los triggers simples para capturar
        # acciones v2 específicas (inventario_obsoleto, brecha_salarial, etc.)
        # ═══════════════════════════════════════════════════════════
        if hasattr(self, 'patrones_extendidos') and self.patrones_extendidos:
            for item in self.patrones_extendidos:
                for patron in item['patrones']:
                    if patron.search(mensaje_lower):
                        return (item['nombre'], 0.92)

        # ═══════════════════════════════════════════════════════════
        # PRIORIDAD 1: Intenciones de auditoría
        # ═══════════════════════════════════════════════════════════
        for nombre in intenciones_prioritarias:
            config = self.intenciones_map.get(nombre, {})
            triggers = config.get('triggers', [])
            for trigger in triggers:
                if trigger.lower() in mensaje:
                    score = len(trigger) / len(mensaje) if len(mensaje) > 0 else 0
                    score += 0.5  # Bonus por ser prioritaria
                    if score > mejor_score:
                        mejor_score = score
                        mejor_match = nombre
        
        if mejor_score > 0.3:
            return (mejor_match, min(mejor_score + 0.3, 1.0))
        
        # ═══════════════════════════════════════════════════════════
        # PRIORIDAD 2: Matching exacto de triggers (con word boundary)
        # ═══════════════════════════════════════════════════════════
        for nombre, config in self.intenciones_map.items():
            triggers = config.get('triggers', [])
            for trigger in triggers:
                trigger_lower = trigger.lower()
                if trigger_lower in mensaje:
                    # Verificar word boundary para evitar "venta" en "inventario"
                    if len(trigger_lower) <= 4:
                        # Triggers cortos requieren word boundary
                        if not re.search(r'\b' + re.escape(trigger_lower) + r'\b', mensaje):
                            continue
                    score = len(trigger_lower) / len(mensaje) if len(mensaje) > 0 else 0
                    score += 0.3 if mensaje.startswith(trigger_lower) else 0
                    
                    if score > mejor_score:
                        mejor_score = score
                        mejor_match = nombre
        
        # ═══════════════════════════════════════════════════════════
        # PRIORIDAD 3: Sinónimos como fallback
        # NO ejecutar si P2 ya identificó una intención BI avanzada
        # (ej: "análisis 360" no debe sobreescribirse con "ventas_analisis")
        # ═══════════════════════════════════════════════════════════
        if mejor_score < 0.3 and mejor_match not in _INTENCIONES_BI_AVANZADAS:
            for palabra in mensaje.split():
                categoria = self.sinonimos_inv.get(palabra)
                if categoria:
                    for nombre, config in self.intenciones_map.items():
                        if categoria in nombre or categoria in str(config.get('triggers', [])):
                            # No sobreescribir una intención específica con una genérica
                            if nombre in _INTENCIONES_BI_AVANZADAS and mejor_match not in _INTENCIONES_BI_AVANZADAS:
                                pass  # Preferir la específica
                            mejor_match = nombre
                            mejor_score = 0.5
                            break
        
        # ═══════════════════════════════════════════════════════════
        # PRIORIDAD 4: Fuzzy matching (cuando todo lo demás falla)
        # ═══════════════════════════════════════════════════════════
        if mejor_score < 0.3:
            fuzzy_match, fuzzy_score = self._detectar_intencion_fuzzy(mensaje)
            if fuzzy_score > mejor_score:
                mejor_match = fuzzy_match
                mejor_score = fuzzy_score
        
        # ═══════════════════════════════════════════════════════════
        # PRIORIDAD 5: Embeddings semánticos — árbitro final
        # ═══════════════════════════════════════════════════════════
        if self.motor_embeddings:
            emb_intencion, emb_score, emb_top5 = self.motor_embeddings.detectar_intencion(mensaje)
            
            if emb_intencion:
                if mejor_score < 0.3 and emb_score >= 0.45:
                    # Keyword no encontró nada confiable → usar embeddings
                    mejor_match = emb_intencion
                    mejor_score = emb_score
                elif mejor_match and emb_intencion == mejor_match and emb_score >= 0.4:
                    # Ambos coinciden → bonus de confianza
                    mejor_score = min(mejor_score + 0.15, 1.0)
                elif emb_score > mejor_score + 0.2 and emb_score >= 0.55:
                    # Embeddings mucho más seguro → preferir embeddings
                    mejor_match = emb_intencion
                    mejor_score = emb_score
        
        return (mejor_match or 'consulta_general', min(mejor_score + 0.3, 1.0))

    def _detectar_intencion_fuzzy(self, mensaje: str) -> Tuple[str, float]:
        """Detecta intención por similitud de tokens cuando la detección exacta falla."""
        palabras_msg = set(mensaje.lower().split())
        mejor_match = None
        mejor_score = 0.0

        for nombre, config in self.intenciones_map.items():
            triggers = config.get('triggers', [])
            for trigger in triggers:
                palabras_trigger = set(trigger.lower().split())
                if not palabras_trigger:
                    continue

                # Overlap de tokens (Jaccard parcial)
                comunes = palabras_msg & palabras_trigger
                if comunes:
                    score = len(comunes) / len(palabras_trigger)
                    # Bonus si más del 50% de las palabras del trigger coinciden
                    if score >= 0.5:
                        score = min(score * 0.7, 0.85)  # Cap para no superar match exacto
                        if score > mejor_score:
                            mejor_score = score
                            mejor_match = nombre

        return (mejor_match, mejor_score)
    
    def _mapear_accion_a_intencion(self, accion: str) -> str:
        """Mapea una acción del CerebroNLP a una intención del sistema."""
        
        # Mapeo directo de acciones a intenciones
        mapeo = {
            'consultar_ventas': 'ventas_basico',
            'analisis_ventas': 'ventas_analisis',
            'top_productos': 'ventas_top_productos',
            'top_clientes': 'ventas_top_clientes',
            'comparar_periodos': 'comparativa_ventas',
            'predecir_ventas': 'prediccion_ventas_inteligente',
            'ventas_por_tienda': 'ventas_por_tienda',
            'ventas_tienda_especifica': 'ventas_tienda_especifica',
            
            'consultar_pos': 'pos_basico',
            'analisis_pos': 'pos_analisis',
            
            'consultar_inventario': 'inventario_basico',
            'productos_criticos': 'inventario_critico',
            'predecir_inventario': 'prediccion_inventario_inteligente',
            
            'consultar_clientes': 'clientes_basico',
            'analisis_clientes': 'clientes_especializado',
            
            'consultar_facturas': 'facturas_basico',
            'cuentas_por_cobrar': 'cxc',
            'cuentas_por_pagar': 'cxp',
            'score_morosos': 'score_morosos',
            
            'dashboard_kpis': 'bi_dashboard',
            'kpis_por_tienda': 'kpis_por_tienda',
            'flujo_caja': 'flujo_caja',
            'facturas_filtradas': 'facturas_basico',
            'generar_pdf_profesional': 'pdf_contextual',
            'consultar_manual': 'manual_odoo',
            'mostrar_ayuda': 'ayuda',
            'responder_saludo': 'saludo',
            
            # Nuevas acciones conversacionales
            'responder_despedida': 'despedida',
            'responder_agradecimiento': 'agradecimiento',
            'contar_chiste': 'chiste',
            'mostrar_capacidades': 'capacidades',
            
            # Auditoría Inteligente
            'auditoria_nocturna': 'auditoria_nocturna',
            'semaforo_salud': 'semaforo_salud',
            'detectar_pagos_fantasma': 'detectar_pagos_fantasma',
            'analizar_churn': 'analizar_churn',
            'reposicion_jit': 'reposicion_jit',
            'stock_lento': 'stock_lento',
            'clientes_olvidados': 'clientes_olvidados',
            'diferencias_centavos': 'diferencias_centavos',
            'diagnosticar_error': 'diagnosticar_error',
            'generar_reporte_auditoria': 'generar_reporte_auditoria',
            'auditoria_calidad_datos': 'auditoria_calidad_datos',
        }
        
        # Retornar la intención mapeada o buscar por similitud
        if accion in mapeo:
            return mapeo[accion]
        
        # Buscar intención que contenga la acción
        for nombre_int, config in self.intenciones_map.items():
            if config.get('accion') == accion:
                return nombre_int
        
        # Fallback
        return 'consulta_general'
    
    def _convertir_periodo_a_fechas(self, periodo: Dict) -> Optional[Dict[str, str]]:
        """Convierte un período del CerebroNLP a fechas de inicio y fin."""
        
        hoy = datetime.now()
        resultado = {}
        
        try:
            tipo = periodo.get('tipo', '')
            
            if tipo == 'dia':
                dias = periodo.get('dias', 0)
                fecha = hoy + timedelta(days=dias)
                resultado['fecha_inicio'] = fecha.strftime('%Y-%m-%d')
                resultado['fecha_fin'] = fecha.strftime('%Y-%m-%d')
                
            elif tipo == 'rango':
                dias = periodo.get('dias', 0)
                meses = periodo.get('meses', 0)
                if dias:
                    inicio = hoy + timedelta(days=dias)
                else:
                    # Aproximar meses a días
                    inicio = hoy + timedelta(days=meses * 30)
                resultado['fecha_inicio'] = inicio.strftime('%Y-%m-%d')
                resultado['fecha_fin'] = hoy.strftime('%Y-%m-%d')
                
            elif tipo == 'mes_actual':
                inicio = hoy.replace(day=1)
                resultado['fecha_inicio'] = inicio.strftime('%Y-%m-%d')
                resultado['fecha_fin'] = hoy.strftime('%Y-%m-%d')
                
            elif tipo == 'mes_anterior':
                fin_mes_ant = hoy.replace(day=1) - timedelta(days=1)
                inicio_mes_ant = fin_mes_ant.replace(day=1)
                resultado['fecha_inicio'] = inicio_mes_ant.strftime('%Y-%m-%d')
                resultado['fecha_fin'] = fin_mes_ant.strftime('%Y-%m-%d')
                
            elif tipo == 'semana_actual':
                inicio = hoy - timedelta(days=hoy.weekday())
                resultado['fecha_inicio'] = inicio.strftime('%Y-%m-%d')
                resultado['fecha_fin'] = hoy.strftime('%Y-%m-%d')
                
            elif tipo == 'semana_anterior':
                inicio = hoy - timedelta(days=hoy.weekday() + 7)
                fin = inicio + timedelta(days=6)
                resultado['fecha_inicio'] = inicio.strftime('%Y-%m-%d')
                resultado['fecha_fin'] = fin.strftime('%Y-%m-%d')
                
            elif tipo == 'año_actual':
                inicio = hoy.replace(month=1, day=1)
                resultado['fecha_inicio'] = inicio.strftime('%Y-%m-%d')
                resultado['fecha_fin'] = hoy.strftime('%Y-%m-%d')
                
            elif tipo == 'año_anterior':
                año_ant = hoy.year - 1
                resultado['fecha_inicio'] = f'{año_ant}-01-01'
                resultado['fecha_fin'] = f'{año_ant}-12-31'
            
            return resultado if resultado else None
            
        except Exception as e:
            logger.error(f"Error convirtiendo período: {e}")
            return None
    
    def _extraer_entidades(self, mensaje: str) -> Dict[str, Any]:
        """Extrae entidades nombradas del mensaje."""
        entidades = {
            'productos': [],
            'clientes': [],
            'proveedores': [],
            'empleados': [],
            'categorias': [],
            'montos': [],
            'cantidades': []
        }
        
        # Extraer montos ($1,234.56)
        patron_monto = re.compile(r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)')
        montos = patron_monto.findall(mensaje)
        for m in montos:
            try:
                valor = float(m.replace(',', ''))
                entidades['montos'].append(valor)
            except Exception:
                pass
        
        # Extraer cantidades (sin $)
        patron_cant = re.compile(r'\b(\d+)\s*(?:unidades?|piezas?|items?|productos?)\b', re.IGNORECASE)
        for match in patron_cant.finditer(mensaje):
            entidades['cantidades'].append(int(match.group(1)))
        
        return entidades
    
    def _extraer_temporalidad(self, mensaje: str, mensaje_lower: str) -> Dict[str, str]:
        """Extrae información temporal del mensaje."""
        hoy = datetime.now()
        fecha_inicio = hoy.strftime('%Y-%m-%d')
        fecha_fin = hoy.strftime('%Y-%m-%d')
        periodo_desc = 'hoy'
        
        # Buscar patrones de tiempo
        for patron, valor in self.patrones_tiempo.items():
            if patron in mensaje_lower:
                if isinstance(valor[0], int):
                    # Días relativos
                    fecha_inicio = (hoy + timedelta(days=valor[0])).strftime('%Y-%m-%d')
                    if valor[1] is not None:
                        fecha_fin = (hoy + timedelta(days=valor[1])).strftime('%Y-%m-%d')
                elif valor[0] == 'semana_actual':
                    inicio = hoy - timedelta(days=hoy.weekday())
                    fecha_inicio = inicio.strftime('%Y-%m-%d')
                elif valor[0] == 'semana_pasada':
                    inicio = hoy - timedelta(days=hoy.weekday() + 7)
                    fin = inicio + timedelta(days=6)
                    fecha_inicio = inicio.strftime('%Y-%m-%d')
                    fecha_fin = fin.strftime('%Y-%m-%d')
                elif valor[0] == 'mes_actual':
                    fecha_inicio = hoy.replace(day=1).strftime('%Y-%m-%d')
                elif valor[0] == 'mes_pasado':
                    primer_mes = hoy.replace(day=1)
                    ultimo_ant = primer_mes - timedelta(days=1)
                    fecha_inicio = ultimo_ant.replace(day=1).strftime('%Y-%m-%d')
                    fecha_fin = ultimo_ant.strftime('%Y-%m-%d')
                elif valor[0] == 'año_actual':
                    fecha_inicio = hoy.replace(month=1, day=1).strftime('%Y-%m-%d')
                    
                periodo_desc = patron
                break
        
        # Buscar "últimos X días/semanas/meses"
        match = self.patron_ultimos.search(mensaje)
        if match:
            cantidad = int(match.group(1))
            unidad = match.group(2).lower()
            
            if 'día' in unidad or 'dia' in unidad:
                fecha_inicio = (hoy - timedelta(days=cantidad)).strftime('%Y-%m-%d')
            elif 'semana' in unidad:
                fecha_inicio = (hoy - timedelta(weeks=cantidad)).strftime('%Y-%m-%d')
            elif 'mes' in unidad:
                fecha_inicio = (hoy - timedelta(days=cantidad * 30)).strftime('%Y-%m-%d')
            
            periodo_desc = f'últimos {cantidad} {unidad}'
        
        # Buscar fechas específicas (dd/mm/yyyy)
        match = self.patron_fecha.search(mensaje)
        if match:
            dia, mes_num, año = match.groups()
            if len(año) == 2:
                año = '20' + año
            try:
                fecha = datetime(int(año), int(mes_num), int(dia))
                fecha_inicio = fecha_fin = fecha.strftime('%Y-%m-%d')
                periodo_desc = f'{dia}/{mes_num}/{año}'
            except Exception:
                pass
        
        # Buscar año específico ("año 2025", "todo el año 2025", "2025")
        # Primero buscar rangos de años "2025 y 2026" o "2025 a 2026"
        patron_rango_anios = re.compile(r'(?:a[ñn]os?\s+)?(\d{4})\s*(?:y|a|al|hasta)\s*(\d{4})', re.IGNORECASE)
        match_rango = patron_rango_anios.search(mensaje_lower)
        if match_rango:
            año_inicio = int(match_rango.group(1))
            año_fin = int(match_rango.group(2))
            # Asegurar orden correcto
            if año_fin < año_inicio:
                año_inicio, año_fin = año_fin, año_inicio
            
            fecha_inicio = f"{año_inicio}-01-01"
            fecha_fin = f"{año_fin}-12-31"
            periodo_desc = f"Años {año_inicio}-{año_fin}"
        else:
            # Buscar año único "año 2025", "todo 2025", "2025"
            patron_anio = re.compile(r'(?:todo\s+)?(?:el\s+)?(?:a[ñn]o\s+)?(\d{4})', re.IGNORECASE)
            match_anio = patron_anio.search(mensaje_lower)
            if match_anio:
                año_encontrado = int(match_anio.group(1))
                # Solo aplicar si es un año válido (entre 2000 y 2100)
                if 2000 <= año_encontrado <= 2100:
                    fecha_inicio = f"{año_encontrado}-01-01"
                    fecha_fin = f"{año_encontrado}-12-31"
                    periodo_desc = f"Año {año_encontrado}"
        
        # Buscar mes específico ("diciembre 2024", "enero 2025", etc.)
        meses_nombres = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        match_mes = self.patron_mes_año.search(mensaje_lower)
        if match_mes:
            nombre_mes = match_mes.group(1).lower()
            año_match = match_mes.group(2)
            
            mes_num = meses_nombres.get(nombre_mes, 1)
            año_num = int(año_match) if año_match else hoy.year
            
            # Si el mes es futuro y no se especificó año, asumir año anterior
            if not año_match and mes_num > hoy.month:
                año_num = hoy.year - 1
            
            # Calcular primer y último día del mes
            primer_dia = datetime(año_num, mes_num, 1)
            if mes_num == 12:
                ultimo_dia = datetime(año_num + 1, 1, 1) - timedelta(days=1)
            else:
                ultimo_dia = datetime(año_num, mes_num + 1, 1) - timedelta(days=1)
            
            fecha_inicio = primer_dia.strftime('%Y-%m-%d')
            fecha_fin = ultimo_dia.strftime('%Y-%m-%d')
            periodo_desc = f'{nombre_mes.capitalize()} {año_num}'

        # ── Comparativa de DOS periodos: "marzo 2026 vs marzo 2025", "2025 vs 2024" ──
        # Detectar AMBOS lados del vs para comparativas específicas
        _patron_vs_meses = re.compile(
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
            r'\s*(?:de\s*)?(\d{4})?\s*(?:vs?\.?|versus|contra|comparado?\s*con)\s*'
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
            r'\s*(?:de\s*)?(\d{4})?',
            re.IGNORECASE
        )
        _patron_vs_años = re.compile(
            r'(\d{4})\s*(?:vs?\.?|versus|contra)\s*(\d{4})',
            re.IGNORECASE
        )

        def _rango_mes(mes_num: int, año_num: int):
            primer = datetime(año_num, mes_num, 1)
            if mes_num == 12:
                ultimo = datetime(año_num + 1, 1, 1) - timedelta(days=1)
            else:
                ultimo = datetime(año_num, mes_num + 1, 1) - timedelta(days=1)
            return primer.strftime('%Y-%m-%d'), ultimo.strftime('%Y-%m-%d')

        match_vs_m = _patron_vs_meses.search(mensaje_lower)
        if match_vs_m:
            mes_a_nom = match_vs_m.group(1).lower()
            año_a = int(match_vs_m.group(2)) if match_vs_m.group(2) else hoy.year
            mes_b_nom = match_vs_m.group(3).lower()
            año_b = int(match_vs_m.group(4)) if match_vs_m.group(4) else hoy.year
            ini_a, fin_a = _rango_mes(meses_nombres[mes_a_nom], año_a)
            ini_b, fin_b = _rango_mes(meses_nombres[mes_b_nom], año_b)
            return {
                'fecha_inicio': ini_a, 'fecha_fin': fin_a,
                'periodo': f'{mes_a_nom.capitalize()} {año_a}',
                'fecha_inicio_a': ini_a, 'fecha_fin_a': fin_a,
                'periodo_a': f'{mes_a_nom.capitalize()} {año_a}',
                'fecha_inicio_b': ini_b, 'fecha_fin_b': fin_b,
                'periodo_b': f'{mes_b_nom.capitalize()} {año_b}',
            }

        match_vs_y = _patron_vs_años.search(mensaje_lower)
        if match_vs_y:
            año_a = int(match_vs_y.group(1))
            año_b = int(match_vs_y.group(2))
            if 2000 <= año_a <= 2100 and 2000 <= año_b <= 2100:
                return {
                    'fecha_inicio': f'{año_a}-01-01', 'fecha_fin': f'{año_a}-12-31',
                    'periodo': f'Año {año_a}',
                    'fecha_inicio_a': f'{año_a}-01-01', 'fecha_fin_a': f'{año_a}-12-31',
                    'periodo_a': f'Año {año_a}',
                    'fecha_inicio_b': f'{año_b}-01-01', 'fecha_fin_b': f'{año_b}-12-31',
                    'periodo_b': f'Año {año_b}',
                }

        return {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'periodo': periodo_desc
        }
    
    def _extraer_parametros(self, mensaje: str) -> Dict[str, Any]:
        """Extrae parámetros del mensaje: límites, filtros, agrupaciones y formato."""
        parametros = {}

        # ── Top N ──────────────────────────────────────────────────────────────
        match = self.patron_top.search(mensaje)
        if match:
            parametros['limite'] = int(match.group(1)) if match.group(1) else 10
            parametros['ordenar'] = 'desc'

        # ── Últimos N días/semanas/meses ───────────────────────────────────────
        match_ult = self.patron_ultimos.search(mensaje)
        if match_ult:
            n = int(match_ult.group(1))
            unidad = match_ult.group(2).lower()
            if 'semana' in unidad:
                parametros['dias_historico'] = n * 7
            elif 'mes' in unidad:
                parametros['dias_historico'] = n * 30
            else:
                parametros['dias_historico'] = n

        # ── Horizonte predicción: "para/próximos/a N días/semanas/meses/años" ──
        # Maneja: "para 30 días", "próximos 30 días", "a 6 meses", "en 1 año"
        _patron_horizonte = re.compile(
            r'(?:para\s+(?:los?\s+)?|próximos?\s+|proximos?\s+|en\s+(?:los?\s+)?|a\s+(?:los?\s+)?)'  # prefijo
            r'(\d+)\s*(d[ií]as?|semanas?|meses?|a[ñn]os?)',
            re.IGNORECASE
        )
        match_hor = _patron_horizonte.search(mensaje)
        if match_hor and 'limite' not in parametros:  # no sobreescribir top-N explícito
            n_hor = int(match_hor.group(1))
            unidad_hor = match_hor.group(2).lower()
            if 'semana' in unidad_hor:
                parametros['limite'] = n_hor * 7
            elif 'mes' in unidad_hor:
                parametros['limite'] = n_hor * 30
            elif 'año' in unidad_hor or 'anio' in unidad_hor:
                parametros['limite'] = n_hor * 365
            else:  # días
                parametros['limite'] = n_hor

        # ── Mayor / Menor que ──────────────────────────────────────────────────
        match = self.patron_mayor.search(mensaje)
        if match:
            parametros['mayor_que'] = float(match.group(1).replace(',', ''))

        match = self.patron_menor.search(mensaje)
        if match:
            parametros['menor_que'] = float(match.group(1).replace(',', ''))

        # ── Comparativa ────────────────────────────────────────────────────────
        match = self.patron_vs.search(mensaje)
        if match:
            parametros['comparar_a'] = match.group(1)
            parametros['comparar_b'] = match.group(2)

        # ── Agrupación (groupby) ────────────────────────────────────────────────
        _GROUPBY_MAP = {
            r'\bpor\s+tienda\b': 'tienda',
            r'\bpor\s+sucursal\b': 'sucursal',
            r'\bpor\s+vendedor\b': 'vendedor',
            r'\bpor\s+vendedora\b': 'vendedor',
            r'\bpor\s+ejecutivo\b': 'vendedor',
            r'\bpor\s+(categoría|categoria)\b': 'categoria',
            r'\bpor\s+marca\b': 'marca',
            r'\bpor\s+producto\b': 'producto',
            r'\bpor\s+(artículo|articulo)\b': 'producto',
            r'\bpor\s+cliente\b': 'cliente',
            r'\bpor\s+proveedor\b': 'proveedor',
            r'\bpor\s+canal\b': 'canal',
            r'\bpor\s+(departamento|área|area)\b': 'departamento',
            r'\bpor\s+(empleado|colaborador)\b': 'empleado',
            r'\bpor\s+(cajero|caja)\b': 'cajero',
            r'\bpor\s+(día|dia)\b': 'dia',
            r'\bpor\s+semana\b': 'semana',
            r'\bpor\s+mes\b': 'mes',
            r'\bpor\s+(año|anio)\b': 'año',
            r'\bdesglosad[ao]\s+por\s+(\w+)': None,  # genérico — captura grupo 1
            r'\bagrupado\s+por\s+(\w+)': None,
        }
        groupby_vals = []
        for patron, valor in _GROUPBY_MAP.items():
            m = re.search(patron, mensaje, re.IGNORECASE)
            if m:
                if valor is None:
                    groupby_vals.append(m.group(1).lower())
                else:
                    groupby_vals.append(valor)
        if groupby_vals:
            parametros['groupby'] = groupby_vals[0] if len(groupby_vals) == 1 else groupby_vals

        # ── Tienda / Sucursal específica ────────────────────────────────────────
        _TIENDAS = [
            'aeropuerto', 'cuautla', 'irapuato', 'moralia', 'morelia', 'puebla',
            'slp', 'san luis', 'lomas', 'antenas', 'toreo', 'cdmx', 'monterrey',
            'guadalajara', 'veracruz', 'cancun', 'mérida', 'merida', 'queretaro',
            'querétaro', 'toluca', 'tijuana', 'juarez', 'leon', 'aguascalientes',
        ]
        for tda in _TIENDAS:
            if re.search(r'\b' + re.escape(tda) + r'\b', mensaje, re.IGNORECASE):
                parametros['tienda'] = tda
                break
        # Patrón genérico "de la tienda X" / "sucursal X"
        if 'tienda' not in parametros:
            m = re.search(r'(?:tienda|sucursal)\s+(?:de\s+)?([A-Za-záéíóúñÁÉÍÓÚÑ\s]{2,25}?)(?:\s|$|,)', mensaje, re.IGNORECASE)
            if m:
                parametros['tienda'] = m.group(1).strip().lower()

        # ── Vendedor específico ───────────────────────────────────────────────
        m = re.search(r'(?:vendedor|ejecutivo|vendedora)\s+(?:llamad[oa]\s+)?([A-Za-záéíóúñÁÉÍÓÚÑ\s]{2,30}?)(?:\s|$|,)', mensaje, re.IGNORECASE)
        if m:
            parametros['vendedor'] = m.group(1).strip()

        # ── Producto / Artículo específico ────────────────────────────────────
        m = re.search(r'(?:del?\s+)?(?:producto|artículo|articulo)\s+(?:llamad[oa]\s+)?["\']?([A-Za-záéíóúñÁÉÍÓÚÑ0-9\s\-]{2,40}?)["\']?(?:\s|$|,)', mensaje, re.IGNORECASE)
        if m:
            parametros['producto'] = m.group(1).strip()

        # ── Cliente específico ────────────────────────────────────────────────
        m = re.search(r'(?:del?\s+)?(?:cliente|customer)\s+(?:llamad[oa]\s+)?["\']?([A-Za-záéíóúñÁÉÍÓÚÑ\s\-]{2,40}?)["\']?(?:\s|$|,)', mensaje, re.IGNORECASE)
        if m:
            parametros['cliente'] = m.group(1).strip()

        # ── Proveedor específico ──────────────────────────────────────────────
        m = re.search(r'(?:del?\s+)?(?:proveedor|supplier)\s+(?:llamad[oa]\s+)?["\']?([A-Za-záéíóúñÁÉÍÓÚÑ\s\-]{2,40}?)["\']?(?:\s|$|,)', mensaje, re.IGNORECASE)
        if m:
            parametros['proveedor'] = m.group(1).strip()

        # ── Formato de salida ─────────────────────────────────────────────────
        _FORMATOS = {
            r'\ben\s+tabla\b': 'tabla',
            r'\ben\s+tabular\b': 'tabla',
            r'\btabla\b': 'tabla',
            r'\ben\s+(una\s+)?gr[aá]fica\b': 'grafica',
            r'\buna\s+gr[aá]fica\b': 'grafica',
            r'\bgr[aá]fica\b': 'grafica',
            r'\bgr[aá]fico\b': 'grafica',
            r'\bchart\b': 'grafica',
            r'\bvisual(?:iza(?:ción|cion))?\b': 'grafica',
            r'\ben\s+lista\b': 'lista',
            r'\ben\s+formato\s+lista\b': 'lista',
            r'\blistado\b': 'lista',
            r'\bresumen\b': 'resumen',
            r'\bsumario\b': 'resumen',
            r'\bbreve\b': 'resumen',
            r'\bexcel\b': 'excel',
            r'\bpdf\b': 'pdf',
            r'\bexportar\b': 'excel',
        }
        for patron, fmt in _FORMATOS.items():
            if re.search(patron, mensaje, re.IGNORECASE):
                parametros['formato'] = fmt
                break

        # ── Dirección de orden ────────────────────────────────────────────────
        if re.search(r'\bmayor\s+a\s+menor\b|\bdescendente\b|\bdecreciente\b', mensaje, re.IGNORECASE):
            parametros['orden_dir'] = 'desc'
        elif re.search(r'\bmenor\s+a\s+mayor\b|\bascendente\b|\bcreciente\b', mensaje, re.IGNORECASE):
            parametros['orden_dir'] = 'asc'

        return parametros
    
    def _extraer_modificadores(self, mensaje: str) -> List[str]:
        """Extrae modificadores de la consulta."""
        modificadores = []
        
        patrones_mod = {
            'detallado': ['detallado', 'detalle', 'completo', 'full', 'todo'],
            'resumen': ['resumen', 'resumido', 'breve', 'corto'],
            'agrupar': ['agrupar', 'por', 'agrupado'],
            'ordenar_asc': ['menor a mayor', 'ascendente', 'creciente'],
            'ordenar_desc': ['mayor a menor', 'descendente', 'decreciente', 'top'],
            'grafico': ['gráfico', 'grafica', 'chart', 'visual'],
            'exportar': ['exportar', 'descargar', 'guardar', 'excel', 'pdf'],
        }
        
        for mod, triggers in patrones_mod.items():
            for trigger in triggers:
                if trigger in mensaje:
                    modificadores.append(mod)
                    break
        
        return list(set(modificadores))
    
    def _detectar_subintenciones(self, mensaje: str, intencion_principal: str) -> List[str]:
        """Detecta subintenciones secundarias."""
        subintenciones = []
        
        # Si pide comparar
        if any(x in mensaje for x in ['vs', 'comparar', 'contra', 'versus']):
            subintenciones.append('comparar')
        
        # Si pide tendencia
        if any(x in mensaje for x in ['tendencia', 'evolución', 'histórico']):
            subintenciones.append('tendencia')
        
        # Si pide predicción
        if any(x in mensaje for x in ['predecir', 'proyección', 'futuro', 'forecast']):
            subintenciones.append('prediccion')
        
        # Si pide exportar
        if any(x in mensaje for x in ['excel', 'pdf', 'exportar', 'descargar']):
            subintenciones.append('exportar')
        
        # Si pide desglose
        if any(x in mensaje for x in ['por', 'desglose', 'detalle', 'breakdown']):
            subintenciones.append('desglosar')
        
        return subintenciones
    
    def generar_respuesta_inteligente(self, consulta: ConsultaEntendida, datos: Any) -> str:
        """Genera una respuesta inteligente basada en la consulta y datos."""
        # Este método puede ser extendido para generar respuestas más naturales
        tipo = consulta.respuesta_tipo
        
        if tipo == 'prediccion':
            return self._formatear_prediccion(datos, consulta)
        elif tipo == 'comparativa':
            return self._formatear_comparativa(datos, consulta)
        elif tipo == 'ranking':
            return self._formatear_ranking(datos, consulta)
        elif tipo == 'analisis':
            return self._formatear_analisis(datos, consulta)
        else:
            return self._formatear_general(datos, consulta)
    
    def _formatear_prediccion(self, datos: Any, consulta: ConsultaEntendida) -> str:
        """Formatea respuesta de predicción."""
        if isinstance(datos, dict) and 'error' in datos:
            return f"{datos['error']}"
        
        return f"""## Predicción: {consulta.intencion_principal.replace('_', ' ').title()}

**Período:** {consulta.temporalidad.get('periodo', 'próximos días')}
**Confianza:** Alta

_Basado en análisis de datos históricos_"""
    
    def _formatear_comparativa(self, datos: Any, consulta: ConsultaEntendida) -> str:
        return "## Análisis Comparativo\n\n_Comparando períodos solicitados_"
    
    def _formatear_ranking(self, datos: Any, consulta: ConsultaEntendida) -> str:
        limite = consulta.parametros.get('limite', 10)
        return f"## Top {limite}\n\n_Ranking generado_"
    
    def _formatear_analisis(self, datos: Any, consulta: ConsultaEntendida) -> str:
        return "## Análisis\n\n_Insights generados automáticamente_"
    
    def _formatear_general(self, datos: Any, consulta: ConsultaEntendida) -> str:
        return "## Resultados\n\n_Consulta procesada_"


# Instancia global
nlp_avanzado = MotorNLPAvanzado()


if __name__ == "__main__":
    # Test
    motor = MotorNLPAvanzado()
    
    tests = [
        "¿Cuánto vendimos la semana pasada?",
        "Top 5 productos más vendidos del mes",
        "Comparar ventas de hoy vs ayer",
        "Proyección de ventas para los próximos 15 días",
        "Análisis de inventario detallado",
        "Empleados por departamento",
        "CXC mayor a $10,000",
        "Cómo va el flujo de caja"
    ]
    
    print("=" * 60)
    print("TEST - Motor NLP Avanzado")
    print("=" * 60)
    
    for test in tests:
        resultado = motor.entender(test)
        print(f"\n'{test}'")
        print(f"   → Intención: {resultado.intencion_principal} ({resultado.confianza:.0%})")
        print(f"   → Acción: {resultado.accion_sugerida}")
        print(f"   → Período: {resultado.temporalidad}")
        print(f"   → Modificadores: {resultado.modificadores}")
