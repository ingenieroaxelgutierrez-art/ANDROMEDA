# ============================================================
# MOTOR NLP LOCAL - Procesamiento de Lenguaje Natural
# ============================================================
# Sin dependencias de APIs externas (OpenAI, Claude, etc.)
# Usa modelos locales de spaCy y sentence-transformers
# ============================================================

import re
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import unicodedata

# Intentar importar spaCy (opcional pero mejora el NLP)
try:
    import spacy
    SPACY_DISPONIBLE = True
except ImportError:
    SPACY_DISPONIBLE = False
    print("spaCy no instalado. Usando motor de regex básico.")

# Intentar importar sentence_transformers para embeddings semánticos
from app.logging_config import get_logger
logger = get_logger("services.nlp.motor_nlp")

try:
    from sentence_transformers import SentenceTransformer, util
    EMBEDDINGS_DISPONIBLE = True
except ImportError:
    EMBEDDINGS_DISPONIBLE = False


@dataclass
class EntidadExtraida:
    """Representa una entidad extraída del texto."""
    tipo: str           # fecha, modelo, campo, numero, tienda, etc.
    valor: str          # valor original
    valor_normalizado: any  # valor procesado
    confianza: float = 1.0
    posicion: Tuple[int, int] = (0, 0)


@dataclass
class IntencionDetectada:
    """Representa una intención detectada con sus entidades."""
    nombre: str                          # consultar_ventas, describir_modelo, etc.
    confianza: float                     # 0.0 - 1.0
    entidades: List[EntidadExtraida] = field(default_factory=list)
    parametros: Dict = field(default_factory=dict)


