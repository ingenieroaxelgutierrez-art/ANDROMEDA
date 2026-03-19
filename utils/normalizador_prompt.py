# ============================================================
# NORMALIZADOR DE PROMPTS - Andrómeda
# ============================================================
# Pre-procesa el texto del usuario ANTES de que llegue al NLP.
# Corrige typos, normaliza sinónimos, expande abreviaciones,
# limpia ruido y devuelve texto listo para detección de intención.
# ============================================================

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from app.logging_config import get_logger
logger = get_logger("utils.normalizador_prompt")


@dataclass
class ResultadoNormalizacion:
    """Resultado del proceso de normalización."""
    texto_original: str
    texto_normalizado: str
    correcciones: List[str] = field(default_factory=list)
    fragmentos_clave: List[str] = field(default_factory=list)
    confianza_interpretacion: float = 1.0


class NormalizadorPrompt:
    """
    Normaliza prompts de usuario antes del pipeline NLP.

    Pipeline:
        1. Limpieza básica (whitespace, puntuación excesiva)
        2. Corrección de typos comunes del dominio
        3. Normalización de acentos (agrega los que faltan)
        4. Expansión de abreviaciones
        5. Traducción de coloquialismos a lenguaje de dominio
        6. Normalización de sinónimos a términos canónicos
        7. Extracción de fragmentos clave de intención
    """

    # ── Typos comunes en español de negocio ──────────────────────
    CORRECCIONES_TYPOS: Dict[str, str] = {
        # Ventas
        'venats': 'ventas', 'vetas': 'ventas', 'benta': 'venta',
        'bentas': 'ventas', 'vntas': 'ventas', 'ventsa': 'ventas',
        'venntas': 'ventas', 'vtas': 'ventas', 'ventass': 'ventas',
        # Inventario
        'inbentario': 'inventario', 'inventaro': 'inventario',
        'imventario': 'inventario', 'invetario': 'inventario',
        'inventrio': 'inventario', 'invntario': 'inventario',
        'imbentario': 'inventario',
        # Productos
        'prodcutos': 'productos', 'producots': 'productos',
        'prductos': 'productos', 'porductos': 'productos',
        'proudctos': 'productos', 'prodcuts': 'productos',
        # Facturas
        'factruas': 'facturas', 'factras': 'facturas',
        'faturas': 'facturas', 'factuars': 'facturas',
        'fcturas': 'facturas', 'fatura': 'factura',
        # Clientes
        'clietes': 'clientes', 'cleintes': 'clientes',
        'clents': 'clientes', 'clinetes': 'clientes',
        'clienes': 'clientes', 'cilentes': 'clientes',
        # Tendencia
        'tenedncia': 'tendencia', 'tendncia': 'tendencia',
        'tendecia': 'tendencia', 'tndencia': 'tendencia',
        'tendensia': 'tendencia', 'tendencai': 'tendencia',
        # Análisis
        'analsis': 'analisis', 'anlaisis': 'analisis',
        'anilisis': 'analisis', 'anlaiss': 'analisis',
        'anlisis': 'analisis', 'analissi': 'analisis',
        # Proveedores
        'provedores': 'proveedores', 'proovedores': 'proveedores',
        'proveeedores': 'proveedores', 'probeedores': 'proveedores',
        # Empleados
        'empleaods': 'empleados', 'empelados': 'empleados',
        'emeplados': 'empleados', 'empleadso': 'empleados',
        # Reporte
        'repote': 'reporte', 'repotre': 'reporte', 'rporte': 'reporte',
        'reorte': 'reporte', 'reoprte': 'reporte',
        # Estadísticas
        'estadisitcas': 'estadisticas', 'estadisiticas': 'estadisticas',
        'estadistcias': 'estadisticas', 'estadisitcas': 'estadisticas',
        # Predicción
        'prediccion': 'prediccion', 'prdeccion': 'prediccion',
        'preddicion': 'prediccion', 'prediccoin': 'prediccion',
        # Presupuesto
        'presupesto': 'presupuesto', 'presuepuesto': 'presupuesto',
        'presupusto': 'presupuesto',
        # Otros
        'ingrsos': 'ingresos', 'ingersos': 'ingresos',
        'compras': 'compras', 'copras': 'compras', 'comprsa': 'compras',
        'nomnia': 'nomina', 'nimina': 'nomina', 'nonima': 'nomina',
        'dsahboard': 'dashboard', 'dashbaord': 'dashboard',
        'auidtoria': 'auditoria', 'audtioria': 'auditoria',
        'rotacion': 'rotacion', 'rotaicón': 'rotacion',
        'proyeccion': 'proyeccion', 'proyecion': 'proyeccion',
        'rentabiliad': 'rentabilidad', 'rentbilidad': 'rentabilidad',
        'margne': 'margen', 'margenn': 'margen', 'amrgen': 'margen',
    }

    # ── Abreviaciones comunes ────────────────────────────────────
    ABREVIACIONES: Dict[str, str] = {
        'inv': 'inventario', 'fac': 'facturas', 'facs': 'facturas',
        'prod': 'productos', 'prods': 'productos',
        'cli': 'clientes', 'clis': 'clientes',
        'prov': 'proveedores', 'provs': 'proveedores',
        'emp': 'empleados', 'emps': 'empleados',
        'dpto': 'departamento', 'depto': 'departamento',
        'rh': 'recursos humanos', 'rrhh': 'recursos humanos',
        'pdv': 'punto de venta', 'tpv': 'punto de venta',
        'cxc': 'cuentas por cobrar', 'cxp': 'cuentas por pagar',
        'stk': 'stock', 'qty': 'cantidad',
        'ppto': 'presupuesto',
        'fact': 'facturacion', 'factu': 'facturacion',
        'pto': 'punto',
    }

    # ── Coloquialismos/Lenguaje informal → canónico ──────────────
    COLOQUIALISMOS: Dict[str, str] = {
        # Dinero
        'plata': 'dinero', 'lana': 'dinero', 'billete': 'dinero',
        'feria': 'dinero', 'varo': 'dinero', 'varos': 'dinero',
        # Acción
        'jala': 'funciona', 'no jala': 'no funciona',
        'truena': 'falla', 'se cayó': 'no funciona',
        # Pedidos
        'me urge': 'urgente', 'ahorita': 'ahora',
        'al rato': 'después', 'nel': 'no', 'simon': 'sí',
        'sale': 'ok', 'orale': 'ok', 'jalón': 'ok',
        # Preguntas informales
        'q onda': 'qué hay', 'khe': 'qué', 'ke': 'qué', 'hala': 'hola', 'halo': 'hola',
        'k': 'qué', 'xq': 'por qué', 'xk': 'por qué',
        'pq': 'por qué', 'x': 'por', 'pa': 'para',
        'tmb': 'también', 'tb': 'también',
        'dnd': 'dónde', 'cm': 'cómo', 'cmo': 'cómo',
        'cuanto': 'cuánto', 'cuantas': 'cuántas', 'cuantos': 'cuántos',
        'como': 'cómo', 'cual': 'cuál', 'cuales': 'cuáles',
        'donde': 'dónde', 'cuando': 'cuándo',
    }

    # ── Contextos de "cómo" que son DATOS vs MANUAL ──────────────
    # Si después de "cómo" vienen estas palabras → consulta de DATOS
    COMO_ES_DATOS = {
        'van', 'va', 'vamos', 'están', 'esta', 'estan', 'anda',
        'sigue', 'siguen', 'quedó', 'quedo', 'fue', 'fueron',
        'le fue', 'nos fue', 'va el', 'van las', 'van los',
        'está el', 'están las', 'va la',
    }

    # Si después de "cómo" vienen estas palabras → procedimiento/manual
    COMO_ES_MANUAL = {
        'hacer', 'hago', 'creo', 'crear', 'cancelo', 'cancelar',
        'configuro', 'configurar', 'instalo', 'instalar', 'activo',
        'activar', 'desactivo', 'desactivar', 'modifico', 'modificar',
        'elimino', 'eliminar', 'borro', 'borrar', 'registro',
        'registrar', 'genero', 'cambio', 'cambiar',
        'puedo crear', 'puedo cancelar', 'puedo hacer',
        'se hace', 'se crea', 'se cancela', 'se configura',
    }

    # ── Palabras de relleno que no aportan a la intención ────────
    STOPWORDS_NEGOCIO = {
        'por favor', 'porfa', 'plis', 'please', 'gracias', 'oye',
        'hey', 'eh', 'mira', 'bueno', 'este', 'pues', 'aver',
        'a ver', 'mm', 'mmm', 'ok', 'okey', 'okay', 'aja',
        'verdad', 'cierto', 'sabes', 'sabes que', 'fíjate',
        'fijate', 'disculpa', 'perdón', 'perdon', 'oiga',
        'necesito que', 'quiero que', 'me puedes', 'podrías',
        'podrias', 'sería', 'seria', 'quisiera',
    }

    def __init__(self):
        # Pre-compilar regex de abreviaciones (word boundary)
        self._re_abreviaciones = {
            re.compile(r'\b' + re.escape(abr) + r'\b', re.IGNORECASE): expansion
            for abr, expansion in self.ABREVIACIONES.items()
        }
        # Pre-compilar regex de coloquialismos
        self._re_coloquialismos = {
            re.compile(r'\b' + re.escape(col) + r'\b', re.IGNORECASE): reemplazo
            for col, reemplazo in self.COLOQUIALISMOS.items()
        }

    def normalizar(self, texto: str) -> ResultadoNormalizacion:
        """
        Pipeline completo de normalización.

        Args:
            texto: Prompt crudo del usuario

        Returns:
            ResultadoNormalizacion con texto limpio y metadatos
        """
        original = texto
        correcciones: List[str] = []

        # 1. Limpieza básica
        texto = self._limpiar_basico(texto)

        # 2. Corregir typos
        texto, typos_corregidos = self._corregir_typos(texto)
        correcciones.extend(typos_corregidos)

        # 3. Expandir abreviaciones
        texto, abrevs = self._expandir_abreviaciones(texto)
        correcciones.extend(abrevs)

        # 4. Traducir coloquialismos
        texto, coloquiales = self._traducir_coloquialismos(texto)
        correcciones.extend(coloquiales)

        # 5. Normalizar acentos interrogativos
        texto = self._normalizar_acentos_interrogativos(texto)

        # 6. Limpiar stopwords de relleno (sin perder sentido)
        texto = self._limpiar_relleno(texto)

        # 7. Normalizar whitespace final
        texto = re.sub(r'\s+', ' ', texto).strip()

        # 8. Extraer fragmentos clave de intención
        fragmentos = self._extraer_fragmentos_clave(texto)

        # Calcular confianza de interpretación
        confianza = 1.0
        if correcciones:
            confianza = max(0.7, 1.0 - len(correcciones) * 0.05)

        return ResultadoNormalizacion(
            texto_original=original,
            texto_normalizado=texto,
            correcciones=correcciones,
            fragmentos_clave=fragmentos,
            confianza_interpretacion=confianza,
        )

    def _limpiar_basico(self, texto: str) -> str:
        """Limpieza básica: whitespace, puntuación excesiva, emojis no útiles."""
        texto = texto.strip()
        # Colapsar múltiples espacios
        texto = re.sub(r'\s+', ' ', texto)
        # Remover puntuación excesiva pero mantener una instancia
        texto = re.sub(r'([?!.])\1+', r'\1', texto)
        # Remover signos de apertura españoles (¿¡) — el NLP no los necesita
        texto = re.sub(r'[¿¡]', '', texto)
        # Lowercase
        texto = texto.lower()
        return texto

    def _corregir_typos(self, texto: str) -> Tuple[str, List[str]]:
        """Corrige typos comunes del dominio de negocio."""
        correcciones = []
        palabras = texto.split()
        resultado = []

        for palabra in palabras:
            # Limpiar la palabra de puntuación para buscar
            limpia = re.sub(r'[.,;:!?]', '', palabra)

            if limpia in self.CORRECCIONES_TYPOS:
                corregida = self.CORRECCIONES_TYPOS[limpia]
                # Preservar puntuación original
                resultado.append(palabra.replace(limpia, corregida))
                correcciones.append(f"typo:{limpia}→{corregida}")
            else:
                # Intentar match por similitud si la palabra es larga
                if len(limpia) >= 5:
                    mejor = self._buscar_typo_cercano(limpia)
                    if mejor:
                        resultado.append(palabra.replace(limpia, mejor))
                        correcciones.append(f"typo~:{limpia}→{mejor}")
                    else:
                        resultado.append(palabra)
                else:
                    resultado.append(palabra)

        return ' '.join(resultado), correcciones

    def _buscar_typo_cercano(self, palabra: str) -> Optional[str]:
        """Busca corrección por distancia de edición simplificada (sin deps externas)."""
        if len(palabra) < 5:
            return None

        mejor_match = None
        mejor_dist = 3  # Máximo 2 cambios permitidos

        for typo, correccion in self.CORRECCIONES_TYPOS.items():
            if abs(len(palabra) - len(typo)) > 2:
                continue
            dist = self._distancia_edicion_rapida(palabra, typo)
            if dist < mejor_dist:
                mejor_dist = dist
                mejor_match = correccion

        return mejor_match

    def _distancia_edicion_rapida(self, s1: str, s2: str) -> int:
        """Distancia de edición simplificada (Levenshtein acotada)."""
        if s1 == s2:
            return 0
        len1, len2 = len(s1), len(s2)
        if abs(len1 - len2) > 2:
            return 99

        # Implementación optimizada con early exit
        if len1 > len2:
            s1, s2 = s2, s1
            len1, len2 = len2, len1

        fila_actual = list(range(len1 + 1))
        for i in range(1, len2 + 1):
            fila_anterior, fila_actual = fila_actual, [i] + [0] * len1
            for j in range(1, len1 + 1):
                costo = 0 if s2[i-1] == s1[j-1] else 1
                fila_actual[j] = min(
                    fila_anterior[j] + 1,      # Eliminar
                    fila_actual[j-1] + 1,       # Insertar
                    fila_anterior[j-1] + costo  # Sustituir
                )
            # Early exit si mínimo de fila > umbral
            if min(fila_actual) > 2:
                return 99

        return fila_actual[len1]

    def _expandir_abreviaciones(self, texto: str) -> Tuple[str, List[str]]:
        """Expande abreviaciones comunes a términos completos."""
        correcciones = []
        for regex, expansion in self._re_abreviaciones.items():
            if regex.search(texto):
                texto = regex.sub(expansion, texto)
                correcciones.append(f"abr:{regex.pattern}→{expansion}")
        return texto, correcciones

    def _traducir_coloquialismos(self, texto: str) -> Tuple[str, List[str]]:
        """Traduce expresiones coloquiales a lenguaje de dominio."""
        correcciones = []
        for regex, reemplazo in self._re_coloquialismos.items():
            if regex.search(texto):
                texto = regex.sub(reemplazo, texto)
                correcciones.append(f"col:{regex.pattern}→{reemplazo}")
        return texto, correcciones

    def _normalizar_acentos_interrogativos(self, texto: str) -> str:
        """
        Agrega acentos a palabras interrogativas cuando faltan.
        Solo en contexto de pregunta (no afirmación).
        """
        # Solo aplicar si parece pregunta
        es_pregunta = any(texto.startswith(p) for p in [
            'como ', 'cuando ', 'cuanto ', 'cuantas ', 'cuantos ',
            'donde ', 'cual ', 'cuales ', 'que ', 'quien ', 'quienes ',
        ]) or texto.endswith('?')

        if es_pregunta:
            reemplazos = {
                r'\bcomo\b': 'cómo', r'\bcuando\b': 'cuándo',
                r'\bcuanto\b': 'cuánto', r'\bcuantas\b': 'cuántas',
                r'\bcuantos\b': 'cuántos', r'\bdonde\b': 'dónde',
                r'\bcual\b': 'cuál', r'\bcuales\b': 'cuáles',
                r'\bque\b': 'qué', r'\bquien\b': 'quién',
                r'\bquienes\b': 'quiénes',
            }
            for patron, reemplazo in reemplazos.items():
                texto = re.sub(patron, reemplazo, texto, count=1)

        return texto

    def _limpiar_relleno(self, texto: str) -> str:
        """Elimina frases de relleno que no aportan al intent."""
        for frase in sorted(self.STOPWORDS_NEGOCIO, key=len, reverse=True):
            texto = re.sub(r'\b' + re.escape(frase) + r'\b', '', texto, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', texto).strip()

    def _extraer_fragmentos_clave(self, texto: str) -> List[str]:
        """
        Extrae los fragmentos clave de intención del texto.
        Prioriza verbos de acción + sustantivos de dominio.
        """
        fragmentos = []

        # Patrones de intención (acción + objeto)
        patrones_intencion = [
            # datos/consulta
            (r'(ventas?\s+(por\s+\w+|de\s+\w+|este\s+\w+|del?\s+\w+))', 'ventas_detalle'),
            (r'(tendencia\s+(de\s+)?\w+)', 'tendencia'),
            (r'(inventario\s+(por\s+\w+|de\s+\w+|actual)?)', 'inventario'),
            (r'(top\s+\d*\s*\w+)', 'ranking'),
            (r'(productos?\s+(más|mas|sin|con)\s+\w+)', 'producto_filtro'),
            (r'(comparar?\s+\w+)', 'comparativa'),
            (r'(predecir?\s+\w+)', 'prediccion'),
            (r'(análisis|analisis)\s+(de\s+)?\w+', 'analisis'),
            (r'(factura|facturas|facturación|facturacion)', 'facturas'),
            (r'(empleados?|nómina|nomina|personal)', 'rrhh'),
            (r'(clientes?\s+(por\s+\w+|más\s+\w+)?)', 'clientes'),
        ]

        for patron, tipo in patrones_intencion:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                fragmentos.append(match.group(0).strip())

        return fragmentos

    def clasificar_tipo_como(self, texto: str) -> str:
        """
        Clasifica si una frase que empieza con 'cómo' es pregunta de DATOS o de MANUAL.

        Returns:
            'datos' | 'manual' | 'ambiguo'
        """
        texto_lower = texto.lower().strip()

        # Eliminar "cómo/como" del inicio
        for prefijo in ['cómo ', 'como ']:
            if texto_lower.startswith(prefijo):
                resto = texto_lower[len(prefijo):]
                break
        else:
            return 'ambiguo'

        # Verificar si lo que sigue es patrón de DATOS
        for patron_datos in self.COMO_ES_DATOS:
            if resto.startswith(patron_datos):
                return 'datos'

        # Verificar si lo que sigue es patrón de MANUAL
        for patron_manual in self.COMO_ES_MANUAL:
            if resto.startswith(patron_manual):
                return 'manual'

        return 'ambiguo'

    def detectar_multiples_intenciones(self, texto: str) -> List[str]:
        """
        Detecta si el usuario pide múltiples cosas en un solo prompt.

        Ej: "dame ventas y también el inventario" → ['ventas', 'inventario']
        """
        # Separadores de intenciones
        separadores = re.split(r'\b(?:y también|y\s+también|y\s+que|además|y\s+de\s+paso|y\s+el|y\s+la|y\s+las|y\s+los|,\s*y|,\s+)\b', texto, flags=re.IGNORECASE)

        if len(separadores) <= 1:
            # Intentar split por "y" si hay conceptos de dominio a ambos lados
            partes = re.split(r'\by\b', texto)
            if len(partes) == 2:
                conceptos_dominio = {
                    'ventas', 'inventario', 'productos', 'clientes', 'facturas',
                    'compras', 'empleados', 'nomina', 'nómina', 'pos', 'caja',
                    'tendencia', 'predicción', 'prediccion', 'margen', 'reporte',
                    'dashboard', 'kpis', 'proveedores', 'crm', 'stock',
                }
                tiene_concepto = [
                    any(c in parte.lower() for c in conceptos_dominio)
                    for parte in partes
                ]
                if all(tiene_concepto):
                    separadores = partes

        return [s.strip() for s in separadores if s.strip()]


# ── Instancia singleton ──────────────────────────────────────────
_normalizador = None

def obtener_normalizador() -> NormalizadorPrompt:
    """Obtiene instancia singleton del normalizador."""
    global _normalizador
    if _normalizador is None:
        _normalizador = NormalizadorPrompt()
    return _normalizador
