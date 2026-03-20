# ============================================================
# ANDROMEDA - Formateador de Conclusiones
# ============================================================
# Estructura conversacional para respuestas del agente:
#   1. Reconocimiento  → "He analizado los datos de X..."
#   2. Datos           → Tablas, métricas (existente)
#   3. Insight Humano  → "Llama la atención que..."
#   4. Cierre          → "¿Quieres que genere el Excel/PDF...?"
# ============================================================


class FormateadorConclusiones:
    """Envuelve respuestas con estructura conversacional humanizada."""

    _DOMINIOS = {
        'venta': 'ventas',
        'top_producto': 'productos más vendidos',
        'top_cliente': 'mejores clientes',
        'top_vendedor': 'mejores vendedores',
        'inventario': 'inventario',
        'stock': 'stock',
        'producto_critico': 'productos críticos',
        'reorden': 'puntos de reorden',
        'rotacion_inv': 'rotación de inventario',
        'financ': 'finanzas',
        'cxc': 'cuentas por cobrar',
        'cxp': 'cuentas por pagar',
        'flujo': 'flujo de caja',
        'factur': 'facturación',
        'compra': 'compras',
        'crm': 'CRM',
        'lead': 'leads y pipeline',
        'rrhh': 'recursos humanos',
        'nomina': 'nómina',
        'pos': 'punto de venta',
        'prediccion': 'predicciones',
        'forecast': 'proyecciones',
        'agotamiento': 'agotamiento de inventario',
        'auditoria': 'auditoría',
        'anomalia': 'anomalías',
        'kpi': 'indicadores clave',
        'estadistic': 'análisis estadístico',
        '360': 'análisis integral',
        'cliente': 'clientes',
        'proveedor': 'proveedores',
        'morosi': 'morosidad',
        'margen': 'márgenes',
        'rentab': 'rentabilidad',
        'rotacion': 'rotación',
        'tendencia': 'tendencias',
        'comparativ': 'comparativa',
        'salud': 'salud del negocio',
        'churn': 'riesgo de fuga de clientes',
        'segmentacion': 'segmentación de clientes',
        'pareto': 'análisis Pareto',
        'rfm': 'análisis RFM',
        'estacionalidad': 'estacionalidad',
        'merma': 'mermas',
        'abc': 'clasificación ABC',
    }

    # Respuestas que NO deben envolverse
    _SKIP_PATTERNS = [
        'error al procesar',
        'consulta crítica',
        'responde **sí**',
        'no pude',
        'no encontré datos',
        'no se encontraron',
        'modo **solo lectura**',
        'intenta reformular',
        'no hay datos',
    ]

    # Marcador para evitar doble aplicación
    _MARCADOR = '<!-- conclusiones-aplicadas -->'

    def aplicar(self, respuesta: str, accion: str, intencion: str,
                es_cadena: bool = False) -> str:
        """Envuelve la respuesta con estructura conversacional.

        Args:
            respuesta: Markdown formateado por los formateadores existentes
            accion: accion_sugerida de la consulta
            intencion: intencion_principal de la consulta
            es_cadena: si fue una cadena multi-agente
        """
        if not respuesta or self._es_skip(respuesta):
            return respuesta

        dominio = self._detectar_dominio(accion, intencion)
        reconocimiento = self._reconocimiento(dominio, es_cadena)
        insight = self._extraer_insight(respuesta)
        cierre = self._cierre()

        partes = [self._MARCADOR, reconocimiento, '', respuesta]

        if insight:
            partes.extend(['', f'💡 **Observación:** {insight}'])

        partes.extend(['', cierre])

        return '\n'.join(partes)

    # ── Internos ─────────────────────────────────────────────

    def _es_skip(self, respuesta: str) -> bool:
        """Detecta respuestas de sistema que no deben envolverse."""
        if self._MARCADOR in respuesta:
            return True
        resp_lower = respuesta[:300].lower()
        return any(p in resp_lower for p in self._SKIP_PATTERNS)

    def _detectar_dominio(self, accion: str, intencion: str) -> str:
        texto = f'{accion} {intencion}'.lower()
        for patron, dominio in self._DOMINIOS.items():
            if patron in texto:
                return dominio
        return 'los datos solicitados'

    def _reconocimiento(self, dominio: str, es_cadena: bool) -> str:
        if es_cadena:
            return (
                f'📊 He realizado un análisis completo de **{dominio}** '
                f'combinando múltiples perspectivas. Esto es lo que encontré:'
            )
        return f'📊 He analizado los datos de **{dominio}** y esto es lo que encontré:'

    def _extraer_insight(self, respuesta: str) -> str:
        """Extrae la observación más relevante: prioriza alertas > insights."""
        lineas = respuesta.split('\n')
        alertas = []
        insights = []
        seccion_actual = None

        for linea in lineas:
            stripped = linea.strip()
            lower = stripped.lower()

            # Detectar inicio de secciones relevantes
            if lower.startswith('### alerta') or lower.startswith('### ⚠'):
                seccion_actual = 'alertas'
                continue
            elif lower.startswith('### insight') or lower.startswith('### 💡'):
                seccion_actual = 'insights'
                continue
            elif stripped.startswith('### ') or stripped.startswith('## '):
                seccion_actual = None
                continue

            # Recolectar items de la sección activa
            if stripped.startswith('- ') and seccion_actual:
                texto = stripped[2:].strip()
                if texto and len(texto) > 10:
                    if seccion_actual == 'alertas':
                        alertas.append(texto)
                    elif seccion_actual == 'insights':
                        insights.append(texto)

        # Priorizar alertas (más accionables)
        if alertas:
            return alertas[0]
        if insights:
            return insights[0]
        return ''

    def _cierre(self) -> str:
        return (
            '📎 ¿Quieres que genere el **Excel**, **PDF** '
            'o alguna **gráfica** para que lo revises con calma?'
        )
