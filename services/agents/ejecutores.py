# ============================================================
# ANDROMEDA - Ejecutores de Agentes
# ============================================================
# Modulo extraido de interfaz_v5.py (ARQ-002)
# Centraliza la logica de ejecucion de los 12 agentes
# ============================================================

import re
import pandas as pd
from typing import Tuple


class EjecutoresAgente:
    """Logica de ejecucion de los 12 agentes.
    
    Recibe una referencia al bot principal para acceder a los
    servicios necesarios (analizador, predictor, conector, etc.).
    """

    def __init__(self, bot):
        self._bot = bot

    # Propiedades delegadas al bot para simplificar acceso
    @property
    def analizador(self):
        return self._bot.analizador

    @property
    def predictor(self):
        return self._bot.predictor

    @property
    def consultas_esp(self):
        return getattr(self._bot, 'consultas_esp', None)

    @property
    def odoo(self):
        return self._bot.odoo

    @property
    def conector(self):
        return getattr(self._bot, 'conector', getattr(self._bot, 'odoo', None))

    @property
    def fmt(self):
        return self._bot.fmt

    @property
    def analizador_inteligente(self):
        return getattr(self._bot, 'analizador_inteligente', None)

    def _ejecutar_accion(self, consulta, mensaje):
        return self._bot._ejecutar_accion(consulta, mensaje)

    def _info_conexion(self):
        return self._bot._info_conexion()

    def _ejecutor_ventas(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        temp = getattr(consulta, 'temporalidad', {}) or {}
        fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')
        params = getattr(consulta, 'parametros', {}) or {}

        if accion == 'ventas_por_dia_semana' and self.consultas_esp:
            datos = self.consultas_esp.ventas_completo(fi, ff)
            if 'error' not in datos and datos.get('por_dia_semana'):
                df = pd.DataFrame(datos['por_dia_semana'])
                resp = f"## Ventas por Día de la Semana\n\n**Período:** {fi} a {ff}\n\n"
                resp += "| Día | Total |\n|---|---:|\n"
                for _, r in df.iterrows():
                    dia = r.get('dia', r.get('day', str(r.iloc[0]) if len(r) > 0 else ''))
                    total = r.get('total', r.get('amount', r.iloc[-1] if len(r) > 0 else 0))
                    resp += f"| {dia} | ${float(total):,.2f} |\n"
                return resp, df

        if accion == 'ticket_promedio_evolucion':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            resumen = datos.get('resumen', {})
            total = resumen.get('total_ventas', 0)
            ordenes = resumen.get('ordenes', 1)
            ticket = total / ordenes if ordenes > 0 else 0
            resp = f"## Evolución del Ticket Promedio\n\n**Período:** {fi} a {ff}\n\n"
            resp += f"| Métrica | Valor |\n|---|---:|\n"
            resp += f"| Ticket promedio | ${ticket:,.2f} |\n"
            resp += f"| Total ventas | ${total:,.2f} |\n"
            resp += f"| Órdenes | {ordenes:,} |\n"
            df = pd.DataFrame(datos.get('por_cliente', [])) if datos.get('por_cliente') else None
            return resp, df

        if accion == 'clientes_nuevos_vs_recurrentes':
            from datetime import datetime, timedelta
            hace_30 = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            hace_90 = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            try:
                if self.odoo and self.odoo.conectado:
                    # Contar pedidos por cliente para distinguir nuevos vs recurrentes
                    df_orders = self.odoo.buscar(
                        'sale.order',
                        filtro=[('state', 'in', ['sale', 'done'])],
                        campos=['partner_id', 'date_order', 'amount_total'],
                        limite=2000
                    )
                    if df_orders is not None and not df_orders.empty:
                        df_orders['cliente'] = df_orders['partner_id'].apply(
                            lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                        )
                        df_orders['fecha'] = df_orders['date_order'].astype(str).str[:10]
                        n_pedidos = df_orders.groupby('cliente').size().reset_index(name='pedidos')
                        nuevos = int((n_pedidos['pedidos'] == 1).sum())
                        recurrentes = int((n_pedidos['pedidos'] > 1).sum())
                        total_cli = len(n_pedidos)
                        recientes_30 = int((df_orders['fecha'] >= hace_30)['partner_id'].nunique() if 'partner_id' in df_orders.columns else 0)
                        resp = (
                            f"## Clientes Nuevos vs Recurrentes\n\n"
                            f"| Segmento | Clientes | % |\n|---|---:|---:|\n"
                            f"| 🆕 Nuevos (1 pedido) | **{nuevos:,}** | {nuevos/total_cli*100:.1f}% |\n"
                            f"| 🔁 Recurrentes (2+ pedidos) | **{recurrentes:,}** | {recurrentes/total_cli*100:.1f}% |\n"
                            f"| 👥 Total clientes | **{total_cli:,}** | 100% |\n\n"
                        )
                        top_rec = n_pedidos[n_pedidos['pedidos'] > 1].sort_values('pedidos', ascending=False)
                        if not top_rec.empty:
                            resp += "**Top clientes recurrentes:**\n\n| Cliente | Pedidos |\n|---|---:|\n"
                            for _, r in top_rec.head(10).iterrows():
                                resp += f"| {str(r['cliente'])[:35]} | {int(r['pedidos'])} |\n"
                        return resp, n_pedidos
            except Exception:
                pass
            if self.consultas_esp:
                datos = self.consultas_esp.clientes_analisis()
                if 'error' not in datos:
                    resumen = datos.get('resumen', {})
                    resp = f"## Clientes\n\n**Total:** {resumen.get('total', 0):,}\n"
                    df = pd.DataFrame(datos.get('por_ciudad', [])) if datos.get('por_ciudad') else None
                    return resp, df

        # ── ventas_por_categoria ─────────────────────────────────────────────
        if accion == 'ventas_por_categoria':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('order_id.state', 'in', ['sale', 'done'])]
                    if fi:
                        filtro.append(('order_id.date_order', '>=', fi))
                    if ff:
                        filtro.append(('order_id.date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'sale.order.line',
                        filtro=filtro,
                        campos=['product_id', 'categ_id', 'price_subtotal', 'product_uom_qty'],
                        limite=2000
                    )
                    if df is not None and not df.empty:
                        if 'categ_id' in df.columns:
                            df['categoria'] = df['categ_id'].apply(
                                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                            )
                            df['subtotal'] = pd.to_numeric(df['price_subtotal'], errors='coerce').fillna(0)
                            agg = df.groupby('categoria')['subtotal'].sum().reset_index()
                            agg = agg.sort_values('subtotal', ascending=False)
                            total = agg['subtotal'].sum()
                            resp = (
                                f"## Ventas por Categoría\n\n"
                                f"**Período:** {fi} a {ff}\n\n"
                                f"| Categoría | Ventas | % del total |\n|---|---:|---:|\n"
                            )
                            for _, r in agg.iterrows():
                                pct = r['subtotal'] / total * 100 if total > 0 else 0
                                resp += f"| {r['categoria']} | ${float(r['subtotal']):,.2f} | {pct:.1f}% |\n"
                            return resp, agg
            except Exception:
                pass
            datos = self.analizador.top_productos_vendidos(fi, ff)
            df = pd.DataFrame(datos.get('productos', []))
            return f"## Ventas por Categoría\n\n**Período:** {fi} a {ff}\n\n> *Clasificación por productos disponible.*", df if not df.empty else None

        # ── ventas_por_canal ──────────────────────────────────────────────────
        if accion == 'ventas_por_canal':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', 'in', ['sale', 'done'])]
                    if fi:
                        filtro.append(('date_order', '>=', fi))
                    if ff:
                        filtro.append(('date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'sale.order', filtro=filtro,
                        campos=['team_id', 'amount_total'], limite=500
                    )
                    if df is not None and not df.empty and 'team_id' in df.columns:
                        df['canal'] = df['team_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['monto'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        agg = df.groupby('canal')['monto'].sum().reset_index().sort_values('monto', ascending=False)
                        total_v = float(agg['monto'].sum())
                        resp = f"## Ventas por Canal\n\n**Período:** {fi} a {ff}\n\n| Canal de Venta | Importe | % del total |\n|---|---:|---:|\n"
                        for _, r in agg.iterrows():
                            pct = float(r['monto']) / total_v * 100 if total_v > 0 else 0
                            resp += f"| {r['canal']} | ${float(r['monto']):,.2f} | {pct:.1f}% |\n"
                        resp += f"\n**Total:** ${total_v:,.2f}"
                        return resp, agg
            except Exception:
                pass
            return "## Ventas por Canal\n\nConfigura los equipos de ventas en Odoo para ver el desglose por canal.", None

        # ── margen_por_producto ───────────────────────────────────────────────
        if accion == 'margen_por_producto':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('order_id.state', 'in', ['sale', 'done'])]
                    if fi:
                        filtro.append(('order_id.date_order', '>=', fi))
                    if ff:
                        filtro.append(('order_id.date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'sale.order.line', filtro=filtro,
                        campos=['product_id', 'price_unit', 'purchase_price', 'price_subtotal', 'product_uom_qty'],
                        limite=1000
                    )
                    if df is not None and not df.empty:
                        df['producto'] = df['product_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['costo'] = pd.to_numeric(df.get('purchase_price', 0), errors='coerce').fillna(0)
                        df['subtotal'] = pd.to_numeric(df.get('price_subtotal', 0), errors='coerce').fillna(0)
                        df['qty'] = pd.to_numeric(df.get('product_uom_qty', 1), errors='coerce').fillna(1)
                        df['costo_linea'] = df['costo'] * df['qty']
                        agg = df.groupby('producto').agg(ventas=('subtotal', 'sum'), costo_total=('costo_linea', 'sum')).reset_index()
                        agg = agg[agg['ventas'] > 0].copy()
                        agg['margen'] = agg['ventas'] - agg['costo_total']
                        agg['margen_pct'] = agg['margen'] / agg['ventas'] * 100
                        agg = agg.sort_values('margen', ascending=False)
                        resp = f"## Margen por Producto\n\n**Período:** {fi} a {ff}\n\n| Producto | Ventas | Costo | Margen | % |\n|---|---:|---:|---:|---:|\n"
                        for _, r in agg.head(20).iterrows():
                            emoji_m = "🟢" if float(r['margen_pct']) > 20 else "🟡" if float(r['margen_pct']) > 5 else "🔴"
                            resp += f"| {str(r['producto'])[:35]} | ${float(r['ventas']):,.2f} | ${float(r['costo_total']):,.2f} | ${float(r['margen']):,.2f} | {emoji_m} {float(r['margen_pct']):.1f}% |\n"
                        return resp, agg
            except Exception:
                pass
            datos_fb = self.analizador.top_productos_vendidos(fi, ff)
            df_fb = pd.DataFrame(datos_fb.get('productos', []))
            return (
                f"## Margen por Producto\n\n**Período:** {fi} a {ff}\n\n"
                "> 💡 *Para márgenes exactos configura `Precio de costo` en cada producto de Odoo.*",
                df_fb if not df_fb.empty else None
            )

        # ── devolucion_ventas ─────────────────────────────────────────────────
        if accion == 'devolucion_ventas':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('move_type', '=', 'out_refund'), ('state', '=', 'posted')]
                    if fi:
                        filtro.append(('invoice_date', '>=', fi))
                    if ff:
                        filtro.append(('invoice_date', '<=', ff))
                    df = self.odoo.buscar(
                        'account.move', filtro=filtro,
                        campos=['name', 'partner_id', 'amount_total', 'invoice_date'], limite=200
                    )
                    if df is not None and not df.empty:
                        total_dev = pd.to_numeric(df['amount_total'], errors='coerce').sum()
                        resp = (
                            f"## Devoluciones de Ventas\n\n**Período:** {fi} a {ff}\n\n"
                            f"- **Notas de crédito:** {len(df):,}\n- **Total devuelto:** ${total_dev:,.2f}\n\n"
                            f"| Folio | Cliente | Monto | Fecha |\n|---|---|---:|---|\n"
                        )
                        for _, r in df.head(15).iterrows():
                            cli = r.get('partner_id', '')
                            cli_n = cli[1] if isinstance(cli, (list, tuple)) else str(cli)
                            resp += f"| {r.get('name', '')} | {cli_n[:30]} | ${float(r.get('amount_total', 0)):,.2f} | {str(r.get('invoice_date', ''))[:10]} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Devoluciones de Ventas\n\nNo se encontraron notas de crédito en el período.", None

        # ── meta_cumplimiento ─────────────────────────────────────────────────
        if accion == 'meta_cumplimiento':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            ventas = datos.get('resumen', {}).get('total_ventas', 0)
            meta = float(params.get('meta', params.get('target', 0)))
            resp = f"## Cumplimiento de Meta de Ventas\n\n**Período:** {fi} a {ff}\n\n| Métrica | Valor |\n|---|---:|\n| 💰 Ventas realizadas | **${ventas:,.2f}** |\n"
            if meta > 0:
                cumpl = ventas / meta * 100
                faltante = max(meta - ventas, 0)
                emoji_m = "🟢" if cumpl >= 100 else "🟡" if cumpl >= 80 else "🔴"
                resp += f"| 🎯 Meta establecida | **${meta:,.2f}** |\n| 📊 % Cumplimiento | **{emoji_m} {cumpl:.1f}%** |\n| ➕ Faltante | **${faltante:,.2f}** |\n"
            else:
                resp += "| 🎯 Meta | *No especificada* |\n\n> 💡 *Indica: 'cumplimiento meta $500,000'*\n"
            df_vend = pd.DataFrame(datos.get('por_vendedor', []))
            return resp, df_vend if not df_vend.empty else None

        # ── ventas_por_hora ───────────────────────────────────────────────────
        if accion == 'ventas_por_hora':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', 'in', ['done', 'invoiced', 'paid'])]
                    if fi:
                        filtro.append(('date_order', '>=', fi))
                    if ff:
                        filtro.append(('date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'pos.order', filtro=filtro, campos=['date_order', 'amount_total'], limite=2000
                    )
                    if df is not None and not df.empty and 'date_order' in df.columns:
                        df['hora'] = pd.to_datetime(df['date_order'], errors='coerce').dt.hour
                        df['monto'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        agg = df.groupby('hora')['monto'].sum().reset_index().sort_values('hora')
                        max_v = float(agg['monto'].max()) if not agg.empty else 1
                        resp = f"## Ventas por Hora del Día (POS)\n\n**Período:** {fi} a {ff}\n\n| Hora | Ventas | Intensidad |\n|---|---:|---|\n"
                        for _, r in agg.iterrows():
                            barras = int(float(r['monto']) / max_v * 10) if max_v > 0 else 0
                            resp += f"| {int(r['hora']):02d}:00 | ${float(r['monto']):,.2f} | {'█' * barras}{'░' * (10 - barras)} |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Ventas por Hora\n\nSe requiere módulo POS activo para análisis por hora.", None

        # ── concentracion_clientes ────────────────────────────────────────────
        if accion == 'concentracion_clientes':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            resp = f"## Concentración de Clientes\n\n**Período:** {fi} a {ff}\n\n"
            if df is not None and not df.empty and 'total' in df.columns:
                col = pd.to_numeric(df['total'], errors='coerce').fillna(0)
                total_cc = float(col.sum())
                df_s = df.copy()
                df_s['total_n'] = col
                df_s = df_s.sort_values('total_n', ascending=False).reset_index(drop=True)
                top5 = float(df_s.head(5)['total_n'].sum())
                top10 = float(df_s.head(10)['total_n'].sum())
                pct5 = top5 / total_cc * 100 if total_cc > 0 else 0
                pct10 = top10 / total_cc * 100 if total_cc > 0 else 0
                resp += (
                    f"| Segmento | Ventas | % del total |\n|---|---:|---:|\n"
                    f"| 🥇 Top 5 clientes | ${top5:,.2f} | **{pct5:.1f}%** |\n"
                    f"| 🏅 Top 10 clientes | ${top10:,.2f} | **{pct10:.1f}%** |\n"
                    f"| 📊 Total clientes | {len(df):,} | 100.0% |\n\n"
                )
                if pct5 > 60:
                    resp += "🔴 **Alta concentración**: más del 60% de ventas en 5 clientes. Riesgo de dependencia.\n"
                elif pct5 > 40:
                    resp += "🟡 **Concentración moderada**: considera diversificar tu cartera.\n"
                else:
                    resp += "🟢 **Cartera diversificada**: buena distribución entre clientes.\n"
                resp += "\n**Top 10 clientes:**\n\n| # | Cliente | Ventas |\n|---|---|---:|\n"
                for i, (_, r) in enumerate(df_s.head(10).iterrows(), 1):
                    nombre = str(r.get('name', r.get('partner', '')))[:35]
                    resp += f"| {i} | {nombre} | ${float(r['total_n']):,.2f} |\n"
            else:
                resp += "No hay datos de clientes disponibles."
            return resp, df

        # ── descuentos_aplicados ──────────────────────────────────────────────
        if accion == 'descuentos_aplicados':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('order_id.state', 'in', ['sale', 'done']), ('discount', '>', 0)]
                    if fi:
                        filtro.append(('order_id.date_order', '>=', fi))
                    if ff:
                        filtro.append(('order_id.date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'sale.order.line', filtro=filtro,
                        campos=['product_id', 'price_unit', 'discount', 'price_subtotal', 'product_uom_qty'],
                        limite=500
                    )
                    if df is not None and not df.empty:
                        df['desc'] = pd.to_numeric(df['discount'], errors='coerce').fillna(0)
                        df['subtotal'] = pd.to_numeric(df['price_subtotal'], errors='coerce').fillna(0)
                        df['precio'] = pd.to_numeric(df.get('price_unit', 0), errors='coerce').fillna(0)
                        df['qty'] = pd.to_numeric(df.get('product_uom_qty', 1), errors='coerce').fillna(1)
                        df['bruto'] = df['precio'] * df['qty']
                        total_bruto = float(df['bruto'].sum())
                        total_neto = float(df['subtotal'].sum())
                        total_desc = total_bruto - total_neto
                        pct_desc = total_desc / total_bruto * 100 if total_bruto > 0 else 0
                        avg_desc = float(df['desc'].mean())
                        resp = (
                            f"## Descuentos Aplicados en Ventas\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Métrica | Valor |\n|---|---:|\n"
                            f"| 🏷️ Líneas con descuento | **{len(df):,}** |\n"
                            f"| 💰 Ventas brutas | **${total_bruto:,.2f}** |\n"
                            f"| 💳 Ventas netas | **${total_neto:,.2f}** |\n"
                            f"| 📉 Descuentos otorgados | **${total_desc:,.2f}** |\n"
                            f"| 🎯 % sobre ventas brutas | **{pct_desc:.1f}%** |\n"
                            f"| 📊 Descuento promedio | **{avg_desc:.1f}%** |\n\n"
                        )
                        if pct_desc > 15:
                            resp += "⚠️ **Alerta:** Nivel de descuentos elevado. Revisar política de precios.\n"
                        return resp, df
            except Exception:
                pass
            return f"## Descuentos Aplicados\n\nNo se encontraron descuentos en el período {fi} - {ff}.", None

        # ── ventas_vs_anterior ────────────────────────────────────────────────
        if accion == 'ventas_vs_anterior':
            datos_act = self.analizador.analisis_ventas_completo(fi, ff)
            ventas_act = datos_act.get('resumen', {}).get('total_ventas', 0)
            ordenes_act = datos_act.get('resumen', {}).get('ordenes', 0)
            datos_prev = self.predictor.comparar_periodos('mes')
            ventas_prev = datos_prev.get('periodo_anterior', {}).get('total_ventas', 0) if 'error' not in datos_prev else 0
            var_abs = ventas_act - ventas_prev
            var_pct = (var_abs / ventas_prev * 100) if ventas_prev > 0 else 0
            emoji_v = "🟢 ↑" if var_pct >= 0 else "🔴 ↓"
            resp = (
                f"## Ventas vs. Período Anterior\n\n**Período actual:** {fi} a {ff}\n\n"
                f"| Métrica | Actual | Anterior | Variación |\n|---|---:|---:|---:|\n"
                f"| 💰 Ventas | **${ventas_act:,.2f}** | ${ventas_prev:,.2f} | {emoji_v} {var_pct:+.1f}% |\n"
                f"| 📋 Órdenes | **{ordenes_act:,}** | — | — |\n\n"
            )
            if var_pct > 0:
                resp += f"✅ Crecimiento de **${var_abs:,.2f}** respecto al período anterior.\n"
            elif var_pct < 0:
                resp += f"⚠️ Caída de **${abs(var_abs):,.2f}** respecto al período anterior.\n"
            df_vend2 = pd.DataFrame(datos_act.get('por_vendedor', []))
            return resp, df_vend2 if not df_vend2.empty else None

        # ── ventas_por_marca ───────────────────────────────────────────────────
        if accion in ('ventas_por_marca', 'ventas_mensuales_marca'):
            try:
                if self.odoo and self.odoo.conectado:
                    filtro_vpm = [('order_id.state', 'in', ['sale', 'done'])]
                    if fi:
                        filtro_vpm.append(('order_id.date_order', '>=', fi))
                    if ff:
                        filtro_vpm.append(('order_id.date_order', '<=', ff))

                    df_lin = self.odoo.buscar(
                        'sale.order.line', filtro=filtro_vpm,
                        campos=['product_id', 'price_subtotal', 'product_uom_qty'],
                        limite=0,
                    )

                    if df_lin is not None and not df_lin.empty:
                        df_lin = df_lin.copy()
                        df_lin['subtotal'] = pd.to_numeric(df_lin['price_subtotal'], errors='coerce').fillna(0)
                        df_lin['qty'] = pd.to_numeric(df_lin['product_uom_qty'], errors='coerce').fillna(0)

                        # Extraer IDs de producto.product
                        df_lin['prod_id'] = df_lin['product_id'].apply(
                            lambda x: int(x[0]) if isinstance(x, (list, tuple)) else int(x) if str(x).isdigit() else None
                        )
                        prod_ids = [int(i) for i in df_lin['prod_id'].dropna().unique().tolist()]

                        # Paso 2: obtener marca de product.product
                        # Intento 1: product_brand_id (módulo OCA product_brand)
                        marca_map = {}
                        df_prods = None
                        try:
                            df_prods = self.odoo.buscar(
                                'product.product',
                                filtro=[('id', 'in', prod_ids)],
                                campos=['id', 'product_brand_id', 'categ_id'],
                                limite=0,
                            )
                        except Exception:
                            pass

                        if df_prods is not None and not df_prods.empty:
                            for _, p in df_prods.iterrows():
                                pid = int(p['id'])
                                brand = p.get('product_brand_id', False)
                                categ = p.get('categ_id', False)
                                # product_brand_id tiene prioridad
                                if brand and isinstance(brand, (list, tuple)) and brand[0]:
                                    marca_map[pid] = str(brand[1])
                                elif categ and isinstance(categ, (list, tuple)):
                                    marca_map[pid] = str(categ[1])
                                else:
                                    marca_map[pid] = 'Sin marca'
                        else:
                            # Sin datos de productos → usar nombre del producto como fallback
                            df_lin['marca'] = df_lin['product_id'].apply(
                                lambda x: x[1] if isinstance(x, (list, tuple)) else 'Sin marca'
                            )

                        if marca_map:
                            df_lin['marca'] = df_lin['prod_id'].map(marca_map).fillna('Sin marca')

                        # Determinar si se usó marca real o categoría
                        tiene_brand = (
                            df_prods is not None
                            and not df_prods.empty
                            and 'product_brand_id' in df_prods.columns
                            and df_prods['product_brand_id'].apply(lambda x: bool(x and isinstance(x, (list, tuple)) and x[0])).any()
                        )
                        etiqueta_grupo = 'Marca' if tiene_brand else 'Categoría / Marca'

                        # Agregado por marca
                        agg_marca = df_lin.groupby('marca').agg(
                            lineas=('subtotal', 'count'),
                            unidades=('qty', 'sum'),
                            ventas=('subtotal', 'sum'),
                        ).reset_index().sort_values('ventas', ascending=False)

                        total_vpm = float(agg_marca['ventas'].sum())
                        total_u = float(agg_marca['unidades'].sum())

                        resp_vpm = (
                            f"## Ventas por {etiqueta_grupo}\n\n"
                            f"**Período:** {fi} → {ff} | "
                            f"**Marcas:** {len(agg_marca)} | "
                            f"**Total:** ${total_vpm:,.2f} | "
                            f"**Unidades:** {total_u:,.0f}\n\n"
                        )
                        if not tiene_brand:
                            resp_vpm += "> ℹ️ *Se está usando categoría de producto como agrupación de marca (módulo de marcas no detectado).*\n\n"

                        resp_vpm += f"| # | {etiqueta_grupo} | Órdenes/Líneas | Unidades | Ventas | % del total |\n|---|---|---:|---:|---:|---:|\n"
                        for i, (_, r) in enumerate(agg_marca.iterrows(), 1):
                            pct = float(r['ventas']) / total_vpm * 100 if total_vpm > 0 else 0
                            resp_vpm += (
                                f"| {i} | **{str(r['marca'])[:35]}** | {int(r['lineas']):,} | "
                                f"{float(r['unidades']):,.0f} | ${float(r['ventas']):,.2f} | {pct:.1f}% |\n"
                            )

                        # Top 3 marcas
                        top3 = agg_marca.head(3)
                        if len(top3) >= 1:
                            pct_top3 = float(top3['ventas'].sum()) / total_vpm * 100 if total_vpm > 0 else 0
                            resp_vpm += f"\n> 🏆 *Top 3 marcas concentran el **{pct_top3:.1f}%** del total.*\n"

                        return resp_vpm, agg_marca
            except Exception:
                import traceback; traceback.print_exc()
            return (
                f"## Ventas por Marca\n\n"
                f"No se encontraron datos de ventas por marca en el período {fi} → {ff}.", None
            )

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_inventario(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        params = getattr(consulta, 'parametros', {}) or {}

        if accion == 'abc_inventario' and self.consultas_esp:
            datos = self.consultas_esp.rotacion_inventario(30)
            if 'error' not in datos:
                resp = "## Clasificación ABC de Inventario\n\n"
                resumen = datos.get('resumen', {})
                resp += f"- **Productos analizados:** {resumen.get('total_productos', 0):,}\n"
                resp += f"- **Período:** últimos 30 días\n\n"
                df = pd.DataFrame(datos.get('productos', [])) if datos.get('productos') else (datos.get('df') if 'df' in datos else None)
                if df is not None and not df.empty:
                    resp += "| Producto | Movimiento | Stock |\n|---|---:|---:|\n"
                    for _, r in df.head(15).iterrows():
                        nombre = r.get('name', r.get('product', ''))
                        mov = r.get('movimiento', r.get('qty_done', 0))
                        stk = r.get('stock', r.get('quantity', 0))
                        resp += f"| {str(nombre)[:35]} | {float(mov):,.0f} | {float(stk):,.0f} |\n"
                return resp, df

        if accion == 'inventario_por_categoria':
            datos = self.analizador.analisis_inventario()
            if 'por_categoria' in datos:
                df = pd.DataFrame(datos['por_categoria'])
                resp = "## Inventario por Categoría\n\n"
                resp += f"- **Total SKUs:** {datos.get('resumen', {}).get('total_productos', 0):,}\n\n"
                return resp, df

        if accion == 'cobertura_stock':
            datos = self.analizador.productos_mas_vendidos_vs_stock()
            if datos.get('criticos'):
                df = pd.DataFrame(datos['criticos'])
                resp = "## Cobertura de Stock\n\n"
                resp += f"- **Productos críticos (< 7 días):** {len(datos['criticos'])}\n\n"
                resp += "| Producto | Stock | Días Cobertura |\n|---|---:|---:|\n"
                for _, r in df.head(15).iterrows():
                    resp += f"| {str(r.get('product', ''))[:35]} | {r.get('stock', 0):,.0f} | {r.get('dias_stock', 0):.0f} |\n"
                return resp, df

        if accion == 'inventario_valorizado_categoria':
            datos = self.analizador.analisis_inventario()
            if datos.get('valoracion'):
                resp = "## Inventario Valorizado por Categoría\n\n"
                val = datos['valoracion']
                resp += f"- **Valor total inventario:** ${val.get('total', 0):,.2f}\n"
                df = pd.DataFrame(datos.get('por_categoria', []))
                return resp, df

        # ── movimientos_stock ────────────────────────────────────────────────
        if accion == 'movimientos_stock':
            temp_l = getattr(consulta, 'temporalidad', {}) or {}
            fi_l, ff_l = temp_l.get('fecha_inicio', ''), temp_l.get('fecha_fin', '')
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', '=', 'done')]
                    if fi_l:
                        filtro.append(('date', '>=', fi_l))
                    if ff_l:
                        filtro.append(('date', '<=', ff_l))
                    df = self.odoo.buscar(
                        'stock.move',
                        filtro=filtro,
                        campos=['product_id', 'product_uom_qty', 'location_id', 'location_dest_id', 'date'],
                        limite=500
                    )
                    if df is not None and not df.empty:
                        n = len(df)
                        total_qty = pd.to_numeric(df['product_uom_qty'], errors='coerce').sum() if 'product_uom_qty' in df.columns else 0
                        resp = (
                            f"## Movimientos de Stock\n\n"
                            f"**Período:** {fi_l} a {ff_l}\n\n"
                            f"- **Movimientos totales:** {n:,}\n"
                            f"- **Unidades totales movidas:** {total_qty:,.0f}\n\n"
                        )
                        if 'product_id' in df.columns:
                            df['producto'] = df['product_id'].apply(
                                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                            )
                            df['qty'] = pd.to_numeric(df.get('product_uom_qty', 0), errors='coerce').fillna(0)
                            top = df.groupby('producto')['qty'].sum().nlargest(10).reset_index()
                            resp += "**Top 10 productos con más movimientos:**\n\n"
                            resp += "| Producto | Uds. movidas |\n|---|---:|\n"
                            for _, r in top.iterrows():
                                resp += f"| {str(r['producto'])[:40]} | {float(r['qty']):,.0f} |\n"
                        return resp, df
            except Exception:
                pass
            datos = self.analizador.analisis_inventario()
            return "## Movimientos de Stock\n\nConecta Odoo para ver movimientos detallados.", None

        # ── productos_bajo_minimo ────────────────────────────────────────────
        if accion == 'productos_bajo_minimo':
            datos = self.analizador.analisis_inventario()
            criticos = datos.get('productos_bajo_stock', [])
            resp = (
                f"## Productos Bajo Mínimo de Stock\n\n"
                f"**{len(criticos)} productos** con stock por debajo del umbral mínimo:\n\n"
                f"| Producto | Stock actual | Mínimo | Diferencia |\n|---|---:|---:|---:|\n"
            )
            for p in criticos[:20]:
                nombre = str(p.get('name', p.get('product', '')))[:35]
                stock = float(p.get('qty_available', p.get('stock', 0)))
                minimo = float(p.get('reorder_point', p.get('minimo', 0)))
                diff = stock - minimo
                emoji = "🔴" if diff < 0 else "🟡"
                resp += f"| {nombre} | {stock:.0f} | {minimo:.0f} | {emoji} {diff:+.0f} |\n"
            if not criticos:
                resp = "## Productos Bajo Mínimo\n\n✅ Todos los productos tienen stock sobre el mínimo configurado."
            return resp, pd.DataFrame(criticos) if criticos else None

        # ── inventario_obsoleto ───────────────────────────────────────────────
        if accion == 'inventario_obsoleto':
            from datetime import datetime, timedelta
            dias_umbral = 180
            corte_obsoleto = (datetime.today() - timedelta(days=dias_umbral)).strftime('%Y-%m-%d')
            try:
                if self.odoo and self.odoo.conectado:
                    # 1. Todos los productos con stock físico (sin límite, todas las empresas)
                    df_stock = self.odoo.buscar(
                        'stock.quant',
                        filtro=[('quantity', '>', 0), ('location_id.usage', '=', 'internal')],
                        campos=['product_id', 'location_id', 'quantity', 'value', 'company_id'],
                        limite=0,
                    )
                    if df_stock is None or df_stock.empty or 'product_id' not in df_stock.columns:
                        return (f"## Inventario Obsoleto\n\nNo hay productos con stock en el sistema.", None)

                    # Extraer IDs únicos de productos con stock
                    df_stock = df_stock.copy()
                    df_stock['prod_id'] = df_stock['product_id'].apply(
                        lambda x: x[0] if isinstance(x, (list, tuple)) else x
                    )
                    df_stock['prod_nombre'] = df_stock['product_id'].apply(
                        lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                    )
                    df_stock['empresa'] = df_stock['company_id'].apply(
                        lambda x: x[1] if isinstance(x, (list, tuple)) else 'N/A'
                    ) if 'company_id' in df_stock.columns else 'N/A'
                    df_stock['qty'] = pd.to_numeric(df_stock.get('quantity', 0), errors='coerce').fillna(0)
                    df_stock['valor'] = pd.to_numeric(df_stock.get('value', 0), errors='coerce').fillna(0)

                    ids_con_stock = set(df_stock['prod_id'].dropna().astype(int).tolist())

                    # 2. Productos con movimiento REAL (state=done) en los últimos 180 días
                    #    stock.move.line es el modelo de movimientos físicos confirmados
                    df_moves = self.odoo.buscar(
                        'stock.move.line',
                        filtro=[
                            ('state', '=', 'done'),
                            ('date', '>=', corte_obsoleto),
                        ],
                        campos=['product_id', 'date'],
                        limite=0,
                    )
                    ids_con_movimiento: set = set()
                    if df_moves is not None and not df_moves.empty and 'product_id' in df_moves.columns:
                        ids_con_movimiento = set(
                            df_moves['product_id'].apply(
                                lambda x: x[0] if isinstance(x, (list, tuple)) else x
                            ).dropna().astype(int).tolist()
                        )

                    # 3. Obsoletos = con stock PERO sin movimiento en los últimos 180 días
                    ids_obsoletos = ids_con_stock - ids_con_movimiento

                    # Agrupar stock de los obsoletos
                    obs_df = df_stock[df_stock['prod_id'].isin(ids_obsoletos)].copy()

                    # Agrupar por producto (puede haber múltiples quants del mismo producto)
                    resumen = obs_df.groupby(['prod_id', 'prod_nombre', 'empresa']).agg(
                        unidades=('qty', 'sum'),
                        valor=('valor', 'sum'),
                    ).reset_index().sort_values('valor', ascending=False)

                    n_obs = len(resumen)
                    val_obs = float(resumen['valor'].sum())
                    total_unids = float(resumen['unidades'].sum())
                    val_all = float(df_stock['valor'].sum())
                    pct_val = (val_obs / val_all * 100) if val_all > 0 else 0
                    pct_prod = (n_obs / len(ids_con_stock) * 100) if ids_con_stock else 0

                    resp = (
                        f"## Inventario Obsoleto — Sin Movimiento > {dias_umbral} Días\n\n"
                        f"**Criterio:** sin movimiento físico confirmado (`stock.move.line`) desde antes del {corte_obsoleto}\n\n"
                        f"| Métrica | Valor |\n|---|---:|\n"
                        f"| 📦 Productos con stock total | **{len(ids_con_stock):,}** |\n"
                        f"| 🔴 Productos obsoletos | **{n_obs:,}** ({pct_prod:.1f}% del catálogo) |\n"
                        f"| 🔢 Unidades inmovilizadas | **{total_unids:,.0f}** |\n"
                        f"| 💰 Capital inmovilizado | **${val_obs:,.2f}** ({pct_val:.1f}% del valor total) |\n"
                        f"| ✅ Con movimiento reciente | **{len(ids_con_movimiento & ids_con_stock):,}** productos |\n\n"
                    )

                    if n_obs > 0:
                        # Agrupar también por empresa
                        if resumen['empresa'].nunique() > 1:
                            por_emp = resumen.groupby('empresa').agg(
                                productos=('prod_id', 'count'),
                                valor=('valor', 'sum'),
                            ).reset_index().sort_values('valor', ascending=False)
                            resp += "**Por Empresa:**\n\n| Empresa | Productos | Valor |\n|---|---:|---:|\n"
                            for _, r in por_emp.iterrows():
                                resp += f"| {str(r['empresa'])[:35]} | {int(r['productos'])} | ${float(r['valor']):,.2f} |\n"
                            resp += "\n"

                        resp += f"**Top obsoletos por valor capital inmovilizado:**\n\n"
                        resp += "| Producto | Empresa | Unidades | Valor |\n|---|---|---:|---:|\n"
                        for _, r in resumen.head(20).iterrows():
                            nombre = str(r['prod_nombre'])[:40]
                            emp = str(r['empresa'])[:20]
                            resp += f"| {nombre} | {emp} | {float(r['unidades']):,.0f} | ${float(r['valor']):,.2f} |\n"
                        resp += "\n⚠️ **Acciones recomendadas:** liquidación, descuento agresivo, transferencia entre empresas o baja del catálogo."
                    else:
                        resp += "✅ No se encontraron productos sin movimiento en los últimos 180 días."

                    return resp, resumen if n_obs > 0 else df_stock
            except Exception:
                import traceback; traceback.print_exc()
            return (
                f"## Inventario Obsoleto\n\n"
                f"No se pudo consultar Odoo. Verifica la conexión.\n\n"
                f"**Criterio:** sin movimiento físico desde antes del {corte_obsoleto}.", None
            )

        # ── inventario_negativo ───────────────────────────────────────────────
        if accion == 'inventario_negativo':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'stock.quant',
                        filtro=[('quantity', '<', 0)],
                        campos=['product_id', 'location_id', 'quantity', 'reserved_quantity'],
                        limite=200
                    )
                    if df is not None and not df.empty:
                        if 'product_id' in df.columns:
                            df = df.copy()
                            df['producto'] = df['product_id'].apply(
                                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                            )
                        n = len(df)
                        total_neg = pd.to_numeric(df['quantity'], errors='coerce').sum() if 'quantity' in df.columns else 0
                        resp = (
                            f"## ⚠️ Stock Negativo Detectado\n\n"
                            f"**{n} ubicaciones** con cantidad negativa en el sistema.\n\n"
                            f"| Producto | Ubicación | Stock |\n|---|---|---:|\n"
                        )
                        for _, r in df.head(20).iterrows():
                            prod = str(r.get('producto', str(r.get('product_id', ''))))[:35]
                            loc = r.get('location_id', '')
                            loc_n = loc[1] if isinstance(loc, (list, tuple)) else str(loc)
                            qty = float(r.get('quantity', 0))
                            resp += f"| {prod} | {str(loc_n)[:25]} | 🔴 {qty:,.0f} |\n"
                        resp += (
                            f"\n**Total unidades en negativo:** {total_neg:,.0f}\n\n"
                            "⚠️ **Causas posibles:**\n"
                            "- Movimientos registrados antes de recibir la mercancía\n"
                            "- Transferencias pendientes de validar\n"
                            "- Configuración incorrecta de ubicaciones\n\n"
                            "> 💡 *Revisa: Inventario → Operaciones → Traslados*"
                        )
                        return resp, df
                    return "✅ No se encontró stock negativo en el sistema.", None
            except Exception:
                pass
            return "No se pudo verificar stock negativo. Verifica la conexión con Odoo.", None

        # ── merma_inventario ──────────────────────────────────────────────────
        if accion == 'merma_inventario':
            temp_m = getattr(consulta, 'temporalidad', {}) or {}
            fi_m = temp_m.get('fecha_inicio', '')
            ff_m = temp_m.get('fecha_fin', '')
            try:
                if self.odoo and self.odoo.conectado:
                    filtro_m = []
                    if fi_m:
                        filtro_m.append(('date_done', '>=', fi_m))
                    if ff_m:
                        filtro_m.append(('date_done', '<=', ff_m))
                    df = self.odoo.buscar(
                        'stock.scrap',
                        filtro=filtro_m or [('state', '=', 'done')],
                        campos=['product_id', 'scrap_qty', 'date_done', 'location_id', 'origin'],
                        limite=200,
                        orden='date_done desc'
                    )
                    if df is not None and not df.empty:
                        df = df.copy()
                        if 'product_id' in df.columns:
                            df['producto'] = df['product_id'].apply(
                                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                            )
                        df['qty'] = pd.to_numeric(df.get('scrap_qty', 0), errors='coerce').fillna(0)
                        total_uds = float(df['qty'].sum())
                        n_registros = len(df)
                        top_prod = df.groupby('producto')['qty'].sum().nlargest(10).reset_index() if 'producto' in df.columns else df.head(10)
                        resp = (
                            f"## Análisis de Mermas\n\n"
                            f"**Período:** {fi_m or 'histórico'} a {ff_m or 'hoy'}\n\n"
                            f"| Métrica | Valor |\n|---|---:|\n"
                            f"| 📋 Registros de merma | **{n_registros:,}** |\n"
                            f"| 📦 Unidades dadas de baja | **{total_uds:,.0f}** |\n\n"
                            f"**Productos con mayor merma:**\n\n"
                            f"| Producto | Unidades dadas de baja |\n|---|---:|\n"
                        )
                        for _, r in top_prod.iterrows():
                            nombre = str(r.get('producto', r.get('product_id', '')))[:40]
                            qty = float(r.get('qty', r.get('scrap_qty', 0)))
                            resp += f"| {nombre} | {qty:,.0f} |\n"
                        resp += "\n> 💡 *Registra mermas en: Inventario → Operaciones → Desechar*"
                        return resp, df
            except Exception:
                pass
            return "No se encontraron registros de merma. Verifica que uses Inventario → Operaciones → Desechar en Odoo.", None

        # ── transferencias_pendientes ─────────────────────────────────────────
        if accion == 'transferencias_pendientes':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'stock.picking',
                        filtro=[('state', 'in', ['assigned', 'waiting', 'confirmed'])],
                        campos=['name', 'partner_id', 'origin', 'scheduled_date', 'state', 'picking_type_id'],
                        limite=100,
                        orden='scheduled_date asc'
                    )
                    if df is not None and not df.empty:
                        n = len(df)
                        estado_map = {
                            'assigned': '✅ Listo para enviar',
                            'confirmed': '🟡 Confirmado',
                            'waiting': '🔴 Esperando operación previa'
                        }
                        resp = (
                            f"## Transferencias Pendientes\n\n"
                            f"**{n} transferencias** en proceso:\n\n"
                            f"| Referencia | Tipo | Estado | Fecha programada |\n|---|---|---|---|\n"
                        )
                        for _, r in df.head(25).iterrows():
                            ref = str(r.get('name', ''))
                            tipo = r.get('picking_type_id', '')
                            tipo_n = tipo[1] if isinstance(tipo, (list, tuple)) else str(tipo)
                            estado = str(r.get('state', ''))
                            est_label = estado_map.get(estado, estado)
                            fecha = str(r.get('scheduled_date', ''))[:10]
                            resp += f"| {ref} | {str(tipo_n)[:20]} | {est_label} | {fecha} |\n"
                        if 'state' in df.columns:
                            resp += "\n**Resumen por estado:**\n"
                            for est, cnt in df['state'].value_counts().items():
                                resp += f"- {estado_map.get(est, est)}: **{cnt}**\n"
                        return resp, df
                    return "✅ No hay transferencias pendientes en este momento.", None
            except Exception:
                pass
            return "No se pudo consultar las transferencias. Verifica la conexión con Odoo.", None

        # ── costo_almacenamiento ──────────────────────────────────────────────
        if accion == 'costo_almacenamiento':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'stock.quant',
                        filtro=[('quantity', '>', 0), ('location_id.usage', '=', 'internal')],
                        campos=['product_id', 'location_id', 'quantity', 'value'],
                        limite=500,
                        orden='value desc'
                    )
                    if df is not None and not df.empty:
                        df = df.copy()
                        df['val'] = pd.to_numeric(df.get('value', 0), errors='coerce').fillna(0)
                        valor_total = float(df['val'].sum())
                        tasa_holding = 0.22  # 22% anual estándar (capital + seguro + espacio + obsolescencia)
                        costo_anual = valor_total * tasa_holding
                        costo_mensual = costo_anual / 12
                        n_skus = len(df)
                        if 'product_id' in df.columns:
                            df['producto'] = df['product_id'].apply(
                                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                            )
                        resp = (
                            f"## Costo de Almacenamiento (Holding Cost)\n\n"
                            f"| Métrica | Valor |\n|---|---:|\n"
                            f"| 📦 SKUs en stock | **{n_skus:,}** |\n"
                            f"| 💰 Valor total inventario | **${valor_total:,.2f}** |\n"
                            f"| 📊 Tasa holding estimada | **{tasa_holding*100:.0f}% anual** |\n"
                            f"| 📅 **Costo anual estimado** | **${costo_anual:,.2f}** |\n"
                            f"| 📆 **Costo mensual estimado** | **${costo_mensual:,.2f}** |\n\n"
                            f"**Top 10 productos por costo de almacenamiento:**\n\n"
                            f"| Producto | Valor en stock | Costo anual holding |\n|---|---:|---:|\n"
                        )
                        for _, r in df.head(10).iterrows():
                            nombre = str(r.get('producto', str(r.get('product_id', ''))))[:35]
                            val = float(r.get('val', 0))
                            costo_prod = val * tasa_holding
                            resp += f"| {nombre} | ${val:,.2f} | ${costo_prod:,.2f} |\n"
                        resp += "\n> ⚠️ *Tasa 22% incluye: capital inmovilizado, seguro, espacio, obsolescencia y manejo.*"
                        return resp, df
            except Exception:
                pass
            datos = self.analizador.analisis_inventario()
            val = datos.get('valoracion', {}).get('total', 0) or 0
            return (
                f"## Costo de Almacenamiento\n\n"
                f"**Valor inventario:** ${val:,.2f}\n"
                f"**Costo holding anual (22%):** ${val * 0.22:,.2f}\n"
                f"**Costo mensual estimado:** ${val * 0.22 / 12:,.2f}", None
            )

        # ── trazabilidad_lote ─────────────────────────────────────────────────
        if accion == 'trazabilidad_lote':
            temp_t = getattr(consulta, 'temporalidad', {}) or {}
            fi_t = temp_t.get('fecha_inicio', '')
            ff_t = temp_t.get('fecha_fin', '')
            params_t = getattr(consulta, 'parametros', {}) or {}
            producto_filtro = params_t.get('producto', '')
            try:
                if self.odoo and self.odoo.conectado:
                    for modelo_lot in ('stock.lot', 'stock.production.lot'):
                        try:
                            filtro_t = []
                            if fi_t:
                                filtro_t.append(('create_date', '>=', fi_t))
                            if ff_t:
                                filtro_t.append(('create_date', '<=', ff_t))
                            if producto_filtro:
                                filtro_t.append(('product_id.name', 'ilike', producto_filtro))
                            df = self.odoo.buscar(
                                modelo_lot,
                                filtro=filtro_t,
                                campos=['name', 'product_id', 'create_date', 'ref'],
                                limite=200,
                                orden='create_date desc'
                            )
                            if df is not None and not df.empty:
                                df = df.copy()
                                if 'product_id' in df.columns:
                                    df['producto'] = df['product_id'].apply(
                                        lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                                    )
                                n = len(df)
                                resp = (
                                    f"## Trazabilidad de Lotes y Números de Serie\n\n"
                                    f"**Período:** {fi_t or 'histórico'} a {ff_t or 'hoy'}\n"
                                    f"**Total lotes/series:** {n:,}\n\n"
                                    f"| Lote/Serie | Producto | Fecha creación |\n|---|---|---|\n"
                                )
                                for _, r in df.head(20).iterrows():
                                    lote = str(r.get('name', ''))
                                    prod = str(r.get('producto', str(r.get('product_id', ''))))[:35]
                                    fecha = str(r.get('create_date', ''))[:10]
                                    resp += f"| {lote} | {prod} | {fecha} |\n"
                                if n > 20:
                                    resp += f"\n*...mostrando 20 de {n} registros*"
                                return resp, df
                        except Exception:
                            continue
            except Exception:
                pass
            return (
                "## Trazabilidad de Lotes\n\n"
                "El módulo de lotes no está habilitado o no hay registros.\n\n"
                "> 💡 *Activa el seguimiento en: Inventario → Configuración → Rastreabilidad*", None
            )

        # ── comparar_stock_fisico_sistema ─────────────────────────────────────
        if accion == 'comparar_stock_fisico_sistema':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'stock.quant',
                        filtro=[('location_id.usage', '=', 'internal')],
                        campos=['product_id', 'location_id', 'quantity', 'reserved_quantity', 'inventory_quantity_auto_apply'],
                        limite=500
                    )
                    if df is not None and not df.empty:
                        df = df.copy()
                        if 'product_id' in df.columns:
                            df['producto'] = df['product_id'].apply(
                                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                            )
                        df['qty'] = pd.to_numeric(df.get('quantity', 0), errors='coerce').fillna(0)
                        df['inv_qty'] = pd.to_numeric(df.get('inventory_quantity_auto_apply', 0), errors='coerce').fillna(0)
                        df['diferencia'] = df['inv_qty'] - df['qty']
                        discrepancias = df[df['diferencia'].abs() > 0.01].copy()
                        n_total = len(df)
                        n_disc = len(discrepancias)
                        resp = (
                            f"## Comparativa Stock Físico vs Sistema\n\n"
                            f"| Métrica | Valor |\n|---|---:|\n"
                            f"| 📦 Registros en inventario | **{n_total:,}** |\n"
                            f"| ⚠️ Con discrepancia | **{n_disc:,}** |\n"
                            f"| ✅ Sin diferencia | **{n_total - n_disc:,}** |\n\n"
                        )
                        if n_disc > 0:
                            resp += "**Discrepancias detectadas:**\n\n| Producto | Stock sistema | Stock físico | Diferencia |\n|---|---:|---:|---:|\n"
                            for _, r in discrepancias.reindex(discrepancias['diferencia'].abs().sort_values(ascending=False).index).head(15).iterrows():
                                prod = str(r.get('producto', str(r.get('product_id', ''))))[:35]
                                q_sis = float(r['qty'])
                                q_fis = float(r['inv_qty'])
                                diff = float(r['diferencia'])
                                emoji = "🔴" if abs(diff) > 10 else "🟡"
                                resp += f"| {prod} | {q_sis:,.0f} | {q_fis:,.0f} | {emoji} {diff:+.0f} |\n"
                            resp += "\n> ⚠️ *Realiza ajuste de inventario en Odoo para corregir las discrepancias.*"
                        else:
                            resp += "✅ No se detectaron discrepancias. El stock del sistema coincide."
                        return resp, discrepancias if n_disc > 0 else df
            except Exception:
                pass
            return (
                "## Comparativa Stock Físico vs Sistema\n\n"
                "Para una comparativa precisa realiza un inventario físico en Odoo.\n\n"
                "> 💡 *Ve a: Inventario → Operaciones → Inventario Físico*", None
            )

        # ── inventario_por_empresa ────────────────────────────────────────────
        if accion == 'inventario_por_empresa':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'stock.quant',
                        filtro=[('quantity', '>', 0), ('location_id.usage', '=', 'internal')],
                        campos=['product_id', 'company_id', 'quantity', 'value'],
                        limite=2000
                    )
                    if df is not None and not df.empty and 'company_id' in df.columns:
                        df = df.copy()
                        df['empresa'] = df['company_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['qty'] = pd.to_numeric(df.get('quantity', 0), errors='coerce').fillna(0)
                        df['valor'] = pd.to_numeric(df.get('value', 0), errors='coerce').fillna(0)
                        agg = df.groupby('empresa').agg(
                            registros=('qty', 'count'),
                            unidades=('qty', 'sum'),
                            valor=('valor', 'sum')
                        ).reset_index().sort_values('unidades', ascending=False)
                        total_uds = float(agg['unidades'].sum())
                        total_val = float(agg['valor'].sum())
                        resp = (
                            f"## Inventario por Empresa\n\n"
                            f"**{len(agg)} empresa(s)** | Unidades totales: **{total_uds:,.0f}** | Valor: **${total_val:,.2f}**\n\n"
                            f"| Empresa | Registros | Unidades | % | Valor |\n|---|---:|---:|---:|---:|\n"
                        )
                        for _, r in agg.iterrows():
                            pct = float(r['unidades']) / total_uds * 100 if total_uds > 0 else 0
                            resp += f"| {str(r['empresa'])[:35]} | {int(r['registros']):,} | {float(r['unidades']):,.0f} | {pct:.1f}% | ${float(r['valor']):,.2f} |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Inventario por Empresa\n\nNo se pudo obtener el desglose por empresa. Verifica la conexión con Odoo.", None

        # ── inventario_por_almacen ────────────────────────────────────────────
        if accion in ('inventario_por_almacen', 'inventario_por_tienda', 'inventario_por_ubicacion'):
            try:
                if self.odoo and self.odoo.conectado:
                    # limite=0 → sin límite: traer TODOS los quants (30+ almacenes)
                    df = self.odoo.buscar(
                        'stock.quant',
                        filtro=[('quantity', '>', 0), ('location_id.usage', '=', 'internal')],
                        campos=['product_id', 'location_id', 'quantity', 'value', 'company_id'],
                        limite=0,
                    )
                    if df is not None and not df.empty and 'location_id' in df.columns:
                        df = df.copy()

                        # Extraer nombre del almacén desde el path completo de la ubicación.
                        # Odoo devuelve location_id como (id, "Empresa / WH1 / Stock") o "WH/Stock".
                        # Se toma el primer segmento útil ignorando carpetas raíz genéricas.
                        _ROOTS = {
                            'physical locations', 'virtual locations', 'partner locations',
                            'ubicaciones físicas', 'ubicaciones virtuales', 'ubicaciones de socios',
                            'all', 'todos', 'todas las ubicaciones', 'all operations',
                        }

                        def _extraer_almacen(loc_val):
                            nombre = loc_val[1] if isinstance(loc_val, (list, tuple)) else str(loc_val)
                            partes = [p.strip() for p in nombre.replace(' / ', '/').split('/')]
                            utiles = [p for p in partes if p and p.lower() not in _ROOTS]
                            return utiles[0] if utiles else nombre

                        df['almacen'] = df['location_id'].apply(_extraer_almacen)
                        df['empresa'] = df['company_id'].apply(
                            lambda x: x[1] if isinstance(x, (list, tuple)) else 'N/A'
                        ) if 'company_id' in df.columns else 'N/A'
                        df['qty'] = pd.to_numeric(df.get('quantity', 0), errors='coerce').fillna(0)
                        df['valor'] = pd.to_numeric(df.get('value', 0), errors='coerce').fillna(0)

                        # Agrupación por empresa + almacén
                        agg = df.groupby(['empresa', 'almacen']).agg(
                            registros=('almacen', 'count'),
                            unidades=('qty', 'sum'),
                            valor=('valor', 'sum')
                        ).reset_index().sort_values(['empresa', 'unidades'], ascending=[True, False])

                        total_almacenes = agg['almacen'].nunique()
                        total_empresas = agg['empresa'].nunique()
                        total_registros = int(agg['registros'].sum())
                        total_unidades = float(agg['unidades'].sum())
                        total_valor = float(agg['valor'].sum())

                        resp = (
                            f"## Inventario por Almacén\n\n"
                            f"| Métrica | Valor |\n|---|---:|\n"
                            f"| 🏢 Empresas | **{total_empresas}** |\n"
                            f"| 🏭 Almacenes con stock | **{total_almacenes}** |\n"
                            f"| 📦 Registros de quant | **{total_registros:,}** |\n"
                            f"| 🔢 Unidades totales | **{total_unidades:,.0f}** |\n"
                            f"| 💰 Valor total | **${total_valor:,.2f}** |\n\n"
                        )

                        # Resumen por empresa
                        if total_empresas > 1:
                            agg_emp = df.groupby('empresa').agg(
                                almacenes=('almacen', 'nunique'),
                                unidades=('qty', 'sum'),
                                valor=('valor', 'sum')
                            ).reset_index().sort_values('unidades', ascending=False)
                            resp += "**Resumen por Empresa:**\n\n"
                            resp += "| Empresa | Almacenes | Unidades | % | Valor |\n|---|---:|---:|---:|---:|\n"
                            for _, r in agg_emp.iterrows():
                                pct = float(r['unidades']) / total_unidades * 100 if total_unidades > 0 else 0
                                resp += (
                                    f"| {str(r['empresa'])[:35]} | {int(r['almacenes'])} | "
                                    f"{float(r['unidades']):,.0f} | {pct:.1f}% | "
                                    f"${float(r['valor']):,.2f} |\n"
                                )
                            resp += "\n"

                        # Desglose completo por almacén
                        resp += "**Desglose por Almacén:**\n\n"
                        resp += "| Empresa | Almacén | Registros | Unidades | % | Valor |\n|---|---|---:|---:|---:|---:|\n"
                        for _, r in agg.iterrows():
                            pct = float(r['unidades']) / total_unidades * 100 if total_unidades > 0 else 0
                            resp += (
                                f"| {str(r['empresa'])[:25]} | {str(r['almacen'])[:30]} | "
                                f"{int(r['registros']):,} | {float(r['unidades']):,.0f} | "
                                f"{pct:.1f}% | ${float(r['valor']):,.2f} |\n"
                            )

                        # Top 5 productos del almacén con más unidades
                        top_row = agg.sort_values('unidades', ascending=False).iloc[0]
                        top_almacen = top_row['almacen']
                        top_prod = df[df['almacen'] == top_almacen].copy()
                        if not top_prod.empty and 'product_id' in top_prod.columns:
                            top_prod['producto'] = top_prod['product_id'].apply(
                                lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                            )
                            top_5 = top_prod.groupby('producto')['qty'].sum().nlargest(5).reset_index()
                            if not top_5.empty:
                                resp += f"\n**Top 5 productos en {str(top_almacen)[:30]}:**\n\n"
                                resp += "| Producto | Unidades |\n|---|---:|\n"
                                for _, r in top_5.iterrows():
                                    resp += f"| {str(r['producto'])[:45]} | {float(r['qty']):,.0f} |\n"

                        return resp, agg
            except Exception:
                pass
            return (
                "## Inventario por Almacén\n\n"
                "No se pudo obtener el desglose por almacén. Verifica la conexión con Odoo.\n\n"
                "> 💡 *El módulo de Inventario debe estar instalado y configurado.*", None
            )

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_finanzas(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        temp = getattr(consulta, 'temporalidad', {}) or {}
        fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')

        if accion == 'rentabilidad_cliente':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            if 'por_cliente' in datos and datos['por_cliente']:
                df = pd.DataFrame(datos['por_cliente'])
                if 'total' in df.columns:
                    df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
                    total_general = float(df['total'].sum())
                    df_sorted = df.sort_values('total', ascending=False)
                    resp = (
                        f"## Rentabilidad por Cliente\n\n"
                        f"**Período:** {fi} a {ff} | **{len(df):,} clientes** | **Total: ${total_general:,.2f}**\n\n"
                        f"| # | Cliente | Ventas | % \n|---|---|---:|---:|\n"
                    )
                    for i, (_, r) in enumerate(df_sorted.head(15).iterrows(), 1):
                        nombre = str(r.get('cliente', r.get('nombre', r.get('name', ''))))[:35]
                        ventas = float(r.get('total', 0))
                        pct = ventas / total_general * 100 if total_general > 0 else 0
                        resp += f"| {i} | {nombre} | ${ventas:,.2f} | {pct:.1f}% |\n"
                    return resp, df_sorted
                return f"## Rentabilidad por Cliente\n\n**Período:** {fi} a {ff}\n\n", df

        if accion == 'dias_cobro_promedio':
            datos = self.analizador.cuentas_por_cobrar()
            if 'por_antiguedad' in datos:
                resp = "## DSO — Días de Cobro Promedio\n\n"
                for rango, info in datos['por_antiguedad'].items():
                    resp += f"- **{rango}:** ${info.get('monto', 0):,.2f} ({info.get('cantidad', 0)} facturas)\n"
                df = pd.DataFrame(datos.get('por_cliente', []))
                return resp, df

        if accion == 'dias_pago_promedio':
            datos = self.analizador.cuentas_por_pagar()
            if 'por_antiguedad' in datos:
                resp = "## DPO — Días de Pago Promedio\n\n"
                for rango, info in datos['por_antiguedad'].items():
                    resp += f"- **{rango}:** ${info.get('monto', 0):,.2f} ({info.get('cantidad', 0)} facturas)\n"
                df = pd.DataFrame(datos.get('por_proveedor', []))
                return resp, df

        if accion == 'facturacion_por_empresa':
            try:
                if self.odoo and self.odoo.conectado:
                    df_fac = self.odoo.buscar(
                        'account.move',
                        filtro=[('move_type', 'in', ['out_invoice', 'out_refund']),
                                ('state', '=', 'posted')]
                            + ([('invoice_date', '>=', fi)] if fi else [])
                            + ([('invoice_date', '<=', ff)] if ff else []),
                        campos=['company_id', 'amount_total', 'move_type'],
                        limite=2000
                    )
                    if df_fac is not None and not df_fac.empty:
                        df_fac['empresa'] = df_fac['company_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df_fac['monto'] = pd.to_numeric(df_fac['amount_total'], errors='coerce').fillna(0)
                        # Facturas positivas, notas crédito negativas
                        df_fac.loc[df_fac['move_type'] == 'out_refund', 'monto'] *= -1
                        agg = df_fac.groupby('empresa').agg(facturas=('monto', 'count'), total=('monto', 'sum')).reset_index().sort_values('total', ascending=False)
                        total_gen = float(agg['total'].sum())
                        resp = (
                            f"## Facturación por Empresa\n\n"
                            f"**Período:** {fi or 'histórico'} a {ff or 'hoy'} | **Total: ${total_gen:,.2f}**\n\n"
                            f"| Empresa | Facturas | Total | % |\n|---|---:|---:|---:|\n"
                        )
                        for _, r in agg.iterrows():
                            pct = float(r['total']) / total_gen * 100 if total_gen else 0
                            resp += f"| {str(r['empresa'])[:35]} | {int(r['facturas'])} | ${float(r['total']):,.2f} | {pct:.1f}% |\n"
                        return resp, agg
            except Exception:
                pass
            if self.consultas_esp:
                datos = self.consultas_esp.empresas_resumen()
                if 'error' not in datos and datos.get('empresas'):
                    df = pd.DataFrame(datos['empresas'])
                    resp = "## Facturación por Empresa\n\nNo hay datos de facturas disponibles.\n"
                    return resp, df

        # ── facturas_filtradas ───────────────────────────────────────────────
        if accion == 'facturas_filtradas':
            datos = self.analizador.analisis_facturacion(fi, ff)
            resumen = datos.get('resumen', {})
            total = resumen.get('total_facturado', 0)
            por_estado = datos.get('por_estado', [])
            resp = (
                f"## Facturas Filtradas\n\n"
                f"**Período:** {fi} a {ff}\n\n"
                f"| Métrica | Valor |\n|---|---:|\n"
                f"| 💰 Total facturado | **${total:,.2f}** |\n"
            )
            if por_estado:
                df = pd.DataFrame(por_estado)
                if 'estado' in df.columns and 'total' in df.columns:
                    for _, r in df.iterrows():
                        resp += f"| {r['estado']} | ${float(r['total']):,.2f} |\n"
            else:
                df = None
            return resp, df

        # ── consultar_pagos ──────────────────────────────────────────────────
        if accion == 'consultar_pagos':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', '=', 'posted'), ('payment_type', 'in', ['inbound', 'outbound'])]
                    if fi:
                        filtro.append(('date', '>=', fi))
                    if ff:
                        filtro.append(('date', '<=', ff))
                    df = self.odoo.buscar(
                        'account.payment',
                        filtro=filtro,
                        campos=['name', 'partner_id', 'amount', 'payment_type', 'date', 'journal_id'],
                        limite=300
                    )
                    if df is not None and not df.empty:
                        df['monto'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
                        entrantes = df[df['payment_type'] == 'inbound']['monto'].sum() if 'payment_type' in df.columns else 0
                        salientes = df[df['payment_type'] == 'outbound']['monto'].sum() if 'payment_type' in df.columns else 0
                        resp = (
                            f"## Pagos del Período\n\n"
                            f"**Período:** {fi} a {ff}\n\n"
                            f"| Tipo | Total |\n|---|---:|\n"
                            f"| 💚 Pagos recibidos | **${entrantes:,.2f}** |\n"
                            f"| 🔴 Pagos realizados | **${salientes:,.2f}** |\n"
                            f"| 📊 Flujo neto | **${entrantes - salientes:,.2f}** |\n\n"
                            f"**Total transacciones:** {len(df):,}\n"
                        )
                        return resp, df
            except Exception:
                pass
            return "## Pagos\n\nNo se encontraron pagos registrados en Odoo para el período.", None

        # ── conciliacion_bancaria ─────────────────────────────────────────────
        if accion == 'conciliacion_bancaria':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', 'in', ['posted', 'confirmed'])]
                    if fi:
                        filtro.append(('date', '>=', fi))
                    if ff:
                        filtro.append(('date', '<=', ff))
                    df = self.odoo.buscar(
                        'account.bank.statement.line', filtro=filtro,
                        campos=['date', 'payment_ref', 'amount', 'is_reconciled', 'partner_id'],
                        limite=300
                    )
                    if df is not None and not df.empty:
                        df['monto'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
                        reconciled = df[df.get('is_reconciled', pd.Series([False] * len(df), index=df.index)) == True]
                        pending = df[df.get('is_reconciled', pd.Series([True] * len(df), index=df.index)) != True]
                        resp = (
                            f"## Conciliación Bancaria\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Estado | Movimientos | Importe |\n|---|---:|---:|\n"
                            f"| ✅ Conciliados | {len(reconciled):,} | ${float(reconciled['monto'].sum()):,.2f} |\n"
                            f"| ⏳ Pendientes | {len(pending):,} | ${float(pending['monto'].sum()):,.2f} |\n"
                            f"| **Total** | **{len(df):,}** | **${float(df['monto'].sum()):,.2f}** |\n\n"
                        )
                        if len(pending) > 0:
                            resp += f"⚠️ **{len(pending)} movimientos** sin conciliar. Revisar para cerrar período contable.\n"
                        return resp, df
            except Exception:
                pass
            return "## Conciliación Bancaria\n\nMódulo de extractos bancarios no disponible o sin movimientos en el período.", None

        # ── analisis_antiguedad ───────────────────────────────────────────────
        if accion == 'analisis_antiguedad':
            try:
                if self.odoo and self.odoo.conectado:
                    from datetime import date as _dt_date
                    hoy_ant = _dt_date.today()
                    filtro = [('move_type', 'in', ['out_invoice', 'in_invoice']), ('payment_state', '!=', 'paid'), ('state', '=', 'posted')]
                    df = self.odoo.buscar(
                        'account.move', filtro=filtro,
                        campos=['partner_id', 'invoice_date_due', 'amount_residual', 'move_type', 'name'],
                        limite=500
                    )
                    if df is not None and not df.empty:
                        df['fecha_venc'] = pd.to_datetime(df['invoice_date_due'], errors='coerce')
                        df['monto'] = pd.to_numeric(df['amount_residual'], errors='coerce').fillna(0)
                        hoy_ts = pd.Timestamp(hoy_ant)
                        df['dias_vencido'] = (hoy_ts - df['fecha_venc']).dt.days.fillna(0).astype(int)
                        r1 = float(df[df['dias_vencido'] <= 0]['monto'].sum())
                        r2 = float(df[(df['dias_vencido'] > 0) & (df['dias_vencido'] <= 30)]['monto'].sum())
                        r3 = float(df[(df['dias_vencido'] > 30) & (df['dias_vencido'] <= 60)]['monto'].sum())
                        r4 = float(df[(df['dias_vencido'] > 60) & (df['dias_vencido'] <= 90)]['monto'].sum())
                        r5 = float(df[df['dias_vencido'] > 90]['monto'].sum())
                        resp = (
                            f"## Análisis de Antigüedad de Cartera\n\n"
                            f"| Rango | Saldo Pendiente |\n|---|---:|\n"
                            f"| ✅ No vencido | ${r1:,.2f} |\n"
                            f"| 🟡 1-30 días vencido | ${r2:,.2f} |\n"
                            f"| 🟠 31-60 días | ${r3:,.2f} |\n"
                            f"| 🔴 61-90 días | ${r4:,.2f} |\n"
                            f"| 🚨 +90 días | **${r5:,.2f}** |\n"
                            f"| **Total** | **${float(df['monto'].sum()):,.2f}** |\n\n"
                        )
                        if r5 > 0:
                            resp += "⚠️ **Facturas con +90 días**: considerar provisión para cuentas incobrables.\n"
                        return resp, df
            except Exception:
                pass
            return "## Análisis de Antigüedad\n\nNo se encontraron facturas pendientes en Odoo.", None

        # ── notas_credito ─────────────────────────────────────────────────────
        if accion == 'notas_credito':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('move_type', 'in', ['out_refund', 'in_refund']), ('state', '=', 'posted')]
                    if fi:
                        filtro.append(('invoice_date', '>=', fi))
                    if ff:
                        filtro.append(('invoice_date', '<=', ff))
                    df = self.odoo.buscar(
                        'account.move', filtro=filtro,
                        campos=['name', 'partner_id', 'amount_total', 'invoice_date', 'move_type'],
                        limite=200
                    )
                    if df is not None and not df.empty:
                        df['monto'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        mask_cli = df.get('move_type', pd.Series()) == 'out_refund'
                        clientes_nc = df[mask_cli]
                        provs_nc = df[~mask_cli]
                        resp = (
                            f"## Notas de Crédito\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Tipo | Cantidad | Importe |\n|---|---:|---:|\n"
                            f"| 🔄 A clientes (NC ventas) | {len(clientes_nc):,} | ${float(clientes_nc['monto'].sum()):,.2f} |\n"
                            f"| 📥 De proveedores | {len(provs_nc):,} | ${float(provs_nc['monto'].sum()):,.2f} |\n"
                            f"| **Total** | **{len(df):,}** | **${float(df['monto'].sum()):,.2f}** |\n\n"
                            f"| # | Folio | Contraparte | Monto |\n|---|---|---|---:|\n"
                        )
                        for i, (_, r) in enumerate(df.head(10).iterrows(), 1):
                            cp = r.get('partner_id', '')
                            cp_n = (cp[1] if isinstance(cp, (list, tuple)) else str(cp))[:25]
                            resp += f"| {i} | {r.get('name', '')} | {cp_n} | ${float(r['monto']):,.2f} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Notas de Crédito\n\nNo se encontraron notas de crédito en el período.", None

        # ── impuestos_resumen ─────────────────────────────────────────────────
        if accion == 'impuestos_resumen':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('tax_line_id', '!=', False), ('move_id.state', '=', 'posted')]
                    if fi:
                        filtro.append(('move_id.invoice_date', '>=', fi))
                    if ff:
                        filtro.append(('move_id.invoice_date', '<=', ff))
                    df = self.odoo.buscar(
                        'account.move.line', filtro=filtro,
                        campos=['tax_line_id', 'balance'], limite=1000
                    )
                    if df is not None and not df.empty:
                        df['impuesto'] = df['tax_line_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['balance'] = pd.to_numeric(df['balance'], errors='coerce').fillna(0)
                        agg = df.groupby('impuesto')['balance'].sum().reset_index().sort_values('balance', ascending=False)
                        resp = f"## Resumen de Impuestos\n\n**Período:** {fi} a {ff}\n\n| Impuesto | Importe |\n|---|---:|\n"
                        for _, r in agg.iterrows():
                            resp += f"| {r['impuesto']} | ${abs(float(r['balance'])):,.2f} |\n"
                        resp += f"\n**Total impuestos:** ${abs(float(agg['balance'].sum())):,.2f}\n"
                        return resp, agg
            except Exception:
                pass
            return "## Impuestos\n\nNo se encontraron líneas de impuesto en el período.", None

        # ── margen_operativo ──────────────────────────────────────────────────
        if accion == 'margen_operativo':
            datos_mo = self.analizador.analisis_ventas_completo(fi, ff)
            ventas_mo = datos_mo.get('resumen', {}).get('total_ventas', 0)
            costo_est = ventas_mo * 0.65
            gastos_op = ventas_mo * 0.15
            util_op = ventas_mo - costo_est - gastos_op
            margen_op = util_op / ventas_mo * 100 if ventas_mo > 0 else 0
            emoji_mo = "🟢" if margen_op > 15 else "🟡" if margen_op > 5 else "🔴"
            resp = (
                f"## Margen Operativo\n\n**Período:** {fi} a {ff}\n\n"
                f"| Concepto | Valor | % |\n|---|---:|---:|\n"
                f"| 💰 Ingresos | **${ventas_mo:,.2f}** | 100% |\n"
                f"| 🏭 Costo ventas (est. 65%) | -${costo_est:,.2f} | -65% |\n"
                f"| 🏢 Gastos operativos (est. 15%) | -${gastos_op:,.2f} | -15% |\n"
                f"| 📊 Utilidad operativa | **${util_op:,.2f}** | **{margen_op:.1f}%** |\n\n"
                f"**Margen operativo: {emoji_mo} {margen_op:.1f}%**\n\n"
                "> ⚠️ *Costos estimados. Para exactitud usa contabilidad analítica en Odoo.*"
            )
            return resp, None

        # ── razon_liquidez ────────────────────────────────────────────────────
        if accion == 'razon_liquidez':
            datos_rl = self.analizador.analisis_facturacion(fi, ff)
            cxc = datos_rl.get('resumen', {}).get('total_cxc', datos_rl.get('resumen', {}).get('pendiente', 0)) or 0
            datos_comp = self.analizador.analisis_compras(fi, ff)
            cxp = datos_comp.get('resumen', {}).get('pendiente', 0) or 0
            try:
                inv_rl = self.analizador.analisis_inventario()
                inv_val = inv_rl.get('valoracion', {}).get('total', 0) or 0
            except Exception:
                inv_val = 0
            activo_c = cxc + inv_val
            razon_l = activo_c / cxp if cxp > 0 else 0
            emoji_rl = "🟢" if razon_l >= 2 else "🟡" if razon_l >= 1 else "🔴"
            resp = (
                f"## Razón de Liquidez\n\n**Período:** {fi} a {ff}\n\n"
                f"| Componente | Valor |\n|---|---:|\n"
                f"| 📋 CxC (activo corriente) | **${cxc:,.2f}** |\n"
                f"| 📦 Inventario | **${inv_val:,.2f}** |\n"
                f"| 💳 CxP (pasivo corriente) | **${cxp:,.2f}** |\n"
                f"| 🎯 **Razón de liquidez** | **{emoji_rl} {razon_l:.2f}x** |\n\n"
                f"| Razón | Interpretación |\n|---|---|\n"
                f"| ≥ 2.0 | 🟢 Solvente |\n| 1.0–2.0 | 🟡 Aceptable |\n| < 1.0 | 🔴 Riesgo |\n"
            )
            return resp, None

        # ── capital_trabajo ───────────────────────────────────────────────────
        if accion == 'capital_trabajo':
            datos_ct = self.analizador.analisis_facturacion(fi, ff)
            cxc_ct = datos_ct.get('resumen', {}).get('total_cxc', datos_ct.get('resumen', {}).get('pendiente', 0)) or 0
            datos_comp_ct = self.analizador.analisis_compras(fi, ff)
            cxp_ct = datos_comp_ct.get('resumen', {}).get('pendiente', 0) or 0
            try:
                inv_ct = self.analizador.analisis_inventario()
                inv_val_ct = inv_ct.get('valoracion', {}).get('total', 0) or 0
            except Exception:
                inv_val_ct = 0
            capital_neto = (cxc_ct + inv_val_ct) - cxp_ct
            emoji_ct = "🟢" if capital_neto > 0 else "🔴"
            resp = (
                f"## Capital de Trabajo Neto\n\n**Período:** {fi} a {ff}\n\n"
                f"**Fórmula:** CTN = (CxC + Inventario) − CxP\n\n"
                f"| Componente | Valor |\n|---|---:|\n"
                f"| 📋 Cuentas por cobrar | **${cxc_ct:,.2f}** |\n"
                f"| 📦 Inventario | **${inv_val_ct:,.2f}** |\n"
                f"| 💳 Cuentas por pagar | **${cxp_ct:,.2f}** |\n"
                f"| 🎯 **Capital de trabajo neto** | **{emoji_ct} ${capital_neto:,.2f}** |\n\n"
                f"{'🔴 **Alerta:** Capital negativo indica riesgo de iliquidez operativa.' if capital_neto < 0 else '🟢 Liquidez operativa positiva.'}"
            )
            return resp, None

        # ── pagos_pendientes_aplicar ──────────────────────────────────────────
        if accion == 'pagos_pendientes_aplicar':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'account.payment',
                        filtro=[('state', '=', 'posted'), ('reconciled_invoice_ids', '=', False)],
                        campos=['name', 'partner_id', 'amount', 'date', 'payment_type'],
                        limite=200
                    )
                    if df is not None and not df.empty:
                        df['monto'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
                        resp = (
                            f"## Pagos Pendientes de Aplicar\n\n"
                            f"**{len(df):,} pagos** registrados sin aplicar a facturas:\n\n"
                            f"| Referencia | Contraparte | Monto | Fecha |\n|---|---|---:|---|\n"
                        )
                        for _, r in df.head(15).iterrows():
                            cp = r.get('partner_id', '')
                            cp_n = (cp[1] if isinstance(cp, (list, tuple)) else str(cp))[:25]
                            resp += f"| {r.get('name', '')} | {cp_n} | ${float(r['monto']):,.2f} | {str(r.get('date', ''))[:10]} |\n"
                        resp += f"\n**Total sin aplicar:** ${float(df['monto'].sum()):,.2f}\n"
                        return resp, df
            except Exception:
                pass
            return "## Pagos Pendientes de Aplicar\n\nNo se encontraron pagos pendientes de conciliar.", None

        # ── estado_cuenta_cliente ─────────────────────────────────────────────
        if accion == 'estado_cuenta_cliente':
            try:
                if self.odoo and self.odoo.conectado:
                    params_ec = getattr(consulta, 'parametros', {}) or {}
                    cliente = params_ec.get('cliente', params_ec.get('partner', ''))
                    filtro = [('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted')]
                    if cliente:
                        filtro.append(('partner_id.name', 'ilike', cliente))
                    if fi:
                        filtro.append(('invoice_date', '>=', fi))
                    if ff:
                        filtro.append(('invoice_date', '<=', ff))
                    df = self.odoo.buscar(
                        'account.move', filtro=filtro,
                        campos=['name', 'partner_id', 'amount_total', 'amount_residual', 'invoice_date', 'payment_state'],
                        limite=100
                    )
                    if df is not None and not df.empty:
                        df['total'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        df['pendiente'] = pd.to_numeric(df['amount_residual'], errors='coerce').fillna(0)
                        sufijo = f" | **Cliente:** {cliente}" if cliente else ""
                        resp = (
                            f"## Estado de Cuenta — Clientes\n\n**Período:** {fi} a {ff}{sufijo}\n\n"
                            f"| Factura | Cliente | Total | Pendiente | Estado |\n|---|---|---:|---:|---|\n"
                        )
                        for _, r in df.head(20).iterrows():
                            cp = r.get('partner_id', '')
                            cp_n = (cp[1] if isinstance(cp, (list, tuple)) else str(cp))[:25]
                            estado = r.get('payment_state', 'not_paid')
                            emoji_e = "✅" if estado == 'paid' else "⏳" if estado == 'partial' else "🔴"
                            resp += f"| {r.get('name', '')} | {cp_n} | ${float(r['total']):,.2f} | ${float(r['pendiente']):,.2f} | {emoji_e} |\n"
                        resp += f"\n**Total facturado:** ${float(df['total'].sum()):,.2f} | **Pendiente:** ${float(df['pendiente'].sum()):,.2f}"
                        return resp, df
            except Exception:
                pass
            return "## Estado de Cuenta Clientes\n\nNo se encontraron facturas de clientes en el período.", None

        # ── estado_cuenta_proveedor ───────────────────────────────────────────
        if accion == 'estado_cuenta_proveedor':
            try:
                if self.odoo and self.odoo.conectado:
                    params_ep = getattr(consulta, 'parametros', {}) or {}
                    proveedor = params_ep.get('proveedor', params_ep.get('partner', ''))
                    filtro = [('move_type', 'in', ['in_invoice', 'in_refund']), ('state', '=', 'posted')]
                    if proveedor:
                        filtro.append(('partner_id.name', 'ilike', proveedor))
                    if fi:
                        filtro.append(('invoice_date', '>=', fi))
                    if ff:
                        filtro.append(('invoice_date', '<=', ff))
                    df = self.odoo.buscar(
                        'account.move', filtro=filtro,
                        campos=['name', 'partner_id', 'amount_total', 'amount_residual', 'invoice_date', 'payment_state'],
                        limite=100
                    )
                    if df is not None and not df.empty:
                        df['total'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        df['pendiente'] = pd.to_numeric(df['amount_residual'], errors='coerce').fillna(0)
                        sufijo_p = f" | **Proveedor:** {proveedor}" if proveedor else ""
                        resp = (
                            f"## Estado de Cuenta — Proveedores\n\n**Período:** {fi} a {ff}{sufijo_p}\n\n"
                            f"| Factura | Proveedor | Total | Pendiente | Estado |\n|---|---|---:|---:|---|\n"
                        )
                        for _, r in df.head(20).iterrows():
                            cp = r.get('partner_id', '')
                            cp_n = (cp[1] if isinstance(cp, (list, tuple)) else str(cp))[:25]
                            estado = r.get('payment_state', 'not_paid')
                            emoji_e = "✅" if estado == 'paid' else "⏳" if estado == 'partial' else "🔴"
                            resp += f"| {r.get('name', '')} | {cp_n} | ${float(r['total']):,.2f} | ${float(r['pendiente']):,.2f} | {emoji_e} |\n"
                        resp += f"\n**Total a pagar:** ${float(df['total'].sum()):,.2f} | **Pendiente:** ${float(df['pendiente'].sum()):,.2f}"
                        return resp, df
            except Exception:
                pass
            return "## Estado de Cuenta Proveedores\n\nNo se encontraron facturas de proveedores en el período.", None

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_crm(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        temp = getattr(consulta, 'temporalidad', {}) or {}
        fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')

        if accion in ('pipeline_etapas', 'valor_pipeline', 'oportunidades_por_vendedor'):
            datos = self.analizador.analisis_crm_pipeline()
            resp = self.analizador.formatear_analisis_md('crm', datos)
            if accion == 'oportunidades_por_vendedor' and 'por_vendedor' in datos:
                df = pd.DataFrame(datos['por_vendedor'])
            elif 'por_etapa' in datos:
                df = pd.DataFrame(datos['por_etapa'])
            else:
                df = None
            return resp, df

        # ── consultar_crm ────────────────────────────────────────────────────
        if accion == 'consultar_crm':
            datos = self.analizador.analisis_crm_pipeline()
            if 'error' not in datos:
                resumen = datos.get('resumen', {})
                por_etapa = datos.get('por_etapa', [])
                resp = (
                    f"## Estado del CRM\n\n"
                    f"| Métrica | Valor |\n|---|---:|\n"
                    f"| 📋 Oportunidades totales | **{resumen.get('total', 0):,}** |\n"
                    f"| 💰 Valor pipeline | **${resumen.get('valor_total', 0):,.2f}** |\n"
                    f"| 🏆 Ganadas | **{resumen.get('ganadas', 0)}** |\n"
                    f"| ❌ Perdidas | **{resumen.get('perdidas', 0)}** |\n\n"
                )
                if por_etapa:
                    df = pd.DataFrame(por_etapa)
                    resp += "**Por etapa del pipeline:**\n\n| Etapa | Oportunidades | Valor |\n|---|---:|---:|\n"
                    for _, r in df.iterrows():
                        resp += f"| {r.get('etapa', '')} | {r.get('count', r.get('cantidad', 0))} | ${float(r.get('valor', r.get('total', 0))):,.2f} |\n"
                    return resp, df
                return resp, None
            return "CRM no disponible o sin oportunidades.", None

        # ── prediccion_churn ─────────────────────────────────────────────────
        if accion == 'prediccion_churn':
            temp_l = getattr(consulta, 'temporalidad', {}) or {}
            fi_l, ff_l = temp_l.get('fecha_inicio', ''), temp_l.get('fecha_fin', '')
            datos = self.analizador.analisis_ventas_completo(fi_l, ff_l)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            resp = f"## Predicción de Churn (Abandono de Clientes)\n\n"
            if df is not None and not df.empty and 'total' in df.columns:
                col = pd.to_numeric(df['total'], errors='coerce').fillna(0)
                p20 = float(col.quantile(0.20))
                en_riesgo = int((col < p20).sum())
                resp += (
                    f"**Clientes analizados:** {len(df):,}\n\n"
                    f"| Segmento | Clientes | Señal |\n|---|---:|---:|\n"
                    f"| 🔴 Alto riesgo churn (<P20) | {en_riesgo} | Compra baja/nula |\n"
                    f"| 🟡 Riesgo medio (P20-P50) | {int(col.between(p20, col.median()).sum())} | Actividad reducida |\n"
                    f"| 🟢 Sin riesgo (>P50) | {int((col > col.median()).sum())} | Activos |\n\n"
                    f"> 💡 *Para churn predictivo con ML se requiere historial de al menos 12 meses y módulo CRM activo.*"
                )
            else:
                resp += "No hay suficientes datos de clientes para calcular riesgo de churn."
            return resp, df

        # ── conversion_leads ──────────────────────────────────────────────────
        if accion == 'conversion_leads':
            try:
                if self.odoo and self.odoo.conectado:
                    df_leads = self.odoo.buscar(
                        'crm.lead', filtro=[('type', '=', 'lead')],
                        campos=['name', 'stage_id', 'probability'], limite=1000
                    )
                    df_won = self.odoo.buscar(
                        'crm.lead',
                        filtro=[('type', '=', 'opportunity'), ('stage_id.is_won', '=', True)],
                        campos=['name', 'expected_revenue'], limite=1000
                    )
                    total_leads = len(df_leads) if df_leads is not None else 0
                    total_won = len(df_won) if df_won is not None else 0
                    tasa_conv = total_won / total_leads * 100 if total_leads > 0 else 0
                    emoji_cl = "🟢" if tasa_conv >= 25 else "🟡" if tasa_conv >= 10 else "🔴"
                    resp = (
                        f"## Tasa de Conversión de Leads\n\n"
                        f"| Métrica | Valor |\n|---|---:|\n"
                        f"| 📥 Leads totales | **{total_leads:,}** |\n"
                        f"| 🏆 Oportunidades ganadas | **{total_won:,}** |\n"
                        f"| 🎯 Tasa de conversión | **{tasa_conv:.1f}%** |\n\n"
                        f"**Nivel:** {emoji_cl} {'Excelente' if tasa_conv >= 25 else 'Aceptable' if tasa_conv >= 10 else 'Bajo — revisar proceso de ventas'}\n"
                    )
                    return resp, df_leads if df_leads is not None else None
            except Exception:
                pass
            return "## Conversión de Leads\n\nMódulo CRM no disponible o sin leads registrados.", None

        # ── actividades_pendientes ────────────────────────────────────────────
        if accion == 'actividades_pendientes':
            try:
                if self.odoo and self.odoo.conectado:
                    from datetime import date as _dt_crm
                    hoy_crm = str(_dt_crm.today())
                    df = self.odoo.buscar(
                        'mail.activity',
                        filtro=[('date_deadline', '<=', hoy_crm),
                                ('res_model', 'in', ['crm.lead', 'res.partner', 'sale.order'])],
                        campos=['res_name', 'activity_type_id', 'date_deadline', 'user_id', 'summary'],
                        limite=200
                    )
                    if df is not None and not df.empty:
                        resp = (
                            f"## Actividades CRM Pendientes\n\n"
                            f"**{len(df):,} actividades** vencidas o por vencer:\n\n"
                            f"| Registro | Tipo | Vencimiento | Responsable |\n|---|---|---|---|\n"
                        )
                        for _, r in df.head(15).iterrows():
                            tipo = r.get('activity_type_id', '')
                            tipo_n = tipo[1] if isinstance(tipo, (list, tuple)) else str(tipo)
                            user = r.get('user_id', '')
                            user_n = (user[1] if isinstance(user, (list, tuple)) else str(user))[:20]
                            resp += f"| {str(r.get('res_name', ''))[:30]} | {tipo_n} | {str(r.get('date_deadline', ''))[:10]} | {user_n} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Actividades Pendientes\n\nNo se encontraron actividades vencidas en CRM.", None

        # ── oportunidades_estancadas ──────────────────────────────────────────
        if accion == 'oportunidades_estancadas':
            try:
                if self.odoo and self.odoo.conectado:
                    from datetime import date as _dt_crm2, timedelta
                    umbral_oe = (_dt_crm2.today() - timedelta(days=30)).strftime('%Y-%m-%d')
                    df = self.odoo.buscar(
                        'crm.lead',
                        filtro=[('type', '=', 'opportunity'), ('stage_id.is_won', '=', False),
                                ('stage_id.probability', '<', 100), ('write_date', '<=', umbral_oe)],
                        campos=['name', 'partner_id', 'stage_id', 'expected_revenue', 'user_id', 'write_date'],
                        limite=100
                    )
                    if df is not None and not df.empty:
                        resp = (
                            f"## Oportunidades Estancadas (sin actividad >30 días)\n\n"
                            f"**{len(df):,} oportunidades** sin actualización reciente:\n\n"
                            f"| Oportunidad | Cliente | Etapa | Revenue esp. | Responsable |\n|---|---|---|---:|---|\n"
                        )
                        for _, r in df.head(15).iterrows():
                            cp = r.get('partner_id', '')
                            cp_n = (cp[1] if isinstance(cp, (list, tuple)) else str(cp))[:20]
                            etapa = r.get('stage_id', '')
                            etapa_n = etapa[1] if isinstance(etapa, (list, tuple)) else str(etapa)
                            user = r.get('user_id', '')
                            user_n = (user[1] if isinstance(user, (list, tuple)) else str(user))[:15]
                            rev = float(r.get('expected_revenue', 0))
                            resp += f"| {str(r.get('name', ''))[:30]} | {cp_n} | {etapa_n} | ${rev:,.2f} | {user_n} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Oportunidades Estancadas\n\nNo se encontraron oportunidades sin actividad reciente.", None

        # ── win_rate ──────────────────────────────────────────────────────────
        if accion == 'win_rate':
            try:
                if self.odoo and self.odoo.conectado:
                    df_won_wr = self.odoo.buscar(
                        'crm.lead', filtro=[('stage_id.is_won', '=', True)],
                        campos=['name', 'expected_revenue'], limite=1000
                    )
                    df_lost_wr = self.odoo.buscar(
                        'crm.lead', filtro=[('active', '=', False), ('probability', '=', 0)],
                        campos=['name'], limite=1000
                    )
                    ganadas_wr = len(df_won_wr) if df_won_wr is not None else 0
                    perdidas_wr = len(df_lost_wr) if df_lost_wr is not None else 0
                    total_cerradas = ganadas_wr + perdidas_wr
                    wr = ganadas_wr / total_cerradas * 100 if total_cerradas > 0 else 0
                    ingresos_g = float(pd.to_numeric(df_won_wr['expected_revenue'], errors='coerce').sum()) if df_won_wr is not None and not df_won_wr.empty else 0
                    emoji_wr = "🟢" if wr >= 40 else "🟡" if wr >= 20 else "🔴"
                    resp = (
                        f"## Win Rate (Tasa de Cierre)\n\n"
                        f"| Métrica | Valor |\n|---|---:|\n"
                        f"| 🏆 Ganadas | **{ganadas_wr:,}** |\n"
                        f"| ❌ Perdidas | **{perdidas_wr:,}** |\n"
                        f"| 📊 Total cerradas | **{total_cerradas:,}** |\n"
                        f"| 🎯 **Win Rate** | **{wr:.1f}%** |\n"
                        f"| 💰 Ingresos ganados | **${ingresos_g:,.2f}** |\n\n"
                        f"**Nivel:** {emoji_wr} {'Alto' if wr >= 40 else 'Medio' if wr >= 20 else 'Bajo — revisar propuesta de valor'}\n"
                    )
                    return resp, df_won_wr
            except Exception:
                pass
            return "## Win Rate\n\nMódulo CRM sin oportunidades cerradas registradas.", None

        # ── tiempo_cierre_promedio ────────────────────────────────────────────
        if accion == 'tiempo_cierre_promedio':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'crm.lead',
                        filtro=[('stage_id.is_won', '=', True), ('date_closed', '!=', False)],
                        campos=['name', 'date_closed', 'create_date', 'expected_revenue'],
                        limite=200
                    )
                    if df is not None and not df.empty:
                        df['fecha_cierre'] = pd.to_datetime(df['date_closed'], errors='coerce')
                        df['fecha_creacion'] = pd.to_datetime(df['create_date'], errors='coerce')
                        df['dias_ciclo'] = (df['fecha_cierre'] - df['fecha_creacion']).dt.days
                        df_v = df[df['dias_ciclo'] > 0].copy()
                        if not df_v.empty:
                            promedio_tc = float(df_v['dias_ciclo'].mean())
                            mediana_tc = float(df_v['dias_ciclo'].median())
                            resp = (
                                f"## Tiempo Promedio de Cierre\n\n**Basado en {len(df_v):,} oportunidades ganadas:**\n\n"
                                f"| Métrica | Días |\n|---|---:|\n"
                                f"| ⏱️ Promedio | **{promedio_tc:.0f} días** |\n"
                                f"| 📊 Mediana | **{mediana_tc:.0f} días** |\n"
                                f"| 🔽 Mínimo | **{int(df_v['dias_ciclo'].min())} días** |\n"
                                f"| 🔼 Máximo | **{int(df_v['dias_ciclo'].max())} días** |\n\n"
                                f"> 💡 *Ciclos <30 días: ventas transaccionales. >180 días: ventas consultivas.*"
                            )
                            return resp, df_v
            except Exception:
                pass
            return "## Tiempo de Cierre\n\nNo hay oportunidades ganadas con fecha de cierre registrada.", None

        # ── leads_por_origen ──────────────────────────────────────────────────
        if accion == 'leads_por_origen':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'crm.lead', filtro=[('type', 'in', ['lead', 'opportunity'])],
                        campos=['source_id', 'expected_revenue'], limite=500
                    )
                    if df is not None and not df.empty and 'source_id' in df.columns:
                        df['origen'] = df['source_id'].apply(
                            lambda x: x[1] if isinstance(x, (list, tuple)) else ('Sin origen' if not x else str(x))
                        )
                        df['revenue'] = pd.to_numeric(df.get('expected_revenue', 0), errors='coerce').fillna(0)
                        agg = df.groupby('origen').agg(cantidad=('origen', 'count'), revenue=('revenue', 'sum')).reset_index().sort_values('cantidad', ascending=False)
                        resp = f"## Leads por Origen\n\n| Origen | Leads | Revenue esperado |\n|---|---:|---:|\n"
                        for _, r in agg.iterrows():
                            resp += f"| {r['origen']} | {int(r['cantidad']):,} | ${float(r.get('revenue', 0)):,.2f} |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Leads por Origen\n\nMódulo CRM sin datos de origen/fuente configurados.", None

        # ── clientes_por_etapa ────────────────────────────────────────────────
        if accion == 'clientes_por_etapa':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'crm.lead',
                        filtro=[('type', '=', 'opportunity'), ('active', '=', True)],
                        campos=['stage_id', 'expected_revenue'], limite=500
                    )
                    if df is not None and not df.empty and 'stage_id' in df.columns:
                        df['etapa'] = df['stage_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['revenue'] = pd.to_numeric(df.get('expected_revenue', 0), errors='coerce').fillna(0)
                        agg = df.groupby('etapa').agg(oportunidades=('etapa', 'count'), revenue=('revenue', 'sum')).reset_index().sort_values('oportunidades', ascending=False)
                        resp = f"## Pipeline por Etapa\n\n| Etapa | Oportunidades | Revenue |\n|---|---:|---:|\n"
                        for _, r in agg.iterrows():
                            resp += f"| {r['etapa']} | {int(r['oportunidades']):,} | ${float(r['revenue']):,.2f} |\n"
                        resp += f"\n**Total pipeline:** {len(df):,} oportunidades | ${float(df['revenue'].sum()):,.2f}"
                        return resp, agg
            except Exception:
                pass
            return "## Clientes por Etapa\n\nMódulo CRM sin oportunidades activas.", None

        # ── lifetime_value ────────────────────────────────────────────────────
        if accion == 'lifetime_value':
            datos_ltv = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli_ltv = datos_ltv.get('por_cliente', [])
            df = pd.DataFrame(por_cli_ltv) if por_cli_ltv else None
            resp = f"## Lifetime Value (LTV) de Clientes\n\n**Período:** {fi} a {ff}\n\n"
            if df is not None and not df.empty and 'total' in df.columns:
                col_ltv = pd.to_numeric(df['total'], errors='coerce').fillna(0)
                df_ltv = df.copy()
                df_ltv['ltv'] = col_ltv
                df_ltv = df_ltv.sort_values('ltv', ascending=False)
                resp += (
                    f"| Métrica | Valor |\n|---|---:|\n"
                    f"| 👥 Clientes analizados | **{len(df):,}** |\n"
                    f"| 📊 LTV promedio | **${float(col_ltv.mean()):,.2f}** |\n"
                    f"| 🏆 LTV máximo | **${float(col_ltv.max()):,.2f}** |\n\n"
                    f"**Top 10 clientes por LTV:**\n\n| # | Cliente | LTV |\n|---|---|---:|\n"
                )
                for i, (_, r) in enumerate(df_ltv.head(10).iterrows(), 1):
                    nombre = str(r.get('name', r.get('partner', '')))[:35]
                    resp += f"| {i} | {nombre} | ${float(r['ltv']):,.2f} |\n"
            else:
                resp += "No hay datos suficientes para calcular LTV."
            return resp, df

        # ── reactivacion_clientes ─────────────────────────────────────────────
        if accion == 'reactivacion_clientes':
            try:
                if self.odoo and self.odoo.conectado:
                    from datetime import date as _dt_rac, timedelta
                    hoy_rac = _dt_rac.today()
                    f60 = (hoy_rac - timedelta(days=60)).strftime('%Y-%m-%d')
                    f180 = (hoy_rac - timedelta(days=180)).strftime('%Y-%m-%d')
                    df = self.odoo.buscar(
                        'sale.order',
                        filtro=[('state', 'in', ['sale', 'done']), ('date_order', '>=', f180), ('date_order', '<=', f60)],
                        campos=['partner_id', 'amount_total', 'date_order'],
                        limite=300
                    )
                    if df is not None and not df.empty and 'partner_id' in df.columns:
                        df['cliente'] = df['partner_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['monto'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        agg = df.groupby('cliente').agg(compras=('monto', 'count'), total=('monto', 'sum')).reset_index().sort_values('total', ascending=False)
                        resp = (
                            f"## Clientes para Reactivación\n\n"
                            f"**Clientes con compras hace 60-180 días** (sin actividad reciente):\n\n"
                            f"**{len(agg):,} clientes** con potencial de reactivación:\n\n"
                            f"| Cliente | Compras | Total histórico |\n|---|---:|---:|\n"
                        )
                        for _, r in agg.head(15).iterrows():
                            resp += f"| {r['cliente'][:35]} | {int(r['compras'])} | ${float(r['total']):,.2f} |\n"
                        resp += "\n> 💡 *Campaña sugerida: descuento especial o contacto personalizado.*"
                        return resp, agg
            except Exception:
                pass
            return "## Reactivación de Clientes\n\nNo se encontraron clientes inactivos en el rango 60-180 días.", None

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_compras(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        temp = getattr(consulta, 'temporalidad', {}) or {}
        fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')

        if accion == 'concentracion_proveedores':
            datos = self.analizador.top_proveedores()
            if datos.get('ranking'):
                df = pd.DataFrame(datos['ranking'])
                resp = "## Concentración de Proveedores\n\n"
                total_gasto = df['total'].sum() if 'total' in df.columns else 0
                if total_gasto > 0 and len(df) > 0:
                    top3 = df.head(3)['total'].sum()
                    resp += f"- **Gasto total:** ${total_gasto:,.2f}\n"
                    resp += f"- **Top 3 proveedores:** ${top3:,.2f} ({top3/total_gasto*100:.1f}%)\n"
                    resp += f"- **Proveedores totales:** {len(df)}\n"
                return resp, df

        if accion == 'lead_time_proveedores':
            datos = self.analizador.analisis_compras(fi, ff)
            resp = self.analizador.formatear_analisis_md('compras', datos)
            df = pd.DataFrame(datos.get('por_proveedor', []))
            return resp, df

        # ── evaluacion_proveedores ────────────────────────────────────────────
        if accion == 'evaluacion_proveedores':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', 'in', ['purchase', 'done'])]
                    if fi:
                        filtro.append(('date_order', '>=', fi))
                    if ff:
                        filtro.append(('date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'purchase.order', filtro=filtro,
                        campos=['partner_id', 'amount_total', 'date_order', 'date_approve'],
                        limite=500
                    )
                    if df is not None and not df.empty and 'partner_id' in df.columns:
                        df['proveedor'] = df['partner_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['monto'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        agg = df.groupby('proveedor').agg(ordenes=('monto', 'count'), total=('monto', 'sum')).reset_index().sort_values('total', ascending=False)
                        resp = (
                            f"## Evaluación de Proveedores\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Proveedor | Órdenes | Compras totales | Ticket prom. |\n|---|---:|---:|---:|\n"
                        )
                        for _, r in agg.head(15).iterrows():
                            ticket_prom = float(r['total']) / max(int(r['ordenes']), 1)
                            resp += f"| {str(r['proveedor'])[:35]} | {int(r['ordenes'])} | ${float(r['total']):,.2f} | ${ticket_prom:,.2f} |\n"
                        return resp, agg
            except Exception:
                pass
            datos = self.analizador.analisis_compras(fi, ff)
            df = pd.DataFrame(datos.get('por_proveedor', []))
            return f"## Evaluación de Proveedores\n\n**Período:** {fi} a {ff}\n\n", df if not df.empty else None

        # ── comparativa_precios ───────────────────────────────────────────────
        if accion == 'comparativa_precios':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('order_id.state', 'in', ['purchase', 'done'])]
                    if fi:
                        filtro.append(('order_id.date_order', '>=', fi))
                    if ff:
                        filtro.append(('order_id.date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'purchase.order.line', filtro=filtro,
                        campos=['product_id', 'price_unit', 'partner_id', 'product_qty'],
                        limite=500
                    )
                    if df is not None and not df.empty and 'product_id' in df.columns:
                        df['producto'] = df['product_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['precio'] = pd.to_numeric(df['price_unit'], errors='coerce').fillna(0)
                        agg = df.groupby('producto')['precio'].agg(['min', 'max', 'mean', 'count']).reset_index()
                        agg.columns = ['producto', 'precio_min', 'precio_max', 'precio_prom', 'compras']
                        agg['variacion'] = (agg['precio_max'] - agg['precio_min']) / agg['precio_min'] * 100
                        agg = agg[agg['compras'] > 1].sort_values('variacion', ascending=False)
                        resp = (
                            f"## Comparativa de Precios de Compra\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Producto | Precio mín. | Precio máx. | Promedio | Variación |\n|---|---:|---:|---:|---:|\n"
                        )
                        for _, r in agg.head(15).iterrows():
                            emoji_cp = "🔴" if float(r['variacion']) > 20 else "🟡" if float(r['variacion']) > 10 else "🟢"
                            resp += f"| {str(r['producto'])[:35]} | ${float(r['precio_min']):,.2f} | ${float(r['precio_max']):,.2f} | ${float(r['precio_prom']):,.2f} | {emoji_cp} {float(r['variacion']):.1f}% |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Comparativa de Precios\n\nNo hay suficientes datos de líneas de compra.", None

        # ── ordenes_pendientes ────────────────────────────────────────────────
        if accion == 'ordenes_pendientes':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'purchase.order',
                        filtro=[('state', 'in', ['draft', 'sent', 'to approve'])],
                        campos=['name', 'partner_id', 'amount_total', 'date_order', 'state'],
                        limite=200
                    )
                    if df is not None and not df.empty:
                        df['monto'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        resp = (
                            f"## Órdenes de Compra Pendientes\n\n"
                            f"**{len(df):,} órdenes** en proceso:\n\n"
                            f"| OC | Proveedor | Monto | Estado |\n|---|---|---:|---|\n"
                        )
                        for _, r in df.head(15).iterrows():
                            cp = r.get('partner_id', '')
                            cp_n = (cp[1] if isinstance(cp, (list, tuple)) else str(cp))[:25]
                            resp += f"| {r.get('name', '')} | {cp_n} | ${float(r['monto']):,.2f} | {r.get('state', '')} |\n"
                        resp += f"\n**Total comprometido:** ${float(df['monto'].sum()):,.2f}\n"
                        return resp, df
            except Exception:
                pass
            return "## Órdenes Pendientes\n\nNo se encontraron órdenes de compra pendientes.", None

        # ── cumplimiento_entregas ─────────────────────────────────────────────
        if accion == 'cumplimiento_entregas':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('origin', 'like', 'PO'), ('state', 'in', ['done', 'cancel'])]
                    if fi:
                        filtro.append(('scheduled_date', '>=', fi))
                    if ff:
                        filtro.append(('scheduled_date', '<=', ff))
                    df = self.odoo.buscar(
                        'stock.picking', filtro=filtro,
                        campos=['name', 'partner_id', 'scheduled_date', 'date_done', 'state'],
                        limite=300
                    )
                    if df is not None and not df.empty:
                        df['sch'] = pd.to_datetime(df['scheduled_date'], errors='coerce')
                        df['done'] = pd.to_datetime(df['date_done'], errors='coerce')
                        df['a_tiempo'] = df['done'] <= df['sch']
                        total_ent = len(df[df['state'] == 'done'])
                        a_tiempo = int(df['a_tiempo'].sum())
                        pct_at = a_tiempo / total_ent * 100 if total_ent > 0 else 0
                        emoji_ent = "🟢" if pct_at >= 90 else "🟡" if pct_at >= 75 else "🔴"
                        resp = (
                            f"## Cumplimiento de Entregas\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Métrica | Valor |\n|---|---:|\n"
                            f"| 📦 Recepciones completadas | **{total_ent:,}** |\n"
                            f"| ✅ A tiempo | **{a_tiempo:,}** |\n"
                            f"| 🎯 % Cumplimiento | **{emoji_ent} {pct_at:.1f}%** |\n\n"
                        )
                        return resp, df
            except Exception:
                pass
            return "## Cumplimiento de Entregas\n\nNo hay datos de recepciones para el período.", None

        # ── compras_por_categoria ─────────────────────────────────────────────
        if accion == 'compras_por_categoria':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('order_id.state', 'in', ['purchase', 'done'])]
                    if fi:
                        filtro.append(('order_id.date_order', '>=', fi))
                    if ff:
                        filtro.append(('order_id.date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'purchase.order.line', filtro=filtro,
                        campos=['product_id', 'categ_id', 'price_subtotal'], limite=1000
                    )
                    if df is not None and not df.empty:
                        df['categ'] = df.get('categ_id', df.get('product_id', pd.Series())).apply(
                            lambda x: x[1] if isinstance(x, (list, tuple)) else 'Sin categoría'
                        )
                        df['subtotal'] = pd.to_numeric(df.get('price_subtotal', 0), errors='coerce').fillna(0)
                        agg = df.groupby('categ')['subtotal'].sum().reset_index().sort_values('subtotal', ascending=False)
                        total_cc = float(agg['subtotal'].sum())
                        resp = f"## Compras por Categoría\n\n**Período:** {fi} a {ff}\n\n| Categoría | Compras | % |\n|---|---:|---:|\n"
                        for _, r in agg.iterrows():
                            pct = float(r['subtotal']) / total_cc * 100 if total_cc > 0 else 0
                            resp += f"| {r['categ']} | ${float(r['subtotal']):,.2f} | {pct:.1f}% |\n"
                        return resp, agg
            except Exception:
                pass
            datos = self.analizador.analisis_compras(fi, ff)
            df = pd.DataFrame(datos.get('por_categoria', []))
            return f"## Compras por Categoría\n\n**Período:** {fi} a {ff}\n\n", df if not df.empty else None

        # ── compras_recurrentes ───────────────────────────────────────────────
        if accion == 'compras_recurrentes':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', 'in', ['purchase', 'done'])]
                    if fi:
                        filtro.append(('date_order', '>=', fi))
                    if ff:
                        filtro.append(('date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'purchase.order', filtro=filtro,
                        campos=['partner_id', 'amount_total', 'date_order'], limite=500
                    )
                    if df is not None and not df.empty and 'partner_id' in df.columns:
                        df['proveedor'] = df['partner_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['monto'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        agg = df.groupby('proveedor').agg(
                            ordenes=('monto', 'count'),
                            total=('monto', 'sum'),
                            promedio=('monto', 'mean')
                        ).reset_index().sort_values('ordenes', ascending=False)
                        total_ordenes = int(agg['ordenes'].sum())
                        total_monto = float(agg['total'].sum())
                        n_proveedores = len(agg)
                        # Umbral dinámico: recurrente = 2+ si hay menos de 10 órdenes, 3+ si hay más
                        umbral = 2 if total_ordenes < 20 else 3
                        recurrentes = agg[agg['ordenes'] >= umbral].copy()
                        ocasionales = agg[agg['ordenes'] < umbral].copy()
                        resp = (
                            f"## Compras Recurrentes por Proveedor\n\n"
                            f"**Período:** {fi or 'histórico'} a {ff or 'hoy'}\n\n"
                            f"| Métrica | Valor |\n|---|---:|\n"
                            f"| 📦 Proveedores únicos | **{n_proveedores:,}** |\n"
                            f"| 🛒 Total órdenes | **{total_ordenes:,}** |\n"
                            f"| 💰 Monto total | **${total_monto:,.2f}** |\n"
                            f"| 🔄 Proveedores recurrentes (≥{umbral} órdenes) | **{len(recurrentes):,}** |\n\n"
                        )
                        if not recurrentes.empty:
                            resp += f"**Proveedores con {umbral}+ órdenes:**\n\n"
                            resp += "| Proveedor | Órdenes | Total comprado | Promedio/orden |\n|---|---:|---:|---:|\n"
                            for _, r in recurrentes.head(15).iterrows():
                                resp += (
                                    f"| {str(r['proveedor'])[:35]} | {int(r['ordenes'])} | "
                                    f"${float(r['total']):,.2f} | ${float(r['promedio']):,.2f} |\n"
                                )
                        else:
                            resp += "📋 **Todos los proveedores tienen una sola orden en el período.**\n\n"
                        if not ocasionales.empty:
                            resp += f"\n**Proveedores con 1 orden (ocasionales):** {len(ocasionales)}\n"
                            for _, r in ocasionales.head(5).iterrows():
                                resp += f"- {str(r['proveedor'])[:40]}: ${float(r['total']):,.2f}\n"
                        if len(recurrentes) == 0 and total_ordenes < 5:
                            resp += (
                                "\n💡 *Hay pocas órdenes de compra en el período. "
                                "Amplía el rango de fechas para un análisis más representativo.*"
                            )
                        return resp, agg
            except Exception:
                pass
            return "## Compras Recurrentes\n\nNo se pudo obtener el historial de órdenes de compra.", None

        # ── ahorro_potencial ──────────────────────────────────────────────────
        if accion == 'ahorro_potencial':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('order_id.state', 'in', ['purchase', 'done'])]
                    if fi:
                        filtro.append(('order_id.date_order', '>=', fi))
                    if ff:
                        filtro.append(('order_id.date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'purchase.order.line', filtro=filtro,
                        campos=['product_id', 'price_unit', 'product_qty', 'price_subtotal'],
                        limite=500
                    )
                    if df is not None and not df.empty and 'product_id' in df.columns:
                        df['producto'] = df['product_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['precio'] = pd.to_numeric(df['price_unit'], errors='coerce').fillna(0)
                        df['subtotal'] = pd.to_numeric(df.get('price_subtotal', 0), errors='coerce').fillna(0)
                        agg = df.groupby('producto').agg(precio_min=('precio', 'min'), precio_max=('precio', 'max'), total=('subtotal', 'sum')).reset_index()
                        agg['ahorro_max'] = (agg['precio_max'] - agg['precio_min']) / agg['precio_max'] * agg['total']
                        agg = agg[agg['ahorro_max'] > 0].sort_values('ahorro_max', ascending=False)
                        total_ahorro = float(agg['ahorro_max'].sum())
                        resp = (
                            f"## Ahorro Potencial en Compras\n\n**Período:** {fi} a {ff}\n\n"
                            f"**Ahorro potencial total: ${total_ahorro:,.2f}**\n\n"
                            f"*(Diferencia entre precio mínimo y máximo pagado por producto)*\n\n"
                            f"| Producto | Precio mín. | Precio máx. | Ahorro pot. |\n|---|---:|---:|---:|\n"
                        )
                        for _, r in agg.head(10).iterrows():
                            resp += f"| {str(r['producto'])[:35]} | ${float(r['precio_min']):,.2f} | ${float(r['precio_max']):,.2f} | ${float(r['ahorro_max']):,.2f} |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Ahorro Potencial\n\nNo hay suficientes compras del mismo producto para comparar precios.", None

        # ── compras_urgentes ──────────────────────────────────────────────────
        if accion == 'compras_urgentes':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'purchase.order',
                        filtro=[('state', 'in', ['draft', 'sent', 'purchase']), ('priority', '=', '1')],
                        campos=['name', 'partner_id', 'amount_total', 'date_order', 'date_planned'],
                        limite=100
                    )
                    if df is not None and not df.empty:
                        df['monto'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        resp = (
                            f"## Compras Urgentes\n\n"
                            f"**{len(df):,} órdenes** marcadas como urgentes:\n\n"
                            f"| OC | Proveedor | Monto | Fecha prometida |\n|---|---|---:|---|\n"
                        )
                        for _, r in df.iterrows():
                            cp = r.get('partner_id', '')
                            cp_n = (cp[1] if isinstance(cp, (list, tuple)) else str(cp))[:25]
                            fecha_prom = str(r.get('date_planned', r.get('date_order', '')))[:10]
                            resp += f"| {r.get('name', '')} | {cp_n} | ${float(r['monto']):,.2f} | {fecha_prom} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Compras Urgentes\n\nNo se encontraron órdenes de compra urgentes.", None

        # ── variacion_precios ─────────────────────────────────────────────────
        if accion == 'variacion_precios':
            datos_vp = self.analizador.analisis_compras(fi, ff)
            df_vp = pd.DataFrame(datos_vp.get('por_proveedor', []))
            resp = (
                f"## Variación de Precios de Compra\n\n**Período:** {fi} a {ff}\n\n"
                f"> 💡 *Para análisis de variación de precios por producto en el tiempo, se requieren al menos 2 períodos de compra del mismo artículo.*\n\n"
            )
            if not df_vp.empty:
                resp += f"Se analizaron **{len(df_vp):,}** proveedores en el período.\n"
            return resp, df_vp if not df_vp.empty else None

        # ── gasto_por_departamento ────────────────────────────────────────────
        if accion == 'gasto_por_departamento':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', 'in', ['purchase', 'done'])]
                    if fi:
                        filtro.append(('date_order', '>=', fi))
                    if ff:
                        filtro.append(('date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'purchase.order', filtro=filtro,
                        campos=['department_id', 'amount_total', 'partner_id'],
                        limite=500
                    )
                    if df is not None and not df.empty and 'department_id' in df.columns:
                        df['depto'] = df['department_id'].apply(
                            lambda x: x[1] if isinstance(x, (list, tuple)) else ('Sin departamento' if not x else str(x))
                        )
                        df['monto'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        agg = df.groupby('depto')['monto'].sum().reset_index().sort_values('monto', ascending=False)
                        total_gd = float(agg['monto'].sum())
                        resp = f"## Gasto por Departamento\n\n**Período:** {fi} a {ff}\n\n| Departamento | Gasto | % |\n|---|---:|---:|\n"
                        for _, r in agg.iterrows():
                            pct = float(r['monto']) / total_gd * 100 if total_gd > 0 else 0
                            resp += f"| {r['depto']} | ${float(r['monto']):,.2f} | {pct:.1f}% |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Gasto por Departamento\n\nNo está configurado el campo `Departamento` en órdenes de compra.", None

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_pdv(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        temp = getattr(consulta, 'temporalidad', {}) or {}
        fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')

        if accion == 'horarios_pico':
            datos = self.analizador.analisis_pos_completo(fi, ff)
            resp = "## Horarios Pico POS\n\n"
            if 'por_hora_pico' in datos:
                df = pd.DataFrame(datos['por_hora_pico'])
                resp += f"**Período:** {fi} a {ff}\n\n"
                return resp, df
            resp = self.analizador.formatear_analisis_md('pos', datos)
            return resp, None

        if accion == 'cierre_caja_pendiente':
            try:
                sesiones = self.odoo.buscar(
                    'pos.session',
                    filtro=[('state', '=', 'opened')],
                    campos=['name', 'config_id', 'user_id', 'start_at'],
                    limite=50
                )
                if sesiones.empty:
                    return "No hay sesiones de caja pendientes de cierre.", None
                sesiones['tienda'] = sesiones['config_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                sesiones['cajero'] = sesiones['user_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                resp = f"## Sesiones Pendientes de Cierre\n\n**{len(sesiones)}** sesiones abiertas:\n\n"
                resp += "| Sesión | Tienda | Cajero | Inicio |\n|---|---|---|---|\n"
                for _, s in sesiones.iterrows():
                    inicio = str(s.get('start_at', ''))[:16]
                    resp += f"| {s['name']} | {s['tienda']} | {s['cajero']} | {inicio} |\n"
                return resp, sesiones
            except Exception as e:
                return f"Error consultando sesiones: {e}", None

        # ── productividad_cajero ──────────────────────────────────────────────
        if accion == 'productividad_cajero':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', 'in', ['done', 'invoiced', 'paid'])]
                    if fi:
                        filtro.append(('date_order', '>=', fi))
                    if ff:
                        filtro.append(('date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'pos.order', filtro=filtro,
                        campos=['user_id', 'amount_total', 'date_order'], limite=2000
                    )
                    if df is not None and not df.empty and 'user_id' in df.columns:
                        df['cajero'] = df['user_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['monto'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        agg = df.groupby('cajero').agg(tickets=('monto', 'count'), ventas=('monto', 'sum')).reset_index()
                        agg['ticket_prom'] = agg['ventas'] / agg['tickets'].replace(0, 1)
                        agg = agg.sort_values('ventas', ascending=False)
                        resp = (
                            f"## Productividad por Cajero (POS)\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Cajero | Tickets | Ventas | Ticket prom. |\n|---|---:|---:|---:|\n"
                        )
                        for _, r in agg.head(15).iterrows():
                            resp += f"| {str(r['cajero'])[:30]} | {int(r['tickets']):,} | ${float(r['ventas']):,.2f} | ${float(r['ticket_prom']):,.2f} |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Productividad por Cajero\n\nMódulo POS no disponible o sin ventas en el período.", None

        # ── devoluciones_pos ──────────────────────────────────────────────────
        if accion == 'devoluciones_pos':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('amount_total', '<', 0)]
                    if fi:
                        filtro.append(('date_order', '>=', fi))
                    if ff:
                        filtro.append(('date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'pos.order', filtro=filtro,
                        campos=['name', 'partner_id', 'amount_total', 'date_order', 'session_id'],
                        limite=200
                    )
                    if df is not None and not df.empty:
                        total_dev = abs(float(pd.to_numeric(df['amount_total'], errors='coerce').sum()))
                        resp = (
                            f"## Devoluciones en POS\n\n**Período:** {fi} a {ff}\n\n"
                            f"- **Devoluciones:** {len(df):,}\n- **Total devuelto:** ${total_dev:,.2f}\n\n"
                            f"| Folio | Monto | Fecha |\n|---|---:|---|\n"
                        )
                        for _, r in df.head(10).iterrows():
                            resp += f"| {r.get('name', '')} | ${abs(float(r.get('amount_total', 0))):,.2f} | {str(r.get('date_order', ''))[:10]} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Devoluciones POS\n\nNo se encontraron devoluciones en el período.", None

        # ── descuentos_por_tienda ──────────────────────────────────────────────
        if accion == 'descuentos_por_tienda':
            try:
                if self.odoo and self.odoo.conectado:
                    from datetime import datetime
                    if not fi:
                        fi = datetime.now().strftime('%Y-%m-01')
                    if not ff:
                        ff = datetime.now().strftime('%Y-%m-%d')

                    # Paso 1: órdenes POS del período → mapa order_id → tienda
                    df_ord = self.odoo.buscar(
                        'pos.order',
                        filtro=[
                            ('state', 'in', ['done', 'invoiced', 'paid']),
                            ('date_order', '>=', fi),
                            ('date_order', '<=', ff),
                        ],
                        campos=['id', 'config_id'],
                        limite=0,
                    )
                    if df_ord is None or df_ord.empty:
                        return (
                            f"## Descuentos por Tienda\n\n"
                            f"No hay órdenes POS en el período {fi} → {ff}.", None
                        )

                    order_tienda = {}
                    for _, r in df_ord.iterrows():
                        cfg = r.get('config_id', '')
                        tienda_n = cfg[1] if isinstance(cfg, (list, tuple)) else str(cfg)
                        order_tienda[int(r['id'])] = tienda_n

                    order_ids = list(order_tienda.keys())

                    # Paso 2: líneas con descuento de esas órdenes
                    df_lin = self.odoo.buscar(
                        'pos.order.line',
                        filtro=[('order_id', 'in', order_ids), ('discount', '>', 0)],
                        campos=['order_id', 'product_id', 'qty', 'price_unit', 'discount', 'price_subtotal_incl'],
                        limite=0,
                    )
                    if df_lin is None or df_lin.empty:
                        return (
                            f"## Descuentos por Tienda — {fi} → {ff}\n\n"
                            f"No se registraron descuentos en el período.", None
                        )

                    df_lin = df_lin.copy()
                    df_lin['oid'] = df_lin['order_id'].apply(
                        lambda x: int(x[0]) if isinstance(x, (list, tuple)) else int(x)
                    )
                    df_lin['tienda'] = df_lin['oid'].map(order_tienda).fillna('Sin tienda')
                    df_lin['producto'] = df_lin['product_id'].apply(
                        lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                    )
                    df_lin['qty'] = pd.to_numeric(df_lin['qty'], errors='coerce').fillna(0)
                    df_lin['precio'] = pd.to_numeric(df_lin['price_unit'], errors='coerce').fillna(0)
                    df_lin['pct_desc'] = pd.to_numeric(df_lin['discount'], errors='coerce').fillna(0)
                    df_lin['neto'] = pd.to_numeric(df_lin['price_subtotal_incl'], errors='coerce').fillna(0)
                    df_lin['bruto'] = df_lin['precio'] * df_lin['qty']
                    # Pérdida de utilidad = lo que se dejó de cobrar por aplicar el descuento
                    df_lin['perdida'] = df_lin['bruto'] - df_lin['neto']
                    df_lin['perdida'] = df_lin['perdida'].clip(lower=0)  # solo positivos

                    # Resumen global
                    total_bruto = float(df_lin['bruto'].sum())
                    total_neto = float(df_lin['neto'].sum())
                    total_perdida = float(df_lin['perdida'].sum())
                    total_lineas = len(df_lin)
                    pct_global = total_perdida / total_bruto * 100 if total_bruto > 0 else 0
                    avg_desc = float(df_lin['pct_desc'].mean())

                    # Agrupado por tienda
                    agg_tienda = df_lin.groupby('tienda').agg(
                        lineas=('perdida', 'count'),
                        bruto=('bruto', 'sum'),
                        neto=('neto', 'sum'),
                        perdida=('perdida', 'sum'),
                        desc_prom=('pct_desc', 'mean'),
                    ).reset_index().sort_values('perdida', ascending=False)

                    # Top productos con mayor pérdida
                    top_prod = df_lin.groupby('producto').agg(
                        lineas=('perdida', 'count'),
                        perdida=('perdida', 'sum'),
                        desc_prom=('pct_desc', 'mean'),
                    ).reset_index().sort_values('perdida', ascending=False).head(10)

                    resp_dt = (
                        f"## Descuentos por Tienda — Pérdida de Utilidad\n\n"
                        f"**Período:** {fi} → {ff}\n\n"
                        f"| Métrica global | Valor |\n|---|---:|\n"
                        f"| 🏷️ Líneas con descuento | **{total_lineas:,}** |\n"
                        f"| 💰 Venta bruta (sin dcto) | **${total_bruto:,.2f}** |\n"
                        f"| 💳 Venta neta (con dcto) | **${total_neto:,.2f}** |\n"
                        f"| 📉 Pérdida total por descuentos | **${total_perdida:,.2f}** |\n"
                        f"| 🎯 % pérdida sobre venta bruta | **{pct_global:.1f}%** |\n"
                        f"| 📊 Descuento promedio | **{avg_desc:.1f}%** |\n\n"
                    )
                    if pct_global > 15:
                        resp_dt += "⚠️ **Alerta:** La pérdida supera el 15% del valor bruto. Revisar política de descuentos.\n\n"

                    resp_dt += "### Pérdida de Utilidad por Tienda\n\n"
                    resp_dt += "| Tienda | Líneas | Venta bruta | Venta neta | Pérdida | % pérdida | Dcto prom. |\n|---|---:|---:|---:|---:|---:|---:|\n"
                    for _, r in agg_tienda.iterrows():
                        bruto_t = float(r['bruto'])
                        pct_t = float(r['perdida']) / bruto_t * 100 if bruto_t > 0 else 0
                        resp_dt += (
                            f"| **{str(r['tienda'])[:28]}** | {int(r['lineas']):,} | "
                            f"${bruto_t:,.2f} | ${float(r['neto']):,.2f} | "
                            f"**${float(r['perdida']):,.2f}** | {pct_t:.1f}% | {float(r['desc_prom']):.1f}% |\n"
                        )

                    resp_dt += "\n### Top 10 Productos con Mayor Pérdida por Descuento\n\n"
                    resp_dt += "| # | Producto | Líneas | Pérdida | Dcto prom. |\n|---|---|---:|---:|---:|\n"
                    for i, (_, r) in enumerate(top_prod.iterrows(), 1):
                        resp_dt += (
                            f"| {i} | {str(r['producto'])[:40]} | {int(r['lineas']):,} | "
                            f"**${float(r['perdida']):,.2f}** | {float(r['desc_prom']):.1f}% |\n"
                        )

                    resp_dt += (
                        "\n> 📊 *Pérdida = precio_unitario × cantidad × (descuento/100). "
                        "Datos de `pos.order.line` — sólo líneas con descuento > 0.*"
                    )
                    return resp_dt, agg_tienda
            except Exception:
                import traceback; traceback.print_exc()
            return (
                f"## Descuentos por Tienda\n\n"
                f"No se pudieron obtener datos de descuentos del período {fi} → {ff}.", None
            )

        # ── descuentos_pos ────────────────────────────────────────────────────
        if accion == 'descuentos_pos':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('discount', '>', 0)]
                    if fi:
                        filtro.append(('order_id.date_order', '>=', fi))
                    if ff:
                        filtro.append(('order_id.date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'pos.order.line', filtro=filtro,
                        campos=['product_id', 'discount', 'price_subtotal_incl', 'qty'],
                        limite=500
                    )
                    if df is not None and not df.empty:
                        df['desc'] = pd.to_numeric(df['discount'], errors='coerce').fillna(0)
                        df['subtotal'] = pd.to_numeric(df.get('price_subtotal_incl', 0), errors='coerce').fillna(0)
                        avg_desc = float(df['desc'].mean())
                        resp = (
                            f"## Descuentos en POS\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Métrica | Valor |\n|---|---:|\n"
                            f"| 🏷️ Líneas con descuento | **{len(df):,}** |\n"
                            f"| 📊 Descuento promedio | **{avg_desc:.1f}%** |\n"
                            f"| 💰 Total ventas con dcto | **${float(df['subtotal'].sum()):,.2f}** |\n\n"
                        )
                        if avg_desc > 15:
                            resp += "⚠️ **Alerta:** Descuento promedio elevado en POS. Revisar política comercial.\n"
                        return resp, df
            except Exception:
                pass
            return "## Descuentos POS\n\nNo se encontraron líneas con descuento en el período.", None

        # ── cuadre_caja ───────────────────────────────────────────────────────
        if accion == 'cuadre_caja':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', '=', 'closed')]
                    if fi:
                        filtro.append(('stop_at', '>=', fi))
                    if ff:
                        filtro.append(('stop_at', '<=', ff))
                    df = self.odoo.buscar(
                        'pos.session', filtro=filtro,
                        campos=['name', 'config_id', 'cash_register_difference', 'total_payments_amount', 'stop_at'],
                        limite=100
                    )
                    if df is not None and not df.empty:
                        df['diferencia'] = pd.to_numeric(df.get('cash_register_difference', 0), errors='coerce').fillna(0)
                        n_faltante = int((df['diferencia'] < 0).sum())
                        n_sobrante = int((df['diferencia'] > 0).sum())
                        n_exacto = int((df['diferencia'] == 0).sum())
                        resp = (
                            f"## Cuadre de Caja POS\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Estado | Sesiones |\n|---|---:|\n"
                            f"| ✅ Exacto | {n_exacto:,} |\n"
                            f"| 🔼 Sobrante | {n_sobrante:,} |\n"
                            f"| 🔴 Faltante | {n_faltante:,} |\n\n"
                            f"| Sesión | Tienda | Diferencia |\n|---|---|---:|\n"
                        )
                        for _, r in df.sort_values('diferencia').head(10).iterrows():
                            tienda = r.get('config_id', '')
                            tienda_n = tienda[1] if isinstance(tienda, (list, tuple)) else str(tienda)
                            dif = float(r['diferencia'])
                            emoji_cj = "🔴" if dif < -1 else "🟢" if abs(dif) <= 1 else "🟡"
                            resp += f"| {r.get('name', '')} | {tienda_n[:20]} | {emoji_cj} ${dif:+,.2f} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Cuadre de Caja\n\nNo se encontraron sesiones cerradas en el período.", None

        # ── pos_por_sucursal ──────────────────────────────────────────────────
        if accion == 'pos_por_sucursal':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', 'in', ['done', 'invoiced', 'paid'])]
                    if fi:
                        filtro.append(('date_order', '>=', fi))
                    if ff:
                        filtro.append(('date_order', '<=', ff))
                    df = self.odoo.buscar(
                        'pos.order', filtro=filtro,
                        campos=['config_id', 'amount_total'], limite=2000
                    )
                    if df is not None and not df.empty and 'config_id' in df.columns:
                        df['sucursal'] = df['config_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['monto'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(0)
                        agg = df.groupby('sucursal').agg(tickets=('monto', 'count'), ventas=('monto', 'sum')).reset_index().sort_values('ventas', ascending=False)
                        total_suc = float(agg['ventas'].sum())
                        resp = (
                            f"## POS por Sucursal\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Sucursal | Tickets | Ventas | % |\n|---|---:|---:|---:|\n"
                        )
                        for _, r in agg.iterrows():
                            pct = float(r['ventas']) / total_suc * 100 if total_suc > 0 else 0
                            resp += f"| {r['sucursal']} | {int(r['tickets']):,} | ${float(r['ventas']):,.2f} | {pct:.1f}% |\n"
                        return resp, agg
            except Exception:
                pass
            return "## POS por Sucursal\n\nNo hay datos de ventas POS en el período.", None

        # ── ventas_diarias_por_tienda ─────────────────────────────────────────
        if accion == 'ventas_diarias_por_tienda':
            try:
                if self.odoo and self.odoo.conectado:
                    from datetime import datetime, timedelta
                    # Si no hay rango definido, usar últimos 30 días
                    if not fi:
                        fi = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    if not ff:
                        ff = datetime.now().strftime('%Y-%m-%d')
                    filtro_vdt = [
                        ('state', 'in', ['done', 'invoiced', 'paid']),
                        ('date_order', '>=', fi),
                        ('date_order', '<=', ff),
                    ]
                    df_vdt = self.odoo.buscar(
                        'pos.order', filtro=filtro_vdt,
                        campos=['date_order', 'config_id', 'amount_total'], limite=0
                    )
                    if df_vdt is not None and not df_vdt.empty:
                        df_vdt = df_vdt.copy()
                        df_vdt['fecha'] = df_vdt['date_order'].astype(str).str[:10]
                        df_vdt['tienda'] = df_vdt['config_id'].apply(
                            lambda x: x[1] if isinstance(x, (list, tuple)) else str(x)
                        )
                        df_vdt['monto'] = pd.to_numeric(df_vdt['amount_total'], errors='coerce').fillna(0)

                        # Agregado: día × tienda
                        agg_vdt = df_vdt.groupby(['fecha', 'tienda']).agg(
                            tickets=('monto', 'count'),
                            ventas=('monto', 'sum')
                        ).reset_index().sort_values(['fecha', 'tienda'])

                        tiendas_unicas = sorted(agg_vdt['tienda'].unique())
                        total_general = float(agg_vdt['ventas'].sum())
                        dias_unicas = sorted(agg_vdt['fecha'].unique())

                        # Resumen por tienda
                        resumen_tienda = agg_vdt.groupby('tienda').agg(
                            dias=('fecha', 'nunique'),
                            tickets=('tickets', 'sum'),
                            ventas=('ventas', 'sum')
                        ).reset_index().sort_values('ventas', ascending=False)

                        resp_vdt = (
                            f"## Ventas Diarias por Tienda\n\n"
                            f"**Período:** {fi} → {ff} | "
                            f"**Días:** {len(dias_unicas)} | "
                            f"**Tiendas:** {len(tiendas_unicas)} | "
                            f"**Total:** ${total_general:,.2f}\n\n"
                        )

                        # Tabla resumen por tienda
                        resp_vdt += "### Resumen por Tienda\n\n"
                        resp_vdt += "| Tienda | Días activos | Tickets | Ventas totales | Prom. diario |\n|---|---:|---:|---:|---:|\n"
                        for _, r in resumen_tienda.iterrows():
                            dias_activos = int(r['dias']) or 1
                            prom_dia = float(r['ventas']) / dias_activos
                            pct = float(r['ventas']) / total_general * 100 if total_general > 0 else 0
                            resp_vdt += (
                                f"| **{str(r['tienda'])[:30]}** | {int(r['dias'])} | "
                                f"{int(r['tickets']):,} | ${float(r['ventas']):,.2f} ({pct:.1f}%) | "
                                f"${prom_dia:,.2f} |\n"
                            )

                        # Tabla detalle diario (máx. 60 filas para no saturar)
                        resp_vdt += "\n### Comportamiento Diario\n\n"
                        if len(tiendas_unicas) <= 4:
                            # Tabla pivotada: columna por tienda
                            pivot = agg_vdt.pivot_table(
                                index='fecha', columns='tienda', values='ventas',
                                aggfunc='sum', fill_value=0
                            ).reset_index()
                            cols_tienda = [c for c in pivot.columns if c != 'fecha']
                            header = "| Fecha | " + " | ".join(str(c)[:20] for c in cols_tienda) + " | Total |\n"
                            sep = "|---|" + "---:|" * (len(cols_tienda) + 1) + "\n"
                            resp_vdt += header + sep
                            for _, row in pivot.head(60).iterrows():
                                fila_total = sum(float(row[c]) for c in cols_tienda)
                                vals = " | ".join(f"${float(row[c]):,.2f}" for c in cols_tienda)
                                resp_vdt += f"| {row['fecha']} | {vals} | **${fila_total:,.2f}** |\n"
                        else:
                            # Demasiadas tiendas → tabla vertical simple
                            resp_vdt += "| Fecha | Tienda | Tickets | Ventas |\n|---|---|---:|---:|\n"
                            for _, r in agg_vdt.head(60).iterrows():
                                resp_vdt += (
                                    f"| {r['fecha']} | {str(r['tienda'])[:25]} | "
                                    f"{int(r['tickets']):,} | ${float(r['ventas']):,.2f} |\n"
                                )
                            if len(agg_vdt) > 60:
                                resp_vdt += f"\n> *Mostrando 60 de {len(agg_vdt):,} registros.*\n"

                        resp_vdt += (
                            "\n> 📊 *Datos de `pos.order` — sólo órdenes en estado done/invoiced/paid. "
                            "Para ver la gráfica selecciona el ícono de visualización.*"
                        )
                        return resp_vdt, agg_vdt
            except Exception:
                import traceback; traceback.print_exc()
            return (
                f"## Ventas Diarias por Tienda\n\n"
                f"No hay datos de ventas POS en el período {fi} → {ff}.", None
            )

        # ── ticket_detalle ────────────────────────────────────────────────────
        if accion == 'ticket_detalle':
            params_td = getattr(consulta, 'parametros', {}) or {}
            num_ticket = params_td.get('ticket', params_td.get('folio', params_td.get('orden', '')))
            try:
                if self.odoo and self.odoo.conectado and num_ticket:
                    df = self.odoo.buscar(
                        'pos.order.line',
                        filtro=[('order_id.name', 'ilike', str(num_ticket))],
                        campos=['product_id', 'qty', 'price_unit', 'discount', 'price_subtotal_incl'],
                        limite=50
                    )
                    if df is not None and not df.empty:
                        df['producto'] = df['product_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['qty'] = pd.to_numeric(df.get('qty', 1), errors='coerce').fillna(1)
                        df['precio'] = pd.to_numeric(df.get('price_unit', 0), errors='coerce').fillna(0)
                        df['subtotal'] = pd.to_numeric(df.get('price_subtotal_incl', 0), errors='coerce').fillna(0)
                        resp = (
                            f"## Detalle de Ticket: {num_ticket}\n\n"
                            f"| Producto | Qty | Precio | Subtotal |\n|---|---:|---:|---:|\n"
                        )
                        for _, r in df.iterrows():
                            resp += f"| {str(r['producto'])[:35]} | {float(r['qty']):.0f} | ${float(r['precio']):,.2f} | ${float(r['subtotal']):,.2f} |\n"
                        resp += f"\n**Total:** ${float(df['subtotal'].sum()):,.2f}"
                        return resp, df
            except Exception:
                pass
            return f"## Detalle de Ticket\n\nEspecifica el número de ticket. Ejemplo: 'detalle ticket POS/001/0001'", None

        # ── productos_mas_vendidos_pos ────────────────────────────────────────
        if accion == 'productos_mas_vendidos_pos':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = []
                    if fi:
                        filtro.append(('order_id.date_order', '>=', fi))
                    if ff:
                        filtro.append(('order_id.date_order', '<=', ff))
                    filtro.append(('order_id.state', 'in', ['done', 'invoiced', 'paid']))
                    df = self.odoo.buscar(
                        'pos.order.line', filtro=filtro,
                        campos=['product_id', 'qty', 'price_subtotal_incl'], limite=2000
                    )
                    if df is not None and not df.empty and 'product_id' in df.columns:
                        df['producto'] = df['product_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['qty'] = pd.to_numeric(df.get('qty', 1), errors='coerce').fillna(0)
                        df['subtotal'] = pd.to_numeric(df.get('price_subtotal_incl', 0), errors='coerce').fillna(0)
                        agg = df.groupby('producto').agg(unidades=('qty', 'sum'), ventas=('subtotal', 'sum')).reset_index().sort_values('unidades', ascending=False)
                        resp = (
                            f"## Top Productos POS\n\n**Período:** {fi} a {ff}\n\n"
                            f"| # | Producto | Unidades | Ventas |\n|---|---|---:|---:|\n"
                        )
                        for i, (_, r) in enumerate(agg.head(15).iterrows(), 1):
                            resp += f"| {i} | {str(r['producto'])[:35]} | {float(r['unidades']):,.0f} | ${float(r['ventas']):,.2f} |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Productos más vendidos en POS\n\nMódulo POS sin datos en el período.", None

        # ── merma_pos ─────────────────────────────────────────────────────────
        if accion == 'merma_pos':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('scrapped', '=', True)]
                    if fi:
                        filtro.append(('date_done', '>=', fi))
                    if ff:
                        filtro.append(('date_done', '<=', ff))
                    df = self.odoo.buscar(
                        'stock.scrap', filtro=filtro,
                        campos=['product_id', 'scrap_qty', 'product_uom_id', 'date_done', 'location_id'],
                        limite=200
                    )
                    if df is not None and not df.empty:
                        df['producto'] = df['product_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['qty'] = pd.to_numeric(df.get('scrap_qty', 0), errors='coerce').fillna(0)
                        agg = df.groupby('producto')['qty'].sum().reset_index().sort_values('qty', ascending=False)
                        resp = (
                            f"## Merma / Desecho\n\n**Período:** {fi} a {ff}\n\n"
                            f"**Total de registros:** {len(df):,}\n\n"
                            f"| Producto | Cantidad desechada |\n|---|---:|\n"
                        )
                        for _, r in agg.head(10).iterrows():
                            resp += f"| {str(r['producto'])[:35]} | {float(r['qty']):,.2f} |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Merma POS\n\nNo se encontraron registros de merma/desecho en el período.", None

        # ── rendimiento_terminal ──────────────────────────────────────────────
        if accion == 'rendimiento_terminal':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', '=', 'closed')]
                    if fi:
                        filtro.append(('stop_at', '>=', fi))
                    if ff:
                        filtro.append(('stop_at', '<=', ff))
                    df = self.odoo.buscar(
                        'pos.session', filtro=filtro,
                        campos=['name', 'config_id', 'total_payments_amount', 'start_at', 'stop_at'],
                        limite=100
                    )
                    if df is not None and not df.empty and 'config_id' in df.columns:
                        df['terminal'] = df['config_id'].apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['ventas'] = pd.to_numeric(df.get('total_payments_amount', 0), errors='coerce').fillna(0)
                        agg = df.groupby('terminal').agg(sesiones=('ventas', 'count'), ventas_total=('ventas', 'sum')).reset_index().sort_values('ventas_total', ascending=False)
                        resp = (
                            f"## Rendimiento por Terminal POS\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Terminal | Sesiones | Ventas totales | Prom/sesión |\n|---|---:|---:|---:|\n"
                        )
                        for _, r in agg.iterrows():
                            prom = float(r['ventas_total']) / max(int(r['sesiones']), 1)
                            resp += f"| {r['terminal']} | {int(r['sesiones'])} | ${float(r['ventas_total']):,.2f} | ${prom:,.2f} |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Rendimiento Terminal\n\nNo hay sesiones cerradas en el período.", None

        # ── ventas_pos_vs_ecommerce ───────────────────────────────────────────
        if accion == 'ventas_pos_vs_ecommerce':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro_pos = [('state', 'in', ['done', 'invoiced', 'paid'])]
                    filtro_so = [('state', 'in', ['sale', 'done'])]
                    if fi:
                        filtro_pos.append(('date_order', '>=', fi))
                        filtro_so.append(('date_order', '>=', fi))
                    if ff:
                        filtro_pos.append(('date_order', '<=', ff))
                        filtro_so.append(('date_order', '<=', ff))
                    df_pos = self.odoo.buscar('pos.order', filtro=filtro_pos, campos=['amount_total'], limite=2000)
                    df_so = self.odoo.buscar('sale.order', filtro=filtro_so, campos=['amount_total', 'team_id'], limite=2000)
                    ventas_pos = float(pd.to_numeric(df_pos['amount_total'], errors='coerce').sum()) if df_pos is not None and not df_pos.empty else 0
                    ventas_so = float(pd.to_numeric(df_so['amount_total'], errors='coerce').sum()) if df_so is not None and not df_so.empty else 0
                    total_mix = ventas_pos + ventas_so
                    pct_pos = ventas_pos / total_mix * 100 if total_mix > 0 else 0
                    pct_so = ventas_so / total_mix * 100 if total_mix > 0 else 0
                    resp = (
                        f"## Ventas POS vs. Canal Digital\n\n**Período:** {fi} a {ff}\n\n"
                        f"| Canal | Ventas | % del total |\n|---|---:|---:|\n"
                        f"| 🏪 POS (punto de venta) | **${ventas_pos:,.2f}** | **{pct_pos:.1f}%** |\n"
                        f"| 💻 Ventas digitales/SO | **${ventas_so:,.2f}** | **{pct_so:.1f}%** |\n"
                        f"| **Total** | **${total_mix:,.2f}** | 100% |\n\n"
                        "> 💡 *'Ventas digitales' incluye todas las órdenes de venta (ecommerce, telefónica, etc.)*"
                    )
                    return resp, None
            except Exception:
                pass
            return "## Ventas POS vs. Ecommerce\n\nNo se pudieron obtener datos comparativos.", None

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_rrhh(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        temp = getattr(consulta, 'temporalidad', {}) or {}
        fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')

        if accion == 'ausentismo_analisis':
            datos = self.analizador.analisis_ausencias()
            resp = self.analizador.formatear_analisis_md('ausencias', datos)
            return resp, None

        if accion == 'vencimiento_contratos':
            datos = self.analizador.contratos_por_vencer()
            resp = self.fmt._formatear_contratos(datos)
            df = pd.DataFrame(datos.get('contratos', []))
            return resp, df if not df.empty else None

        if accion == 'antiguedad_empleados':
            datos = self.analizador.analisis_headcount()
            resp = self.analizador.formatear_analisis_md('headcount', datos)
            df = pd.DataFrame(datos.get('por_departamento', []))
            return resp, df if not df.empty else None

        if accion == 'costo_por_empleado':
            datos = self.analizador.analisis_nomina()
            resp = self.analizador.formatear_analisis_md('nomina', datos)
            return resp, None

        # ── analisis_rh / headcount ──────────────────────────────────────────
        if accion in ('analisis_rh', 'headcount'):
            datos = self.analizador.analisis_headcount()
            resumen = datos.get('resumen', {})
            total = resumen.get('total_empleados', 0)
            por_dep = datos.get('por_departamento', [])
            resp = (
                f"## {'Análisis de RRHH' if accion == 'analisis_rh' else 'Headcount — Plantilla de Personal'}\n\n"
                f"| Métrica | Valor |\n|---|---:|\n"
                f"| 👥 Empleados activos | **{total}** |\n"
            )
            if resumen.get('nuevas_altas'):
                resp += f"| ✅ Altas recientes | **{resumen.get('nuevas_altas', 0)}** |\n"
            if resumen.get('bajas_periodo'):
                resp += f"| 📉 Bajas en el período | **{resumen.get('bajas_periodo', 0)}** |\n"
            if por_dep:
                df = pd.DataFrame(por_dep)
                resp += f"\n**Por departamento:**\n\n| Departamento | Empleados |\n|---|---:|\n"
                for _, r in df.head(10).iterrows():
                    dep = str(r.get('department', r.get('departamento', r.iloc[0])))[:35]
                    n = r.get('count', r.get('total', r.get('empleados', 0)))
                    resp += f"| {dep} | {int(float(n))} |\n"
                return resp, df
            return resp, None

        # ── rotacion_personal ────────────────────────────────────────────────
        if accion == 'rotacion_personal':
            from datetime import datetime, timedelta
            hace_90 = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            total, bajas, altas = 0, 0, 0
            df_rot = None
            try:
                if self.odoo and self.odoo.conectado:
                    df_act = self.odoo.buscar('hr.employee', filtro=[('active', '=', True)],
                        campos=['name', 'department_id', 'date_start'], limite=500)
                    total = len(df_act) if df_act is not None and not df_act.empty else 0
                    # Altas recientes: empleados con date_start en últimos 90 días
                    if df_act is not None and not df_act.empty and 'date_start' in df_act.columns:
                        df_act['fecha'] = df_act['date_start'].astype(str).str[:10]
                        altas = int((df_act['fecha'] >= hace_90).sum())
                    # Bajas: empleados inactivos dados de baja en últimos 90 días
                    df_baj = self.odoo.buscar('hr.employee',
                        filtro=[('active', '=', False)],
                        campos=['name', 'department_id'], limite=200)
                    bajas = len(df_baj) if df_baj is not None and not df_baj.empty else 0
                    df_rot = df_act
            except Exception:
                datos = self.analizador.analisis_headcount()
                total = datos.get('resumen', {}).get('total_empleados', 0)
            total = max(total, 1)
            tasa_rot = bajas / total * 100
            tasa_altas = altas / total * 100
            nivel = "Alta 🔴" if tasa_rot > 20 else "Moderada 🟡" if tasa_rot > 10 else "Normal 🟢"
            resp = (
                f"## Análisis de Rotación de Personal\n\n"
                f"| Métrica | Valor |\n|---|---:|\n"
                f"| 👥 Plantilla activa | **{total:,}** |\n"
                f"| 📈 Altas (últimos 90 días) | **{altas}** |\n"
                f"| 📉 Bajas (empleados inactivos) | **{bajas}** |\n"
                f"| 🔄 Tasa rotación neta | **{tasa_rot:.1f}%** |\n"
                f"| 📊 Tasa entrada | **{tasa_altas:.1f}%** |\n\n"
                f"**Nivel de rotación:** {nivel}\n\n"
            )
            if tasa_rot > 20:
                resp += "⚠️ **Acción urgente:** Rotación alta. Implementar encuestas de salida y plan de retención.\n"
            elif tasa_rot > 10:
                resp += "🟡 **Monitorear:** Rotación moderada. Identificar áreas y perfiles más afectados.\n"
            else:
                resp += "🟢 **Situación controlada.** Continuar con encuestas de clima laboral periódicas.\n"
            return resp, df_rot

        # ── brecha_salarial ───────────────────────────────────────────────────
        if accion == 'brecha_salarial':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'hr.contract',
                        filtro=[('state', '=', 'open')],
                        campos=['employee_id', 'job_id', 'wage', 'department_id'],
                        limite=300
                    )
                    if df is not None and not df.empty and 'wage' in df.columns:
                        df['salario'] = pd.to_numeric(df['wage'], errors='coerce').fillna(0)
                        df['puesto'] = df.get('job_id', pd.Series()).apply(lambda x: x[1] if isinstance(x, (list, tuple)) else ('Sin puesto' if not x else str(x)))
                        agg = df.groupby('puesto')['salario'].agg(['min', 'max', 'mean', 'count']).reset_index()
                        agg.columns = ['puesto', 'min_sal', 'max_sal', 'prom_sal', 'empleados']
                        # Evitar división por cero / inf: usar NaN cuando min_sal=0
                        agg['brecha'] = agg.apply(
                            lambda r: (r['max_sal'] - r['min_sal']) / r['min_sal'] * 100
                            if r['min_sal'] > 0 else 0.0, axis=1
                        )
                        agg = agg[agg['empleados'] > 1].sort_values('brecha', ascending=False)
                        resp = (
                            f"## Brecha Salarial por Puesto\n\n"
                            f"**{len(agg)} puestos** con 2+ empleados | Contratos activos: {len(df)}\n\n"
                            f"| Puesto | Empleados | Sal. mín. | Sal. máx. | Promedio | Brecha |\n|---|---:|---:|---:|---:|---:|\n"
                        )
                        for _, r in agg.head(15).iterrows():
                            brecha_val = float(r['brecha'])
                            emoji_bs = "🔴" if brecha_val > 50 else "🟡" if brecha_val > 25 else "🟢"
                            resp += f"| {str(r['puesto'])[:30]} | {int(r['empleados'])} | ${float(r['min_sal']):,.2f} | ${float(r['max_sal']):,.2f} | ${float(r['prom_sal']):,.2f} | {emoji_bs} {brecha_val:.0f}% |\n"
                        resp += "\n> 💡 *Brecha >50%: revisar equidad salarial interna.*"
                        return resp, agg
            except Exception:
                pass
            return "## Brecha Salarial\n\nNo hay contratos activos o el módulo HR no está disponible.", None

        # ── horas_extra ───────────────────────────────────────────────────────
        if accion == 'horas_extra':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = []
                    if fi:
                        filtro.append(('check_in', '>=', fi))
                    if ff:
                        filtro.append(('check_in', '<=', ff))
                    df = self.odoo.buscar(
                        'hr.attendance', filtro=filtro,
                        campos=['employee_id', 'check_in', 'check_out', 'worked_hours'],
                        limite=1000
                    )
                    if df is not None and not df.empty:
                        df['horas'] = pd.to_numeric(df.get('worked_hours', 0), errors='coerce').fillna(0)
                        df['empleado'] = df.get('employee_id', pd.Series()).apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        agg = df.groupby('empleado')['horas'].sum().reset_index().sort_values('horas', ascending=False)
                        jornada_esp = 8.0
                        dias = max((pd.to_datetime(ff, errors='coerce') - pd.to_datetime(fi, errors='coerce')).days if fi and ff else 30, 1)
                        horas_esp = jornada_esp * dias * 5 / 7
                        agg['horas_extra'] = (agg['horas'] - horas_esp).clip(lower=0)
                        resp = (
                            f"## Análisis de Horas Extra\n\n**Período:** {fi} a {ff}\n\n"
                            f"| Empleado | Horas trabajadas | Horas extra est. |\n|---|---:|---:|\n"
                        )
                        for _, r in agg.head(15).iterrows():
                            resp += f"| {str(r['empleado'])[:30]} | {float(r['horas']):.1f}h | {float(r['horas_extra']):.1f}h |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Horas Extra\n\nMódulo de asistencias no disponible o sin registros en el período.", None

        # ── vacaciones_pendientes ─────────────────────────────────────────────
        if accion == 'vacaciones_pendientes':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'hr.leave.allocation',
                        filtro=[('state', '=', 'validate'), ('holiday_status_id.name', 'ilike', 'Vacacion')],
                        campos=['employee_id', 'number_of_days', 'holiday_status_id'],
                        limite=300
                    )
                    if df is not None and not df.empty:
                        df['empleado'] = df.get('employee_id', pd.Series()).apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['dias'] = pd.to_numeric(df.get('number_of_days', 0), errors='coerce').fillna(0)
                        total_dias = float(df['dias'].sum())
                        resp = (
                            f"## Vacaciones Pendientes\n\n"
                            f"**Total días disponibles:** {total_dias:,.0f} días en {len(df):,} empleados\n\n"
                            f"| Empleado | Días disponibles |\n|---|---:|\n"
                        )
                        for _, r in df.sort_values('dias', ascending=False).head(15).iterrows():
                            resp += f"| {str(r['empleado'])[:35]} | {float(r['dias']):.0f} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Vacaciones Pendientes\n\nMódulo de ausencias no disponible o sin asignaciones de vacaciones.", None

        # ── costo_rotacion ────────────────────────────────────────────────────
        if accion == 'costo_rotacion':
            datos_cr = self.analizador.analisis_empleados()
            resumen = datos_cr.get('resumen', {})
            total_emp = resumen.get('total', 100) or 100
            bajas = resumen.get('bajas', 0) or 0
            try:
                df_sal = self.odoo.buscar('hr.contract', filtro=[('state', '=', 'open')], campos=['wage'], limite=300) if self.odoo and self.odoo.conectado else None
                salario_prom = float(pd.to_numeric(df_sal['wage'], errors='coerce').mean()) if df_sal is not None and not df_sal.empty else 15000
            except Exception:
                salario_prom = 15000
            costo_por_baja = salario_prom * 1.5
            costo_total_rot = bajas * costo_por_baja
            tasa_r = bajas / total_emp * 100 if total_emp > 0 else 0
            resp = (
                f"## Costo de Rotación de Personal\n\n"
                f"**Fórmula:** Costo = Bajas × (1.5 × Salario promedio)\n\n"
                f"| Métrica | Valor |\n|---|---:|\n"
                f"| 👥 Empleados totales | **{total_emp:,}** |\n"
                f"| 📉 Bajas en el período | **{bajas:,}** |\n"
                f"| 💰 Salario promedio | **${salario_prom:,.2f}** |\n"
                f"| 💳 Costo estimado por baja | **${costo_por_baja:,.2f}** |\n"
                f"| 🚨 **Costo total rotación** | **${costo_total_rot:,.2f}** |\n"
                f"| 📊 Tasa de rotación | **{tasa_r:.1f}%** |\n\n"
                "> ⚠️ *Factor 1.5x incluye: selección, onboarding, productividad perdida. Ajusta según tu empresa.*"
            )
            return resp, None

        # ── clima_organizacional ──────────────────────────────────────────────
        if accion == 'clima_organizacional':
            datos_co = self.analizador.analisis_empleados()
            resumen_co = datos_co.get('resumen', {})
            total_e = resumen_co.get('total', 0)
            bajas_co = resumen_co.get('bajas', 0)
            ausencias_co = resumen_co.get('ausencias', 0)
            tasa_rot_co = bajas_co / total_e * 100 if total_e > 0 else 0
            tasa_aus_co = ausencias_co / total_e * 100 if total_e > 0 else 0
            score_co = max(0, min(100, 100 - tasa_rot_co * 2 - tasa_aus_co))
            emoji_co = "🟢" if score_co >= 70 else "🟡" if score_co >= 50 else "🔴"
            resp = (
                f"## Indicadores de Clima Organizacional\n\n"
                f"*(Basado en métricas objetivas de RRHH)*\n\n"
                f"| Indicador | Valor | Estado |\n|---|---:|---|\n"
                f"| 👥 Headcount | {total_e} | — |\n"
                f"| 📉 Tasa de rotación | {tasa_rot_co:.1f}% | {'🔴 Alta' if tasa_rot_co > 20 else '🟡 Moderada' if tasa_rot_co > 10 else '🟢 Baja'} |\n"
                f"| 🏖️ Tasa de ausentismo | {tasa_aus_co:.1f}% | {'🔴 Alta' if tasa_aus_co > 5 else '🟡 Moderada' if tasa_aus_co > 2 else '🟢 Normal'} |\n"
                f"| 🌡️ **Score clima** | **{score_co:.0f}/100** | **{emoji_co}** |\n\n"
                "> 💡 *Para análisis profundo de clima: implementar encuestas periódicas en Odoo.*"
            )
            return resp, None

        # ── cumplimiento_jornada ──────────────────────────────────────────────
        if accion == 'cumplimiento_jornada':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = []
                    if fi:
                        filtro.append(('check_in', '>=', fi))
                    if ff:
                        filtro.append(('check_in', '<=', ff))
                    df = self.odoo.buscar(
                        'hr.attendance', filtro=filtro,
                        campos=['employee_id', 'worked_hours', 'check_in'],
                        limite=1000
                    )
                    if df is not None and not df.empty:
                        df['horas'] = pd.to_numeric(df.get('worked_hours', 0), errors='coerce').fillna(0)
                        df['empleado'] = df.get('employee_id', pd.Series()).apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        agg = df.groupby('empleado').agg(dias=('horas', 'count'), horas_total=('horas', 'sum')).reset_index()
                        agg['horas_prom_dia'] = agg['horas_total'] / agg['dias'].replace(0, 1)
                        jornada = 8.0
                        agg['cumplimiento_pct'] = agg['horas_prom_dia'] / jornada * 100
                        resp = (
                            f"## Cumplimiento de Jornada\n\n**Período:** {fi} a {ff} | Jornada esperada: 8h\n\n"
                            f"| Empleado | Días | Horas prom./día | % Cumplimiento |\n|---|---:|---:|---:|\n"
                        )
                        for _, r in agg.sort_values('cumplimiento_pct').head(15).iterrows():
                            emoji_cj = "🟢" if float(r['cumplimiento_pct']) >= 95 else "🟡" if float(r['cumplimiento_pct']) >= 80 else "🔴"
                            resp += f"| {str(r['empleado'])[:30]} | {int(r['dias'])} | {float(r['horas_prom_dia']):.1f}h | {emoji_cj} {float(r['cumplimiento_pct']):.0f}% |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Cumplimiento de Jornada\n\nMódulo de asistencias no disponible.", None

        # ── estructura_organizacional ─────────────────────────────────────────
        if accion == 'estructura_organizacional':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'hr.employee',
                        filtro=[('active', '=', True)],
                        campos=['name', 'department_id', 'job_id', 'parent_id'],
                        limite=300
                    )
                    if df is not None and not df.empty:
                        df['depto'] = df.get('department_id', pd.Series()).apply(lambda x: x[1] if isinstance(x, (list, tuple)) else 'Sin departamento')
                        agg_depto = df.groupby('depto').size().reset_index(name='empleados').sort_values('empleados', ascending=False)
                        resp = (
                            f"## Estructura Organizacional\n\n"
                            f"**Total empleados activos:** {len(df):,}\n\n"
                            f"| Departamento | Empleados | % |\n|---|---:|---:|\n"
                        )
                        for _, r in agg_depto.iterrows():
                            pct = int(r['empleados']) / len(df) * 100
                            resp += f"| {r['depto']} | {int(r['empleados'])} | {pct:.1f}% |\n"
                        return resp, agg_depto
            except Exception:
                pass
            datos = self.analizador.analisis_empleados()
            df_dep = pd.DataFrame(datos.get('por_departamento', []))
            resp = f"## Estructura Organizacional\n\n**Total:** {datos.get('resumen', {}).get('total', 0)} empleados\n\n"
            return resp, df_dep if not df_dep.empty else None

        # ── incapacidades ─────────────────────────────────────────────────────
        if accion == 'incapacidades':
            try:
                if self.odoo and self.odoo.conectado:
                    filtro = [('state', '=', 'validate')]
                    if fi:
                        filtro.append(('date_from', '>=', fi))
                    if ff:
                        filtro.append(('date_from', '<=', ff))
                    df = self.odoo.buscar(
                        'hr.leave',
                        filtro=filtro,
                        campos=['employee_id', 'holiday_status_id', 'number_of_days', 'date_from', 'date_to'],
                        limite=300
                    )
                    if df is not None and not df.empty:
                        df['tipo'] = df.get('holiday_status_id', pd.Series()).apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['empleado'] = df.get('employee_id', pd.Series()).apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        df['dias'] = pd.to_numeric(df.get('number_of_days', 0), errors='coerce').fillna(0)
                        por_tipo = df.groupby('tipo')['dias'].sum().reset_index().sort_values('dias', ascending=False)
                        resp = (
                            f"## Análisis de Incapacidades / Ausencias\n\n**Período:** {fi} a {ff}\n\n"
                            f"**Total ausencias validadas:** {len(df):,} | **Días acumulados:** {float(df['dias'].sum()):,.0f}\n\n"
                            f"| Tipo de ausencia | Días totales |\n|---|---:|\n"
                        )
                        for _, r in por_tipo.iterrows():
                            resp += f"| {r['tipo']} | {float(r['dias']):.0f} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Incapacidades\n\nMódulo de ausencias no disponible o sin registros en el período.", None

        # ── prestaciones_resumen ──────────────────────────────────────────────
        if accion == 'prestaciones_resumen':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'hr.contract',
                        filtro=[('state', '=', 'open')],
                        campos=['employee_id', 'wage', 'job_id', 'department_id', 'date_start'],
                        limite=300
                    )
                    if df is not None and not df.empty and 'wage' in df.columns:
                        df['salario'] = pd.to_numeric(df['wage'], errors='coerce').fillna(0)
                        total_nomina = float(df['salario'].sum())
                        promedio_sal = float(df['salario'].mean())
                        n_contratos = len(df)
                        resp = (
                            f"## Resumen de Prestaciones y Contratos\n\n"
                            f"| Métrica | Valor |\n|---|---:|\n"
                            f"| 📄 Contratos activos | **{n_contratos:,}** |\n"
                            f"| 💰 Nómina mensual total | **${total_nomina:,.2f}** |\n"
                            f"| 📊 Salario promedio | **${promedio_sal:,.2f}** |\n"
                            f"| 🔼 Salario máximo | **${float(df['salario'].max()):,.2f}** |\n"
                            f"| 🔽 Salario mínimo | **${float(df['salario'].min()):,.2f}** |\n\n"
                            "> 💡 *Para prestaciones detalladas (IMSS, aguinaldo, vacaciones), configura los conceptos en la nómina de Odoo.*"
                        )
                        return resp, df
            except Exception:
                pass
            datos_pr = self.analizador.analisis_empleados()
            resp = (
                f"## Prestaciones y Contratos\n\n"
                f"**Empleados activos:** {datos_pr.get('resumen', {}).get('total', 0)}\n\n"
                "> 💡 *Módulo de contratos/nómina requerido para detalle de prestaciones.*"
            )
            return resp, None

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_predicciones(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')

        if accion == 'forecast_estacional':
            datos = self.predictor.analizar_estacionalidad()
            if 'error' not in datos:
                resp = self.fmt._formatear_estacionalidad(datos)
                df = pd.DataFrame(datos.get('por_dia_semana', []))
                return resp, df if not df.empty else None
            return f"{datos.get('error')}", None

        if accion == 'prediccion_flujo_caja':
            datos = self.predictor.predecir_flujo_caja()
            if 'error' not in datos:
                resp = self.fmt._formatear_flujo_caja(datos)
                return resp, None
            return f"{datos.get('error')}", None

        if accion == 'score_salud_negocio':
            datos = self.predictor.score_salud_negocio()
            if 'error' not in datos:
                resp = self.fmt._formatear_salud_negocio(datos)
                return resp, None
            return f"{datos.get('error')}", None

        if accion == 'escenarios_what_if' and self.predictor:
            datos = self.predictor.comparar_periodos('mes')
            if 'error' not in datos:
                resp = "## Escenarios What-If\n\n"
                resp += self.fmt._formatear_comparativa(datos)
                return resp, None
            return f"{datos.get('error')}", None

        # ── simulacion_montecarlo ────────────────────────────────────────────
        if accion == 'simulacion_montecarlo':
            import math, random
            temp = getattr(consulta, 'temporalidad', {}) or {}
            fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')
            params = getattr(consulta, 'parametros', {}) or {}
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            ventas_mes = datos.get('resumen', {}).get('total_ventas', 0) / 12 or 100000
            iteraciones = int(params.get('iteraciones', 1000))
            n_meses = int(params.get('meses', 6))
            tasa_media = float(params.get('tasa_crecimiento', 0.03))
            tasa_std = float(params.get('volatilidad', 0.10))
            resultados = []
            random.seed(42)
            for _ in range(min(iteraciones, 1000)):
                acum = ventas_mes
                for _ in range(n_meses):
                    r = random.gauss(tasa_media, tasa_std)
                    acum *= (1 + r)
                resultados.append(acum)
            resultados.sort()
            p5 = resultados[int(0.05 * len(resultados))]
            p50 = resultados[int(0.50 * len(resultados))]
            p95 = resultados[int(0.95 * len(resultados))]
            media_res = sum(resultados) / len(resultados)
            resp = (
                f"## Simulación Montecarlo — Proyección de Ventas\n\n"
                f"**Base:** ${ventas_mes:,.2f}/mes | **Iteraciones:** {min(iteraciones, 1000)} | **Horizonte:** {n_meses} meses\n\n"
                f"| Percentil | Ventas Proyectadas |\n|---|---:|\n"
                f"| P5 (pesimista) | **${p5:,.2f}** |\n"
                f"| P50 (mediana) | **${p50:,.2f}** |\n"
                f"| Media esperada | **${media_res:,.2f}** |\n"
                f"| P95 (optimista) | **${p95:,.2f}** |\n\n"
                f"**Tasa crecimiento:** {tasa_media*100:.1f}% ± {tasa_std*100:.1f}% (desv. mensual)\n\n"
                f"> ⚠️ *Simulación con distribución normal. Ajusta la volatilidad según tu industria.*"
            )
            return resp, None

        # ── forecast_financiero ──────────────────────────────────────────────
        if accion == 'forecast_financiero':
            temp = getattr(consulta, 'temporalidad', {}) or {}
            fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')
            params = getattr(consulta, 'parametros', {}) or {}
            datos = self.predictor.predecir_flujo_caja()
            if 'error' not in datos:
                resp = "## Forecast Financiero\n\n" + self.fmt._formatear_flujo_caja(datos)
                return resp, None
            # fallback: proyección basada en ventas
            datos_v = self.analizador.analisis_ventas_completo(fi, ff)
            ventas = datos_v.get('resumen', {}).get('total_ventas', 0)
            meses = int(params.get('meses', 6))
            base = ventas / 12 or 0
            filas = [{'Mes': i+1, 'Ingresos': base*(1.03**i), 'Egresos': base*0.65*(1.02**i),
                      'Flujo': base*(1.03**i) - base*0.65*(1.02**i)} for i in range(meses)]
            df = pd.DataFrame(filas)
            resp = (
                f"## Forecast Financiero — {meses} meses\n\n"
                f"**Base mensual:** ${base:,.2f}\n\n"
                f"| Mes | Ingresos | Egresos | Flujo Neto |\n|---|---:|---:|---:|\n"
            )
            for _, r in df.iterrows():
                emoji = "🟢" if r['Flujo'] > 0 else "🔴"
                resp += f"| {int(r['Mes'])} | ${r['Ingresos']:,.2f} | ${r['Egresos']:,.2f} | {emoji} ${r['Flujo']:,.2f} |\n"
            return resp, df

        # ── forecast_inventario ──────────────────────────────────────────────
        if accion == 'forecast_inventario':
            temp = getattr(consulta, 'temporalidad', {}) or {}
            fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')
            params = getattr(consulta, 'parametros', {}) or {}
            datos_inv = self.analizador.analisis_inventario()
            productos = datos_inv.get('productos_bajo_stock', [])
            meses = int(params.get('meses', 3))
            resp = (
                f"## Forecast de Inventario — {meses} meses\n\n"
                f"**Productos en riesgo de quiebre de stock:**\n\n"
                f"| Producto | Stock actual | Consumo mensual est. | Meses restantes |\n|---|---:|---:|---:|\n"
            )
            if productos:
                for p in productos[:10]:
                    nombre = str(p.get('name', ''))[:35]
                    stock = float(p.get('qty_available', p.get('stock', 0)))
                    consumo = float(p.get('consumo_mensual', stock / 3 if stock > 0 else 1))
                    meses_rest = stock / consumo if consumo > 0 else 99
                    emoji = "🔴" if meses_rest < 1 else "🟡" if meses_rest < 2 else "🟢"
                    resp += f"| {nombre} | {stock:.0f} | {consumo:.0f} | {emoji} {meses_rest:.1f} |\n"
            else:
                resp += "| Sin productos en riesgo | — | — | 🟢 OK |\n"
            return resp, pd.DataFrame(productos) if productos else None

        # ── proyeccion_crecimiento ────────────────────────────────────────────
        if accion == 'proyeccion_crecimiento':
            temp = getattr(consulta, 'temporalidad', {}) or {}
            fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')
            params = getattr(consulta, 'parametros', {}) or {}
            datos = self.predictor.comparar_periodos('mes')
            if 'error' not in datos:
                resp = "## Proyección de Crecimiento\n\n"
                variacion = datos.get('variacion_pct', 0)
                actual = datos.get('actual', {}).get('total', 0)
                anterior = datos.get('anterior', {}).get('total', 0)
                resp += (
                    f"| Período | Ventas |\n|---|---:|\n"
                    f"| Mes anterior | ${anterior:,.2f} |\n"
                    f"| Mes actual | ${actual:,.2f} |\n"
                    f"| Variación | **{variacion:+.1f}%** |\n\n"
                )
                meses = int(params.get('meses', 6))
                resp += f"**Proyección {meses} meses con tasa {variacion:.1f}%/mes:**\n\n"
                resp += "| Mes | Proyección |\n|---|---:|\n"
                base = actual
                for i in range(1, meses + 1):
                    base *= (1 + variacion / 100)
                    resp += f"| +{i} mes | ${base:,.2f} |\n"
                return resp, None
            return "No hay datos suficientes para proyectar crecimiento.", None

        # ── prediccion_demanda / prediccion_demanda_producto ──────────────────
        if accion in ('prediccion_demanda', 'prediccion_demanda_producto'):
            temp = getattr(consulta, 'temporalidad', {}) or {}
            fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')
            params = getattr(consulta, 'parametros', {}) or {}
            datos_est = self.predictor.analizar_estacionalidad()
            datos_v = self.analizador.analisis_ventas_completo(fi, ff)
            ventas_mes = datos_v.get('resumen', {}).get('total_ventas', 0) / 12 or 0
            meses = int(params.get('meses', 3))
            resp = (
                f"## Predicción de Demanda\n\n"
                f"**Demanda promedio mensual:** ${ventas_mes:,.2f}\n\n"
            )
            if 'error' not in datos_est and datos_est.get('tendencia'):
                resp += f"**Tendencia detectada:** {datos_est['tendencia']}\n\n"
            resp += f"| Mes | Demanda Estimada |\n|---|---:|\n"
            for i in range(1, meses + 1):
                factor = 1.02 ** i
                resp += f"| +{i} mes | ${ventas_mes * factor:,.2f} |\n"
            resp += "\n> ⚠️ *Predicción por promedio móvil con tendencia +2%/mes. Para mayor precisión activa el módulo de forecasting.*"
            return resp, None

        # ── alertas_predictivas ──────────────────────────────────────────────
        if accion == 'alertas_predictivas':
            alertas = []
            try:
                datos_inv = self.analizador.analisis_inventario()
                bajo_stock = datos_inv.get('productos_bajo_stock', [])
                if bajo_stock:
                    alertas.append(f"🔴 **Inventario:** {len(bajo_stock)} productos con stock crítico")
            except Exception:
                pass
            try:
                datos_v = self.analizador.analisis_ventas_completo('', '')
                ventas = datos_v.get('resumen', {}).get('total_ventas', 0)
                comp = self.predictor.comparar_periodos('mes')
                if 'error' not in comp and comp.get('variacion_pct', 0) < -10:
                    alertas.append(f"🔴 **Ventas:** caída de {comp['variacion_pct']:.1f}% vs mes anterior")
            except Exception:
                pass
            try:
                datos_crm = self.analizador.analisis_crm_pipeline()
                perdidos = datos_crm.get('resumen', {}).get('perdidos', 0)
                if perdidos > 5:
                    alertas.append(f"🟡 **CRM:** {perdidos} oportunidades perdidas recientemente")
            except Exception:
                pass
            resp = "## Alertas Predictivas\n\n"
            if alertas:
                for a in alertas:
                    resp += f"- {a}\n"
            else:
                resp += "✅ No se detectaron alertas críticas en este momento.\n"
            resp += "\n> 💡 *Las alertas se generan comparando indicadores actuales vs umbrales históricos.*"
            return resp, None

        # ── prediccion_rotacion_personal ──────────────────────────────────────
        if accion == 'prediccion_rotacion_personal':
            datos = self.analizador.analisis_headcount()
            resumen = datos.get('resumen', {})
            total = resumen.get('total_empleados', 0)
            bajas = resumen.get('bajas_periodo', 0)
            tasa_rot = (bajas / total * 100) if total > 0 else 0
            resp = (
                f"## Predicción de Rotación de Personal\n\n"
                f"| Métrica | Valor |\n|---|---:|\n"
                f"| 👥 Empleados activos | **{total}** |\n"
                f"| 📉 Bajas en el período | **{bajas}** |\n"
                f"| 🔄 Tasa de rotación | **{tasa_rot:.1f}%** |\n\n"
            )
            nivel = "Alta 🔴" if tasa_rot > 20 else "Moderada 🟡" if tasa_rot > 10 else "Normal 🟢"
            resp += f"**Nivel de rotación:** {nivel}\n\n"
            if tasa_rot > 20:
                resp += "⚠️ **Acción recomendada:** Revisar clima laboral, compensaciones y plan de carrera.\n"
            elif tasa_rot > 10:
                resp += "🟡 **Atención:** Rotación por encima del promedio. Identificar áreas o perfiles con mayor riesgo.\n"
            else:
                resp += "🟢 **Rotación controlada.** Monitorear trimestralmente.\n"
            return resp, None

        # ── modelo_propension_compra ──────────────────────────────────────────
        if accion == 'modelo_propension_compra':
            temp = getattr(consulta, 'temporalidad', {}) or {}
            fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            resp = f"## Modelo de Propensión de Compra\n\n**Período:** {fi} a {ff}\n\n"
            if df is not None and not df.empty and 'total' in df.columns:
                col = pd.to_numeric(df['total'], errors='coerce').fillna(0)
                p66 = float(col.quantile(0.66))
                clientes_alta = int((col >= p66).sum())
                resp += (
                    f"| Segmento | Clientes | Acción sugerida |\n|---|---:|---|\n"
                    f"| 🟢 Alta propensión (≥P66) | {clientes_alta} | Ofertas exclusivas, upselling |\n"
                    f"| 🟡 Media propensión | {int((col.between(col.quantile(0.33), p66)).sum())} | Email marketing, demos |\n"
                    f"| 🔴 Baja propensión (<P33) | {int((col < col.quantile(0.33)).sum())} | Reactivación, descuentos |"
                )
            else:
                resp += "No hay datos de clientes para el modelo."
            return resp, df

        # ── deteccion_tendencia_cambio ────────────────────────────────────────
        if accion == 'deteccion_tendencia_cambio':
            datos = self.predictor.comparar_periodos('mes')
            if 'error' not in datos:
                var_mes = datos.get('variacion_pct', 0)
                datos_t = self.predictor.comparar_periodos('trimestre')
                var_trim = datos_t.get('variacion_pct', 0) if 'error' not in datos_t else 0
                resp = (
                    f"## Detección de Cambio de Tendencia\n\n"
                    f"| Período | Variación |\n|---|---:|\n"
                    f"| Mes a mes | **{var_mes:+.1f}%** |\n"
                    f"| Trimestre | **{var_trim:+.1f}%** |\n\n"
                )
                if var_mes < -10 and var_trim < -5:
                    resp += "🔴 **Cambio de tendencia negativo detectado.** Las ventas muestran caída sostenida. Acción inmediata requerida.\n"
                elif var_mes > 10 and var_trim > 5:
                    resp += "🟢 **Tendencia positiva confirmada.** Crecimiento sostenido. Aprovechar momentum.\n"
                elif abs(var_mes - var_trim) > 15:
                    resp += "🟡 **Cambio brusco detectado.** El mes actual difiere significativamente del trimestre. Investigar causas.\n"
                else:
                    resp += "🟢 **Tendencia estable.** No se detectan cambios estructurales significativos.\n"
                return resp, None
            return "No hay datos para detectar cambios de tendencia.", None

        # ── forecast_multiproducto ────────────────────────────────────────────
        if accion == 'forecast_multiproducto':
            temp = getattr(consulta, 'temporalidad', {}) or {}
            fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')
            params = getattr(consulta, 'parametros', {}) or {}
            datos = self.analizador.top_productos_vendidos(fi, ff)
            meses = int(params.get('meses', 3))
            if 'error' not in datos and datos.get('productos'):
                df = pd.DataFrame(datos['productos'])
                resp = (
                    f"## Forecast Multiproducto — {meses} meses\n\n"
                    f"| Producto | Ventas base | Proy. +{meses}m |\n|---|---:|---:|\n"
                )
                for _, r in df.head(10).iterrows():
                    nombre = str(r.get('name', r.get('product', '')))[:35]
                    t = float(r.get('total', 0))
                    proy = t * (1.025 ** meses)
                    resp += f"| {nombre} | ${t:,.2f} | ${proy:,.2f} |\n"
                return resp, df
            return "No hay datos de productos para el forecast multiproducto.", None

        # ── backtesting_modelo ────────────────────────────────────────────────
        if accion == 'backtesting_modelo':
            datos = self.predictor.comparar_periodos('mes')
            if 'error' not in datos:
                actual = datos.get('actual', {}).get('total', 0)
                anterior = datos.get('anterior', {}).get('total', 0)
                pred_simple = anterior * 1.03
                error_pct = abs(pred_simple - actual) / actual * 100 if actual > 0 else 0
                mape = error_pct
                resp = (
                    f"## Backtesting del Modelo de Predicción\n\n"
                    f"**Metodología:** Naive forecast (mes anterior × 1.03)\n\n"
                    f"| Métrica | Valor |\n|---|---:|\n"
                    f"| Valor real (mes actual) | ${actual:,.2f} |\n"
                    f"| Predicción (mes anterior +3%) | ${pred_simple:,.2f} |\n"
                    f"| Error absoluto | ${abs(pred_simple - actual):,.2f} |\n"
                    f"| MAPE (error %) | **{mape:.1f}%** |\n\n"
                    f"{'🟢 Modelo con buena precisión (MAPE < 10%)' if mape < 10 else '🟡 Precisión moderada (10-20%)' if mape < 20 else '🔴 Alta imprecisión (MAPE > 20%). Ajustar modelo.'}\n\n"
                    f"> 💡 *Para backtesting de modelos ML/SARIMA se requieren al menos 24 meses de historico.*"
                )
                return resp, None
            return "No hay datos suficientes para backtesting.", None

        # ── intervalos_confianza ──────────────────────────────────────────────
        if accion == 'intervalos_confianza':
            import math
            temp = getattr(consulta, 'temporalidad', {}) or {}
            fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            if df is not None and not df.empty and 'total' in df.columns:
                col = pd.to_numeric(df['total'], errors='coerce').dropna()
                n = len(col)
                media = float(col.mean())
                desv = float(col.std(ddof=1)) if n > 1 else 0
                se = desv / math.sqrt(n) if n > 0 else 0
                z95, z99 = 1.96, 2.576
                ic95_l, ic95_u = media - z95 * se, media + z95 * se
                ic99_l, ic99_u = media - z99 * se, media + z99 * se
                resp = (
                    f"## Intervalos de Confianza — Ventas por Cliente\n\n"
                    f"**n = {n:,}** | **Media = ${media:,.2f}** | **Desv. = ${desv:,.2f}**\n\n"
                    f"| Confianza | Límite inferior | Límite superior |\n|---|---:|---:|\n"
                    f"| 95% | ${ic95_l:,.2f} | ${ic95_u:,.2f} |\n"
                    f"| 99% | ${ic99_l:,.2f} | ${ic99_u:,.2f} |\n\n"
                    f"> 💡 *IC 95% significa que el 95% de las veces la media verdadera está dentro de ese rango.*"
                )
                return resp, df
            return "No hay suficientes datos para calcular intervalos de confianza.", None

        # ── proyeccion_ventas ─────────────────────────────────────────────────
        if accion == 'proyeccion_ventas':
            import re as _re
            from datetime import datetime, timedelta
            # Extraer días solicitados del mensaje (ej. "próximos 90 días", "60 días", "3 meses")
            dias_proyeccion = 90  # default
            m_dias = _re.search(r'(\d+)\s*d[ií]as?', mensaje, _re.IGNORECASE)
            m_meses = _re.search(r'(\d+)\s*meses?', mensaje, _re.IGNORECASE)
            m_sem = _re.search(r'(\d+)\s*semanas?', mensaje, _re.IGNORECASE)
            if m_dias:
                dias_proyeccion = int(m_dias.group(1))
            elif m_meses:
                dias_proyeccion = int(m_meses.group(1)) * 30
            elif m_sem:
                dias_proyeccion = int(m_sem.group(1)) * 7
            dias_proyeccion = max(7, min(dias_proyeccion, 365))

            # Base histórica: últimos 90 días de ventas reales para calcular tasa y promedio
            try:
                hoy = datetime.now()
                hace_90 = (hoy - timedelta(days=90)).strftime('%Y-%m-%d')
                hoy_str = hoy.strftime('%Y-%m-%d')

                df_hist = None
                if self.odoo and self.odoo.conectado:
                    df_hist = self.odoo.buscar(
                        'sale.order',
                        filtro=[
                            ('state', 'in', ['sale', 'done']),
                            ('date_order', '>=', hace_90),
                            ('date_order', '<=', hoy_str),
                        ],
                        campos=['date_order', 'amount_total'],
                        limite=0,
                    )

                if df_hist is None or df_hist.empty:
                    # fallback al analizador
                    datos = self.analizador.analisis_ventas_completo(hace_90, hoy_str)
                    total_hist = datos.get('resumen', {}).get('total_ventas', 0)
                    promedio_diario = total_hist / 90 if total_hist > 0 else 0
                    tasa_diaria = 0.0
                else:
                    df_hist = df_hist.copy()
                    df_hist['fecha'] = df_hist['date_order'].astype(str).str[:10]
                    df_hist['monto'] = pd.to_numeric(df_hist['amount_total'], errors='coerce').fillna(0)
                    por_dia = df_hist.groupby('fecha')['monto'].sum().reset_index()
                    por_dia = por_dia.sort_values('fecha')
                    promedio_diario = float(por_dia['monto'].mean()) if not por_dia.empty else 0

                    # Tasa de crecimiento diaria por regresión lineal simple
                    n = len(por_dia)
                    if n >= 7:
                        y = por_dia['monto'].values
                        x = list(range(n))
                        x_mean = sum(x) / n
                        y_mean = sum(y) / n
                        slope = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y)) / \
                                sum((xi - x_mean) ** 2 for xi in x) if sum((xi - x_mean) ** 2 for xi in x) != 0 else 0
                        tasa_diaria = slope / promedio_diario if promedio_diario > 0 else 0.0
                    else:
                        tasa_diaria = 0.0

                # Limitar tasa diaria a ±5% para evitar proyecciones absurdas
                tasa_diaria = max(-0.05, min(0.05, tasa_diaria))

                # Construir proyección día a día (o semana a semana si horizonte > 60d)
                proyeccion = []
                base = promedio_diario
                usar_semanas = dias_proyeccion > 60
                agrupacion = 7 if usar_semanas else 1
                etiqueta = "Semana" if usar_semanas else "Día"
                iteraciones = dias_proyeccion // agrupacion

                for i in range(iteraciones):
                    base_iter = base * ((1 + tasa_diaria * agrupacion) ** i)
                    fecha_inicio_iter = hoy + timedelta(days=i * agrupacion + 1)
                    fecha_label = fecha_inicio_iter.strftime('%Y-%m-%d')
                    pesimista = base_iter * 0.80
                    optimista = base_iter * 1.20
                    proyeccion.append({
                        etiqueta: fecha_label,
                        'Base': base_iter * agrupacion,
                        'Pesimista': pesimista * agrupacion,
                        'Optimista': optimista * agrupacion,
                    })

                df_proy = pd.DataFrame(proyeccion)
                total_base = float(df_proy['Base'].sum())
                total_pesi = float(df_proy['Pesimista'].sum())
                total_opti = float(df_proy['Optimista'].sum())

                tendencia_txt = (
                    "📈 Crecimiento" if tasa_diaria > 0.001 else
                    "📉 Decrecimiento" if tasa_diaria < -0.001 else
                    "➖ Estable"
                )

                resp = (
                    f"## Proyección de Ventas — Próximos {dias_proyeccion} días\n\n"
                    f"**Base histórica:** últimos 90 días | "
                    f"**Promedio diario:** ${promedio_diario:,.2f} | "
                    f"**Tendencia:** {tendencia_txt} ({tasa_diaria*100:+.2f}%/día)\n\n"
                    f"| Escenario | Total proyectado |\n|---|---:|\n"
                    f"| 🔴 Pesimista (−20%) | **${total_pesi:,.2f}** |\n"
                    f"| ⚪ Base | **${total_base:,.2f}** |\n"
                    f"| 🟢 Optimista (+20%) | **${total_opti:,.2f}** |\n\n"
                    f"**Desglose por {etiqueta.lower()}:**\n\n"
                    f"| {etiqueta} | Pesimista | Base | Optimista |\n|---|---:|---:|---:|\n"
                )
                for _, r in df_proy.iterrows():
                    resp += (
                        f"| {r[etiqueta]} | ${float(r['Pesimista']):,.2f} | "
                        f"${float(r['Base']):,.2f} | ${float(r['Optimista']):,.2f} |\n"
                    )
                resp += (
                    f"\n> ⚠️ *Proyección por tendencia lineal sobre histórico de 90 días. "
                    f"No considera estacionalidad, promociones ni factores externos. "
                    f"Para mayor precisión usa la simulación Montecarlo.*"
                )
                return resp, df_proy

            except Exception:
                import traceback; traceback.print_exc()
            return (
                f"## Proyección de Ventas — {dias_proyeccion} días\n\n"
                "No se pudo obtener el histórico de ventas para proyectar. "
                "Verifica la conexión con Odoo.", None
            )



    def _ejecutor_diagnostico(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        temp = getattr(consulta, 'temporalidad', {}) or {}
        fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')

        if accion == 'campos_vacios_criticos' and self.conector:
            try:
                datos = self.conector.buscar(
                    'res.partner',
                    filtro=[('active', '=', True), ('customer_rank', '>', 0)],
                    campos=['name', 'email', 'phone', 'vat', 'street'],
                    limite=300
                )
                if datos is not None and not datos.empty:
                    nulos_por_col = datos.isna().sum()
                    resp = "## Campos Vacíos en Clientes\n\n"
                    resp += f"**Clientes analizados:** {len(datos)}\n\n"
                    resp += "| Campo | Vacíos | % |\n|---|---:|---:|\n"
                    for col in ['email', 'phone', 'vat', 'street']:
                        if col in nulos_por_col:
                            n = int(nulos_por_col[col])
                            pct = n / len(datos) * 100
                            resp += f"| {col} | {n} | {pct:.1f}% |\n"
                    return resp, datos
            except Exception:
                pass

        if accion == 'salud_base_datos':
            datos = self.analizador.analisis_usuarios()
            resp = "## Salud de la Base de Datos\n\n"
            if 'resumen' in datos:
                r = datos['resumen']
                resp += f"- **Usuarios totales:** {r.get('total', 0)}\n"
                resp += f"- **Activos (7d):** {r.get('activos_7d', 0)}\n"
                resp += f"- **Inactivos (30d):** {r.get('inactivos_30d', 0)}\n"
            df = pd.DataFrame(datos.get('usuarios', []))
            return resp, df if not df.empty else None

        # ── validacion_cruzada ────────────────────────────────────────────────
        if accion == 'validacion_cruzada':
            datos_vc_v = self.analizador.analisis_ventas_completo(fi, ff)
            datos_vc_f = self.analizador.analisis_facturacion(fi, ff)
            ventas_vc = datos_vc_v.get('resumen', {}).get('total_ventas', 0)
            facturado_vc = datos_vc_f.get('resumen', {}).get('total_facturado', 0)
            diff_vc = abs(ventas_vc - facturado_vc)
            pct_diff = diff_vc / ventas_vc * 100 if ventas_vc > 0 else 0
            emoji_vc = "🟢" if pct_diff < 2 else "🟡" if pct_diff < 5 else "🔴"
            resp = (
                f"## Validación Cruzada: Ventas vs. Facturación\n\n**Período:** {fi} a {ff}\n\n"
                f"| Fuente | Importe |\n|---|---:|\n"
                f"| 📊 Ventas (órdenes confirmadas) | **${ventas_vc:,.2f}** |\n"
                f"| 🧾 Facturación (account.move) | **${facturado_vc:,.2f}** |\n"
                f"| ⚠️ Diferencia | **{emoji_vc} ${diff_vc:,.2f} ({pct_diff:.1f}%)** |\n\n"
            )
            if pct_diff > 5:
                resp += "🔴 **Diferencia significativa**: revisar órdenes sin facturar o facturas sin orden de venta.\n"
            elif pct_diff > 2:
                resp += "🟡 **Diferencia moderada**: verificar devoluciones y notas de crédito.\n"
            else:
                resp += "🟢 **Validación OK**: diferencia dentro del margen aceptable.\n"
            return resp, None

        # ── consistencia_datos ────────────────────────────────────────────────
        if accion == 'consistencia_datos':
            alertas_cd = []
            try:
                if self.odoo and self.odoo.conectado:
                    df_neg = self.odoo.buscar(
                        'stock.quant', filtro=[('quantity', '<', 0), ('location_id.usage', '=', 'internal')],
                        campos=['product_id', 'quantity', 'location_id'], limite=50
                    )
                    if df_neg is not None and not df_neg.empty:
                        alertas_cd.append(f"🔴 **{len(df_neg)} productos** con stock negativo")
            except Exception:
                pass
            try:
                if self.odoo and self.odoo.conectado:
                    df_sin_precio = self.odoo.buscar(
                        'product.product', filtro=[('list_price', '=', 0), ('active', '=', True)],
                        campos=['name'], limite=50
                    )
                    if df_sin_precio is not None and not df_sin_precio.empty:
                        alertas_cd.append(f"🟡 **{len(df_sin_precio)} productos** con precio de venta = 0")
            except Exception:
                pass
            try:
                if self.odoo and self.odoo.conectado:
                    df_sin_cat = self.odoo.buscar(
                        'product.product', filtro=[('categ_id', '=', False), ('active', '=', True)],
                        campos=['name'], limite=50
                    )
                    if df_sin_cat is not None and not df_sin_cat.empty:
                        alertas_cd.append(f"🟡 **{len(df_sin_cat)} productos** sin categoría asignada")
            except Exception:
                pass
            resp = f"## Consistencia de Datos\n\n"
            if alertas_cd:
                resp += "\n".join(f"- {a}" for a in alertas_cd)
                resp += "\n\n> 💡 *Corrige estas inconsistencias para mejorar la calidad de tus reportes.*"
            else:
                resp += "✅ No se detectaron inconsistencias críticas en los datos revisados."
            return resp, None

        # ── registros_duplicados ──────────────────────────────────────────────
        if accion == 'registros_duplicados':
            try:
                if self.odoo and self.odoo.conectado:
                    df_partners = self.odoo.buscar(
                        'res.partner', filtro=[('active', '=', True), ('customer_rank', '>', 0)],
                        campos=['name', 'email', 'vat'], limite=500
                    )
                    duplicados_nombre = 0
                    duplicados_email = 0
                    duplicados_rfc = 0
                    if df_partners is not None and not df_partners.empty:
                        if 'name' in df_partners.columns:
                            dup = df_partners['name'].str.lower().str.strip().duplicated(keep=False)
                            duplicados_nombre = int(dup.sum())
                        if 'email' in df_partners.columns:
                            emails = df_partners['email'].dropna().str.lower().str.strip()
                            emails = emails[emails != '']
                            dup_e = emails.duplicated(keep=False)
                            duplicados_email = int(dup_e.sum())
                        if 'vat' in df_partners.columns:
                            vats = df_partners['vat'].dropna().str.strip()
                            vats = vats[vats != '']
                            dup_v = vats.duplicated(keep=False)
                            duplicados_rfc = int(dup_v.sum())
                    resp = (
                        f"## Detección de Registros Duplicados\n\n"
                        f"**Análisis de res.partner (clientes):**\n\n"
                        f"| Criterio | Posibles duplicados |\n|---|---:|\n"
                        f"| 📋 Nombre similar | {'🔴 ' if duplicados_nombre > 5 else ''}{duplicados_nombre} |\n"
                        f"| 📧 Email duplicado | {'🔴 ' if duplicados_email > 0 else '✅ '}{duplicados_email} |\n"
                        f"| 🆔 RFC/Tax ID duplicado | {'🔴 ' if duplicados_rfc > 0 else '✅ '}{duplicados_rfc} |\n\n"
                    )
                    if duplicados_email > 0 or duplicados_rfc > 0:
                        resp += "⚠️ **Acción requerida:** Fusionar registros duplicados para mantener integridad del CRM.\n"
                    return resp, df_partners
            except Exception:
                pass
            return "## Registros Duplicados\n\nNo se pudo analizar. Verifica la conexión con Odoo.", None

        # ── reconciliacion_stock_contable ─────────────────────────────────────
        if accion == 'reconciliacion_stock_contable':
            try:
                if self.odoo and self.odoo.conectado:
                    df_stock = self.odoo.buscar(
                        'stock.valuation.layer', filtro=[],
                        campos=['product_id', 'value', 'quantity'], limite=300
                    )
                    datos_inv = self.analizador.analisis_inventario()
                    val_cont = float(df_stock['value'].sum()) if df_stock is not None and not df_stock.empty else 0
                    val_sistema = datos_inv.get('valoracion', {}).get('total', 0) or 0
                    diff_rc = abs(val_cont - val_sistema)
                    resp = (
                        f"## Reconciliación Stock vs. Contabilidad\n\n"
                        f"| Fuente | Valoración |\n|---|---:|\n"
                        f"| 📦 Stock (inventario) | **${val_sistema:,.2f}** |\n"
                        f"| 📒 Contabilidad (valuación) | **${val_cont:,.2f}** |\n"
                        f"| ⚠️ Diferencia | **${diff_rc:,.2f}** |\n\n"
                    )
                    if diff_rc > val_sistema * 0.01:
                        resp += "🔴 **Diferencia significativa**: revisar ajustes de inventario y asientos contables.\n"
                    else:
                        resp += "🟢 **Reconciliación OK**: diferencia dentro del 1% aceptable.\n"
                    return resp, df_stock
            except Exception:
                pass
            return "## Reconciliación Stock-Contabilidad\n\nMódulo de valoración de inventario no disponible.", None

        # ── integridad_referencial ────────────────────────────────────────────
        if accion == 'integridad_referencial':
            alertas_ir = []
            try:
                if self.odoo and self.odoo.conectado:
                    df_lineas_sin_order = self.odoo.buscar(
                        'sale.order.line', filtro=[('order_id', '=', False)],
                        campos=['id'], limite=10
                    )
                    if df_lineas_sin_order is not None and len(df_lineas_sin_order) > 0:
                        alertas_ir.append(f"🔴 {len(df_lineas_sin_order)} líneas de venta sin orden padre")
            except Exception:
                pass
            try:
                if self.odoo and self.odoo.conectado:
                    df_mov_sin_prod = self.odoo.buscar(
                        'stock.move', filtro=[('product_id', '=', False), ('state', '!=', 'cancel')],
                        campos=['id'], limite=10
                    )
                    if df_mov_sin_prod is not None and len(df_mov_sin_prod) > 0:
                        alertas_ir.append(f"🔴 {len(df_mov_sin_prod)} movimientos de stock sin producto")
            except Exception:
                pass
            resp = f"## Integridad Referencial\n\n"
            if alertas_ir:
                resp += "**Problemas detectados:**\n\n" + "\n".join(f"- {a}" for a in alertas_ir)
                resp += "\n\n> ⚠️ *Estos registros huérfanos pueden causar errores en reportes.*"
            else:
                resp += "✅ No se detectaron problemas de integridad referencial en los modelos revisados."
            return resp, None

        # ── secuencias_rotas ──────────────────────────────────────────────────
        if accion == 'secuencias_rotas':
            try:
                if self.odoo and self.odoo.conectado:
                    df_seq = self.odoo.buscar(
                        'ir.sequence', filtro=[('active', '=', True)],
                        campos=['name', 'prefix', 'number_next', 'number_increment'],
                        limite=50
                    )
                    if df_seq is not None and not df_seq.empty:
                        resp = (
                            f"## Estado de Secuencias del Sistema\n\n"
                            f"| Secuencia | Prefijo | Siguiente número |\n|---|---|---:|\n"
                        )
                        for _, r in df_seq.head(15).iterrows():
                            resp += f"| {str(r.get('name', ''))[:35]} | {r.get('prefix', '')} | {r.get('number_next', '')} |\n"
                        resp += f"\n**Total secuencias activas:** {len(df_seq):,}\n\n> 💡 *Verifica manualmente si existen huecos en las secuencias de facturas en Contabilidad.*"
                        return resp, df_seq
            except Exception:
                pass
            return "## Secuencias del Sistema\n\nNo se pudieron obtener las secuencias de Odoo.", None

        # ── configuraciones_riesgosas ─────────────────────────────────────────
        if accion == 'configuraciones_riesgosas':
            try:
                if self.odoo and self.odoo.conectado:
                    df_admin = self.odoo.buscar(
                        'res.users',
                        filtro=[('active', '=', True), ('groups_id.full_name', 'ilike', 'Administración')],
                        campos=['name', 'login', 'groups_id'],
                        limite=50
                    )
                    n_admin = len(df_admin) if df_admin is not None else 0
                    resp = (
                        f"## Configuraciones de Riesgo\n\n"
                        f"| Riesgo | Estado |\n|---|---|\n"
                        f"| 👑 Usuarios con permisos de administrador | {'🔴 ' if n_admin > 3 else '🟢 '}{n_admin} usuarios |\n\n"
                    )
                    if n_admin > 3:
                        resp += "⚠️ **Riesgo alto**: demasiados administradores. Aplicar principio de mínimo privilegio.\n"
                    if df_admin is not None and not df_admin.empty:
                        resp += "\n**Usuarios administradores:**\n\n| Usuario | Login |\n|---|---|\n"
                        for _, r in df_admin.head(10).iterrows():
                            resp += f"| {r.get('name', '')} | {r.get('login', '')} |\n"
                    return resp, df_admin
            except Exception:
                pass
            return "## Configuraciones Riesgosas\n\nNo se pudieron obtener los usuarios administradores.", None

        # ── accesos_inusuales ─────────────────────────────────────────────────
        if accion == 'accesos_inusuales':
            try:
                if self.odoo and self.odoo.conectado:
                    from datetime import date as _dt_ai, timedelta
                    hace_7 = (_dt_ai.today() - timedelta(days=7)).strftime('%Y-%m-%d')
                    df = self.odoo.buscar(
                        'res.users',
                        filtro=[('active', '=', True), ('login_date', '>=', hace_7)],
                        campos=['name', 'login', 'login_date'],
                        limite=100
                    )
                    if df is not None and not df.empty:
                        resp = (
                            f"## Accesos Recientes (últimos 7 días)\n\n"
                            f"**{len(df):,} usuarios** con acceso reciente:\n\n"
                            f"| Usuario | Login | Último acceso |\n|---|---|---|\n"
                        )
                        for _, r in df.sort_values('login_date', ascending=False).head(15).iterrows():
                            resp += f"| {r.get('name', '')} | {r.get('login', '')} | {str(r.get('login_date', ''))[:16]} |\n"
                        resp += "\n> 💡 *Para detectar accesos nocturnos o fuera de horario laboral, compara los timestamps con la jornada esperada.*"
                        return resp, df
            except Exception:
                pass
            return "## Accesos Inusuales\n\nNo se pudieron obtener los registros de acceso.", None

        # ── operaciones_masivas ───────────────────────────────────────────────
        if accion == 'operaciones_masivas':
            try:
                if self.odoo and self.odoo.conectado:
                    from datetime import date as _dt_om, timedelta
                    hace_30 = (_dt_om.today() - timedelta(days=30)).strftime('%Y-%m-%d')
                    df = self.odoo.buscar(
                        'mail.tracking.value',
                        filtro=[('create_date', '>=', hace_30)],
                        campos=['create_uid', 'create_date', 'field', 'model_name'],
                        limite=200
                    )
                    if df is not None and not df.empty:
                        df['usuario'] = df.get('create_uid', pd.Series()).apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        agg = df.groupby('usuario').size().reset_index(name='operaciones').sort_values('operaciones', ascending=False)
                        resp = (
                            f"## Operaciones Masivas Recientes (30 días)\n\n"
                            f"**{len(df):,} cambios** rastreados:\n\n"
                            f"| Usuario | Operaciones |\n|---|---:|\n"
                        )
                        for _, r in agg.head(10).iterrows():
                            emoji_om = "🔴" if int(r['operaciones']) > 100 else "🟡" if int(r['operaciones']) > 50 else "🟢"
                            resp += f"| {r['usuario'][:35]} | {emoji_om} {int(r['operaciones']):,} |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Operaciones Masivas\n\nNo se encontraron registros de cambios en el período.", None

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_odoo(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')

        if accion == 'explorar_modelo' and self.conector:
            modelo = (getattr(consulta, 'parametros', {}) or {}).get('modelo', '')
            if modelo:
                try:
                    campos = self.conector.obtener_campos(modelo)
                    if campos:
                        items = list(campos.items())[:30]
                        resp = f"## Estructura del Modelo: {modelo}\n\n"
                        resp += f"**Campos totales:** {len(campos)}\n\n"
                        resp += "| Campo | Tipo | Descripción |\n|---|---|---|\n"
                        for nombre, info in items:
                            tipo = info.get('type', '')
                            desc = info.get('string', '')[:40]
                            resp += f"| {nombre} | {tipo} | {desc} |\n"
                        return resp, None
                except Exception:
                    pass

        if accion == 'campos_modelo' and self.conector:
            modelo = (getattr(consulta, 'parametros', {}) or {}).get('modelo', '')
            if modelo:
                try:
                    campos = self.conector.obtener_campos(modelo)
                    if campos:
                        df = pd.DataFrame([
                            {'campo': k, 'tipo': v.get('type', ''), 'descripcion': v.get('string', '')}
                            for k, v in campos.items()
                        ])
                        resp = f"## Campos del Modelo: {modelo}\n\n**Total:** {len(campos)} campos\n"
                        return resp, df
                except Exception:
                    pass

        if accion == 'version_odoo':
            try:
                resp = self._info_conexion()
                return resp, None
            except Exception:
                pass

        # ── info_sistema ─────────────────────────────────────────────────────
        if accion == 'info_sistema':
            resp = "## Información del Sistema Odoo\n\n"
            try:
                if self.conector and self.conector.conectado:
                    info = self.conector.obtener_version() if hasattr(self.conector, 'obtener_version') else {}
                    if info:
                        resp += f"| Parámetro | Valor |\n|---|---|\n"
                        for k, v in info.items():
                            resp += f"| {k} | {v} |\n"
                    else:
                        resp += "Conectado a Odoo ✅\n\n"
                        resp += self._info_conexion() if hasattr(self, '_info_conexion') else ""
                else:
                    resp += "⚠️ Odoo no conectado. Verifica la configuración de conexión.\n"
            except Exception as e:
                resp += f"Odoo conectado (detalles no disponibles): {e}\n"
            return resp, None

        # ── explicar_modelo ──────────────────────────────────────────────────
        if accion == 'explicar_modelo':
            params = getattr(consulta, 'parametros', {}) or {}
            modelo = params.get('modelo', params.get('model', ''))
            resp = f"## Descripción del Modelo Odoo: {modelo or '(no especificado)'}\n\n"
            if modelo and self.conector and self.conector.conectado:
                try:
                    campos = self.conector.obtener_campos(modelo)
                    if campos:
                        resp += f"**Modelo:** `{modelo}`\n**Total campos:** {len(campos)}\n\n"
                        resp += "| Campo | Tipo | Etiqueta |\n|---|---|---|\n"
                        for k, v in list(campos.items())[:25]:
                            resp += f"| `{k}` | {v.get('type','')} | {v.get('string','')} |\n"
                        if len(campos) > 25:
                            resp += f"\n*...y {len(campos)-25} campos más*\n"
                        return resp, None
                except Exception:
                    pass
            resp += (
                "Para explorar un modelo de Odoo escribe:\n\n"
                "`explica el modelo sale.order`\n\n"
                "**Modelos principales:**\n"
                "- `sale.order` — Pedidos de venta\n"
                "- `account.move` — Facturas\n"
                "- `stock.quant` — Inventario\n"
                "- `res.partner` — Clientes/Proveedores\n"
                "- `crm.lead` — Oportunidades CRM\n"
                "- `hr.employee` — Empleados\n"
            )
            return resp, None

        # ── consultar_usuarios ────────────────────────────────────────────────
        if accion == 'consultar_usuarios':
            try:
                if self.conector and self.conector.conectado:
                    df = self.conector.buscar(
                        'res.users',
                        filtro=[('active', '=', True), ('share', '=', False)],
                        campos=['name', 'login', 'groups_id', 'write_date'],
                        limite=100
                    )
                    if df is not None and not df.empty:
                        resp = (
                            f"## Usuarios del Sistema\n\n"
                            f"**Total usuarios internos activos:** {len(df)}\n\n"
                            f"| Usuario | Login | Último acceso |\n|---|---|---|\n"
                        )
                        for _, r in df.head(20).iterrows():
                            nombre = str(r.get('name', ''))[:30]
                            login = str(r.get('login', ''))
                            fecha = str(r.get('write_date', ''))[:10]
                            resp += f"| {nombre} | {login} | {fecha} |\n"
                        return resp, df
            except Exception:
                pass
            datos = self.analizador.analisis_usuarios()
            resp = "## Usuarios del Sistema\n\n"
            if 'resumen' in datos:
                r = datos['resumen']
                resp += f"- **Usuarios:** {r.get('total', 0)}\n- **Activos (7d):** {r.get('activos_7d', 0)}\n"
            return resp, None

        # ── actividad_usuarios ────────────────────────────────────────────────
        if accion == 'actividad_usuarios':
            datos = self.analizador.analisis_usuarios()
            resp = "## Actividad de Usuarios\n\n"
            if 'resumen' in datos:
                r = datos['resumen']
                resp += (
                    f"| Métrica | Valor |\n|---|---:|\n"
                    f"| 👥 Usuarios totales | **{r.get('total', 0)}** |\n"
                    f"| ✅ Activos (7 días) | **{r.get('activos_7d', 0)}** |\n"
                    f"| ⏳ Inactivos (30 días) | **{r.get('inactivos_30d', 0)}** |\n\n"
                )
            df = pd.DataFrame(datos.get('usuarios', []))
            if not df.empty:
                resp += "| Usuario | Último acceso |\n|---|---|\n"
                for _, r in df.head(15).iterrows():
                    nombre = str(r.get('name', ''))[:35]
                    fecha = str(r.get('date', r.get('last_login', '')))[:16]
                    resp += f"| {nombre} | {fecha} |\n"
            return resp, df if not df.empty else None

        # ── consultar_proyectos ───────────────────────────────────────────────
        if accion == 'consultar_proyectos':
            try:
                if self.conector and self.conector.conectado:
                    df = self.conector.buscar(
                        'project.project',
                        filtro=[('active', '=', True)],
                        campos=['name', 'user_id', 'date_start', 'date', 'task_count'],
                        limite=100
                    )
                    if df is not None and not df.empty:
                        resp = (
                            f"## Proyectos en Odoo\n\n"
                            f"**Proyectos activos:** {len(df)}\n\n"
                            f"| Proyecto | Responsable | Inicio | Fin | Tareas |\n|---|---|---|---|---:|\n"
                        )
                        for _, r in df.head(20).iterrows():
                            nombre = str(r.get('name', ''))[:35]
                            resp_user = r.get('user_id', '')
                            user = resp_user[1] if isinstance(resp_user, (list, tuple)) else str(resp_user)
                            inicio = str(r.get('date_start', ''))[:10]
                            fin = str(r.get('date', ''))[:10]
                            tareas = r.get('task_count', 0)
                            resp += f"| {nombre} | {user[:20]} | {inicio} | {fin} | {tareas} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Proyectos\n\nMódulo de Proyectos no disponible o sin proyectos activos.", None

        # ── tareas ────────────────────────────────────────────────────────────
        if accion == 'tareas':
            try:
                if self.conector and self.conector.conectado:
                    params = getattr(consulta, 'parametros', {}) or {}
                    filtro = [('active', '=', True)]
                    if params.get('proyecto'):
                        filtro.append(('project_id.name', 'ilike', params['proyecto']))
                    df = self.conector.buscar(
                        'project.task',
                        filtro=filtro,
                        campos=['name', 'project_id', 'user_ids', 'stage_id', 'date_deadline', 'priority'],
                        limite=100
                    )
                    if df is not None and not df.empty:
                        resp = (
                            f"## Tareas en Odoo\n\n"
                            f"**Total tareas activas:** {len(df)}\n\n"
                            f"| Tarea | Proyecto | Etapa | Prioridad |\n|---|---|---|---|\n"
                        )
                        for _, r in df.head(20).iterrows():
                            nombre = str(r.get('name', ''))[:40]
                            proj = r.get('project_id', '')
                            proj_n = proj[1] if isinstance(proj, (list, tuple)) else str(proj)
                            etapa = r.get('stage_id', '')
                            etapa_n = etapa[1] if isinstance(etapa, (list, tuple)) else str(etapa)
                            prio = '⭐' if str(r.get('priority', '0')) == '1' else '—'
                            resp += f"| {nombre} | {proj_n[:25]} | {etapa_n} | {prio} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Tareas\n\nMódulo de Proyectos no disponible o sin tareas activas.", None

        # ── consulta_sql_segura / consulta_dinamica ───────────────────────────
        if accion in ('consulta_sql_segura', 'consulta_dinamica'):
            params = getattr(consulta, 'parametros', {}) or {}
            modelo = params.get('modelo', params.get('model', ''))
            resp = (
                "## Consulta Dinámica a Odoo\n\n"
                "Puedo consultar cualquier modelo de Odoo directamente. "
                "Especifica el modelo y los campos que necesitas.\n\n"
                "**Ejemplos:**\n"
                "- `consulta sale.order de los últimos 30 días`\n"
                "- `dame los campos de res.partner con customer_rank > 0`\n"
                "- `busca en stock.quant productos con qty < 5`\n\n"
            )
            if modelo:
                try:
                    if self.conector and self.conector.conectado:
                        campos = self.conector.obtener_campos(modelo)
                        if campos:
                            resp += f"**Modelo `{modelo}` disponible** — {len(campos)} campos definidos.\n"
                except Exception:
                    pass
            resp += "> ⚠️ *Consultas SQL directas no están disponibles por razones de seguridad. Usa consultas semánticas naturales.*"
            return resp, None

        # ── relaciones_modelo ─────────────────────────────────────────────────
        if accion == 'relaciones_modelo':
            params_rm = getattr(consulta, 'parametros', {}) or {}
            modelo_rm = params_rm.get('modelo', params_rm.get('model', ''))
            try:
                if self.odoo and self.odoo.conectado and modelo_rm:
                    df = self.odoo.buscar(
                        'ir.model.fields',
                        filtro=[('model_id.model', '=', modelo_rm), ('ttype', 'in', ['many2one', 'one2many', 'many2many'])],
                        campos=['name', 'field_description', 'ttype', 'relation'],
                        limite=50
                    )
                    if df is not None and not df.empty:
                        resp = (
                            f"## Relaciones del Modelo `{modelo_rm}`\n\n"
                            f"| Campo | Descripción | Tipo | Modelo relacionado |\n|---|---|---|---|\n"
                        )
                        for _, r in df.iterrows():
                            resp += f"| `{r.get('name', '')}` | {r.get('field_description', '')} | {r.get('ttype', '')} | `{r.get('relation', '')}` |\n"
                        return resp, df
                    return f"## Relaciones de `{modelo_rm}`\n\nNo se encontraron relaciones o el modelo no existe.", None
            except Exception:
                pass
            return "## Relaciones del Modelo\n\nEspecifica un modelo. Ej: *'relaciones del modelo sale.order'*", None

        # ── flujo_trabajo_modelo ──────────────────────────────────────────────
        if accion == 'flujo_trabajo_modelo':
            params_fw = getattr(consulta, 'parametros', {}) or {}
            modelo_fw = params_fw.get('modelo', params_fw.get('model', ''))
            flujos = {
                'sale.order': ['draft → sent → sale → done → cancel'],
                'purchase.order': ['draft → sent → to approve → purchase → done → cancel'],
                'account.move': ['draft → posted → cancel'],
                'stock.picking': ['draft → waiting → confirmed → assigned → done → cancel'],
                'crm.lead': ['new → qualified → proposition → won/lost'],
                'hr.leave': ['draft → confirm → validate1 → validate → refuse'],
                'project.task': ['in_progress → done → cancelled'],
            }
            if modelo_fw and modelo_fw in flujos:
                resp = (
                    f"## Flujo de Trabajo: `{modelo_fw}`\n\n"
                    f"**Estados y transiciones:**\n\n"
                    f"```\n{chr(10).join(flujos[modelo_fw])}\n```\n\n"
                )
            elif modelo_fw:
                try:
                    if self.odoo and self.odoo.conectado:
                        df_st = self.odoo.buscar(
                            'ir.model.fields',
                            filtro=[('model_id.model', '=', modelo_fw), ('name', '=', 'state')],
                            campos=['selection', 'field_description'], limite=1
                        )
                        resp = f"## Flujo de `{modelo_fw}`\n\nCampo `state` disponible. Consulta los estados directamente en Odoo para este modelo.\n"
                    else:
                        resp = f"## Flujo de `{modelo_fw}`\n\nConexión no disponible. Verifica en Odoo → Configuración → Técnico → Flujos de trabajo.\n"
                except Exception:
                    resp = f"## Flujo de `{modelo_fw}`\n\nNo disponible.\n"
            else:
                resp = (
                    "## Flujos de Trabajo Disponibles\n\n"
                    "Modelos documentados:\n\n"
                    + "\n".join(f"- `{m}`: {v[0]}" for m, v in flujos.items())
                    + "\n\n> *Especifica un modelo para ver su flujo: 'flujo de sale.order'*"
                )
            return resp, None

        # ── permisos_usuario ──────────────────────────────────────────────────
        if accion == 'permisos_usuario':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'res.users',
                        filtro=[('active', '=', True), ('share', '=', False)],
                        campos=['name', 'login', 'groups_id'],
                        limite=50
                    )
                    if df is not None and not df.empty:
                        resp = (
                            f"## Usuarios y Permisos del Sistema\n\n"
                            f"**{len(df):,} usuarios internos activos**\n\n"
                            f"| Usuario | Login |\n|---|---|\n"
                        )
                        for _, r in df.head(15).iterrows():
                            resp += f"| {r.get('name', '')} | {r.get('login', '')} |\n"
                        resp += "\n> 💡 *Para ver grupos específicos de un usuario, ve a Configuración → Usuarios en Odoo.*"
                        return resp, df
            except Exception:
                pass
            return "## Permisos de Usuario\n\nNo se pudieron obtener los usuarios del sistema.", None

        # ── log_acciones_usuario ──────────────────────────────────────────────
        if accion == 'log_acciones_usuario':
            try:
                if self.odoo and self.odoo.conectado:
                    from datetime import date as _dt_lau, timedelta
                    hace_14 = (_dt_lau.today() - timedelta(days=14)).strftime('%Y-%m-%d')
                    df = self.odoo.buscar(
                        'mail.tracking.value',
                        filtro=[('create_date', '>=', hace_14)],
                        campos=['create_uid', 'create_date', 'model_name', 'field'],
                        limite=200
                    )
                    if df is not None and not df.empty:
                        df['usuario'] = df.get('create_uid', pd.Series()).apply(lambda x: x[1] if isinstance(x, (list, tuple)) else str(x))
                        agg = df.groupby(['usuario', 'model_name']).size().reset_index(name='cambios').sort_values('cambios', ascending=False)
                        resp = (
                            f"## Log de Acciones (últimos 14 días)\n\n"
                            f"**{len(df):,} cambios registrados**\n\n"
                            f"| Usuario | Modelo | Cambios |\n|---|---|---:|\n"
                        )
                        for _, r in agg.head(15).iterrows():
                            resp += f"| {r['usuario'][:30]} | `{r['model_name']}` | {int(r['cambios']):,} |\n"
                        return resp, agg
            except Exception:
                pass
            return "## Log de Acciones\n\nNo se encontraron registros de cambios recientes.", None

        # ── modulos_instalados ────────────────────────────────────────────────
        if accion == 'modulos_instalados':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'ir.module.module',
                        filtro=[('state', '=', 'installed')],
                        campos=['name', 'shortdesc', 'author', 'installed_version'],
                        limite=200
                    )
                    if df is not None and not df.empty:
                        resp = (
                            f"## Módulos Instalados en Odoo\n\n"
                            f"**Total:** {len(df):,} módulos instalados\n\n"
                            f"| Módulo | Descripción | Versión |\n|---|---|---|\n"
                        )
                        for _, r in df.head(20).iterrows():
                            resp += f"| `{r.get('name', '')}` | {str(r.get('shortdesc', ''))[:40]} | {r.get('installed_version', '')} |\n"
                        if len(df) > 20:
                            resp += f"\n*... y {len(df) - 20} módulos más*"
                        return resp, df
            except Exception:
                pass
            return "## Módulos Instalados\n\nNo se pudieron obtener los módulos del sistema.", None

        # ── ir_cron_activos ───────────────────────────────────────────────────
        if accion == 'ir_cron_activos':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'ir.cron',
                        filtro=[('active', '=', True)],
                        campos=['name', 'nextcall', 'interval_number', 'interval_type', 'user_id'],
                        limite=50
                    )
                    if df is not None and not df.empty:
                        resp = (
                            f"## Tareas Programadas Activas (ir.cron)\n\n"
                            f"**{len(df):,} tareas activas**\n\n"
                            f"| Tarea | Próxima ejecución | Intervalo |\n|---|---|---|\n"
                        )
                        for _, r in df.iterrows():
                            intervalo = f"{r.get('interval_number', '')} {r.get('interval_type', '')}"
                            resp += f"| {str(r.get('name', ''))[:40]} | {str(r.get('nextcall', ''))[:16]} | {intervalo} |\n"
                        return resp, df
            except Exception:
                pass
            return "## Tareas Programadas\n\nNo se pudieron obtener las tareas programadas.", None

        # ── parametros_sistema ────────────────────────────────────────────────
        if accion == 'parametros_sistema':
            try:
                if self.odoo and self.odoo.conectado:
                    PARAM_SEGUROS = [
                        'web.base.url', 'web.company.name', 'mail.catchall.domain',
                        'base.setup.default_currency', 'auth_password_policy.minlength'
                    ]
                    df = self.odoo.buscar(
                        'ir.config_parameter',
                        filtro=[('key', 'in', PARAM_SEGUROS)],
                        campos=['key', 'value'],
                        limite=30
                    )
                    if df is not None and not df.empty:
                        resp = (
                            f"## Parámetros del Sistema\n\n"
                            f"| Parámetro | Valor |\n|---|---|\n"
                        )
                        for _, r in df.iterrows():
                            resp += f"| `{r.get('key', '')}` | {r.get('value', '')} |\n"
                        resp += "\n> 🔒 *Solo se muestran parámetros no sensibles.*"
                        return resp, df
            except Exception:
                pass
            return "## Parámetros del Sistema\n\nNo se pudieron obtener los parámetros.", None

        # ── ayuda / mostrar_capacidades ───────────────────────────────────────
        if accion in ('ayuda', 'mostrar_capacidades'):
            resp = (
                "## Capacidades de ANDROMEDA\n\n"
                "Soy un asistente inteligente para Odoo con los siguientes módulos:\n\n"
                "| Módulo | Acciones disponibles |\n|---|---|\n"
                "| 📊 **Ventas** | análisis, top productos, canal, margen, devoluciones, metas |\n"
                "| 📦 **Inventario** | stock, alertas, rotación, valoración, obsoletos |\n"
                "| 💰 **Finanzas** | facturación, flujo caja, conciliación, impuestos, ratios |\n"
                "| 🤝 **CRM** | pipeline, conversión, leads, actividades, lifetime value |\n"
                "| 🛒 **Compras** | órdenes, proveedores, lead time, comparativa precios |\n"
                "| 🖥️ **POS** | ventas POS, cajeros, descuentos, cuadre caja, sucursales |\n"
                "| 👥 **RRHH** | empleados, contratos, ausencias, rotación, jornada |\n"
                "| 🔮 **Predicciones** | demanda, ventas futuras, riesgo clientes |\n"
                "| 🔧 **Diagnóstico** | validación datos, duplicados, integridad, accesos |\n"
                "| ⚙️ **Sistema** | módulos, parámetros, cron, usuarios, flujos |\n\n"
                "> 💬 *Puedes hacer preguntas en lenguaje natural. Ejemplo: '¿Cuáles son mis 10 mejores clientes?' o 'Muestra el flujo de caja del mes.'*"
            )
            return resp, None

        # ── consultar_manual ──────────────────────────────────────────────────
        if accion == 'consultar_manual':
            try:
                from services.knowledge.procesador_manuales import (
                    obtener_procesador, traducir_consulta_i18n,
                )
                from models.conector_odoo import _ctx_idioma
                idioma_manual = _ctx_idioma.get()

                proc = obtener_procesador()
                if not proc.secciones:
                    _TITULO_NO_IDX = {
                        "en": "## Odoo Manual\n\nThe manual index has not been generated yet. Please process the `MANUAL.docx` file first.",
                        "ja": "## Odooマニュアル\n\nマニュアルインデックスがまだ生成されていません。先に`MANUAL.docx`ファイルを処理してください。",
                    }
                    return (
                        _TITULO_NO_IDX.get(
                            idioma_manual,
                            "## Manual de Odoo\n\nEl índice del manual aún no está generado. "
                            "Procesa el archivo `MANUAL.docx` primero."
                        ),
                        None
                    )
                # Normalizar consulta: JA/EN → palabras clave ES para el índice
                consulta_busqueda = traducir_consulta_i18n(mensaje, idioma_manual)
                resultados = proc.buscar(consulta_busqueda, max_resultados=2)
                resp = proc.formatear_respuesta(resultados, idioma=idioma_manual)
            except Exception:
                resp = "## Consultar Manual\n\nNo se pudo acceder al manual de Odoo."
            return resp, None

        # ── info_conexion ─────────────────────────────────────────────────────
        if accion == 'info_conexion':
            if hasattr(self._bot, '_info_conexion'):
                return self._bot._info_conexion(), None
            if self.odoo:
                conectado = getattr(self.odoo, 'conectado', False)
                url = getattr(self.odoo, 'url', 'N/A')
                resp = (
                    f"## Información de Conexión\n\n"
                    f"| Parámetro | Valor |\n|---|---|\n"
                    f"| 🌐 URL | `{url}` |\n"
                    f"| ✅ Estado | {'**Conectado**' if conectado else '**Desconectado**'} |\n"
                )
                return resp, None
            return "## Información de Conexión\n\nNo hay conector Odoo configurado.", None

        # ── generar_pdf / generar_pdf_profesional ─────────────────────────────
        if accion in ('generar_pdf', 'generar_pdf_profesional'):
            resp = (
                "## Generación de PDF\n\n"
                "Para exportar cualquier reporte como PDF:\n\n"
                "1. Ejecuta el análisis deseado (ej. *'ventas del mes'*)\n"
                "2. En la interfaz, usa el botón **📥 Exportar PDF**\n"
                "3. Se generará con el formato profesional de ANDROMEDA\n\n"
                "> 💡 *También puedes exportar a Excel con el botón **📊 Exportar Excel**.*"
            )
            return resp, None

        # ── generar_excel ─────────────────────────────────────────────────────
        if accion == 'generar_excel':
            resp = (
                "## Exportar a Excel\n\n"
                "Para exportar datos a Excel:\n\n"
                "1. Obtén el análisis deseado (ej. *'inventario actual'*)\n"
                "2. Usa el botón **📊 Exportar Excel** en la interfaz\n"
                "3. Se descargará un archivo `.xlsx` con los datos tabulados\n\n"
                "> 💡 *Los datos mostrados en tablas pueden exportarse directamente.*"
            )
            return resp, None

        return self._ejecutar_accion(consulta, mensaje)


    def _ejecutor_estadistica(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        temp = getattr(consulta, 'temporalidad', {}) or {}
        fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')

        if accion == 'score_salud_negocio':
            datos = self.predictor.score_salud_negocio()
            if 'error' not in datos:
                resp = self.fmt._formatear_salud_negocio(datos)
                return resp, None

        if accion == 'curva_abc_ventas':
            datos = self.analizador.top_productos_vendidos(fi, ff)
            if 'error' not in datos and datos.get('productos'):
                df = pd.DataFrame(datos['productos'])
                resp = "## Curva ABC de Ventas\n\n"
                if 'total' in df.columns:
                    total_ventas = df['total'].sum()
                    df_sorted = df.sort_values('total', ascending=False)
                    df_sorted['acum_pct'] = df_sorted['total'].cumsum() / total_ventas * 100
                    a = len(df_sorted[df_sorted['acum_pct'] <= 80])
                    b = len(df_sorted[(df_sorted['acum_pct'] > 80) & (df_sorted['acum_pct'] <= 95)])
                    c = len(df_sorted[df_sorted['acum_pct'] > 95])
                    resp += f"- **Clase A (80% ingresos):** {a} productos\n"
                    resp += f"- **Clase B (15% ingresos):** {b} productos\n"
                    resp += f"- **Clase C (5% ingresos):** {c} productos\n"
                return resp, df

        if accion == 'comparativa_tiendas' and self.analizador_inteligente:
            from services.analysis.analisis_inteligente import ContextoConsulta, TipoAgrupacion, FormateadorInteligente
            ctx = ContextoConsulta()
            ctx.tipo_reporte = 'ventas'
            ctx.agrupacion = TipoAgrupacion.POR_TIENDA
            ctx.fecha_inicio = fi
            ctx.fecha_fin = ff
            resultado = self.analizador_inteligente._ventas_por_tienda(ctx)
            resp = FormateadorInteligente.formatear(resultado)
            df = pd.DataFrame(resultado.get('tiendas', []))
            return resp, df if not df.empty else None

        # ── analisis_estadistico ─────────────────────────────────────────────
        if accion == 'analisis_estadistico':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            resumen = datos.get('resumen', {})
            ventas = resumen.get('total_ventas', 0)
            ordenes = resumen.get('ordenes', 1) or 1
            media = ventas / ordenes
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            resp = (
                f"## Análisis Estadístico\n\n"
                f"**Período:** {fi} a {ff}\n\n"
                f"| Métrica | Valor |\n|---|---:|\n"
                f"| 📊 Total ventas | **${ventas:,.2f}** |\n"
                f"| 📋 Órdenes | **{ordenes:,}** |\n"
                f"| 📐 Media por orden | **${media:,.2f}** |\n"
            )
            if df is not None and not df.empty and 'total' in df.columns:
                col = pd.to_numeric(df['total'], errors='coerce').dropna()
                if not col.empty:
                    mediana = float(col.median())
                    desv = float(col.std(ddof=0))
                    p25, p75 = float(col.quantile(0.25)), float(col.quantile(0.75))
                    q1, q3 = p25, p75
                    iqr = q3 - q1
                    outliers = int(((col < q1 - 1.5 * iqr) | (col > q3 + 1.5 * iqr)).sum())
                    resp += f"| 📊 Mediana | **${mediana:,.2f}** |\n"
                    resp += f"| 📉 Desv. estándar | **${desv:,.2f}** |\n"
                    resp += f"| P25/P75 | **${p25:,.2f} / ${p75:,.2f}** |\n"
                    resp += f"| ⚡ Outliers (IQR) | **{outliers}** |\n"
            resp += "\n> 💡 *¿Quieres segmentación RFM, análisis de correlación o distribución detallada?*"
            return resp, df

        # ── correlacion_variables ────────────────────────────────────────────
        if accion == 'correlacion_variables':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            if df is not None and not df.empty:
                cols_num = df.select_dtypes(include='number').columns.tolist()
                resp = f"## Correlación de Variables\n\n**Período:** {fi} a {ff}\n\n"
                if len(cols_num) >= 2:
                    resp += "| Par de variables | Correlación Pearson | Interpretación |\n|---|---:|---|\n"
                    for i, c1 in enumerate(cols_num[:4]):
                        for c2 in cols_num[i+1:4]:
                            corr = df[[c1, c2]].dropna()
                            if len(corr) > 2:
                                r = float(corr[c1].corr(corr[c2]))
                                interp = "Fuerte +" if r > 0.7 else "Moderada +" if r > 0.4 else "Débil +" if r > 0.1 else "Fuerte -" if r < -0.7 else "Moderada -" if r < -0.4 else "Débil -"
                                resp += f"| {c1} ↔ {c2} | {r:.3f} | {interp} |\n"
                    resp += "\n> ⚠️ *Correlación ≠ causalidad. Un r cercano a ±1 indica relación lineal fuerte.*"
                else:
                    resp += "Se requieren al menos 2 variables numéricas para correlación.\n"
                return resp, df
            return "No hay suficientes datos para calcular correlaciones.", None

        # ── segmentacion_datos / analisis_rfm ───────────────────────────────
        if accion in ('segmentacion_datos', 'analisis_rfm'):
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            resp = f"## {'Segmentación de Clientes (RFM)' if 'rfm' in accion else 'Segmentación de Datos'}\n\n**Período:** {fi} a {ff}\n\n"
            if df is not None and not df.empty and 'total' in df.columns:
                col = pd.to_numeric(df['total'], errors='coerce').fillna(0)
                p33, p66 = float(col.quantile(0.33)), float(col.quantile(0.66))
                alto = int((col >= p66).sum())
                medio = int(((col >= p33) & (col < p66)).sum())
                bajo = int((col < p33).sum())
                resp += (
                    f"| Segmento | Clientes | Umbral |\n|---|---:|---|\n"
                    f"| 🥇 Alto valor (≥P66) | **{alto}** | ≥ ${p66:,.2f} |\n"
                    f"| 🥈 Valor medio (P33-P66) | **{medio}** | ${p33:,.2f} – ${p66:,.2f} |\n"
                    f"| 🥉 Bajo valor (<P33) | **{bajo}** | < ${p33:,.2f} |\n\n"
                    f"**Total clientes analizados:** {len(df):,}\n\n"
                    f"> 💡 *RFM completo requiere fechas de última compra y frecuencia. Activa el módulo de CRM para mayor profundidad.*"
                )
            else:
                resp += "No hay datos de clientes para segmentar en este período."
            return resp, df

        # ── distribucion_datos ───────────────────────────────────────────────
        if accion == 'distribucion_datos':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            if df is not None and not df.empty and 'total' in df.columns:
                col = pd.to_numeric(df['total'], errors='coerce').dropna()
                percentiles = [10, 25, 50, 75, 90]
                resp = (
                    f"## Distribución de Ventas\n\n"
                    f"**Período:** {fi} a {ff} | **n = {len(col):,}**\n\n"
                    f"| Percentil | Valor |\n|---|---:|\n"
                )
                for p in percentiles:
                    resp += f"| P{p} | **${float(col.quantile(p/100)):,.2f}** |\n"
                resp += f"| Min | ${float(col.min()):,.2f} |\n| Max | ${float(col.max()):,.2f} |\n"
                resp += f"\n**Media:** ${float(col.mean()):,.2f} | **Mediana:** ${float(col.median()):,.2f}\n"
                return resp, df
            return "No hay datos para analizar la distribución.", None

        # ── outliers_datos ───────────────────────────────────────────────────
        if accion == 'outliers_datos':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            if df is not None and not df.empty and 'total' in df.columns:
                col = pd.to_numeric(df['total'], errors='coerce').dropna()
                q1, q3 = float(col.quantile(0.25)), float(col.quantile(0.75))
                iqr = q3 - q1
                lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                mask_out = (col < lim_inf) | (col > lim_sup)
                n_out = int(mask_out.sum())
                resp = (
                    f"## Detección de Outliers (Método IQR)\n\n"
                    f"**Período:** {fi} a {ff}\n\n"
                    f"| Límite | Valor |\n|---|---:|\n"
                    f"| Q1 (P25) | ${q1:,.2f} |\n"
                    f"| Q3 (P75) | ${q3:,.2f} |\n"
                    f"| IQR | ${iqr:,.2f} |\n"
                    f"| Límite inferior | ${lim_inf:,.2f} |\n"
                    f"| Límite superior | ${lim_sup:,.2f} |\n\n"
                    f"**Outliers detectados: {n_out}** ({n_out/len(col)*100:.1f}% del total)\n\n"
                )
                if n_out > 0:
                    resp += "⚠️ Los outliers pueden ser ventas extraordinarias, errores de captura o fraudes. Revisar manualmente.\n"
                else:
                    resp += "✅ No se detectaron outliers significativos.\n"
                return resp, df
            return "No hay datos para detectar outliers.", None

        # ── kpis_empresariales ───────────────────────────────────────────────
        if accion == 'kpis_empresariales':
            datos_v = self.analizador.analisis_ventas_completo(fi, ff)
            datos_i = self.analizador.analisis_inventario()
            resumen = datos_v.get('resumen', {})
            ventas = resumen.get('total_ventas', 0)
            ordenes = resumen.get('ordenes', 1) or 1
            ticket = ventas / ordenes
            inv_val = datos_i.get('valoracion', {}).get('total', 0) or 0
            resp = (
                f"## KPIs Empresariales\n\n"
                f"**Período:** {fi} a {ff}\n\n"
                f"| KPI | Valor |\n|---|---:|\n"
                f"| 💰 Ventas totales | **${ventas:,.2f}** |\n"
                f"| 📋 Órdenes | **{ordenes:,}** |\n"
                f"| 🎟️ Ticket promedio | **${ticket:,.2f}** |\n"
                f"| 📦 Valor inventario | **${inv_val:,.2f}** |\n\n"
                f"> 💡 *¿Quieres KPIs de CRM, compras, RRHH o comparativa por tienda?*"
            )
            return resp, None

        # ── analisis_pareto ──────────────────────────────────────────────────
        if accion == 'analisis_pareto':
            datos = self.analizador.top_productos_vendidos(fi, ff)
            if 'error' not in datos and datos.get('productos'):
                df = pd.DataFrame(datos['productos'])
                if 'total' in df.columns:
                    total = df['total'].sum()
                    df_sorted = df.sort_values('total', ascending=False)
                    df_sorted['acum'] = df_sorted['total'].cumsum()
                    df_sorted['acum_pct'] = df_sorted['acum'] / total * 100
                    df_80 = df_sorted[df_sorted['acum_pct'] <= 80]
                    n_80 = len(df_80)
                    n_total = len(df_sorted)
                    resp = (
                        f"## Análisis de Pareto (80/20)\n\n"
                        f"**Período:** {fi} a {ff}\n\n"
                        f"📊 **{n_80} de {n_total} productos** ({n_80/n_total*100:.1f}%) generan el **80% de los ingresos**.\n\n"
                        f"| # | Producto | Ventas | % Acumulado |\n|---|---|---:|---:|\n"
                    )
                    for i, (_, r) in enumerate(df_sorted.head(10).iterrows(), 1):
                        nombre = str(r.get('name', r.get('product', '')))[:40]
                        t = float(r.get('total', 0))
                        pct = float(r['acum_pct'])
                        resp += f"| {i} | {nombre} | ${t:,.2f} | {pct:.1f}% |\n"
                    return resp, df_sorted
            return "No hay datos de productos para el análisis Pareto.", None

        # ── analisis_cohort / analisis_cohorte_retencion ─────────────────────
        if accion in ('analisis_cohort', 'analisis_cohorte_retencion'):
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            resp = (
                f"## Análisis de Cohortes\n\n"
                f"**Período:** {fi} a {ff}\n\n"
            )
            if df is not None and not df.empty:
                n_clientes = len(df)
                n_activos = len(df[pd.to_numeric(df.get('total', 0), errors='coerce') > 0]) if 'total' in df.columns else n_clientes
                resp += (
                    f"- **Clientes en cohorte:** {n_clientes:,}\n"
                    f"- **Clientes activos:** {n_activos:,} ({n_activos/n_clientes*100:.1f}%)\n\n"
                    f"> 💡 *Para cohortes de retención por mes de adquisición, se necesita historial de al menos 6 meses.*\n"
                    f"> *¿Quieres ver clientes por primera compra vs. recurrentes?*"
                )
            else:
                resp += "No hay datos de clientes disponibles para este período."
            return resp, df

        # ── benchmarking ─────────────────────────────────────────────────────
        if accion == 'benchmarking':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_vend = datos.get('por_vendedor', [])
            df = pd.DataFrame(por_vend) if por_vend else None
            resp = f"## Benchmarking Interno\n\n**Período:** {fi} a {ff}\n\n"
            if df is not None and not df.empty and 'total' in df.columns:
                col = pd.to_numeric(df['total'], errors='coerce').fillna(0)
                promedio = float(col.mean())
                resp += (
                    f"| Vendedor | Ventas | vs. Promedio |\n|---|---:|---:|\n"
                )
                for _, r in df.sort_values('total', ascending=False).head(10).iterrows():
                    nombre = str(r.get('name', r.get('user', '')))[:35]
                    t = float(r.get('total', 0))
                    vs = ((t - promedio) / promedio * 100) if promedio > 0 else 0
                    emoji = "🟢" if vs >= 0 else "🔴"
                    resp += f"| {nombre} | ${t:,.2f} | {emoji} {vs:+.1f}% |\n"
                resp += f"\n**Promedio del equipo:** ${promedio:,.2f}"
            else:
                resp += "No hay datos de vendedores para benchmarking."
            return resp, df

        # ── analisis_tendencia_avanzado ──────────────────────────────────────
        if accion == 'analisis_tendencia_avanzado':
            datos = self.predictor.analizar_estacionalidad()
            if 'error' not in datos:
                df_sem = pd.DataFrame(datos.get('por_dia_semana', []))
                resp = f"## Tendencia Avanzada y Estacionalidad\n\n"
                if datos.get('tendencia'):
                    resp += f"**Tendencia:** {datos['tendencia']}\n\n"
                if not df_sem.empty:
                    resp += self.fmt._formatear_estacionalidad(datos)
                return resp, df_sem if not df_sem.empty else None
            return self.predictor.analizar_estacionalidad().get('error', 'Sin datos'), None

        # ── test_hipotesis ───────────────────────────────────────────────────
        if accion == 'test_hipotesis':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_vend = datos.get('por_vendedor', [])
            df = pd.DataFrame(por_vend) if por_vend else None
            resp = f"## Test de Hipótesis Estadístico\n\n**Período:** {fi} a {ff}\n\n"
            if df is not None and not df.empty and 'total' in df.columns and len(df) >= 2:
                col = pd.to_numeric(df['total'], errors='coerce').dropna()
                media = float(col.mean())
                desv = float(col.std(ddof=1)) if len(col) > 1 else 0
                n = len(col)
                # t-test de una muestra
                import math
                se = desv / math.sqrt(n) if n > 0 and desv > 0 else 1
                t_stat = media / se if se > 0 else 0
                resp += (
                    f"**H₀:** Las ventas por vendedor son iguales (media = ${media:,.2f})\n\n"
                    f"| Estadístico | Valor |\n|---|---:|\n"
                    f"| Media | ${media:,.2f} |\n"
                    f"| Desv. estándar | ${desv:,.2f} |\n"
                    f"| n | {n} |\n"
                    f"| t-estadístico | {t_stat:.3f} |\n\n"
                )
                if n < 30:
                    resp += "⚠️ **Muestra pequeña (n<30)**: resultados indicativos, no concluyentes.\n"
                resp += "> 💡 *Para pruebas A/B o comparativas entre grupos, especifica los grupos a comparar.*"
            else:
                resp += "Se requieren al menos 2 grupos de datos para realizar un test de hipótesis."
            return resp, df

        # ── regresion_multiple ───────────────────────────────────────────────
        if accion == 'regresion_multiple':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            resp = f"## Regresión Múltiple\n\n**Período:** {fi} a {ff}\n\n"
            if df is not None and not df.empty:
                cols_num = df.select_dtypes(include='number').columns.tolist()
                resp += (
                    f"**Variables disponibles:** {', '.join(cols_num[:5])}\n\n"
                    f"Para ejecutar regresión múltiple, especifica:\n"
                    f"- **Variable dependiente** (Y): la que quieres predecir\n"
                    f"- **Variables independientes** (X): las que explican Y\n\n"
                    f"**Ejemplo:** `regresión de ventas en función de descuento y cantidad`\n\n"
                    f"> 💡 *Con datos históricos actuales puedo calcular coeficientes y R² para explicar variabilidad.*"
                )
            else:
                resp += "No hay datos disponibles para regresión."
            return resp, df

        # ── analisis_varianza ────────────────────────────────────────────────
        if accion == 'analisis_varianza':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_vend = datos.get('por_vendedor', [])
            df = pd.DataFrame(por_vend) if por_vend else None
            resp = f"## ANOVA — Análisis de Varianza\n\n**Período:** {fi} a {ff}\n\n"
            if df is not None and not df.empty and 'total' in df.columns and len(df) >= 3:
                grupos = df.groupby(df.columns[0])['total'].apply(list) if len(df.columns) > 1 else {}
                col = pd.to_numeric(df['total'], errors='coerce').dropna()
                media_total = float(col.mean())
                varianza = float(col.var(ddof=1)) if len(col) > 1 else 0
                resp += (
                    f"**Grupos analizados:** {len(df)} vendedores\n\n"
                    f"| Métrica | Valor |\n|---|---:|\n"
                    f"| Media total | ${media_total:,.2f} |\n"
                    f"| Varianza | ${varianza:,.2f} |\n"
                    f"| CV (%) | {varianza**0.5/media_total*100:.1f}% |\n\n"
                    f"> 💡 *Para ANOVA formal (F-test) especifica los grupos a comparar (ej: tiendas, regiones).*"
                )
            else:
                resp += "Se requieren al menos 3 grupos para ANOVA."
            return resp, df

        # ── mapa_calor ───────────────────────────────────────────────────────
        if accion == 'mapa_calor':
            datos = self.predictor.analizar_estacionalidad()
            if 'error' not in datos and datos.get('por_dia_semana'):
                df = pd.DataFrame(datos['por_dia_semana'])
                resp = (
                    f"## Mapa de Calor — Ventas por Día\n\n"
                    f"**Intensidad de ventas por día de la semana:**\n\n"
                    f"| Día | Ventas | Intensidad |\n|---|---:|---|\n"
                )
                if not df.empty:
                    col_val = df.select_dtypes(include='number').columns
                    if len(col_val) > 0:
                        col = df[col_val[0]]
                        max_v = float(col.max()) if len(col) > 0 else 1
                        for _, r in df.iterrows():
                            dia = str(r.iloc[0])
                            val = float(r[col_val[0]])
                            barras = int(val / max_v * 10) if max_v > 0 else 0
                            resp += f"| {dia} | ${val:,.2f} | {'█' * barras}{'░' * (10-barras)} |\n"
                return resp, df
            return "No hay datos de estacionalidad para generar el mapa de calor.", None

        # ── analisis_canasta ─────────────────────────────────────────────────
        if accion == 'analisis_canasta':
            datos = self.analizador.top_productos_vendidos(fi, ff)
            if 'error' not in datos and datos.get('productos'):
                df = pd.DataFrame(datos['productos'])
                resp = (
                    f"## Análisis de Canasta (Market Basket)\n\n"
                    f"**Período:** {fi} a {ff}\n\n"
                    f"**Top 10 productos más comprados:**\n\n"
                    f"| Producto | Ventas | % del total |\n|---|---:|---:|\n"
                )
                total = df['total'].sum() if 'total' in df.columns else 1
                for _, r in df.head(10).iterrows():
                    nombre = str(r.get('name', r.get('product', '')))[:40]
                    t = float(r.get('total', 0))
                    pct = t / total * 100 if total > 0 else 0
                    resp += f"| {nombre} | ${t:,.2f} | {pct:.1f}% |\n"
                resp += "\n> 💡 *Para asociaciones producto-producto (Apriori/FP-Growth) se necesitan datos de líneas de pedido con órdenes completas.*"
                return resp, df
            return "No hay datos de productos para el análisis de canasta.", None

        # ── indice_gini_clientes ─────────────────────────────────────────────
        if accion == 'indice_gini_clientes':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            resp = f"## Índice de Gini — Concentración de Clientes\n\n**Período:** {fi} a {ff}\n\n"
            if df is not None and not df.empty and 'total' in df.columns:
                col = pd.to_numeric(df['total'], errors='coerce').dropna().sort_values()
                n = len(col)
                gini = float((2 * sum((i + 1) * v for i, v in enumerate(col)) / (n * col.sum())) - (n + 1) / n) if col.sum() > 0 else 0
                top5 = col.tail(5).sum() / col.sum() * 100 if col.sum() > 0 else 0
                interp = "Alta concentración 🔴" if gini > 0.6 else "Concentración moderada 🟡" if gini > 0.4 else "Distribución equitativa 🟢"
                resp += (
                    f"**Gini = {gini:.3f}** → {interp}\n\n"
                    f"- Top 5 clientes concentran: **{top5:.1f}%** del ingreso\n"
                    f"- Clientes analizados: **{n:,}**\n\n"
                    f"| Gini | Significado |\n|---|---|\n"
                    f"| 0.0 | Distribución perfectamente equitativa |\n"
                    f"| 0.5 | Concentración moderada |\n"
                    f"| 1.0 | Un cliente genera todo el ingreso |\n"
                )
            else:
                resp += "No hay datos de clientes para calcular el índice Gini."
            return resp, df

        # ── estacionalidad_avanzada ──────────────────────────────────────────
        if accion == 'estacionalidad_avanzada':
            datos = self.predictor.analizar_estacionalidad()
            if 'error' not in datos:
                resp = self.fmt._formatear_estacionalidad(datos)
                df = pd.DataFrame(datos.get('por_dia_semana', []))
                return resp, df if not df.empty else None
            return datos.get('error', 'Sin datos de estacionalidad'), None

        # ── volatilidad_ventas ───────────────────────────────────────────────
        if accion == 'volatilidad_ventas':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_cli = datos.get('por_cliente', [])
            df = pd.DataFrame(por_cli) if por_cli else None
            if df is not None and not df.empty and 'total' in df.columns:
                col = pd.to_numeric(df['total'], errors='coerce').dropna()
                media = float(col.mean())
                desv = float(col.std(ddof=0))
                cv = (desv / media * 100) if media > 0 else 0
                nivel = "Alta 🔴" if cv > 50 else "Moderada 🟡" if cv > 25 else "Baja 🟢"
                resp = (
                    f"## Volatilidad de Ventas\n\n"
                    f"**Período:** {fi} a {ff}\n\n"
                    f"| Métrica | Valor |\n|---|---:|\n"
                    f"| 📊 Media | ${media:,.2f} |\n"
                    f"| 📉 Desv. estándar | ${desv:,.2f} |\n"
                    f"| 🎯 Coeficiente de Variación | **{cv:.1f}%** |\n"
                    f"| 📈 Nivel de volatilidad | **{nivel}** |\n\n"
                )
                if cv > 50:
                    resp += "⚠️ **Volatilidad alta**: ventas muy irregulares. Considerar estrategias de estabilización (suscripciones, contratos marco).\n"
                elif cv > 25:
                    resp += "🟡 **Volatilidad moderada**: hay variabilidad pero controlable. Revisar patrones por temporada.\n"
                else:
                    resp += "🟢 **Ventas estables**: baja variabilidad indica flujo comercial predecible.\n"
                return resp, df
            return "No hay datos para calcular volatilidad.", None

        # ── ranking_multidimensional ──────────────────────────────────────────
        if accion == 'ranking_multidimensional':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            por_vend = datos.get('por_vendedor', [])
            df = pd.DataFrame(por_vend) if por_vend else None
            resp = f"## Ranking Multidimensional\n\n**Período:** {fi} a {ff}\n\n"
            if df is not None and not df.empty:
                cols_num = df.select_dtypes(include='number').columns.tolist()
                resp += f"**Métricas evaluadas:** {', '.join(cols_num[:4])}\n\n"
                resp += "| # | Entidad | Score Compuesto |\n|---|---|---:|\n"
                for i, (_, r) in enumerate(df.head(10).iterrows(), 1):
                    nombre = str(r.iloc[0])[:35]
                    score = sum(float(r.get(c, 0)) for c in cols_num[:3]) / max(len(cols_num[:3]), 1)
                    resp += f"| {i} | {nombre} | {score:,.2f} |\n"
                resp += "\n> 💡 *Para ranking ponderado personalizado, especifica los pesos de cada métrica.*"
            else:
                resp += "No hay datos para el ranking."
            return resp, df

        # ── kpis_personalizados ───────────────────────────────────────────────
        if accion == 'kpis_personalizados':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            resumen = datos.get('resumen', {})
            ventas = resumen.get('total_ventas', 0)
            ordenes = resumen.get('ordenes', 1) or 1
            resp = (
                f"## KPIs Personalizados\n\n"
                f"**Período:** {fi} a {ff}\n\n"
                f"Especifica qué métricas deseas monitorear. Por ejemplo:\n"
                f"- _'KPI: ventas por vendedor vs meta $X'_\n"
                f"- _'KPI: stock mínimo por producto'_\n"
                f"- _'KPI: días promedio de cobro'_\n\n"
                f"**Datos base disponibles:**\n"
                f"- 💰 Ventas: ${ventas:,.2f} | Órdenes: {ordenes:,} | Ticket promedio: ${ventas/ordenes:,.2f}\n"
            )
            return resp, None

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_matematicas(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        temp = getattr(consulta, 'temporalidad', {}) or {}
        fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')
        params = getattr(consulta, 'parametros', {}) or {}

        if accion == 'calculo_cagr':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            resumen = datos.get('resumen', {})
            total = resumen.get('total_ventas', 0)
            resp = f"## CAGR — Tasa de Crecimiento Anual Compuesto\n\n"
            resp += f"**Período:** {fi} a {ff}\n"
            resp += f"**Ventas del período:** ${total:,.2f}\n\n"
            resp += "Para calcular el CAGR se requieren al menos 2 períodos anuales. "
            resp += "Intenta con un rango de al menos 2 años.\n"
            df = pd.DataFrame(datos.get('por_cliente', []))
            return resp, df if not df.empty else None

        if accion == 'calculo_margen_contribucion':
            datos = self.analizador.top_productos_vendidos(fi, ff)
            if 'error' not in datos and datos.get('productos'):
                df = pd.DataFrame(datos['productos'])
                resp = "## Margen de Contribución por Producto\n\n"
                return resp, df

        # ── calculo_roi ──────────────────────────────────────────────────────
        if accion == 'calculo_roi':
            inversion = params.get('inversion', 0) or params.get('costo', 0)
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            ventas = datos.get('resumen', {}).get('total_ventas', 0)
            if not inversion and ventas:
                # Estimar inversión como 60% de ventas (costo estimado) si no se dio
                inversion = ventas * 0.6
            ganancia = ventas - inversion
            roi = (ganancia / inversion * 100) if inversion > 0 else 0
            resp = (
                f"## ROI — Retorno sobre Inversión\n\n"
                f"**Período:** {fi} a {ff}\n\n"
                f"| Concepto | Valor |\n|---|---:|\n"
                f"| 💰 Ingresos (ventas) | **${ventas:,.2f}** |\n"
                f"| 💳 Inversión/Costo | **${inversion:,.2f}** |\n"
                f"| 📈 Ganancia neta | **${ganancia:,.2f}** |\n"
                f"| 🎯 **ROI** | **{roi:.1f}%** |\n\n"
                f"**Fórmula:** ROI = (Ganancia − Inversión) / Inversión × 100\n\n"
            )
            if not params.get('inversion'):
                resp += "> ⚠️ *La inversión fue estimada como el 60% de los ingresos. Especifica el costo real para mayor precisión.*\n"
            df = pd.DataFrame(datos.get('por_cliente', []))
            return resp, df if not df.empty else None

        # ── calculo_margenes ─────────────────────────────────────────────────
        if accion == 'calculo_margenes':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            resumen = datos.get('resumen', {})
            ventas = resumen.get('total_ventas', 0)
            costo_est = ventas * 0.65
            margen_bruto = ventas - costo_est
            margen_pct = (margen_bruto / ventas * 100) if ventas > 0 else 0
            resp = (
                f"## Análisis de Márgenes\n\n"
                f"**Período:** {fi} a {ff}\n\n"
                f"| Métrica | Valor |\n|---|---:|\n"
                f"| 💰 Ventas netas | **${ventas:,.2f}** |\n"
                f"| 🏭 Costo estimado (65%) | **${costo_est:,.2f}** |\n"
                f"| 📊 Margen bruto | **${margen_bruto:,.2f}** |\n"
                f"| 🎯 % Margen bruto | **{margen_pct:.1f}%** |\n\n"
                f"> 💡 *Para márgenes exactos se requieren costos estándar (`standard_price`) en Odoo.*\n\n"
                f"> *¿Quieres ver margen por producto o calculo_margen_contribucion?*"
            )
            df = pd.DataFrame(datos.get('por_cliente', []))
            return resp, df if not df.empty else None

        # ── calculo_rentabilidad ─────────────────────────────────────────────
        if accion == 'calculo_rentabilidad':
            datos = self.analizador.analisis_facturacion(fi, ff)
            resumen = datos.get('resumen', {})
            total = resumen.get('total_facturado', 0)
            cobrado = resumen.get('total_cobrado', total)
            pend = total - cobrado
            resp = (
                f"## Análisis de Rentabilidad\n\n"
                f"**Período:** {fi} a {ff}\n\n"
                f"| Métrica | Valor |\n|---|---:|\n"
                f"| 💰 Total facturado | **${total:,.2f}** |\n"
                f"| ✅ Cobrado | **${cobrado:,.2f}** |\n"
                f"| ⏳ Pendiente | **${pend:,.2f}** |\n"
                f"| 📈 % Cobro efectivo | **{(cobrado/total*100 if total>0 else 0):.1f}%** |\n\n"
                f"> 💡 *Para rentabilidad neta completa se necesitan datos de costos operativos.*"
            )
            return resp, None

        # ── calculo_break_even / calculo_punto_equilibrio ────────────────────
        if accion in ('calculo_break_even', 'calculo_punto_equilibrio'):
            costo_fijo = float(params.get('costo_fijo', 0) or params.get('fixed_cost', 0))
            precio_venta = float(params.get('precio', 0) or params.get('precio_venta', 0))
            costo_variable = float(params.get('costo_variable', 0) or params.get('variable_cost', 0))
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            ventas = datos.get('resumen', {}).get('total_ventas', 0)
            ordenes = datos.get('resumen', {}).get('ordenes', 1) or 1
            if not precio_venta:
                precio_venta = ventas / ordenes
            if not costo_variable:
                costo_variable = precio_venta * 0.65
            if not costo_fijo:
                costo_fijo = ventas * 0.20
            mc_unitario = precio_venta - costo_variable
            pe_unidades = (costo_fijo / mc_unitario) if mc_unitario > 0 else 0
            pe_ventas = pe_unidades * precio_venta
            resp = (
                f"## Punto de Equilibrio (Break-Even)\n\n"
                f"**Fórmula:** PE = Costos Fijos / (Precio − Costo Variable Unitario)\n\n"
                f"| Parámetro | Valor |\n|---|---:|\n"
                f"| 💳 Costo fijo total | **${costo_fijo:,.2f}** |\n"
                f"| 🏷️ Precio de venta unitario | **${precio_venta:,.2f}** |\n"
                f"| 🏭 Costo variable unitario | **${costo_variable:,.2f}** |\n"
                f"| 📊 Margen de contribución unitario | **${mc_unitario:,.2f}** |\n\n"
                f"**Resultado:**\n"
                f"- 📦 PE en unidades: **{pe_unidades:,.0f} unidades**\n"
                f"- 💰 PE en ventas: **${pe_ventas:,.2f}**\n\n"
            )
            if not params.get('costo_fijo'):
                resp += "> ⚠️ *Valores estimados desde datos históricos de Odoo. Proporciona tus costos reales para un resultado preciso.*\n"
            return resp, None

        # ── calculo_crecimiento ──────────────────────────────────────────────
        if accion == 'calculo_crecimiento':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            ventas = datos.get('resumen', {}).get('total_ventas', 0)
            resp = (
                f"## Análisis de Crecimiento\n\n"
                f"**Período actual:** {fi} a {ff}\n"
                f"**Ventas del período:** ${ventas:,.2f}\n\n"
                f"> 💡 *Para calcular la tasa de crecimiento compara con: 'ventas de [período anterior] vs [período actual]'.*\n\n"
                f"**Fórmula:** Crecimiento = (Valor Final − Valor Inicial) / Valor Inicial × 100"
            )
            datos_pred = self.predictor.comparar_periodos('mes')
            if 'error' not in datos_pred:
                var = datos_pred.get('variacion_pct', 0)
                resp += f"\n\n**Variación vs. mes anterior:** {var:+.1f}%"
            return resp, None

        # ── calculo_descuentos ───────────────────────────────────────────────
        if accion == 'calculo_descuentos':
            try:
                if self.odoo and self.odoo.conectado:
                    df = self.odoo.buscar(
                        'sale.order.line',
                        filtro=[('order_id.date_order', '>=', fi), ('order_id.date_order', '<=', ff),
                                ('discount', '>', 0), ('order_id.state', 'in', ['sale', 'done'])],
                        campos=['product_id', 'price_unit', 'discount', 'price_subtotal', 'product_uom_qty'],
                        limite=300
                    )
                    if df is not None and not df.empty:
                        total_bruto = (df['price_unit'] * df['product_uom_qty']).sum() if 'price_unit' in df.columns else 0
                        total_neto = df['price_subtotal'].sum() if 'price_subtotal' in df.columns else 0
                        total_desc = total_bruto - total_neto
                        pct_desc = (total_desc / total_bruto * 100) if total_bruto > 0 else 0
                        avg_desc = df['discount'].mean() if 'discount' in df.columns else 0
                        resp = (
                            f"## Análisis de Descuentos\n\n"
                            f"**Período:** {fi} a {ff}\n\n"
                            f"| Métrica | Valor |\n|---|---:|\n"
                            f"| 🏷️ Líneas con descuento | **{len(df):,}** |\n"
                            f"| 💰 Monto bruto (sin descuento) | **${total_bruto:,.2f}** |\n"
                            f"| 💳 Monto neto (con descuento) | **${total_neto:,.2f}** |\n"
                            f"| 📉 Total descuentos otorgados | **${total_desc:,.2f}** |\n"
                            f"| 🎯 % Descuento sobre ventas | **{pct_desc:.1f}%** |\n"
                            f"| 📊 Descuento promedio por línea | **{avg_desc:.1f}%** |\n\n"
                        )
                        if pct_desc > 15:
                            resp += "⚠️ **Alerta:** Nivel de descuentos alto. Revisar política de precios y margen mínimo.\n"
                        return resp, df
            except Exception:
                pass
            return "## Descuentos\n\nNo se encontraron líneas con descuento en el período.", None

        # ── calculo_tir ──────────────────────────────────────────────────────
        if accion == 'calculo_tir':
            flujos = params.get('flujos', [])
            if flujos:
                # Calcular TIR con Newton-Raphson simplificado
                try:
                    def npv(r, flows):
                        return sum(c / (1 + r) ** i for i, c in enumerate(flows))
                    r = 0.1
                    for _ in range(100):
                        nr = npv(r, flujos)
                        dnr = sum(-i * c / (1 + r) ** (i + 1) for i, c in enumerate(flujos))
                        if abs(dnr) < 1e-12:
                            break
                        r -= nr / dnr
                    tir_pct = r * 100
                    resp = (
                        f"## TIR — Tasa Interna de Retorno\n\n"
                        f"**Flujos de caja:** {flujos}\n\n"
                        f"**TIR calculada: {tir_pct:.2f}%**\n\n"
                        f"- Si TIR > Costo de capital → el proyecto es viable ✅\n"
                        f"- Si TIR < Costo de capital → el proyecto no es rentable ❌\n"
                    )
                    return resp, None
                except Exception:
                    pass
            return (
                "## TIR — Tasa Interna de Retorno\n\n"
                "Para calcular la TIR proporciona los flujos de caja anuales.\n\n"
                "**Ejemplo:** `calcula la TIR con flujos [-100000, 30000, 40000, 50000, 60000]`\n\n"
                "**Fórmula:** Σ [CFt / (1+TIR)^t] = 0", None
            )

        # ── calculo_vpn ──────────────────────────────────────────────────────
        if accion == 'calculo_vpn':
            flujos = params.get('flujos', [])
            tasa = float(params.get('tasa', params.get('wacc', 0.10)))
            if flujos:
                vpn = sum(c / (1 + tasa) ** i for i, c in enumerate(flujos))
                resp = (
                    f"## VPN — Valor Presente Neto\n\n"
                    f"**Flujos:** {flujos} | **Tasa de descuento:** {tasa*100:.1f}%\n\n"
                    f"**VPN = ${vpn:,.2f}**\n\n"
                    f"{'✅ VPN positivo: el proyecto genera valor.' if vpn > 0 else '❌ VPN negativo: el proyecto destruye valor.'}\n\n"
                    f"**Fórmula:** VPN = Σ [CFt / (1+r)^t]"
                )
                return resp, None
            return (
                "## VPN — Valor Presente Neto\n\n"
                "Proporciona los flujos de caja y la tasa de descuento.\n\n"
                "**Ejemplo:** `calcula VPN con flujos [-500000, 150000, 200000, 250000] y tasa 10%`\n\n"
                "**Fórmula:** VPN = Σ [CFt / (1+r)^t]", None
            )

        # ── calculo_amortizacion ─────────────────────────────────────────────
        if accion == 'calculo_amortizacion':
            capital = float(params.get('capital', params.get('monto', 0)))
            tasa_anual = float(params.get('tasa', 0.12)) / 12
            periodos = int(params.get('periodos', params.get('meses', 12)))
            if capital and tasa_anual and periodos:
                cuota = capital * (tasa_anual * (1 + tasa_anual) ** periodos) / ((1 + tasa_anual) ** periodos - 1) if tasa_anual > 0 else capital / periodos
                filas = []
                saldo = capital
                for i in range(1, min(periodos + 1, 13)):
                    interes = saldo * tasa_anual
                    amort = cuota - interes
                    saldo -= amort
                    filas.append({'Período': i, 'Cuota': cuota, 'Capital': amort, 'Interés': interes, 'Saldo': max(saldo, 0)})
                df = pd.DataFrame(filas)
                resp = (
                    f"## Tabla de Amortización\n\n"
                    f"**Capital:** ${capital:,.2f} | **Tasa mensual:** {tasa_anual*100:.2f}% | **Períodos:** {periodos} meses\n\n"
                    f"**Cuota mensual fija: ${cuota:,.2f}**\n\n"
                    f"| Período | Cuota | Capital | Interés | Saldo |\n|---|---:|---:|---:|---:|\n"
                )
                for _, r in df.head(12).iterrows():
                    resp += f"| {int(r['Período'])} | ${r['Cuota']:,.2f} | ${r['Capital']:,.2f} | ${r['Interés']:,.2f} | ${r['Saldo']:,.2f} |\n"
                if periodos > 12:
                    resp += f"\n*...mostrando los primeros 12 de {periodos} períodos*"
                return resp, df
            return (
                "## Tabla de Amortización\n\n"
                "Proporciona: **capital**, **tasa anual** y **número de meses**.\n\n"
                "**Ejemplo:** `amortización de $500,000 a 10% anual en 36 meses`", None
            )

        # ── analisis_sensibilidad ────────────────────────────────────────────
        if accion == 'analisis_sensibilidad':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            ventas_base = datos.get('resumen', {}).get('total_ventas', 0)
            filas = []
            for var_pct in [-20, -10, -5, 0, 5, 10, 20]:
                ventas_esc = ventas_base * (1 + var_pct / 100)
                costo_esc = ventas_esc * 0.65
                margen_esc = ventas_esc - costo_esc
                filas.append({'Variación': f"{var_pct:+.0f}%", 'Ventas': ventas_esc,
                               'Costo': costo_esc, 'Margen': margen_esc})
            df = pd.DataFrame(filas)
            resp = (
                f"## Análisis de Sensibilidad\n\n"
                f"**Base:** ${ventas_base:,.2f} en ventas ({fi} → {ff})\n\n"
                f"| Variación en ventas | Ingresos | Costo (65%) | Margen |\n|---|---:|---:|---:|\n"
            )
            for _, r in df.iterrows():
                emoji = "🟢" if float(r['Margen']) > 0 else "🔴"
                resp += f"| {r['Variación']} | ${float(r['Ventas']):,.2f} | ${float(r['Costo']):,.2f} | {emoji} ${float(r['Margen']):,.2f} |\n"
            resp += "\n> 💡 *Ajusta el % de costo variable para escenarios más precisos.*"
            return resp, df

        # ── calculo_payback ──────────────────────────────────────────────────
        if accion == 'calculo_payback':
            inversion = float(params.get('inversion', 0) or params.get('capital', 0))
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            ventas_mes = datos.get('resumen', {}).get('total_ventas', 0) / 12
            margen_mes = ventas_mes * 0.35
            if not inversion:
                inversion = ventas_mes * 6
            meses_payback = (inversion / margen_mes) if margen_mes > 0 else 0
            resp = (
                f"## Período de Recuperación (Payback)\n\n"
                f"| Concepto | Valor |\n|---|---:|\n"
                f"| 💳 Inversión inicial | **${inversion:,.2f}** |\n"
                f"| 💰 Flujo mensual estimado | **${margen_mes:,.2f}** |\n"
                f"| ⏱️ **Payback** | **{meses_payback:.1f} meses ({meses_payback/12:.1f} años)** |\n\n"
                f"**Fórmula:** Payback = Inversión / Flujo de Caja Mensual\n\n"
            )
            if not params.get('inversion'):
                resp += "> ⚠️ *Inversión y flujos estimados. Proporciona los valores reales para precisión.*"
            return resp, None

        # ── calculo_wacc ─────────────────────────────────────────────────────
        if accion == 'calculo_wacc':
            ke = float(params.get('ke', params.get('costo_capital', 0.15)))
            kd = float(params.get('kd', params.get('costo_deuda', 0.08)))
            e_pct = float(params.get('equity_pct', 0.60))
            d_pct = 1 - e_pct
            tasa_imp = float(params.get('impuestos', 0.30))
            wacc = ke * e_pct + kd * (1 - tasa_imp) * d_pct
            resp = (
                f"## WACC — Costo Promedio Ponderado de Capital\n\n"
                f"| Componente | Valor |\n|---|---:|\n"
                f"| 💼 Costo del capital propio (Ke) | **{ke*100:.1f}%** |\n"
                f"| 🏦 Costo de deuda (Kd) | **{kd*100:.1f}%** |\n"
                f"| 📊 Proporción capital propio | **{e_pct*100:.0f}%** |\n"
                f"| 💳 Proporción deuda | **{d_pct*100:.0f}%** |\n"
                f"| 🧾 Tasa impositiva | **{tasa_imp*100:.0f}%** |\n"
                f"| 🎯 **WACC** | **{wacc*100:.2f}%** |\n\n"
                f"**Fórmula:** WACC = Ke × (E/V) + Kd × (1−t) × (D/V)\n\n"
                f"> 💡 *Si la TIR del proyecto > WACC ({wacc*100:.2f}%), el proyecto crea valor.*"
            )
            return resp, None

        # ── depreciacion ─────────────────────────────────────────────────────
        if accion == 'depreciacion':
            valor = float(params.get('valor', params.get('costo', 0)))
            vida_util = int(params.get('vida_util', params.get('anos', 5)))
            valor_residual = float(params.get('valor_residual', 0))
            metodo = params.get('metodo', 'lineal')
            if not valor:
                return (
                    "## Cálculo de Depreciación\n\n"
                    "Proporciona: **valor del activo**, **vida útil** y **método** (lineal/decreciente).\n\n"
                    "**Ejemplo:** `deprecia un activo de $500,000 en 5 años por método lineal`", None
                )
            dep_anual = (valor - valor_residual) / vida_util
            filas = []
            val_libro = valor
            for i in range(1, vida_util + 1):
                dep = dep_anual if metodo == 'lineal' else (val_libro * (2 / vida_util))
                val_libro -= dep
                filas.append({'Año': i, 'Depreciación': dep, 'Valor en libros': max(val_libro, valor_residual)})
            df = pd.DataFrame(filas)
            resp = (
                f"## Depreciación — Método {metodo.title()}\n\n"
                f"**Activo:** ${valor:,.2f} | **Vida útil:** {vida_util} años | **Valor residual:** ${valor_residual:,.2f}\n\n"
                f"**Depreciación anual:** ${dep_anual:,.2f}\n\n"
                f"| Año | Depreciación | Valor en Libros |\n|---|---:|---:|\n"
            )
            for _, r in df.iterrows():
                resp += f"| {int(r['Año'])} | ${float(r['Depreciación']):,.2f} | ${float(r['Valor en libros']):,.2f} |\n"
            return resp, df

        # ── calculo_elasticidad ──────────────────────────────────────────────
        if accion == 'calculo_elasticidad':
            delta_q = float(params.get('delta_q', params.get('cambio_cantidad', 0)))
            delta_p = float(params.get('delta_p', params.get('cambio_precio', 0)))
            if delta_q and delta_p:
                elasticidad = delta_q / delta_p
                tipo = "Elástica" if abs(elasticidad) > 1 else "Inelástica" if abs(elasticidad) < 1 else "Unitaria"
                resp = (
                    f"## Elasticidad Precio-Demanda\n\n"
                    f"**ΔCantidad:** {delta_q:+.1f}% | **ΔPrecio:** {delta_p:+.1f}%\n\n"
                    f"**Elasticidad = {elasticidad:.2f}** → Demanda **{tipo}**\n\n"
                    f"| Elasticidad | Interpretación |\n|---|---|\n"
                    f"| |E| > 1 | Elástica: los consumidores son sensibles al precio |\n"
                    f"| |E| < 1 | Inelástica: precio no afecta mucho la demanda |\n"
                    f"| |E| = 1 | Unitaria: % cambio igual en precio y cantidad |\n"
                )
                return resp, None
            return (
                "## Elasticidad Precio-Demanda\n\n"
                "**Fórmula:** E = (%ΔCantidad) / (%ΔPrecio)\n\n"
                "**Ejemplo:** `elasticidad si precio sube 10% y ventas bajan 15%`\n\n"
                "Con E = -15% / 10% = **-1.5** → Demanda Elástica.", None
            )

        # ── analisis_apalancamiento ──────────────────────────────────────────
        if accion == 'analisis_apalancamiento':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            ventas = datos.get('resumen', {}).get('total_ventas', 0)
            costos_var = ventas * 0.65
            costos_fijos = ventas * 0.15
            uaii = ventas - costos_var - costos_fijos
            gao = ((ventas - costos_var) / uaii) if uaii != 0 else 0
            resp = (
                f"## Análisis de Apalancamiento Operativo\n\n"
                f"**Período:** {fi} a {ff}\n\n"
                f"| Métrica | Valor |\n|---|---:|\n"
                f"| 💰 Ventas | **${ventas:,.2f}** |\n"
                f"| 🏭 Costos variables (65%) | **${costos_var:,.2f}** |\n"
                f"| 🏢 Costos fijos (15%) | **${costos_fijos:,.2f}** |\n"
                f"| 📊 UAII (EBIT) | **${uaii:,.2f}** |\n"
                f"| 🎯 **GAO** (Grado Apal. Operativo) | **{gao:.2f}x** |\n\n"
                f"**Interpretación:** Un GAO de {gao:.2f}x significa que si las ventas suben 1%, la utilidad operativa sube {gao:.2f}%.\n\n"
                f"> ⚠️ *Costos estimados. Para precisión, configura costos reales en Odoo.*"
            )
            return resp, None

        # ── calculo_dupont ───────────────────────────────────────────────────
        if accion == 'calculo_dupont':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            ventas = datos.get('resumen', {}).get('total_ventas', 0)
            utilidad_neta = ventas * 0.12
            activos_totales = ventas * 1.5
            patrimonio = activos_totales * 0.60
            margen = (utilidad_neta / ventas * 100) if ventas > 0 else 0
            rotacion = ventas / activos_totales if activos_totales > 0 else 0
            multiplic = activos_totales / patrimonio if patrimonio > 0 else 0
            roe = margen / 100 * rotacion * multiplic * 100
            resp = (
                f"## Análisis DuPont\n\n"
                f"**ROE = Margen Neto × Rotación de Activos × Multiplicador de Capital**\n\n"
                f"| Factor DuPont | Valor |\n|---|---:|\n"
                f"| 📊 Margen neto (Utilidad/Ventas) | **{margen:.1f}%** |\n"
                f"| 🔄 Rotación activos (Ventas/Activos) | **{rotacion:.2f}x** |\n"
                f"| 💳 Multiplicador capital (Activos/Patrimonio) | **{multiplic:.2f}x** |\n"
                f"| 🎯 **ROE estimado** | **{roe:.1f}%** |\n\n"
                f"> ⚠️ *Utilidad y activos estimados. Para cálculo exacto se requiere balance general.*"
            )
            return resp, None

        # ── calculo_capital_requerido ────────────────────────────────────────
        if accion == 'calculo_capital_requerido':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            cxc = datos.get('resumen', {}).get('total_cxc', 0) or 0
            inventario_val = 0
            try:
                inv = self.analizador.analisis_inventario()
                inventario_val = inv.get('valoracion', {}).get('total', 0) or 0
            except Exception:
                pass
            cxp = datos.get('resumen', {}).get('total_cxp', 0) or 0
            capital_trabajo = (cxc + inventario_val) - cxp
            resp = (
                f"## Capital de Trabajo Requerido\n\n"
                f"**Fórmula:** CT = (CxC + Inventario) − CxP\n\n"
                f"| Componente | Valor |\n|---|---:|\n"
                f"| 📋 Cuentas por cobrar (CxC) | **${cxc:,.2f}** |\n"
                f"| 📦 Valor inventario | **${inventario_val:,.2f}** |\n"
                f"| 💳 Cuentas por pagar (CxP) | **${cxp:,.2f}** |\n"
                f"| 🎯 **Capital de Trabajo Neto** | **${capital_trabajo:,.2f}** |\n\n"
                f"{'🟢 Capital positivo: suficiente liquidez operativa.' if capital_trabajo > 0 else '🔴 Capital negativo: riesgo de iliquidez. Revisar política de cobro y pago.'}"
            )
            return resp, None

        # ── proyeccion_financiera ────────────────────────────────────────────
        if accion == 'proyeccion_financiera':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            ventas = datos.get('resumen', {}).get('total_ventas', 0)
            meses = int(params.get('meses', params.get('periodos', 6)))
            tasa_crec = float(params.get('tasa_crecimiento', 0.05))
            filas = []
            base = ventas / 12 if ventas else 0
            for i in range(1, meses + 1):
                proy = base * (1 + tasa_crec) ** i
                costo = proy * 0.65
                margen = proy - costo
                filas.append({'Mes': i, 'Ventas Proyectadas': proy, 'Costo': costo, 'Margen': margen})
            df = pd.DataFrame(filas)
            resp = (
                f"## Proyección Financiera — {meses} meses\n\n"
                f"**Base mensual:** ${base:,.2f} | **Tasa de crecimiento:** {tasa_crec*100:.1f}% mensual\n\n"
                f"| Mes | Ventas Proyectadas | Costo (65%) | Margen |\n|---|---:|---:|---:|\n"
            )
            for _, r in df.iterrows():
                resp += f"| {int(r['Mes'])} | ${float(r['Ventas Proyectadas']):,.2f} | ${float(r['Costo']):,.2f} | ${float(r['Margen']):,.2f} |\n"
            total_proy = df['Ventas Proyectadas'].sum() if not df.empty else 0
            resp += f"\n**Total proyectado {meses} meses:** ${total_proy:,.2f}\n\n"
            resp += "> ⚠️ *Proyección basada en datos históricos de Odoo con crecimiento lineal. Ajusta la tasa según tu estrategia.*"
            return resp, df

        return self._ejecutar_accion(consulta, mensaje)

