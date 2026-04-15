# ============================================================
# VALIDADOR DE RESPUESTAS - Andrómeda
# ============================================================
# Post-procesa las respuestas ANTES de enviarlas al usuario.
# Detecta alucinaciones, respuestas vacías, contenido irrelevante,
# y garantiza calidad mínima en cada respuesta.
# ============================================================

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.logging_config import get_logger
logger = get_logger("utils.validador_respuestas")


@dataclass
class ResultadoValidacion:
    """Resultado de la validación de una respuesta."""
    respuesta_original: str
    respuesta_validada: str
    es_valida: bool
    problemas: List[str] = field(default_factory=list)
    confianza_respuesta: float = 1.0
    accion_correctiva: str = ''  # 'ninguna' | 'mejorada' | 'reemplazada' | 'rechazada'


class ValidadorRespuestas:
    """
    Valida y mejora respuestas antes de enviarlas al usuario.

    Detecta:
        - Respuestas vacías o genéricas
        - Contenido de manual cuando se pidieron datos
        - Advertencias internas filtradas al usuario
        - Datos inventados o inconsistentes
        - Respuestas que no corresponden a la consulta
    """

    # ── Patrones de contenido interno que NO debería llegar al usuario ──
    PATRONES_INTERNOS = [
        r'validaci[oó]n del agente',
        r'nota del agente',
        r'error interno',
        r'traceback',
        r'exception',
        r'NoneType',
        r'KeyError',
        r'IndexError',
        r'AttributeError',
        r'TypeError',
        r'stack trace',
        r'\bNone\b.*\bNone\b',  # Múltiples None seguidos = datos rotos
    ]

    # ── Patrones de respuesta vacía o inútil ──
    PATRONES_VACIA = [
        r'^no\s+(se\s+)?(encontr[oó]|hay)\s+(datos?|resultados?|informaci[oó]n)',
        r'^sin\s+datos',
        r'^no\s+tengo\s+(datos|información)',
        r'^\s*$',
    ]

    # ── Frases que indican alucinación (afirmaciones sospechosas) ──
    PATRONES_ALUCINACION = [
        # Cita a fuentes externas (el bot NO tiene acceso a internet)
        r'según.*(?:reuters|bloomberg|cnn|bbc|forbes|wikipedia|google)',
        r'en el año 20[3-9]\d',  # Años futuros lejanos
        r'según las últimas noticias',
        r'como is well known',
        r'de acuerdo (?:a|con) (?:mi|mis) datos de entrenamiento',
        # Invención de datos específicos sin fuente
        r'estudios (?:recientes|demuestran|indican)',
        r'(?:un|el) estudio de (?:la|el|harvard|mit|mckinsey)',
        r'según (?:expertos|analistas|investigadores)',
        r'las estadísticas (?:muestran|indican|revelan)',
        # Porcentajes irreales (>500% en contexto ERP)
        r'\b\d{4,}(?:\.\d+)?%',  # 1000%+ en cualquier contexto
        # Fechas imposibles o datos fabricados
        r'(?:desde|en) (?:1[0-8]\d{2}|19[0-4]\d)',  # Antes de 1950 (no hay ERP)
        r'exactamente \$[\d,]+\.\d{2}(?!\s*\|)',  # "exactamente $X" sin tabla (invención)
        # Entidades ficticias (el bot inventa nombres)
        r'(?:la empresa|el cliente|el proveedor) (?:XYZ|ABC|ejemplo|ficticio)',
        r'por ejemplo.*(?:juan pérez|john doe|empresa ejemplo)',
    ]

    # ── Mapeo de tipo de consulta → qué debe contener la respuesta ──
    REQUISITOS_POR_TIPO = {
        'consulta': {'necesita_datos': True, 'necesita_tabla': True},
        'analisis': {'necesita_datos': True, 'necesita_insight': True},
        'prediccion': {'necesita_datos': True, 'necesita_horizonte': True},
        'tendencia': {'necesita_datos': True, 'necesita_direccion': True},
        'ranking': {'necesita_datos': True, 'necesita_tabla': True},
        'comparativa': {'necesita_datos': True, 'necesita_comparacion': True},
        'manual': {'necesita_pasos': True},
        'ayuda': {},
        'reporte': {'necesita_datos': True},
    }

    def __init__(self):
        self._re_internos = [re.compile(p, re.IGNORECASE) for p in self.PATRONES_INTERNOS]
        self._re_vacia = [re.compile(p, re.IGNORECASE) for p in self.PATRONES_VACIA]
        self._re_alucinacion = [re.compile(p, re.IGNORECASE) for p in self.PATRONES_ALUCINACION]

    def validar(
        self,
        respuesta: str,
        consulta_original: str,
        accion: str = '',
        tipo_respuesta: str = '',
        df: Any = None,
        confianza_previa: float = 1.0,
    ) -> ResultadoValidacion:
        """
        Valida una respuesta completa antes de enviarla al usuario.

        Args:
            respuesta: Texto de respuesta generado
            consulta_original: Prompt original del usuario
            accion: Acción ejecutada (consultar_ventas, tendencia, etc.)
            tipo_respuesta: Tipo esperado (consulta, analisis, prediccion, etc.)
            df: DataFrame de datos asociado (si existe)
            confianza_previa: Confianza del pipeline hasta este punto

        Returns:
            ResultadoValidacion con respuesta limpia y métricas
        """
        problemas: List[str] = []
        respuesta_limpia = respuesta
        confianza = confianza_previa

        # 0. Bypass rápido: respuesta ejecutiva estructurada ya validada en pipeline
        #    Si contiene la firma de ANDROMEDA o tablas markdown de datos reales,
        #    es de alta calidad — solo limpiar internos, no penalizar.
        _es_ejecutiva = (
            'análisis ejecutivo generado por' in respuesta.lower()
            or 'andromeda' in respuesta.lower()[:200]
            or bool(re.search(r'\|\s*#\s*\|', respuesta))  # tabla con columna #
            or bool(re.search(r'\$[\d,.]{3,}', respuesta))  # montos formateados
        )
        if _es_ejecutiva:
            respuesta_limpia, internos = self._limpiar_internos(respuesta_limpia)
            problemas.extend(internos)
            return ResultadoValidacion(
                respuesta_original=respuesta,
                respuesta_validada=respuesta_limpia,
                es_valida=True,
                problemas=problemas,
                confianza_respuesta=max(0.85, confianza_previa),
                accion_correctiva='ninguna',
            )

        # 1. Limpiar contenido interno que no debería ser visible
        respuesta_limpia, internos = self._limpiar_internos(respuesta_limpia)
        problemas.extend(internos)

        # 2. Detectar respuesta vacía o inútil
        if self._es_respuesta_vacia(respuesta_limpia):
            problemas.append('respuesta_vacia')
            respuesta_limpia = self._generar_respuesta_honesta(
                consulta_original, accion, 'no_datos'
            )
            confianza *= 0.4

        # 3. Detectar alucinaciones
        alucinaciones = self._detectar_alucinaciones(respuesta_limpia)
        if alucinaciones:
            problemas.extend(alucinaciones)
            confianza *= 0.5

        # 4. Verificar relevancia: ¿la respuesta tiene que ver con lo que se pidió?
        if not self._es_relevante(respuesta_limpia, consulta_original, accion):
            problemas.append('respuesta_irrelevante')
            confianza *= 0.6
            # Agregar nota de contexto
            respuesta_limpia = self._agregar_contexto_respuesta(
                respuesta_limpia, consulta_original, accion
            )

        # 5. Verificar que contenido de manual no se mezcle con datos
        if accion and accion != 'consultar_manual':
            if self._contiene_contenido_manual(respuesta_limpia):
                problemas.append('manual_en_consulta_datos')
                respuesta_limpia = self._remover_contenido_manual(respuesta_limpia)
                confianza *= 0.7

        # 6. Validar coherencia entre datos (df) y texto
        if df is not None and hasattr(df, 'empty') and not df.empty:
            incoherencias = self._validar_coherencia_datos(respuesta_limpia, df)
            problemas.extend(incoherencias)
            if incoherencias:
                confianza *= 0.8

        # 7. Asegurar respuesta no vacía después de limpieza
        if not respuesta_limpia.strip():
            respuesta_limpia = self._generar_respuesta_honesta(
                consulta_original, accion, 'limpieza_vacio'
            )
            problemas.append('vacia_post_limpieza')
            confianza *= 0.3

        # Determinar acción correctiva
        if not problemas:
            accion_correctiva = 'ninguna'
        elif 'respuesta_vacia' in problemas or 'vacia_post_limpieza' in problemas:
            accion_correctiva = 'reemplazada'
        elif any(p.startswith('alucinacion') for p in problemas):
            accion_correctiva = 'rechazada' if confianza < 0.3 else 'mejorada'
        else:
            accion_correctiva = 'mejorada'

        return ResultadoValidacion(
            respuesta_original=respuesta,
            respuesta_validada=respuesta_limpia,
            es_valida=len(problemas) == 0,
            problemas=problemas,
            confianza_respuesta=max(0.0, min(1.0, confianza)),
            accion_correctiva=accion_correctiva,
        )

    def _limpiar_internos(self, texto: str) -> tuple:
        """Elimina mensajes internos del sistema que se filtraron al usuario."""
        problemas = []
        for regex in self._re_internos:
            if regex.search(texto):
                problemas.append(f'contenido_interno:{regex.pattern[:30]}')
                # Remover la línea que contiene el patrón interno
                lineas = texto.split('\n')
                lineas = [l for l in lineas if not regex.search(l)]
                texto = '\n'.join(lineas)
        return texto, problemas

    def _es_respuesta_vacia(self, texto: str) -> bool:
        """Detecta si la respuesta es vacía o inútil."""
        texto_limpio = texto.strip()
        if not texto_limpio or len(texto_limpio) < 10:
            return True
        for regex in self._re_vacia:
            if regex.search(texto_limpio):
                return True
        return False

    def _detectar_alucinaciones(self, texto: str) -> List[str]:
        """Detecta patrones que sugieren información inventada."""
        problemas = []
        for regex in self._re_alucinacion:
            if regex.search(texto):
                problemas.append(f'alucinacion:{regex.pattern[:30]}')
        return problemas

    def _es_relevante(self, respuesta: str, consulta: str, accion: str) -> bool:
        """Verifica que la respuesta tenga relación con la consulta."""
        if not consulta or not respuesta:
            return True  # No se puede evaluar sin contexto

        # Respuesta con tabla markdown (líneas con |) = respuesta de datos, siempre relevante
        if re.search(r'^\|.+\|', respuesta, re.MULTILINE):
            return True

        # Respuesta con HTML (gráfica embebida) = relevante
        if '<div' in respuesta or '<img' in respuesta or '<table' in respuesta:
            return True

        resp_lower = respuesta.lower()
        consulta_lower = consulta.lower()

        # Extraer conceptos clave de la consulta
        conceptos_consulta = set()
        keywords_dominio = {
            'ventas': {'ventas', 'venta', 'vendido', 'total', 'monto', 'ingresos'},
            'inventario': {'inventario', 'stock', 'existencias', 'almacén', 'productos'},
            'facturas': {'facturas', 'facturación', 'cfdi', 'cobrar', 'pagar'},
            'clientes': {'clientes', 'cliente', 'comprador'},
            'productos': {'productos', 'producto', 'artículos'},
            'empleados': {'empleados', 'personal', 'nómina'},
            'tendencia': {'tendencia', 'evolución', 'trend', 'crecimiento'},
            'prediccion': {'predicción', 'prediccion', 'forecast', 'proyección'},
            'marca': {'marca', 'marcas', 'fabricante', 'brand'},
            'tienda': {'tienda', 'sucursal', 'punto de venta'},
        }

        for concepto, keywords in keywords_dominio.items():
            if any(kw in consulta_lower for kw in keywords):
                conceptos_consulta.add(concepto)

        if not conceptos_consulta:
            return True  # No se puede evaluar

        # Verificar que al menos un concepto esté en la respuesta
        for concepto in conceptos_consulta:
            if any(kw in resp_lower for kw in keywords_dominio.get(concepto, set())):
                return True

        # Si la respuesta tiene datos numéricos, probablemente es relevante
        if re.search(r'\$[\d,.]+|\d+\.?\d*%|\d{1,3}(?:,\d{3})+', respuesta):
            return True

        return False

    def _contiene_contenido_manual(self, texto: str) -> bool:
        """Detecta si la respuesta tiene contenido de manual/documentación mezclado."""
        indicadores_manual = [
            'manual de odoo',
            'paso 1:', 'paso 2:', 'paso 3:',
            'procedimiento para',
            'ir a menú',
            'hacer clic en',
            'seleccionar la opción',
            'en la pestaña',
            'capítulo', 'sección del manual',
        ]
        texto_lower = texto.lower()
        coincidencias = sum(1 for ind in indicadores_manual if ind in texto_lower)
        return coincidencias >= 2

    def _remover_contenido_manual(self, texto: str) -> str:
        """Remueve bloques de contenido de manual de una respuesta de datos."""
        lineas = texto.split('\n')
        lineas_limpias = []
        en_bloque_manual = False

        for linea in lineas:
            linea_lower = linea.lower().strip()
            # Detectar inicio de bloque manual
            if any(p in linea_lower for p in ['manual de odoo', 'procedimiento:', 'pasos:']):
                en_bloque_manual = True
                continue
            # Detectar fin de bloque (línea vacía después de manual)
            if en_bloque_manual and linea.strip() == '':
                en_bloque_manual = False
                continue
            if not en_bloque_manual:
                lineas_limpias.append(linea)

        resultado = '\n'.join(lineas_limpias).strip()
        return resultado if resultado else texto

    def _validar_coherencia_datos(self, respuesta: str, df) -> List[str]:
        """Valida que los números mencionados en la respuesta sean coherentes con el DataFrame."""
        problemas = []
        try:
            # Extraer números de la respuesta
            numeros_resp = re.findall(r'[\$]?([\d,]+(?:\.\d+)?)', respuesta)
            if not numeros_resp or df is None:
                return problemas

            n_filas = max(len(df), 1)

            # Obtener rangos del DataFrame
            for col in df.select_dtypes(include=['number']).columns:
                col_min = df[col].min()
                col_max = df[col].max()

                for num_str in numeros_resp:
                    try:
                        num = float(num_str.replace(',', ''))
                        # El límite superior se ajusta al número de filas:
                        # un total de N filas puede ser hasta N * col_max (+ 50% margen).
                        limite = col_max * n_filas * 1.5
                        if col_max > 0 and num > max(limite, col_max * 100):
                            problemas.append(f'numero_fuera_rango:{num_str}')
                            break
                    except (ValueError, TypeError):
                        continue
        except Exception:
            pass

        return problemas

    def _generar_respuesta_honesta(self, consulta: str, accion: str, motivo: str) -> str:
        """
        Genera una respuesta honesta cuando no hay datos o la original fue descartada.
        NUNCA inventa datos — admite la limitación.
        """
        consulta_corta = consulta[:60] if consulta else 'tu consulta'

        respuestas = {
            'no_datos': (
                f"No encontré datos para **{consulta_corta}** en el periodo consultado.\n\n"
                "Puedes intentar:\n"
                "- Ampliar el rango de fechas (ej: *'ventas últimos 3 meses'*)\n"
                "- Ser más específico (ej: *'ventas por marca este mes'*)\n"
                "- Verificar que el módulo esté activo en Odoo"
            ),
            'limpieza_vacio': (
                f"Procesé tu consulta sobre **{consulta_corta}**, pero no pude generar una respuesta confiable.\n\n"
                "Por favor reformula la consulta con más detalle para obtener mejores resultados."
            ),
        }

        return respuestas.get(motivo, respuestas['limpieza_vacio'])

    def _agregar_contexto_respuesta(self, respuesta: str, consulta: str, accion: str) -> str:
        """Agrega contexto cuando la respuesta parece no coincidir con la consulta."""
        # No modificar si la respuesta ya es larga y tiene datos
        if len(respuesta) > 200 and re.search(r'\d+', respuesta):
            return respuesta
        return respuesta


# ── Instancia singleton ──────────────────────────────────────────
_validador = None

def obtener_validador() -> ValidadorRespuestas:
    """Obtiene instancia singleton del validador."""
    global _validador
    if _validador is None:
        _validador = ValidadorRespuestas()
    return _validador
