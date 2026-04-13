# -*- coding: utf-8 -*-
"""
ANDROMEDA - Arquitectura Multi-Agente Expandida
================================================
12 Agentes especializados con experiencia de nivel experto (20+ años):

 1. Ventas          - Análisis comercial y rendimiento de ventas
 2. Inventarios     - Gestión de stock, rotación, cadena de suministro
 3. Finanzas        - Contabilidad, cobranza, flujo de caja, facturación
 4. Diagnóstico     - Detección de anomalías, auditoría, salud del sistema
 5. Consultas Odoo  - Consultoría funcional ERP, modelos, usuarios
 6. CRM             - Pipeline, oportunidades, retención, churn
 7. Compras         - Adquisiciones, proveedores, costeo
 8. PDV             - Punto de venta, sesiones, tickets, métodos de pago
 9. Predicciones    - Forecast, Monte Carlo, LSTM, series de tiempo
10. Matemáticas     - Cálculos financieros, márgenes, ROI, break-even
11. Estadística     - Análisis de datos, correlación, segmentación, KPIs
12. RRHH            - Recursos humanos, nómina, asistencia, contratos

Cada agente tiene:
- Prompt base de experto con reglas anti-alucinación
- Validaciones pre/post ejecución propias
- Reglas de negocio específicas de su dominio
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.logging_config import get_logger
logger = get_logger("services.agents.multi_agente")


@dataclass
class ResultadoPreEjecucion:
    permitido: bool
    consulta: Any
    advertencias: List[str] = field(default_factory=list)
    motivo_bloqueo: str = ""
    requiere_confirmacion: bool = False
    confianza_agente: float = 0.0


@dataclass
class ResultadoPostEjecucion:
    respuesta: str
    confianza_datos: float
    observaciones: List[str] = field(default_factory=list)


class AgenteEspecializadoBase:
    id_agente: str = "agente_base"
    prompt_base: str = "Responder solo con datos verificables del sistema."
    acciones_soportadas: Set[str] = set()
    palabras_clave_prompt: Set[str] = set()

    def score_prompt(self, mensaje: str) -> float:
        import re as _re
        texto = (mensaje or "").lower()
        if not texto:
            return 0.0
        score = 0
        for kw in self.palabras_clave_prompt:
            # Usar word boundary para evitar falsos positivos
            # Ej: "venta" no debería matchear dentro de "inventario"
            if _re.search(r'\b' + _re.escape(kw) + r'\b', texto):
                score += 1
        if not self.palabras_clave_prompt:
            return 0.0
        return min(1.0, score / max(3, len(self.palabras_clave_prompt)))

    def soporta_accion(self, accion: str) -> bool:
        return accion in self.acciones_soportadas

    def ejecutar(self, consulta: Any, mensaje: str, ejecutor: Callable[[Any, str], Tuple[str, Any]]) -> Tuple[str, Any]:
        """Permite que el agente dispare el backend real registrado por la UI."""
        return ejecutor(consulta, mensaje)

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        """Hook para aportar análisis determinista sobre datos reales ya obtenidos."""
        return respuesta

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = self._advertencias_de_parametros(consulta)
        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.7
        )

    def _advertencias_de_parametros(self, consulta: Any) -> List[str]:
        """
        Convierte los parámetros extraídos por el NLP en advertencias internas
        que sirven de contexto a los agentes LLM y ejecutores.

        Estas advertencias NO se muestran al usuario directamente; viajan por
        el pipeline para enriquecer el prompt del LLM y los filtros de Odoo.
        """
        advertencias: List[str] = []
        params = getattr(consulta, 'parametros', {}) or {}

        # Agrupación solicitada
        groupby = params.get('groupby')
        if groupby:
            if isinstance(groupby, list):
                for g in groupby:
                    advertencias.append(f'usuario_pide_agrupar_por_{g}')
            else:
                advertencias.append(f'usuario_pide_agrupar_por_{groupby}')

        # Filtro de tienda
        if params.get('tienda'):
            advertencias.append(f"usuario_filtro_tienda:{params['tienda']}")

        # Filtro de cliente
        if params.get('cliente'):
            advertencias.append(f"usuario_filtro_cliente:{params['cliente']}")

        # Filtro de vendedor
        if params.get('vendedor'):
            advertencias.append(f"usuario_filtro_vendedor:{params['vendedor']}")

        # Filtro de producto
        if params.get('producto'):
            advertencias.append(f"usuario_filtro_producto:{params['producto']}")

        # Filtro de proveedor
        if params.get('proveedor'):
            advertencias.append(f"usuario_filtro_proveedor:{params['proveedor']}")

        # Ranking / límite explícito
        limite = params.get('limite')
        if isinstance(limite, int):
            advertencias.append(f'usuario_pide_top_{limite}')

        # Formato de salida
        formato = params.get('formato') or getattr(consulta, 'formato_solicitado', None)
        if formato and formato != 'auto':
            advertencias.append(f'usuario_pide_formato_{formato}')

        # Rangos de monto
        if params.get('mayor_que') is not None:
            advertencias.append(f"usuario_filtro_monto_min:{params['mayor_que']}")
        if params.get('menor_que') is not None:
            advertencias.append(f"usuario_filtro_monto_max:{params['menor_que']}")

        return advertencias

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        confianza = float(getattr(consulta, 'confianza', 0.0) or 0.0)
        observaciones: List[str] = []

        # Regla global anti-alucinación: ajustar confianza sin contaminar la respuesta
        if error:
            confianza = min(confianza, 0.25)
            observaciones.append("respuesta_con_error")

        if df is None and not error:
            resp_lower = (respuesta or "").lower()
            hay_descargo = any(
                token in resp_lower for token in [
                    "no hay", "no se encontró", "no disponible", "error", "reformular", "confianza"
                ]
            )
            if not hay_descargo:
                # Solo reducir confianza y registrar en observaciones internas,
                # NUNCA inyectar texto de validación en la respuesta al usuario.
                confianza = min(confianza, 0.55)
                observaciones.append("sin_evidencia_tabular")

        return ResultadoPostEjecucion(
            respuesta=respuesta,
            confianza_datos=max(0.0, min(1.0, confianza)),
            observaciones=observaciones
        )


class AgentVentas(AgenteEspecializadoBase):
    """Experto en análisis comercial con 20+ años en retail y distribución."""
    id_agente = "agente_ventas"
    prompt_base = (
        "Eres un director comercial con 20+ años de experiencia en retail, distribución y e-commerce. "
        "Solo respondes con datos verificables de Odoo. Siempre indicas período, filtros y fuente de datos. "
        "Cuando detectas tendencias, diferencias la correlación de la causalidad. "
        "Nunca inventas cifras; si no hay datos suficientes, lo dices explícitamente. "
        "Priorizas: ticket promedio, margen, mix de productos, estacionalidad y crecimiento interanual."
    )
    acciones_soportadas = {
        'consultar_ventas', 'analisis_ventas', 'top_productos', 'top_clientes',
        'ventas_vendedor', 'ventas_por_vendedor', 'tendencia', 'comparar_periodos',
        'comparativa', 'ventas_completo', 'ventas_por_empresa', 'ventas_por_tienda',
        'ventas_por_marca', 'ventas_mensuales_marca',
        'comparar_periodos_especificos', 'ventas_tienda_especifica',
        'comparativa_periodos', 'estacionalidad', 'empresas_resumen',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'ventas_por_canal',              # Desglose por canal de venta (web, tienda, marketplace)
        'ventas_por_categoria',          # Desglose por categoría de producto
        'margen_por_producto',           # Análisis de márgenes por producto vendido
        'devolucion_ventas',             # Análisis de devoluciones (notas de crédito/refunds)
        'meta_cumplimiento',             # Cumplimiento de metas comerciales vs real
        'ventas_por_dia_semana',         # Patrón de ventas por día de la semana
        'ventas_por_hora',               # Patrón de ventas intradiario
        'concentracion_clientes',        # Análisis de concentración (Pareto clientes)
        'clientes_nuevos_vs_recurrentes', # Segmentación nuevos vs recurrentes
        'ticket_promedio_evolucion',     # Evolución del ticket promedio en el tiempo
        'descuentos_aplicados',          # Análisis de descuentos otorgados y su impacto
        'ventas_vs_anterior',            # Comparativa directa con período anterior
    }
    palabras_clave_prompt = {
        'venta', 'ventas', 'ticket', 'ingresos', 'vendedor', 'vendedores',
        'producto', 'cliente', 'comparativa', 'facturado', 'revenue',
        'top productos', 'más vendido', 'ranking', 'rendimiento comercial',
        'tienda', 'sucursal', 'marca', 'estacionalidad', 'temporada',
        'período', 'mensual', 'empresa', 'canal',
        # === Nuevas keywords v2 ===
        'categoría', 'margen', 'devolución', 'devoluciones', 'meta',
        'objetivo', 'cumplimiento', 'descuento', 'descuentos', 'recurrente',
        'nuevo cliente', 'concentración', 'pareto', 'día semana', 'horario',
        'refund', 'nota de crédito', 'crecimiento',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = []
        temp = getattr(consulta, 'temporalidad', {}) or {}
        texto = (mensaje or '').lower()

        if not temp.get('fecha_inicio') or not temp.get('fecha_fin'):
            hoy = datetime.now()
            inicio = (hoy - timedelta(days=30)).strftime('%Y-%m-%d')
            fin = hoy.strftime('%Y-%m-%d')
            temp['fecha_inicio'] = temp.get('fecha_inicio', inicio)
            temp['fecha_fin'] = temp.get('fecha_fin', fin)
            consulta.temporalidad = temp
            advertencias.append('temporalidad_default_30_dias')

        # Anti-alucinación: detectar ambigüedad entre ventas brutas vs netas
        accion = getattr(consulta, 'accion_sugerida', '')
        if accion in ('margen_por_producto', 'descuentos_aplicados') and 'costo' not in texto:
            advertencias.append('margen_requiere_campo_costo_verificar_disponibilidad')

        # Anti-alucinación: si piden comparar sin definir períodos explícitos
        if accion in ('comparar_periodos', 'comparar_periodos_especificos', 'ventas_vs_anterior'):
            if not any(x in texto for x in ['vs', 'contra', 'anterior', 'pasado', 'enero', 'febrero',
                                              'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
                                              'septiembre', 'octubre', 'noviembre', 'diciembre', '2024', '2025', '2026']):
                advertencias.append('comparativa_sin_periodos_explicitos_usar_mes_anterior')

        # Incluir contexto de parámetros del usuario (groupby, tienda, formato, etc.)
        advertencias.extend(self._advertencias_de_parametros(consulta))

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.92
        )

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        resultado = super().post_ejecucion(consulta, respuesta, df, error)

        # Anti-alucinación: verificar coherencia de montos en respuesta vs datos
        if df is not None and hasattr(df, 'shape') and not error:
            resp_lower = (respuesta or '').lower()
            # Si menciona "total" pero el df tiene pocas filas, advertir
            if 'total' in resp_lower and hasattr(df, '__len__') and len(df) == 0:
                resultado.observaciones.append('respuesta_menciona_total_sin_registros')
                resultado.confianza_datos = min(resultado.confianza_datos, 0.30)

        return resultado

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta
        try:
            cols_money = [c for c in df.columns if c in ('amount_total', 'price_subtotal', 'amount_untaxed')]
            if not cols_money:
                return respuesta
            col = cols_money[0]
            import pandas as pd
            serie = pd.to_numeric(df[col], errors='coerce').dropna()
            if serie.empty:
                return respuesta
            total = float(serie.sum())
            if total <= 0:
                return respuesta
            top20_n = max(1, int(len(serie) * 0.2))
            top20_sum = float(serie.nlargest(top20_n).sum())
            concentracion = top20_sum / total * 100
            linea = (
                f"\n\n**Análisis del agente comercial:**\n"
                f"- Total acumulado: ${total:,.2f}\n"
                f"- Registros analizados: {len(serie)}\n"
                f"- Concentración top 20%: {concentracion:.1f}% del total"
            )
            if 'Análisis del agente comercial' not in (respuesta or ''):
                return respuesta + linea
        except Exception:
            pass
        return respuesta


class AgentInventarios(AgenteEspecializadoBase):
    """Experto en gestión de inventarios y cadena de suministro con 20+ años."""
    id_agente = "agente_inventario"
    prompt_base = (
        "Eres un gerente de supply chain con 20+ años de experiencia en gestión de inventarios, "
        "logística y operaciones de almacén. Priorizas exactitud de stock, índices de rotación, "
        "criticidad ABC y niveles de reorden. No extrapolas sin indicador explícito. "
        "Siempre consideras costos de almacenamiento, obsolescencia y servicio al cliente. "
        "Recomiendas acciones concretas basadas en datos observables del sistema."
    )
    acciones_soportadas = {
        'consultar_inventario', 'analisis_inventario', 'productos_sin_stock',
        'rotacion_inventario', 'valoracion_inventario', 'predecir_agotamiento',
        'inventario_por_tienda', 'inventario_por_almacen', 'inventario_por_ubicacion',
        'productos_criticos', 'rotacion_inventario_avanzado', 'kpi_rotacion_inventario',
        'kpi_faltantes', 'productos_bajo_minimo', 'movimientos_stock',
        'reposicion_jit', 'stock_lento',
        'prediccion_inventario_inteligente',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'abc_inventario',                # Clasificación ABC por valor/rotación
        'inventario_obsoleto',           # Productos obsoletos (sin movimiento > 180 días)
        'costo_almacenamiento',          # Costo de mantener inventario (holding cost)
        'trazabilidad_lote',             # Rastreo de lotes y números de serie
        'inventario_negativo',           # Detección de stock negativo (inconsistencia)
        'inventario_por_categoria',      # Desglose por categoría de producto
        'cobertura_stock',               # Días de cobertura de stock actual
        'merma_inventario',              # Análisis de mermas y ajustes de inventario
        'transferencias_pendientes',     # Transferencias entre almacenes pendientes
        'inventario_valorizado_categoria', # Valorización por categoría
        'comparar_stock_fisico_sistema', # Discrepancias stock físico vs sistema
    }
    palabras_clave_prompt = {
        'inventario', 'stock', 'existencias', 'almacén', 'almacen', 'rotación',
        'agotado', 'reposición', 'faltante', 'movimiento', 'traslado', 'ubicación',
        'mínimo', 'máximo', 'reorden', 'desabasto', 'obsoleto', 'lento',
        'bodega', 'producto crítico', 'valoración', 'jit',
        # === Nuevas keywords v2 ===
        'abc', 'clasificación abc', 'merma', 'cobertura', 'lote', 'serie',
        'transferencia', 'negativo', 'ajuste', 'conteo', 'físico',
        'costo almacenamiento', 'holding', 'obsolescencia', 'caducidad',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = []
        params = getattr(consulta, 'parametros', {}) or {}
        texto = (mensaje or '').lower()

        limite = params.get('limite')
        if isinstance(limite, int) and limite > 200:
            params['limite'] = 200
            consulta.parametros = params
            advertencias.append('limite_ajustado_200')

        # Anti-alucinación: si pide stock negativo, advertir que puede ser dato real
        accion = getattr(consulta, 'accion_sugerida', '')
        if accion == 'inventario_negativo':
            advertencias.append('stock_negativo_puede_indicar_movimientos_pendientes')

        # Anti-alucinación: ABC requiere campo de costo y cantidad vendida
        if accion == 'abc_inventario':
            advertencias.append('abc_requiere_datos_costo_y_movimiento_verificar')

        # Anti-alucinación: merma necesita verificar ajustes de inventario
        if accion == 'merma_inventario' and 'ajuste' not in texto and 'merma' not in texto:
            advertencias.append('merma_verificar_tipo_movimiento_scrap_adjustment')

        # Incluir contexto de parámetros del usuario
        advertencias.extend(self._advertencias_de_parametros(consulta))

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.90
        )

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        resultado = super().post_ejecucion(consulta, respuesta, df, error)

        # Anti-alucinación: stock no puede ser flotante con muchos decimales
        if df is not None and hasattr(df, 'columns'):
            for col in ('quantity', 'qty_available', 'virtual_available'):
                if col in df.columns:
                    import pandas as pd
                    vals = pd.to_numeric(df[col], errors='coerce')
                    if vals.notna().any() and (vals.abs() > 1e7).any():
                        resultado.observaciones.append(f'posible_dato_anomalo_en_{col}')
                        resultado.confianza_datos = min(resultado.confianza_datos, 0.60)

        return resultado

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta
        try:
            hallazgos = []
            if 'quantity' in df.columns:
                import pandas as pd
                qty = pd.to_numeric(df['quantity'], errors='coerce')
                negativos = int((qty < 0).sum())
                ceros = int((qty == 0).sum())
                if negativos > 0:
                    hallazgos.append(f"- Stock negativo: {negativos} registros (posible inconsistencia)")
                if ceros > 0:
                    hallazgos.append(f"- Stock en cero: {ceros} registros")
            if not hallazgos or 'Análisis del agente de inventario' in (respuesta or ''):
                return respuesta
            return respuesta + "\n\n**Análisis del agente de inventario:**\n" + "\n".join(hallazgos)
        except Exception:
            pass
        return respuesta


class AgentFinanzas(AgenteEspecializadoBase):
    """Experto financiero nivel CFO con 20+ años en contabilidad y tesorería."""
    id_agente = "agente_finanzas"
    prompt_base = (
        "Eres un CFO con 20+ años de experiencia en contabilidad, tesorería y control financiero. "
        "Reportas montos y estados con enfoque conservador siguiendo principios contables. "
        "Si faltan datos clave, lo explicitas antes de concluir. Siempre consideras: "
        "antigüedad de cartera, provisiones de cobranza dudosa, flujo de efectivo operativo, "
        "y ratios financieros clave (liquidez, endeudamiento, cobertura). "
        "Nunca redondeas montos significativos sin advertir; la precisión en centavos importa."
    )
    acciones_soportadas = {
        'consultar_facturas', 'analisis_facturacion', 'cuentas_por_cobrar', 'cuentas_por_pagar',
        'cxc_analisis', 'cxp_analisis', 'score_morosos', 'flujo_caja', 'salud_negocio',
        'facturas_filtradas', 'kpi_ticket_promedio', 'consultar_pagos', 'diferencias_centavos',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'conciliacion_bancaria',         # Conciliación de pagos vs facturas
        'analisis_antiguedad',           # Aging analysis detallado por rangos
        'notas_credito',                 # Análisis de notas de crédito emitidas
        'impuestos_resumen',             # Resumen de impuestos por período
        'rentabilidad_cliente',          # Ingreso neto por cliente (ventas - devoluciones - descuentos)
        'margen_operativo',              # Margen operativo por línea de negocio
        'razon_liquidez',                # Ratio de liquidez corriente
        'capital_trabajo',               # Capital de trabajo (activo corriente - pasivo corriente)
        'dias_cobro_promedio',           # DSO: Days Sales Outstanding promedio
        'dias_pago_promedio',            # DPO: Days Payable Outstanding promedio
        'facturacion_por_empresa',       # Desglose de facturación por empresa/company_id
        'pagos_pendientes_aplicar',      # Pagos recibidos sin aplicar a facturas
        'estado_cuenta_cliente',         # Estado de cuenta completo por cliente
        'estado_cuenta_proveedor',       # Estado de cuenta completo por proveedor
    }
    palabras_clave_prompt = {
        'factura', 'facturas', 'cxc', 'cxp', 'morosos', 'cobrar', 'pagar', 'flujo',
        'finanzas', 'saldo', 'cartera', 'cobranza', 'tesorería', 'contabilidad',
        'pagos', 'cfdi', 'timbrado', 'notas de crédito', 'deuda',
        # === Nuevas keywords v2 ===
        'conciliación', 'antigüedad', 'aging', 'impuesto', 'iva', 'isr',
        'rentabilidad', 'liquidez', 'capital de trabajo', 'dso', 'dpo',
        'estado de cuenta', 'saldo pendiente', 'vencido', 'por vencer',
        'margen operativo', 'utilidad neta', 'ebitda',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = []
        temp = getattr(consulta, 'temporalidad', {}) or {}
        texto = (mensaje or '').lower()

        if not temp.get('fecha_inicio') and not temp.get('fecha_fin'):
            hoy = datetime.now()
            temp['fecha_inicio'] = (hoy - timedelta(days=30)).strftime('%Y-%m-%d')
            temp['fecha_fin'] = hoy.strftime('%Y-%m-%d')
            consulta.temporalidad = temp
            advertencias.append('rango_financiero_default_30_dias')

        # Anti-alucinación: verificar que se pide estado correcto de factura
        accion = getattr(consulta, 'accion_sugerida', '')
        if accion in ('cuentas_por_cobrar', 'cxc_analisis', 'score_morosos'):
            if 'cancelada' in texto or 'borrador' in texto:
                advertencias.append('cxc_debe_filtrar_solo_facturas_posted_open')

        # Anti-alucinación: conciliación requiere datos de pagos Y facturas
        if accion == 'conciliacion_bancaria':
            advertencias.append('conciliacion_requiere_cruce_pagos_y_facturas')

        # Anti-alucinación: ratios financieros necesitan datos de ambos lados del balance
        if accion in ('razon_liquidez', 'capital_trabajo'):
            advertencias.append('ratio_requiere_balance_completo_verificar_datos')

        # Incluir contexto de parámetros del usuario
        advertencias.extend(self._advertencias_de_parametros(consulta))

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.92
        )

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        resultado = super().post_ejecucion(consulta, respuesta, df, error)

        # Anti-alucinación: montos financieros deben ser razonables
        if df is not None and hasattr(df, 'columns') and not error:
            for col in ('amount_total', 'amount_residual', 'amount_untaxed'):
                if col in df.columns:
                    import pandas as pd
                    vals = pd.to_numeric(df[col], errors='coerce')
                    if vals.notna().any():
                        # Detectar montos negativos inesperados en facturas de cliente
                        if (vals < 0).any():
                            resultado.observaciones.append(f'montos_negativos_en_{col}_verificar_notas_credito')

        return resultado

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta
        try:
            hallazgos = []
            if 'amount_residual' in df.columns and 'amount_total' in df.columns:
                import pandas as pd
                residual = pd.to_numeric(df['amount_residual'], errors='coerce').sum()
                total = pd.to_numeric(df['amount_total'], errors='coerce').sum()
                if total > 0:
                    cobrado = total - residual
                    pct = cobrado / total * 100
                    hallazgos.append(f"- Total facturado: ${total:,.2f}")
                    hallazgos.append(f"- Cobrado: ${cobrado:,.2f} ({pct:.1f}%)")
                    hallazgos.append(f"- Pendiente: ${residual:,.2f}")
            if not hallazgos or 'Análisis del agente financiero' in (respuesta or ''):
                return respuesta
            return respuesta + "\n\n**Análisis del agente financiero:**\n" + "\n".join(hallazgos)
        except Exception:
            pass
        return respuesta


class AgentDiagnostico(AgenteEspecializadoBase):
    """Experto en diagnóstico de sistemas y auditoría con 20+ años."""
    id_agente = "agente_diagnostico"
    prompt_base = (
        "Eres un auditor senior y arquitecto de sistemas con 20+ años de experiencia en "
        "diagnóstico operativo, detección de fraude y auditoría de datos empresariales. "
        "Priorizas causas raíz sobre síntomas, validación reproducible y acciones seguras de solo lectura. "
        "Clasificas hallazgos por severidad (crítico/alto/medio/bajo) y probabilidad. "
        "Nunca afirmas fraude sin evidencia estadística sólida; usas lenguaje probabilístico. "
        "Recomiendas controles preventivos además de correctivos."
    )
    acciones_soportadas = {
        'diagnosticar_error', 'auditoria_nocturna', 'semaforo_salud',
        'detectar_pagos_fantasma', 'detectar_anomalias', 'analisis_riesgos',
        'generar_reporte_auditoria',
        'auditoria_fraude', 'auditoria_calidad_datos',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'validacion_cruzada',            # Validación cruzada entre fuentes de datos
        'consistencia_datos',            # Verificación de consistencia entre tablas/modelos
        'registros_duplicados',          # Detección de registros duplicados en BD
        'campos_vacios_criticos',        # Campos obligatorios vacíos en registros críticos
        'reconciliacion_stock_contable', # Stock físico (quant) vs contable (account.move)
        'integridad_referencial',        # Verificar FK huérfanos y relaciones rotas
        'secuencias_rotas',              # Detección de huecos en secuencias (facturas, órdenes)
        'configuraciones_riesgosas',     # Ajustes del sistema que representan riesgo
        'accesos_inusuales',             # Patrones de acceso atípicos de usuarios
        'operaciones_masivas',           # Detección de borrados/ediciones masivas sospechosas
        'salud_base_datos',              # Métricas de salud de la BD (tamaño, fragmentación)
    }
    palabras_clave_prompt = {
        'error', 'falla', 'traceback', 'anomalia', 'anomalía', 'riesgo',
        'auditoría', 'diagnóstico', 'fraude', 'inconsistencia', 'salud',
        'semáforo', 'alerta', 'exception', 'bug',
        'calidad de datos', 'datos duplicados', 'integridad', 'validación',
        # === Nuevas keywords v2 ===
        'duplicado', 'duplicados', 'huérfano', 'referencial', 'secuencia rota',
        'campo vacío', 'reconciliación', 'conciliación stock', 'acceso inusual',
        'operación masiva', 'borrado masivo', 'base de datos', 'configuración riesgosa',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        texto = (mensaje or '').lower()
        advertencias = []
        accion = getattr(consulta, 'accion_sugerida', '')

        if accion == 'diagnosticar_error' and not any(
            x in texto for x in ['error', 'falla', 'traceback', 'no funciona', 'exception']
        ):
            return ResultadoPreEjecucion(
                permitido=False,
                consulta=consulta,
                motivo_bloqueo=(
                    "El agente de diagnóstico requiere una descripción explícita del error "
                    "(mensaje, módulo o traceback) para evitar conclusiones no verificables."
                ),
                advertencias=['diagnostico_sin_contexto'],
                confianza_agente=0.35
            )

        if 'traceback' not in texto and accion == 'diagnosticar_error':
            advertencias.append('sin_traceback_detallado')

        # Anti-alucinación: auditorías de calidad requieren modelos específicos
        if accion in ('consistencia_datos', 'integridad_referencial', 'registros_duplicados'):
            advertencias.append('auditoria_datos_solo_lectura_no_modifica')

        # Anti-alucinación: fraude requiere evidencia estadística
        if accion in ('auditoria_fraude', 'detectar_pagos_fantasma', 'accesos_inusuales'):
            advertencias.append('hallazgos_requieren_evidencia_no_afirmar_fraude')

        # Anti-alucinación: reconciliación stock-contable es compleja
        if accion == 'reconciliacion_stock_contable':
            advertencias.append('reconciliacion_puede_tener_diferencias_por_timing')

        # Incluir contexto de parámetros del usuario
        advertencias.extend(self._advertencias_de_parametros(consulta))

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.89
        )

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        resultado = super().post_ejecucion(consulta, respuesta, df, error)

        # Anti-alucinación: si el diagnóstico no encontró problemas, ajustar confianza alta
        if not error and df is not None and hasattr(df, '__len__') and len(df) == 0:
            accion = getattr(consulta, 'accion_sugerida', '')
            if accion in ('registros_duplicados', 'campos_vacios_criticos', 'secuencias_rotas'):
                resultado.observaciones.append('auditoria_sin_hallazgos_buena_senal')
                resultado.confianza_datos = max(resultado.confianza_datos, 0.90)

        # Anti-alucinación: severidad debe ser proporcional a la evidencia
        resp_lower = (respuesta or '').lower()
        if 'crítico' in resp_lower or 'fraude confirmado' in resp_lower:
            if df is None or (hasattr(df, '__len__') and len(df) < 3):
                resultado.observaciones.append('severidad_alta_con_poca_evidencia')
                resultado.confianza_datos = min(resultado.confianza_datos, 0.50)

        return resultado

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta

        hallazgos = []

        try:
            nulos = int(df.isna().sum().sum())
            if nulos > 0:
                hallazgos.append(f"- Valores nulos detectados: {nulos}")
        except Exception:
            pass

        try:
            duplicados = int(df.duplicated().sum())
            if duplicados > 0:
                hallazgos.append(f"- Filas potencialmente duplicadas: {duplicados}")
        except Exception:
            pass

        if not hallazgos or 'Diagnóstico del agente' in (respuesta or ''):
            return respuesta

        return respuesta + "\n\n**Diagnóstico del agente:**\n" + "\n".join(hallazgos)


class AgentConsultasOdoo(AgenteEspecializadoBase):
    """Consultor funcional Odoo con 20+ años de experiencia en ERP."""
    id_agente = "agente_odoo"
    prompt_base = (
        "Eres un consultor funcional Odoo certificado con 20+ años implementando y administrando "
        "ERPs en empresas de todos los tamaños. Conoces a profundidad los modelos de datos de Odoo "
        "(sale.order, purchase.order, account.move, stock.quant, res.partner, hr.employee, etc.). "
        "Puedes explicar relaciones entre modelos, campos técnicos, flujos de trabajo y configuraciones. "
        "Respondes consultas sobre el sistema, usuarios, accesos y estructura de datos. "
        "Siempre mencionas el modelo técnico junto con el nombre funcional."
    )
    acciones_soportadas = {
        'info_sistema', 'explicar_modelo', 'consultar_usuarios', 'actividad_usuarios',
        'ayuda', 'consultar_proyectos', 'tareas',
        'consultar_manual', 'info_conexion', 'mostrar_capacidades',
        'consulta_dinamica', 'generar_pdf_profesional',
        'generar_pdf', 'generar_excel',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'explorar_modelo',               # Navegar estructura de un modelo Odoo específico
        'campos_modelo',                 # Listar todos los campos de un modelo con metadatos
        'relaciones_modelo',             # Visualizar relaciones Many2one/One2many/Many2many
        'flujo_trabajo_modelo',          # Explicar el workflow/estados de un modelo
        'permisos_usuario',              # Verificar permisos y grupos de un usuario
        'log_acciones_usuario',          # Historial de acciones de un usuario
        'modulos_instalados',            # Listar módulos instalados y su estado
        'ir_cron_activos',               # Tareas programadas (cron) activas
        'parametros_sistema',            # Parámetros de configuración del sistema
        'version_odoo',                  # Versión del servidor y módulos
        'consulta_sql_segura',           # Consulta de solo lectura con validación SQL
    }
    palabras_clave_prompt = {
        'odoo', 'sistema', 'modelo', 'campo', 'configuración', 'usuario', 'usuarios',
        'acceso', 'permiso', 'módulo', 'versión', 'conexión', 'proyecto', 'tarea',
        'técnico', 'erp', 'flujo', 'workflow',
        'manual', 'documentación', 'capacidades', 'qué puedes', 'pdf', 'consulta libre',
        # === Nuevas keywords v2 ===
        'relación', 'many2one', 'one2many', 'many2many', 'ir.cron', 'cron',
        'tarea programada', 'parámetros', 'instalado', 'estructura',
        'query', 'sql', 'explorar', 'navegar modelo',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = []
        texto = (mensaje or '').lower()

        # Regla: si pide modificar datos del sistema, bloquear
        if any(x in texto for x in ['borrar', 'eliminar', 'modificar', 'cambiar permiso', 'crear usuario']):
            return ResultadoPreEjecucion(
                permitido=False,
                consulta=consulta,
                motivo_bloqueo=(
                    "ANDROMEDA opera en modo solo lectura. Las operaciones de escritura sobre "
                    "usuarios, permisos o configuración del sistema deben realizarse directamente en Odoo."
                ),
                advertencias=['operacion_escritura_bloqueada'],
                confianza_agente=0.95
            )

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.88
        )

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta
        try:
            n_reg = len(df)
            n_cols = len(df.columns)
            nulos = int(df.isna().sum().sum())
            completitud = ((n_reg * n_cols - nulos) / max(1, n_reg * n_cols)) * 100
            linea = (
                f"\n\n**Metadatos del agente Odoo:**\n"
                f"- Registros: {n_reg}\n"
                f"- Campos: {n_cols}\n"
                f"- Completitud de datos: {completitud:.1f}%"
            )
            if 'Metadatos del agente Odoo' not in (respuesta or ''):
                return respuesta + linea
        except Exception:
            pass
        return respuesta


class AgentCRM(AgenteEspecializadoBase):
    """Experto en CRM y estrategia comercial con 20+ años."""
    id_agente = "agente_crm"
    prompt_base = (
        "Eres un director de desarrollo de negocio con 20+ años de experiencia en CRM, "
        "gestión de pipeline, conversión de leads y retención de clientes. "
        "Analizas el embudo de ventas con métricas: tasa de conversión, tiempo promedio por etapa, "
        "valor ponderado del pipeline, win-rate y churn-rate. "
        "Diferencias leads fríos de calientes con criterios objetivos. "
        "Recomiendas acciones de nurturing y seguimiento basadas en datos, no intuición."
    )
    acciones_soportadas = {
        'consultar_crm', 'analisis_crm', 'analizar_churn', 'clientes_olvidados',
        'clientes_analisis',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'pipeline_etapas',               # Análisis por etapa del pipeline (embudo)
        'conversion_leads',              # Tasa de conversión de leads a oportunidades
        'actividades_pendientes',        # Actividades/tareas pendientes de seguimiento
        'oportunidades_estancadas',      # Oportunidades sin movimiento > N días
        'valor_pipeline',                # Valor ponderado total del pipeline
        'win_rate',                      # Tasa de cierre (ganadas / total cerradas)
        'tiempo_cierre_promedio',        # Días promedio del lead al cierre
        'leads_por_origen',              # Leads agrupados por fuente/origen
        'clientes_por_etapa',            # Distribución de clientes por etapa CRM
        'oportunidades_por_vendedor',    # Pipeline por vendedor
        'prediccion_churn',              # Predicción de abandono de clientes
        'lifetime_value',                # Customer Lifetime Value estimado
        'reactivacion_clientes',         # Clientes inactivos con potencial de reactivación
    }
    palabras_clave_prompt = {
        'crm', 'pipeline', 'oportunidad', 'oportunidades', 'lead', 'leads', 'prospecto',
        'embudo', 'conversión', 'churn', 'retención', 'cliente olvidado', 'seguimiento',
        'etapa', 'win rate', 'cierre',
        'análisis de clientes', 'fidelización', 'recurrencia', 'lifetime value',
        # === Nuevas keywords v2 ===
        'funnel', 'tasa de cierre', 'actividades', 'estancado', 'inactivo',
        'reactivar', 'origen lead', 'fuente', 'ltv', 'valor pipeline',
        'seguimiento pendiente', 'nurturing', 'prospeción',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = []
        temp = getattr(consulta, 'temporalidad', {}) or {}
        texto = (mensaje or '').lower()

        accion = getattr(consulta, 'accion_sugerida', '')
        if accion in ('analizar_churn', 'clientes_olvidados', 'prediccion_churn', 'reactivacion_clientes'):
            if not temp.get('fecha_inicio'):
                hoy = datetime.now()
                temp['fecha_inicio'] = (hoy - timedelta(days=90)).strftime('%Y-%m-%d')
                temp['fecha_fin'] = hoy.strftime('%Y-%m-%d')
                consulta.temporalidad = temp
                advertencias.append('churn_requiere_90_dias_minimo')

        # Anti-alucinación: LTV requiere historial largo
        if accion == 'lifetime_value':
            if not temp.get('fecha_inicio'):
                hoy = datetime.now()
                temp['fecha_inicio'] = (hoy - timedelta(days=365)).strftime('%Y-%m-%d')
                temp['fecha_fin'] = hoy.strftime('%Y-%m-%d')
                consulta.temporalidad = temp
                advertencias.append('ltv_requiere_historial_12_meses_minimo')

        # Anti-alucinación: win rate necesita oportunidades cerradas
        if accion == 'win_rate' and not any(x in texto for x in ['ganada', 'perdida', 'cerrada', 'won', 'lost']):
            advertencias.append('win_rate_calcula_solo_oportunidades_cerradas')

        # Incluir contexto de parámetros del usuario
        advertencias.extend(self._advertencias_de_parametros(consulta))

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.88
        )

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        resultado = super().post_ejecucion(consulta, respuesta, df, error)

        # Anti-alucinación: si se mencionan porcentajes de conversión inverosímiles
        if not error and df is not None and hasattr(df, '__len__'):
            accion = getattr(consulta, 'accion_sugerida', '')
            if accion in ('conversion_leads', 'win_rate') and len(df) < 5:
                resultado.observaciones.append('muestra_crm_muy_pequena_para_porcentajes_confiables')
                resultado.confianza_datos = min(resultado.confianza_datos, 0.55)

        return resultado

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta
        try:
            hallazgos = []
            if 'expected_revenue' in df.columns:
                import pandas as pd
                rev = pd.to_numeric(df['expected_revenue'], errors='coerce').dropna()
                if not rev.empty:
                    hallazgos.append(f"- Valor total pipeline: ${rev.sum():,.2f}")
                    hallazgos.append(f"- Oportunidades analizadas: {len(rev)}")
                    hallazgos.append(f"- Valor promedio: ${rev.mean():,.2f}")
            if 'probability' in df.columns and 'expected_revenue' in df.columns:
                import pandas as pd
                prob = pd.to_numeric(df['probability'], errors='coerce').fillna(0)
                rev_all = pd.to_numeric(df['expected_revenue'], errors='coerce').fillna(0)
                ponderado = (rev_all * prob / 100).sum()
                if ponderado > 0:
                    hallazgos.append(f"- Valor ponderado (prob.): ${ponderado:,.2f}")
            if not hallazgos or 'Análisis del agente CRM' in (respuesta or ''):
                return respuesta
            return respuesta + "\n\n**Análisis del agente CRM:**\n" + "\n".join(hallazgos)
        except Exception:
            pass
        return respuesta


class AgentCompras(AgenteEspecializadoBase):
    """Experto en compras y gestión de proveedores con 20+ años."""
    id_agente = "agente_compras"
    prompt_base = (
        "Eres un director de compras con 20+ años de experiencia en procurement, negociación "
        "con proveedores y gestión de la cadena de abastecimiento. "
        "Analizas: costo total de adquisición (TCO), lead times, concentración de proveedores, "
        "cumplimiento de entregas y variaciones de precio. "
        "Siempre alertas sobre riesgos de proveedor único y recomiendas diversificación. "
        "Calculas ahorros potenciales y priorizas por impacto en el negocio."
    )
    acciones_soportadas = {
        'consultar_compras', 'analisis_compras', 'top_proveedores',
        'kpis_compras',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'evaluacion_proveedores',        # Scorecard de proveedores (cumplimiento, calidad, costo)
        'lead_time_proveedores',         # Tiempos de entrega promedio por proveedor
        'concentracion_proveedores',     # Riesgo de concentración (índice Herfindahl)
        'comparativa_precios',           # Comparativa de precios entre proveedores
        'ordenes_pendientes',            # Órdenes de compra pendientes de recibir
        'cumplimiento_entregas',         # % de entregas a tiempo vs tardias
        'compras_por_categoria',         # Gasto agrupado por categoría de producto
        'compras_recurrentes',           # Compras periódicas y patrones de reorden
        'ahorro_potencial',              # Análisis de ahorros potenciales (consolidación, negociación)
        'compras_urgentes',              # Compras urgentes/no planificadas vs programadas
        'variacion_precios',             # Variación de precios unitarios en el tiempo
        'gasto_por_departamento',        # Gasto de compras por departamento solicitante
    }
    palabras_clave_prompt = {
        'compra', 'compras', 'proveedor', 'proveedores', 'adquisición', 'purchase',
        'orden de compra', 'gasto', 'abastecimiento', 'cotización', 'licitación',
        'costo', 'costeo', 'flete',
        'procurement', 'presupuesto compras', 'evaluación proveedores',
        # === Nuevas keywords v2 ===
        'lead time', 'tiempo entrega', 'concentración proveedor', 'precio unitario',
        'pendiente recibir', 'cumplimiento entrega', 'ahorro', 'urgente',
        'recurrente', 'variación precio', 'negociación', 'scorecard',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = []
        temp = getattr(consulta, 'temporalidad', {}) or {}
        texto = (mensaje or '').lower()

        if not temp.get('fecha_inicio') and not temp.get('fecha_fin'):
            hoy = datetime.now()
            temp['fecha_inicio'] = (hoy - timedelta(days=30)).strftime('%Y-%m-%d')
            temp['fecha_fin'] = hoy.strftime('%Y-%m-%d')
            consulta.temporalidad = temp
            advertencias.append('rango_compras_default_30_dias')

        # Anti-alucinación: evaluación de proveedores requiere historial suficiente
        accion = getattr(consulta, 'accion_sugerida', '')
        if accion == 'evaluacion_proveedores':
            if not temp.get('fecha_inicio'):
                hoy = datetime.now()
                temp['fecha_inicio'] = (hoy - timedelta(days=180)).strftime('%Y-%m-%d')
                temp['fecha_fin'] = hoy.strftime('%Y-%m-%d')
                consulta.temporalidad = temp
            advertencias.append('evaluacion_proveedor_requiere_historial_6_meses')

        # Anti-alucinación: concentración necesita múltiples proveedores para ser significativa
        if accion == 'concentracion_proveedores':
            advertencias.append('concentracion_requiere_minimo_3_proveedores_activos')

        # Anti-alucinación: ahorro potencial no es ahorro realizado
        if accion == 'ahorro_potencial':
            advertencias.append('ahorro_es_estimacion_no_garantia')

        # Incluir contexto de parámetros del usuario
        advertencias.extend(self._advertencias_de_parametros(consulta))

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.90
        )

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        resultado = super().post_ejecucion(consulta, respuesta, df, error)

        # Anti-alucinación: verificar que los montos de compra son razonables
        if df is not None and hasattr(df, 'columns') and not error:
            for col in ('amount_total', 'amount_untaxed'):
                if col in df.columns:
                    import pandas as pd
                    vals = pd.to_numeric(df[col], errors='coerce')
                    if vals.notna().any() and (vals < 0).any():
                        resultado.observaciones.append(f'compras_con_montos_negativos_verificar_{col}')

        return resultado

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta
        try:
            hallazgos = []
            if 'amount_total' in df.columns:
                import pandas as pd
                montos = pd.to_numeric(df['amount_total'], errors='coerce').dropna()
                if not montos.empty:
                    hallazgos.append(f"- Gasto total: ${montos.sum():,.2f}")
                    hallazgos.append(f"- Órdenes analizadas: {len(montos)}")
            if 'partner_id' in df.columns:
                n_prov = df['partner_id'].nunique()
                hallazgos.append(f"- Proveedores distintos: {n_prov}")
            if not hallazgos or 'Análisis del agente de compras' in (respuesta or ''):
                return respuesta
            return respuesta + "\n\n**Análisis del agente de compras:**\n" + "\n".join(hallazgos)
        except Exception:
            pass
        return respuesta


class AgentPDV(AgenteEspecializadoBase):
    """Experto en punto de venta y operación de tiendas con 20+ años."""
    id_agente = "agente_pdv"
    prompt_base = (
        "Eres un director de operaciones retail con 20+ años de experiencia en punto de venta, "
        "gestión de tiendas y experiencia del cliente en piso. "
        "Dominas: análisis de sesiones POS, cuadres de caja, métodos de pago, tickets promedio, "
        "productividad por cajero y detección de inconsistencias operativas. "
        "Siempre verificas que las sesiones estén cuadradas antes de reportar cifras. "
        "Alertas sobre sesiones abiertas, diferencias de caja y productos sin costo configurado."
    )
    acciones_soportadas = {
        'analisis_pos', 'sesiones_pos', 'sesiones_abiertas', 'metodos_pago',
        'productos_costo_cero', 'productos_sin_categoria',
        'consultar_pos', 'pos_completo',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'productividad_cajero',          # Ventas por cajero, tickets/hora, monto promedio
        'horarios_pico',                 # Análisis de horas punta de venta
        'devoluciones_pos',              # Devoluciones y cancelaciones en POS
        'descuentos_pos',                # Descuentos aplicados en punto de venta
        'cuadre_caja',                   # Diferencias entre monto esperado y real
        'pos_por_sucursal',              # Comparativa de rendimiento entre sucursales
        'ticket_detalle',                # Detalle de un ticket específico
        'productos_mas_vendidos_pos',    # Top productos solo en POS
        'merma_pos',                     # Productos con merma en punto de venta
        'rendimiento_terminal',          # Rendimiento por terminal/caja
        'cierre_caja_pendiente',         # Sesiones que debieron cerrarse y no
        'ventas_pos_vs_ecommerce',       # Comparativa canal físico vs digital
    }
    palabras_clave_prompt = {
        'pos', 'punto de venta', 'pdv', 'caja', 'cajero', 'sesión', 'sesiones',
        'ticket', 'arqueo', 'cuadre', 'cierre de caja', 'método de pago',
        'efectivo', 'tarjeta', 'terminal', 'tienda',
        'venta en piso', 'corte de caja', 'devolución pos',
        # === Nuevas keywords v2 ===
        'productividad cajero', 'hora punta', 'horario pico', 'sucursal',
        'descuento pos', 'cancelación', 'diferencia caja', 'faltante caja',
        'sobrante', 'merma', 'terminal', 'rendimiento sucursal',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = []
        texto = (mensaje or '').lower()
        accion = getattr(consulta, 'accion_sugerida', '')

        # Regla: para sesiones abiertas y cierre_caja_pendiente no necesitamos temporalidad
        if accion not in ('sesiones_abiertas', 'cierre_caja_pendiente'):
            temp = getattr(consulta, 'temporalidad', {}) or {}
            if not temp.get('fecha_inicio') and not temp.get('fecha_fin'):
                hoy = datetime.now()
                temp['fecha_inicio'] = (hoy - timedelta(days=7)).strftime('%Y-%m-%d')
                temp['fecha_fin'] = hoy.strftime('%Y-%m-%d')
                consulta.temporalidad = temp
                advertencias.append('rango_pos_default_7_dias')

        # Anti-alucinación: cuadre de caja requiere sesión cerrada
        if accion == 'cuadre_caja':
            advertencias.append('cuadre_solo_confiable_en_sesiones_cerradas')

        # Anti-alucinación: productividad por cajero necesita campo user_id
        if accion == 'productividad_cajero':
            advertencias.append('productividad_depende_de_user_id_en_pos_order')

        # Anti-alucinación: comparativa POS vs ecommerce requiere ambos canales activos
        if accion == 'ventas_pos_vs_ecommerce':
            advertencias.append('comparativa_requiere_canal_ecommerce_configurado')

        # Incluir contexto de parámetros del usuario
        advertencias.extend(self._advertencias_de_parametros(consulta))

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.91
        )

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        resultado = super().post_ejecucion(consulta, respuesta, df, error)

        # Anti-alucinación: diferencias de caja deben ser explícitas
        accion = getattr(consulta, 'accion_sugerida', '')
        if accion == 'cuadre_caja' and df is not None and hasattr(df, 'columns'):
            if 'difference' in df.columns or 'cash_register_difference' in df.columns:
                import pandas as pd
                col_diff = 'difference' if 'difference' in df.columns else 'cash_register_difference'
                vals = pd.to_numeric(df[col_diff], errors='coerce')
                if vals.notna().any() and (vals.abs() > 1000).any():
                    resultado.observaciones.append('diferencias_caja_significativas_revisar')

        return resultado

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta
        try:
            hallazgos = []
            if 'amount_total' in df.columns:
                import pandas as pd
                ventas = pd.to_numeric(df['amount_total'], errors='coerce').dropna()
                if not ventas.empty:
                    hallazgos.append(f"- Ventas POS total: ${ventas.sum():,.2f}")
                    hallazgos.append(f"- Tickets: {len(ventas)}")
                    hallazgos.append(f"- Ticket promedio: ${ventas.mean():,.2f}")
            if not hallazgos or 'Análisis del agente PDV' in (respuesta or ''):
                return respuesta
            return respuesta + "\n\n**Análisis del agente PDV:**\n" + "\n".join(hallazgos)
        except Exception:
            pass
        return respuesta


class AgentPredicciones(AgenteEspecializadoBase):
    """Experto en modelos predictivos y forecasting con 20+ años."""
    id_agente = "agente_predicciones"
    prompt_base = (
        "Eres un científico de datos senior con 20+ años de experiencia en forecasting, "
        "modelado predictivo y simulación estocástica. "
        "Dominas: regresión lineal/polinomial, ARIMA, LSTM, simulación Monte Carlo, "
        "bootstrapping y modelos de series de tiempo. "
        "Siempre reportas intervalos de confianza, no solo valores puntuales. "
        "Adviertes las limitaciones del modelo: tamaño de muestra, estacionalidad no capturada, "
        "eventos atípicos y horizonte máximo confiable de predicción. "
        "Nunca presentas una predicción como certeza; usas lenguaje probabilístico explícito."
    )
    acciones_soportadas = {
        'tendencia', 'predecir_agotamiento', 'prediccion_ventas', 'prediccion_demanda',
        'simulacion_montecarlo', 'forecast_financiero', 'forecast_inventario',
        'prediccion_churn', 'proyeccion_crecimiento',
        'prediccion_ventas_inteligente', 'prediccion_inventario_inteligente',
        'prediccion_ml', 'tendencias_ml', 'prediccion_lstm',
        'predecir', 'predecir_ventas',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'forecast_estacional',           # Pronóstico con ajuste estacional
        'prediccion_demanda_producto',   # Demanda futura por producto específico
        'escenarios_what_if',            # Simulación de escenarios (optimista/pesimista/base)
        'alertas_predictivas',           # Alertas automáticas de umbrales predictivos
        'prediccion_flujo_caja',         # Forecast de flujo de efectivo
        'prediccion_rotacion_personal',  # Predicción de rotación de personal
        'modelo_propension_compra',      # Probabilidad de recompra por cliente
        'deteccion_tendencia_cambio',    # Detección de cambio de tendencia (changepoint)
        'forecast_multiproducto',        # Pronóstico cruzado de múltiples productos
        'backtesting_modelo',            # Validación retrospectiva de modelos predictivos
        'intervalos_confianza',          # Cálculo explícito de intervalos de confianza
    }
    palabras_clave_prompt = {
        'predecir', 'predicción', 'forecast', 'proyección', 'proyectar', 'estimar',
        'futuro', 'monte carlo', 'montecarlo', 'simulación', 'lstm', 'serie temporal',
        'tendencia', 'pronóstico', 'regresión', 'modelo predictivo',
        'ml', 'machine learning', 'neural', 'red neuronal', 'arima',
        # === Nuevas keywords v2 ===
        'estacional', 'what if', 'escenario', 'optimista', 'pesimista',
        'alerta predictiva', 'umbral', 'changepoint', 'backtesting',
        'validación modelo', 'intervalo confianza', 'propensión',
        'demanda futura', 'forecast días', 'cuánto se va a vender',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = []
        temp = getattr(consulta, 'temporalidad', {}) or {}

        # Regla: las predicciones necesitan datos históricos suficientes
        if not temp.get('fecha_inicio'):
            hoy = datetime.now()
            temp['fecha_inicio'] = (hoy - timedelta(days=180)).strftime('%Y-%m-%d')
            temp['fecha_fin'] = hoy.strftime('%Y-%m-%d')
            consulta.temporalidad = temp
            advertencias.append('prediccion_requiere_historico_180_dias')

        # Regla: advertir si se pide horizonte de predicción muy largo
        params = getattr(consulta, 'parametros', {}) or {}
        horizonte = params.get('horizonte_dias', 0)
        if isinstance(horizonte, int) and horizonte > 90:
            advertencias.append('horizonte_prediccion_largo_menor_confianza')

        # Incluir contexto de parámetros del usuario
        advertencias.extend(self._advertencias_de_parametros(consulta))

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.85
        )

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        resultado = super().post_ejecucion(consulta, respuesta, df, error)

        # Regla: registrar internamente que falta disclaimer, sin alterar la respuesta.
        if not error and 'intervalo de confianza' not in (respuesta or '').lower():
            resultado.observaciones.append('disclaimer_prediccion_agregado')

        return resultado

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta

        try:
            columnas_numericas = df.select_dtypes(include=['number']).columns.tolist()
        except Exception:
            columnas_numericas = []

        if not columnas_numericas or 'Tendencia observada por el agente' in (respuesta or ''):
            return respuesta

        serie = df[columnas_numericas[0]].dropna()
        if len(serie) < 4:
            return respuesta

        mitad = max(1, len(serie) // 2)
        promedio_inicial = float(serie.iloc[:mitad].mean())
        promedio_final = float(serie.iloc[mitad:].mean())
        delta = promedio_final - promedio_inicial

        if abs(delta) < max(abs(promedio_inicial) * 0.03, 1e-9):
            tendencia = 'estable'
        elif delta > 0:
            tendencia = 'al alza'
        else:
            tendencia = 'a la baja'

        return (
            respuesta
            + "\n\n**Tendencia observada por el agente:**\n"
            + f"- Serie analizada: {columnas_numericas[0]}\n"
            + f"- Comportamiento en la muestra: {tendencia}\n"
            + f"- Promedio inicial: {promedio_inicial:,.2f}\n"
            + f"- Promedio final: {promedio_final:,.2f}"
        )


class AgentMatematicas(AgenteEspecializadoBase):
    """Experto en matemáticas aplicadas y cálculos financieros con 20+ años."""
    id_agente = "agente_matematicas"
    prompt_base = (
        "Eres un actuario y matemático aplicado con 20+ años de experiencia en cálculos financieros, "
        "análisis cuantitativo y modelado matemático empresarial. "
        "Dominas: márgenes brutos/netos/operativos, ROI, ROE, EBITDA, punto de equilibrio (break-even), "
        "tasa interna de retorno (TIR), valor presente neto (VPN), amortización y crecimiento compuesto. "
        "Siempre muestras las fórmulas usadas y los pasos del cálculo para transparencia. "
        "Validas que los inputs tengan sentido antes de calcular (no divides entre cero, "
        "no calculas márgenes con costos negativos sin advertir)."
    )
    acciones_soportadas = {
        'calculo_margenes', 'calculo_rentabilidad', 'calculo_roi', 'calculo_break_even',
        'calculo_crecimiento', 'calculo_descuentos', 'calculo_tir', 'calculo_vpn',
        'calculo_amortizacion', 'calculo_punto_equilibrio',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'analisis_sensibilidad',         # Análisis de sensibilidad (qué pasa si cambia X)
        'calculo_payback',               # Período de recuperación de inversión
        'calculo_wacc',                  # Costo promedio ponderado de capital
        'depreciacion',                  # Cálculo de depreciación de activos
        'calculo_elasticidad',           # Elasticidad precio-demanda
        'analisis_apalancamiento',       # Apalancamiento operativo y financiero
        'calculo_cagr',                  # Tasa de crecimiento anual compuesto
        'calculo_margen_contribucion',   # Margen de contribución por producto/línea
        'calculo_dupont',                # Análisis DuPont (descomposición de ROE)
        'calculo_capital_requerido',     # Capital necesario para operación/expansión
        'proyeccion_financiera',         # Proyección financiera a N meses/años
    }
    palabras_clave_prompt = {
        'calcular', 'cálculo', 'margen', 'rentabilidad', 'roi', 'retorno',
        'break even', 'punto de equilibrio', 'tir', 'vpn', 'amortización',
        'porcentaje', 'tasa', 'crecimiento', 'descuento', 'fórmula',
        'ebitda', 'utilidad', 'ganancia',
        # === Nuevas keywords v2 ===
        'sensibilidad', 'payback', 'wacc', 'depreciación', 'elasticidad',
        'apalancamiento', 'cagr', 'contribución', 'dupont', 'roe',
        'capital requerido', 'proyección financiera', 'inversión',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = []
        params = getattr(consulta, 'parametros', {}) or {}

        # Regla: validar que hay valores numéricos para calcular
        texto = (mensaje or '').lower()
        tiene_numeros = any(c.isdigit() for c in texto)

        if not tiene_numeros and not params:
            advertencias.append('sin_valores_numericos_explicitos_se_usaran_datos_odoo')

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.93
        )

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        resultado = super().post_ejecucion(consulta, respuesta, df, error)

        # Regla: si es cálculo, la confianza es alta si no hubo error
        if not error:
            resultado.confianza_datos = max(resultado.confianza_datos, 0.90)

        return resultado

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta

        try:
            columnas_numericas = df.select_dtypes(include=['number']).columns.tolist()
        except Exception:
            columnas_numericas = []

        if not columnas_numericas or 'Indicadores matemáticos del agente' in (respuesta or ''):
            return respuesta

        lineas = []
        for columna in columnas_numericas[:2]:
            serie = df[columna].dropna()
            if len(serie) < 2:
                continue
            promedio = float(serie.mean())
            if promedio != 0:
                variabilidad = abs(float(serie.std(ddof=0)) / promedio) * 100
                lineas.append(f"- {columna}: promedio {promedio:,.2f}, variabilidad {variabilidad:,.2f}%")

        if not lineas:
            return respuesta

        return respuesta + "\n\n**Indicadores matemáticos del agente:**\n" + "\n".join(lineas)


class AgentEstadistica(AgenteEspecializadoBase):
    """Experto en estadística y ciencia de datos con 20+ años."""
    id_agente = "agente_estadistica"
    prompt_base = (
        "Eres un científico de datos y estadístico senior con 20+ años de experiencia en "
        "análisis cuantitativo, ciencia de datos y business intelligence. "
        "Dominas: estadística descriptiva (media, mediana, moda, desviación estándar, percentiles), "
        "análisis de correlación (Pearson, Spearman), segmentación (clustering K-means, RFM), "
        "detección de outliers (IQR, Z-score), distribuciones, análisis de regresión, "
        "y construcción de dashboards de KPIs empresariales. "
        "Siempre indicas tamaño de muestra, significancia estadística y limitaciones del análisis. "
        "No sobreinterpretas correlaciones como causalidades."
    )
    acciones_soportadas = {
        'analisis_360', 'analisis_estadistico', 'correlacion_variables',
        'segmentacion_datos', 'distribucion_datos', 'outliers_datos',
        'kpis_empresariales', 'analisis_rfm', 'analisis_pareto',
        'analisis_cohort', 'benchmarking',
        'dashboard_kpis_empresariales', 'kpis_comerciales', 'kpis_talento',
        'kpis_operaciones', 'kpis_tiendas', 'kpis_por_tienda',
        'segmentacion_clientes', 'anomalias_ml',
        'dashboard_kpis', 'dashboard_automatico',
        'reporte_bi', 'reporte_ejecutivo', 'analisis_inteligente',
        'kpi_picking_cedis', 'kpi_ventas_por_canal', 'kpi_ventas_por_marca',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'analisis_tendencia_avanzado',   # Descomposición de tendencia + estacionalidad + residuo
        'test_hipotesis',                # Pruebas estadísticas (t-test, chi-cuadrado, ANOVA)
        'regresion_multiple',            # Regresión con múltiples variables independientes
        'analisis_varianza',             # ANOVA: comparación de medias entre grupos
        'mapa_calor',                    # Heatmap: correlación o intensidad bidimensional
        'analisis_canasta',              # Market basket analysis (asociación de productos)
        'curva_abc_ventas',              # ABC por ingresos (cuántos productos generan 80%)
        'indice_gini_clientes',          # Concentración de ingresos por cliente (Gini)
        'estacionalidad_avanzada',       # Detección automática de patrones estacionales
        'volatilidad_ventas',            # Coeficiente de variación y estabilidad de ventas
        'analisis_cohorte_retencion',    # Retención de cohortes por mes de adquisición
        'score_salud_negocio',           # Índice compuesto de salud empresarial
        'comparativa_tiendas',           # Benchmarking estadístico entre tiendas
        'ranking_multidimensional',      # Ranking ponderado por múltiples KPIs
        'kpis_personalizados',           # KPIs definidos por el usuario dinámicamente
    }
    palabras_clave_prompt = {
        'estadística', 'estadístico', 'correlación', 'segmentación', 'segmentar',
        'distribución', 'outlier', 'atípico', 'percentil', 'desviación',
        'promedio', 'mediana', 'varianza', 'kpi', 'kpis', 'indicador',
        'pareto', '80/20', 'rfm', 'cohort', 'cluster', 'benchmark',
        'análisis de datos', 'data science', '360',
        'dashboard', 'reporte ejecutivo', 'bi', 'business intelligence',
        'tablero', 'métricas', 'resumen ejecutivo',
        # === Nuevas keywords v2 ===
        'hipótesis', 't-test', 'chi cuadrado', 'anova', 'regresión',
        'mapa de calor', 'heatmap', 'canasta', 'basket', 'gini',
        'volatilidad', 'cohorte', 'retención', 'salud negocio',
        'ranking', 'score', 'multidimensional', 'personalizado',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = []
        temp = getattr(consulta, 'temporalidad', {}) or {}

        # Regla: análisis estadísticos necesitan datos suficientes
        if not temp.get('fecha_inicio'):
            hoy = datetime.now()
            temp['fecha_inicio'] = (hoy - timedelta(days=90)).strftime('%Y-%m-%d')
            temp['fecha_fin'] = hoy.strftime('%Y-%m-%d')
            consulta.temporalidad = temp
            advertencias.append('estadistica_default_90_dias')

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.90
        )

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        resultado = super().post_ejecucion(consulta, respuesta, df, error)

        # Regla: recordar limitaciones de muestra si hay pocos datos
        if df is not None and hasattr(df, '__len__') and len(df) < 30:
            resultado.observaciones.append('muestra_pequena_n_menor_30')
            resultado.confianza_datos = min(resultado.confianza_datos, 0.65)

        return resultado

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta

        try:
            columnas_numericas = df.select_dtypes(include=['number']).columns.tolist()
        except Exception:
            columnas_numericas = []

        if not columnas_numericas or 'Resumen estadístico del agente' in (respuesta or ''):
            return respuesta

        lineas = []
        for columna in columnas_numericas[:3]:
            serie = df[columna].dropna()
            if serie.empty:
                continue
            lineas.append(
                f"- {columna}: media {serie.mean():,.2f}, mediana {serie.median():,.2f}, desviación {serie.std(ddof=0):,.2f}"
            )

        if not lineas:
            return respuesta

        return respuesta + "\n\n**Resumen estadístico del agente:**\n" + "\n".join(lineas)


class AgentRRHH(AgenteEspecializadoBase):
    """Experto en recursos humanos y gestión del talento con 20+ años."""
    id_agente = "agente_rrhh"
    prompt_base = (
        "Eres un director de recursos humanos con 20+ años de experiencia en gestión del talento, "
        "nóminas, relaciones laborales y desarrollo organizacional. "
        "Analizas: headcount, rotación de personal, ausentismo, costos de nómina, "
        "distribución por departamento, antigüedad y cumplimiento de contratos. "
        "Siempre manejas datos de colaboradores con confidencialidad; no expones salarios "
        "individuales a menos que se solicite explícitamente con filtros específicos. "
        "Alertas sobre vencimientos de contratos, rotación elevada y concentración de riesgo."
    )
    acciones_soportadas = {
        'consultar_empleados', 'analisis_rh', 'headcount', 'departamentos',
        'rotacion_personal', 'asistencia', 'ausencias', 'nomina', 'contratos',
        # === Nuevas acciones v2 — certeza y profundidad ===
        'costo_por_empleado',            # Costo total empresa por empleado (nómina + prestaciones)
        'ausentismo_analisis',           # Análisis profundo de ausentismo con patrones
        'vencimiento_contratos',         # Contratos próximos a vencer con alertas
        'brecha_salarial',               # Análisis de equidad salarial por género/puesto
        'productividad_departamento',    # Métricas de productividad por área
        'antiguedad_empleados',          # Distribución de antigüedad del personal
        'horas_extra',                   # Análisis de horas extra por departamento/empleado
        'vacaciones_pendientes',         # Días de vacaciones pendientes por empleado
        'costo_rotacion',                # Costo estimado de la rotación de personal
        'clima_organizacional',          # Indicadores de clima laboral (basado en datos)
        'cumplimiento_jornada',          # Análisis de cumplimiento de horarios de trabajo
        'estructura_organizacional',     # Organigrama y estructura jerárquica
        'incapacidades',                 # Análisis de incapacidades médicas
        'prestaciones_resumen',          # Resumen de prestaciones y beneficios
    }
    palabras_clave_prompt = {
        'empleado', 'empleados', 'personal', 'rh', 'recursos humanos', 'nómina',
        'nomina', 'salario', 'sueldo', 'departamento', 'headcount', 'rotación',
        'asistencia', 'vacaciones', 'permiso', 'contrato', 'ausencia', 'falta',
        'colaborador', 'plantilla', 'puesto',
        # === Nuevas keywords v2 ===
        'ausentismo', 'brecha salarial', 'equidad', 'antigüedad', 'horas extra',
        'overtime', 'productividad', 'costo empleado', 'rotación personal',
        'incapacidad', 'prestación', 'organigrama', 'jornada', 'clima laboral',
        'vencimiento contrato', 'bajada', 'alta', 'baja empleado',
    }

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        advertencias = []
        params = getattr(consulta, 'parametros', {}) or {}

        # Regla: limitar resultados de nómina por confidencialidad
        accion = getattr(consulta, 'accion_sugerida', '')
        if accion == 'nomina':
            limite = params.get('limite')
            if not isinstance(limite, int) or limite > 50:
                params['limite'] = 50
                consulta.parametros = params
                advertencias.append('nomina_limitada_50_por_confidencialidad')

        # Incluir contexto de parámetros del usuario
        advertencias.extend(self._advertencias_de_parametros(consulta))

        return ResultadoPreEjecucion(
            permitido=True,
            consulta=consulta,
            advertencias=advertencias,
            confianza_agente=0.88
        )

    def enriquecer_respuesta(self, consulta: Any, respuesta: str, df: Any, mensaje: str = "") -> str:
        if df is None or not hasattr(df, 'empty') or df.empty:
            return respuesta
        try:
            hallazgos = []
            n = len(df)
            hallazgos.append(f"- Registros analizados: {n}")
            if 'department_id' in df.columns:
                n_dep = df['department_id'].nunique()
                hallazgos.append(f"- Departamentos involucrados: {n_dep}")
            if 'wage' in df.columns:
                import pandas as pd
                salarios = pd.to_numeric(df['wage'], errors='coerce').dropna()
                if not salarios.empty:
                    hallazgos.append(f"- Nómina promedio: ${salarios.mean():,.2f}")
            if len(hallazgos) <= 1 or 'Análisis del agente RRHH' in (respuesta or ''):
                return respuesta
            return respuesta + "\n\n**Análisis del agente RRHH:**\n" + "\n".join(hallazgos)
        except Exception:
            pass
        return respuesta


class AgentValidadorFinal(AgenteEspecializadoBase):
    id_agente = "agente_validador_final"
    prompt_base = (
        "Validar la respuesta final antes de entregarla. "
        "Reducir confianza si hay afirmaciones fuertes sin datos, respuesta pobre o contradicciones. "
        "Priorizar honestidad y trazabilidad sobre fluidez."
    )
    acciones_soportadas: Set[str] = set()
    palabras_clave_prompt: Set[str] = set()

    def post_ejecucion(self, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        base = super().post_ejecucion(consulta, respuesta, df, error=error)
        confianza = base.confianza_datos
        observaciones = list(base.observaciones)
        texto = (respuesta or "").strip()
        texto_lower = texto.lower()

        if len(texto) < 24:
            confianza = min(confianza, 0.45)
            observaciones.append('respuesta_demasiado_corta')

        if df is not None and hasattr(df, 'empty') and not df.empty:
            if not any(ch.isdigit() for ch in texto):
                confianza = min(confianza, 0.62)
                observaciones.append('sin_evidencia_numerica')
            if any(token in texto_lower for token in ['no pude', 'no disponible', 'sin datos']):
                confianza = min(confianza, 0.55)
                observaciones.append('descargo_con_datos_existentes')
        else:
            hay_descargo = any(
                token in texto_lower
                for token in ['no hay', 'no se encontró', 'no disponible', 'no pude obtener', 'sin datos']
            )
            afirmaciones_fuertes = any(
                token in texto_lower
                for token in ['total', 'promedio', 'creció', 'disminuyó', 'se observó', 'se registró', 'ranking', 'top']
            )
            if afirmaciones_fuertes and not hay_descargo:
                confianza = min(confianza, 0.35)
                observaciones.append('afirmacion_fuerte_sin_datos')

        if error or confianza < 0.65:
            observaciones.append('requiere_regeneracion')

        return ResultadoPostEjecucion(
            respuesta=respuesta,
            confianza_datos=max(0.0, min(1.0, confianza)),
            observaciones=list(dict.fromkeys(observaciones))
        )


# ============================================================
# CADENA MULTI-AGENTE — Pipeline Colaborativo
# ============================================================


@dataclass
class PasoAgente:
    """Resultado de un paso individual en la cadena multi-agente."""
    agente_id: str
    rol: str                                    # 'principal', 'datos', 'enriquecimiento', 'calculo', 'validacion', 'validacion_final'
    resultado_pre: Optional[ResultadoPreEjecucion] = None
    resultado_post: Optional[ResultadoPostEjecucion] = None
    respuesta_parcial: str = ""
    datos_parciales: Any = None
    confianza: float = 0.0
    exito: bool = True
    error: str = ""


@dataclass
class ResultadoCadena:
    """Resultado consolidado de la cadena multi-agente completa."""
    respuesta_final: str
    confianza_consolidada: float
    agentes_involucrados: List[str] = field(default_factory=list)
    pasos: List[PasoAgente] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)
    observaciones: List[str] = field(default_factory=list)
    prompt_combinado: str = ""
    datos_consolidados: Any = None


# Mapa de reglas: qué agentes de soporte se activan según el contexto del prompt
REGLAS_CADENA = {
    # === Predicciones y Tendencias ===
    'tendencia': ['agente_estadistica', 'agente_predicciones'],
    'predicción': ['agente_estadistica', 'agente_predicciones'],
    'prediccion': ['agente_estadistica', 'agente_predicciones'],
    'forecast': ['agente_estadistica', 'agente_predicciones'],
    'proyección': ['agente_estadistica', 'agente_predicciones'],
    'monte carlo': ['agente_predicciones', 'agente_matematicas'],
    'estacional': ['agente_predicciones', 'agente_estadistica'],
    'what if': ['agente_predicciones', 'agente_matematicas'],
    'escenario': ['agente_predicciones', 'agente_matematicas'],

    # === Finanzas y Cálculos ===
    'margen': ['agente_matematicas', 'agente_finanzas'],
    'rentabilidad': ['agente_matematicas', 'agente_finanzas'],
    'roi': ['agente_matematicas', 'agente_finanzas'],
    'calculo': ['agente_matematicas'],
    'cálculo': ['agente_matematicas'],
    'punto de equilibrio': ['agente_matematicas'],
    'break even': ['agente_matematicas', 'agente_finanzas'],
    'tir': ['agente_matematicas', 'agente_finanzas'],
    'vpn': ['agente_matematicas', 'agente_finanzas'],
    'dupont': ['agente_matematicas', 'agente_finanzas'],
    'liquidez': ['agente_finanzas', 'agente_matematicas'],
    'capital de trabajo': ['agente_finanzas', 'agente_matematicas'],
    'ebitda': ['agente_finanzas', 'agente_matematicas'],
    'apalancamiento': ['agente_matematicas', 'agente_finanzas'],

    # === Estadística y Análisis ===
    'comparar': ['agente_estadistica'],
    'comparativa': ['agente_estadistica'],
    'crecimiento': ['agente_estadistica', 'agente_matematicas'],
    'kpi': ['agente_estadistica'],
    'promedio': ['agente_estadistica'],
    'desviación': ['agente_estadistica'],
    'correlación': ['agente_estadistica', 'agente_matematicas'],
    'segmentar': ['agente_estadistica'],
    'rfm': ['agente_estadistica', 'agente_crm'],
    'pareto': ['agente_estadistica'],
    'abc': ['agente_estadistica'],
    'cohort': ['agente_estadistica', 'agente_crm'],
    'outlier': ['agente_estadistica', 'agente_diagnostico'],
    'atípico': ['agente_estadistica', 'agente_diagnostico'],
    'hipótesis': ['agente_estadistica'],
    'regresión': ['agente_estadistica', 'agente_matematicas'],
    'volatilidad': ['agente_estadistica'],
    'heatmap': ['agente_estadistica'],
    'mapa de calor': ['agente_estadistica'],

    # === Agrupaciones que enriquecen ===
    'por marca': ['agente_estadistica'],
    'por tienda': ['agente_estadistica'],
    'por vendedor': ['agente_estadistica'],
    'por sucursal': ['agente_estadistica'],
    'por departamento': ['agente_estadistica'],
    'por categoría': ['agente_estadistica'],
    'por proveedor': ['agente_estadistica'],
    'por cajero': ['agente_estadistica'],

    # === Auditoría y Diagnóstico ===
    'anomalía': ['agente_diagnostico', 'agente_estadistica'],
    'anomalia': ['agente_diagnostico', 'agente_estadistica'],
    'fraude': ['agente_diagnostico', 'agente_estadistica'],
    'duplicado': ['agente_diagnostico'],
    'inconsistencia': ['agente_diagnostico'],
    'reconciliación': ['agente_diagnostico', 'agente_finanzas'],
    'integridad': ['agente_diagnostico'],
    'calidad datos': ['agente_diagnostico'],

    # === Cross-domain: validación cruzada entre agentes ===
    'ventas vs inventario': ['agente_inventario', 'agente_estadistica'],
    'stock vs ventas': ['agente_ventas', 'agente_estadistica'],
    'compras vs ventas': ['agente_ventas', 'agente_estadistica'],
    'facturación vs ventas': ['agente_finanzas', 'agente_estadistica'],
    'cxc vs ventas': ['agente_finanzas', 'agente_estadistica'],
    'nómina vs headcount': ['agente_rrhh', 'agente_matematicas'],
    'inventario vs compras': ['agente_compras', 'agente_estadistica'],
    'pos vs facturación': ['agente_finanzas', 'agente_estadistica'],
    'rotación personal': ['agente_rrhh', 'agente_estadistica'],
    'rotación inventario': ['agente_inventario', 'agente_estadistica'],

    # === CRM y Retención ===
    'churn': ['agente_crm', 'agente_predicciones'],
    'retención': ['agente_crm', 'agente_estadistica'],
    'lifetime value': ['agente_crm', 'agente_matematicas'],
    'ltv': ['agente_crm', 'agente_matematicas'],
    'pipeline': ['agente_crm', 'agente_estadistica'],

    # === Reportes ejecutivos (multi-agente siempre) ===
    'reporte ejecutivo': ['agente_estadistica', 'agente_finanzas'],
    'dashboard': ['agente_estadistica'],
    'resumen ejecutivo': ['agente_estadistica', 'agente_finanzas'],
    '360': ['agente_estadistica', 'agente_diagnostico'],
    'salud negocio': ['agente_finanzas', 'agente_diagnostico', 'agente_estadistica'],
}


class GestorMultiAgente:
    """
    Orquestador de 12 agentes especializados con soporte de cadenas multi-agente.

    Flujo simple (1 agente):
        resolver_agente() → pre_ejecutar() → [ejecución externa] → post_ejecutar()

    Flujo cadena (N agentes colaborativos):
        planificar_cadena(mensaje) → la UI/bot ejecuta cada paso → consolidar_cadena()

    Ejemplo cadena para "¿cómo van las ventas por marca y cuál es su tendencia?":
        1. agente_ventas     (principal)    → obtiene datos de ventas por marca
        2. agente_estadistica (enriquecimiento) → calcula distribución y estadísticas
        3. agente_predicciones (calculo)     → calcula tendencia y forecast
    """

    def __init__(self):
        self.agentes = {
            # --- Agentes core ---
            'agente_ventas': AgentVentas(),
            'agente_inventario': AgentInventarios(),
            'agente_finanzas': AgentFinanzas(),
            'agente_diagnostico': AgentDiagnostico(),
            # --- Agentes expandidos ---
            'agente_odoo': AgentConsultasOdoo(),
            'agente_crm': AgentCRM(),
            'agente_compras': AgentCompras(),
            'agente_pdv': AgentPDV(),
            'agente_predicciones': AgentPredicciones(),
            'agente_matematicas': AgentMatematicas(),
            'agente_estadistica': AgentEstadistica(),
            'agente_rrhh': AgentRRHH(),
            'agente_validador_final': AgentValidadorFinal(),
        }
        self.ejecutores_por_agente: Dict[str, Callable[[Any, str], Tuple[str, Any]]] = {}
        self.ejecutor_default: Optional[Callable[[Any, str], Tuple[str, Any]]] = None

    # ================================================================
    # FLUJO SIMPLE — Un solo agente
    # ================================================================

    def resolver_agente(self, accion: str, mensaje: str, agente_sugerido: Optional[str] = None) -> Tuple[str, float, str]:
        """Resuelve cuál agente debe atender la acción. Retorna (agente_id, confianza, razón)."""
        # 1) Priorizar acción explícita
        for agente_id, agente in self.agentes.items():
            if agente.soporta_accion(accion):
                return agente_id, 0.95, 'mapeo_por_accion'

        # 2) Sugerencia previa del router
        if agente_sugerido in self.agentes:
            score = self.agentes[agente_sugerido].score_prompt(mensaje)
            return agente_sugerido, max(0.6, score), 'sugerencia_router'

        # 3) Clasificación por prompt
        mejor_agente = 'agente_ventas'
        mejor_score = 0.0
        for agente_id, agente in self.agentes.items():
            score = agente.score_prompt(mensaje)
            if score > mejor_score:
                mejor_agente = agente_id
                mejor_score = score

        return mejor_agente, max(0.5, mejor_score), 'clasificacion_prompt'

    def pre_ejecutar(self, agente_id: str, consulta: Any, mensaje: str) -> ResultadoPreEjecucion:
        agente = self.agentes.get(agente_id)
        if not agente:
            return ResultadoPreEjecucion(permitido=True, consulta=consulta, confianza_agente=0.5)
        return agente.pre_ejecucion(consulta, mensaje)

    def registrar_ejecutor(self, agente_id: str, ejecutor: Callable[[Any, str], Tuple[str, Any]]) -> None:
        self.ejecutores_por_agente[agente_id] = ejecutor

    def registrar_ejecutor_default(self, ejecutor: Callable[[Any, str], Tuple[str, Any]]) -> None:
        self.ejecutor_default = ejecutor

    def ejecutar_accion(self, agente_id: str, consulta: Any, mensaje: str) -> Tuple[str, Any]:
        agente = self.agentes.get(agente_id)
        ejecutor = self.ejecutores_por_agente.get(agente_id) or self.ejecutor_default
        if not ejecutor:
            raise RuntimeError(f"No hay ejecutor registrado para {agente_id}")
        if not agente:
            return ejecutor(consulta, mensaje)
        return agente.ejecutar(consulta, mensaje, ejecutor)

    def post_ejecutar(self, agente_id: str, consulta: Any, respuesta: str, df: Any, error: bool = False) -> ResultadoPostEjecucion:
        agente = self.agentes.get(agente_id)
        if agente_id == 'agente_validador_final' and agente:
            return agente.post_ejecucion(consulta, respuesta, df, error=error)

        if agente:
            respuesta = agente.enriquecer_respuesta(consulta, respuesta, df)

        if not agente:
            base = AgenteEspecializadoBase()
            resultado = base.post_ejecucion(consulta, respuesta, df, error=error)
        else:
            resultado = agente.post_ejecucion(consulta, respuesta, df, error=error)

        validador_final = self.agentes.get('agente_validador_final')
        if not validador_final:
            return resultado

        resultado_final = validador_final.post_ejecucion(
            consulta,
            resultado.respuesta,
            df,
            error=error,
        )
        return ResultadoPostEjecucion(
            respuesta=resultado_final.respuesta,
            confianza_datos=min(resultado.confianza_datos, resultado_final.confianza_datos),
            observaciones=list(dict.fromkeys(resultado.observaciones + resultado_final.observaciones))
        )

    def prompt_base(self, agente_id: str) -> str:
        agente = self.agentes.get(agente_id)
        if not agente:
            return AgenteEspecializadoBase.prompt_base
        return agente.prompt_base

    # ================================================================
    # FLUJO CADENA — Múltiples agentes colaborativos
    # ================================================================

    def planificar_cadena(self, mensaje: str, accion: str = '', agente_sugerido: Optional[str] = None) -> List[PasoAgente]:
        """
        Analiza el mensaje del usuario y planifica qué agentes deben intervenir.

        Retorna una lista ordenada de PasoAgente con:
          - El agente principal (el que corresponde a la acción)
          - Agentes de soporte (según reglas de contexto del prompt)

        Ejemplo:
          Input:  "¿Cómo van las ventas por marca y cuál es su tendencia?"
          Output: [
            PasoAgente(agente_id='agente_ventas', rol='principal'),
            PasoAgente(agente_id='agente_estadistica', rol='enriquecimiento'),
            PasoAgente(agente_id='agente_predicciones', rol='calculo'),
          ]
        """
        # 1. Determinar agente principal
        agente_principal_id, confianza_principal, razon = self.resolver_agente(
            accion, mensaje, agente_sugerido
        )

        pasos = [PasoAgente(
            agente_id=agente_principal_id,
            rol='principal',
            confianza=confianza_principal,
        )]

        # 2. Escanear el mensaje buscando conceptos que activan agentes de soporte
        # Normalizar: lowercase, colapsar espacios, strip acentos opcionales
        import re as _re
        texto_lower = _re.sub(r'\s+', ' ', (mensaje or '').lower().strip())
        agentes_soporte_ids: List[str] = []

        for concepto, agentes_ids in REGLAS_CADENA.items():
            # Matching con word boundary para evitar falsos positivos
            concepto_norm = concepto.lower().strip()
            if _re.search(r'\b' + _re.escape(concepto_norm) + r'\b', texto_lower):
                for aid in agentes_ids:
                    if aid != agente_principal_id and aid not in agentes_soporte_ids:
                        agentes_soporte_ids.append(aid)

        # 3. Clasificar el rol de cada agente de soporte
        for aid in agentes_soporte_ids:
            agente = self.agentes.get(aid)
            if not agente:
                continue

            # Determinar rol según tipo de agente
            if aid == 'agente_estadistica':
                rol = 'enriquecimiento'
            elif aid == 'agente_predicciones':
                rol = 'calculo'
            elif aid == 'agente_matematicas':
                rol = 'calculo'
            elif aid == 'agente_diagnostico':
                rol = 'validacion'
            else:
                rol = 'datos'

            pasos.append(PasoAgente(
                agente_id=aid,
                rol=rol,
                confianza=agente.score_prompt(mensaje),
            ))

        return pasos

    def es_cadena(self, mensaje: str, accion: str = '', agente_sugerido: Optional[str] = None) -> bool:
        """Determina si un mensaje requiere cadena multi-agente (más de 1 agente)."""
        pasos = self.planificar_cadena(mensaje, accion, agente_sugerido)
        return len(pasos) > 1

    def obtener_prompts_cadena(self, pasos: List[PasoAgente]) -> str:
        """
        Combina los prompts base de todos los agentes involucrados en la cadena.
        Útil para alimentar al LLM con el conocimiento combinado de los expertos.
        """
        prompts = []
        for paso in pasos:
            agente = self.agentes.get(paso.agente_id)
            if agente:
                prompts.append(f"[{agente.id_agente.upper()} — {paso.rol}]: {agente.prompt_base}")
        return "\n\n".join(prompts)

    def pre_ejecutar_cadena(self, pasos: List[PasoAgente], consulta: Any, mensaje: str) -> List[PasoAgente]:
        """
        Ejecuta pre_ejecucion de TODOS los agentes de la cadena.
        Cada agente enriquece la consulta (agrega temporalidad, límites, etc.).
        Si algún agente bloquea, se marca como no exitoso pero la cadena continúa.
        """
        for paso in pasos:
            agente = self.agentes.get(paso.agente_id)
            if not agente:
                continue

            resultado_pre = agente.pre_ejecucion(consulta, mensaje)
            paso.resultado_pre = resultado_pre

            if not resultado_pre.permitido:
                paso.exito = False
                paso.error = resultado_pre.motivo_bloqueo
            else:
                # La consulta se va enriqueciendo con cada agente
                consulta = resultado_pre.consulta
                paso.confianza = resultado_pre.confianza_agente

        return pasos

    def post_ejecutar_cadena(
        self,
        pasos: List[PasoAgente],
        consulta: Any,
        respuesta: str,
        df: Any,
        error: bool = False
    ) -> ResultadoCadena:
        """
        Ejecuta post_ejecucion de TODOS los agentes de la cadena.
        Cada agente valida/enriquece la respuesta desde su perspectiva de experto.
        Al final, consolida la confianza y observaciones de toda la cadena.
        """
        advertencias_globales: List[str] = []
        observaciones_globales: List[str] = []
        respuesta_actual = respuesta

        for paso in pasos:
            if not paso.exito:
                advertencias_globales.append(f"{paso.agente_id}: bloqueado — {paso.error}")
                continue

            agente = self.agentes.get(paso.agente_id)
            if not agente:
                continue

            respuesta_actual = agente.enriquecer_respuesta(consulta, respuesta_actual, df)

            resultado_post = agente.post_ejecucion(consulta, respuesta_actual, df, error=error)
            paso.resultado_post = resultado_post
            paso.respuesta_parcial = resultado_post.respuesta
            paso.confianza = resultado_post.confianza_datos
            paso.datos_parciales = df

            # La respuesta se va enriqueciendo (el post puede agregar disclaimers, notas)
            respuesta_actual = resultado_post.respuesta
            observaciones_globales.extend(resultado_post.observaciones)

        validador_final = self.agentes.get('agente_validador_final')
        if validador_final:
            resultado_validacion_final = validador_final.post_ejecucion(
                consulta,
                respuesta_actual,
                df,
                error=error,
            )
            pasos.append(PasoAgente(
                agente_id='agente_validador_final',
                rol='validacion_final',
                resultado_post=resultado_validacion_final,
                respuesta_parcial=resultado_validacion_final.respuesta,
                datos_parciales=df,
                confianza=resultado_validacion_final.confianza_datos,
            ))
            respuesta_actual = resultado_validacion_final.respuesta
            observaciones_globales.extend(resultado_validacion_final.observaciones)

        # Recolectar advertencias de pre_ejecucion
        for paso in pasos:
            if paso.resultado_pre and paso.resultado_pre.advertencias:
                advertencias_globales.extend(
                    f"{paso.agente_id}: {a}" for a in paso.resultado_pre.advertencias
                )

        # Calcular confianza consolidada (promedio ponderado)
        confianzas = []
        for paso in pasos:
            if paso.exito and paso.confianza > 0:
                if paso.rol == 'principal':
                    peso = 2.0
                elif paso.rol == 'validacion_final':
                    peso = 1.5
                else:
                    peso = 1.0
                confianzas.append((paso.confianza, peso))

        if confianzas:
            suma_ponderada = sum(c * p for c, p in confianzas)
            suma_pesos = sum(p for _, p in confianzas)
            confianza_final = suma_ponderada / suma_pesos
        else:
            confianza_final = 0.5

        agentes_ids = [p.agente_id for p in pasos if p.exito]

        return ResultadoCadena(
            respuesta_final=respuesta_actual,
            confianza_consolidada=max(0.0, min(1.0, confianza_final)),
            agentes_involucrados=agentes_ids,
            pasos=pasos,
            advertencias=advertencias_globales,
            observaciones=list(set(observaciones_globales)),
            prompt_combinado=self.obtener_prompts_cadena(pasos),
            datos_consolidados=df,
        )

    def resumen_cadena(self, resultado: ResultadoCadena) -> str:
        """Genera un resumen legible de la cadena ejecutada para el usuario."""
        lineas = ["**🔗 Cadena Multi-Agente:**"]
        for i, paso in enumerate(resultado.pasos, 1):
            estado = "✅" if paso.exito else "❌"
            agente = self.agentes.get(paso.agente_id)
            nombre = agente.id_agente if agente else paso.agente_id
            lineas.append(f"  {i}. {estado} **{nombre}** ({paso.rol}) — confianza: {paso.confianza:.0%}")

        lineas.append(f"\n**Confianza consolidada:** {resultado.confianza_consolidada:.0%}")

        if resultado.advertencias:
            lineas.append(f"**Advertencias:** {len(resultado.advertencias)}")

        return "\n".join(lineas)

    def ejecutar_cadena_completa(
        self,
        pasos: List[PasoAgente],
        consulta: Any,
        mensaje: str,
        respuesta_principal: str,
        df_principal: Any,
    ) -> ResultadoCadena:
        """
        Ejecuta la cadena completa: el agente principal ya fue ejecutado,
        ahora cada agente de soporte ejecuta su propio paso (consulta datos
        de su dominio) y enriquece la respuesta con hallazgos reales.

        Flujo por cada agente de soporte:
          1. ejecutar_accion(agente_id, consulta, mensaje)  → datos propios
          2. enriquecer_respuesta(consulta, respuesta, df)  → aportes deterministas
          3. post_ejecucion(consulta, respuesta, df)        → validación
        """
        advertencias: List[str] = []
        observaciones: List[str] = []
        respuesta_actual = respuesta_principal
        df_consolidado = df_principal

        for paso in pasos:
            if not paso.exito:
                advertencias.append(f"{paso.agente_id}: bloqueado — {paso.error}")
                continue

            agente = self.agentes.get(paso.agente_id)
            if not agente:
                continue

            # El principal ya fue ejecutado externamente
            if paso.rol == 'principal':
                paso.respuesta_parcial = respuesta_principal
                paso.datos_parciales = df_principal
                # Enriquecer con el agente principal
                respuesta_actual = agente.enriquecer_respuesta(consulta, respuesta_actual, df_principal)
                resultado_post = agente.post_ejecucion(consulta, respuesta_actual, df_principal)
                paso.resultado_post = resultado_post
                paso.confianza = resultado_post.confianza_datos
                respuesta_actual = resultado_post.respuesta
                observaciones.extend(resultado_post.observaciones)
                continue

            # === Agente de soporte: ejecutar solo si tiene acción propia ===
            accion_actual = getattr(consulta, 'accion_sugerida', '') or ''
            acciones_propias = getattr(agente, 'acciones_soportadas', set()) or set()
            ejecutor = self.ejecutores_por_agente.get(paso.agente_id) or self.ejecutor_default
            resp_soporte = ""
            df_soporte = None

            # Solo ejecutar si el agente tiene una acción específica para esta consulta;
            # de lo contrario ir directo a enriquecimiento con df_principal.
            if ejecutor and accion_actual in acciones_propias:
                try:
                    resp_soporte, df_soporte = agente.ejecutar(consulta, mensaje, ejecutor)
                    paso.respuesta_parcial = resp_soporte
                    paso.datos_parciales = df_soporte
                except Exception as e:
                    paso.error = str(e)[:120]
                    advertencias.append(f"{paso.agente_id}: error ejecución — {paso.error}")
                    # No marcar exito=False: aún puede enriquecer con df_principal

            # Enriquecer la respuesta acumulada con datos del soporte
            df_para_enriquecer = df_soporte if (df_soporte is not None and hasattr(df_soporte, 'empty') and not df_soporte.empty) else df_principal
            respuesta_actual = agente.enriquecer_respuesta(consulta, respuesta_actual, df_para_enriquecer)

            resultado_post = agente.post_ejecucion(consulta, respuesta_actual, df_para_enriquecer)
            paso.resultado_post = resultado_post
            paso.confianza = resultado_post.confianza_datos
            respuesta_actual = resultado_post.respuesta
            observaciones.extend(resultado_post.observaciones)

        # Validador final
        validador = self.agentes.get('agente_validador_final')
        if validador:
            resultado_val = validador.post_ejecucion(consulta, respuesta_actual, df_principal)
            pasos.append(PasoAgente(
                agente_id='agente_validador_final',
                rol='validacion_final',
                resultado_post=resultado_val,
                respuesta_parcial=resultado_val.respuesta,
                datos_parciales=df_principal,
                confianza=resultado_val.confianza_datos,
            ))
            respuesta_actual = resultado_val.respuesta
            observaciones.extend(resultado_val.observaciones)

        # Advertencias de pre_ejecucion
        for paso in pasos:
            if paso.resultado_pre and paso.resultado_pre.advertencias:
                advertencias.extend(f"{paso.agente_id}: {a}" for a in paso.resultado_pre.advertencias)

        # Confianza consolidada
        confianzas = []
        for paso in pasos:
            if paso.exito and paso.confianza > 0:
                peso = 2.0 if paso.rol == 'principal' else (1.5 if paso.rol == 'validacion_final' else 1.0)
                confianzas.append((paso.confianza, peso))

        if confianzas:
            confianza_final = sum(c * p for c, p in confianzas) / sum(p for _, p in confianzas)
        else:
            confianza_final = 0.5

        return ResultadoCadena(
            respuesta_final=respuesta_actual,
            confianza_consolidada=max(0.0, min(1.0, confianza_final)),
            agentes_involucrados=[p.agente_id for p in pasos if p.exito],
            pasos=pasos,
            advertencias=advertencias,
            observaciones=list(set(observaciones)),
            prompt_combinado=self.obtener_prompts_cadena(pasos),
            datos_consolidados=df_principal,
        )
