# ============================================================
# MOTOR DE EMBEDDINGS - DETECCIÓN DE INTENCIONES SEMÁNTICA
# ============================================================
# Usa sentence-transformers para vectorizar intenciones y
# encontrar la más cercana al input del usuario por similitud
# coseno. Más robusto que keyword matching ante variaciones
# del lenguaje natural.
# ============================================================

import os
import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from app.logging_config import get_logger
logger = get_logger("services.nlp.motor_embeddings")

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_DISPONIBLE = True
except ImportError:
    EMBEDDINGS_DISPONIBLE = False
    logger.warning("sentence-transformers no disponible")

# Ruta para cache de embeddings pre-calculados
CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "embeddings_cache"
CACHE_FILE = CACHE_DIR / "intenciones_embeddings.npz"
META_FILE = CACHE_DIR / "intenciones_meta.json"

# Modelo multilingual ligero (~120MB, <100ms por query)
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class MotorEmbeddings:
    """
    Motor de detección de intenciones basado en embeddings semánticos.
    
    Ventajas sobre keyword matching:
    - Entiende sinónimos y paráfrasis sin definirlos manualmente
    - Tolera errores ortográficos y variaciones coloquiales
    - Captura semántica profunda (ej: "cuánto se vendió" ≈ "total de ventas")
    - Se mejora añadiendo ejemplos, sin cambiar código
    """
    
    def __init__(self, intenciones_map: Dict, umbral_confianza: float = 0.45):
        self.intenciones_map = intenciones_map
        self.umbral = umbral_confianza
        self.modelo = None
        self.embeddings_intenciones = None  # ndarray (N, dim)
        self.etiquetas = []  # lista paralela: nombre de intención
        self.frases = []  # lista paralela: frase original
        self._inicializado = False
        
        if not EMBEDDINGS_DISPONIBLE:
            logger.warning("Motor de embeddings desactivado (falta sentence-transformers)")
            return
        
        self._inicializar()
    
    def _inicializar(self):
        """Carga modelo y genera/carga embeddings de intenciones."""
        try:
            import socket
            timeout_original = socket.getdefaulttimeout()
            socket.setdefaulttimeout(60)
            try:
                self.modelo = SentenceTransformer(MODELO_EMBEDDINGS)
            finally:
                socket.setdefaulttimeout(timeout_original)
            del socket  # Evitar retener referencia
            logger.info(f"Modelo de embeddings cargado: {MODELO_EMBEDDINGS}")
        except Exception as e:
            logger.error(f"Error cargando modelo de embeddings: {e}")
            return
        
        # Intentar cargar desde cache
        if self._cargar_cache():
            self._inicializado = True
            logger.info(f"Embeddings cargados desde cache ({len(self.etiquetas)} frases)")
            return
        
        # Generar embeddings desde intenciones_map
        self._generar_embeddings()
        self._inicializado = True
    
    def _construir_corpus(self) -> Tuple[List[str], List[str]]:
        """
        Construye el corpus de frases y sus etiquetas desde intenciones_map.
        Incluye triggers + frases de ejemplo expandidas para mejor cobertura.
        """
        frases = []
        etiquetas = []
        
        # Ejemplos adicionales para ampliar cobertura semántica
        ejemplos_extra = {
            'ventas_basico': [
                'cuánto vendimos', 'mostrame las ventas', 'dame el total de ventas',
                'ventas del mes', 'cuánto se vendió hoy', 'total vendido',
                'resumen de ventas', 'cuántas ventas hay',
            ],
            'ventas_analisis': [
                'cómo van las ventas', 'analiza las ventas', 'situación de ventas',
                'qué tal están las ventas', 'repórtame ventas', 'análisis comercial',
            ],
            'ventas_top_productos': [
                'qué se vende más', 'cuáles son los más vendidos', 'ranking de productos',
                'productos estrella', 'dame el top de productos',
            ],
            'ventas_top_clientes': [
                'mejores clientes', 'quién compra más', 'clientes principales',
                'ranking de clientes', 'nuestros mejores compradores',
            ],
            'ventas_vendedor': [
                'quién vende más', 'ranking de vendedores', 'productividad vendedores',
                'ventas por vendedor', 'desempeño de vendedores',
            ],
            'ventas_tendencia': [
                'cómo van las ventas en el tiempo', 'tendencia de ventas', 'evolución comercial',
                'histórico de ventas', 'gráfica de ventas',
            ],
            'ventas_comparativa': [
                'comparar ventas', 'hoy contra ayer', 'este mes vs el pasado',
                'comparativa de períodos', 'variación de ventas',
            ],
            'pos_basico': [
                'ventas de tienda', 'ventas del punto de venta', 'tickets de caja',
                'cuánto se vendió en caja', 'resumen pos', 'ventas de mostrador',
            ],
            'pos_metodos_pago': [
                'cómo pagan los clientes', 'efectivo vs tarjeta', 'formas de pago',
                'métodos de pago usados', 'distribución de pagos',
            ],
            'facturas_basico': [
                'facturas emitidas', 'facturación del mes', 'cuántas facturas hay',
                'dame las facturas', 'resumen de facturación',
            ],
            'cxc': [
                'cuánto nos deben', 'cartera de clientes', 'cuentas por cobrar',
                'pendiente de cobro', 'deudores morosos', 'cobranza pendiente',
            ],
            'cxp': [
                'cuánto debemos', 'deudas con proveedores', 'pendiente de pago',
                'cuentas por pagar', 'obligaciones pendientes',
            ],
            'inventario_basico': [
                'cuánto stock hay', 'estado del inventario', 'existencias actuales',
                'qué tenemos en almacén', 'nivel de inventario',
            ],
            'inventario_critico': [
                'productos agotados', 'qué se está acabando', 'faltantes de inventario',
                'productos sin stock', 'alertas de inventario',
            ],
            'inventario_rotacion': [
                'productos que no se mueven', 'rotación de inventario', 'productos lentos',
                'qué no se vende', 'días de inventario',
            ],
            'inventario_prediccion': [
                'cuándo se acaba', 'predicción de stock', 'alerta de agotamiento',
                'cuándo pedir más', 'punto de reorden',
            ],
            'compras_basico': [
                'órdenes de compra', 'compras a proveedores', 'cuánto compramos',
                'pedidos de compra', 'resumen de compras',
            ],
            'rh_empleados': [
                'cuántos empleados', 'listado de personal', 'plantilla actual',
                'directorio de empleados', 'headcount',
            ],
            'rh_nomina': [
                'nómina del mes', 'costo de nómina', 'salarios totales',
                'cuánto pagamos de nómina', 'payroll',
            ],
            'crm_pipeline': [
                'oportunidades abiertas', 'estado del crm', 'leads activos',
                'pipeline de ventas', 'prospectos pendientes',
            ],
            'prediccion_general': [
                'qué va a pasar', 'predicción para el mes', 'proyección de resultados',
                'estimar ventas futuras', 'forecast',
            ],
            'ventas_prediccion': [
                'cuánto vamos a vender', 'proyección de ventas', 'predicción de ventas',
                'forecast de ventas', 'estima las ventas',
            ],
            'flujo_caja': [
                'flujo de efectivo', 'dinero disponible', 'proyección de caja',
                'cuánto efectivo tendremos', 'cash flow',
            ],
            'salud_negocio': [
                'cómo estamos', 'salud general', 'diagnóstico del negocio',
                'score empresarial', 'estado general',
            ],
            'estacionalidad': [
                'patrones de venta', 'mejores días para vender', 'temporada alta',
                'cuándo se vende más', 'estacionalidad',
            ],
            'ayuda': [
                'qué puedes hacer', 'para qué sirves', 'cómo te uso',
                'quién eres', 'muéstrame tus funciones', 'dame una ayuda',
            ],
            'conexion': [
                'estás conectado', 'estado del servidor', 'conexión a odoo',
                'verificar conexión', 'status del sistema',
            ],
            'kpis_por_tienda': [
                'indicadores por tienda', 'rendimiento de tiendas', 'kpis de sucursales',
                'cómo va cada tienda', 'comparativa de tiendas', 'dashboard tiendas',
            ],
            'bi_dashboard': [
                'mostrame indicadores', 'kpis principales', 'tablero de control',
                'métricas del negocio', 'dashboard general',
            ],
            'reporte_excel': [
                'exportar a excel', 'dame un excel', 'descarga los datos',
                'pasa esto a excel', 'generar csv',
            ],
            'pdf_contextual': [
                'genera un pdf', 'pasa esto a pdf', 'imprime en pdf',
                'exporta a pdf', 'dame el reporte pdf',
            ],
            # Auditoría
            'auditoria_nocturna': [
                'auditoría nocturna', 'revisión nocturna', 'auditar datos nocturnos',
            ],
            'semaforo_salud': [
                'semáforo de salud', 'estado general rápido', 'dashboard semáforo',
            ],
            'auditoria_calidad_datos': [
                'revisar calidad datos', 'calidad de la información', 'datos confiables',
            ],
        }
        
        for nombre_intencion, config in self.intenciones_map.items():
            # Triggers definidos
            for trigger in config.get('triggers', []):
                frases.append(trigger)
                etiquetas.append(nombre_intencion)
            
            # Ejemplos extra si existen
            for ejemplo in ejemplos_extra.get(nombre_intencion, []):
                frases.append(ejemplo)
                etiquetas.append(nombre_intencion)
        
        return frases, etiquetas
    
    def _generar_embeddings(self):
        """Genera embeddings para todas las intenciones y guarda cache."""
        self.frases, self.etiquetas = self._construir_corpus()
        
        logger.info(f"Generando embeddings para {len(self.frases)} frases...")
        self.embeddings_intenciones = self.modelo.encode(
            self.frases, 
            show_progress_bar=False,
            normalize_embeddings=True  # pre-normalizar para coseno rápido
        )
        
        # Guardar cache
        self._guardar_cache()
        logger.info(f"Embeddings generados y cacheados ({len(self.frases)} frases, {self.embeddings_intenciones.shape[1]} dims)")
    
    def _guardar_cache(self):
        """Persiste embeddings a disco para carga rápida."""
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(
                str(CACHE_FILE),
                embeddings=self.embeddings_intenciones
            )
            import hashlib
            frases_hash = hashlib.sha256('|'.join(sorted(self.frases)).encode()).hexdigest()[:16]
            meta = {
                'etiquetas': self.etiquetas,
                'frases': self.frases,
                'modelo': MODELO_EMBEDDINGS,
                'num_intenciones': len(set(self.etiquetas)),
                'num_frases': len(self.frases),
                'frases_hash': frases_hash,
            }
            with open(META_FILE, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"No se pudo guardar cache de embeddings: {e}")
    
    def _cargar_cache(self) -> bool:
        """Intenta cargar embeddings desde cache. Retorna True si exitoso."""
        if not CACHE_FILE.exists() or not META_FILE.exists():
            return False
        
        try:
            with open(META_FILE, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            # Validar que el cache corresponde al mismo modelo y mapa de intenciones
            if meta.get('modelo') != MODELO_EMBEDDINGS:
                return False
            
            # Verificar que las intenciones no han cambiado (agregar o quitar invalida)
            intenciones_actuales = set(self.intenciones_map.keys())
            intenciones_cache = set(meta.get('etiquetas', []))
            if intenciones_cache != intenciones_actuales:
                return False
            
            # Verificar que las frases de entrenamiento no cambiaron
            if meta.get('frases_hash'):
                import hashlib
                frases_actuales, _ = self._construir_corpus()
                hash_actual = hashlib.sha256('|'.join(sorted(frases_actuales)).encode()).hexdigest()[:16]
                if hash_actual != meta['frases_hash']:
                    return False
            
            data = np.load(str(CACHE_FILE))
            self.embeddings_intenciones = data['embeddings']
            self.etiquetas = meta['etiquetas']
            self.frases = meta['frases']
            
            if len(self.etiquetas) != self.embeddings_intenciones.shape[0]:
                return False
            
            # Validar dimensionalidad (384 para MiniLM-L12)
            if self.modelo and hasattr(self.modelo, 'get_sentence_embedding_dimension'):
                dim_esperada = self.modelo.get_sentence_embedding_dimension()
                if self.embeddings_intenciones.shape[1] != dim_esperada:
                    logger.warning(f"Dimensionalidad cache ({self.embeddings_intenciones.shape[1]}) != modelo ({dim_esperada})")
                    return False
            
            return True
        except Exception:
            return False
    
    def detectar_intencion(self, mensaje: str) -> Tuple[str, float, List[Tuple[str, float]]]:
        """
        Detecta la intención del mensaje usando similitud semántica.
        
        Args:
            mensaje: Texto del usuario
            
        Returns:
            (intencion_ganadora, confianza, top_5_candidatos)
        """
        if not self._inicializado or self.modelo is None:
            return ('', 0.0, [])
        
        # Vectorizar el input del usuario
        emb_query = self.modelo.encode(
            [mensaje], 
            show_progress_bar=False,
            normalize_embeddings=True
        )  # shape (1, dim)
        
        # Similitud coseno (ya normalizados → dot product)
        scores = np.dot(self.embeddings_intenciones, emb_query.T).flatten()
        
        # Agrupar por intención: tomar el MÁXIMO score de cada intención
        scores_por_intencion: Dict[str, float] = {}
        for idx, (etiqueta, score) in enumerate(zip(self.etiquetas, scores)):
            if etiqueta not in scores_por_intencion or score > scores_por_intencion[etiqueta]:
                scores_por_intencion[etiqueta] = float(score)
        
        # Ordenar por score
        ranking = sorted(scores_por_intencion.items(), key=lambda x: x[1], reverse=True)
        top_5 = ranking[:5]
        
        if not ranking:
            return ('', 0.0, [])
        
        mejor_intencion, mejor_score = ranking[0]
        
        return (mejor_intencion, mejor_score, top_5)
    
    def invalidar_cache(self):
        """Fuerza regeneración de embeddings (llamar si cambia intenciones_map)."""
        try:
            if CACHE_FILE.exists():
                CACHE_FILE.unlink()
            if META_FILE.exists():
                META_FILE.unlink()
        except Exception:
            pass
        self._generar_embeddings()
    
    @property
    def disponible(self) -> bool:
        return self._inicializado and self.modelo is not None


# Singleton
_motor_embeddings: Optional[MotorEmbeddings] = None

def obtener_motor_embeddings(intenciones_map: Dict) -> Optional[MotorEmbeddings]:
    """Obtiene o crea el motor de embeddings singleton."""
    global _motor_embeddings
    if _motor_embeddings is None and EMBEDDINGS_DISPONIBLE:
        _motor_embeddings = MotorEmbeddings(intenciones_map)
    return _motor_embeddings
