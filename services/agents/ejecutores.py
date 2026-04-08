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

        if accion == 'clientes_nuevos_vs_recurrentes' and self.consultas_esp:
            datos = self.consultas_esp.clientes_analisis()
            if 'error' not in datos:
                resp = "## Clientes Nuevos vs Recurrentes\n\n"
                resumen = datos.get('resumen', {})
                resp += f"- **Total clientes:** {resumen.get('total', 0):,}\n"
                resp += f"- **Con email:** {resumen.get('con_email', 0):,}\n"
                resp += f"- **Con teléfono:** {resumen.get('con_telefono', 0):,}\n"
                df = pd.DataFrame(datos.get('por_ciudad', [])) if datos.get('por_ciudad') else None
                return resp, df

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

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_finanzas(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        temp = getattr(consulta, 'temporalidad', {}) or {}
        fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')

        if accion == 'rentabilidad_cliente':
            datos = self.analizador.analisis_ventas_completo(fi, ff)
            if 'por_cliente' in datos:
                df = pd.DataFrame(datos['por_cliente'])
                resp = f"## Rentabilidad por Cliente\n\n**Período:** {fi} a {ff}\n\n"
                return resp, df

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

        if accion == 'facturacion_por_empresa' and self.consultas_esp:
            datos = self.consultas_esp.empresas_resumen()
            if 'error' not in datos and datos.get('empresas'):
                df = pd.DataFrame(datos['empresas'])
                resp = "## Facturación por Empresa\n\n"
                return resp, df

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_crm(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')

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

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_diagnostico(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')

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

        return self._ejecutar_accion(consulta, mensaje)

    def _ejecutor_matematicas(self, consulta, mensaje: str) -> Tuple[str, pd.DataFrame]:
        accion = getattr(consulta, 'accion_sugerida', '')
        temp = getattr(consulta, 'temporalidad', {}) or {}
        fi, ff = temp.get('fecha_inicio', ''), temp.get('fecha_fin', '')

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

        return self._ejecutar_accion(consulta, mensaje)