class MotorNLP:
    """
    Motor de Procesamiento de Lenguaje Natural local.
    No requiere APIs externas ni conexión a internet.
    """
    
    def __init__(self, usar_spacy: bool = True, usar_embeddings: bool = False):
        """
        Inicializa el motor NLP.
        
        Args:
            usar_spacy: Intentar usar spaCy si está disponible
            usar_embeddings: Usar sentence-transformers para similitud semántica
        """
        self.nlp = None
        self.modelo_embeddings = None
        
        # Cargar spaCy si está disponible
        if usar_spacy and SPACY_DISPONIBLE:
            try:
                self.nlp = spacy.load("es_core_news_sm")
                print("spaCy cargado (es_core_news_sm)")
            except OSError:
                try:
                    self.nlp = spacy.load("es_core_news_md")
                    print("spaCy cargado (es_core_news_md)")
                except OSError:
                    print("Modelo de spaCy no encontrado. Instalar: python -m spacy download es_core_news_sm")
        
        # Cargar modelo de embeddings para búsqueda semántica
        if usar_embeddings and EMBEDDINGS_DISPONIBLE:
            try:
                # Modelo multilingüe pequeño y eficiente
                self.modelo_embeddings = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                print("Modelo de embeddings cargado")
            except Exception as e:
                print(f"No se pudo cargar modelo de embeddings: {e}")
        
        # Definir patrones de intenciones
        self._definir_intenciones()
        
        # Definir patrones de entidades
        self._definir_patrones_entidades()
        
        # Vocabulario de sinónimos
        self._definir_sinonimos()
        
        # Modelos de Odoo conocidos
        self._definir_modelos_odoo()
    
    def _definir_intenciones(self):
        """Define los patrones para detectar intenciones."""
        self.intenciones = {
            # Consultas de ventas
            'consultar_ventas': {
                'patrones': [
                    r'(cuántas?|cuantas?|total\s+de?)\s*(ventas?|ordenes?|pedidos?)',
                    r'ventas?\s*(de|del|hoy|ayer|mes|semana|año)',
                    r'(mostrar|ver|dame|obtener|consultar)\s*(las?)?\s*ventas?',
                    r'reporte\s*(de)?\s*ventas?',
                    r'(cuánto|cuanto)\s*(se\s*)?(vendió|vendio|ha\s*vendido)',
                    r'monto\s*(total|de)?\s*ventas?',
                ],
                'prioridad': 10,
                'accion': 'ventas'
            },
            
            # Consultas de inventario/stock
            'consultar_inventario': {
                'patrones': [
                    r'(cuánto|cuanto|qué|que)\s*(stock|inventario|existencias?)',
                    r'(stock|inventario|existencias?)\s*(de|del|en)',
                    r'(productos?\s*con|sin)\s*stock',
                    r'(mostrar|ver|dame)\s*(el)?\s*(stock|inventario)',
                    r'(cuántos?|cuantos?)\s*productos?\s*(hay|tenemos|quedan)',
                ],
                'prioridad': 9,
                'accion': 'inventario'
            },
            
            # Consultas de clientes
            'consultar_clientes': {
                'patrones': [
                    r'(cuántos?|cuantos?)\s*clientes?',
                    r'(lista|listado|mostrar|ver)\s*(de)?\s*clientes?',
                    r'clientes?\s*(activos?|nuevos?|del?\s*mes)',
                    r'información\s*(de|del)\s*cliente',
                    r'(buscar|encontrar)\s*cliente',
                ],
                'prioridad': 8,
                'accion': 'clientes'
            },
            
            # Consultas de productos
            'consultar_productos': {
                'patrones': [
                    r'(cuántos?|cuantos?)\s*productos?',
                    r'(lista|catálogo|catalogo)\s*(de)?\s*productos?',
                    r'(buscar|encontrar)\s*(un)?\s*producto',
                    r'(información|info|datos?)\s*(de|del)\s*producto',
                    r'productos?\s*(activos?|disponibles?)',
                ],
                'prioridad': 8,
                'accion': 'productos'
            },
            
            # Punto de Venta (POS)
            'consultar_pos': {
                'patrones': [
                    r'(tickets?|pos|punto\s*de\s*venta)',
                    r'ventas?\s*(en\s*)?(tienda|sucursal|pos)',
                    r'(cuántos?|cuantos?)\s*tickets?',
                    r'reporte\s*(de)?\s*(pos|tienda)',
                    r'(caja|cajas|sesión|sesiones?)\s*(de)?\s*pos',
                ],
                'prioridad': 9,
                'accion': 'pos'
            },
            
            # Explorar estructura (modelos y campos)
            'describir_modelo': {
                'patrones': [
                    r'(qué|que|cuáles|cuales)\s*(son\s*los?)?\s*campos?\s*(de|del|tiene)',
                    r'(describir|describe|explicar|estructura)\s*(el)?\s*(modelo)?',
                    r'(campos?|atributos?|propiedades?)\s*(de|del)\s*(\w+\.?\w*)',
                    r'cómo\s*(es|está)\s*(estructurado|compuesto)',
                    r'(muéstrame|muestrame|ver)\s*(los)?\s*campos?',
                ],
                'prioridad': 7,
                'accion': 'describir'
            },
            
            # Listar modelos
            'listar_modelos': {
                'patrones': [
                    r'(qué|que|cuáles|cuales)\s*(son\s*los?)?\s*modelos?',
                    r'(listar?|mostrar|ver)\s*(los)?\s*modelos?',
                    r'(tablas?|entidades?)\s*(disponibles?|hay)',
                    r'modelos?\s*(de|para|relacionados?)',
                ],
                'prioridad': 6,
                'accion': 'modelos'
            },
            
            # Buscar campo
            'buscar_campo': {
                'patrones': [
                    r'(buscar|encontrar|dónde|donde)\s*(está|esta)?\s*(el)?\s*campo',
                    r'(en\s*qué|en\s*que)\s*(modelo|tabla)\s*(está|esta)',
                    r'campo\s*(llamado|que\s*se\s*llama)',
                ],
                'prioridad': 6,
                'accion': 'buscar_campo'
            },
            
            # Generar reporte
            'generar_reporte': {
                'patrones': [
                    r'(generar?|crear?|hacer?|exportar?)\s*(un)?\s*(reporte|informe|excel|pdf)',
                    r'(descargar?|bajar?)\s*(un)?\s*(reporte|datos?|excel)',
                    r'reporte\s*(de|del|para|en)',
                    r'(exportar?|guardar?)\s*(a|en)?\s*(excel|csv|pdf)',
                ],
                'prioridad': 10,
                'accion': 'reporte'
            },
            
            # Estadísticas y resumen
            'resumen_sistema': {
                'patrones': [
                    r'(resumen|estadísticas?|estadisticas?|dashboard)',
                    r'(estado|situación|situacion)\s*(del)?\s*(sistema|odoo)',
                    r'(cómo|como)\s*(está|esta|va)\s*(el)?\s*(negocio|sistema)',
                    r'(números|numeros|métricas|metricas)\s*(generales?)?',
                ],
                'prioridad': 5,
                'accion': 'resumen'
            },
            
            # Comparativas
            'comparar': {
                'patrones': [
                    r'compara(r|ción|tiva|tivo)?',
                    r'(diferencia|versus|vs)\s*(entre)?',
                    r'(mejor|peor)\s*(que|vs)',
                    r'(este|esta)\s*(mes|semana|año)\s*(vs|contra|versus)',
                ],
                'prioridad': 8,
                'accion': 'comparar'
            },
            
            # Análisis de datos
            'analizar': {
                'patrones': [
                    r'^(analiza|análisis|analisis|analizame)',
                    r'(analizar?|análisis)\s*(las?|los?|el|la)?\s*(ventas?|datos?|inventario|stock|pos|tickets?)',
                    r'(estadísticas?|estadisticas?|stats)\s*(de|del)',
                    r'(insights?|métricas?|metricas?|kpis?)',
                    r'dame\s*(un)?\s*(análisis|analisis)',
                    r'análisis\s*(de|del)',
                ],
                'prioridad': 12,
                'accion': 'analizar'
            },
            
            # Top productos
            'top_productos': {
                'patrones': [
                    r'(top|mejores?|más\s*vendidos?|mas\s*vendidos?)',
                    r'productos?\s*(top|populares?|estrella)',
                    r'(ranking|rank)\s*(de)?\s*productos?',
                    r'qué\s*(productos?|artículos?)\s*(se)?\s*vende(n)?\s*más',
                    r'productos?\s*más\s*vendidos?',
                ],
                'prioridad': 11,
                'accion': 'top_productos'
            },
            
            # Tendencias
            'tendencia': {
                'patrones': [
                    r'tendencia(s)?',
                    r'(cómo|como)\s*(van|están|evolucionan)\s*(las)?\s*(ventas?|datos?)',
                    r'(evolución|evolucion|progreso|avance)\s*(de)?',
                    r'(histórico|historico|historial)\s*(de)?',
                    r'(semana|mes)\s*(a|vs)\s*(semana|mes)',
                ],
                'prioridad': 11,
                'accion': 'tendencia'
            },
            
            # Ayuda
            'ayuda': {
                'patrones': [
                    r'^(ayuda|help|qué\s*puedo|que\s*puedo|comandos?)$',
                    r'(cómo|como)\s*(funciona|uso|usar)',
                    r'(qué|que)\s*(puedes?|sabes?)\s*hacer',
                ],
                'prioridad': 1,
                'accion': 'ayuda'
            },
            
            # Saludo
            'saludo': {
                'patrones': [
                    r'^(hola|buenos?\s*días?|buenas?\s*tardes?|buenas?\s*noches?|hey|hi)$',
                    r'^(qué\s*tal|que\s*tal|cómo\s*estás|como\s*estas)$',
                ],
                'prioridad': 0,
                'accion': 'saludo'
            },
        }
    
    def _definir_patrones_entidades(self):
        """Define patrones regex para extraer entidades."""
        self.patrones_entidades = {
            # Fechas
            'fecha': [
                # Relativas
                (r'\bhoy\b', lambda m: datetime.now().strftime('%Y-%m-%d'), 'relativa'),
                (r'\bayer\b', lambda m: (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), 'relativa'),
                (r'\bmañana\b', lambda m: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'), 'relativa'),
                (r'\b(esta|este)\s*semana\b', lambda m: 'semana_actual', 'periodo'),
                (r'\b(este|esta)\s*mes\b', lambda m: 'mes_actual', 'periodo'),
                (r'\b(este|esta)\s*año\b', lambda m: 'año_actual', 'periodo'),
                (r'\bmes\s*pasado\b', lambda m: 'mes_anterior', 'periodo'),
                (r'\baño\s*pasado\b', lambda m: 'año_anterior', 'periodo'),
                (r'\bsemana\s*pasada\b', lambda m: 'semana_anterior', 'periodo'),
                (r'\búltimos?\s*(\d+)\s*(días?|semanas?|meses?)\b', self._calcular_ultimos, 'rango'),
                # Absolutas
                (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', self._parsear_fecha_dmy, 'absoluta'),
                (r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b', self._parsear_fecha_ymd, 'absoluta'),
            ],
            
            # Números
            'numero': [
                (r'\b(\d+(?:,\d{3})*(?:\.\d+)?)\b', lambda m: float(m.group(1).replace(',', '')), 'decimal'),
                (r'\b(\d+)\s*(pesos?|mxn|\$|usd|dólares?|dolares?)\b', lambda m: float(m.group(1)), 'moneda'),
            ],
            
            # Modelos de Odoo
            'modelo': [
                (r'\b(sale\.order(?:\.line)?)\b', lambda m: m.group(1), 'ventas'),
                (r'\b(pos\.order(?:\.line)?)\b', lambda m: m.group(1), 'pos'),
                (r'\b(product\.(?:product|template|category))\b', lambda m: m.group(1), 'productos'),
                (r'\b(stock\.(?:quant|move|picking|location))\b', lambda m: m.group(1), 'inventario'),
                (r'\b(res\.partner)\b', lambda m: m.group(1), 'contactos'),
                (r'\b(account\.(?:move|move\.line|account))\b', lambda m: m.group(1), 'contabilidad'),
                (r'\b(hr\.(?:employee|department))\b', lambda m: m.group(1), 'rrhh'),
                (r'\b(purchase\.order(?:\.line)?)\b', lambda m: m.group(1), 'compras'),
            ],
            
            # Tiendas/Sucursales
            'tienda': [
                (r'\b(aeropuerto|cuautla|irapuato|moral|morelia|puebla|slp|san\s*luis|lomas|antenas|toreo)\b', 
                 lambda m: m.group(1).lower(), 'sucursal'),
            ],
            
            # Estados
            'estado': [
                (r'\b(completado|confirmado|cancelado|borrador|pagado|enviado|entregado)\b',
                 lambda m: m.group(1).lower(), 'estado_orden'),
            ],
            
            # Campos de ordenamiento
            'orden': [
                (r'\b(mayor|menor|más|menos|primeros?|últimos?)\b',
                 lambda m: m.group(1).lower(), 'ordenamiento'),
                (r'\b(ascendente|descendente|asc|desc)\b',
                 lambda m: m.group(1).lower(), 'direccion'),
            ],
            
            # Límites
            'limite': [
                (r'\b(top|primeros?|últimos?)\s*(\d+)\b',
                 lambda m: int(m.group(2)), 'cantidad'),
            ],
        }
    
    def _definir_sinonimos(self):
        """Define sinónimos para normalizar consultas."""
        self.sinonimos = {
            # Ventas
            'ventas': ['venta', 'ventas', 'ordenes', 'orden', 'pedidos', 'pedido', 'compras_cliente'],
            'factura': ['factura', 'facturas', 'cfdi', 'comprobante'],
            
            # Productos
            'producto': ['producto', 'productos', 'articulo', 'artículos', 'items', 'mercancia'],
            'stock': ['stock', 'inventario', 'existencias', 'existencia', 'disponible'],
            
            # Clientes
            'cliente': ['cliente', 'clientes', 'contacto', 'contactos', 'partner'],
            
            # Tiempo
            'hoy': ['hoy', 'ahora', 'actual', 'presente'],
            'mes': ['mes', 'mensual', 'mensualmente'],
            'año': ['año', 'anual', 'anualmente'],
            
            # Acciones
            'mostrar': ['mostrar', 'ver', 'listar', 'dame', 'dime', 'muestra', 'enseña', 'obtener'],
            'cuantos': ['cuántos', 'cuantos', 'cuántas', 'cuantas', 'cantidad', 'total', 'número'],
            'generar': ['generar', 'crear', 'hacer', 'exportar', 'descargar', 'guardar'],
        }
        
        # Crear índice inverso
        self.sinonimo_a_canonical = {}
        for canonical, lista in self.sinonimos.items():
            for sin in lista:
                self.sinonimo_a_canonical[sin.lower()] = canonical
    
    def _definir_modelos_odoo(self):
        """Define mapeo de términos comunes a modelos de Odoo."""
        self.termino_a_modelo = {
            # Ventas
            'ventas': 'sale.order',
            'venta': 'sale.order',
            'ordenes': 'sale.order',
            'pedidos': 'sale.order',
            'lineas_venta': 'sale.order.line',
            
            # POS
            'tickets': 'pos.order',
            'ticket': 'pos.order',
            'pos': 'pos.order',
            'punto_venta': 'pos.order',
            'cajas': 'pos.session',
            'sesiones': 'pos.session',
            
            # Productos
            'productos': 'product.product',
            'producto': 'product.product',
            'articulos': 'product.product',
            'plantillas': 'product.template',
            'categorias': 'product.category',
            
            # Inventario
            'stock': 'stock.quant',
            'inventario': 'stock.quant',
            'existencias': 'stock.quant',
            'movimientos': 'stock.move',
            'transferencias': 'stock.picking',
            'ubicaciones': 'stock.location',
            'almacenes': 'stock.warehouse',
            
            # Contactos
            'clientes': 'res.partner',
            'cliente': 'res.partner',
            'proveedores': 'res.partner',
            'contactos': 'res.partner',
            
            # Contabilidad
            'facturas': 'account.move',
            'factura': 'account.move',
            'asientos': 'account.move.line',
            'cuentas': 'account.account',
            'diarios': 'account.journal',
            
            # Compras
            'compras': 'purchase.order',
            'compra': 'purchase.order',
            
            # RRHH
            'empleados': 'hr.employee',
            'empleado': 'hr.employee',
            'departamentos': 'hr.department',
        }
    
    def _calcular_ultimos(self, match) -> str:
        """Calcula el rango de fechas para 'últimos X días/semanas/meses'."""
        cantidad = int(match.group(1))
        unidad = match.group(2).lower()
        
        if 'día' in unidad or 'dia' in unidad:
            delta = timedelta(days=cantidad)
        elif 'semana' in unidad:
            delta = timedelta(weeks=cantidad)
        elif 'mes' in unidad:
            delta = timedelta(days=cantidad * 30)  # Aproximación
        else:
            delta = timedelta(days=cantidad)
        
        fecha_inicio = (datetime.now() - delta).strftime('%Y-%m-%d')
        return f"desde:{fecha_inicio}"
    
    def _parsear_fecha_dmy(self, match) -> str:
        """Parsea fecha en formato DD/MM/YYYY."""
        dia, mes, año = match.groups()
        if len(año) == 2:
            año = '20' + año
        return f"{año}-{mes.zfill(2)}-{dia.zfill(2)}"
    
    def _parsear_fecha_ymd(self, match) -> str:
        """Parsea fecha en formato YYYY-MM-DD."""
        año, mes, dia = match.groups()
        return f"{año}-{mes.zfill(2)}-{dia.zfill(2)}"
    
    def normalizar_texto(self, texto: str) -> str:
        """Normaliza el texto para procesamiento."""
        # Convertir a minúsculas
        texto = texto.lower().strip()
        
        # Normalizar caracteres Unicode (ñ, acentos, etc.)
        # Pero mantener caracteres españoles importantes
        
        # Eliminar puntuación excesiva pero mantener signos de pregunta
        texto = re.sub(r'[¡!]+', '', texto)
        texto = re.sub(r'[¿?]+', '', texto)
        texto = re.sub(r'\.{2,}', '.', texto)
        texto = re.sub(r'\s+', ' ', texto)
        
        return texto.strip()
    
    def extraer_entidades(self, texto: str) -> List[EntidadExtraida]:
        """Extrae todas las entidades del texto."""
        entidades = []
        texto_norm = self.normalizar_texto(texto)
        
        for tipo, patrones in self.patrones_entidades.items():
            for patron, extractor, subtipo in patrones:
                for match in re.finditer(patron, texto_norm, re.IGNORECASE):
                    try:
                        valor_norm = extractor(match)
                        entidad = EntidadExtraida(
                            tipo=tipo,
                            valor=match.group(0),
                            valor_normalizado=valor_norm,
                            confianza=0.9,
                            posicion=(match.start(), match.end())
                        )
                        entidades.append(entidad)
                    except Exception:
                        continue
        
        return entidades
    
    def detectar_intencion(self, texto: str) -> IntencionDetectada:
        """
        Detecta la intención principal del usuario.
        
        Args:
            texto: Texto de entrada del usuario
        
        Returns:
            IntencionDetectada con la intención más probable
        """
        texto_norm = self.normalizar_texto(texto)
        mejor_match = None
        mejor_confianza = 0.0
        mejor_prioridad = -1
        
        for nombre, config in self.intenciones.items():
            for patron in config['patrones']:
                match = re.search(patron, texto_norm, re.IGNORECASE)
                if match:
                    # Calcular confianza basada en la cobertura del patrón
                    cobertura = len(match.group(0)) / len(texto_norm)
                    confianza = min(0.5 + cobertura * 0.5, 1.0)
                    prioridad = config['prioridad']
                    
                    # Preferir mayor prioridad, luego mayor confianza
                    if (prioridad > mejor_prioridad or 
                        (prioridad == mejor_prioridad and confianza > mejor_confianza)):
                        mejor_match = nombre
                        mejor_confianza = confianza
                        mejor_prioridad = prioridad
        
        if mejor_match is None:
            # Intento de fallback - buscar palabras clave sueltas
            mejor_match = self._detectar_por_palabras_clave(texto_norm)
            mejor_confianza = 0.5 if mejor_match else 0.0
        
        # Extraer entidades
        entidades = self.extraer_entidades(texto)
        
        # Construir parámetros a partir de entidades
        parametros = self._construir_parametros(entidades, mejor_match)
        
        return IntencionDetectada(
            nombre=mejor_match or 'desconocido',
            confianza=mejor_confianza,
            entidades=entidades,
            parametros=parametros
        )
    
    def _detectar_por_palabras_clave(self, texto: str) -> Optional[str]:
        """Detecta intención por palabras clave sueltas."""
        palabras = set(texto.split())
        
        # Mapeo de palabras clave a intenciones
        keywords = {
            'consultar_ventas': {'ventas', 'venta', 'vendido', 'vendieron'},
            'consultar_inventario': {'stock', 'inventario', 'existencias'},
            'consultar_clientes': {'cliente', 'clientes', 'contacto'},
            'consultar_productos': {'producto', 'productos', 'articulo'},
            'consultar_pos': {'ticket', 'tickets', 'pos', 'tienda'},
            'listar_modelos': {'modelos', 'modelo', 'tablas', 'entidades'},
            'generar_reporte': {'reporte', 'excel', 'exportar', 'descargar'},
        }
        
        for intencion, kws in keywords.items():
            if palabras & kws:
                return intencion
        
        return None
    
    def _construir_parametros(self, entidades: List[EntidadExtraida], 
                               intencion: str) -> Dict:
        """Construye parámetros estructurados a partir de entidades."""
        params = {}
        
        for ent in entidades:
            if ent.tipo == 'fecha':
                if 'fecha_inicio' not in params:
                    params['fecha_inicio'] = ent.valor_normalizado
                else:
                    params['fecha_fin'] = ent.valor_normalizado
            
            elif ent.tipo == 'modelo':
                params['modelo'] = ent.valor_normalizado
            
            elif ent.tipo == 'tienda':
                params['tienda'] = ent.valor_normalizado
            
            elif ent.tipo == 'limite':
                params['limite'] = ent.valor_normalizado
            
            elif ent.tipo == 'numero':
                params['valor'] = ent.valor_normalizado
        
        # Inferir modelo si no se especificó
        if 'modelo' not in params and intencion:
            params['modelo'] = self._inferir_modelo(intencion)
        
        return params
    
    def _inferir_modelo(self, intencion: str) -> str:
        """Infiere el modelo de Odoo basado en la intención."""
        mapeo = {
            'consultar_ventas': 'sale.order',
            'consultar_inventario': 'stock.quant',
            'consultar_clientes': 'res.partner',
            'consultar_productos': 'product.product',
            'consultar_pos': 'pos.order',
        }
        return mapeo.get(intencion, '')
    
    def obtener_modelo_por_termino(self, termino: str) -> Optional[str]:
        """Obtiene el modelo de Odoo correspondiente a un término."""
        termino = termino.lower().strip()
        return self.termino_a_modelo.get(termino)
    
    def calcular_similitud(self, texto1: str, texto2: str) -> float:
        """
        Calcula similitud semántica entre dos textos.
        Requiere sentence-transformers instalado.
        """
        if self.modelo_embeddings:
            emb1 = self.modelo_embeddings.encode(texto1, convert_to_tensor=True)
            emb2 = self.modelo_embeddings.encode(texto2, convert_to_tensor=True)
            return float(util.cos_sim(emb1, emb2)[0][0])
        else:
            # Fallback: similitud por palabras comunes (Jaccard)
            set1 = set(texto1.lower().split())
            set2 = set(texto2.lower().split())
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            return intersection / union if union > 0 else 0.0


# ============================================================
# FUNCIONES DE UTILIDAD
# ============================================================

def inicializar_motor_nlp(ligero: bool = True) -> MotorNLP:
    """
    Inicializa el motor NLP con la configuración apropiada.
    
    Args:
        ligero: True para versión ligera sin embeddings pesados
    """
    return MotorNLP(usar_spacy=True, usar_embeddings=not ligero)


# ============================================================
# PRUEBAS
# ============================================================

if __name__ == "__main__":
    print("Probando Motor NLP...")
    print("=" * 60)
    
    motor = MotorNLP(usar_spacy=True, usar_embeddings=False)
    
    # Pruebas de intenciones
    pruebas = [
        "¿Cuántas ventas hay hoy?",
        "Mostrar el inventario de productos",
        "¿Cuáles son los campos de sale.order?",
        "Generar reporte de ventas del mes",
        "Tickets de la tienda Morelia",
        "¿Cuántos clientes activos tenemos?",
        "Dame las ventas de los últimos 7 días",
        "¿Qué modelos hay disponibles?",
        "Hola, ¿cómo estás?",
    ]
    
    for prueba in pruebas:
        print(f"\nInput: {prueba}")
        resultado = motor.detectar_intencion(prueba)
        print(f"   → Intención: {resultado.nombre} (confianza: {resultado.confianza:.2f})")
        if resultado.entidades:
            print(f"   → Entidades: {[(e.tipo, e.valor) for e in resultado.entidades]}")
        if resultado.parametros:
            print(f"   → Parámetros: {resultado.parametros}")
