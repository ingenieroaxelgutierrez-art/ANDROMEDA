# ============================================================
# CEREBRO NLP - SISTEMA DE COMPRENSIÓN INTELIGENTE
# ============================================================
# Motor cognitivo avanzado para procesamiento de lenguaje natural
# Inspirado en modelos de IA modernos pero 100% local
# ============================================================

import re
import os 
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import json
import math

# spaCy para análisis lingüístico
try:
    import spacy
    from spacy.tokens import Doc, Token
    SPACY_DISPONIBLE = True
except ImportError:
    SPACY_DISPONIBLE = False

from app.logging_config import get_logger
logger = get_logger("services.nlp.cerebro_nlp")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# ============================================================
# TIPOS Y ESTRUCTURAS DE DATOS
# ============================================================

class TipoConsulta(Enum):
    """Tipos de consulta que el usuario puede hacer."""
    CONSULTA_DATOS = "consulta"      # Quiere ver datos
    ANALISIS = "analisis"            # Quiere análisis profundo
    COMPARATIVA = "comparativa"      # Quiere comparar
    PREDICCION = "prediccion"        # Quiere proyecciones
    REPORTE = "reporte"              # Quiere exportar
    AYUDA = "ayuda"                  # Necesita ayuda
    CONFIGURACION = "config"         # Configurar algo
    CONVERSACIONAL = "chat"          # Solo charla
    MANUAL = "manual"                # Consultar manual Odoo
    GRAFICA = 'grafica'              # Quiere una gráfica


class NivelEspecificidad(Enum):
    """Qué tan específica es la consulta."""
    VAGA = 1        # "dame algo de ventas"
    GENERAL = 2     # "ventas del mes"
    ESPECIFICA = 3  # "ventas de enero por tienda"
    MUY_ESPECIFICA = 4  # "ventas de enero vs febrero por tienda de ropa"


@dataclass
class EntidadSmart:
    """Entidad extraída con inteligencia contextual."""
    tipo: str
    valor: Any
    valor_original: str
    confianza: float
    contexto: str = ""        # En qué contexto se encontró
    es_inferida: bool = False  # Si fue inferida vs explícita


@dataclass 
class IntencionSmart:
    """Intención detectada con análisis profundo."""
    nombre: str
    confianza: float
    tipo_consulta: TipoConsulta
    especificidad: NivelEspecificidad
    entidades: List[EntidadSmart]
    parametros: Dict[str, Any]
    accion_principal: str
    acciones_secundarias: List[str]
    necesita_contexto: List[str]  # Qué información falta
    razonamiento: str  # Por qué se eligió esta intención


@dataclass
class AnalisisSemantico:
    """Resultado del análisis semántico profundo."""
    tokens_relevantes: List[str]
    verbos_accion: List[str]
    sustantivos_clave: List[str]
    modificadores: List[str]
    temporalidad: Dict[str, Any]
    comparadores: List[str]
    negaciones: List[str]
    preguntas: bool
    sentimiento: str  # positivo, negativo, neutro


@dataclass
class ContextoConversacional:
    """Contexto de la conversación para continuidad."""
    tema_actual: Optional[str] = None
    modelo_actual: Optional[str] = None
    periodo_actual: Optional[Dict] = None
    entidades_mencionadas: Dict[str, Any] = field(default_factory=dict)
    historial_intenciones: List[str] = field(default_factory=list)
    ultima_consulta: Optional[str] = None
    ultimo_resultado: Optional[str] = None
    preguntas_pendientes: List[str] = field(default_factory=list)


# ============================================================
# CEREBRO NLP PRINCIPAL
# ============================================================

