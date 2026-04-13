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
        
        # ==== PREDICCIONES ====
        if accion == 'predecir_ventas':
            # Extraer días desde entidades o parámetros - default 180 días
            dias = params.get('limite', 180)
            
            # Buscar horizonte en entidades del cerebro (prioridad: periodo_prediccion > horizonte > params)
            encontrado = False
            entidades_cerebro = self._bot._obtener_entidades_cerebro(consulta)
            
            for ent in entidades_cerebro:
                if hasattr(ent, 'tipo'):
                    if ent.tipo == 'periodo_prediccion' and isinstance(ent.valor, dict):
                        # Usar los días calculados desde el período futuro
                        dias = ent.valor.get('dias', 180)
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
            if pred.datos_historicos:
                df = pd.DataFrame(pred.datos_historicos[-30:])
        
        elif accion == 'predecir_agotamiento':
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
        
        elif accion == 'salud_negocio':
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
        
        elif accion == 'comparar_periodos':
            # Detectar tipo de comparación desde contexto o entidades
            contexto_lower = consulta.contexto.lower()
            tipo_comparativa = None
            
            # Buscar primero en entidades del cerebro (más preciso)
            for ent in self._bot._obtener_entidades_cerebro(consulta):
                if hasattr(ent, 'tipo') and ent.tipo == 'tipo_comparativa':
                    tipo_comparativa = ent.valor
                    break
            
            # Si no se encontró en entidades, buscar en texto
            if not tipo_comparativa:
                if 'ayer' in contexto_lower or 'hoy vs ayer' in contexto_lower:
                    tipo_comparativa = 'dia'
                elif 'mes' in contexto_lower:
                    tipo_comparativa = 'mes'
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
        
        elif accion == 'analisis_ventas':
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
        
        elif accion == 'tendencia':
            respuesta, df = self._generar_tendencia(consulta, mensaje)
        
        # ==== POS ====
        elif accion == 'consultar_pos':
            df = self._bot.odoo.tickets_pos(fecha_ini, fecha_fin)
            respuesta = self._bot.fmt._formato_pos(df, fecha_ini, fecha_fin)
            self._bot.ultimo_modelo = 'pos.order'
        
        elif accion == 'analisis_pos':
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
        
        elif accion == 'cuentas_por_cobrar':
            datos = self._bot.analizador.cuentas_por_cobrar()
            respuesta = self._bot.analizador.formatear_analisis_md('cxc', datos)
            if 'por_cliente' in datos:
                df = pd.DataFrame(datos['por_cliente'])
        
        elif accion == 'cuentas_por_pagar':
            datos = self._bot.analizador.cuentas_por_pagar()
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
        
        elif accion == 'rotacion_inventario':
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

                respuesta = f"## 📊 {accion_legible}\n"
                respuesta += f"**Período:** {fecha_ini} → {fecha_fin} &nbsp;|&nbsp; "
                respuesta += f"**Registros:** {n_registros:,}\n\n"

                # Estadísticas inteligentes por columna numérica
                cols_num = df.select_dtypes(include=['number']).columns.tolist()
                if cols_num:
                    respuesta += "### Resumen\n"
                    respuesta += "| Métrica | Total | Promedio | Máx | Mín |\n"
                    respuesta += "|---------|-------|----------|-----|-----|\n"
                    for col in cols_num[:5]:
                        nombre = _nombres_cols.get(col, col.replace('_', ' ').title())
                        total = df[col].sum()
                        promedio = df[col].mean()
                        maximo = df[col].max()
                        minimo = df[col].min()
                        es_moneda = col.lower() in _cols_monetarias or any(p in col.lower() for p in ('amount', 'price', 'total', 'cost', 'wage'))
                        if es_moneda:
                            respuesta += f"| {nombre} | **${total:,.2f}** | ${promedio:,.2f} | ${maximo:,.2f} | ${minimo:,.2f} |\n"
                        else:
                            respuesta += f"| {nombre} | **{total:,.0f}** | {promedio:,.1f} | {maximo:,.0f} | {minimo:,.0f} |\n"
                    respuesta += "\n"

                    # Insight automático: detectar concentración en top registros
                    col_principal = cols_num[0]
                    if n_registros >= 5:
                        total_general = df[col_principal].sum()
                        if total_general > 0:
                            top_5 = df.nlargest(min(5, n_registros), col_principal)[col_principal].sum()
                            pct_top = (top_5 / total_general) * 100
                            if pct_top > 50:
                                es_mon = col_principal.lower() in _cols_monetarias or 'amount' in col_principal.lower() or 'price' in col_principal.lower()
                                fmt = f"${top_5:,.2f}" if es_mon else f"{top_5:,.0f}"
                                respuesta += f"💡 **Insight:** Los top 5 registros concentran el **{pct_top:.0f}%** del total ({fmt})\n\n"

                # Enriquecer con LLM si está disponible
                if hasattr(self._bot, 'cerebro_llm') and self._bot.cerebro_llm:
                    try:
                        contexto_datos = df.head(15).to_string(index=False)
                        # Obtener contexto de memoria si está disponible
                        contexto_memoria = ""
                        if hasattr(self._bot, 'memoria_jerarquica') and self._bot.memoria_jerarquica:
                            mem_vec = getattr(self._bot.memoria_jerarquica, 'memoria_vectorial', None)
                            if mem_vec and hasattr(mem_vec, 'obtener_contexto_para_llm'):
                                try:
                                    contexto_memoria = mem_vec.obtener_contexto_para_llm(mensaje, max_recuerdos=2)
                                except Exception:
                                    pass
                            # Contexto relacional del grafo
                            try:
                                contexto_grafo = self._bot.memoria_jerarquica.obtener_contexto_grafo(accion)
                                if contexto_grafo:
                                    contexto_memoria = (contexto_memoria + "\n\n" + contexto_grafo).strip()
                            except Exception:
                                pass

                        # Construir sección de especificaciones del usuario
                        especificaciones = _construir_especificaciones_usuario(params, consulta)

                        prompt_llm = (
                            f"Eres un analista BI experto. Analiza estos datos de '{accion_legible}' "
                            f"del período {fecha_ini} a {fecha_fin}.\n\n"
                            f"Datos ({n_registros} registros, muestra de 15):\n{contexto_datos}\n\n"
                        )
                        if contexto_memoria:
                            prompt_llm += f"Contexto de análisis previos:\n{contexto_memoria}\n\n"
                        if especificaciones:
                            prompt_llm += f"Especificaciones del usuario:\n{especificaciones}\n\n"
                        prompt_llm += (
                            f"Pregunta exacta del usuario: {mensaje}\n\n"
                            f"Instrucciones ESTRICTAS:\n"
                            f"- Responde EXACTAMENTE lo que el usuario pidió, no más ni menos\n"
                            f"- Si el usuario pidió un formato específico (tabla/lista/gráfica), úsalo\n"
                            f"- Si el usuario filtró por tienda/vendedor/producto, reporta SOLO esos datos\n"
                            f"- Si el usuario pidió top N, muestra exactamente N elementos\n"
                            f"- Usa SOLO hechos observables de los datos proporcionados\n"
                            f"- Si detectas algo notable (tendencia, anomalía, concentración), menciónalo\n"
                            f"- No inventes cifras que no estén en los datos\n"
                            f"- Si hay contexto de análisis previos, compara brevemente"
                        )
                        resp_llm = self._bot.cerebro_llm.generar(prompt_llm)
                        if resp_llm and hasattr(resp_llm, 'contenido') and resp_llm.contenido:
                            respuesta += f"### 💡 Análisis\n{resp_llm.contenido}\n"
                    except Exception:
                        pass  # LLM no disponible, la tabla es suficiente

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

