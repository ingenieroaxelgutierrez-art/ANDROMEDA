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
        # === Acciones v2 RRHH ===
        'rotacion_personal': 'rotación de personal',
        'clima_organ': 'clima organizacional',
        'clima': 'clima organizacional',
        'brecha_sal': 'brecha salarial',
        'brecha': 'brecha salarial',
        'horas_extra': 'horas extra',
        'vacacion': 'vacaciones',
        'incapacid': 'incapacidades',
        'prestacion': 'prestaciones laborales',
        'cumplimiento_jornada': 'jornada laboral',
        'jornada': 'jornada laboral',
        'estructura_organ': 'estructura organizacional',
        'organigrama': 'organigrama',
        'costo_rotacion': 'costo de rotación',
        # === Acciones v2 Inventario ===
        'inventario_obsoleto': 'inventario obsoleto',
        'obsoleto': 'inventario obsoleto',
        'inventario_por_almacen': 'inventario por almacén',
        'almacen': 'inventario por almacén',
        'trazabilidad': 'trazabilidad de lotes',
        'lote': 'trazabilidad de lotes',
        'cobertura_stock': 'cobertura de stock',
        'inventario_negativo': 'stock negativo',
        'transferencia': 'transferencias',
        'costo_almacenamiento': 'costo de almacenamiento',
        'comparar_stock': 'comparativa stock físico vs sistema',
        # === Acciones v2 Finanzas ===
        'notas_credito': 'notas de crédito',
        'impuesto': 'impuestos',
        'margen_operativo': 'margen operativo',
        'razon_liquidez': 'liquidez',
        'liquidez': 'liquidez',
        'capital_trabajo': 'capital de trabajo',
        'pagos_pendientes': 'pagos pendientes',
        'estado_cuenta': 'estado de cuenta',
        'conciliacion': 'conciliación bancaria',
        'antiguedad': 'antigüedad de saldos',
        # === Acciones v2 CRM ===
        'conversion_lead': 'conversión de leads',
        'actividades_pendientes': 'actividades pendientes',
        'oportunidades': 'oportunidades CRM',
        'win_rate': 'tasa de cierre',
        'lifetime_value': 'valor de vida del cliente',
        'reactivacion': 'reactivación de clientes',
        # === Acciones v2 Compras ===
        'compras_recurrentes': 'compras recurrentes',
        'comparativa_precios': 'comparativa de precios',
        'cumplimiento_entregas': 'cumplimiento de entregas',
        'ahorro_potencial': 'ahorro potencial',
        'compras_urgentes': 'compras urgentes',
        'gasto_por_departamento': 'gasto por departamento',
        # === Acciones v2 PDV ===
        'descuentos_pos': 'descuentos en POS',
        'devoluciones_pos': 'devoluciones en POS',
        'cuadre_caja': 'cuadre de caja',
        'pos_por_sucursal': 'POS por sucursal',
        'ticket_detalle': 'detalle de ticket',
        'rendimiento_terminal': 'rendimiento de terminal',
        'ventas_pos_vs': 'POS vs e-commerce',
        # === Acciones v2 Diagnóstico ===
        'validacion_cruzada': 'validación cruzada',
        'consistencia': 'consistencia de datos',
        'registros_duplicados': 'registros duplicados',
        'reconciliacion': 'reconciliación contable',
        'integridad': 'integridad de datos',
        'secuencias_rotas': 'secuencias rotas',
        'configuraciones_riesgosas': 'configuraciones de riesgo',
        'accesos_inusuales': 'accesos inusuales',
        'operaciones_masivas': 'operaciones masivas',
        # === Acciones v2 Odoo/Sistema ===
        'relaciones_modelo': 'relaciones de modelo Odoo',
        'flujo_trabajo': 'flujo de trabajo Odoo',
        'permisos_usuario': 'permisos de usuario',
        'log_acciones': 'log de acciones',
        'modulos_instalados': 'módulos instalados',
        'ir_cron': 'tareas programadas',
        'parametros_sistema': 'parámetros del sistema',
        'capacidades': 'capacidades del asistente',
        'generar_pdf': 'generación de PDF',
        'generar_excel': 'generación de Excel',
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
        # 1. Coincidencia exacta por nombre de acción (más precisa)
        if accion in self._DOMINIOS:
            return self._DOMINIOS[accion]
        # 2. Substring: gana la clave más larga (evita falsos positivos genéricos)
        texto = f'{accion} {intencion}'.lower()
        candidatos = [(pat, dom) for pat, dom in self._DOMINIOS.items() if pat in texto]
        if candidatos:
            return max(candidatos, key=lambda x: len(x[0]))[1]
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
