# ============================================================
# ANDROMEDA - Ejecutor de Acciones
# ============================================================
# Módulo extraído de interfaz_v5.py (ARQ-v2-001)
# Centraliza _ejecutar_accion y todos sus helpers:
#   - _generar_tendencia, _generar_kpis_por_tienda
#   - _consultar_facturas_filtradas, _generar_reporte
#   - _generar_pdf_profesional, _ejecutar_consulta_dinamica
#   - _contar_chiste, _mostrar_capacidades, _responder_*
#   - _ventas_tienda_especifica, _generar_ayuda_completa
#   - _info_conexion, _ejecutar_consulta_avanzada_v2
#   - _mapear_accion_a_consulta_odoo, _respuesta_accion_no_disponible
# ============================================================

from app.logging_config import get_logger
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
import os
import pandas as pd

# Base de Conocimiento (importación defensiva)
try:
    from services.knowledge.procesador_manuales import obtener_procesador, buscar_en_manual
    MANUAL_ODOO_DISPONIBLE = True
except Exception:
    MANUAL_ODOO_DISPONIBLE = False
    buscar_en_manual = None

logger = get_logger("services.actions.ejecutor_acciones")


class EjecutorAcciones:
    """Ejecuta acciones del sistema según la consulta entendida.
    
    Extraído de OdooAIProV5._ejecutar_accion (ARQ-v2-001).
    Recibe referencia al bot para acceder a todos los servicios.
    """

    def __init__(self, bot):
        self._bot = bot

    def ejecutar(self, consulta, mensaje: str = ""):
        """Punto de entrada principal — delega a _ejecutar_accion."""
        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutar_accion(self, consulta, mensaje: str = "") -> Tuple[str, pd.DataFrame]:
        """Ejecuta la acción basada en la consulta entendida con manejo de errores."""
        accion = consulta.accion_sugerida
        temp = consulta.temporalidad
        params = consulta.parametros or {}
        df = None
        respuesta = ""

        fecha_ini = temp.get('fecha_inicio')
        fecha_fin = temp.get('fecha_fin')

        # ==== MANUALES / AYUDA / CONSULTA GENERAL ====
        if accion in ('consultar_manual', 'manual_odoo', 'manual_facturacion', 'manual_pos',
                      'manual_inventario', 'manual_crm', 'manual_ventas', 'manual_rrhh',
                      'manual_compras', 'manual_configuracion'):
            if MANUAL_ODOO_DISPONIBLE and buscar_en_manual:
                try:
                    # buscar_en_manual() retorna un str con Markdown ya formateado
                    respuesta = buscar_en_manual(mensaje)
                    if not respuesta or respuesta.strip().startswith("No encontré"):
                        respuesta = (
                            "No encontré secciones del manual que coincidan con tu consulta. "
                            "Intenta con términos más específicos como _'crear factura'_, "
                            "_'cancelar pedido'_, _'configurar impuesto'_, _'cierre de caja'_."
                        )
                except Exception as e:
                    logger.error(f"Error consultando manual: {e}")
                    respuesta = (
                        "Ocurrió un error al consultar el manual. "
                        "Para procedimientos de Odoo visita https://www.odoo.com/documentation"
                    )
            else:
                respuesta = (
                    "## 📖 Consulta de Manual\n\n"
                    "El módulo de manuales no está disponible en este momento. "
                    "Para consultar procedimientos de Odoo, visita la documentación oficial en https://www.odoo.com/documentation"
                )

        elif accion in ('ayuda', 'mostrar_capacidades'):
            respuesta = self._generar_ayuda_completa()

        elif accion and str(accion).startswith('graficar'):
            # Acciones de gráfica: obtener datos reales para que la interfaz (Gradio y API)
            # genere la visualización. Se mapea a la consulta de datos correspondiente.
            try:
                # Mapear acción de gráfica → consulta de datos equivalente
                _mapa_grafica = {
                    'graficar_ventas_tienda': 'ventas_por_tienda',
                    'graficar_pos': 'ventas_por_tienda',
                    'graficar_ventas': 'consultar_ventas',
                    'graficar_inventario': 'analisis_inventario',
                    'graficar_clientes': 'top_clientes',
                    'graficar_finanzas': 'cuentas_cobrar',
                    'graficar_kpis': 'semaforo_salud',
                }
                accion_datos = _mapa_grafica.get(str(accion), 'consultar_ventas')

                # Clonar consulta apuntando a la acción de datos equivalente
                import copy
                consulta_datos = copy.copy(consulta)
                consulta_datos.accion_sugerida = accion_datos
                respuesta_datos, df = self._ejecutar_accion(consulta_datos, mensaje)

                if df is not None and not df.empty:
                    respuesta = f"📊 **Visualización lista** — datos de {accion_datos.replace('_', ' ')}\n\n"
                    respuesta += respuesta_datos
                else:
                    # Fallback: usar ultimo_df si la consulta no devolvió datos nuevos
                    respuesta = (
                        "📊 **Visualización generada** a partir de los últimos datos consultados.\n\n"
                        "_Si deseas graficar datos diferentes, incluye la consulta en el mismo mensaje._"
                    )
                    df = getattr(self._bot, 'ultimo_df', None)
            except Exception as e:
                logger.warning(f"graficar_* fallback por error: {e}")
                respuesta = "📊 **Visualización lista** — usando datos del contexto actual."
                df = getattr(self._bot, 'ultimo_df', None)

        elif accion == 'info_conexion':
            respuesta = self._bot._info_conexion() if hasattr(self._bot, '_info_conexion') else "Conexión activa con Odoo."

        elif accion in ('saludo', 'despedida'):
            respuesta = (
                "¡Hola! Soy **ANDROMEDA**, tu asistente de análisis empresarial para Odoo.\n\n"
                "Estoy listo para ayudarte con análisis de ventas, inventario, finanzas, predicciones, "
                "auditorías inteligentes, manuales de Odoo y mucho más.\n\n"
                "Puedes preguntarme directamente, por ejemplo:\n"
                "- _'¿Cuánto vendimos este mes?'_\n"
                "- _'¿Qué productos están por agotarse?'_\n"
                "- _'Predice las ventas para los próximos 30 días'_\n"
                "- _'¿Cómo cancelo una factura en Odoo?'_\n\n"
                "¿En qué te puedo ayudar hoy?"
            )

        elif accion in ('consulta_general', 'desconocida', '', None):
            # IMPORTANTE: NO usar LLM aquí. El LLM no tiene acceso a los datos reales
            # del negocio y fabrica respuestas numéricas plausibles pero falsas.
            # La respuesta orientativa guia al usuario a formular una consulta ejecutable.
            respuesta = self._respuesta_consulta_general(mensaje)

        # ==== PREDICCIONES ====
        elif accion in ('predecir_ventas', 'predecir', 'prediccion_ventas_inteligente'):
            # Extraer días desde entidades o parámetros - default 30 días
            # El NLP extrae "para N días" / "próximos N días" como params['limite']
            dias = params.get('limite', 30)

            # Buscar horizonte en entidades del cerebro (prioridad: periodo_prediccion > horizonte > params)
            encontrado = False
            entidades_cerebro = self._bot._obtener_entidades_cerebro(consulta)

            for ent in entidades_cerebro:
                if hasattr(ent, 'tipo'):
                    if ent.tipo == 'periodo_prediccion' and isinstance(ent.valor, dict):
                        # Usar los días calculados desde el período futuro
                        dias = ent.valor.get('dias', params.get('limite', 30))
                        encontrado = True
                        break
                    elif ent.tipo == 'horizonte' and not encontrado:
                        dias = ent.valor if isinstance(ent.valor, int) else 30
                        encontrado = True
            
            # Limitar a un máximo razonable de 365 días
            dias = min(max(dias, 1), 365)
            print(f"Debug predicción: dias={dias}")
            
            pred = self._bot.predictor.predecir_ventas(dias)
            respuesta = self._bot.predictor.formatear_prediccion_md(pred)
            # Guardar predicción completa para que la interfaz pueda graficar
            # histórico + proyección con banda de confianza
            self._bot.ultima_prediccion = pred
            if pred.datos_historicos:
                df = pd.DataFrame(pred.datos_historicos[-30:])
        
        elif accion in ('predecir_agotamiento', 'prediccion_inventario_inteligente'):
            datos = self._bot.predictor.predecir_agotamiento()
            if 'error' not in datos:
                respuesta = self._bot.fmt._formatear_prediccion_inventario(datos)
                if datos.get('predicciones'):
                    df = pd.DataFrame(datos['predicciones'][:20])
            else:
                respuesta = f"{datos['error']}"
        
        elif accion == 'flujo_caja':
            datos = self._bot.predictor.predecir_flujo_caja()
            if 'error' not in datos:
                respuesta = self._bot.fmt._formatear_flujo_caja(datos)
            else:
                respuesta = f"{datos['error']}"
        
        elif accion in ('salud_negocio', 'semaforo_salud'):
            datos = self._bot.predictor.score_salud_negocio()
            if 'error' not in datos:
                respuesta = self._bot.fmt._formatear_salud_negocio(datos)
            else:
                respuesta = f"{datos['error']}"
        
        elif accion == 'estacionalidad':
            datos = self._bot.predictor.analizar_estacionalidad()
            if 'error' not in datos:
                respuesta = self._bot.fmt._formatear_estacionalidad(datos)
                if datos.get('por_dia_semana'):
                    df = pd.DataFrame(datos['por_dia_semana'])
            else:
                respuesta = f"{datos['error']}"
        
        elif accion in ('comparar_periodos', 'comparativa_periodos', 'comparar_periodos_especificos'):
            contexto_lower = consulta.contexto.lower()

            # ── Comparativa con periodos ESPECÍFICOS extraídos por el NLP ──────
            # Activado cuando el usuario escribe "marzo 2026 vs marzo 2025", "2025 vs 2024", etc.
            if temp.get('fecha_inicio_a') and temp.get('fecha_inicio_b'):
                ini_a = temp['fecha_inicio_a']
                fin_a = temp['fecha_fin_a']
                ini_b = temp['fecha_inicio_b']
                fin_b = temp['fecha_fin_b']
                label_a = temp.get('periodo_a', ini_a[:7])
                label_b = temp.get('periodo_b', ini_b[:7])

                if self._bot.odoo and self._bot.odoo.conectado:
                    import pandas as _pd
                    df_a = self._bot.odoo.ventas_periodo(ini_a, fin_a)
                    df_b = self._bot.odoo.ventas_periodo(ini_b, fin_b)
                    total_a = df_a['amount_total'].sum() if df_a is not None and not df_a.empty else 0
                    total_b = df_b['amount_total'].sum() if df_b is not None and not df_b.empty else 0
                    n_a = len(df_a) if df_a is not None else 0
                    n_b = len(df_b) if df_b is not None else 0
                    variacion = ((total_a - total_b) / total_b * 100) if total_b > 0 else (100.0 if total_a > 0 else 0.0)
                    emoji = '🟢' if variacion >= 0 else '🔴'
                    ticket_a = total_a / n_a if n_a else 0
                    ticket_b = total_b / n_b if n_b else 0
                    respuesta = (
                        f"## Comparativa: {label_a} vs {label_b}\n\n"
                        f"| Métrica | {label_a} | {label_b} | Variación |\n"
                        f"|---------|{'-'*len(label_a)}|{'-'*len(label_b)}|----------:|\n"
                        f"| **Ventas totales** | **${total_a:,.2f}** | **${total_b:,.2f}** | {emoji} {variacion:+.1f}% |\n"
                        f"| **Órdenes** | {n_a:,} | {n_b:,} | — |\n"
                        f"| **Ticket promedio** | ${ticket_a:,.2f} | ${ticket_b:,.2f} | — |\n\n"
                        f"**Diferencia absoluta:** ${total_a - total_b:+,.2f}\n\n"
                        f"> *{label_a}: {ini_a} → {fin_a}*  \n"
                        f"> *{label_b}: {ini_b} → {fin_b}*"
                    )
                    # DataFrame para gráfica
                    if df_a is not None and not df_a.empty and df_b is not None and not df_b.empty:
                        df_a['periodo'] = label_a
                        df_b['periodo'] = label_b
                        df = _pd.concat([df_a, df_b], ignore_index=True)
                else:
                    respuesta = "Sin conexión a Odoo para realizar la comparativa."

            else:
                # ── Comparativa genérica (esta semana vs pasada, este mes vs anterior) ──
                tipo_comparativa = None

                # Buscar primero en entidades del cerebro (más preciso)
                for ent in self._bot._obtener_entidades_cerebro(consulta):
                    if hasattr(ent, 'tipo') and ent.tipo == 'tipo_comparativa':
                        tipo_comparativa = ent.valor
                        break

                # Si no se encontró en entidades, inferir del texto
                if not tipo_comparativa:
                    if 'ayer' in contexto_lower or 'hoy vs ayer' in contexto_lower:
                        tipo_comparativa = 'dia'
                    elif any(m in contexto_lower for m in [
                        'mes', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
                    ]):
                        tipo_comparativa = 'mes'
                    elif 'año' in contexto_lower or 'anio' in contexto_lower:
                        tipo_comparativa = 'año'
                    else:
                        tipo_comparativa = 'semana'

                datos = self._bot.predictor.comparar_periodos(tipo_comparativa)
                if 'error' not in datos:
                    respuesta = self._bot.fmt._formatear_comparativa(datos)
                else:
                    respuesta = f"{datos['error']}"
        
        # ==== VENTAS ====
        elif accion == 'consultar_ventas':
            df = self._bot.odoo.ventas_periodo(fecha_ini, fecha_fin)
            respuesta = self._bot.fmt._formato_ventas(df, fecha_ini, fecha_fin)
            self._bot.ultimo_modelo = 'sale.order'
        
        elif accion == 'ventas_por_tienda':
            # Consulta directa POS → ranking ejecutivo por punto de venta
            try:
                if self._bot.odoo and self._bot.odoo.conectado:
                    datos_pos = self._bot.odoo.buscar(
                        'pos.order',
                        filtro=[('date_order', '>=', fecha_ini), ('date_order', '<=', fecha_fin),
                                ('state', 'in', ['paid', 'done', 'invoiced'])],
                        campos=['config_id', 'amount_total', 'amount_tax'],
                        limite=5000
                    )
                    if datos_pos is not None and not datos_pos.empty:
                        datos_pos['tienda'] = datos_pos['config_id'].apply(
                            lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else str(x))
                        kpis = (datos_pos.groupby('tienda')
                                .agg(Ventas_Total=('amount_total', 'sum'),
                                     Num_Tickets=('amount_total', 'count'),
                                     Ticket_Prom=('amount_total', 'mean'))
                                .sort_values('Ventas_Total', ascending=False))
                        total_general = kpis['Ventas_Total'].sum()
                        n_tiendas = len(kpis)

                        respuesta = f"## Ventas por Punto de Venta\n\n"
                        respuesta += f"> **Período:** {fecha_ini} → {fecha_fin} &nbsp;|&nbsp; **{n_tiendas}** puntos de venta activos\n\n"
                        respuesta += "### Desempeño Comparativo\n\n"
                        respuesta += "| # | Punto de Venta | Ventas Totales | Tickets | Ticket Promedio | % del Total |\n"
                        respuesta += "|---|----------------|---------------|---------|-----------------|----------:|\n"
                        acum_pct = 0.0
                        for i, (tienda, row) in enumerate(kpis.iterrows(), 1):
                            pct = (row['Ventas_Total'] / total_general * 100) if total_general > 0 else 0
                            acum_pct += pct
                            respuesta += (f"| {i} | **{tienda[:32]}** "
                                          f"| **${row['Ventas_Total']:,.2f}** "
                                          f"| {row['Num_Tickets']:,.0f} "
                                          f"| ${row['Ticket_Prom']:,.2f} "
                                          f"| {pct:.1f}% |\n")
                        respuesta += f"\n**Total consolidado: ${total_general:,.2f}**\n\n"

                        # Hallazgos ejecutivos
                        respuesta += "---\n\n**Hallazgos:**\n\n"
                        lider = kpis.index[0]
                        lider_pct = kpis.iloc[0]['Ventas_Total'] / total_general * 100 if total_general > 0 else 0
                        respuesta += f"- **Tienda líder:** {lider} — aporta el **{lider_pct:.0f}%** del ingreso total del canal POS.\n"
                        if n_tiendas >= 2:
                            brecha = kpis.iloc[0]['Ventas_Total'] - kpis.iloc[-1]['Ventas_Total']
                            rezago = kpis.index[-1]
                            respuesta += f"- **Brecha de rendimiento:** {lider} supera a {rezago} en **${brecha:,.2f}**. Analizar causas operativas.\n"
                        mejor_ticket = kpis['Ticket_Prom'].idxmax()
                        peor_ticket = kpis['Ticket_Prom'].idxmin()
                        if mejor_ticket != peor_ticket:
                            respuesta += (f"- **Mayor ticket promedio:** {mejor_ticket} "
                                          f"(${kpis.loc[mejor_ticket, 'Ticket_Prom']:,.2f}). "
                                          f"Indica upselling efectivo o mix de mayor valor.\n")
                        respuesta += "\n"
                        df = kpis.reset_index()
                        df.columns = ['Tienda', 'Ventas Total', 'Nro Tickets', 'Ticket Promedio']
                        return respuesta, df
                # Fallback si no hay datos POS
                datos = self._bot.analizador.analisis_ventas_completo(fecha_ini, fecha_fin)
                respuesta = self._bot.analizador.formatear_analisis_md('ventas', datos)
                if 'por_cliente' in datos:
                    df = pd.DataFrame(datos['por_cliente'])
            except Exception as e:
                datos = self._bot.analizador.analisis_ventas_completo(fecha_ini, fecha_fin)
                respuesta = self._bot.analizador.formatear_analisis_md('ventas', datos)

        elif accion in ('analisis_ventas', 'ventas_completo', 'ventas_por_marca',
                        'ventas_mensuales_marca'):
            datos = self._bot.analizador.analisis_ventas_completo(fecha_ini, fecha_fin)
            respuesta = self._bot.analizador.formatear_analisis_md('ventas', datos)
            if 'por_cliente' in datos:
                df = pd.DataFrame(datos['por_cliente'])
        
        elif accion == 'top_productos':
            datos = self._bot.analizador.top_productos_vendidos(fecha_ini, fecha_fin)
            if 'error' not in datos:
                respuesta = self._bot.fmt._formatear_top_productos(datos, params.get('limite', 10))
                if datos.get('productos'):
                    df = pd.DataFrame(datos['productos'])
            else:
                respuesta = f"{datos.get('error')}"
        
        elif accion == 'top_clientes':
            datos = self._bot.analizador.analisis_ventas_completo(fecha_ini, fecha_fin)
            respuesta = self._bot.fmt._formatear_top_clientes(datos, params.get('limite', 10))
            if 'por_cliente' in datos:
                df = pd.DataFrame(datos['por_cliente'])
        
        elif accion == 'ventas_vendedor':
            datos = self._bot.analizador.analisis_ventas_completo(fecha_ini, fecha_fin)
            respuesta = self._bot.fmt._formatear_ventas_vendedor(datos)
            if 'por_vendedor' in datos:
                df = pd.DataFrame(datos['por_vendedor'])
        
        elif accion == 'ventas_por_empresa':
            consultas_esp = getattr(self._bot, 'consultas_esp', None)
            if consultas_esp:
                try:
                    datos = consultas_esp.ventas_completo(fecha_ini, fecha_fin)
                    if 'error' not in datos:
                        respuesta = self._bot.fmt._formatear_ventas_por_empresa(datos)
                        if datos.get('por_empresa'):
                            df = pd.DataFrame(datos['por_empresa'])
                    else:
                        respuesta = f"Error obteniendo ventas por empresa: {datos['error']}"
                except Exception as e:
                    respuesta = f"Error en ventas por empresa: {str(e)}"
            else:
                respuesta = "Módulo de consultas especializadas no disponible."

        elif accion == 'tendencia':
            respuesta, df = self._generar_tendencia(consulta, mensaje)
        
        # ==== POS ====
        elif accion == 'consultar_pos':
            df = self._bot.odoo.tickets_pos(fecha_ini, fecha_fin)
            respuesta = self._bot.fmt._formato_pos(df, fecha_ini, fecha_fin)
            self._bot.ultimo_modelo = 'pos.order'
        
        elif accion in ('analisis_pos', 'pos_completo'):
            datos = self._bot.analizador.analisis_pos_completo(fecha_ini, fecha_fin)
            respuesta = self._bot.analizador.formatear_analisis_md('pos', datos)
        
        elif accion == 'metodos_pago':
            datos = self._bot.analizador.analisis_metodos_pago_pos(fecha_ini, fecha_fin)
            respuesta = self._bot.fmt._formatear_metodos_pago(datos)
            if 'metodos' in datos:
                df = pd.DataFrame(datos['metodos'])
        
        elif accion == 'sesiones_pos':
            datos = self._bot.analizador.analisis_pos_completo(fecha_ini, fecha_fin)
            respuesta = self._bot.fmt._formatear_sesiones(datos)
        
        elif accion == 'sesiones_abiertas':
            # Obtener sesiones de POS abiertas directamente
            try:
                sesiones = self._bot.odoo.buscar(
                    'pos.session',
                    filtro=[('state', '=', 'opened')],
                    campos=['id', 'name', 'config_id', 'user_id', 'start_at', 'cash_register_balance_start', 'cash_register_balance_end_real'],
                    limite=50
                )
                if sesiones.empty:
                    respuesta = "No hay sesiones de caja abiertas actualmente."
                else:
                    # Limpiar campos many2one
                    sesiones['tienda'] = sesiones['config_id'].apply(
                        lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                    )
                    sesiones['cajero'] = sesiones['user_id'].apply(
                        lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                    )
                    respuesta = f"## Sesiones de Caja Abiertas\n\n**{len(sesiones)}** sesiones actualmente abiertas:\n\n"
                    respuesta += "| Sesión | Tienda | Cajero | Inicio | Saldo Inicial |\n|---|---|---|---|---:|\n"
                    for _, s in sesiones.iterrows():
                        inicio = s.get('start_at', '')[:16] if s.get('start_at') else '-'
                        saldo = s.get('cash_register_balance_start', 0) or 0
                        respuesta += f"| {s['name']} | {s['tienda']} | {s['cajero']} | {inicio} | ${saldo:,.2f} |\n"
                    df = sesiones[['name', 'tienda', 'cajero', 'start_at']]
            except Exception as e:
                respuesta = f"Error al consultar sesiones: {str(e)}"
        
        # ==== FACTURACIÓN ====
        elif accion == 'consultar_facturas':
            datos = self._bot.analizador.analisis_facturacion(fecha_ini, fecha_fin)
            respuesta = self._bot.analizador.formatear_analisis_md('facturacion', datos)
            self._bot.ultimo_modelo = 'account.move'
        
        elif accion == 'analisis_facturacion':
            datos = self._bot.analizador.analisis_facturacion(fecha_ini, fecha_fin)
            respuesta = self._bot.analizador.formatear_analisis_md('facturacion', datos)
        
        elif accion in ('cuentas_por_cobrar', 'cxc_analisis', 'score_morosos'):
            datos = self._bot.analizador.cuentas_por_cobrar()
            if 'error' not in datos:
                respuesta = self._bot.fmt._formatear_cxc_especializado(datos)
            else:
                respuesta = self._bot.analizador.formatear_analisis_md('cxc', datos)
            if 'por_cliente' in datos:
                df = pd.DataFrame(datos['por_cliente'])

        elif accion in ('cuentas_por_pagar', 'cxp_analisis'):
            datos = self._bot.analizador.cuentas_por_pagar()
            if 'error' not in datos:
                respuesta = self._bot.fmt._formatear_cxp_especializado(datos)
            else:
                respuesta = self._bot.analizador.formatear_analisis_md('cxp', datos)
            if 'por_proveedor' in datos:
                df = pd.DataFrame(datos['por_proveedor'])
        
        # ==== INVENTARIO ====
        elif accion == 'consultar_inventario':
            df = self._bot.odoo.stock_disponible()
            respuesta = self._bot.fmt._formato_inventario(df)
            self._bot.ultimo_modelo = 'stock.quant'
        
        elif accion == 'analisis_inventario':
            datos = self._bot.analizador.analisis_inventario()
            respuesta = self._bot.analizador.formatear_analisis_md('inventario', datos)
            if 'por_categoria' in datos:
                df = pd.DataFrame(datos['por_categoria'])
        
        elif accion == 'productos_sin_stock':
            datos = self._bot.analizador.analisis_inventario()
            if 'productos_sin_stock' in datos:
                df = pd.DataFrame(datos['productos_sin_stock'])
                respuesta = f"## Productos Sin Stock\n\n**{datos.get('resumen', {}).get('sin_stock', 0)}** productos agotados."
            else:
                respuesta = "No hay productos sin stock"
        
        elif accion in ('inventario_por_almacen', 'inventario_por_tienda', 'inventario_por_ubicacion', 'stock_lento', 'reposicion_jit'):
            consultas_esp = getattr(self._bot, 'consultas_esp', None)
            if consultas_esp:
                try:
                    datos = consultas_esp.inventario_por_almacen()
                    if 'error' not in datos:
                        respuesta = self._bot.fmt._formatear_inventario_por_almacen(datos)
                        almacenes = datos.get('almacenes', [])
                        if almacenes:
                            df = pd.DataFrame(almacenes)
                    else:
                        respuesta = f"Error obteniendo inventario por almacén: {datos['error']}"
                except Exception as e:
                    respuesta = f"Error en inventario por almacén: {str(e)}"
            else:
                respuesta = "Módulo de consultas especializadas no disponible."

        elif accion == 'productos_criticos':
            consultas_esp = getattr(self._bot, 'consultas_esp', None)
            if consultas_esp:
                try:
                    umbral = params.get('umbral', 5)
                    datos = consultas_esp.productos_criticos(umbral)
                    if 'error' not in datos:
                        resumen = datos.get('resumen', {})
                        # Adaptar al formato de _formatear_productos_criticos
                        agotados = datos.get('productos_agotados', [])
                        bajo_stock = datos.get('productos_bajo_stock', [])
                        productos_fmt = [
                            {
                                'producto': p.get('name', ''),
                                'stock': p.get('qty_available', 0),
                                'venta_diaria': 0,
                                'dias_stock': 0,
                                'estado': 'agotado' if p.get('qty_available', 0) <= 0 else 'bajo_stock'
                            }
                            for p in (agotados[:10] + bajo_stock[:10])
                        ]
                        datos_fmt = {
                            'confianza': datos.get('confianza_datos', 0),
                            'metricas': {
                                'productos_agotados': resumen.get('agotados', 0),
                                'productos_criticos': resumen.get('total', 0),
                                'productos_bajo_stock': resumen.get('bajo_stock', 0),
                            },
                            'productos': productos_fmt,
                        }
                        respuesta = self._bot.fmt._formatear_productos_criticos(datos_fmt)
                        todos_productos = agotados + bajo_stock
                        if todos_productos:
                            df = pd.DataFrame(todos_productos)
                    else:
                        respuesta = f"Error obteniendo productos críticos: {datos['error']}"
                except Exception as e:
                    respuesta = f"Error en productos críticos: {str(e)}"
            else:
                respuesta = "Módulo de consultas especializadas no disponible."

        elif accion in ('rotacion_inventario', 'kpi_rotacion_inventario', 'rotacion_inventario_avanzado'):
            datos = self._bot.analizador.productos_mas_vendidos_vs_stock()
            respuesta = self._bot.fmt._formatear_rotacion_inventario(datos)
            if datos.get('criticos'):
                df = pd.DataFrame(datos['criticos'])
        
        elif accion == 'valoracion_inventario':
            datos = self._bot.analizador.analisis_inventario()
            respuesta = self._bot.fmt._formatear_valoracion(datos)
        
        elif accion == 'productos_costo_cero':
            datos = self._bot.analizador.analisis_inventario()
            productos = datos.get('productos_costo_cero', [])
            total = datos.get('resumen', {}).get('costo_cero', len(productos))
            if productos:
                df = pd.DataFrame(productos)
                respuesta = f"## Productos con Costo Cero\n\n**{total}** productos tienen costo $0.00 configurado.\n\n"
                respuesta += "| Producto | Código | Stock |\n|---|---|---:|\n"
                for p in productos[:15]:
                    respuesta += f"| {p['name'][:40]} | {p.get('default_code', '')} | {p.get('qty_available', 0):.0f} |\n"
                if total > 15:
                    respuesta += f"\n*...y {total - 15} más*"
            else:
                respuesta = "No hay productos con costo cero"
        
        elif accion == 'productos_sin_categoria':
            datos = self._bot.analizador.analisis_inventario()
            productos = datos.get('productos_sin_categoria', [])
            total = datos.get('resumen', {}).get('sin_categoria', len(productos))
            if productos:
                df = pd.DataFrame(productos)
                respuesta = f"## Productos Sin Categoría\n\n**{total}** productos no tienen categoría asignada.\n\n"
                respuesta += "| Producto | Código | Stock |\n|---|---|---:|\n"
                for p in productos[:15]:
                    respuesta += f"| {p['name'][:40]} | {p.get('default_code', '')} | {p.get('qty_available', 0):.0f} |\n"
                if total > 15:
                    respuesta += f"\n*...y {total - 15} más*"
            else:
                respuesta = "Todos los productos tienen categoría asignada"
        
        elif accion == 'kpi_ticket_promedio':
            fecha_ini = params.get('fecha_inicio', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
            fecha_fin = params.get('fecha_fin', datetime.now().strftime('%Y-%m-%d'))
            datos = self._bot.analizador.analisis_ventas_completo(fecha_ini, fecha_fin)
            if 'error' in datos:
                respuesta = f"No se pudieron obtener datos de ventas: {datos['error']}"
            else:
                resumen = datos.get('resumen', {})
                total_ventas = resumen.get('monto_total', 0)
                num_ordenes = resumen.get('total_ordenes', 1)
                ticket_prom = resumen.get('ticket_promedio', total_ventas / num_ordenes if num_ordenes > 0 else 0)
                maximo = resumen.get('maximo', 0)
                minimo = resumen.get('minimo', 0)
                tendencia = datos.get('tendencia', '')
                icono_tendencia = {'alza': '📈', 'baja': '📉', 'estable': '➖'}.get(tendencia, '➖')

                respuesta = (
                    f"## Ticket Promedio\n\n"
                    f"**Período:** {fecha_ini} → {fecha_fin}\n\n"
                    f"| Métrica | Valor |\n"
                    f"|---------|-------|\n"
                    f"| 🎟️ Ticket promedio | **${ticket_prom:,.2f}** |\n"
                    f"| 📦 Órdenes totales | **{num_ordenes:,}** |\n"
                    f"| 💰 Total ventas    | **${total_ventas:,.2f}** |\n"
                    f"| ⬆️ Orden más alta  | ${maximo:,.2f} |\n"
                    f"| ⬇️ Orden más baja  | ${minimo:,.2f} |\n"
                    f"| {icono_tendencia} Tendencia       | {tendencia.capitalize() if tendencia else 'N/A'} |\n\n"
                )

                insights = datos.get('insights', [])
                if insights:
                    respuesta += "### 💡 Insights\n"
                    for insight in insights:
                        respuesta += f"- {insight}\n"

                if datos.get('por_cliente'):
                    df = pd.DataFrame(datos['por_cliente'])

        # ==== ANÁLISIS 360° ====
        elif accion == 'analisis_360':
            analizador_360 = getattr(self._bot, 'analizador_360', None)
            if analizador_360:
                try:
                    from services.analysis.analisis_360 import Formateador360
                    resultado = analizador_360.analizar_entidad(mensaje)
                    if resultado:
                        respuesta = Formateador360.formatear(resultado)
                        productos = resultado.inventario.get('productos', [])
                        if productos:
                            df = pd.DataFrame(productos[:20])
                    else:
                        respuesta = (
                            "Para el **Análisis 360°** necesito que especifiques una entidad. Ejemplos:\n\n"
                            "- _'¿Cómo va Immortale?'_ → Análisis completo de la marca\n"
                            "- _'Todo sobre el producto [nombre]'_\n"
                            "- _'Análisis del cliente [nombre]'_\n"
                            "- _'¿Cómo está [marca/producto/vendedor]?'_"
                        )
                except Exception as e:
                    respuesta = f"Error en análisis 360°: {str(e)}"
            else:
                respuesta = (
                    "El módulo de Análisis 360° no está activo en este momento.\n\n"
                    "Prueba con: _'ventas del mes'_, _'top 10 productos'_, _'análisis de inventario'_"
                )

        # ==== DASHBOARD KPIs EMPRESARIALES ====
        elif accion in ('dashboard_kpis_empresariales', 'kpis_comerciales', 'dashboard_kpis',
                        'kpis_operaciones', 'kpis_tiendas', 'kpis_por_tienda', 'dashboard_automatico',
                        'kpis_compras', 'kpi_faltantes', 'kpi_picking_cedis',
                        'kpi_ventas_por_canal', 'kpi_ventas_por_marca', 'kpis_talento'):
            motor_kpis = getattr(self._bot, 'motor_kpis', None)
            if motor_kpis:
                try:
                    from services.analysis.kpis_empresariales import FormateadorKPIs
                    fi_dt = datetime.strptime(fecha_ini, '%Y-%m-%d') if fecha_ini else None
                    ff_dt = datetime.strptime(fecha_fin, '%Y-%m-%d') if fecha_fin else None
                    if accion == 'kpis_comerciales':
                        from services.analysis.kpis_empresariales import CategoriaKPI
                        resultados = motor_kpis.ejecutar_categoria(CategoriaKPI.COMERCIAL, fi_dt, ff_dt)
                        respuesta = FormateadorKPIs.formatear_categoria(CategoriaKPI.COMERCIAL, resultados)
                    else:
                        dashboard = motor_kpis.generar_dashboard_completo(fi_dt, ff_dt)
                        respuesta = FormateadorKPIs.formatear_dashboard(dashboard, "Dashboard KPIs Empresariales")
                except Exception as e:
                    respuesta = f"Error generando KPIs: {str(e)}"
            else:
                respuesta = (
                    "El módulo de KPIs Empresariales no está activo.\n\n"
                    "Prueba con: _'ventas del mes'_, _'ticket promedio'_, _'top productos'_"
                )

        # ==== AUDITORÍA CALIDAD DATOS ====
        elif accion in ('auditoria_calidad_datos', 'generar_reporte_auditoria', 'auditoria_nocturna'):
            auditoria_calidad = getattr(self._bot, 'auditoria_calidad', None)
            if auditoria_calidad:
                try:
                    resultado = auditoria_calidad.ejecutar_auditoria_completa()
                    respuesta = auditoria_calidad.formatear_resultado_markdown(resultado)
                    hallazgos = resultado.hallazgos or []
                    if hallazgos:
                        df = pd.DataFrame([{
                            'Modelo': h.modelo_odoo,
                            'Categoria': h.categoria,
                            'Severidad': h.severidad,
                            'Descripcion': str(h.descripcion)[:80]
                        } for h in hallazgos[:50]])
                except Exception as e:
                    respuesta = f"Error ejecutando auditoría de calidad: {str(e)}"
            else:
                respuesta = (
                    "El módulo de Auditoría de Calidad de Datos no está activo.\n\n"
                    "Prueba con: _'dame las anomalías'_, _'reporte de ventas'_"
                )

        # ==== DETECCIÓN DE ANOMALÍAS Y FRAUDE ====
        elif accion in ('detectar_anomalias', 'auditoria_fraude', 'analisis_riesgos',
                        'diferencias_centavos', 'detectar_pagos_fantasma'):
            analizador_anomalias = getattr(self._bot, 'analizador_anomalias', None)
            if analizador_anomalias:
                try:
                    resultado = analizador_anomalias.ejecutar_auditoria_completa()
                    respuesta = analizador_anomalias.formatear_auditoria_markdown(resultado)
                    hallazgos = resultado.hallazgos or []
                    if hallazgos:
                        df = pd.DataFrame([{
                            'Tipo': h.tipo_riesgo.value if hasattr(h.tipo_riesgo, 'value') else str(h.tipo_riesgo),
                            'Severidad': h.severidad.value if hasattr(h.severidad, 'value') else str(h.severidad),
                            'Descripcion': str(h.descripcion)[:80],
                            'Accion': str(h.recomendacion)[:60]
                        } for h in hallazgos[:50]])
                except Exception as e:
                    respuesta = f"Error en detección de anomalías: {str(e)}"
            else:
                respuesta = (
                    "El módulo de detección de anomalías no está activo.\n\n"
                    "Prueba con: _'auditoría de datos'_, _'dame los KPIs'_"
                )

        # ==== PREDICCIÓN ML / LSTM ====
        elif accion in ('prediccion_ml', 'anomalias_ml', 'tendencias_ml'):
            motor_ml = getattr(self._bot, 'motor_ml', None)
            if motor_ml:
                try:
                    if accion == 'prediccion_ml':
                        from services.prediction.motor_ml import FormateadorML
                        pred = motor_ml.predecir_ventas_ml()
                        respuesta = FormateadorML.formatear_prediccion(pred)
                        if pred.prediccion_diaria:
                            df = pd.DataFrame(pred.prediccion_diaria)
                    elif accion == 'anomalias_ml':
                        from services.prediction.motor_ml import FormateadorML
                        datos = motor_ml.detectar_anomalias_ventas()
                        respuesta = FormateadorML.formatear_anomalias(datos)
                        if datos.get('anomalias'):
                            df = pd.DataFrame(datos['anomalias'])
                    elif accion == 'tendencias_ml':
                        from services.prediction.motor_ml import FormateadorML
                        datos = motor_ml.detectar_tendencias_ml() if hasattr(motor_ml, 'detectar_tendencias_ml') else {}
                        if datos:
                            respuesta = FormateadorML.formatear_tendencias(datos)
                        else:
                            pred = motor_ml.predecir_ventas_ml()
                            respuesta = FormateadorML.formatear_prediccion(pred)
                except Exception as e:
                    respuesta = f"Error en análisis ML: {str(e)}"
            else:
                respuesta = "El módulo de Machine Learning no está activo. Prueba con _'predecir ventas'_."

        elif accion == 'prediccion_lstm':
            motor_lstm = getattr(self._bot, 'motor_lstm', None)
            if motor_lstm:
                try:
                    from services.prediction.neural_lstm import FormateadorLSTM
                    pred = motor_lstm.predecir_ventas_lstm()
                    respuesta = FormateadorLSTM.formatear_prediccion(pred)
                    if pred.prediccion_semanal:
                        df = pd.DataFrame(pred.prediccion_semanal)
                except Exception as e:
                    respuesta = f"Error en predicción LSTM: {str(e)}"
            else:
                respuesta = "El motor LSTM no está activo. Prueba con _'predecir ventas'_."

        elif accion in ('segmentacion_clientes', 'analizar_churn'):
            motor_ml = getattr(self._bot, 'motor_ml', None)
            auditoria = getattr(self._bot, 'auditoria', None)
            if accion == 'analizar_churn' and auditoria:
                try:
                    churns = auditoria.analizar_churn_clientes()
                    if churns:
                        respuesta = f"## Análisis de Churn de Clientes\n\n**{len(churns)}** clientes en riesgo de abandono.\n\n"
                        respuesta += "| Cliente | Score Riesgo | Último Pedido | Predicción |\n|---|---:|---|---|\n"
                        for c in churns[:20]:
                            score = getattr(c, 'score_riesgo', 0)
                            dias = getattr(c, 'dias_sin_compra', 0)
                            cliente = getattr(c, 'nombre_cliente', 'N/A')
                            pred_str = getattr(c, 'prediccion', 'N/A')
                            respuesta += f"| {cliente[:30]} | {score:.0f}% | hace {dias} días | {pred_str} |\n"
                        df = pd.DataFrame([{
                            'Cliente': getattr(c, 'nombre_cliente', ''),
                            'Score': getattr(c, 'score_riesgo', 0),
                            'Dias sin compra': getattr(c, 'dias_sin_compra', 0)
                        } for c in churns])
                    else:
                        respuesta = "No se detectaron clientes en riesgo de churn."
                except Exception as e:
                    respuesta = f"Error en análisis de churn: {str(e)}"
            elif motor_ml:
                try:
                    from services.prediction.motor_ml import FormateadorML
                    seg = motor_ml.segmentar_clientes()
                    respuesta = FormateadorML.formatear_segmentacion(seg)
                    if seg.segmentos:
                        rows = []
                        for seg_item in seg.segmentos:
                            rows.append({'Segmento': seg_item.nombre, 'Clientes': seg_item.num_clientes,
                                         'Valor medio': seg_item.valor_medio})
                        df = pd.DataFrame(rows)
                except Exception as e:
                    respuesta = f"Error en segmentación de clientes: {str(e)}"
            else:
                respuesta = "El módulo de ML no está activo. Prueba con _'top clientes'_, _'ventas por cliente'_."

        # ==== REPORTES BI ====
        elif accion in ('reporte_bi', 'reporte_ejecutivo', 'analisis_inteligente'):
            motor_bi = getattr(self._bot, 'motor_bi', None)
            if motor_bi:
                try:
                    reporte = motor_bi.generar_reporte_completo()
                    respuesta = motor_bi.formatear_reporte_markdown(reporte)
                    anomalias = reporte.anomalias if hasattr(reporte, 'anomalias') else []
                    if anomalias:
                        df = pd.DataFrame([{
                            'Tipo': a.tipo if hasattr(a, 'tipo') else str(a),
                            'Descripcion': a.descripcion if hasattr(a, 'descripcion') else str(a)
                        } for a in anomalias[:30]])
                except Exception as e:
                    # Caer a análisis ventas como alternativa
                    try:
                        datos = self._bot.analizador.analisis_ventas_completo(fecha_ini, fecha_fin)
                        respuesta = self._bot.analizador.formatear_analisis_md('ventas', datos)
                    except Exception:
                        respuesta = f"Error generando reporte BI: {str(e)}"
            else:
                datos = self._bot.analizador.analisis_ventas_completo(fecha_ini, fecha_fin)
                respuesta = self._bot.analizador.formatear_analisis_md('ventas', datos)

        # ==== CRM / CLIENTES ====
        elif accion in ('analisis_crm', 'clientes_analisis', 'clientes_olvidados'):
            try:
                if self._bot.odoo and self._bot.odoo.conectado:
                    if accion == 'clientes_olvidados':
                        # Clientes sin compras en los últimos 90 días
                        fecha_corte = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                        datos_raw = self._bot.odoo.buscar(
                            'res.partner',
                            filtro=[('customer_rank', '>', 0), ('active', '=', True)],
                            campos=['name', 'email', 'phone', 'last_activity_time'],
                            limite=200
                        )
                        if datos_raw is not None and not datos_raw.empty:
                            respuesta = f"## Clientes Inactivos (sin actividad reciente)\n\n**{len(datos_raw)}** clientes encontrados."
                            df = datos_raw
                        else:
                            respuesta = "No se encontraron datos de clientes."
                    else:
                        # Análisis CRM general
                        datos = self._bot.odoo.buscar(
                            'crm.lead',
                            filtro=[('active', '=', True)],
                            campos=['name', 'partner_id', 'stage_id', 'expected_revenue', 'probability', 'user_id'],
                            limite=200,
                            orden='expected_revenue desc'
                        )
                        if datos is not None and not datos.empty:
                            total_revenue = datos['expected_revenue'].sum() if 'expected_revenue' in datos.columns else 0
                            n = len(datos)
                            respuesta = f"## Análisis CRM\n\n**{n}** oportunidades activas | Ingreso esperado total: **${total_revenue:,.2f}**\n\n"
                            respuesta += "Ver tabla adjunta para detalle de oportunidades."
                            df = datos
                        else:
                            respuesta = "No hay oportunidades CRM activas en el sistema."
                else:
                    respuesta = "No hay conexión con Odoo para consultar datos CRM."
            except Exception as e:
                respuesta = f"Error en análisis CRM: {str(e)}"

        # ==== ANÁLISIS COMPRAS ====
        elif accion in ('analisis_compras', 'consultar_compras'):
            try:
                if self._bot.odoo and self._bot.odoo.conectado:
                    datos = self._bot.odoo.buscar(
                        'purchase.order',
                        filtro=[('date_order', '>=', fecha_ini), ('date_order', '<=', fecha_fin),
                                ('state', 'in', ['purchase', 'done'])],
                        campos=['name', 'partner_id', 'amount_total', 'date_order', 'state'],
                        limite=200,
                        orden='amount_total desc'
                    )
                    if datos is not None and not datos.empty:
                        total = datos['amount_total'].sum() if 'amount_total' in datos.columns else 0
                        n = len(datos)
                        respuesta = f"## Análisis de Compras\n\n**{n}** órdenes | Total: **${total:,.2f}**\n\n"
                        respuesta += f"**Período:** {fecha_ini} → {fecha_fin}\n\n"
                        respuesta += "Ver tabla adjunta para detalle de órdenes de compra."
                        df = datos
                    else:
                        respuesta = f"No hay órdenes de compra en el período {fecha_ini} - {fecha_fin}."
                else:
                    respuesta = "No hay conexión con Odoo."
            except Exception as e:
                respuesta = f"Error en análisis de compras: {str(e)}"

        # ==== CONSULTAS HR ====
        elif accion in ('consultar_empleados', 'departamentos', 'ausencias', 'asistencia',
                        'nomina', 'contratos', 'empresas_resumen', 'consultar_usuarios'):
            try:
                if self._bot.odoo and self._bot.odoo.conectado:
                    _cfg = {
                        'consultar_empleados': ('hr.employee',
                            [('active', '=', True)],
                            ['name', 'department_id', 'job_id', 'work_email', 'coach_id'], 200),
                        'departamentos': ('hr.department',
                            [('active', '=', True)],
                            ['name', 'manager_id', 'parent_id'], 100),
                        'ausencias': ('hr.leave.allocation',
                            [('state', '=', 'validate')],
                            ['employee_id', 'holiday_status_id', 'number_of_days', 'date_from'], 200),
                        'asistencia': ('hr.attendance',
                            [('check_in', '>=', fecha_ini)],
                            ['employee_id', 'check_in', 'check_out', 'worked_hours'], 200),
                        'nomina': ('hr.payslip',
                            [('date_from', '>=', fecha_ini), ('state', 'in', ['done', 'paid'])],
                            ['employee_id', 'name', 'date_from', 'date_to', 'net_wage'], 200),
                        'contratos': ('hr.contract',
                            [('state', 'in', ['open', 'pending'])],
                            ['name', 'employee_id', 'job_id', 'wage', 'date_start', 'state'], 200),
                        'empresas_resumen': ('res.company',
                            [],
                            ['name', 'partner_id', 'currency_id', 'phone', 'email', 'country_id'], 50),
                        'consultar_usuarios': ('res.users',
                            [('active', '=', True), ('share', '=', False)],
                            ['name', 'login', 'groups_id'], 100),
                    }
                    modelo, filtro, campos, limite = _cfg[accion]
                    datos = self._bot.odoo.buscar(modelo, filtro, campos, limite=limite)
                    nombre_accion = accion.replace('_', ' ').title()
                    if datos is not None and not datos.empty:
                        respuesta = f"## {nombre_accion}\n\n**{len(datos)}** registros encontrados.\n\nVer tabla adjunta."
                        df = datos
                    else:
                        respuesta = f"No se encontraron datos de **{nombre_accion}** en el sistema."
                else:
                    respuesta = "No hay conexión con Odoo."
            except Exception as e:
                respuesta = f"Error consultando {accion.replace('_', ' ')}: {str(e)}"

        # ==== TOP PROVEEDORES ====
        elif accion == 'top_proveedores':
            try:
                if self._bot.odoo and self._bot.odoo.conectado:
                    datos = self._bot.odoo.buscar(
                        'purchase.order',
                        filtro=[('date_order', '>=', fecha_ini), ('date_order', '<=', fecha_fin),
                                ('state', 'in', ['purchase', 'done'])],
                        campos=['partner_id', 'amount_total'],
                        limite=500,
                        orden='amount_total desc'
                    )
                    if datos is not None and not datos.empty:
                        datos['proveedor'] = datos['partner_id'].apply(
                            lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        top = (datos.groupby('proveedor')['amount_total']
                               .sum().sort_values(ascending=False).head(params.get('limite', 10)))
                        respuesta = f"## Top {len(top)} Proveedores\n\n"
                        respuesta += "| # | Proveedor | Total Compras |\n|---|---|---:|\n"
                        for i, (prov, total) in enumerate(top.items(), 1):
                            respuesta += f"| {i} | {str(prov)[:35]} | **${total:,.2f}** |\n"
                        df = top.reset_index().rename(columns={'proveedor': 'Proveedor', 'amount_total': 'Total'})
                    else:
                        respuesta = f"No hay datos de compras en el período."
                else:
                    respuesta = "No hay conexión con Odoo."
            except Exception as e:
                respuesta = f"Error en top proveedores: {str(e)}"

        # ==== GENERAR REPORTES ====
        elif accion in ('generar_excel', 'generar_pdf', 'generar_pdf_profesional'):
            respuesta = (
                "Para generar un reporte, especifica qué datos quieres exportar:\n\n"
                "- _'exportar ventas del mes a Excel'_\n"
                "- _'generar PDF de inventario'_\n"
                "- _'reporte de top 10 productos'_\n\n"
                "Una vez que obtengas los datos con una consulta, el botón de exportar aparecer á en la tabla."
            )

        # ==== DIAGNÓSTICO ====
        elif accion == 'diagnosticar_error':
            respuesta = self._info_conexion()

        else:
            # Router inteligente V2: consulta Odoo directamente vía mapeador.
            # Si hay datos reales → los muestra; si no → respuesta honesta.
            # Esto activa todos los ~53 handlers V2 sin elif explícito.
            resp_v2, df_v2 = self._ejecutar_consulta_avanzada_v2(
                accion, consulta, fecha_ini or '', fecha_fin or '', params, mensaje
            )
            if resp_v2:
                respuesta = resp_v2
                if df_v2 is not None:
                    df = df_v2
            else:
                respuesta = self._respuesta_consulta_general(mensaje)

        return respuesta, df

    def _respuesta_consulta_general(self, mensaje: str = '') -> str:
        """Respuesta profesional orientativa con detección de contexto."""
        msg_lower = (mensaje or '').lower()

        # Detección de contexto para respuesta más relevante
        if any(k in msg_lower for k in ['venta', 'vendido', 'sell', 'ingreso', 'revenue']):
            return (
                "Para consultar ventas puedo ayudarte con:\n\n"
                "- **Ventas del período**: _'ventas de este mes'_, _'ventas de enero'_\n"
                "- **Top productos**: _'top 10 productos más vendidos'_\n"
                "- **Por cliente**: _'ventas por cliente'_, _'top 10 clientes'_\n"
                "- **Comparativa**: _'comparar ventas este mes vs mes pasado'_\n"
                "- **Predicción**: _'predecir ventas próximos 30 días'_\n\n"
                "¿Qué período o dimensión te interesa analizar?"
            )
        if any(k in msg_lower for k in ['inventario', 'stock', 'producto', 'almacén', 'bodega']):
            return (
                "Para análisis de inventario puedo consultarte:\n\n"
                "- **Stock actual**: _'stock disponible por producto'_, _'productos sin stock'_\n"
                "- **Movimientos**: _'kardex de [producto]'_, _'entradas y salidas'_\n"
                "- **Rotación**: _'rotación de inventario'_, _'stock lento o muerto'_\n"
                "- **Alertas**: _'qué productos se van a agotar'_, _'reposición justo a tiempo'_\n\n"
                "¿Qué producto o categoría específica te interesa?"
            )
        if any(k in msg_lower for k in ['factura', 'cobr', 'pagar', 'deuda', 'pago', 'cuenta']):
            return (
                "Para gestión financiera puedo ayudarte con:\n\n"
                "- **Cuentas por cobrar**: _'facturas pendientes de cobro'_, _'clientes morosos'_\n"
                "- **Cuentas por pagar**: _'facturas a proveedores pendientes'_\n"
                "- **Flujo de caja**: _'flujo de caja de los últimos 30 días'_\n"
                "- **Anomalías**: _'detectar pagos duplicados'_, _'diferencias en facturas'_\n\n"
                "¿Quieres ver un análisis específico de cuentas por cobrar o pagar?"
            )
        if any(k in msg_lower for k in ['cliente', 'crm', 'lead', 'oportunidad', 'contacto']):
            return (
                "Para análisis de clientes y CRM:\n\n"
                "- **Ranking**: _'top 10 mejores clientes'_, _'clientes más activos'_\n"
                "- **Riesgo**: _'análisis de churn'_, _'clientes que dejaron de comprar'_\n"
                "- **CRM**: _'análisis del CRM'_, _'oportunidades abiertas'_\n"
                "- **Segmentación**: _'clientes por región'_, _'ticket promedio por cliente'_\n\n"
                "¿Te interesa algún cliente o segmento en particular?"
            )
        if any(k in msg_lower for k in ['manual', 'cómo', 'como', 'proceso', 'procedi', 'paso']):
            return (
                "Para guías y procedimientos de Odoo:\n\n"
                "- **Facturación**: _'cómo crear una factura'_, _'cómo cancelar una factura'_\n"
                "- **Ventas**: _'cómo crear una orden de venta'_, _'proceso de confirmación'_\n"
                "- **Inventario**: _'cómo registrar entrada de mercancía'_, _'ajuste de inventario'_\n"
                "- **POS**: _'cómo hacer cierre de caja'_, _'cómo aplicar descuento en POS'_\n\n"
                "Describe el proceso que necesitas y buscaré en el manual."
            )
        if any(k in msg_lower for k in ['predic', 'forecast', 'próximo', 'proximo', 'futuro', 'tendencia']):
            return (
                "Para predicciones y análisis predictivo:\n\n"
                "- **Ventas futuras**: _'predecir ventas próximos 30 días'_\n"
                "- **Agotamiento**: _'qué productos se agotarán pronto'_\n"
                "- **Flujo de caja**: _'predecir flujo de caja'_\n"
                "- **Tendencias**: _'analizar tendencia de ventas'_, _'estacionalidad'_\n\n"
                "¿Qué horizonte de tiempo o módulo te interesa predecir?"
            )

        # Respuesta genérica profesional si no se detectó contexto
        return (
            "Soy **ANDROMEDA**, tu asistente de análisis empresarial para Odoo.\n\n"
            "Puedo ayudarte con:\n\n"
            "| Área | Ejemplos de consulta |\n"
            "|------|---------------------|\n"
            "| 📊 **Ventas** | _'ventas del mes'_, _'top productos'_, _'comparar periodos'_ |\n"
            "| 🏪 **Inventario** | _'stock disponible'_, _'productos sin stock'_, _'rotación'_ |\n"
            "| 💰 **Finanzas** | _'facturas pendientes'_, _'cuentas por cobrar'_, _'flujo de caja'_ |\n"
            "| 👥 **Clientes** | _'top clientes'_, _'análisis CRM'_, _'riesgo de churn'_ |\n"
            "| 🔮 **Predicciones** | _'predecir ventas 60 días'_, _'agotamiento de stock'_ |\n"
            "| 📖 **Manual Odoo** | _'cómo crear una factura'_, _'proceso de cierre de caja'_ |\n"
            "| 🔍 **Auditoría** | _'detectar anomalías'_, _'pagos duplicados'_, _'dashboard KPIs'_ |\n\n"
            "Describe tu consulta con el área y período que te interesa."
        )

    def _generar_tendencia(self, consulta=None, mensaje: str = '') -> Tuple[str, pd.DataFrame]:
        """Genera análisis de tendencia de ventas con desglose inteligente según contexto."""
        mensaje_lower = (mensaje or '').lower()
        contexto_lower = (getattr(consulta, 'contexto', '') or '').lower()
        texto_busqueda = f"{mensaje_lower} {contexto_lower}"

        # Detectar si el usuario pide desglose por marca
        pide_marca = any(kw in texto_busqueda for kw in ['por marca', 'marca', 'marcas', 'brand'])

        # === Sección 1: Tendencia general de ventas (14 días) ===
        historico = []
        for i in range(13, -1, -1):
            fecha = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            try:
                v = self._bot.odoo.ventas_periodo(fecha, fecha)
                total = v['amount_total'].sum() if not v.empty else 0
            except Exception:
                total = 0
            historico.append({'Fecha': fecha, 'Total': total})

        df = pd.DataFrame(historico)
        total_14 = sum(h['Total'] for h in historico)
        promedio = total_14 / 14 if total_14 > 0 else 0

        # Calcular tendencia simple (primera mitad vs segunda mitad)
        mitad = len(historico) // 2
        total_primera = sum(h['Total'] for h in historico[:mitad])
        total_segunda = sum(h['Total'] for h in historico[mitad:])
        if total_primera > 0:
            variacion = ((total_segunda - total_primera) / total_primera) * 100
        else:
            variacion = 0

        if variacion > 10:
            tendencia_txt = "📈 **ALZA**"
        elif variacion < -10:
            tendencia_txt = "📉 **BAJA**"
        else:
            tendencia_txt = "➖ **ESTABLE**"

        md = "## Tendencia de Ventas (14 días)\n\n"
        md += f"| Métrica | Valor |\n|---------|-------|\n"
        md += f"| Tendencia | {tendencia_txt} ({variacion:+.1f}%) |\n"
        md += f"| Total 14 días | **${total_14:,.2f}** |\n"
        md += f"| Promedio diario | **${promedio:,.2f}** |\n\n"

        # Tabla diaria
        md += "| Fecha | Total |\n|-------|------:|\n"
        for h in historico:
            md += f"| {h['Fecha']} | ${h['Total']:,.2f} |\n"

        # === Sección 2: Desglose por marca (si se solicitó) ===
        if pide_marca and self._bot.motor_kpis:
            try:
                resultado_marca = self._bot.motor_kpis.kpi_ventas_por_marca()
                if resultado_marca and resultado_marca.datos is not None and not resultado_marca.datos.empty:
                    df_marcas = resultado_marca.datos
                    md += "\n---\n\n## Ventas por Marca (POS últimos 30 días)\n\n"
                    md += "| # | Marca | Ventas | Unidades | % |\n"
                    md += "|---|-------|-------:|--------:|---:|\n"
                    for i, (_, row) in enumerate(df_marcas.iterrows(), 1):
                        md += (f"| {i} | {row.get('Marca', '')} "
                            f"| ${row.get('Ventas', 0):,.2f} "
                            f"| {row.get('Unidades', 0):,.0f} "
                            f"| {row.get('Porcentaje', 0):.1f}% |\n")
                    # Usar df_marcas como DataFrame principal para la tabla interactiva
                    df = df_marcas
                else:
                    md += "\n> ℹ️ No se encontraron datos de marcas para el período actual.\n"
            except Exception as e:
                md += f"\n> ⚠️ No se pudo obtener desglose por marca: {str(e)[:80]}\n"

        return md, df
    

    def _generar_kpis_por_tienda(self, fecha_ini: str, fecha_fin: str) -> str:
        """Genera KPIs desglosados por tienda/sucursal."""
        try:
            # Obtener datos de POS por tienda
            pos_data = self._bot.odoo.buscar(
                'pos.order',
                filtro=[
                    ('date_order', '>=', fecha_ini),
                    ('date_order', '<=', fecha_fin),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ],
                campos=['id', 'name', 'amount_total', 'session_id', 'config_id', 'date_order', 'partner_id'],
                limite=5000
            )

            if pos_data.empty:
                return "No hay datos de punto de venta en el período seleccionado."

            # Extraer nombre de tienda del config_id
            pos_data['tienda'] = pos_data['config_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'Sin Tienda'
            )

            # Agrupar por tienda
            kpis_tienda = pos_data.groupby('tienda').agg({
                'amount_total': ['sum', 'mean', 'count'],
                'id': 'count'
            }).reset_index()
            kpis_tienda.columns = ['Tienda', 'Ventas_Total', 'Ticket_Promedio', 'Transacciones', 'Ordenes']
            kpis_tienda = kpis_tienda.sort_values('Ventas_Total', ascending=False)

            total_general = kpis_tienda['Ventas_Total'].sum()

            # Construir tabla markdown
            header = (
                f"## KPIs por Tienda/Sucursal\n\n"
                f"### Período: {fecha_ini} a {fecha_fin}\n\n"
                f"| # | Tienda | Total Ventas | Ticket Promedio | Transacciones | % Participación |\n"
                f"|---|--------|-------------|-----------------|---------------|-----------------|\n"
            )
            rows = ""
            for i, row in enumerate(kpis_tienda.itertuples(), 1):
                pct = (row.Ventas_Total / total_general * 100) if total_general > 0 else 0
                rows += (
                    f"| {i} | {row.Tienda} "
                    f"| ${row.Ventas_Total:,.2f} "
                    f"| ${row.Ticket_Promedio:,.2f} "
                    f"| {row.Transacciones:,.0f} "
                    f"| {pct:.1f}% |\n"
                )

            footer = (
                f"\n| **Total** | **{len(kpis_tienda)} tiendas** "
                f"| **${total_general:,.2f}** | | | |\n\n"
            )

            # Insights
            mejor = kpis_tienda.iloc[0] if len(kpis_tienda) > 0 else None
            insights = ""
            if mejor is not None:
                insights = (
                    f"### 💡 Insights\n"
                    f"- **Mejor tienda:** {mejor['Tienda']} "
                    f"(${mejor['Ventas_Total']:,.2f})\n"
                    f"- **Total tiendas activas:** {len(kpis_tienda)}\n"
                )

            return header + rows + footer + insights

        except Exception as e:
            return f"Error al generar KPIs por tienda: {str(e)}"

    def _consultar_facturas_filtradas(self, consulta, fecha_ini: str, fecha_fin: str) -> tuple:
        """Consulta facturas con filtros avanzados (estado, tienda, cliente)."""
        try:
            filtros = [
                ('invoice_date', '>=', fecha_ini),
                ('invoice_date', '<=', fecha_fin),
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ]

            # Extraer filtros de las entidades del cerebro
            estado_factura = None
            tienda_filtro = None

            for ent in self._bot._obtener_entidades_cerebro(consulta):
                if hasattr(ent, 'tipo'):
                    if ent.tipo == 'estado_factura':
                        estado_factura = ent.valor
                    elif ent.tipo == 'tienda':
                        tienda_filtro = ent.valor

            # También buscar en parámetros
            if consulta.parametros:
                estado_factura = estado_factura or consulta.parametros.get('estado')
                tienda_filtro = tienda_filtro or consulta.parametros.get('tienda')

            # Aplicar filtro de estado
            if estado_factura == 'pendiente':
                filtros.append(('amount_residual', '>', 0))
                filtros.append(('payment_state', 'in', ['not_paid', 'partial']))
            elif estado_factura == 'pagada':
                filtros.append(('payment_state', '=', 'paid'))

            # Obtener facturas con campo de journal (diario contable que indica tienda)
            facturas = self._bot.odoo.buscar(
                'account.move',
                filtro=filtros,
                campos=['id', 'name', 'partner_id', 'invoice_date', 'amount_total',
                        'amount_residual', 'payment_state', 'state', 'invoice_user_id', 'journal_id'],
                limite=500
            )

            if facturas.empty:
                return "No se encontraron facturas con los filtros especificados.", None

            # Limpiar campos many2one
            facturas['Cliente'] = facturas['partner_id'].apply(
                lambda x: x[1][:35] if isinstance(x, (list, tuple)) and len(x) > 1 else 'Sin Cliente'
            )

            # Extraer nombre del diario (tienda)
            facturas['Diario'] = facturas['journal_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else ''
            )

            # Extraer nombre del vendedor
            facturas['Vendedor'] = facturas['invoice_user_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else ''
            )

            # Filtrar por tienda si se especificó
            if tienda_filtro:
                tienda_normalizada = tienda_filtro.lower().strip()

                variantes_tienda = [tienda_normalizada]
                if tienda_normalizada == 'moral':
                    variantes_tienda.extend(['la moral', 'moral', 'pos moral', 'pdv moral', 'tienda moral', 'premium.*moral'])
                elif tienda_normalizada == 'aeropuerto':
                    variantes_tienda.extend(['aero', 'pos aeropuerto', 'pdv aeropuerto', 'premium.*aero'])
                elif tienda_normalizada == 'centro':
                    variantes_tienda.extend(['centro', 'pos centro', 'pdv centro', 'tienda centro', 'premium.*centro'])

                pattern = '|'.join(variantes_tienda)
                mask = (
                    facturas['Diario'].str.lower().str.contains(pattern, na=False, regex=True) |
                    facturas['Cliente'].str.lower().str.contains(pattern, na=False, regex=True) |
                    facturas['Vendedor'].str.lower().str.contains(pattern, na=False, regex=True)
                )
                facturas_filtradas = facturas[mask]

                if facturas_filtradas.empty:
                    diarios_unicos = facturas['Diario'].unique().tolist()
                    diarios_str = ", ".join([d for d in diarios_unicos if d])[:200]

                    msg = f"No se encontraron facturas para la tienda '{tienda_filtro}'.\n\n"
                    msg += f"**Diarios disponibles:** {diarios_str}\n\n"
                    msg += f"**Nota:** Las facturas de cliente no suelen tener información de tienda/sucursal. "
                    msg += f"Para ver ventas por tienda, usa mejor: \"**ventas de {tienda_filtro}**\" o \"**pos de {tienda_filtro}**\""
                    return msg, None

                facturas = facturas_filtradas

            # Calcular totales
            total_facturas = len(facturas)
            monto_total = facturas['amount_total'].sum()
            saldo_pendiente = facturas['amount_residual'].sum()

            titulo_estado = ""
            if estado_factura == 'pendiente':
                titulo_estado = " Pendientes de Pago"
            elif estado_factura == 'pagada':
                titulo_estado = " Pagadas"

            titulo_tienda = f" - {tienda_filtro}" if tienda_filtro else ""

            md = (
                f"## Facturas{titulo_estado}{titulo_tienda}\n\n"
                f"**Período:** {fecha_ini} a {fecha_fin}\n"
                f"**Total facturas:** {total_facturas}\n"
                f"**Monto total:** ${monto_total:,.2f}\n"
                f"**Saldo pendiente:** ${saldo_pendiente:,.2f}\n\n"
            )

            # Crear DataFrame limpio para la tabla
            df_display = facturas[['name', 'Cliente', 'invoice_date', 'amount_total', 'amount_residual', 'payment_state']].copy()
            df_display.columns = ['Factura', 'Cliente', 'Fecha', 'Monto', 'Saldo', 'Estado Pago']

            return md, df_display

        except Exception as e:
            return f"Error al consultar facturas: {str(e)}", None

    def _generar_reporte(self, formato: str) -> str:
        if self._bot.ultimo_df is None or self._bot.ultimo_df.empty:
            return "No hay datos. Primero consulta algo."

        archivo = self._bot.reportes.generar_reporte(
            {self._bot.ultimo_modelo or 'Datos': self._bot.ultimo_df},
            "Reporte",
            formato
        )
        return f"## Reporte Generado\n\n**{formato.upper()}**: `{archivo}`"

    def _generar_pdf_profesional(self, contexto: str = "") -> str:
        """Genera un PDF profesional con ReportLab."""
        if not self._bot.generador_pdf_reportlab:
            return "El generador de PDFs profesionales no está disponible. Instala reportlab."

        try:
            from services.reports import SeccionReporte, ConfiguracionReporte

            secciones = []

            # Si hay datos en el último DataFrame, incluirlos
            if self._bot.ultimo_df is not None and not self._bot.ultimo_df.empty:
                datos_tabla = self._bot.ultimo_df.head(50).values.tolist()
                encabezados = list(self._bot.ultimo_df.columns)

                secciones.append(SeccionReporte(
                    titulo="Datos Analizados",
                    contenido=datos_tabla,
                    tipo='tabla',
                    metadata={'encabezados': encabezados}
                ))

            # Si hay auditoría disponible, generar resumen
            if self._bot.auditoria and hasattr(self._bot.auditoria, 'ejecutar_auditoria_express'):
                try:
                    resultado_auditoria = self._bot.auditoria.ejecutar_auditoria_express()
                    if resultado_auditoria and 'metricas' in resultado_auditoria:
                        secciones.append(SeccionReporte(
                            titulo="Resumen de Auditoría",
                            contenido=resultado_auditoria.get('metricas', {}),
                            tipo='resumen_ejecutivo'
                        ))
                except Exception:
                    pass

            if not secciones:
                return "No hay datos para generar el PDF. Primero realiza una consulta o análisis."

            # Generar el PDF
            config = ConfiguracionReporte(
                titulo="Reporte Ejecutivo ANDROMEDA",
                subtitulo=contexto[:100] if contexto else "Análisis de Datos Empresariales",
                empresa=os.getenv("ODOO_EMPRESA", "Mi Empresa")
            )

            exito, ruta = self._bot.generador_pdf_reportlab.generar_reporte(secciones, config=config)

            if exito:
                return (
                    f"## PDF Profesional Generado\n\n"
                    f"**Archivo:** `{ruta}`\n\n"
                    f"El reporte incluye {len(secciones)} sección(es) con datos actualizados."
                )
            else:
                return "Error al generar el PDF. Verifica que reportlab esté instalado correctamente."

        except Exception as e:
            return f"Error generando PDF: {str(e)}"

    def _ejecutar_consulta_dinamica(self, pregunta: str, parametros: dict = None) -> tuple:
        """Ejecuta una consulta dinámica generada por el LLM."""
        if not self._bot.generador_queries:
            return "El generador de queries no está disponible.", None

        try:
            # Si hay parámetros específicos del LLM, usar directamente
            if parametros and 'modelo' in parametros and 'dominio' in parametros:
                from services.llm.generador_queries import QueryOdoo
                query = QueryOdoo(
                    modelo=parametros['modelo'],
                    dominio=parametros.get('dominio', []),
                    campos=parametros.get('campos', ['name', 'id']),
                    limite=parametros.get('limite', 50),
                    orden=parametros.get('orden'),
                    descripcion=pregunta
                )
                resultado = self._bot.generador_queries.ejecutar_query(query)
            else:
                resultado = self._bot.generador_queries.procesar_pregunta(pregunta)

            if not resultado.exito:
                return f"Error en consulta: {resultado.error}", None

            if not resultado.datos:
                return "No se encontraron datos para esta consulta.", None

            # Crear DataFrame con los resultados
            df = pd.DataFrame(resultado.datos)
            self._bot.ultimo_df = df

            # Interpretar resultados con el LLM si está disponible
            interpretacion = self._bot.generador_queries.interpretar_resultados(resultado, pregunta)

            respuesta = (
                f"## Consulta Dinámica\n\n"
                f"**Pregunta:** {pregunta}\n"
                f"**Registros encontrados:** {len(df)}\n\n"
            )
            if interpretacion:
                respuesta += f"**Análisis:** {interpretacion}\n"

            return respuesta, df

        except Exception as e:
            return f"Error en consulta dinámica: {str(e)}", None

    def _contar_chiste(self) -> str:
        """Cuenta un chiste relacionado con datos y negocios."""
        import random
        chistes = [
            "## ¡Un chiste para ti!\n\n¿Por qué el contador siempre lleva una calculadora? ¡Por si las facturas no cuadran! 📊😄",
            "## ¡Un chiste para ti!\n\n¿Qué le dijo Excel a la base de datos? 'Tú sí que tienes buenos registros' 💻😂",
            "## ¡Un chiste para ti!\n\n¿Por qué los datos en Odoo nunca se pierden? ¡Porque tienen buenos respaldos! 🔄😜",
            "## ¡Un chiste para ti!\n\n¿Qué le dice un ERP a otro? '¿Módulos este fin de semana?' 🤓",
            "## ¡Un chiste para ti!\n\nMi función favorita es SUM... porque siempre suma al equipo 📈",
            "## ¡Un chiste para ti!\n\n¿Por qué el inventario fue al psicólogo? Tenía problemas de stock emocional 📦😅",
            "## ¡Un chiste para ti!\n\nUn cliente entra en la tienda y pregunta: '¿Tienen facturas?' El sistema responde: '¿Las quiere timbradas o sin timbrar?' 🧾",
            "## ¡Un chiste para ti!\n\n¿Cuál es el colmo de un analista de datos? Tener una vida sin gráficas 📊",
            "## ¡Un chiste para ti!\n\n¿Por qué el dashboard estaba triste? Porque nadie lo consultaba 📉😢",
            "## ¡Un chiste para ti!\n\n¿Qué hace un KPI cuando se siente solo? Se compara con el mes anterior 📈"
        ]
        return random.choice(chistes) + "\n\n💡 **¿En qué más puedo ayudarte?** Pregúntame sobre ventas, inventario, clientes..."

    def _mostrar_capacidades(self) -> str:
        """Muestra un resumen de las capacidades del sistema."""
        return (
            "## 🌌 Soy ANDROMEDA - Tu Asistente de Inteligencia de Negocios\n\n"
            "**Consultas de datos:**\n"
            "- 📊 Ventas, facturación, ingresos\n"
            "- 📦 Inventario y stock\n"
            "- 👥 Clientes y proveedores\n"
            "- 🏪 Punto de Venta (POS)\n\n"
            "**Análisis avanzado:**\n"
            "- 📈 Tendencias y predicciones\n"
            "- 🎯 KPIs empresariales\n"
            "- 🔍 Detección de anomalías\n"
            "- 💡 Insights automáticos\n\n"
            "**Reportes:**\n"
            "- 📄 PDF profesionales\n"
            "- 📊 Gráficas interactivas\n"
            "- 📋 Excel y CSV\n\n"
            "**Pregúntame lo que necesites en lenguaje natural.**"
        )

    def _responder_despedida(self) -> str:
        """Responde a una despedida con calidez."""
        import random
        despedidas = [
            "## 👋 ¡Hasta luego campeón!\n\nFue un placer analizar datos contigo. Cuando vuelvas, aquí estaré. ¡Éxito en todo! 🌟💪",
            "## 👋 ¡Nos vemos!\n\nGracias por confiar en ANDROMEDA. Que tus negocios vayan al 100%. Cualquier consulta, aquí ando. 🚀",
            "## 👋 ¡Hasta pronto!\n\nFue genial ayudarte. Recuerda: cuando necesites analizar, predecir o entender tus datos, cuento conmigo. 😊📊",
            "## 👋 ¡Chao!\n\n¡Acabas de ver el poder del análisis inteligente! Vuelve pronto para descubrir más insights. Nos vemos, campeón. 🔥✨"
        ]
        return random.choice(despedidas)

    def _responder_agradecimiento(self) -> str:
        """Responde a un agradecimiento con empatía y humor."""
        import random
        respuestas = [
            "## 🙌 ¡Para ti!\n\n¡Ese es mi trabajo, hacer que los datos hablen! 📊 ¿Hay algo más que quieras saber sobre tu negocio?",
            "## 😊 ¡Con todo el gusto!\n\nPara eso estoy aquí, para darte insights que de verdad importen. ¿Otra pregunta? 💡",
            "## ✨ ¡Claro que sí!\n\nSi hay algo que me encanta es desbloquear el potencial de tus datos. ¿Qué más te atormenta analizando? 😄📈",
            "## 🌟 ¡Para servirte!\n\nEstoy aquí para hacer tu vida más fácil. ¿Seguimos descubriendo cosas increíbles sobre tu negocio? 🚀"
        ]
        return random.choice(respuestas)

    def _responder_saludo(self) -> str:
        """Responde a un saludo con empatía y calidez."""
        import random
        from datetime import datetime

        hora = datetime.now().hour
        if hora < 12:
            momento = "Buenos días"
        elif hora < 19:
            momento = "Buenas tardes"
        else:
            momento = "Buenas noches"

        respuestas = [
            f"## 👋 ¡{momento}!\n\n¡Qué onda! Aquí estoy para ayudarte con todo lo que necesites sobre tu negocio. 😊\n\n💡 **Puedo ayudarte con:**\n- 📊 Análisis de ventas y tendencias\n- 🎯 Predicciones y pronósticos\n- 📈 KPIs y métricas clave\n- 🔍 Anomalías y oportunidades\n\n**¿Qué necesitas ahora?**",
            f"## 🌟 ¡Hola!\n\n¡Me encanta verte por aquí! 😄 Soy ANDROMEDA, tu compañero de análisis de negocios.\n\nEsto es lo que puedo hacer por ti:\n- 💰 Consultas sobre ventas, ingresos y rentabilidad\n- 📦 Información de inventario y stock\n- 👥 Análisis de clientes y comportamientos\n- 🎲 Predicciones inteligentes basadas en datos\n\n**¿Por dónde empezamos?**",
            f"## 🚀 ¡{momento}!\n\n¡Bienvenido! Aquí estoy para hacer tus análisis mucho más fáciles y útiles. 💪\n\nSin complicaciones, solo preguntas naturales como:\n- \"¿Cómo vamos con las ventas?\"\n- \"Top 10 productos esta semana\"\n- \"¿Hay clientes en riesgo?\"\n- \"Grafica mi inventario por categoría\"\n\n**¿Con qué te ayudo?**",
            f"## 😊 ¡{momento}!\n\n¡Qué bueno que estés aquí! Aquí va mi magia de análisis para tu negocio.\n\nPuedo hacer de todo:\n✅ Reportes instantáneos\n✅ Gráficas espectaculares\n✅ Predicciones inteligentes\n✅ Alertas de problemas\n✅ 10+ idiomas disponibles\n\n**¿Qué consultamos primero?**"
        ]
        return random.choice(respuestas)

    def _ventas_tienda_especifica(self, tienda: str, fecha_ini: str, fecha_fin: str) -> str:
        """Consulta ventas de una tienda/unidad operativa específica."""
        try:
            # Buscar el warehouse/operating unit que coincida
            warehouses = self._bot.odoo.search_read('stock.warehouse',
                [('name', 'ilike', tienda)],
                campos=['id', 'name', 'code']
            )

            if not warehouses:
                try:
                    ous = self._bot.odoo.search_read('operating.unit',
                        [('name', 'ilike', tienda)],
                        campos=['id', 'name', 'code']
                    )
                    if ous:
                        warehouses = ous
                except Exception:
                    pass

            if not warehouses:
                return (
                    f"## Tienda no encontrada\n\n"
                    f"No se encontró una tienda con el nombre **{tienda}**.\n\n"
                    f"Intenta con el nombre exacto o usa **\"ventas por tienda\"** para ver todas."
                )

            # Obtener ventas de POS para la tienda
            pos_data = self._bot.odoo.buscar(
                'pos.order',
                filtro=[
                    ('date_order', '>=', fecha_ini),
                    ('date_order', '<=', fecha_fin),
                    ('state', 'in', ['paid', 'done', 'invoiced']),
                    ('config_id.name', 'ilike', tienda)
                ],
                campos=['id', 'name', 'amount_total', 'date_order', 'partner_id'],
                limite=1000
            )

            if pos_data.empty:
                return f"No se encontraron ventas para **{tienda}** en el período {fecha_ini} a {fecha_fin}."

            total = pos_data['amount_total'].sum()
            ticket_prom = pos_data['amount_total'].mean()
            n_ventas = len(pos_data)

            return (
                f"## Ventas de {tienda}\n\n"
                f"**Período:** {fecha_ini} a {fecha_fin}\n"
                f"**Total ventas:** ${total:,.2f}\n"
                f"**Ticket promedio:** ${ticket_prom:,.2f}\n"
                f"**Transacciones:** {n_ventas:,}\n"
            )

        except Exception as e:
            return f"Error al consultar ventas de {tienda}: {str(e)}"

    def _generar_ayuda_completa(self) -> str:
        return (
            "## 🌌 ANDROMEDA - Capacidades\n\n"
            "**Consultas:**\n"
            "- Ventas, facturas, inventario, clientes, productos\n"
            "- KPIs por tienda, marca, vendedor\n"
            "- Estados de cuenta y cobranza\n\n"
            "**Análisis:**\n"
            "- Tendencias y predicciones\n"
            "- Detección de anomalías\n"
            "- Análisis 360° de negocio\n\n"
            "**Reportes:**\n"
            "- PDF profesionales\n"
            "- Gráficas y dashboards\n"
            "- Excel y CSV\n\n"
            "**Solo pregunta en lenguaje natural.**"
        )

    def _info_conexion(self) -> str:
        url = getattr(self._bot, 'odoo_url', 'N/D')
        db = getattr(self._bot, 'odoo_db', 'N/D')
        user = getattr(self._bot, 'odoo_user', 'N/D')
        conectado = "Sí ✅" if getattr(self._bot, 'conector', None) else "No ❌"
        return (
            f"## 🔗 Información del Sistema\n\n"
            f"**URL Odoo:** {url}\n"
            f"**Base de datos:** {db}\n"
            f"**Usuario:** {user}\n"
            f"**Conectado:** {conectado}\n"
        )

    def _ejecutar_consulta_avanzada_v2(self, accion: str, consulta, fecha_ini: str, fecha_fin: str, params: dict, mensaje: str):
        """
        Router inteligente para acciones v2. Estrategia escalonada:
        1. Intentar resolver con consulta directa a Odoo (datos reales)
        2. Si hay LLM, enriquecer la respuesta con análisis contextual
        3. Si no hay datos, dar respuesta honesta (nunca inventar)
        """
        import pandas as pd

        df = None
        respuesta = ""

        try:
            # ---- Mapeo de acciones a consultas Odoo ----
            consultas_directas = self._bot._mapear_accion_a_consulta_odoo(accion, fecha_ini, fecha_fin, params, consulta)

            if consultas_directas:
                modelo = consultas_directas.get('modelo', '')
                filtro = consultas_directas.get('filtro', [])
                campos = consultas_directas.get('campos', [])
                limite = consultas_directas.get('limite', 80)
                orden = consultas_directas.get('orden', '')

                if modelo and self._bot.odoo:
                    try:
                        datos = self._bot.odoo.buscar(modelo, filtro, campos, limite=limite, orden=orden)
                        if datos is not None and not datos.empty:
                            df = datos
                    except Exception:
                        pass  # Sin datos, se intentará con LLM

            # ---- Construir respuesta ----
            accion_legible = accion.replace('_', ' ').title()

            # Nombres legibles para columnas Odoo
            _nombres_cols = {
                'amount_total': 'Monto Total', 'amount_untaxed': 'Subtotal',
                'amount_tax': 'Impuestos', 'amount_residual': 'Saldo Pendiente',
                'price_subtotal': 'Subtotal', 'price_unit': 'Precio Unitario',
                'product_uom_qty': 'Cantidad', 'qty_available': 'Stock Disponible',
                'qty_on_hand': 'Stock en Mano', 'virtual_available': 'Stock Virtual',
                'quantity': 'Cantidad', 'standard_price': 'Costo',
                'lst_price': 'Precio de Venta', 'wage': 'Salario',
                'debit': 'Débito', 'credit': 'Crédito', 'balance': 'Balance',
            }
            # Columnas monetarias (para prefijo $)
            _cols_monetarias = {
                'amount_total', 'amount_untaxed', 'amount_tax', 'amount_residual',
                'price_subtotal', 'price_unit', 'price_total', 'standard_price',
                'lst_price', 'wage', 'debit', 'credit', 'balance', 'total',
                'subtotal', 'amount', 'monto', 'cost', 'margin',
            }

            if df is not None and not df.empty:
                n_registros = len(df)
                fecha_str = f"{fecha_ini} → {fecha_fin}" if fecha_ini and fecha_fin else "período actual"

                # ── 1. Limpiar campos many2one [id, 'Nombre'] → 'Nombre' ──────────────
                df = df.copy()
                for col in df.columns:
                    try:
                        sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                        if isinstance(sample, (list, tuple)) and len(sample) == 2:
                            df[col] = df[col].apply(
                                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else (str(x) if x else ''))
                    except Exception:
                        pass

                # ── 2. Excluir columnas técnicas irrelevantes para el análisis ────────
                _cols_excluir = {'id', 'write_uid', 'create_uid', 'message_follower_ids',
                                 'activity_ids', 'message_ids', 'currency_id'}
                df_bi = df[[c for c in df.columns
                            if c not in _cols_excluir
                            and not c.endswith('_uid')
                            and c != 'id']].copy()

                # ── 3. Identificar columna monetaria principal ────────────────────────
                _prioridad_monto = ['amount_total', 'amount_untaxed', 'price_subtotal',
                                    'price_total', 'lst_price', 'standard_price',
                                    'wage', 'debit', 'balance', 'amount_residual']
                col_monto = next((c for c in _prioridad_monto if c in df_bi.columns), None)
                if not col_monto:
                    cols_num_all = df_bi.select_dtypes(include='number').columns.tolist()
                    col_monto = next((c for c in cols_num_all
                                     if any(k in c.lower() for k in
                                            ('amount', 'price', 'total', 'cost', 'wage',
                                             'balance', 'revenue', 'subtotal'))), None)
                    if not col_monto and cols_num_all:
                        col_monto = cols_num_all[0]

                # ── 4. Identificar columna de entidad (quién / qué) ──────────────────
                _prioridad_cat = ['partner_id', 'product_id', 'user_id', 'config_id',
                                  'team_id', 'categ_id', 'warehouse_id', 'location_id',
                                  'journal_id', 'department_id', 'name']
                col_cat = next((c for c in _prioridad_cat if c in df_bi.columns), None)
                if not col_cat:
                    col_cat = next((c for c in df_bi.columns
                                    if df_bi[c].dtype == object
                                    and df_bi[c].nunique() > 1
                                    and c not in ('state', 'move_type', 'payment_state')), None)

                nombre_monto = _nombres_cols.get(col_monto, col_monto.replace('_', ' ').title()) if col_monto else 'Valor'
                nombre_cat = _nombres_cols.get(col_cat, col_cat.replace('_', ' ').title()) if col_cat else 'Entidad'

                # ── 5. Calcular KPIs ejecutivos ──────────────────────────────────────
                monto_total = df_bi[col_monto].sum() if col_monto else 0
                monto_prom = df_bi[col_monto].mean() if col_monto else 0
                monto_max = df_bi[col_monto].max() if col_monto else 0
                es_moneda = col_monto and (col_monto in _cols_monetarias
                                           or any(k in (col_monto or '').lower()
                                                  for k in ('amount', 'price', 'total',
                                                            'cost', 'wage', 'balance')))

                # ── 6. Header ejecutivo ──────────────────────────────────────────────
                respuesta = f"## {accion_legible}\n\n"
                respuesta += f"> **Período:** {fecha_str} &nbsp;|&nbsp; **{n_registros:,}** registros analizados\n\n"

                # ── 7. KPIs resumen (tablero ejecutivo) ──────────────────────────────
                respuesta += "### Resumen Ejecutivo\n\n"
                respuesta += "| KPI | Valor | Indicador |\n|-----|-------|----------|\n"
                if col_monto:
                    fmt_total = f"**${monto_total:,.2f}**" if es_moneda else f"**{monto_total:,.0f}**"
                    fmt_prom  = f"${monto_prom:,.2f}" if es_moneda else f"{monto_prom:,.1f}"
                    fmt_max   = f"${monto_max:,.2f}" if es_moneda else f"{monto_max:,.0f}"
                    respuesta += f"| {nombre_monto} Total | {fmt_total} | ← cifra clave |\n"
                    respuesta += f"| Promedio por Transacción | {fmt_prom} | — |\n"
                    respuesta += f"| Transacción / Registro Máximo | {fmt_max} | — |\n"
                respuesta += f"| Registros en Período | **{n_registros:,}** | — |\n\n"

                # ── 8. Ranking Top 10 por entidad ────────────────────────────────────
                if col_cat and col_monto and n_registros > 1:
                    top_n = min(10, n_registros)
                    try:
                        ranking = (df_bi[[col_cat, col_monto]]
                                   .groupby(col_cat, as_index=False)[col_monto].sum()
                                   .sort_values(col_monto, ascending=False)
                                   .head(top_n))
                        ranking.columns = [nombre_cat, nombre_monto]
                        acum = ranking[nombre_monto].sum()
                        pct_vs_total = (acum / monto_total * 100) if monto_total > 0 else 100

                        respuesta += f"### Top {top_n} — {nombre_cat} por {nombre_monto}\n\n"
                        respuesta += f"| # | {nombre_cat} | {nombre_monto} | % Participación |\n"
                        respuesta += f"|---|{'---'*3}|{'---'*2}|----------------|\n"
                        acum_pct = 0.0
                        for i, (_, row) in enumerate(ranking.iterrows(), 1):
                            ent = str(row[nombre_cat])[:38] if row[nombre_cat] else 'N/A'
                            val = row[nombre_monto]
                            pct = (val / monto_total * 100) if monto_total > 0 else 0
                            acum_pct += pct
                            fmt_val = f"**${val:,.2f}**" if es_moneda else f"**{val:,.0f}**"
                            respuesta += f"| {i} | {ent} | {fmt_val} | {pct:.1f}% |\n"
                        respuesta += f"\n"

                        # ── 9. Hallazgos automáticos ─────────────────────────────────
                        top3_val = ranking.head(3)[nombre_monto].sum()
                        pct_top3 = (top3_val / monto_total * 100) if monto_total > 0 else 0
                        respuesta += "---\n\n**Hallazgos clave:**\n\n"
                        respuesta += f"- El top 3 concentra el **{pct_top3:.0f}%** del {nombre_monto.lower()} total ({f'${top3_val:,.2f}' if es_moneda else f'{top3_val:,.0f}'}).\n"
                        if pct_top3 > 70:
                            respuesta += f"- **Alerta de concentración:** dependencia crítica en pocos registros. Se recomienda diversificación.\n"
                        elif pct_top3 > 50:
                            respuesta += f"- Concentración moderada. Evaluar estrategias para ampliar la base.\n"
                        else:
                            respuesta += f"- Distribución equilibrada: {n_registros} entidades activas en el período.\n"

                        # Brecha líder - último
                        if len(ranking) >= 2:
                            lider_val = ranking.iloc[0][nombre_monto]
                            ultimo_val = ranking.iloc[-1][nombre_monto]
                            lider_nom = str(ranking.iloc[0][nombre_cat])[:30]
                            brecha = lider_val - ultimo_val
                            if es_moneda and brecha > 0:
                                respuesta += f"- **Brecha de desempeño:** {lider_nom} supera al último en **${brecha:,.2f}**.\n"
                        respuesta += "\n"
                    except Exception:
                        pass

                elif col_monto and n_registros >= 2:
                    # Sin columna categórica — detectar tendencia por fecha si existe
                    cols_fecha = [c for c in df_bi.columns
                                  if any(k in c for k in ('date', 'Date', 'invoice_date',
                                                           'date_order', 'check_in', 'start_at'))]
                    if cols_fecha:
                        try:
                            col_f = cols_fecha[0]
                            df_bi[col_f] = pd.to_datetime(df_bi[col_f], errors='coerce')
                            tend = df_bi.groupby(df_bi[col_f].dt.to_period('M'))[col_monto].sum()
                            if len(tend) >= 2:
                                ult = tend.iloc[-1]
                                pen = tend.iloc[-2]
                                variacion = ((ult - pen) / pen * 100) if pen > 0 else 0
                                signo = "▲" if variacion >= 0 else "▼"
                                label = "crecimiento" if variacion >= 0 else "contracción"
                                respuesta += f"**Variación mensual:** {signo} **{abs(variacion):.1f}%** ({label} vs período anterior). "
                                if abs(variacion) > 20:
                                    respuesta += f"Variación significativa. Validar causa raíz.\n\n"
                                else:
                                    respuesta += f"Evolución dentro de rango normal.\n\n"
                        except Exception:
                            pass

                # ── 10. Enriquecer con LLM (prompt nivel Junta Directiva) ────────────
                if hasattr(self._bot, 'cerebro_llm') and self._bot.cerebro_llm:
                    try:
                        contexto_datos = df_bi.head(20).to_string(index=False)
                        contexto_memoria = ""
                        if hasattr(self._bot, 'memoria_jerarquica') and self._bot.memoria_jerarquica:
                            mem_vec = getattr(self._bot.memoria_jerarquica, 'memoria_vectorial', None)
                            if mem_vec and hasattr(mem_vec, 'obtener_contexto_para_llm'):
                                try:
                                    contexto_memoria = mem_vec.obtener_contexto_para_llm(mensaje, max_recuerdos=2)
                                except Exception:
                                    pass
                            try:
                                contexto_grafo = self._bot.memoria_jerarquica.obtener_contexto_grafo(accion)
                                if contexto_grafo:
                                    contexto_memoria = (contexto_memoria + "\n\n" + contexto_grafo).strip()
                            except Exception:
                                pass

                        especificaciones = _construir_especificaciones_usuario(params, consulta)

                        prompt_llm = (
                            f"Eres el Chief Data Officer presentando ante la Junta Directiva y el CEO. "
                            f"Analiza el reporte de '{accion_legible}' (período: {fecha_str}).\n\n"
                            f"DATOS VERIFICADOS del sistema ({n_registros} registros, muestra representativa):\n"
                            f"{contexto_datos}\n\n"
                        )
                        if contexto_memoria:
                            prompt_llm += f"Contexto histórico / análisis previos:\n{contexto_memoria}\n\n"
                        if especificaciones:
                            prompt_llm += f"Filtros aplicados por el usuario:\n{especificaciones}\n\n"
                        prompt_llm += (
                            f"Pregunta del usuario: {mensaje}\n\n"
                            f"INSTRUCCIONES — respuesta para Junta Directiva:\n"
                            f"1. Abre con UNA oración ejecutiva que resuma el estado del indicador\n"
                            f"2. Lista máx. 3 hallazgos concretos usando los números del dataset\n"
                            f"3. Señala 1 riesgo o punto de atención si lo hay en los datos\n"
                            f"4. Cierra con 1-2 acciones recomendadas, específicas y medibles\n"
                            f"5. Tono: profesional, directo. Sin tecnicismos de base de datos.\n"
                            f"6. NUNCA inventes cifras — usa solo los datos proporcionados.\n"
                            f"7. Máximo 200 palabras."
                        )
                        resp_llm = self._bot.cerebro_llm.generar(prompt_llm)
                        if resp_llm and hasattr(resp_llm, 'contenido') and resp_llm.contenido:
                            respuesta += f"### Análisis Ejecutivo\n\n{resp_llm.contenido}\n"
                    except Exception:
                        pass  # LLM no disponible — la tabla cuantitativa es suficiente

            else:
                # Sin datos directos: intentar con LLM contextual sobre Odoo
                if hasattr(self._bot, 'cerebro_llm') and self._bot.cerebro_llm:
                    try:
                        prompt_llm = (
                            f"El usuario pregunta sobre '{accion_legible}' en el sistema Odoo. "
                            f"Mensaje original: {mensaje}\n"
                            f"Período: {fecha_ini} a {fecha_fin}\n\n"
                            f"No tenemos datos tabularizados disponibles para esta consulta específica. "
                            f"Explica qué información se necesitaría del sistema para responder esta consulta, "
                            f"y sugiere consultas alternativas que el usuario puede hacer. "
                            f"NUNCA inventes datos ni cifras."
                        )
                        resp_llm = self._bot.cerebro_llm.generar(prompt_llm)
                        if resp_llm and hasattr(resp_llm, 'contenido') and resp_llm.contenido:
                            respuesta = resp_llm.contenido
                        else:
                            respuesta = self._respuesta_accion_no_disponible(accion_legible)
                    except Exception:
                        respuesta = self._respuesta_accion_no_disponible(accion_legible)
                else:
                    respuesta = self._respuesta_accion_no_disponible(accion_legible)

        except Exception as e:
            respuesta = f"⚠️ Error al ejecutar **{accion.replace('_', ' ')}**: {str(e)}\n\nIntenta reformular tu consulta."

        return respuesta, df


    def _respuesta_accion_no_disponible(self, accion_legible: str) -> str:
        """Respuesta contextual cuando no hay datos, con sugerencias específicas por dominio."""
        accion_lower = accion_legible.lower()

        # Sugerencias específicas por dominio
        sugerencias = {
            'vent': [
                '"ventas del mes"', '"cuánto vendimos hoy"',
                '"top 10 productos vendidos"', '"ventas por vendedor"'
            ],
            'inventari': [
                '"estado del inventario"', '"productos sin stock"',
                '"rotación de inventario"', '"inventario por almacén"'
            ],
            'factur': [
                '"facturas pendientes"', '"cuentas por cobrar"',
                '"facturas del mes"', '"antigüedad de cartera"'
            ],
            'client': [
                '"top 10 clientes"', '"clientes nuevos del mes"',
                '"análisis de clientes"'
            ],
            'compr': [
                '"compras del mes"', '"top proveedores"',
                '"órdenes de compra pendientes"'
            ],
            'pos': [
                '"ventas del punto de venta"', '"tickets de hoy"',
                '"métodos de pago"'
            ],
        }

        ejemplos = None
        for clave, lista in sugerencias.items():
            if clave in accion_lower:
                ejemplos = lista
                break

        if not ejemplos:
            ejemplos = ['"ventas del mes"', '"estado del inventario"', '"facturas pendientes"', '"qué puedes hacer"']

        ejemplos_md = "\n".join(f"  - {e}" for e in ejemplos[:4])

        return (
            f"## ℹ️ {accion_legible}\n\n"
            f"No encontré datos para esta consulta en el período solicitado.\n\n"
            f"**¿Qué puedes hacer?**\n"
            f"- Prueba con un período más amplio (ej: _\"ventas del año\"_)\n"
            f"- Verifica que los módulos necesarios estén instalados en Odoo\n\n"
            f"**Consultas que sí puedo responder:**\n"
            f"{ejemplos_md}"
        )


# ============================================================
# FUNCIONES AUXILIARES DEL MÓDULO
# ============================================================

def _construir_especificaciones_usuario(params: dict, consulta) -> str:
    """
    Construye un bloque de texto con las especificaciones que el usuario
    indicó explícitamente, para incluirlo en el prompt del LLM.

    Esto garantiza que el LLM sepa exactamente qué filtros/formato/agrupación
    el usuario solicitó y los refleje en su respuesta.
    """
    if not params:
        return ""

    lineas = []

    # Filtros de dominio
    if params.get('tienda'):
        lineas.append(f"- Filtrar SOLO la tienda/sucursal: {params['tienda']}")
    if params.get('cliente'):
        lineas.append(f"- Filtrar SOLO el cliente: {params['cliente']}")
    if params.get('vendedor'):
        lineas.append(f"- Filtrar SOLO el vendedor/ejecutivo: {params['vendedor']}")
    if params.get('producto'):
        lineas.append(f"- Filtrar SOLO el producto: {params['producto']}")
    if params.get('proveedor'):
        lineas.append(f"- Filtrar SOLO el proveedor: {params['proveedor']}")

    # Agrupación
    groupby = params.get('groupby')
    if groupby:
        if isinstance(groupby, list):
            lineas.append(f"- Agrupar resultados por: {', '.join(groupby)}")
        else:
            lineas.append(f"- Agrupar resultados por: {groupby}")

    # Límite / ranking
    limite = params.get('limite')
    if isinstance(limite, int):
        lineas.append(f"- Mostrar exactamente los top {limite} resultados")

    # Rangos numéricos
    if params.get('mayor_que') is not None:
        lineas.append(f"- Solo registros con monto mayor a: ${params['mayor_que']:,.2f}")
    if params.get('menor_que') is not None:
        lineas.append(f"- Solo registros con monto menor a: ${params['menor_que']:,.2f}")

    # Formato de salida
    fmt = params.get('formato') or getattr(consulta, 'formato_solicitado', 'auto')
    if fmt and fmt != 'auto':
        _fmt_labels = {
            'tabla': 'tabla Markdown',
            'grafica': 'gráfica (Plotly)',
            'lista': 'lista de puntos',
            'resumen': 'resumen ejecutivo',
            'excel': 'tabla exportable a Excel',
            'pdf': 'reporte en PDF',
        }
        lineas.append(f"- Formato de salida preferido: {_fmt_labels.get(fmt, fmt)}")

    # Dirección de orden
    if params.get('orden_dir') == 'asc':
        lineas.append("- Ordenar de menor a mayor")
    elif params.get('orden_dir') == 'desc':
        lineas.append("- Ordenar de mayor a menor")

    return "\n".join(lineas)

