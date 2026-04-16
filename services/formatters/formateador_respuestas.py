# ============================================================
# ANDROMEDA - Formateador de Respuestas
# ============================================================
# Modulo extraido de interfaz_v5.py (ARQ-001)
# Centraliza los metodos de formateo en un modulo dedicado
# ============================================================

from datetime import datetime
from typing import Dict, List, Any


class FormateadorRespuestas:
    """Clase dedicada al formateo de respuestas en Markdown.
    
    Todos los metodos son funciones puras: reciben datos y devuelven strings.
    No requieren estado externo ni conexion a servicios.
    """

    MONEDA = '$'  # Símbolo de moneda configurable (default: peso/dólar)

    @classmethod
    def configurar_moneda(cls, simbolo: str):
        """Permite configurar el símbolo de moneda desde la compañía de Odoo."""
        cls.MONEDA = simbolo

    @property
    def _m(self) -> str:
        return self.MONEDA

    def _formatear_prediccion_inventario(self, datos: Dict) -> str:
        resumen = datos.get('resumen', {})
        insights_lista = datos.get('insights', [])
        criticos = resumen.get('criticos', 0)
        alertas_count = resumen.get('alertas', 0)
        total_prod = resumen.get('total_productos', 0)
        sin_mov = resumen.get('sin_movimiento', 0)

        emoji_estado = "🔴" if criticos > 0 else "🟡" if alertas_count > 0 else "🟢"
        pct_riesgo = ((criticos + alertas_count) / max(1, total_prod)) * 100

        md = f"""## {emoji_estado} Predicción de Agotamiento de Inventario

### Estado General: {emoji_estado} {pct_riesgo:.0f}% de productos en riesgo

### Resumen
| Métrica | Valor |
|---------|-------|
| Total productos analizados | **{total_prod:,}** |
| 🔴 Críticos (<7 días) | **{criticos}** |
| 🟡 Alerta (7-14 días) | **{alertas_count}** |
| ⏸️ Sin movimiento | **{sin_mov}** |
"""

        if criticos > 0:
            md += f"\n> 🔴 **URGENTE**: {criticos} producto(s) se agotarán en menos de 7 días. Emitir órdenes de compra o trasladar stock de inmediato.\n"
        if alertas_count > 0:
            md += f"\n> 🟡 **Atención**: {alertas_count} producto(s) en zona de alerta (7-14 días). Iniciar proceso de reposición.\n"
        if sin_mov > 0:
            md += f"\n> ⏸️ **Sin movimiento**: {sin_mov} producto(s) sin ventas recientes. Evaluar si son obsoletos o requieren promoción.\n"

        if insights_lista:
            md += "\n### Insights\n"
            for insight in insights_lista:
                md += f"- {insight}\n"

        md += "\n### Productos Críticos\n_Ver tabla de datos para detalles de cada producto_"
        md += "\n\n> 💡 *¿Quieres ver los montos de reposición, clasificación ABC o simular escenarios de demanda?*"
        return md

    def _formatear_flujo_caja(self, datos: Dict) -> str:
        estado_emoji = '🟢' if datos.get('estado') == 'POSITIVO' else '🔴'
        insights_lista = datos.get('insights', [])
        insights = "\n".join(insights_lista) if insights_lista else "Sin insights"

        alertas_lista = datos.get('alertas', [])
        alertas = "\n".join(alertas_lista) if alertas_lista else "Sin alertas"
        return f"""## Predicción de Flujo de Caja

### Período: {datos.get('periodo', 'Próximos 30 días')}

| Concepto | Monto |
|----------|-------|
| Entradas proyectadas | **{self._m}{datos.get('entradas_proyectadas', 0):,.2f}** |
| Salidas proyectadas | **{self._m}{datos.get('salidas_proyectadas', 0):,.2f}** |
| {estado_emoji} Flujo neto | **{self._m}{datos.get('flujo_neto', 0):,.2f}** |

### Cartera
| Concepto | Monto |
|----------|-------|
| Por cobrar (CXC) | {self._m}{datos.get('cxc', {}).get('total', 0):,.2f} |
| Por pagar (CXP) | {self._m}{datos.get('cxp', {}).get('total', 0):,.2f} |

### Insights
{insights}

### Alertas
{alertas}"""

    def _formatear_salud_negocio(self, datos: Dict) -> str:
        score = datos.get('score_general', 0)
        emoji = datos.get('emoji', '🟡')
        estado = datos.get('estado', 'REGULAR')
        
        # Barra visual
        color = '#22c55e' if score >= 80 else '#f59e0b' if score >= 60 else '#ef4444'
        
        md = f"""## {emoji} Score de Salud del Negocio

### Puntuación General: **{score:.0f}/100** ({estado})

### Desglose por Área
"""
        for area, valor in datos.get('scores', {}).items():
            area_emoji = '📈' if 'Ventas' in area else '📦' if 'Inventario' in area else '💰' if 'Flujo' in area else '💳'
            md += f"| {area_emoji} {area} | **{valor:.0f}/100** |\n"
        
        md += "\n### Insights\n"
        for insight in datos.get('insights', []):
            md += f"\n{insight}"
        
        md += "\n\n### Recomendaciones\n"
        for rec in datos.get('recomendaciones', []):
            md += f"\n{rec}"
        
        return md

    def _formatear_estacionalidad(self, datos: Dict) -> str:
        insights_lista = datos.get('insights', [])
        recomendaciones_lista = datos.get('recomendaciones', [])

        mejor_dia = datos.get('mejor_dia', 'N/A')
        peor_dia = datos.get('peor_dia', 'N/A')
        mejor_mes = datos.get('mejor_mes', 'N/A')
        peor_mes = datos.get('peor_mes', 'N/A')

        md = f"""## 📆 Análisis de Estacionalidad

### Patrones Identificados
| Métrica | Valor |
|---------|-------|
| 🏆 Mejor día de la semana | **{mejor_dia}** |
| 🔽 Peor día de la semana | {peor_dia} |
| 🌟 Mejor mes del año | **{mejor_mes}** |
| 🔽 Peor mes del año | {peor_mes} |
"""

        if mejor_dia != 'N/A':
            md += f"\n> 💡 **Oportunidad**: el {mejor_dia} es el día más fuerte. Concentrar campañas, personal y stock para ese día.\n"
        if peor_dia != 'N/A':
            md += f"> 🔍 **Para mejorar**: el {peor_dia} es el día más débil. Considerar promociones o descuentos para mover inventario ese día.\n"

        if insights_lista:
            md += "\n### 🔎 Insights\n"
            for insight in insights_lista:
                md += f"- {insight}\n"

        if recomendaciones_lista:
            md += "\n### ✅ Recomendaciones\n"
            for rec in recomendaciones_lista:
                md += f"- {rec}\n"

        md += "\n_Ver tabla para detalle completo por día de la semana_"
        md += "\n\n> 💡 *¿Quieres ver el análisis por hora, producto o sucursal?*"
        return md

    def _formatear_comparativa(self, datos: Dict) -> str:
        actual = datos.get('periodo_actual', {})
        anterior = datos.get('periodo_anterior', {})
        var = datos.get('variacion_porcentaje', 0)
        emoji = '📈' if var > 0 else '📉' if var < 0 else '➡️'
        color = '🟢' if var > 5 else '🔴' if var < -5 else '🟡'

        insights_lista = datos.get('insights', [])

        # Interpretación en lenguaje claro
        if var > 20:
            interpretacion = f"🟢 **Crecimiento excepcional** (+{var:.1f}%): las ventas se dispararon. Identificar qué lo causó para replicarlo."
        elif var > 5:
            interpretacion = f"🟢 **Crecimiento positivo** (+{var:.1f}%): el período actual supera al anterior. Buen desempeño."
        elif var > 0:
            interpretacion = f"🟡 **Crecimiento leve** (+{var:.1f}%): mejora marginal. Monitorear si se mantiene la tendencia."
        elif var == 0:
            interpretacion = "➡️ **Sin cambio**: resultados idénticos. Verificar si es por factores estacionales."
        elif var > -5:
            interpretacion = f"🟡 **Caída leve** ({var:.1f}%): ligera disminución. Vigilar causas antes de que se profundice."
        elif var > -20:
            interpretacion = f"🔴 **Caída significativa** ({var:.1f}%): las ventas bajaron. Analizar causas: mercado, competencia, operaciones."
        else:
            interpretacion = f"🔴 **Caída crítica** ({var:.1f}%): disminución severa. Requiere plan de recuperación inmediato."

        md = f"""## {emoji} Comparativa: {actual.get('nombre', '')} vs {anterior.get('nombre', '')}

### {actual.get('nombre', 'Período Actual')}
| Métrica | Valor |
|---------|-------|
| Órdenes | **{actual.get('ordenes', 0):,}** |
| Total | **{self._m}{actual.get('total', 0):,.2f}** |
| Promedio por orden | **{self._m}{actual.get('promedio', actual.get('total', 0) / max(1, actual.get('ordenes', 1))):,.2f}** |

### {anterior.get('nombre', 'Período Anterior')}
| Métrica | Valor |
|---------|-------|
| Órdenes | **{anterior.get('ordenes', 0):,}** |
| Total | **{self._m}{anterior.get('total', 0):,.2f}** |
| Promedio por orden | **{self._m}{anterior.get('promedio', anterior.get('total', 0) / max(1, anterior.get('ordenes', 1))):,.2f}** |

### {emoji} Variación {color}
| Métrica | Valor |
|---------|-------|
| Variación % | **{var:+.1f}%** |
| Variación absoluta | **{self._m}{datos.get('variacion_absoluta', 0):+,.2f}** |
| Diferencia en órdenes | **{actual.get('ordenes', 0) - anterior.get('ordenes', 0):+,}** |

### Interpretación
{interpretacion}
"""
        if insights_lista:
            md += "\n### Insights Adicionales\n"
            for insight in insights_lista:
                md += f"- {insight}\n"

        md += "\n> 💡 *¿Quieres ver el desglose por producto, vendedor o proyección para el siguiente período?*"
        return md

    def _format_ventas(self, df, f_ini, f_fin) -> str:
        """Alias de _formato_ventas para compatibilidad."""
        return self._formato_ventas(df, f_ini, f_fin)

    def _formatear_top_productos(self, datos: Dict, limite: int) -> str:
        productos = datos.get('productos', [])[:limite]
        total_ingresos = datos.get('total_ingresos', 0)
        total_unidades = datos.get('total_unidades', 0)
        total_productos = datos.get('total_productos', 0)

        md = f"""## 🏆 Top {limite} Productos Más Vendidos

### Resumen General
| Métrica | Valor |
|---------|-------|
| Productos únicos | **{total_productos:,}** |
| Unidades vendidas (total) | **{total_unidades:,.0f}** |
| Ingresos (total) | **{self._m}{total_ingresos:,.2f}** |

### Ranking
| # | Producto | Unidades | Ingresos | % del Total |
|---|----------|----------|----------|-------------|
"""
        ingresos_top = 0.0
        for i, p in enumerate(productos, 1):
            ing = p.get('price_subtotal', 0)
            ingresos_top += ing
            pct = (ing / total_ingresos * 100) if total_ingresos > 0 else 0
            nombre = str(p.get('producto', ''))[:35]
            md += f"| {i} | {nombre} | {p.get('product_uom_qty', 0):,.0f} | {self._m}{ing:,.2f} | {pct:.1f}% |\n"

        # Insight Pareto
        if total_ingresos > 0 and len(productos) > 0:
            pct_top_n = ingresos_top / total_ingresos * 100
            md += f"\n### 📊 Insight Pareto\n"
            md += f"Los top {len(productos)} productos generan el **{pct_top_n:.1f}%** de los ingresos totales.\n"
            if pct_top_n > 80:
                md += f"\n> 🔴 **Concentración alta**: {len(productos)} productos representan más del 80% de ingresos. Alta dependencia de pocos SKUs. Diversificar el catálogo reduce riesgo.\n"
            elif pct_top_n > 60:
                md += f"\n> 🟡 **Concentración moderada**: fortalecer los siguientes productos en el ranking puede mejorar la estabilidad de ingresos.\n"
            else:
                md += f"\n> 🟢 **Distribución saludable**: los ingresos están bien distribuidos entre el catálogo de productos.\n"

        md += "\n> 💡 *¿Quieres ver la tendencia de ventas de un producto específico, márgenes o predicción de demanda?*"
        return md

    def _formatear_top_clientes(self, datos: Dict, limite: int) -> str:
        clientes = datos.get('por_cliente', [])[:limite]
        total_general = sum(c.get('sum', 0) for c in clientes)

        md = f"## 🏆 Top {limite} Clientes\n\n"
        md += "| # | Cliente | Órdenes | Total | % Participación |\n|---|---------|---------|-------|----------------|\n"

        top3_sum = 0.0
        for i, c in enumerate(clientes, 1):
            monto = c.get('sum', 0)
            pct = (monto / total_general * 100) if total_general > 0 else 0
            if i <= 3:
                top3_sum += monto
            md += f"| {i} | {str(c.get('cliente', ''))[:30]} | {c.get('count', 0)} | {self._m}{monto:,.2f} | {pct:.1f}% |\n"

        # Alertas de concentración
        if total_general > 0 and len(clientes) >= 3:
            pct_top3 = top3_sum / total_general * 100
            md += f"\n### 📊 Análisis de Concentración\n"
            md += f"Los top 3 clientes representan el **{pct_top3:.1f}%** del total.\n"
            if pct_top3 > 70:
                md += f"\n> 🔴 **Riesgo de concentración crítico**: 3 clientes generan más del 70% de los ingresos. Perder uno impactaría gravemente el negocio. Diversificar la base de clientes.\n"
            elif pct_top3 > 50:
                md += f"\n> 🟡 **Concentración moderada**: los top 3 representan {pct_top3:.0f}%. Evaluar estrategias de retención y captación de nuevos clientes.\n"
            else:
                md += f"\n> 🟢 **Base de clientes saludable**: buena distribución de ingresos. Bajo riesgo de dependencia.\n"

        md += "\n> 💡 *¿Quieres ver el análisis de lealtad, clientes en riesgo de churn o RFM (Recencia, Frecuencia, Monto)?*"
        return md

    def _formatear_ventas_vendedor(self, datos: Dict) -> str:
        vendedores = datos.get('por_vendedor', [])[:15]
        if not vendedores:
            return "## Ventas por Vendedor\n\nNo hay datos disponibles."

        total_general = sum(v.get('sum', 0) for v in vendedores)
        promedio_general = total_general / len(vendedores) if vendedores else 0

        md = "## 💼 Ventas por Vendedor\n\n"
        md += "| # | Vendedor | Órdenes | Total | % del Equipo | vs Promedio |\n|---|----------|---------|-------|--------------|-------------|\n"

        for i, v in enumerate(vendedores, 1):
            monto = v.get('sum', 0)
            pct = (monto / total_general * 100) if total_general > 0 else 0
            vs_prom = ((monto - promedio_general) / promedio_general * 100) if promedio_general > 0 else 0
            flecha = "🔼" if vs_prom > 10 else "🔽" if vs_prom < -10 else "➡️"
            md += f"| {i} | {str(v.get('vendedor', ''))[:25]} | {v.get('count', 0)} | {self._m}{monto:,.2f} | {pct:.1f}% | {flecha} {vs_prom:+.1f}% |\n"

        # Insights de desempeño
        if len(vendedores) >= 2:
            top_vend = vendedores[0]
            bot_vend = vendedores[-1]
            top_monto = top_vend.get('sum', 0)
            bot_monto = bot_vend.get('sum', 0)
            if bot_monto > 0:
                brecha = (top_monto - bot_monto) / bot_monto * 100
                md += f"\n### 📊 Análisis de Desempeño\n"
                md += f"- **Promedio del equipo**: {self._m}{promedio_general:,.2f}\n"
                md += f"- **Líder de ventas**: {str(top_vend.get('vendedor',''))[:25]} ({self._m}{top_monto:,.2f})\n"
                md += f"- **Brecha líder vs último**: **{brecha:.0f}%** de diferencia\n"
                if brecha > 300:
                    md += f"\n> 🔴 **Desbalance alto en el equipo**: el vendedor líder supera al último por {brecha:.0f}%. Revisar asignación de territorios, capacitación o cuentas.\n"
                elif brecha > 100:
                    md += f"\n> 🟡 **Diferencia notable** entre vendedores. Compartir tácticas del líder puede elevar el desempeño general.\n"
                else:
                    md += f"\n> 🟢 **Equipo equilibrado**: baja dispersión de resultados. Buen rendimiento colectivo.\n"

        md += "\n> 💡 *¿Quieres ver el rendimiento de un vendedor específico, cumplimiento de metas o comparativa por período?*"
        return md

    def _formato_ventas(self, df, f_ini, f_fin) -> str:
        if df.empty:
            return f"No hay ventas entre {f_ini} y {f_fin}"
        total = df['amount_total'].sum()
        n = len(df)
        promedio = total / n
        maximo = df['amount_total'].max()

        # Tendencia: comparar primera mitad vs segunda mitad
        tendencia_txt = ""
        try:
            col_fecha = next((c for c in df.columns if 'date' in c.lower()), None)
            if col_fecha:
                import pandas as pd
                fechas = pd.to_datetime(df[col_fecha], errors='coerce')
                df_t = df.assign(_fecha=fechas, _monto=pd.to_numeric(df['amount_total'], errors='coerce')).dropna(subset=['_fecha', '_monto'])
                df_t = df_t.sort_values('_fecha')
                mitad = len(df_t) // 2
                if mitad > 0:
                    p1 = float(df_t['_monto'].iloc[:mitad].sum())
                    p2 = float(df_t['_monto'].iloc[mitad:].sum())
                    if p1 > 0:
                        cambio = (p2 - p1) / p1 * 100
                        flecha = "📈" if cambio > 5 else "📉" if cambio < -5 else "➡️"
                        tendencia_txt = f"\n| Tendencia del período | **{flecha} {cambio:+.1f}%** (2ª mitad vs 1ª mitad) |"
        except Exception:
            pass

        alertas = []
        if n < 10:
            alertas.append("🟡 **Pocos registros**: muestra pequeña, los promedios pueden no ser representativos.")
        if total > 0:
            top1_pct = float(df['amount_total'].nlargest(1).sum()) / total * 100
            if top1_pct > 30:
                alertas.append(f"🟡 **Concentración alta**: la mayor operación representa el {top1_pct:.1f}% del total. Dependencia de pocos pedidos grandes.")

        md = f"""## Ventas | {f_ini} a {f_fin}

| Métrica | Valor |
|---------|-------|
| Órdenes | **{n:,}** |
| Total | **{self._m}{total:,.2f}** |
| Promedio por orden | **{self._m}{promedio:,.2f}** |
| Mayor orden | **{self._m}{maximo:,.2f}** |{tendencia_txt}
"""
        if alertas:
            md += "\n### ⚠️ Alertas\n"
            for a in alertas:
                md += f"- {a}\n"

        md += "\n> 💡 *¿Quieres ver el desglose por vendedor, producto, predicción o comparativa con el período anterior?*"
        return md

    def _formato_pos(self, df, f_ini, f_fin) -> str:
        if df.empty:
            return f"No hay tickets POS entre {f_ini} y {f_fin}"
        total = df['amount_total'].sum() if 'amount_total' in df.columns else 0
        n = len(df)
        promedio = total / n if n > 0 else 0

        alertas = []
        sesiones_abiertas = 0
        if 'state' in df.columns:
            sesiones_abiertas = int((df['state'] == 'opened').sum())
            if sesiones_abiertas > 0:
                alertas.append(f"🔴 **{sesiones_abiertas} sesión(es) abierta(s)**: cerrar para evitar inconsistencias en el reporte.")

        negs = 0
        if 'amount_total' in df.columns:
            try:
                import pandas as pd
                negs = int((pd.to_numeric(df['amount_total'], errors='coerce') < 0).sum())
                if negs > 0:
                    alertas.append(f"🟡 **{negs} transacción(es) negativa(s)** (posibles devoluciones). Verificar en el cierre de caja.")
            except Exception:
                pass

        if promedio < 50 and promedio > 0:
            alertas.append(f"🟡 **Ticket promedio bajo** (${promedio:,.2f}): evaluar estrategias de upselling o combos.")

        md = f"""## Punto de Venta | {f_ini} a {f_fin}

| Métrica | Valor |
|---------|-------|
| Tickets | **{n:,}** |
| Ventas totales | **{self._m}{total:,.2f}** |
| Ticket promedio | **{self._m}{promedio:,.2f}** |
"""
        if alertas:
            md += "\n### ⚠️ Alertas\n"
            for a in alertas:
                md += f"- {a}\n"

        md += "\n> 💡 *¿Quieres ver productividad por cajero, métodos de pago, sesiones detalladas o comparativa de sucursales?*"
        return md

    def _formatear_metodos_pago(self, datos: Dict) -> str:
        metodos = datos.get('metodos', [])
        total_general = sum(m.get('sum', 0) for m in metodos)
        n_metodos = len(metodos)

        md = "## 💳 Métodos de Pago\n\n"
        md += "| Método | Transacciones | Total | % |\n|--------|---------------|-------|---|\n"

        for m in metodos:
            md += f"| {m.get('metodo', '')} | {m.get('count', 0)} | {self._m}{m.get('sum', 0):,.2f} | {m.get('porcentaje', 0):.1f}% |\n"

        if metodos:
            top_metodo = max(metodos, key=lambda x: x.get('sum', 0))
            top_pct = top_metodo.get('porcentaje', 0)
            md += f"\n### Insights\n"
            md += f"- **Método dominante**: {top_metodo.get('metodo', 'N/A')} ({top_pct:.1f}% del total)\n"
            if n_metodos == 1:
                md += "> 🟡 **Un solo método de pago**: si falla, no hay alternativa. Considerar activar métodos adicionales para no perder ventas.\n"
            elif top_pct > 80:
                md += f"> 🟡 **Alta concentración en {top_metodo.get('metodo', '')}**: si hay problemas con este método (fallas de terminal, etc.) el impacto en ventas sería muy alto.\n"
            else:
                md += f"> 🟢 **Buena diversidad de métodos de pago** ({n_metodos} opciones): el cliente tiene flexibilidad y los riesgos operativos son menores.\n"

        md += "\n> 💡 *¿Quieres ver métodos de pago por sucursal, cajero o período específico?*"
        return md

    def _formatear_sesiones(self, datos: Dict) -> str:
        sesiones = datos.get('por_sesion', [])[:15]
        total_general = sum(s.get('sum', 0) for s in sesiones)
        abiertas = [s for s in sesiones if s.get('estado') == 'open' or s.get('state') == 'opened']

        md = "## 🖥️ Sesiones POS\n\n"
        md += "| Sesión | Tickets | Total | Estado |\n|--------|---------|-------|--------|\n"

        for s in sesiones:
            estado = s.get('estado', s.get('state', ''))
            estado_emoji = "🔴 Abierta" if estado in ('open', 'opened') else "✅ Cerrada" if estado in ('closed', 'cerrada') else estado
            md += f"| {str(s.get('sesion', ''))[:28]} | {s.get('count', 0)} | {self._m}{s.get('sum', 0):,.2f} | {estado_emoji} |\n"

        if abiertas:
            md += f"\n> 🔴 **{len(abiertas)} sesión(es) abierta(s)**: deben cerrarse para que los reportes financieros sean precisos y los cuadres de caja sean confiables.\n"
        else:
            md += f"\n> 🟢 **Todas las sesiones están cerradas**: los datos de este período son confiables para reportes.\n"

        if total_general > 0 and sesiones:
            promedio_sesion = total_general / len(sesiones)
            md += f"\n### Indicadores\n- Venta promedio por sesión: **{self._m}{promedio_sesion:,.2f}**\n"

        md += "\n> 💡 *¿Quieres ver el detalle de una sesión específica, productividad por cajero o comparativa de sucursales?*"
        return md

    def _formato_inventario(self, df) -> str:
        if df.empty:
            return "No hay datos de inventario"
        total = df['quantity'].sum() if 'quantity' in df.columns else 0
        n = len(df)

        alertas = []
        try:
            import pandas as pd
            if 'quantity' in df.columns:
                qty = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
                negativos = int((qty < 0).sum())
                ceros = int((qty == 0).sum())
                criticos = int(((qty > 0) & (qty < 10)).sum())
                if negativos > 0:
                    alertas.append(f"🔴 **{negativos} producto(s) con stock negativo**. Revisar movimientos pendientes.")
                if ceros > 0:
                    alertas.append(f"🟡 **{ceros} producto(s) sin existencias** (stock = 0). Evaluar si requieren reposición.")
                if criticos > 0:
                    alertas.append(f"🟡 **{criticos} producto(s) con menos de 10 unidades**. Stock crítico.")
        except Exception:
            pass

        md = f"""## Inventario

| Métrica | Valor |
|---------|-------|
| Productos en catálogo | **{n:,}** |
| Unidades totales | **{total:,.0f}** |
"""
        if alertas:
            md += "\n### ⚠️ Alertas\n"
            for a in alertas:
                md += f"- {a}\n"
        md += "\n> 💡 *¿Quieres ver rotación, productos críticos, predicción de agotamiento o clasificación ABC?*"
        return md

    def _formatear_rotacion_inventario(self, datos: Dict) -> str:
        criticos = datos.get('criticos', [])
        todos = datos.get('todos', [])
        total_analizados = len(todos) if todos else len(criticos)

        filas = []
        for p in criticos[:10]:
            dias = p.get('dias_stock', 0)
            urgencia = "🔴" if dias < 3 else "🟡" if dias < 7 else "⏰"
            fila = (
                f"| {urgencia} {p.get('nombre', '')[:28]} "
                f"| {p.get('vendido', 0):,.0f} "
                f"| {p.get('qty_available', 0):,.0f} "
                f"| {dias:.0f} |"
            )
            filas.append(fila)

        tabla_productos = "\n".join(filas) if filas else "| Sin datos | - | - | - |"
        n_urgentes = len([p for p in criticos if p.get('dias_stock', 99) < 3])
        n_alerta = len([p for p in criticos if 3 <= p.get('dias_stock', 99) < 7])

        md = f"""## 🔄 Rotación de Inventario

### Estado de Stock
| Nivel | Cantidad |
|-------|----------|
| 🔴 Urgente (<3 días) | **{n_urgentes}** |
| 🟡 Alerta (3-7 días) | **{n_alerta}** |
| Total con <7 días | **{len(criticos)}** |
| Total analizados | **{total_analizados}** |

### Productos Críticos (< 7 días de stock)

| Estado | Producto | Vendido/mes | Stock | Días Stock |
|--------|----------|-------------|-------|------------|
{tabla_productos}
"""

        if n_urgentes > 0:
            md += f"\n> 🔴 **ACCIÓN INMEDIATA**: {n_urgentes} producto(s) con menos de 3 días de stock. Ordenar de reposición HOY.\n"
        if n_alerta > 0:
            md += f"\n> 🟡 **Iniciar proceso de compra**: {n_alerta} producto(s) entre 3 y 7 días. Emitir orden de compra esta semana.\n"
        if len(criticos) == 0:
            md += f"\n> 🟢 **Inventario saludable**: ningún producto con menos de 7 días de cobertura.\n"

        md += "\n> 💡 *¿Quieres ver la clasificación ABC, valoración de inventario o predicción de agotamiento?*"
        return md

    def _formatear_valoracion(self, datos: Dict) -> str:
        resumen = datos.get('resumen', {})
        total_prod = resumen.get('total_productos', 0)
        total_uds = resumen.get('total_unidades', 0)
        valor = datos.get('valoracion', 0)

        alertas = []
        if datos.get('sin_costo', 0) > 0:
            alertas.append(f"🟡 **{datos['sin_costo']} producto(s) sin costo configurado**: la valoración es parcial. Actualizar costos en Odoo para obtener cifras exactas.")
        if total_uds > 0 and valor > 0:
            valor_por_ud = valor / total_uds
            alertas.append(f"💰 Costo promedio por unidad: **${valor_por_ud:,.2f}**")

        md = f"""## 💲 Valoración de Inventario

| Métrica | Valor |
|---------|-------|
| Total productos | **{total_prod:,}** |
| Unidades totales | **{total_uds:,.0f}** |
| 💲 Valor estimado del inventario | **{self._m}{valor:,.2f}** |
"""
        if alertas:
            md += "\n### ⚠️ Observaciones\n"
            for a in alertas:
                md += f"- {a}\n"

        md += "\n> 💡 *El valor del inventario es clave para el balance general. ¿Quieres ver el desglose por categoría, almacén o clasificación ABC?*"
        return md
    
    # ============================================================
    # FORMATEADORES ESPECIALIZADOS (CEREBRO ANDROMEDA)
    # ============================================================

    def _formatear_ventas_especializado(self, datos: Dict) -> str:
        """Formatear análisis completo de ventas desde consultas especializadas."""
        metricas = datos.get('metricas', {})
        confianza = datos.get('confianza', 0)
        emoji_conf = '🟢' if confianza >= 95 else '🟡' if confianza >= 80 else '🔴'
        
        md = f"""## Análisis Especializado de Ventas

### Confianza de Datos: {emoji_conf} **{confianza:.1f}%**

### Métricas Principales
| Métrica | Valor |
|---------|-------|
| Total Órdenes | **{metricas.get('total_ordenes', 0):,}** |
| Ventas Totales | **{self._m}{metricas.get('total_ventas', 0):,.2f}** |
| Ticket Promedio | **{self._m}{metricas.get('promedio_venta', 0):,.2f}** |
| Venta Máxima | **{self._m}{metricas.get('venta_maxima', 0):,.2f}** |
| Venta Mínima | **{self._m}{metricas.get('venta_minima', 0):,.2f}** |
| Mediana | **{self._m}{metricas.get('mediana_venta', 0):,.2f}** |

### Insights
"""
        for insight in datos.get('insights', []):
            md += f"- {insight}\n"
        
        if datos.get('alertas'):
            md += "\n### Alertas\n"
            for alerta in datos.get('alertas', []):
                md += f"- {alerta}\n"
        
        md += "\n_Ver tabla de datos para detalle completo_"
        return md

    def _formatear_ventas_por_empresa(self, datos: Dict) -> str:
        """Formatear ventas agrupadas por empresa."""
        metricas = datos.get('metricas', {})
        confianza = datos.get('confianza_datos', datos.get('confianza', 0))
        
        # Contar empresas
        empresas = datos.get('por_empresa', [])
        num_empresas = len(empresas) if empresas else metricas.get('empresas_con_ventas', 0)
        
        md = f"""## Ventas por Empresa

### Confianza: **{confianza:.1f}%**

### Resumen
| Métrica | Valor |
|---------|-------|
| Empresas con ventas | **{num_empresas}** |
| Total Órdenes | **{metricas.get('num_ordenes', metricas.get('total_ordenes', 0)):,}** |
| Ventas Totales | **{self._m}{metricas.get('total_ventas', 0):,.2f}** |

### Ranking por Empresa
"""
        if empresas:
            md += "| # | Empresa | Órdenes | Total | % |\n|---|---------|---------|-------|---|\n"
            total_general = sum(e.get('total', 0) for e in empresas)
            for i, emp in enumerate(empresas[:10], 1):
                emp_total = emp.get('total', 0)
                pct = (emp_total / total_general * 100) if total_general > 0 else 0
                emp_nombre = str(emp.get('empresa', 'N/A'))[:30]
                emp_ordenes = emp.get('ordenes', 0)
                md += f"| {i} | {emp_nombre} | {emp_ordenes} | {self._m}{emp_total:,.2f} | {pct:.1f}% |\n"
        
        return md

    def _formatear_inventario_por_almacen(self, datos: Dict) -> str:
        """Formatear inventario desglosado por almacén."""
        # Soportar diferentes nombres de claves
        resumen = datos.get('resumen', datos.get('metricas', {}))
        confianza = datos.get('confianza', datos.get('confianza_datos', 0))
        
        md = f"""## Inventario por Almacén

### Confianza de Datos: **{confianza:.1f}%**

### Resumen General
| Métrica | Valor |
|---------|-------|
| Total Almacenes | **{resumen.get('total_almacenes', 0)}** |
| Total Productos | **{resumen.get('total_productos_unicos', resumen.get('total_productos', 0)):,}** |
| Unidades Totales | **{resumen.get('total_cantidad', resumen.get('total_unidades', 0)):,.0f}** |

### Desglose por Almacén
"""
        # Soportar 'almacenes' o 'por_almacen'
        almacenes = datos.get('almacenes', datos.get('por_almacen', []))
        if almacenes:
            md += "| Almacén | Empresa | Productos | Cantidad | % |\n|---------|---------|-----------|----------|---|\n"
            total_cantidad = sum(a.get('total_cantidad', a.get('unidades', 0)) for a in almacenes)
            for alm in almacenes[:15]:
                cant = alm.get('total_cantidad', alm.get('unidades', 0))
                pct = (cant / total_cantidad * 100) if total_cantidad > 0 else 0
                nombre = str(alm.get('nombre', alm.get('almacen', '')))[:25]
                empresa = str(alm.get('empresa', ''))[:20]
                prods = alm.get('productos_unicos', alm.get('productos', 0))
                md += f"| {nombre} | {empresa} | {prods} | {cant:,.0f} | {pct:.1f}% |\n"
        
        if datos.get('alertas'):
            md += "\n### Alertas\n"
            for alerta in datos.get('alertas', []):
                md += f"- {alerta}\n"
        
        return md

    def _formatear_productos_criticos(self, datos: Dict) -> str:
        """Formatear productos con inventario crítico."""
        metricas = datos.get('metricas', {})
        confianza = datos.get('confianza', 0)
        
        emoji_alerta = '🔴' if metricas.get('productos_criticos', 0) > 20 else '🟡' if metricas.get('productos_criticos', 0) > 5 else '🟢'
        
        md = f"""## {emoji_alerta} Productos en Estado Crítico

### Confianza de Datos: **{confianza:.1f}%**

### Resumen de Criticidad
| Nivel | Cantidad | Descripción |
|-------|----------|-------------|
| Agotado | **{metricas.get('productos_agotados', 0)}** | Sin stock |
| Crítico | **{metricas.get('productos_criticos', 0)}** | < 7 días de stock |
| Bajo | **{metricas.get('productos_bajo_stock', 0)}** | < 14 días de stock |

### Productos que Requieren Acción Inmediata
"""
        productos = datos.get('productos', [])
        if productos:
            md += "| Producto | Stock Actual | Venta/Día | Días Stock | Estado |\n|----------|--------------|-----------|------------|--------|\n"
            for prod in productos[:15]:
                estado = prod.get('estado', 'crítico')
                emoji = '🔴' if estado == 'agotado' else '🟠' if estado == 'critico' else '🟡'
                md += f"| {str(prod.get('producto', ''))[:30]} | {prod.get('stock', 0):,.0f} | {prod.get('venta_diaria', 0):,.1f} | {prod.get('dias_stock', 0):.0f} | {emoji} |\n"
        
        md += "\n### Recomendaciones\n"
        for rec in datos.get('recomendaciones', []):
            md += f"- {rec}\n"
        
        return md

    def _formatear_rotacion_avanzada(self, datos: Dict) -> str:
        """Formatear análisis avanzado de rotación de inventario."""
        metricas = datos.get('metricas', {})
        confianza = datos.get('confianza', 0)
        
        md = f"""## Análisis Avanzado de Rotación de Inventario

### Confianza de Datos: **{confianza:.1f}%**

### Indicadores de Rotación
| Métrica | Valor |
|---------|-------|
| Rotación Promedio | **{metricas.get('rotacion_promedio', 0):.2f}** veces/período |
| Días de Inventario Promedio | **{metricas.get('dias_inventario_promedio', 0):.0f}** días |
| Valor Inmovilizado | **{self._m}{metricas.get('valor_inmovilizado', 0):,.2f}** |

### Clasificación ABC
| Categoría | Productos | % Valor | Descripción |
|-----------|-----------|---------|-------------|
| A (Alto) | {metricas.get('productos_a', 0)} | {metricas.get('pct_valor_a', 0):.1f}% | Alta rotación |
| B (Medio) | {metricas.get('productos_b', 0)} | {metricas.get('pct_valor_b', 0):.1f}% | Rotación media |
| C (Bajo) | {metricas.get('productos_c', 0)} | {metricas.get('pct_valor_c', 0):.1f}% | Baja rotación |

### Insights
"""
        for insight in datos.get('insights', []):
            md += f"- {insight}\n"
        
        return md

    def _formatear_cxc_especializado(self, datos: Dict) -> str:
        """Formatear cuentas por cobrar con análisis especializado.
        Acepta datos de analizador_avanzado.cuentas_por_cobrar() o consultas_especializadas.cuentas_por_cobrar().
        """
        metricas = datos.get('metricas', {})
        confianza = datos.get('confianza', datos.get('confianza_datos', 0))

        # Valores principales — soporte para claves directas (analizador) y nested (metricas)
        total_cxc = metricas.get('total_cxc', datos.get('total', datos.get('total_pendiente', 0)))
        facturas_pendientes = metricas.get('facturas_pendientes', datos.get('total_facturas', datos.get('num_facturas', 0)))
        clientes_deudores = metricas.get('clientes_deudores', len(datos.get('por_cliente', [])))
        antiguedad_prom = metricas.get('antiguedad_promedio', 0)

        # Aging buckets — convierte ambos formatos de por_antiguedad
        ag = datos.get('por_antiguedad', {})
        vigente  = metricas.get('vigente',      ag.get('0. Por vencer',  ag.get('Al corriente', 0)))
        v30_60   = metricas.get('vencido_30_60', ag.get('1. 1-30 días',   ag.get('1-30 días',    0)))
        v60_90   = metricas.get('vencido_60_90', ag.get('2. 31-60 días',  ag.get('31-60 días',   0)))
        v90_plus = metricas.get('vencido_90_plus',
                                ag.get('4. +90 días', ag.get('Más de 90 días', 0))
                                + ag.get('3. 61-90 días', ag.get('61-90 días', 0)))
        total_aged = vigente + v30_60 + v60_90 + v90_plus or 1
        pct_vigente = metricas.get('pct_vigente', vigente / total_aged * 100)
        pct_30_60   = metricas.get('pct_30_60',   v30_60  / total_aged * 100)
        pct_60_90   = metricas.get('pct_60_90',   v60_90  / total_aged * 100)
        pct_90_plus = metricas.get('pct_90_plus',  v90_plus / total_aged * 100)

        # Top deudores — cualquier formato
        top_raw = datos.get('top_deudores', [
            {'cliente': d.get('cliente', ''), 'monto': d.get('saldo', d.get('monto', 0)), 'dias_vencido': d.get('dias_vencido', 0)}
            for d in datos.get('por_cliente', [])[:10]
        ])

        md = f"""## Análisis Especializado de Cuentas por Cobrar

### Confianza de Datos: **{confianza:.1f}%**

### Resumen General
| Métrica | Valor |
|---------|-------|
| Total por Cobrar | **{self._m}{total_cxc:,.2f}** |
| Facturas Pendientes | **{facturas_pendientes}** |
| Clientes Deudores | **{clientes_deudores}** |
| Antigüedad Promedio | **{antiguedad_prom:.0f}** días |

### Análisis por Antigüedad
| Período | Monto | % |
|---------|-------|---|
| Vigente (0-30 días) | {self._m}{vigente:,.2f} | {pct_vigente:.1f}% |
| Vencido 30-60 días | {self._m}{v30_60:,.2f} | {pct_30_60:.1f}% |
| Vencido 60-90 días | {self._m}{v60_90:,.2f} | {pct_60_90:.1f}% |
| Vencido +90 días | {self._m}{v90_plus:,.2f} | {pct_90_plus:.1f}% |

### Top Deudores
"""
        if top_raw:
            md += "| # | Cliente | Monto | Días Vencido |\n|---|---------|-------|-------------|\n"
            for i, d in enumerate(top_raw[:10], 1):
                md += f"| {i} | {str(d.get('cliente', ''))[:30]} | {self._m}{d.get('monto', 0):,.2f} | {d.get('dias_vencido', 0)} |\n"

        return md

    def _formatear_cxp_especializado(self, datos: Dict) -> str:
        """Formatear cuentas por pagar con análisis especializado.
        Acepta datos de analizador_avanzado.cuentas_por_pagar() o consultas_especializadas.
        """
        metricas = datos.get('metricas', {})
        confianza = datos.get('confianza', datos.get('confianza_datos', 0))

        total_cxp = metricas.get('total_cxp', datos.get('total', datos.get('total_pendiente', 0)))
        facturas_pendientes = metricas.get('facturas_pendientes', datos.get('total_facturas', datos.get('num_facturas', 0)))
        proveedores = metricas.get('proveedores', len(datos.get('por_proveedor', [])))
        antiguedad_prom = metricas.get('antiguedad_promedio', 0)

        ag = datos.get('por_antiguedad', {})
        vigente  = metricas.get('vigente',       ag.get('0. Por vencer',  ag.get('Al corriente', 0)))
        v30_60   = metricas.get('vencido_30_60',  ag.get('1. 1-30 días',   ag.get('1-30 días',    0)))
        v60_90   = metricas.get('vencido_60_90',  ag.get('2. 31-60 días',  ag.get('31-60 días',   0)))
        v90_plus = metricas.get('vencido_90_plus',
                                ag.get('4. +90 días', ag.get('Más de 90 días', 0))
                                + ag.get('3. 61-90 días', ag.get('61-90 días', 0)))
        total_aged = vigente + v30_60 + v60_90 + v90_plus or 1
        pct_vigente = metricas.get('pct_vigente', vigente / total_aged * 100)
        pct_30_60   = metricas.get('pct_30_60',   v30_60  / total_aged * 100)
        pct_60_90   = metricas.get('pct_60_90',   v60_90  / total_aged * 100)
        pct_90_plus = metricas.get('pct_90_plus',  v90_plus / total_aged * 100)

        top_raw = datos.get('top_proveedores', [
            {'proveedor': d.get('proveedor', d.get('cliente', '')), 'monto': d.get('saldo', d.get('monto', 0)), 'dias_vencido': d.get('dias_vencido', 0)}
            for d in datos.get('por_proveedor', datos.get('por_cliente', []))[:10]
        ])

        md = f"""## Análisis Especializado de Cuentas por Pagar

### Confianza de Datos: **{confianza:.1f}%**

### Resumen General
| Métrica | Valor |
|---------|-------|
| Total por Pagar | **{self._m}{total_cxp:,.2f}** |
| Facturas Pendientes | **{facturas_pendientes}** |
| Proveedores | **{proveedores}** |
| Antigüedad Promedio | **{antiguedad_prom:.0f}** días |

### Análisis por Antigüedad
| Período | Monto | % |
|---------|-------|---|
| Vigente (0-30 días) | {self._m}{vigente:,.2f} | {pct_vigente:.1f}% |
| Vencido 30-60 días | {self._m}{v30_60:,.2f} | {pct_30_60:.1f}% |
| Vencido 60-90 días | {self._m}{v60_90:,.2f} | {pct_60_90:.1f}% |
| Vencido +90 días | {self._m}{v90_plus:,.2f} | {pct_90_plus:.1f}% |

### Top Proveedores por Pagar
"""
        if top_raw:
            md += "| # | Proveedor | Monto | Días Vencido |\n|---|-----------|-------|-------------|\n"
            for i, p in enumerate(top_raw[:10], 1):
                md += f"| {i} | {str(p.get('proveedor', ''))[:30]} | {self._m}{p.get('monto', 0):,.2f} | {p.get('dias_vencido', 0)} |\n"

        return md

    def _formatear_pos_especializado(self, datos: Dict) -> str:
        """Formatear análisis especializado de Punto de Venta."""
        metricas = datos.get('metricas', {})
        confianza = datos.get('confianza', 0)

        md = f"""## Análisis Especializado de Punto de Venta

### Confianza de Datos: **{confianza:.1f}%**

### Métricas Generales
| Métrica | Valor |
|---------|-------|
| Total Tickets | **{metricas.get('total_tickets', 0):,}** |
| Ventas Totales | **{self._m}{metricas.get('total_ventas', 0):,.2f}** |
| Ticket Promedio | **{self._m}{metricas.get('ticket_promedio', 0):,.2f}** |
| Ticket Máximo | **{self._m}{metricas.get('ticket_maximo', 0):,.2f}** |
| Artículos por Ticket | **{metricas.get('articulos_promedio', 0):.1f}** |

### Métodos de Pago
"""
        metodos = datos.get('metodos_pago', [])
        if metodos:
            md += "| Método | Transacciones | Monto | % |\n|--------|---------------|-------|---|\n"
            for m in metodos[:5]:
                md += f"| {m.get('metodo', '')} | {m.get('transacciones', 0)} | {self._m}{m.get('monto', 0):,.2f} | {m.get('porcentaje', 0):.1f}% |\n"
        
        md += "\n### Ventas por Sesión/Sucursal\n"
        sesiones = datos.get('por_sesion', [])
        if sesiones:
            md += "| Sesión | Tickets | Total |\n|--------|---------|-------|\n"
            for s in sesiones[:10]:
                md += f"| {str(s.get('sesion', ''))[:30]} | {s.get('tickets', 0)} | {self._m}{s.get('total', 0):,.2f} |\n"
        
        return md

    def _formatear_comparativa_periodos(self, datos: Dict) -> str:
        """Formatear comparativa entre períodos."""
        actual = datos.get('periodo_actual', {})
        anterior = datos.get('periodo_anterior', {})
        variacion = datos.get('variacion', {})
        confianza = datos.get('confianza', 0)
        
        emoji_var = '📈' if variacion.get('porcentaje', 0) > 0 else '📉' if variacion.get('porcentaje', 0) < 0 else '➡️'
        color_var = '🟢' if variacion.get('porcentaje', 0) > 5 else '🔴' if variacion.get('porcentaje', 0) < -5 else '🟡'
        
        md = f"""## Comparativa de Períodos

### Confianza de Datos: **{confianza:.1f}%**

### Período Actual: {actual.get('nombre', '')}
| Métrica | Valor |
|---------|-------|
| Órdenes | **{actual.get('ordenes', 0):,}** |
| Total Ventas | **{self._m}{actual.get('total', 0):,.2f}** |
| Promedio | **{self._m}{actual.get('promedio', 0):,.2f}** |

### Período Anterior: {anterior.get('nombre', '')}
| Métrica | Valor |
|---------|-------|
| Órdenes | **{anterior.get('ordenes', 0):,}** |
| Total Ventas | **{self._m}{anterior.get('total', 0):,.2f}** |
| Promedio | **{self._m}{anterior.get('promedio', 0):,.2f}** |

### {emoji_var} Variación {color_var}
| Métrica | Valor |
|---------|-------|
| Variación % | **{variacion.get('porcentaje', 0):+.1f}%** |
| Variación Absoluta | **{self._m}{variacion.get('absoluta', 0):+,.2f}** |
| Variación Órdenes | **{variacion.get('ordenes', 0):+,}** |

### Análisis
"""
        for insight in datos.get('insights', []):
            md += f"- {insight}\n"
        
        return md

    def _formatear_clientes_especializado(self, datos: Dict) -> str:
        """Formatear análisis especializado de clientes."""
        metricas = datos.get('metricas', {})
        confianza = datos.get('confianza', 0)
        
        md = f"""## Análisis Especializado de Clientes

### Confianza de Datos: **{confianza:.1f}%**

### Métricas Generales
| Métrica | Valor |
|---------|-------|
| Total Clientes | **{metricas.get('total_clientes', 0):,}** |
| Clientes Activos | **{metricas.get('clientes_activos', 0)}** |
| Nuevos (30 días) | **{metricas.get('clientes_nuevos', 0)}** |
| Ventas Promedio/Cliente | **{self._m}{metricas.get('ventas_promedio_cliente', 0):,.2f}** |

### Top Clientes por Valor
"""
        top_clientes = datos.get('top_clientes', [])
        if top_clientes:
            md += "| # | Cliente | Órdenes | Total | % Participación |\n|---|---------|---------|-------|----------------|\n"
            total_ventas = sum(c.get('total', 0) for c in top_clientes)
            for i, c in enumerate(top_clientes[:10], 1):
                pct = (c.get('total', 0) / total_ventas * 100) if total_ventas > 0 else 0
                md += f"| {i} | {str(c.get('cliente', ''))[:30]} | {c.get('ordenes', 0)} | {self._m}{c.get('total', 0):,.2f} | {pct:.1f}% |\n"
        
        md += "\n### Segmentación\n"
        segmentos = datos.get('segmentos', {})
        if segmentos:
            md += "| Segmento | Clientes | % |\n|----------|----------|---|\n"
            for seg, info in segmentos.items():
                md += f"| {seg} | {info.get('cantidad', 0)} | {info.get('porcentaje', 0):.1f}% |\n"
        
        return md

    def _formatear_empresas_resumen(self, datos: Dict) -> str:
        """Formatear resumen de empresas del sistema."""
        metricas = datos.get('metricas', {})
        confianza = datos.get('confianza', 0)
        
        md = f"""## Resumen de Empresas del Sistema

### Confianza de Datos: **{confianza:.1f}%**

### Visión General
| Métrica | Valor |
|---------|-------|
| Total Empresas | **{metricas.get('total_empresas', 0)}** |
| Empresas Activas | **{metricas.get('empresas_activas', 0)}** |
| Ventas Totales | **{self._m}{metricas.get('ventas_totales', 0):,.2f}** |

### Detalle por Empresa
"""
        empresas = datos.get('empresas', [])
        if empresas:
            md += "| Empresa | Ventas | Compras | % Participación |\n|---------|--------|---------|----------------|\n"
            total = sum(e.get('ventas', 0) for e in empresas)
            for emp in empresas[:10]:
                pct = (emp.get('ventas', 0) / total * 100) if total > 0 else 0
                md += f"| {str(emp.get('nombre', ''))[:30]} | {self._m}{emp.get('ventas', 0):,.2f} | {self._m}{emp.get('compras', 0):,.2f} | {pct:.1f}% |\n"
        
        return md

    def _formatear_reporte_ejecutivo(self, datos: Dict) -> str:
        """Formatear reporte ejecutivo completo generado por el cerebro."""
        confianza = datos.get('confianza', 0)
        emoji_conf = '🟢' if confianza >= 95 else '🟡' if confianza >= 80 else '🔴'
        
        md = f"""## REPORTE EJECUTIVO - ANDROMEDA

### Confianza de Datos: {emoji_conf} **{confianza:.1f}%**
_Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}_

---

### VENTAS
"""
        ventas = datos.get('ventas', {})
        md += f"""| Métrica | Valor |
|---------|-------|
| Órdenes | **{ventas.get('ordenes', 0):,}** |
| Total | **{self._m}{ventas.get('total', 0):,.2f}** |
| Promedio | **{self._m}{ventas.get('promedio', 0):,.2f}** |

### INVENTARIO
"""
        inventario = datos.get('inventario', {})
        md += f"""| Métrica | Valor |
|---------|-------|
| Productos | **{inventario.get('productos', 0):,}** |
| Unidades | **{inventario.get('unidades', 0):,.0f}** |
| Valor Estimado | **{self._m}{inventario.get('valor', 0):,.2f}** |
| Productos Críticos | **{inventario.get('criticos', 0)}** |

### CARTERA
"""
        cartera = datos.get('cartera', {})
        md += f"""| Concepto | Valor |
|----------|-------|
| Por Cobrar (CXC) | **{self._m}{cartera.get('cxc', 0):,.2f}** |
| Por Pagar (CXP) | **{self._m}{cartera.get('cxp', 0):,.2f}** |
| Flujo Neto | **{self._m}{cartera.get('flujo_neto', 0):+,.2f}** |

### PUNTO DE VENTA
"""
        pos = datos.get('pos', {})
        md += f"""| Métrica | Valor |
|---------|-------|
| Tickets | **{pos.get('tickets', 0):,}** |
| Ventas POS | **{self._m}{pos.get('total', 0):,.2f}** |
| Ticket Promedio | **{self._m}{pos.get('promedio', 0):,.2f}** |

### INSIGHTS PRINCIPALES
"""
        for insight in datos.get('insights', []):
            md += f"- {insight}\n"
        
        md += "\n### RECOMENDACIONES\n"
        for rec in datos.get('recomendaciones', []):
            md += f"- {rec}\n"
        
        md += f"\n---\n_Generado por ANDROMEDA v5.0 - Sistema de Inteligencia Empresarial_"
        return md

    def _formatear_top_proveedores(self, datos: Dict, limite: int) -> str:
        md = f"## Top {limite} Proveedores\n\n"
        md += "| # | Proveedor | Órdenes | Total |\n|---|-----------|---------|-------|\n"
        
        for i, p in enumerate(datos.get('ranking', [])[:limite], 1):
            md += f"| {i} | {str(p.get('proveedor', ''))[:30]} | {p.get('ordenes', 0)} | {self._m}{p.get('total', 0):,.2f} |\n"
        
        return md

    def _formatear_contratos(self, datos: Dict) -> str:
        contratos = datos.get('contratos', [])
        if not contratos:
            return datos.get('mensaje', 'No hay contratos por vencer próximamente')
        
        md = f"""## Contratos por Vencer

 **{datos.get('total', 0)}** contratos vencen en los próximos 30 días.

| Empleado | Vence | Días | Salario |
|----------|-------|------|---------|
"""
        for c in contratos[:15]:
            md += f"| {c.get('empleado', '')[:25]} | {c.get('date_end', '')} | {c.get('dias_restantes', 0)} | {self._m}{c.get('wage', 0):,.2f} |\n"
        
        return md

    def _formatear_usuarios(self, datos: Dict) -> str:
        return f"""## 👤 Usuarios del Sistema

| Métrica | Valor |
|---------|-------|
| Total usuarios | **{datos.get('total_usuarios', 0)}** |
| Activos (7 días) | **{datos.get('activos_7_dias', 0)}** |
| Inactivos (+30 días) | **{datos.get('inactivos_30_dias', 0)}** |

_Ver tabla para detalles_"""

    def _formatear_anomalias(self, anomalias: List) -> str:
        """Formatear anomalías detectadas."""
        if not anomalias:
            return "## Sin Anomalías Detectadas\n\nNo se encontraron patrones anómalos en los datos."
        
        md = f"""## Anomalías Financieras Detectadas

**Total:** {len(anomalias)} anomalías identificadas

"""
        nivel_emoji = {
            'urgent': 'URGENTE',
            'critical': 'CRÍTICO',
            'warning': 'ATENCIÓN',
            'info': 'INFO'
        }
        
        for i, anomalia in enumerate(anomalias[:10], 1):
            nivel = getattr(anomalia, 'nivel', None)
            nivel_str = nivel.value if nivel else 'info'
            emoji = nivel_emoji.get(nivel_str, '⚪')
            
            md += f"""### {emoji} {i}. {anomalia.titulo}
- **Descripción:** {anomalia.descripcion}
- **Valor Actual:** {self._m}{anomalia.valor_actual:,.2f}
- **Esperado:** {self._m}{anomalia.valor_esperado:,.2f}
- **Desviación:** {anomalia.desviacion_porcentual:+.1f}%
- **Confianza:** {anomalia.confianza:.0f}%
- **Recomendación:** {anomalia.recomendacion}

"""
        return md

    def _formatear_riesgos(self, resultado) -> str:
        """Formatear análisis de riesgos."""
        score = resultado.score_riesgo
        
        if score < 20:
            estado = "BAJO RIESGO"
        elif score < 50:
            estado = "RIESGO MODERADO"
        elif score < 75:
            estado = "ALTO RIESGO"
        else:
            estado = "RIESGO CRÍTICO"
        
        md = f"""## Análisis de Riesgos Empresariales

### Estado: {estado}
**Score de Riesgo:** {score:.0f}/100

### Resumen
| Métrica | Valor |
|---------|-------|
| Transacciones analizadas | {resultado.transacciones_analizadas:,} |
| Entidades revisadas | {resultado.entidades_revisadas:,} |
| Hallazgos | {len(resultado.hallazgos)} |

### Recomendaciones de Control

"""
        for i, rec in enumerate(resultado.recomendaciones_control[:5], 1):
            md += f"{i}. {rec}\n\n"
        
        return md

    def _formatear_auditoria_nocturna(self, resultado) -> str:
        """Formatea el resultado de la auditoría nocturna completa."""
        alertas_criticas = len(resultado.alertas_criticas)
        alertas_warning = len(resultado.alertas_warning)
        alertas_info = len(resultado.alertas_info)
        
        # Determinar estado general
        if resultado.score_salud >= 80:
            emoji_estado = "🟢"
            estado = "EXCELENTE"
        elif resultado.score_salud >= 60:
            emoji_estado = "🟡"
            estado = "MODERADO"
        else:
            emoji_estado = "🔴"
            estado = "CRÍTICO"
        
        md = f"""## Auditoría Nocturna Completa

### {emoji_estado} Estado General: **{estado}** | Score: **{resultado.score_salud}/100**

---

### Resumen de Alertas

| Tipo | Cantidad | Estado |
|------|----------|--------|
| Críticas | **{alertas_criticas}** | {'Atención inmediata' if alertas_criticas > 0 else 'OK'} |
| Warnings | **{alertas_warning}** | {'Revisar pronto' if alertas_warning > 0 else 'OK'} |
| Informativas | **{alertas_info}** | {'Notar' if alertas_info > 0 else 'OK'} |

---
"""
        
        # Mostrar alertas críticas
        if resultado.alertas_criticas:
            md += "\n### Alertas Críticas (Acción Inmediata)\n\n"
            for alerta in resultado.alertas_criticas[:5]:
                md += f"""<div style="background:rgba(239,68,68,0.1);border-left:4px solid #ef4444;padding:12px;margin:8px 0;border-radius:8px;">
<b>{alerta.titulo}</b><br>
 {alerta.descripcion}<br>
 Impacto: {alerta.impacto}<br>
 <i>{alerta.accion_sugerida}</i>
</div>\n"""
        
        # Mostrar alertas de warning
        if resultado.alertas_warning:
            md += "\n### Alertas de Advertencia\n\n"
            for alerta in resultado.alertas_warning[:5]:
                md += f"""<div style="background:rgba(245,158,11,0.1);border-left:4px solid #f59e0b;padding:12px;margin:8px 0;border-radius:8px;">
<b>{alerta.titulo}</b><br>
 {alerta.descripcion}<br>
 <i>{alerta.accion_sugerida}</i>
</div>\n"""
        
        # Mostrar alertas informativas
        if resultado.alertas_info:
            md += "\n### Alertas Informativas\n\n"
            for alerta in resultado.alertas_info[:3]:
                md += f"- **{alerta.titulo}**: {alerta.descripcion}\n"
        
        md += f"\n---\n\n*Auditoría ejecutada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        return md

    def _formatear_semaforo_salud(self, semaforo: Dict) -> str:
        """Formatea el semáforo de salud operativa."""
        indicadores = semaforo.get('indicadores', {})
        score_global = semaforo.get('score_global', 0)
        recomendaciones = semaforo.get('recomendaciones', [])
        
        # Determinar color del semáforo
        if score_global >= 80:
            semaforo_html = '<div style="width:80px;height:80px;border-radius:50%;background:#22c55e;margin:0 auto;display:flex;align-items:center;justify-content:center;font-size:32px;box-shadow:0 0 20px #22c55e;">🟢</div>'
            estado = "ÓPTIMO"
        elif score_global >= 60:
            semaforo_html = '<div style="width:80px;height:80px;border-radius:50%;background:#f59e0b;margin:0 auto;display:flex;align-items:center;justify-content:center;font-size:32px;box-shadow:0 0 20px #f59e0b;">🟡</div>'
            estado = "MODERADO"
        else:
            semaforo_html = '<div style="width:80px;height:80px;border-radius:50%;background:#ef4444;margin:0 auto;display:flex;align-items:center;justify-content:center;font-size:32px;box-shadow:0 0 20px #ef4444;">🔴</div>'
            estado = "CRÍTICO"
        
        md = f"""## 🚦 Semáforo de Salud Operativa

<div style="text-align:center;margin:20px 0;">
{semaforo_html}
<h2 style="margin-top:16px;">Score Global: <span style="color:#667eea;">{score_global}/100</span></h2>
<p style="color:#8b949e;font-size:18px;">Estado: <b>{estado}</b></p>
</div>

---

### Indicadores por Área

| Área | Score | Estado |
|------|-------|--------|
"""
        
        for area, datos in indicadores.items():
            score = datos.get('score', 0)
            if score >= 80:
                emoji = "🟢"
            elif score >= 60:
                emoji = "🟡"
            else:
                emoji = "🔴"
            md += f"| {area} | **{score}** | {emoji} |\n"
        
        if recomendaciones:
            md += "\n---\n\n### Recomendaciones Prioritarias\n\n"
            for i, rec in enumerate(recomendaciones[:5], 1):
                md += f"{i}. {rec}\n"
        
        return md

    def _formatear_churn_clientes(self, predicciones: List) -> str:
        """Formatea las predicciones de churn de clientes."""
        if not predicciones:
            return "No se detectaron clientes en riesgo de abandono significativo."
        
        alto_riesgo = [p for p in predicciones if p.riesgo_churn >= 0.7]
        medio_riesgo = [p for p in predicciones if 0.4 <= p.riesgo_churn < 0.7]
        
        total_valor = sum(p.valor_potencial_perdido for p in predicciones)
        
        md = f"""## Análisis de Riesgo de Churn (Abandono de Clientes)

### Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Alto riesgo (>70%) | **{len(alto_riesgo)} clientes** |
| Medio riesgo (40-70%) | **{len(medio_riesgo)} clientes** |
| Valor en riesgo total | **{self._m}{total_valor:,.2f}** |

---

### Clientes en Alto Riesgo de Abandono

"""
        for p in alto_riesgo[:10]:
            md += f"""<div style="background:rgba(239,68,68,0.1);border-left:4px solid #ef4444;padding:12px;margin:8px 0;border-radius:8px;">
<b>{p.cliente_nombre}</b><br>
Última compra: {p.ultima_compra.strftime('%Y-%m-%d') if p.ultima_compra else 'N/A'}<br>
Días sin comprar: <b>{p.dias_sin_comprar}</b> (habitual: {p.frecuencia_habitual_dias} días)<br>
Riesgo: <b style="color:#ef4444;">{p.riesgo_churn:.0%}</b><br>
Valor en riesgo: <b>{self._m}{p.valor_potencial_perdido:,.2f}</b>
</div>\n"""
        
        md += "\n### Acciones Recomendadas\n\n"
        md += "1. Contactar clientes de alto riesgo con oferta personalizada\n"
        md += "2. Campaña de reactivación por email\n"
        md += "3. Ofrecer descuento o beneficio especial\n"
        md += "4. Analizar causas de abandono (precio, servicio, competencia)\n"
        
        return md

    def _formatear_reposicion_jit(self, alertas: List) -> str:
        """Formatea las alertas de reposición Just-in-Time."""
        if not alertas:
            return "Todos los productos tienen stock suficiente. No se requiere reposición urgente."
        
        criticos = [a for a in alertas if a.urgencia == 'CRÍTICO']
        urgentes = [a for a in alertas if a.urgencia == 'URGENTE']
        normales = [a for a in alertas if a.urgencia == 'NORMAL']
        
        md = f"""## Reposición de Inventario Just-in-Time

### Resumen

| Urgencia | Productos | Acción |
|----------|-----------|--------|
| CRÍTICO | **{len(criticos)}** | Pedir HOY |
| URGENTE | **{len(urgentes)}** | Pedir esta semana |
| NORMAL | **{len(normales)}** | Programar pedido |

---

"""
        if criticos:
            md += "### Productos CRÍTICOS (Pedir HOY)\n\n"
            md += "| Producto | Stock | Consumo/día | Días | Cantidad |\n"
            md += "|----------|-------|-------------|------|----------|\n"
            for a in criticos[:10]:
                md += f"| {a.producto[:30]} | {a.stock_actual} | {a.consumo_diario:.1f} | {a.dias_cobertura} | **{a.cantidad_sugerida}** |\n"
        
        if urgentes:
            md += "\n### Productos URGENTES (Esta semana)\n\n"
            md += "| Producto | Stock | Días cobertura | Cantidad sugerida |\n"
            md += "|----------|-------|----------------|-------------------|\n"
            for a in urgentes[:10]:
                md += f"| {a.producto[:30]} | {a.stock_actual} | {a.dias_cobertura} | {a.cantidad_sugerida} |\n"
        
        return md

    def _formatear_stock_lento(self, datos: Dict) -> str:
        """Formatea el análisis de stock lento."""
        productos = datos.get('productos', [])
        resumen = datos.get('resumen', {})
        
        if not productos:
            return "No se detectó inventario con rotación lenta significativa."
        
        md = f"""## Análisis de Stock Lento y Muerto

### Resumen

| Métrica | Valor |
|---------|-------|
| Productos con stock lento | **{resumen.get('total_productos_lentos', 0)}** |
| Valor inmovilizado | **{self._m}{resumen.get('valor_inmovilizado', 0):,.2f}** |
| Días promedio sin movimiento | **{resumen.get('dias_promedio_sin_movimiento', 0)}** |

---

### Productos con Stock Muerto (Sin movimiento)

| Producto | Stock | Valor | Días sin venta | Sugerencia |
|----------|-------|-------|----------------|------------|
"""
        for p in productos[:15]:
            producto = p.get('nombre', 'N/A')[:30]
            stock = p.get('stock', 0)
            valor = p.get('valor', 0)
            dias = p.get('dias_sin_venta', 0)
            sugerencia = "🔴 Liquidar" if dias > 180 else "🟡 Promocionar"
            md += f"| {producto} | {stock} | {self._m}{valor:,.2f} | {dias} | {sugerencia} |\n"
        
        md += "\n### Recomendaciones\n\n"
        md += "1. **Liquidación**: Productos sin movimiento >180 días\n"
        md += "2. **Promoción**: Descuentos para productos 90-180 días\n"
        md += "3. **Devolución**: Negociar con proveedores si es posible\n"
        md += "4. **Donación**: Considerar para productos obsoletos\n"
        
        return md

    def _formatear_clientes_olvidados(self, datos: Dict) -> str:
        """Formatea el análisis de clientes olvidados."""
        clientes = datos.get('clientes', [])
        resumen = datos.get('resumen', {})
        
        if not clientes:
            return "Todos los clientes tienen actividad reciente. No hay clientes olvidados significativos."
        
        md = f"""## Clientes Olvidados (Reactivación)

### Resumen

| Métrica | Valor |
|---------|-------|
| Clientes potenciales | **{resumen.get('total_clientes', 0)}** |
| Valor histórico total | **{self._m}{resumen.get('valor_historico', 0):,.2f}** |
| Promedio días inactivos | **{resumen.get('dias_promedio_inactivos', 0)}** |

---

### Clientes Prioritarios para Reactivación

"""
        for c in clientes[:10]:
            md += f"""<div style="background:rgba(102,126,234,0.1);border-left:4px solid #667eea;padding:12px;margin:8px 0;border-radius:8px;">
<b> {c.get('nombre', 'N/A')}</b><br>
 Inactivo por: {c.get('meses_inactivo', 0)} meses<br>
 Compras históricas: <b>{self._m}{c.get('compra_historica', 0):,.2f}</b><br>
 {c.get('email', 'Sin email') or 'Sin email'} |  {c.get('telefono', 'Sin teléfono') or 'Sin teléfono'}
</div>\n"""
        
        md += "\n### Estrategias de Reactivación\n\n"
        md += "1. **Email personalizado** con oferta especial\n"
        md += "2. **Llamada de seguimiento** del equipo comercial\n"
        md += "3. **Cupón de descuento** o regalo por regreso\n"
        md += "4. **Campaña de remarketing** en redes sociales\n"
        
        return md

    def _formatear_alertas_auditoria(self, titulo: str, alertas: List, emoji: str) -> str:
        """Formatea un conjunto de alertas de auditoría."""
        if not alertas:
            return f"**{titulo}**: No se detectaron problemas."
        
        md = f"""## {emoji} {titulo}

### Se detectaron **{len(alertas)}** alertas

---

"""
        for i, alerta in enumerate(alertas[:15], 1):
            severidad_color = {
                'critica': '#ef4444',
                'warning': '#f59e0b', 
                'info': '#3b82f6'
            }
            color = severidad_color.get(alerta.categoria, '#6b7280')
            
            md += f"""<div style="background:rgba(102,126,234,0.05);border-left:4px solid {color};padding:12px;margin:8px 0;border-radius:8px;">
<b>#{i} {alerta.titulo}</b><br>
 {alerta.descripcion}<br>
 Impacto: {alerta.impacto}<br>
 <i>{alerta.accion_sugerida}</i>
</div>\n"""
        
        return md

    def _formatear_diagnostico_error(self, diagnostico: Dict) -> str:
        """Formatea el diagnóstico de un error de Odoo."""
        if not diagnostico:
            return "No se pudo diagnosticar el error. Por favor, proporciona más detalles."
        
        md = f"""## Diagnóstico de Error

### Problema Detectado
**{diagnostico.get('tipo_error', 'Error desconocido')}**

---

### Descripción
{diagnostico.get('descripcion', 'Sin descripción disponible')}

### Causa Probable
{diagnostico.get('causa', 'No se pudo determinar la causa')}

---

### Solución Recomendada

{diagnostico.get('solucion', 'Contactar con soporte técnico')}

---

### Pasos a Seguir

"""
        pasos = diagnostico.get('pasos', [])
        for i, paso in enumerate(pasos, 1):
            md += f"{i}. {paso}\n"
        
        if not pasos:
            md += "1. Verificar la conexión con Odoo\n"
            md += "2. Revisar los permisos del usuario\n"
            md += "3. Contactar con soporte si persiste\n"
        
        return md