class CerebroNLP:
    """
    Sistema de comprensión de lenguaje natural avanzado.
    
    Características:
    - Análisis sintáctico y semántico profundo
    - Comprensión de contexto conversacional
    - Inferencia de información implícita
    - Desambiguación inteligente
    - Puntuación multi-factor para intenciones
    """
    
    def __init__(self):
        """Inicializar el cerebro NLP."""
        
        # Cargar spaCy
        self.nlp = None
        if SPACY_DISPONIBLE:
            try:
                self.nlp = spacy.load("es_core_news_sm")
                print("Cerebro NLP inicializado con spaCy")
            except Exception:
                print("spaCy modelo no encontrado")
        
        # Contexto conversacional
        self.contexto = ContextoConversacional()
        
        # Inicializar bases de conocimiento
        self._init_conocimiento()
        self._init_patrones_semanticos()
        self._init_grafos_intenciones()
    
    def _init_conocimiento(self):
        """Inicializa la base de conocimiento del dominio."""
        
        # =====================================================
        # TIENDAS / UNIDADES OPERATIVAS CONOCIDAS
        # =====================================================
        self.tiendas_conocidas = {
            # Nombre normalizado: variantes posibles
            'aeropuerto': ['aeropuerto', 'aero'],
            'cuautla': ['cuautla'],
            'irapuato': ['irapuato'],
            'moral': ['moral', 'la moral'],
            'MT': ['mt', 'toreo', 'flagstore', 'mt flagstore'],
            'xmp': ['xmp', 'ridespot', 'sai', 'xmp ridespot', 'sai xmp', 'sai ridespot'],
            'morelia': ['morelia'],
            'puebla': ['puebla'],
            'san luis': ['slp', 'san luis', 'san luis potosí', 'sanluispotosi'],
            'lomas': ['lomas', 'lomas verdes'],
            'antenas': ['antenas', 'las antenas'],
            'cedis': ['cedis', 'centro de distribución', 'bodega central'],
            'franquicias': ['franquicias', 'franquicia', 'franq'],
        }
        
        # Crear índice inverso para búsqueda rápida
        self.tienda_a_nombre = {}
        for nombre, variantes in self.tiendas_conocidas.items():
            for variante in variantes:
                self.tienda_a_nombre[variante.lower()] = nombre
        
        # =====================================================
        # RESPUESTAS CONVERSACIONALES INTELIGENTES
        # =====================================================
        self.respuestas_inteligentes = {
            'chistes': [
                "¿Por qué el contador siempre lleva una calculadora? ¡Por si las facturas no cuadran! 📊😄",
                "¿Qué le dijo Excel a la base de datos? 'Tú sí que tienes buenos registros' 💻😂",
                "¿Por qué los datos en Odoo nunca se pierden? ¡Porque tienen buenos respaldos! 🔄😜",
                "¿Qué le dice un ERP a otro? '¿Módulos este fin de semana?' 🤓",
                "Mi función favorita es SUM... porque siempre suma al equipo 📈",
                "¿Por qué el inventario fue al psicólogo? Tenía problemas de stock emocional 📦😅",
                "Un cliente entra en la tienda y pregunta: '¿Tienen facturas?' El sistema responde: '¿Las quiere timbradas o sin timbrar?' 🧾",
            ],
            'capacidades_resumen': """## 🌌 Soy ANDROMEDA - Tu Asistente de Inteligencia de Negocios

### Lo que puedo hacer por ti:

**CONSULTAS DE DATOS**
- Ventas (hoy, semana, mes, año, por tienda, por vendedor)
- Inventario (stock, productos críticos, rotación)
- Clientes (top clientes, morosos, cartera)
- Compras y proveedores
- Punto de Venta (POS)

**PREDICCIONES INTELIGENTES**
- Forecast de ventas para los próximos días
- Predicción de qué productos se agotarán
- Score de morosidad de clientes

**ANÁLISIS AVANZADO**
- Comparativas (enero vs febrero, hoy vs ayer)
- Top productos, clientes, vendedores
- KPIs financieros
- Detección de anomalías

**MANUAL DE ODOO**
- Cómo hacer facturas
- Procesos paso a paso
- Tutoriales con imágenes

**REPORTES**
- Excel, PDF, HTML
- Envío por correo

###Prueba preguntándome:
- "Ventas de hoy"
- "Ventas de Moral" (por tienda)
- "Top 10 productos"
- "Predicción de ventas"
- "Cómo hacer una factura"
""",
            'despedidas': [
                "👋 ¡Hasta luego! Fue un placer ayudarte.",
                "👋 ¡Nos vemos! Aquí estaré cuando me necesites.",
                "👋 ¡Hasta pronto! Que tengas un excelente día.",
                "👋 ¡Chao! Vuelve cuando quieras analizar más datos.",
            ],
            'agradecimientos': [
                "¡De nada! 😊 ¿Hay algo más que pueda ayudarte?",
                "¡Con gusto! Estoy para servirte 🙌",
                "¡No hay de qué! ¿Alguna otra consulta?",
            ],
            'no_entiendo': [
                "🤔 No estoy seguro de entenderte. ¿Podrías reformularlo?",
                "🤔 Hmm... no capté bien eso. ¿Puedes decirlo de otra forma?",
            ],
        }
        
        # Conceptos del dominio Odoo
        self.conceptos = {
            'ventas': {
                'sinonimos': ['venta', 'ventas', 'vendido', 'vendieron', 'vender', 
                             'facturado', 'facturación', 'ingreso', 'ingresos',
                             'órdenes', 'ordenes', 'pedidos', 'orders', 'sales'],
                'modelos': ['sale.order', 'pos.order', 'account.move'],
                'metricas': ['total', 'cantidad', 'monto', 'promedio', 'conteo'],
                'dimensiones': ['cliente', 'producto', 'tienda', 'vendedor', 'fecha'],
                'tipo': 'transaccional'
            },
            'inventario': {
                'sinonimos': ['stock', 'inventario', 'existencias', 'almacén', 
                             'bodega', 'productos', 'mercancía', 'disponible'],
                'modelos': ['stock.quant', 'product.product', 'stock.move'],
                'metricas': ['cantidad', 'valor', 'rotación', 'días'],
                'dimensiones': ['producto', 'almacén', 'ubicación', 'categoría'],
                'tipo': 'snapshot'
            },
            'clientes': {
                'sinonimos': ['cliente', 'clientes', 'customer', 'comprador',
                             'partner', 'socio', 'contacto'],
                'modelos': ['res.partner'],
                'metricas': ['total', 'nuevos', 'activos', 'inactivos'],
                'dimensiones': ['país', 'categoría', 'vendedor'],
                'tipo': 'maestro'
            },
            'productos': {
                'sinonimos': ['producto', 'productos', 'artículo', 'item',
                             'sku', 'referencia', 'mercancía'],
                'modelos': ['product.product', 'product.template'],
                'metricas': ['total', 'activos', 'vendidos'],
                'dimensiones': ['categoría', 'marca', 'tipo'],
                'tipo': 'maestro'
            },
            'facturas': {
                'sinonimos': ['factura', 'facturas', 'cfdi', 'comprobante',
                             'invoice', 'facturación'],
                'modelos': ['account.move'],
                'metricas': ['total', 'monto', 'pendientes', 'pagadas'],
                'dimensiones': ['cliente', 'fecha', 'estado'],
                'tipo': 'transaccional'
            },
            'pos': {
                'sinonimos': ['pos', 'punto de venta', 'caja', 'ticket', 'tickets',
                             'mostrador', 'tienda', 'tpv', 'terminal', 'pdv', 'PdV'],
                'modelos': ['pos.order', 'pos.session'],
                'metricas': ['total', 'tickets', 'promedio'],
                'dimensiones': ['tienda', 'cajero', 'método_pago', 'hora'],
                'tipo': 'transaccional'
            },
            'empleados': {
                'sinonimos': ['empleado', 'empleados', 'personal', 'trabajador',
                             'staff', 'colaborador', 'equipo'],
                'modelos': ['hr.employee'],
                'metricas': ['total', 'activos', 'nuevos'],
                'dimensiones': ['departamento', 'puesto', 'antiguedad'],
                'tipo': 'maestro'
            },
            'compras': {
                'sinonimos': ['compra', 'compras', 'purchase', 'adquisición',
                             'pedido proveedor', 'orden compra'],
                'modelos': ['purchase.order'],
                'metricas': ['total', 'monto', 'pendientes'],
                'dimensiones': ['proveedor', 'producto', 'fecha'],
                'tipo': 'transaccional'
            },
            'cxc': {
                'sinonimos': ['cxc', 'cuentas por cobrar', 'cartera', 'cobranza',
                             'deudores', 'pendiente cobro', 'receivables'],
                'modelos': ['account.move'],
                'metricas': ['saldo', 'vencido', 'por_vencer', 'total'],
                'dimensiones': ['cliente', 'antigüedad', 'vendedor'],
                'tipo': 'financiero'
            },
            'cxp': {
                'sinonimos': ['cxp', 'cuentas por pagar', 'deudas', 'payables',
                             'proveedores por pagar', 'acreedores'],
                'modelos': ['account.move'],
                'metricas': ['saldo', 'vencido', 'por_vencer', 'total'],
                'dimensiones': ['proveedor', 'antigüedad'],
                'tipo': 'financiero'
            },
            'kpis': {
                'sinonimos': ['kpi', 'kpis', 'indicador', 'indicadores', 'métrica',
                             'métricas', 'dashboard', 'tablero', 'score', 'salud'],
                'modelos': [],
                'metricas': ['todos', 'específico'],
                'dimensiones': ['área', 'tipo'],
                'tipo': 'analítico'
            },
            'finanzas': {
                'sinonimos': ['finanzas', 'financiero', 'financieros', 'financiera', 'financieras',
                             'flujo de caja', 'cash flow', 'liquidez', 'presupuesto',
                             'riesgo', 'riesgos', 'anomalía', 'anomalías', 'anomalia', 'anomalias',
                             'fraude', 'auditoría financiera', 'estacionalidad'],
                'modelos': ['account.move'],
                'metricas': ['flujo', 'saldo', 'riesgo', 'score'],
                'dimensiones': ['periodo', 'tipo'],
                'tipo': 'financiero'
            },
            'manual': {
                'sinonimos': ['manual', 'cómo', 'como', 'tutorial', 'guía', 'ayuda',
                             'procedimiento', 'proceso', 'paso a paso', 'pasos', 'hacer', 'hago'],
                'modelos': [],
                'metricas': [],
                'dimensiones': [],
                'tipo': 'documental'
            }
        }
        
        # Acciones verbales
        self.verbos_accion = {
            'consultar': ['mostrar', 'ver', 'dame', 'dime', 'obtener', 'buscar',
                         'consultar', 'traer', 'listar', 'enseñar', 'muéstrame',
                         'quiero', 'necesito', 'dónde', 'cuál', 'cuáles'],
            'analizar': ['analizar', 'analiza', 'análisis', 'evaluar', 'estudiar',
                        'revisar', 'examinar', 'investigar', 'profundizar'],
            'comparar': ['comparar', 'comparativa', 'versus', 'vs', 'contra',
                        'diferencia', 'variación', 'cambio', 'antes y después'],
            'predecir': ['predecir', 'proyectar', 'forecast', 'estimar', 'futuro',
                        'tendencia', 'pronóstico', 'qué pasará', 'cuánto venderemos'],
            'reportar': ['reporte', 'exportar', 'excel', 'pdf', 'informe',
                        'descargar', 'generar reporte', 'sacar'],
            'contar': ['cuántos', 'cuántas', 'total', 'cantidad', 'número',
                      'conteo', 'suma', 'cuánto'],
            'explicar': ['cómo', 'explica', 'explícame', 'qué es', 'para qué',
                        'tutorial', 'proceso', 'procedimiento', 'pasos'],
            'graficar': ['graficar', 'gráfica', 'gráfico', 'visualizar', 'ver en gráfico', 'mostrar gráfica']
        }
        
        # Modificadores temporales
        self.temporales = {
            'hoy': {'dias': 0, 'tipo': 'dia'},
            'ayer': {'dias': -1, 'tipo': 'dia'},
            'anteayer': {'dias': -2, 'tipo': 'dia'},
            'mañana': {'dias': 1, 'tipo': 'dia'},
            'esta semana': {'tipo': 'semana_actual'},
            'semana pasada': {'tipo': 'semana_anterior'},
            'este mes': {'tipo': 'mes_actual'},
            'mes pasado': {'tipo': 'mes_anterior'},
            'mes anterior': {'tipo': 'mes_anterior'},
            'este año': {'tipo': 'año_actual'},
            'año pasado': {'tipo': 'año_anterior'},
            'último trimestre': {'meses': -3, 'tipo': 'trimestre'},
            'últimos 7 días': {'dias': -7, 'tipo': 'rango'},
            'últimos 15 días': {'dias': -15, 'tipo': 'rango'},
            'últimos 30 días': {'dias': -30, 'tipo': 'rango'},
            'último mes': {'meses': -1, 'tipo': 'rango'},
            'últimos 3 meses': {'meses': -3, 'tipo': 'rango'},
            'últimos 6 meses': {'meses': -6, 'tipo': 'rango'},
        }
        
        # Meses
        self.meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Modificadores de cantidad
        self.cuantificadores = {
            'todo': 'sin_limite',
            'todos': 'sin_limite',
            'todas': 'sin_limite',
            'top': 'ranking',
            'mejores': 'ranking_desc',
            'peores': 'ranking_asc',
            'primeros': 'ranking',
            'últimos': 'ranking_inverso',
            'más': 'max',
            'menos': 'min',
            'mayor': 'max',
            'menor': 'min',
            'promedio': 'avg',
            'total': 'sum'
        }
    
    def _init_patrones_semanticos(self):
        """Inicializa patrones para análisis semántico."""
        
        # Patrones de pregunta
        self.patrones_pregunta = [
            r'^(qué|que|cuál|cual|cuáles|cuales|cuánto|cuanto|cuántos|cuantos|'
            r'cuántas|cuantas|cómo|como|dónde|donde|quién|quien|por qué|porqué)',
            r'\?$'
        ]
        
        # Patrones de comparación
        self.patrones_comparacion = [
            r'(\w+)\s+(?:vs|versus|contra|comparado?\s+con|frente\s+a)\s+(\w+)',
            r'comparar?\s+(.+)\s+(?:con|y|vs)\s+(.+)',
            r'diferencia\s+entre\s+(.+)\s+y\s+(.+)',
            r'qué\s+(?:cambió|cambio|varió|vario)\s+(?:de|entre)',
        ]
        
        # Patrones de ranking
        self.patrones_ranking = [
            r'(?:top|mejores?|primeros?|principales?)\s*(\d+)?',
            r'(?:peores?|últimos?|menos)\s*(\d+)?',
            r'(?:qué|que|cuál|cual)\s+(?:\w+\s+)?(?:más|menos)\s+(?:vende|vendió|compra|compró)',
        ]
        
        # Patrones numéricos
        self.patron_numero = re.compile(r'\b(\d+(?:[,\.]\d+)?)\b')
        self.patron_moneda = re.compile(r'\$\s*([\d,\.]+)')
        self.patron_porcentaje = re.compile(r'(\d+(?:\.\d+)?)\s*%')
        
        # Patrones de fecha
        self.patron_fecha_completa = re.compile(
            r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})'
        )
        self.patron_mes_año = re.compile(
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|'
            r'septiembre|octubre|noviembre|diciembre)(?:\s+(?:de\s+)?(\d{4}))?',
            re.IGNORECASE
        )
    
    def _init_grafos_intenciones(self):
        """Inicializa el grafo de intenciones con acciones."""
        
        # Mapeo intención -> acción con contexto
        self.grafos_intenciones = {
            # === VENTAS ===
            'ventas_consulta': {
                'concepto': 'ventas',
                'tipo': TipoConsulta.CONSULTA_DATOS,
                'accion': 'consultar_ventas',
                'requiere': [],
                'opcional': ['periodo', 'filtro'],
                'modelo': 'sale.order'
            },
            'ventas_analisis': {
                'concepto': 'ventas',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'analisis_ventas',
                'requiere': [],
                'opcional': ['periodo', 'dimension'],
                'modelo': 'sale.order'
            },
            'ventas_top_productos': {
                'concepto': 'ventas',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'top_productos',
                'requiere': [],
                'opcional': ['periodo', 'limite'],
                'modelo': 'sale.order.line'
            },
            'ventas_comparativa': {
                'concepto': 'ventas',
                'tipo': TipoConsulta.COMPARATIVA,
                'accion': 'comparar_periodos',
                'requiere': ['periodo_1', 'periodo_2'],
                'opcional': [],
                'modelo': 'sale.order'
            },
            'ventas_prediccion': {
                'concepto': 'ventas',
                'tipo': TipoConsulta.PREDICCION,
                'accion': 'predecir_ventas',
                'requiere': [],
                'opcional': ['horizonte'],
                'modelo': 'sale.order'
            },
            'ventas_por_tienda': {
                'concepto': 'ventas',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'ventas_por_tienda',
                'requiere': [],
                'opcional': ['periodo', 'tienda'],
                'modelo': 'pos.order'
            },
            'graficar_ventas': {
                'concepto': 'ventas',
                'tipo': TipoConsulta.GRAFICA,
                'accion': 'graficar_ventas',
                'requiere': [],
                'opcional': ['periodo', 'dimension'],
                'modelo': 'sale.order'
            },
            
            # === POS ===
            'pos_consulta': {
                'concepto': 'pos',
                'tipo': TipoConsulta.CONSULTA_DATOS,
                'accion': 'consultar_pos',
                'requiere': [],
                'opcional': ['periodo', 'tienda'],
                'modelo': 'pos.order'
            },
            'pos_analisis': {
                'concepto': 'pos',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'analisis_pos',
                'requiere': [],
                'opcional': ['periodo'],
                'modelo': 'pos.order'
            },
            'graficar_pos': {
                'concepto': 'pos',
                'tipo': TipoConsulta.GRAFICA,
                'accion': 'graficar_pos',
                'requiere': [],
                'opcional': ['periodo', 'dimension'],
                'modelo': 'pos.order'
            },
            # === INVENTARIO ===
            'inventario_consulta': {
                'concepto': 'inventario',
                'tipo': TipoConsulta.CONSULTA_DATOS,
                'accion': 'consultar_inventario',
                'requiere': [],
                'opcional': ['producto', 'almacen'],
                'modelo': 'stock.quant'
            },
            'inventario_critico': {
                'concepto': 'inventario',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'productos_criticos',
                'requiere': [],
                'opcional': ['umbral'],
                'modelo': 'stock.quant'
            },
            'inventario_prediccion': {
                'concepto': 'inventario',
                'tipo': TipoConsulta.PREDICCION,
                'accion': 'predecir_inventario',
                'requiere': [],
                'opcional': ['producto'],
                'modelo': 'stock.quant'
            },
            'graficar_inventario': {
                'concepto': 'inventario',
                'tipo': TipoConsulta.GRAFICA,
                'accion': 'graficar_inventario',
                'requiere': [],
                'opcional': ['periodo', 'dimension'],
                'modelo': 'stock.quant'
            },
            
            # === CLIENTES ===
            'clientes_consulta': {
                'concepto': 'clientes',
                'tipo': TipoConsulta.CONSULTA_DATOS,
                'accion': 'consultar_clientes',
                'requiere': [],
                'opcional': ['filtro'],
                'modelo': 'res.partner'
            },
            'clientes_analisis': {
                'concepto': 'clientes',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'analisis_clientes',
                'requiere': [],
                'opcional': ['periodo'],
                'modelo': 'res.partner'
            },
            'clientes_top': {
                'concepto': 'clientes',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'top_clientes',
                'requiere': [],
                'opcional': ['periodo', 'limite'],
                'modelo': 'res.partner'
            },
            'graficar_clientes': {
                'concepto': 'clientes',
                'tipo': TipoConsulta.GRAFICA,
                'accion': 'graficar_clientes',
                'requiere': [],
                'opcional': ['periodo', 'dimension'],
                'modelo': 'res.partner'
            },
            # === FINANZAS ===
            'facturas_consulta': {
                'concepto': 'facturas',
                'tipo': TipoConsulta.CONSULTA_DATOS,
                'accion': 'consultar_facturas',
                'requiere': [],
                'opcional': ['periodo', 'estado'],
                'modelo': 'account.move'
            },
            'cxc_consulta': {
                'concepto': 'cxc',
                'tipo': TipoConsulta.CONSULTA_DATOS,
                'accion': 'cuentas_por_cobrar',
                'requiere': [],
                'opcional': ['cliente'],
                'modelo': 'account.move'
            },
            'cxp_consulta': {
                'concepto': 'cxp',
                'tipo': TipoConsulta.CONSULTA_DATOS,
                'accion': 'cuentas_por_pagar',
                'requiere': [],
                'opcional': ['proveedor'],
                'modelo': 'account.move'
            },
            'morosos_analisis': {
                'concepto': 'cxc',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'score_morosos',
                'requiere': [],
                'opcional': [],
                'modelo': 'account.move'
            },
            'graficar_finanzas': {
                'concepto': 'finanzas',
                'tipo': TipoConsulta.GRAFICA,
                'accion': 'graficar_finanzas',
                'requiere': [],
                'opcional': ['periodo', 'dimension'],
                'modelo': 'account.move'
            },
            
            # === KPIs ===
            'kpis_dashboard': {
                'concepto': 'kpis',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'dashboard_kpis',
                'requiere': [],
                'opcional': ['categoria'],
                'modelo': None
            },
            'graficar_kpis': {
                'concepto': 'kpis',
                'tipo': TipoConsulta.GRAFICA,
                'accion': 'graficar_kpis',
                'requiere': [],
                'opcional': ['categoria'],
                'modelo': None
            },
            
            # === MANUAL ===
            'manual_consulta': {
                'concepto': 'manual',
                'tipo': TipoConsulta.MANUAL,
                'accion': 'consultar_manual',
                'requiere': ['tema'],
                'opcional': [],
                'modelo': None
            },
            
            # === AYUDA ===
            'ayuda_general': {
                'concepto': 'ayuda',
                'tipo': TipoConsulta.AYUDA,
                'accion': 'mostrar_ayuda',
                'requiere': [],
                'opcional': ['tema'],
                'modelo': None
            },
            
            # === SALUDO ===
            'saludo': {
                'concepto': 'saludo',
                'tipo': TipoConsulta.CONVERSACIONAL,
                'accion': 'responder_saludo',
                'requiere': [],
                'opcional': [],
                'modelo': None
            },
            'graficar_saludo': {
                'concepto': 'saludo',
                'tipo': TipoConsulta.GRAFICA,
                'accion': 'graficar_saludo',
                'requiere': [],
                'opcional': [],
                'modelo': None
            },
            
            # === DESPEDIDA ===
            'despedida': {
                'concepto': 'despedida',
                'tipo': TipoConsulta.CONVERSACIONAL,
                'accion': 'responder_despedida',
                'requiere': [],
                'opcional': [],
                'modelo': None
            },
            
            # === AGRADECIMIENTO ===
            'agradecimiento': {
                'concepto': 'agradecimiento',
                'tipo': TipoConsulta.CONVERSACIONAL,
                'accion': 'responder_agradecimiento',
                'requiere': [],
                'opcional': [],
                'modelo': None
            },
            
            # === CHISTE ===
            'chiste': {
                'concepto': 'humor',
                'tipo': TipoConsulta.CONVERSACIONAL,
                'accion': 'contar_chiste',
                'requiere': [],
                'opcional': [],
                'modelo': None
            },
            
            # === CAPACIDADES ===
            'capacidades': {
                'concepto': 'ayuda',
                'tipo': TipoConsulta.AYUDA,
                'accion': 'mostrar_capacidades',
                'requiere': [],
                'opcional': [],
                'modelo': None
            },
            
            # === VENTAS POR TIENDA ESPECÍFICA ===
            'ventas_tienda_especifica': {
                'concepto': 'ventas',
                'tipo': TipoConsulta.CONSULTA_DATOS,
                'accion': 'ventas_tienda_especifica',
                'requiere': ['tienda'],
                'opcional': ['periodo'],
                'modelo': 'pos.order'
            },
            'graficar_ventas_tienda': {
                'concepto': 'ventas',
                'tipo': TipoConsulta.GRAFICA,
                'accion': 'graficar_ventas_tienda',
                'requiere': ['tienda'],
                'opcional': ['periodo'],
                'modelo': 'pos.order'
            },
            
            # === FLUJO DE CAJA ===
            'flujo_caja': {
                'concepto': 'finanzas',
                'tipo': TipoConsulta.PREDICCION,
                'accion': 'flujo_caja',
                'requiere': [],
                'opcional': ['horizonte'],
                'modelo': 'account.move'
            },
            'graficar_flujo_caja': {
                'concepto': 'finanzas',
                'tipo': TipoConsulta.GRAFICA,
                'accion': 'graficar_flujo_caja',
                'requiere': [],
                'opcional': ['horizonte'],
                'modelo': 'account.move'
            },
            
            # === KPIs POR TIENDA ===
            'kpis_por_tienda': {
                'concepto': 'kpis',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'kpis_por_tienda',
                'requiere': [],
                'opcional': ['periodo', 'tienda'],
                'modelo': 'pos.order'
            },
            'graficar_kpis_tienda': {
                'concepto': 'kpis',
                'tipo': TipoConsulta.GRAFICA,
                'accion': 'graficar_kpis_tienda',
                'requiere': [],
                'opcional': ['periodo', 'tienda'],
                'modelo': 'pos.order'
            },
            
            # === FACTURAS FILTRADAS ===
            'facturas_filtradas': {
                'concepto': 'facturas',
                'tipo': TipoConsulta.CONSULTA_DATOS,
                'accion': 'facturas_filtradas',
                'requiere': [],
                'opcional': ['estado', 'tienda', 'periodo'],
                'modelo': 'account.move'
            },
            
            # === PDF CONTEXTUAL ===
            'pdf_contextual': {
                'concepto': 'reporte',
                'tipo': TipoConsulta.REPORTE,
                'accion': 'generar_pdf_profesional',
                'requiere': [],
                'opcional': [],
                'modelo': None
            },
            
            # === BUSINESS INTELLIGENCE AVANZADO ===
            'salud_negocio': {
                'concepto': 'kpis',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'salud_negocio',
                'requiere': [],
                'opcional': [],
                'modelo': None
            },
            'estacionalidad': {
                'concepto': 'finanzas',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'estacionalidad',
                'requiere': [],
                'opcional': ['periodo'],
                'modelo': 'sale.order'
            },
            'reporte_bi': {
                'concepto': 'kpis',
                'tipo': TipoConsulta.REPORTE,
                'accion': 'reporte_bi',
                'requiere': [],
                'opcional': [],
                'modelo': None
            },
            'auditoria_fraude': {
                'concepto': 'finanzas',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'auditoria_fraude',
                'requiere': [],
                'opcional': [],
                'modelo': 'account.move'
            },
            'detectar_anomalias': {
                'concepto': 'finanzas',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'detectar_anomalias',
                'requiere': [],
                'opcional': [],
                'modelo': 'account.move'
            },
            'analisis_riesgos': {
                'concepto': 'finanzas',
                'tipo': TipoConsulta.ANALISIS,
                'accion': 'analisis_riesgos',
                'requiere': [],
                'opcional': [],
                'modelo': None
            },
        }
    
    # ============================================================
    # ANÁLISIS PRINCIPAL
    # ============================================================
    
    def analizar(self, texto: str) -> IntencionSmart:
        """
        Analiza una consulta y retorna la intención inteligente.
        
        Este es el método principal que orquesta todo el análisis.
        """
        texto_original = texto
        texto = texto.strip()
        
        # 1. Pre-procesamiento
        texto_limpio = self._preprocesar(texto)
        
        # 2. Análisis sintáctico con spaCy
        analisis = self._analisis_sintactico(texto_limpio)
        
        # 3. Extraer entidades
        entidades = self._extraer_entidades(texto_limpio, analisis)
        
        # 4. Detectar tipo de consulta
        tipo_consulta = self._detectar_tipo_consulta(texto_limpio, analisis)
        
        # 5. Identificar concepto principal
        concepto_principal = self._identificar_concepto(texto_limpio, analisis, entidades)
        
        # 6. Calcular intención con puntuación multi-factor
        intencion = self._calcular_intencion(
            texto_limpio, 
            concepto_principal,
            tipo_consulta,
            analisis,
            entidades
        )
        
        # 7. Inferir información faltante del contexto
        intencion = self._aplicar_contexto(intencion)
        
        # 8. Validar coherencia
        intencion = self._validar_coherencia(intencion, texto_original)
        
        # 9. Actualizar contexto conversacional
        self._actualizar_contexto(intencion)
        
        return intencion
    
    def _preprocesar(self, texto: str) -> str:
        """Pre-procesa el texto normalizando y limpiando."""
        
        # Convertir a minúsculas
        texto = texto.lower()
        
        # Normalizar acentos opcionales
        # texto = self._normalizar_acentos(texto)
        
        # Limpiar signos de puntuación excesivos
        texto = re.sub(r'[!¡¿]+', '', texto)
        texto = re.sub(r'\s+', ' ', texto)
        
        # Expandir abreviaturas comunes
        abreviaturas = {
            'q ': 'que ',
            'xq ': 'porque ',
            'dnd ': 'donde ',
            'tb ': 'también ',
            'x ': 'por ',
            'pf ': 'por favor ',
            'fav ': 'favor ',
        }
        for abrev, expansion in abreviaturas.items():
            texto = texto.replace(abrev, expansion)
        
        return texto.strip()
    
    def _analisis_sintactico(self, texto: str) -> AnalisisSemantico:
        """Realiza análisis sintáctico profundo con spaCy."""
        
        tokens_relevantes = []
        verbos_accion = []
        sustantivos_clave = []
        modificadores = []
        temporalidad = {}
        comparadores = []
        negaciones = []
        es_pregunta = False
        
        # Detectar si es pregunta
        for patron in self.patrones_pregunta:
            if re.search(patron, texto, re.IGNORECASE):
                es_pregunta = True
                break
        
        if self.nlp:
            doc = self.nlp(texto)
            
            for token in doc:
                # Verbos
                if token.pos_ == 'VERB':
                    verbos_accion.append(token.lemma_)
                    tokens_relevantes.append(token.lemma_)
                
                # Sustantivos
                elif token.pos_ == 'NOUN':
                    sustantivos_clave.append(token.lemma_)
                    tokens_relevantes.append(token.lemma_)
                
                # Adjetivos y adverbios (modificadores)
                elif token.pos_ in ('ADJ', 'ADV'):
                    modificadores.append(token.text)
                
                # Negaciones
                if token.dep_ == 'neg' or token.text in ('no', 'sin', 'nunca', 'nada'):
                    negaciones.append(token.text)
                
                # Números
                if token.pos_ == 'NUM':
                    tokens_relevantes.append(token.text)
        else:
            # Fallback sin spaCy
            palabras = texto.split()
            tokens_relevantes = palabras
            
            # Detectar verbos y sustantivos por listas
            for palabra in palabras:
                for verbo_tipo, lista_verbos in self.verbos_accion.items():
                    if palabra in lista_verbos:
                        verbos_accion.append(palabra)
                        break
        
        # Detectar temporalidad
        for temp, valor in self.temporales.items():
            if temp in texto:
                temporalidad[temp] = valor
        
        # Detectar comparadores
        for patron in self.patrones_comparacion:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                comparadores.append(match.group())
        
        # Detectar sentimiento simple
        palabras_positivas = ['mejor', 'más', 'aumentó', 'creció', 'subió', 'excelente', 'bien']
        palabras_negativas = ['peor', 'menos', 'bajó', 'cayó', 'mal', 'problema', 'crítico']
        
        sentimiento = 'neutro'
        for p in palabras_positivas:
            if p in texto:
                sentimiento = 'positivo'
                break
        for p in palabras_negativas:
            if p in texto:
                sentimiento = 'negativo'
                break
        
        return AnalisisSemantico(
            tokens_relevantes=tokens_relevantes,
            verbos_accion=verbos_accion,
            sustantivos_clave=sustantivos_clave,
            modificadores=modificadores,
            temporalidad=temporalidad,
            comparadores=comparadores,
            negaciones=negaciones,
            preguntas=es_pregunta,
            sentimiento=sentimiento
        )
    
    def _extraer_entidades(self, texto: str, analisis: AnalisisSemantico) -> List[EntidadSmart]:
        """Extrae entidades del texto con inteligencia."""
        
        entidades = []
        
        # 1. Fechas específicas
        match_fecha = self.patron_fecha_completa.search(texto)
        if match_fecha:
            dia, mes, año = match_fecha.groups()
            if len(año) == 2:
                año = '20' + año
            entidades.append(EntidadSmart(
                tipo='fecha',
                valor=f"{año}-{mes.zfill(2)}-{dia.zfill(2)}",
                valor_original=match_fecha.group(),
                confianza=0.95
            ))
        
        # 2. Meses
        match_mes = self.patron_mes_año.search(texto)
        if match_mes:
            mes_nombre, año = match_mes.groups()
            mes_num = self.meses.get(mes_nombre.lower(), 1)
            año = año or str(datetime.now().year)
            entidades.append(EntidadSmart(
                tipo='periodo_mes',
                valor={'mes': mes_num, 'año': int(año)},
                valor_original=match_mes.group(),
                confianza=0.9
            ))
        
        # 3. Números/cantidades
        for match in self.patron_numero.finditer(texto):
            num_str = match.group(1).replace(',', '')
            try:
                num = float(num_str) if '.' in num_str else int(num_str)
                # Determinar contexto del número
                contexto = self._contexto_numero(texto, match.start())
                entidades.append(EntidadSmart(
                    tipo='numero',
                    valor=num,
                    valor_original=match.group(),
                    confianza=0.85,
                    contexto=contexto
                ))
            except Exception:
                pass
        
        # 4. Períodos de tiempo
        for periodo, config in analisis.temporalidad.items():
            entidades.append(EntidadSmart(
                tipo='periodo',
                valor=config,
                valor_original=periodo,
                confianza=0.9
            ))
        
        # 5. Entidades de ranking (top N)
        for patron in self.patrones_ranking:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                limite = match.group(1) if match.lastindex and match.group(1) else '10'
                entidades.append(EntidadSmart(
                    tipo='ranking',
                    valor=int(limite),
                    valor_original=match.group(),
                    confianza=0.85
                ))
                break
        
        # 6. Detectar tiendas/almacenes mencionados
        patron_tienda = re.compile(r'(?:tienda|sucursal|almacén|local|punto)\s+["\']?(\w+)["\']?', re.IGNORECASE)
        match_tienda = patron_tienda.search(texto)
        if match_tienda:
            entidades.append(EntidadSmart(
                tipo='tienda',
                valor=match_tienda.group(1),
                valor_original=match_tienda.group(),
                confianza=0.8
            ))
        
        return entidades
    
    def _contexto_numero(self, texto: str, posicion: int) -> str:
        """Determina el contexto de un número encontrado."""
        
        # Obtener palabras cercanas
        antes = texto[max(0, posicion-30):posicion].split()
        
        if any(p in antes for p in ['top', 'mejores', 'primeros', 'últimos']):
            return 'limite'
        elif any(p in antes for p in ['$', 'pesos', 'monto', 'total']):
            return 'monto'
        elif any(p in antes for p in ['días', 'meses', 'años', 'semanas']):
            return 'tiempo'
        
        return 'cantidad'
    
    def _detectar_tipo_consulta(self, texto: str, analisis: AnalisisSemantico) -> TipoConsulta:
        """Detecta el tipo de consulta del usuario."""
        
        # Comparativa
        if analisis.comparadores or 'vs' in texto or 'versus' in texto or 'comparar' in texto:
            return TipoConsulta.COMPARATIVA
        
        # Predicción
        palabras_prediccion = ['predecir', 'predice', 'predicción', 'prediccion', 'proyección',
                               'proyeccion', 'forecast', 'futuro', 'pronóstico', 'pronostico',
                               'tendencia', 'venderemos', 'venderá', 'estimar']
        if any(p in texto for p in palabras_prediccion):
            return TipoConsulta.PREDICCION
        
        # Reporte
        palabras_reporte = ['reporte', 'exportar', 'excel', 'pdf', 'descargar', 'generar']
        if any(p in texto for p in palabras_reporte):
            return TipoConsulta.REPORTE
        
        # Manual/Ayuda procedimiento
        palabras_manual = ['cómo', 'como se', 'proceso', 'procedimiento', 'tutorial',
                          'paso a paso', 'pasos para', 'manual', 'guía']
        if any(p in texto for p in palabras_manual):
            return TipoConsulta.MANUAL
        
        # Análisis
        palabras_analisis = ['analizar', 'análisis', 'analiza', 'evaluar', 'estudiar',
                            'profundidad', 'detalle', 'completo', 'dashboard', 'kpi']
        if any(p in texto for p in palabras_analisis):
            return TipoConsulta.ANALISIS
        
        # Saludo/Conversacional
        saludos = ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'hey', 'qué tal',
                  'cómo estás', 'gracias', 'adiós', 'bye', 'hasta luego']
        if any(s in texto for s in saludos):
            return TipoConsulta.CONVERSACIONAL
        
        # Ayuda general
        if 'ayuda' in texto or texto in ['?', 'help']:
            return TipoConsulta.AYUDA
        
        # Gráficas
        grafica = ['graficar', 'gráfica', 'gráfico', 'visualizar', 'mostrar gráfico', 'plotear',
                   'grafia', 'grafía', 'chart', 'plot']
        if any(g in texto for g in grafica):
            return TipoConsulta.GRAFICA
        
        # Por defecto: consulta de datos
        return TipoConsulta.CONSULTA_DATOS
        
    
    def _identificar_concepto(self, texto: str, analisis: AnalisisSemantico, 
                              entidades: List[EntidadSmart]) -> str:
        """Identifica el concepto principal de la consulta."""
        
        puntuaciones = {}
        
        for concepto, info in self.conceptos.items():
            score = 0
            matches = []
            
            # Buscar sinónimos
            for sinonimo in info['sinonimos']:
                if sinonimo in texto:
                    # Peso más alto para match exacto de palabra
                    if re.search(rf'\b{re.escape(sinonimo)}\b', texto):
                        score += 10
                        matches.append(sinonimo)
                    else:
                        score += 3
            
            # Buscar en sustantivos detectados por spaCy
            for sustantivo in analisis.sustantivos_clave:
                if sustantivo in info['sinonimos']:
                    score += 5
            
            # Bonus por contexto del historial
            if self.contexto.tema_actual == concepto:
                score += 3
            
            if score > 0:
                puntuaciones[concepto] = {
                    'score': score,
                    'matches': matches
                }
        
        # Seleccionar concepto con mayor puntuación
        if puntuaciones:
            mejor = max(puntuaciones.items(), key=lambda x: x[1]['score'])
            return mejor[0]
        
        # Si no hay concepto claro, usar contexto o 'general'
        if self.contexto.tema_actual:
            return self.contexto.tema_actual
        
        return 'general'
    
    def _calcular_intencion(self, texto: str, concepto: str, 
                            tipo_consulta: TipoConsulta,
                            analisis: AnalisisSemantico,
                            entidades: List[EntidadSmart]) -> IntencionSmart:
        """Calcula la intención final con puntuación multi-factor."""
        
        mejor_intencion = None
        mejor_score = 0
        razonamiento = []
        
        # =====================================================
        # FASE 0: DETECCIÓN DE PATRONES ESPECÍFICOS
        # Esto tiene prioridad sobre el análisis general
        # Sistema inteligente de comprensión semántica
        # =====================================================
        
        texto_palabras = texto.split()
        num_palabras = len(texto_palabras)
        
        # -------------------------------------------------
        # 0.1 CHISTES (máxima prioridad conversacional)
        # -------------------------------------------------
        patrones_chiste = ['chiste', 'cuéntame algo gracioso', 'hazme reír', 
                          'algo gracioso', 'bromea', 'dime un chiste', 'cuenta un chiste',
                          'cuentame un chiste', 'me cuentas un chiste']
        if any(p in texto for p in patrones_chiste):
            return IntencionSmart(
                nombre='chiste',
                confianza=0.95,
                tipo_consulta=TipoConsulta.CONVERSACIONAL,
                especificidad=NivelEspecificidad.GENERAL,
                entidades=[],
                parametros={},
                accion_principal='contar_chiste',
                acciones_secundarias=[],
                necesita_contexto=[],
                razonamiento='chiste_detectado'
            )
        
        # -------------------------------------------------
        # 0.2 CAPACIDADES / QUÉ PUEDES HACER
        # -------------------------------------------------
        patrones_capacidades = ['qué puedes hacer', 'que puedes hacer', 'qué haces',
                               'que haces', 'qué sabes hacer', 'tus capacidades',
                               'para qué sirves', 'cómo me ayudas', 'qué funciones tienes',
                               'de qué eres capaz', 'resumen de lo que haces',
                               'quién eres', 'quien eres', 'preséntate', 'presentate']
        if any(p in texto for p in patrones_capacidades):
            return IntencionSmart(
                nombre='capacidades',
                confianza=0.95,
                tipo_consulta=TipoConsulta.AYUDA,
                especificidad=NivelEspecificidad.GENERAL,
                entidades=[],
                parametros={},
                accion_principal='mostrar_capacidades',
                acciones_secundarias=[],
                necesita_contexto=[],
                razonamiento='capacidades_detectado'
            )
        
        # -------------------------------------------------
        # 0.3 DESPEDIDAS
        # -------------------------------------------------
        despedidas = ['adiós', 'adios', 'bye', 'hasta luego', 'nos vemos', 
                     'chao', 'me voy', 'hasta pronto', 'hasta mañana']
        if num_palabras <= 4 and any(d in texto for d in despedidas):
            return IntencionSmart(
                nombre='despedida',
                confianza=0.95,
                tipo_consulta=TipoConsulta.CONVERSACIONAL,
                especificidad=NivelEspecificidad.GENERAL,
                entidades=[],
                parametros={},
                accion_principal='responder_despedida',
                acciones_secundarias=[],
                necesita_contexto=[],
                razonamiento='despedida_detectada'
            )
        
        # -------------------------------------------------
        # 0.4 AGRADECIMIENTOS
        # -------------------------------------------------
        agradecimientos = ['gracias', 'muchas gracias', 'te agradezco', 'thanks',
                          'agradecido', 'muy amable', 'excelente gracias']
        if num_palabras <= 5 and any(a in texto for a in agradecimientos):
            return IntencionSmart(
                nombre='agradecimiento',
                confianza=0.95,
                tipo_consulta=TipoConsulta.CONVERSACIONAL,
                especificidad=NivelEspecificidad.GENERAL,
                entidades=[],
                parametros={},
                accion_principal='responder_agradecimiento',
                acciones_secundarias=[],
                necesita_contexto=[],
                razonamiento='agradecimiento_detectado'
            )
        
        # -------------------------------------------------
        # 0.5 SALUDOS SIMPLES (solo si es muy corto)
        # -------------------------------------------------
        saludos = ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'holi',
                   'hey', 'qué tal', 'hi', 'hello', 'buen día', 'holo', 'halo', 'ola', 'buenas', 'qué onda', 'qué hubo']
        if num_palabras <= 3 and any(s in texto for s in saludos):
            return IntencionSmart(
                nombre='saludo',
                confianza=0.95,
                tipo_consulta=TipoConsulta.CONVERSACIONAL,
                especificidad=NivelEspecificidad.GENERAL,
                entidades=[],
                parametros={},
                accion_principal='responder_saludo',
                acciones_secundarias=[],
                necesita_contexto=[],
                razonamiento='saludo_detectado'
            )
        
        # -------------------------------------------------
        # 0.5B VENTAS BÁSICAS (cuánto vendimos, ventas de hoy, etc.)
        # -------------------------------------------------
        patrones_ventas_basicas = ['cuánto vendimos', 'cuanto vendimos', 'ventas de hoy',
                                   'ventas del día', 'qué vendimos', 'total vendido',
                                   'vendimos hoy', 'ventas hoy', 'venta de hoy']
        if any(p in texto for p in patrones_ventas_basicas):
            return IntencionSmart(
                nombre='ventas_consulta',
                confianza=0.90,
                tipo_consulta=TipoConsulta.CONSULTA_DATOS,
                especificidad=NivelEspecificidad.GENERAL,
                entidades=entidades,
                parametros={},
                accion_principal='consultar_ventas',
                acciones_secundarias=[],
                necesita_contexto=[],
                razonamiento='ventas_basicas_detectado'
            )
        
        # -------------------------------------------------
        # 0.6 VENTAS POR TIENDA ESPECÍFICA
        # Detectar: "ventas Moral", "ventas de tienda Aeropuerto"
        # -------------------------------------------------
        tienda_detectada = None
        for variante, nombre in self.tienda_a_nombre.items():
            if variante in texto:
                tienda_detectada = nombre
                break
        
        if tienda_detectada and any(v in texto for v in ['venta', 'ventas', 'vendido', 'pos']):
            entidades.append(EntidadSmart(
                tipo='tienda',
                valor=tienda_detectada,
                valor_original=tienda_detectada,
                confianza=0.95,
                contexto='filtro_tienda'
            ))
            return IntencionSmart(
                nombre='ventas_tienda_especifica',
                confianza=0.92,
                tipo_consulta=TipoConsulta.CONSULTA_DATOS,
                especificidad=NivelEspecificidad.ESPECIFICA,
                entidades=entidades,
                parametros={'tienda': tienda_detectada},
                accion_principal='ventas_tienda_especifica',
                acciones_secundarias=[],
                necesita_contexto=[],
                razonamiento=f'tienda_especifica={tienda_detectada}'
            )
        
        # Solo tienda mencionada sin contexto de ventas - guardar para después
        if tienda_detectada:
            entidades.append(EntidadSmart(
                tipo='tienda',
                valor=tienda_detectada,
                valor_original=tienda_detectada,
                confianza=0.85,
                contexto='tienda_mencionada'
            ))
        
        # -------------------------------------------------
        # 0.7 VENTAS POR TIENDA (genérico)
        # -------------------------------------------------
        if any(p in texto for p in ['por tienda', 'por sucursal', 'por unidad operativa',
                                    'ventas tienda', 'venta tienda', 'por punto de venta']):
            mejor_intencion = 'ventas_por_tienda'
            mejor_score = 88
            razonamiento = ['ventas_por_tienda_detectado']
        
        # -------------------------------------------------
        # 0.8 TOP/RANKING PRODUCTOS
        # -------------------------------------------------
        if any(p in texto for p in ['top', 'mejores', 'más vendidos', 'principales producto']):
            if 'producto' in texto or 'vendido' in texto or 'artículo' in texto:
                mejor_intencion = 'ventas_top_productos'
                mejor_score = 88
                razonamiento = ['top_productos_detectado']
        
        # -------------------------------------------------
        # 0.9 TOP CLIENTES
        # -------------------------------------------------
        if re.search(r'top\s*\d*\s*cliente', texto) or any(p in texto for p in ['mejores cliente', 'principales cliente', 'clientes que más compran']):
            mejor_intencion = 'clientes_top'
            mejor_score = 88
            razonamiento = ['top_clientes_detectado']
        
        # -------------------------------------------------
        # 0.10 PREDICCIONES (mejorado con extracción de periodo futuro)
        # -------------------------------------------------
        patrones_prediccion = ['predicción', 'predecir', 'predice', 'pronóstico', 'forecast', 
                               'proyección', 'proyectar', 'estimar', 'cuánto venderemos']
        if any(p in texto for p in patrones_prediccion):
            # Extraer periodo futuro si se menciona
            dias_prediccion = 7  # default
            
            # Buscar días explícitos "para 30 días", "próximos 15 días"
            match_dias = re.search(r'(?:para|próximos?|siguientes?)\s*(\d+)\s*días?', texto)
            if match_dias:
                dias_prediccion = int(match_dias.group(1))
            
            # Buscar mes futuro "para marzo 2026", "marzo", etc.
            meses_futuro = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
            }
            for mes_nombre, mes_num in meses_futuro.items():
                if mes_nombre in texto:
                    # Calcular días desde hoy hasta el inicio de ese mes
                    match_año = re.search(r'(\d{4})', texto)
                    año = int(match_año.group(1)) if match_año else datetime.now().year
                    hoy = datetime.now()
                    mes_inicio = datetime(año, mes_num, 1)
                    # Si el mes es futuro, calcular días
                    if mes_inicio > hoy:
                        dias_prediccion = (mes_inicio - hoy).days + 30  # hasta fin del mes
                        entidades.append(EntidadSmart(
                            tipo='periodo_prediccion',
                            valor={'mes': mes_num, 'año': año, 'dias': dias_prediccion},
                            valor_original=f"{mes_nombre} {año}",
                            confianza=0.95
                        ))
                    break
            
            # Agregar entidad de horizonte
            entidades.append(EntidadSmart(
                tipo='horizonte',
                valor=dias_prediccion,
                valor_original=f"{dias_prediccion} días",
                confianza=0.9
            ))
            
            # Primero verificar inventario (antes de ventas)
            if 'inventario' in texto or 'stock' in texto:
                mejor_intencion = 'inventario_prediccion'
                mejor_score = 94
                razonamiento = ['prediccion_inventario_detectado', f'dias={dias_prediccion}']
            elif 'venta' in texto or 'ingreso' in texto or not ('inventario' in texto or 'stock' in texto):
                mejor_intencion = 'ventas_prediccion'
                mejor_score = 94
                razonamiento = ['prediccion_ventas_detectado', f'dias={dias_prediccion}']
            else:
                mejor_intencion = 'ventas_prediccion'
                mejor_score = 90
                razonamiento = ['prediccion_general', f'dias={dias_prediccion}']
        
        # -------------------------------------------------
        # 0.11 MOROSOS / CARTERA
        # -------------------------------------------------
        if any(p in texto for p in ['moroso', 'morosos', 'morosidad', 'deudor', 
                                    'no paga', 'no han pagado', 'cartera vencida']):
            mejor_intencion = 'morosos_analisis'
            mejor_score = 92
            razonamiento = ['morosos_detectado']
        
        # -------------------------------------------------
        # 0.12 STOCK CRÍTICO
        # -------------------------------------------------
        if any(p in texto for p in ['agotarse', 'agotando', 'sin stock', 'stock bajo', 
                                    'crítico', 'faltante', 'reponer', 'poco inventario',
                                    'productos bajos', 'escasez']):
            mejor_intencion = 'inventario_critico'
            mejor_score = 88
            razonamiento = ['inventario_critico_detectado']
        
        # -------------------------------------------------
        # 0.12B FLUJO DE CAJA / PREDICCIÓN FINANCIERA
        # -------------------------------------------------
        if any(p in texto for p in ['flujo de caja', 'cash flow', 'liquidez proyectada',
                                    'predice.*flujo', 'predecir flujo', 'proyección caja',
                                    'efectivo disponible', 'predicción financiera']):
            mejor_intencion = 'flujo_caja'
            mejor_score = 94
            razonamiento = ['flujo_caja_detectado']
            # Extraer días si se mencionan
            match_dias = re.search(r'(\d+)\s*días?', texto)
            if match_dias:
                entidades.append(EntidadSmart(
                    tipo='horizonte',
                    valor=int(match_dias.group(1)),
                    valor_original=match_dias.group(),
                    confianza=0.9
                ))
        
        # -------------------------------------------------
        # 0.12C KPIs / INDICADORES POR TIENDA
        # -------------------------------------------------
        if any(p in texto for p in ['indicadores de tiendas', 'kpis por tienda', 'indicadores por tienda',
                                    'indicadores tiendas', 'dashboard tiendas', 'rendimiento tiendas',
                                    'resultados por tienda', 'comparativa tiendas']):
            mejor_intencion = 'kpis_por_tienda'
            mejor_score = 92
            razonamiento = ['kpis_tienda_detectado']
        
        # -------------------------------------------------
        # 0.13 COMPARATIVAS (mejorado con extracción de periodos)
        # -------------------------------------------------
        patrones_comparativa = ['vs', 'versus', 'comparar', 'comparativa', 
                                'comparado con', 'contra', 'diferencia entre']
        if any(p in texto for p in patrones_comparativa):
            mejor_intencion = 'ventas_comparativa'
            mejor_score = 88
            razonamiento = ['comparativa_detectada']
            
            # Extraer los dos periodos de comparación (hoy vs ayer, enero vs febrero, etc.)
            match_vs = re.search(r'(\w+)\s+vs\s+(\w+)', texto)
            match_versus = re.search(r'(\w+)\s+versus\s+(\w+)', texto)
            match_comparar = re.search(r'compara[r]?\s+(.+?)\s+(?:con|y)\s+(.+?)(?:\s|$)', texto)
            
            periodo_1, periodo_2 = None, None
            if match_vs:
                periodo_1, periodo_2 = match_vs.group(1), match_vs.group(2)
            elif match_versus:
                periodo_1, periodo_2 = match_versus.group(1), match_versus.group(2)
            elif match_comparar:
                periodo_1, periodo_2 = match_comparar.group(1).strip(), match_comparar.group(2).strip()
            
            # Mapear periodos conocidos
            periodos_map = {
                'hoy': 'dia', 'ayer': 'dia',
                'semana': 'semana', 'mes': 'mes', 'año': 'anio',
                'enero': 'mes', 'febrero': 'mes', 'marzo': 'mes', 'abril': 'mes',
                'mayo': 'mes', 'junio': 'mes', 'julio': 'mes', 'agosto': 'mes',
                'septiembre': 'mes', 'octubre': 'mes', 'noviembre': 'mes', 'diciembre': 'mes'
            }
            
            if periodo_1 and periodo_2:
                entidades.append(EntidadSmart(
                    tipo='comparativa',
                    valor={'periodo_1': periodo_1, 'periodo_2': periodo_2},
                    valor_original=f"{periodo_1} vs {periodo_2}",
                    confianza=0.92
                ))
                # Determinar tipo de comparación
                if periodo_1.lower() in ['hoy', 'ayer'] or periodo_2.lower() in ['hoy', 'ayer']:
                    entidades.append(EntidadSmart(
                        tipo='tipo_comparativa',
                        valor='dia',
                        valor_original='hoy vs ayer',
                        confianza=0.95
                    ))
                razonamiento.append(f'periodos={periodo_1}_vs_{periodo_2}')
        
        # -------------------------------------------------
        # 0.13B FACTURAS CON FILTROS (pendientes, tienda, etc.)
        # -------------------------------------------------
        if 'factura' in texto:
            # Detectar estado (pendientes, pagadas, etc.)
            estado = None
            if any(p in texto for p in ['pendiente', 'sin pagar', 'por cobrar', 'adeudo']):
                estado = 'pendiente'
            elif any(p in texto for p in ['pagada', 'cobrada', 'liquidada']):
                estado = 'pagada'
            
            # Detectar tienda/cliente
            tienda_match = None
            for variante, nombre in self.tienda_a_nombre.items():
                if variante in texto:
                    tienda_match = nombre
                    break
            
            if estado or tienda_match:
                mejor_intencion = 'facturas_filtradas'
                mejor_score = 90
                razonamiento = ['facturas_filtradas_detectado']
                if estado:
                    entidades.append(EntidadSmart(
                        tipo='estado_factura',
                        valor=estado,
                        valor_original=estado,
                        confianza=0.9
                    ))
                    razonamiento.append(f'estado={estado}')
                if tienda_match:
                    entidades.append(EntidadSmart(
                        tipo='tienda',
                        valor=tienda_match,
                        valor_original=tienda_match,
                        confianza=0.9,
                        contexto='filtro_tienda'
                    ))
                    razonamiento.append(f'tienda={tienda_match}')
        
        # -------------------------------------------------
        # 0.13C PDF CONTEXTUAL (esos datos, lo anterior, etc.)
        # -------------------------------------------------
        patrones_pdf_contextual = ['esos datos', 'esto en pdf', 'lo anterior', 
                                   'pasalo a pdf', 'generame eso', 'sacame el pdf',
                                   'hazme un pdf', 'pdf de esto', 'exporta esto',
                                   'pdf profesional', 'convierte a pdf']
        if any(p in texto for p in patrones_pdf_contextual) and 'pdf' in texto:
            mejor_intencion = 'pdf_contextual'
            mejor_score = 95
            razonamiento = ['pdf_contextual_detectado']
        
        # -------------------------------------------------
        # 0.14 MANUAL / PROCESO / TUTORIAL
        # -------------------------------------------------
        # Preguntas de "cómo hago X", "cómo creo X", "cómo genero X", etc.
        patrones_manual = ['cómo', 'como', 'proceso para', 'pasos para', 
                          'tutorial', 'guía para', 'procedimiento', 'instrucciones',
                          'cómo hago', 'cómo creo', 'cómo genero', 'cómo registro',
                          'cómo se hace', 'cómo puedo hacer', 'ayuda con', 'ayúdame a']
        # Detectar pregunta de cómo hacer algo
        patrones_como_hacer = [
            'cómo hago', 'como hago', 'cómo creo', 'como creo',
            'cómo genero', 'como genero', 'cómo registro', 'como registro',
            'cómo se hace', 'como se hace', 'cómo puedo hacer', 'como puedo hacer',
            'pasos para', 'procedimiento para', 'proceso para',
            'tutorial de', 'guía de', 'guía para'
        ]
        es_pregunta_como_hacer = any(p in texto for p in patrones_como_hacer)
        
        if es_pregunta_como_hacer:
            # Es claramente una pregunta de "cómo hacer algo" → manual
            mejor_intencion = 'manual_consulta'
            mejor_score = 92
            razonamiento = ['manual_como_hacer_detectado']
            tipo_consulta = TipoConsulta.MANUAL
        elif any(p in texto for p in patrones_manual):
            # Solo si parece una pregunta de procedimiento, no análisis de datos
            palabras_analisis = ['ventas de', 'inventario de', 'mostrar', 'dame', 'cuánto', 'cuantas', 'lista de']
            if not any(a in texto for a in palabras_analisis):
                mejor_intencion = 'manual_consulta'
                mejor_score = 82
                razonamiento = ['manual_detectado']
                tipo_consulta = TipoConsulta.MANUAL
        
        # -------------------------------------------------
        # 0.15 Si detectamos patrón específico, construir respuesta
        # -------------------------------------------------
        if mejor_score >= 80:
            config = self.grafos_intenciones.get(mejor_intencion, {})
            parametros = self._construir_parametros(entidades, analisis)
            
            return IntencionSmart(
                nombre=mejor_intencion,
                confianza=mejor_score / 100,
                tipo_consulta=tipo_consulta,
                especificidad=NivelEspecificidad.ESPECIFICA if entidades else NivelEspecificidad.GENERAL,
                entidades=entidades,
                parametros=parametros,
                accion_principal=config.get('accion', 'consultar'),
                acciones_secundarias=[],
                necesita_contexto=[],
                razonamiento=' | '.join(razonamiento)
            )
        
        # =====================================================
        # FASE 1: ANÁLISIS GENERAL POR GRAFOS
        # =====================================================
        
        # Buscar en grafos de intención
        for nombre_int, config in self.grafos_intenciones.items():
            score = 0
            razones = []
            
            # 1. Match de concepto (peso: 40%)
            if config['concepto'] == concepto:
                score += 40
                razones.append(f"concepto={concepto}")
            elif config['concepto'] == 'general':
                score += 10
            
            # 2. Match de tipo de consulta (peso: 30%)
            if config['tipo'] == tipo_consulta:
                score += 30
                razones.append(f"tipo={tipo_consulta.value}")
            elif tipo_consulta == TipoConsulta.CONSULTA_DATOS:
                score += 10
            
            # 3. Entidades requeridas (peso: 20%)
            entidades_encontradas = [e.tipo for e in entidades]
            requeridas_ok = all(req in entidades_encontradas for req in config['requiere'])
            if requeridas_ok:
                score += 20
                razones.append("entidades_ok")
            elif not config['requiere']:
                score += 15
            
            # 4. Especificidad (peso: 10%)
            if entidades:
                score += min(10, len(entidades) * 2)
                razones.append(f"entidades={len(entidades)}")
            
            if score > mejor_score:
                mejor_score = score
                mejor_intencion = nombre_int
                razonamiento = razones
        
        # =====================================================
        # FASE 2: FALLBACK POR VERBOS DE ACCIÓN
        # =====================================================
        
        if mejor_score < 30:
            for verbo in analisis.verbos_accion:
                for tipo_verbo, lista in self.verbos_accion.items():
                    if verbo in lista:
                        if tipo_verbo == 'explicar':
                            mejor_intencion = 'manual_consulta'
                            razonamiento = ['verbo_explicar']
                        elif tipo_verbo == 'contar':
                            mejor_intencion = f'{concepto}_consulta' if concepto != 'general' else 'ayuda_general'
                            razonamiento = ['verbo_contar']
                        break
        
        if not mejor_intencion:
            mejor_intencion = 'ayuda_general'
            razonamiento = ['default']
        
        # =====================================================
        # CONSTRUIR RESPUESTA
        # =====================================================
        
        parametros = self._construir_parametros(entidades, analisis)
        
        # Calcular especificidad
        if len(entidades) >= 3:
            especificidad = NivelEspecificidad.MUY_ESPECIFICA
        elif len(entidades) >= 2:
            especificidad = NivelEspecificidad.ESPECIFICA
        elif entidades:
            especificidad = NivelEspecificidad.GENERAL
        else:
            especificidad = NivelEspecificidad.VAGA
        
        config = self.grafos_intenciones.get(mejor_intencion, {})
        
        necesita = []
        if config.get('requiere'):
            for req in config['requiere']:
                if req not in [e.tipo for e in entidades]:
                    necesita.append(req)
        
        return IntencionSmart(
            nombre=mejor_intencion,
            confianza=mejor_score / 100,
            tipo_consulta=tipo_consulta,
            especificidad=especificidad,
            entidades=entidades,
            parametros=parametros,
            accion_principal=config.get('accion', 'ayuda'),
            acciones_secundarias=[],
            necesita_contexto=necesita,
            razonamiento=' | '.join(razonamiento)
        )
    
    def _construir_parametros(self, entidades: List[EntidadSmart], 
                              analisis: AnalisisSemantico) -> Dict[str, Any]:
        """Construye diccionario de parámetros desde las entidades."""
        
        params = {}
        
        for entidad in entidades:
            if entidad.tipo == 'periodo':
                params['periodo'] = entidad.valor
                params['periodo_texto'] = entidad.valor_original
            elif entidad.tipo == 'periodo_mes':
                params['mes'] = entidad.valor['mes']
                params['año'] = entidad.valor['año']
            elif entidad.tipo == 'fecha':
                if 'fecha_inicio' not in params:
                    params['fecha_inicio'] = entidad.valor
                else:
                    params['fecha_fin'] = entidad.valor
            elif entidad.tipo == 'ranking':
                params['limite'] = entidad.valor
            elif entidad.tipo == 'numero':
                if entidad.contexto == 'limite':
                    params['limite'] = entidad.valor
                elif entidad.contexto == 'monto':
                    params['monto'] = entidad.valor
            elif entidad.tipo == 'tienda':
                params['tienda'] = entidad.valor
        
        # Agregar modificadores
        if analisis.modificadores:
            params['modificadores'] = analisis.modificadores
        
        return params
    
    def _aplicar_contexto(self, intencion: IntencionSmart) -> IntencionSmart:
        """Aplica contexto conversacional para enriquecer la intención."""
        
        # Si la intención está muy vaga, intentar usar contexto
        if intencion.especificidad == NivelEspecificidad.VAGA:
            
            # Heredar período del contexto 
            if self.contexto.periodo_actual and 'periodo' not in intencion.parametros:
                intencion.parametros['periodo'] = self.contexto.periodo_actual
                intencion.entidades.append(EntidadSmart(
                    tipo='periodo',
                    valor=self.contexto.periodo_actual,
                    valor_original='(del contexto)',
                    confianza=0.7,
                    es_inferida=True
                ))
            
            # Actualizar especificidad
            if intencion.parametros:
                intencion = IntencionSmart(
                    nombre=intencion.nombre,
                    confianza=intencion.confianza,
                    tipo_consulta=intencion.tipo_consulta,
                    especificidad=NivelEspecificidad.GENERAL,
                    entidades=intencion.entidades,
                    parametros=intencion.parametros,
                    accion_principal=intencion.accion_principal,
                    acciones_secundarias=intencion.acciones_secundarias,
                    necesita_contexto=intencion.necesita_contexto,
                    razonamiento=intencion.razonamiento + ' | contexto_aplicado'
                )
        
        return intencion
    
    def _validar_coherencia(self, intencion: IntencionSmart, texto_original: str) -> IntencionSmart:
        """Valida que la intención sea coherente con la consulta."""
        
        # Si la confianza es muy baja, degradar a ayuda
        if intencion.confianza < 0.25:
            return IntencionSmart(
                nombre='ayuda_general',
                confianza=0.5,
                tipo_consulta=TipoConsulta.AYUDA,
                especificidad=NivelEspecificidad.VAGA,
                entidades=[],
                parametros={'consulta_original': texto_original},
                accion_principal='mostrar_ayuda',
                acciones_secundarias=[],
                necesita_contexto=['clarificacion'],
                razonamiento='confianza_baja -> ayuda'
            )
        
        return intencion
    
    def _actualizar_contexto(self, intencion: IntencionSmart):
        """Actualiza el contexto conversacional."""
        
        # Actualizar tema
        config = self.grafos_intenciones.get(intencion.nombre, {})
        if config.get('concepto'):
            self.contexto.tema_actual = config['concepto']
        
        # Actualizar modelo
        if config.get('modelo'):
            self.contexto.modelo_actual = config['modelo']
        
        # Actualizar período si se especificó
        if 'periodo' in intencion.parametros:
            self.contexto.periodo_actual = intencion.parametros['periodo']
        
        # Agregar al historial
        self.contexto.historial_intenciones.append(intencion.nombre)
        if len(self.contexto.historial_intenciones) > 10:
            self.contexto.historial_intenciones.pop(0)
        
        # Guardar entidades
        for entidad in intencion.entidades:
            self.contexto.entidades_mencionadas[entidad.tipo] = entidad.valor
    
    def reiniciar_contexto(self):
        """Reinicia el contexto conversacional."""
        self.contexto = ContextoConversacional()
    
    # ============================================================
    # MÉTODOS DE UTILIDAD
    # ============================================================
    
    def obtener_sugerencias(self, intencion: IntencionSmart) -> List[str]:
        """Genera sugerencias basadas en la intención detectada."""
        
        sugerencias = []
        
        concepto = self.grafos_intenciones.get(intencion.nombre, {}).get('concepto', '')
        
        if concepto == 'ventas':
            sugerencias = [
                "Analizar ventas en detalle",
                "Ver tendencia de ventas",
                "Top 10 productos más vendidos",
                "Mejores clientes del mes"
            ]
        elif concepto == 'inventario':
            sugerencias = [
                "Productos con stock crítico",
                "Rotación de inventario",
                "Recomendaciones de reposición"
            ]
        elif concepto == 'pos':
            sugerencias = [
                "Análisis por método de pago",
                "Ventas por tienda",
                "Ventas por hora"
            ]
        elif intencion.tipo_consulta == TipoConsulta.AYUDA:
            sugerencias = [
                "Ventas de hoy",
                "Stock de productos",
                "Lista de clientes",
                "Predicción de ventas"
            ]
        
        return sugerencias
    
    def explicar_intencion(self, intencion: IntencionSmart) -> str:
        """Genera una explicación legible de la intención detectada."""
        
        partes = []
        partes.append(f"**Intención:** {intencion.nombre}")
        partes.append(f"**Tipo:** {intencion.tipo_consulta.value}")
        partes.append(f"**Especificidad:** {intencion.especificidad.name}")
        partes.append(f"**Confianza:** {intencion.confianza:.0%}")
        
        if intencion.entidades:
            ents = ", ".join([f"{e.tipo}={e.valor}" for e in intencion.entidades[:3]])
            partes.append(f"**Entidades:** {ents}")
        
        if intencion.necesita_contexto:
            partes.append(f"**Necesita:** {', '.join(intencion.necesita_contexto)}")
        
        partes.append(f"**Acción:** {intencion.accion_principal}")
        partes.append(f"**Razonamiento:** {intencion.razonamiento}")
        
        return "\n".join(partes)


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

_cerebro_nlp: Optional[CerebroNLP] = None

def obtener_cerebro_nlp() -> CerebroNLP:
    """Obtiene la instancia global del Cerebro NLP."""
    global _cerebro_nlp
    if _cerebro_nlp is None:
        _cerebro_nlp = CerebroNLP()
    return _cerebro_nlp


def analizar_consulta(texto: str) -> IntencionSmart:
    """Función de conveniencia para analizar una consulta."""
    cerebro = obtener_cerebro_nlp()
    return cerebro.analizar(texto)


# ============================================================
# EXPORTACIONES
# ============================================================

__all__ = [
    'CerebroNLP',
    'IntencionSmart',
    'EntidadSmart',
    'AnalisisSemantico',
    'TipoConsulta',
    'NivelEspecificidad',
    'ContextoConversacional',
    'obtener_cerebro_nlp',
    'analizar_consulta'
]
