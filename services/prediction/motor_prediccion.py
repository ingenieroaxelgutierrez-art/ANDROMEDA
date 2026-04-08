# ============================================================
# MOTOR DE PREDICCIÓN - ANÁLISIS PREDICTIVO PARA ODOO
# ============================================================
# Predicciones basadas en datos históricos
# Tendencias, proyecciones y alertas inteligentes
# ============================================================

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from collections import defaultdict

from app.logging_config import get_logger
logger = get_logger("services.prediction.motor_prediccion")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@dataclass
class Prediccion:
    """Resultado de una predicción."""
    tipo: str
    valor_actual: float
    valor_predicho: float
    tendencia: str  # 'alza', 'baja', 'estable'
    confianza: float  # 0-100
    periodo: str
    insights: List[str]
    datos_historicos: List[Dict]
    alertas: List[str]


class MotorPrediccion:
    """Motor de predicción y análisis predictivo."""
    
    def __init__(self):
        self.conector = None
        self.cache_historico = {}
    
    def set_conector(self, conector):
        """Configura el conector de Odoo."""
        self.conector = conector
    
    # ========================================================
    # PREDICCIÓN DE VENTAS
    # ========================================================
    
    def predecir_ventas(self, dias_futuro: int = 7) -> Prediccion:
        """Predice ventas para los próximos días."""
        if not self.conector:
            return self._error_prediccion("ventas")
        
        try:
            # Obtener histórico de 90 días
            historico = self._obtener_historico_ventas(90)
            
            if len(historico) < 7:
                return self._error_prediccion("ventas", "Pocos datos históricos")
            
            # Calcular tendencia
            df = pd.DataFrame(historico)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df = df.sort_values('fecha')
            
            # Media móvil de 7 días
            df['media_movil'] = df['total'].rolling(window=7, min_periods=1).mean()
            
            # Tendencia lineal simple
            x = np.arange(len(df))
            y = df['total'].values
            
            # Regresión lineal básica
            n = len(x)
            if n > 1:
                slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
                intercept = (np.sum(y) - slope * np.sum(x)) / n
            else:
                slope = 0
                intercept = y[0] if len(y) > 0 else 0
            
            # Predecir próximos días
            predicciones = []
            ultimo_idx = len(df)
            for i in range(dias_futuro):
                pred = slope * (ultimo_idx + i) + intercept
                pred = max(0, pred)  # No negativos
                fecha_pred = datetime.now() + timedelta(days=i+1)
                predicciones.append({
                    'fecha': fecha_pred.strftime('%Y-%m-%d'),
                    'prediccion': round(pred, 2)
                })
            
            # Determinar tendencia
            promedio_reciente = df['total'].tail(7).mean()
            promedio_anterior = df['total'].head(7).mean()
            
            if slope > promedio_reciente * 0.02:
                tendencia = 'alza'
            elif slope < -promedio_reciente * 0.02:
                tendencia = 'baja'
            else:
                tendencia = 'estable'
            
            # Calcular confianza basada en variabilidad
            if len(df) > 1:
                std = df['total'].std()
                mean = df['total'].mean()
                cv = (std / mean) * 100 if mean > 0 else 100
                confianza = max(30, min(95, 100 - cv))
            else:
                confianza = 50
            
            # Generar insights
            insights = self._generar_insights_ventas(df, slope, tendencia, predicciones)
            
            # Alertas
            alertas = self._generar_alertas_ventas(df, predicciones, tendencia)
            
            # Total predicho
            valor_predicho = sum(p['prediccion'] for p in predicciones)
            
            return Prediccion(
                tipo='ventas',
                valor_actual=round(promedio_reciente * dias_futuro, 2),
                valor_predicho=round(valor_predicho, 2),
                tendencia=tendencia,
                confianza=round(confianza, 1),
                periodo=f"Próximos {dias_futuro} días",
                insights=insights,
                datos_historicos=historico[-30:],  # Últimos 30 días
                alertas=alertas
            )
            
        except Exception as e:
            return self._error_prediccion("ventas", str(e))
    
    def _obtener_historico_ventas(self, dias: int) -> List[Dict]:
        """Obtiene histórico de ventas por día."""
        historico = []
        hoy = datetime.now()
        
        for i in range(dias, -1, -1):
            fecha = (hoy - timedelta(days=i)).strftime('%Y-%m-%d')
            try:
                ventas = self.conector.ventas_periodo(fecha, fecha)
                total = ventas['amount_total'].sum() if not ventas.empty else 0
                cantidad = len(ventas)
                historico.append({
                    'fecha': fecha,
                    'total': float(total),
                    'cantidad': cantidad,
                    'ticket_promedio': float(total / cantidad) if cantidad > 0 else 0
                })
            except Exception:
                historico.append({
                    'fecha': fecha,
                    'total': 0,
                    'cantidad': 0,
                    'ticket_promedio': 0
                })
        
        return historico
    
    def _generar_insights_ventas(self, df: pd.DataFrame, slope: float, tendencia: str, predicciones: List[Dict]) -> List[str]:
        """Genera insights sobre ventas."""
        insights = []
        
        # Tendencia
        if tendencia == 'alza':
            insights.append(f"Las ventas muestran tendencia ALCISTA (+${abs(slope):.2f}/día)")
        elif tendencia == 'baja':
            insights.append(f"Las ventas muestran tendencia BAJISTA (-${abs(slope):.2f}/día)")
        else:
            insights.append("Las ventas se mantienen estables")
        
        # Mejor día
        if len(df) > 0:
            mejor_dia = df.loc[df['total'].idxmax()]
            insights.append(f"🏆 Mejor día: {mejor_dia['fecha'].strftime('%d/%m')} con ${mejor_dia['total']:,.2f}")
        
        # Promedio
        promedio = df['total'].mean()
        insights.append(f"Promedio diario: ${promedio:,.2f}")
        
        # Día de la semana más fuerte
        df['dia_semana'] = df['fecha'].dt.dayofweek
        ventas_por_dia = df.groupby('dia_semana')['total'].mean()
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        if len(ventas_por_dia) > 0:
            mejor_dia_semana = ventas_por_dia.idxmax()
            insights.append(f"Día más fuerte: {dias[mejor_dia_semana]}")
        
        # Proyección
        total_pred = sum(p['prediccion'] for p in predicciones)
        insights.append(f"Proyección próximos {len(predicciones)} días: ${total_pred:,.2f}")
        
        return insights
    
    def _generar_alertas_ventas(self, df: pd.DataFrame, predicciones: List[Dict], tendencia: str) -> List[str]:
        """Genera alertas sobre ventas."""
        alertas = []
        
        if len(df) < 3:
            return alertas
        
        promedio = df['total'].mean()
        ultimo = df['total'].iloc[-1]
        
        # Caída drástica
        if ultimo < promedio * 0.5:
            alertas.append("ALERTA: Ventas del último día muy por debajo del promedio")
        
        # Tendencia negativa sostenida
        if tendencia == 'baja':
            ultimos_7 = df['total'].tail(7)
            if all(ultimos_7.diff().dropna() < 0):
                alertas.append("URGENTE: 7 días consecutivos de caída en ventas")
        
        # Predicción baja
        pred_promedio = np.mean([p['prediccion'] for p in predicciones])
        if pred_promedio < promedio * 0.7:
            alertas.append("AVISO: La proyección indica ventas 30% menores al promedio")
        
        return alertas
    
    # ========================================================
    # PREDICCIÓN DE INVENTARIO
    # ========================================================
    
    def predecir_agotamiento(self, producto_id: int = None, top: int = 20) -> Dict:
        """Predice cuándo se agotarán los productos."""
        if not self.conector:
            return {'error': 'Sin conexión'}
        
        try:
            # Obtener stock actual
            stock = self.conector.stock_disponible()
            
            if stock.empty:
                return {'error': 'Sin datos de stock'}
            
            # Obtener ventas del último mes para calcular velocidad
            hace_30 = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            hoy = datetime.now().strftime('%Y-%m-%d')
            
            # Intentar obtener líneas de venta
            try:
                lineas = self.conector.buscar(
                    'sale.order.line',
                    filtro=[
                        ('order_id.date_order', '>=', hace_30),
                        ('order_id.state', 'in', ['sale', 'done'])
                    ],
                    campos=['product_id', 'product_uom_qty'],
                    limite=5000
                )
            except Exception:
                lineas = pd.DataFrame()
            
            predicciones = []
            
            for _, row in stock.iterrows():
                prod_id = row.get('product_id')
                if isinstance(prod_id, (list, tuple)):
                    prod_id = prod_id[0]
                
                qty = row.get('quantity', 0)
                prod_name = row.get('product_id')
                if isinstance(prod_name, (list, tuple)):
                    prod_name = prod_name[1] if len(prod_name) > 1 else str(prod_name[0])
                
                # Calcular velocidad de venta
                velocidad = 0
                if not lineas.empty:
                    prod_ventas = lineas[lineas['product_id'].apply(
                        lambda x: x[0] if isinstance(x, (list, tuple)) else x
                    ) == prod_id]
                    if not prod_ventas.empty:
                        total_vendido = prod_ventas['product_uom_qty'].sum()
                        velocidad = total_vendido / 30  # Promedio diario
                
                # Calcular días hasta agotamiento
                if velocidad > 0:
                    dias_stock = qty / velocidad
                    fecha_agotamiento = datetime.now() + timedelta(days=dias_stock)
                else:
                    dias_stock = 999
                    fecha_agotamiento = None
                
                predicciones.append({
                    'producto_id': prod_id,
                    'producto': str(prod_name)[:50],
                    'stock_actual': qty,
                    'velocidad_diaria': round(velocidad, 2),
                    'dias_stock': round(dias_stock, 1),
                    'fecha_agotamiento': fecha_agotamiento.strftime('%Y-%m-%d') if fecha_agotamiento else 'N/A',
                    'urgencia': 'CRÍTICO' if dias_stock < 7 else 'ALERTA' if dias_stock < 14 else 'OK'
                })
            
            # Ordenar por días de stock
            predicciones.sort(key=lambda x: x['dias_stock'])
            
            # Filtrar críticos
            criticos = [p for p in predicciones if p['urgencia'] == 'CRÍTICO']
            alertas = [p for p in predicciones if p['urgencia'] == 'ALERTA']
            
            return {
                'predicciones': predicciones[:top],
                'criticos': criticos[:10],
                'alertas': alertas[:10],
                'resumen': {
                    'total_productos': len(predicciones),
                    'criticos': len(criticos),
                    'alertas': len(alertas),
                    'sin_movimiento': len([p for p in predicciones if p['velocidad_diaria'] == 0])
                },
                'insights': [
                    f"{len(criticos)} productos se agotarán en menos de 7 días",
                    f"{len(alertas)} productos en alerta (7-14 días)",
                    f"{len([p for p in predicciones if p['velocidad_diaria'] == 0])} productos sin movimiento en 30 días"
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ========================================================
    # PREDICCIÓN DE FLUJO DE CAJA
    # ========================================================
    
    def predecir_flujo_caja(self, dias: int = 30) -> Dict:
        """Predice el flujo de caja basado en CXC y CXP."""
        if not self.conector:
            return {'error': 'Sin conexión'}
        
        try:
            # Cuentas por cobrar
            cxc = self._obtener_cxc_proyectada()
            
            # Cuentas por pagar
            cxp = self._obtener_cxp_proyectada()
            
            # Proyección de ventas
            pred_ventas = self.predecir_ventas(dias)
            ingresos_proyectados = pred_ventas.valor_predicho if pred_ventas.tipo != 'error' else 0
            
            # Calcular flujo
            entradas = cxc.get('por_cobrar_pronto', 0) + ingresos_proyectados * 0.3  # 30% al contado
            salidas = cxp.get('por_pagar_pronto', 0)
            
            flujo_neto = entradas - salidas
            
            # Proyección semanal
            proyeccion_semanal = []
            for semana in range(1, (dias // 7) + 1):
                entrada_sem = (cxc.get('por_cobrar_pronto', 0) / 4) + (ingresos_proyectados / 4) * 0.3
                salida_sem = cxp.get('por_pagar_pronto', 0) / 4
                proyeccion_semanal.append({
                    'semana': semana,
                    'entradas': round(entrada_sem, 2),
                    'salidas': round(salida_sem, 2),
                    'neto': round(entrada_sem - salida_sem, 2)
                })
            
            return {
                'periodo': f'Próximos {dias} días',
                'entradas_proyectadas': round(entradas, 2),
                'salidas_proyectadas': round(salidas, 2),
                'flujo_neto': round(flujo_neto, 2),
                'estado': 'POSITIVO' if flujo_neto > 0 else 'NEGATIVO',
                'proyeccion_semanal': proyeccion_semanal,
                'cxc': cxc,
                'cxp': cxp,
                'insights': [
                    f"Entradas proyectadas: ${entradas:,.2f}",
                    f"Salidas proyectadas: ${salidas:,.2f}",
                    f"{'📈' if flujo_neto > 0 else '📉'} Flujo neto: ${flujo_neto:,.2f}",
                    f"CXC pendiente: ${cxc.get('total', 0):,.2f}",
                    f"CXP pendiente: ${cxp.get('total', 0):,.2f}"
                ],
                'alertas': self._alertas_flujo(flujo_neto, cxc, cxp)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _obtener_cxc_proyectada(self) -> Dict:
        """Obtiene CXC con proyección de cobro."""
        try:
            facturas = self.conector.buscar(
                'account.move',
                filtro=[
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', '!=', 'paid')
                ],
                campos=['name', 'partner_id', 'amount_residual', 'invoice_date_due'],
                limite=500
            )
            
            total = facturas['amount_residual'].sum() if not facturas.empty else 0
            
            # Por cobrar pronto (vence en 30 días)
            hoy = datetime.now().date()
            en_30 = (datetime.now() + timedelta(days=30)).date()
            
            por_cobrar_pronto = 0
            if not facturas.empty and 'invoice_date_due' in facturas.columns:
                for _, row in facturas.iterrows():
                    fecha = row.get('invoice_date_due')
                    if fecha:
                        if isinstance(fecha, str):
                            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
                        if fecha <= en_30:
                            por_cobrar_pronto += row.get('amount_residual', 0)
            
            return {
                'total': float(total),
                'por_cobrar_pronto': float(por_cobrar_pronto),
                'facturas': len(facturas)
            }
        except Exception:
            return {'total': 0, 'por_cobrar_pronto': 0, 'facturas': 0}
    
    def _obtener_cxp_proyectada(self) -> Dict:
        """Obtiene CXP con proyección de pago."""
        try:
            facturas = self.conector.buscar(
                'account.move',
                filtro=[
                    ('move_type', '=', 'in_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', '!=', 'paid')
                ],
                campos=['name', 'partner_id', 'amount_residual', 'invoice_date_due'],
                limite=500
            )
            
            total = facturas['amount_residual'].sum() if not facturas.empty else 0
            
            # Por pagar pronto
            hoy = datetime.now().date()
            en_30 = (datetime.now() + timedelta(days=30)).date()
            
            por_pagar_pronto = 0
            if not facturas.empty and 'invoice_date_due' in facturas.columns:
                for _, row in facturas.iterrows():
                    fecha = row.get('invoice_date_due')
                    if fecha:
                        if isinstance(fecha, str):
                            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
                        if fecha <= en_30:
                            por_pagar_pronto += row.get('amount_residual', 0)
            
            return {
                'total': float(total),
                'por_pagar_pronto': float(por_pagar_pronto),
                'facturas': len(facturas)
            }
        except Exception:
            return {'total': 0, 'por_pagar_pronto': 0, 'facturas': 0}
    
    def _alertas_flujo(self, flujo_neto: float, cxc: Dict, cxp: Dict) -> List[str]:
        """Genera alertas de flujo de caja."""
        alertas = []
        
        if flujo_neto < 0:
            alertas.append("ALERTA: Flujo de caja negativo proyectado")
        
        if cxp.get('por_pagar_pronto', 0) > cxc.get('por_cobrar_pronto', 0):
            alertas.append("Las salidas superan las entradas inmediatas")
        
        if cxc.get('total', 0) > 0:
            ratio = cxc.get('por_cobrar_pronto', 0) / cxc.get('total', 1)
            if ratio < 0.3:
                alertas.append("Solo 30% de la cartera vence pronto - evaluar políticas de crédito")
        
        return alertas
    
    # ========================================================
    # ANÁLISIS DE ESTACIONALIDAD
    # ========================================================
    
    def analizar_estacionalidad(self) -> Dict:
        """Analiza patrones estacionales en ventas."""
        if not self.conector:
            return {'error': 'Sin conexión'}
        
        try:
            # Obtener histórico amplio
            historico = self._obtener_historico_ventas(365)
            
            if len(historico) < 30:
                return {'error': 'Se requieren al menos 30 días de datos'}
            
            df = pd.DataFrame(historico)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['dia_semana'] = df['fecha'].dt.dayofweek
            df['mes'] = df['fecha'].dt.month
            df['semana_mes'] = df['fecha'].dt.day // 7 + 1
            
            # Análisis por día de la semana
            dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            por_dia = df.groupby('dia_semana')['total'].agg(['mean', 'sum', 'count']).reset_index()
            por_dia['dia'] = por_dia['dia_semana'].apply(lambda x: dias[x])
            
            # Análisis por mes
            meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                     'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            por_mes = df.groupby('mes')['total'].agg(['mean', 'sum', 'count']).reset_index()
            por_mes['nombre_mes'] = por_mes['mes'].apply(lambda x: meses[x-1] if 1 <= x <= 12 else 'N/A')
            
            # Mejores y peores días
            mejor_dia = dias[por_dia.loc[por_dia['mean'].idxmax(), 'dia_semana']]
            peor_dia = dias[por_dia.loc[por_dia['mean'].idxmin(), 'dia_semana']]
            
            # Mejores y peores meses (si hay datos)
            meses_con_datos = por_mes[por_mes['count'] > 0]
            mejor_mes = meses_con_datos.loc[meses_con_datos['mean'].idxmax(), 'nombre_mes'] if len(meses_con_datos) > 0 else 'N/A'
            peor_mes = meses_con_datos.loc[meses_con_datos['mean'].idxmin(), 'nombre_mes'] if len(meses_con_datos) > 0 else 'N/A'
            
            return {
                'por_dia_semana': por_dia.to_dict('records'),
                'por_mes': por_mes.to_dict('records'),
                'mejor_dia': mejor_dia,
                'peor_dia': peor_dia,
                'mejor_mes': mejor_mes,
                'peor_mes': peor_mes,
                'insights': [
                    f"Mejor día de la semana: {mejor_dia}",
                    f"Día más bajo: {peor_dia}",
                    f"Mes más fuerte: {mejor_mes}",
                    f"Mes más débil: {peor_mes}",
                    f"Días analizados: {len(df)}"
                ],
                'recomendaciones': self._recomendaciones_estacionalidad(mejor_dia, peor_dia, mejor_mes, peor_mes)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _recomendaciones_estacionalidad(self, mejor_dia: str, peor_dia: str, mejor_mes: str, peor_mes: str) -> List[str]:
        """Genera recomendaciones basadas en estacionalidad."""
        recs = []
        
        recs.append(f"Planifica promociones especiales para {peor_dia} para aumentar ventas")
        recs.append(f"Maximiza inventario y personal los {mejor_dia}")
        
        if mejor_mes != 'N/A':
            recs.append(f"Prepara campañas agresivas para {mejor_mes}")
        
        if peor_mes != 'N/A':
            recs.append(f"Considera promociones especiales en {peor_mes}")
        
        return recs
    
    # ========================================================
    # ANÁLISIS COMPARATIVO (PASADO VS PRESENTE)
    # ========================================================
    
    def comparar_periodos(self, tipo: str = 'semana') -> Dict:
        """Compara el período actual vs anterior."""
        if not self.conector:
            return {'error': 'Sin conexión'}
        
        try:
            hoy = datetime.now()
            
            if tipo == 'dia':
                actual_ini = actual_fin = hoy.strftime('%Y-%m-%d')
                anterior_ini = anterior_fin = (hoy - timedelta(days=1)).strftime('%Y-%m-%d')
                periodo_actual = "Hoy"
                periodo_anterior = "Ayer"
            elif tipo == 'semana':
                inicio_semana = hoy - timedelta(days=hoy.weekday())
                actual_ini = inicio_semana.strftime('%Y-%m-%d')
                actual_fin = hoy.strftime('%Y-%m-%d')
                anterior_ini = (inicio_semana - timedelta(days=7)).strftime('%Y-%m-%d')
                anterior_fin = (inicio_semana - timedelta(days=1)).strftime('%Y-%m-%d')
                periodo_actual = "Esta semana"
                periodo_anterior = "Semana pasada"
            elif tipo == 'mes':
                actual_ini = hoy.replace(day=1).strftime('%Y-%m-%d')
                actual_fin = hoy.strftime('%Y-%m-%d')
                primer_mes_ant = hoy.replace(day=1) - timedelta(days=1)
                anterior_ini = primer_mes_ant.replace(day=1).strftime('%Y-%m-%d')
                anterior_fin = primer_mes_ant.strftime('%Y-%m-%d')
                periodo_actual = "Este mes"
                periodo_anterior = "Mes pasado"
            else:
                return {'error': f'Tipo no soportado: {tipo}'}
            
            # Obtener datos
            ventas_actual = self.conector.ventas_periodo(actual_ini, actual_fin)
            ventas_anterior = self.conector.ventas_periodo(anterior_ini, anterior_fin)
            
            total_actual = ventas_actual['amount_total'].sum() if not ventas_actual.empty else 0
            total_anterior = ventas_anterior['amount_total'].sum() if not ventas_anterior.empty else 0
            
            # Calcular variación
            if total_anterior > 0:
                variacion = ((total_actual - total_anterior) / total_anterior) * 100
            else:
                variacion = 100 if total_actual > 0 else 0
            
            return {
                'tipo': tipo,
                'periodo_actual': {
                    'nombre': periodo_actual,
                    'inicio': actual_ini,
                    'fin': actual_fin,
                    'total': round(total_actual, 2),
                    'ordenes': len(ventas_actual)
                },
                'periodo_anterior': {
                    'nombre': periodo_anterior,
                    'inicio': anterior_ini,
                    'fin': anterior_fin,
                    'total': round(total_anterior, 2),
                    'ordenes': len(ventas_anterior)
                },
                'variacion_porcentaje': round(variacion, 2),
                'variacion_absoluta': round(total_actual - total_anterior, 2),
                'tendencia': 'alza' if variacion > 5 else 'baja' if variacion < -5 else 'estable',
                'insights': [
                    f"{periodo_actual}: ${total_actual:,.2f} ({len(ventas_actual)} órdenes)",
                    f"{periodo_anterior}: ${total_anterior:,.2f} ({len(ventas_anterior)} órdenes)",
                    f"{'🟢' if variacion > 0 else '🔴'} Variación: {variacion:+.1f}%",
                    f"💰Diferencia: ${total_actual - total_anterior:+,.2f}"
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ========================================================
    # SCORE DE SALUD DEL NEGOCIO
    # ========================================================
    
    def score_salud_negocio(self) -> Dict:
        """Calcula un score de salud del negocio."""
        if not self.conector:
            return {'error': 'Sin conexión'}
        
        try:
            scores = {}
            
            # 1. Score de ventas (tendencia)
            pred_ventas = self.predecir_ventas(7)
            if pred_ventas.tipo != 'error':
                if pred_ventas.tendencia == 'alza':
                    scores['ventas'] = 90
                elif pred_ventas.tendencia == 'estable':
                    scores['ventas'] = 70
                else:
                    scores['ventas'] = 50
            else:
                scores['ventas'] = 60
            
            # 2. Score de inventario
            pred_inv = self.predecir_agotamiento()
            if 'resumen' in pred_inv:
                criticos = pred_inv['resumen'].get('criticos', 0)
                total = pred_inv['resumen'].get('total_productos', 1)
                ratio = criticos / total if total > 0 else 0
                scores['inventario'] = max(40, 100 - (ratio * 200))
            else:
                scores['inventario'] = 70
            
            # 3. Score de flujo de caja
            flujo = self.predecir_flujo_caja(30)
            if 'flujo_neto' in flujo:
                if flujo['estado'] == 'POSITIVO':
                    scores['flujo_caja'] = 85
                else:
                    scores['flujo_caja'] = 50
            else:
                scores['flujo_caja'] = 65
            
            # 4. Score de cartera (CXC)
            cxc = flujo.get('cxc', {})
            total_cxc = cxc.get('total', 0)
            if total_cxc > 0:
                ratio_cobro = cxc.get('por_cobrar_pronto', 0) / total_cxc
                scores['cartera'] = min(100, ratio_cobro * 150)
            else:
                scores['cartera'] = 100
            
            # Score general
            score_general = sum(scores.values()) / len(scores)
            
            # Determinar estado
            if score_general >= 80:
                estado = 'EXCELENTE'
                emoji = '🟢'
            elif score_general >= 60:
                estado = 'BUENO'
                emoji = '🟡'
            elif score_general >= 40:
                estado = 'REGULAR'
                emoji = '🟠'
            else:
                estado = 'CRÍTICO'
                emoji = '🔴'
            
            return {
                'score_general': round(score_general, 1),
                'estado': estado,
                'emoji': emoji,
                'scores': {
                    'Ventas': round(scores['ventas'], 1),
                    'Inventario': round(scores['inventario'], 1),
                    'Flujo de Caja': round(scores['flujo_caja'], 1),
                    'Cartera': round(scores['cartera'], 1)
                },
                'insights': [
                    f"{emoji} Score general: {score_general:.0f}/100 ({estado})",
                    f"Ventas: {scores['ventas']:.0f}/100",
                    f"Inventario: {scores['inventario']:.0f}/100",
                    f"Flujo de caja: {scores['flujo_caja']:.0f}/100",
                    f"Cartera: {scores['cartera']:.0f}/100"
                ],
                'recomendaciones': self._recomendaciones_salud(scores)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _recomendaciones_salud(self, scores: Dict) -> List[str]:
        """Genera recomendaciones basadas en scores."""
        recs = []
        
        if scores.get('ventas', 100) < 60:
            recs.append("Implementa promociones para impulsar ventas")
        
        if scores.get('inventario', 100) < 60:
            recs.append("Revisa productos críticos y genera órdenes de compra")
        
        if scores.get('flujo_caja', 100) < 60:
            recs.append("Optimiza cobranza y negocia plazos con proveedores")
        
        if scores.get('cartera', 100) < 60:
            recs.append("Intensifica gestión de cobranza de cartera vencida")
        
        if not recs:
            recs.append("¡El negocio está saludable! Mantén el buen trabajo")
        
        return recs
    
    # ========================================================
    # UTILIDADES
    # ========================================================
    
    def _error_prediccion(self, tipo: str, msg: str = "Sin conexión a Odoo") -> Prediccion:
        """Genera una predicción de error."""
        return Prediccion(
            tipo='error',
            valor_actual=0,
            valor_predicho=0,
            tendencia='desconocido',
            confianza=0,
            periodo='N/A',
            insights=[f"No se pudo generar predicción de {tipo}: {msg}"],
            datos_historicos=[],
            alertas=[f"Error en predicción de {tipo}"]
        )
    
    def formatear_prediccion_md(self, pred: Prediccion) -> str:
        """Formatea una predicción como Markdown."""
        if pred.tipo == 'error':
            return f"## Error en Predicción\n\n{pred.insights[0]}"
        
        emoji_tend = '📈' if pred.tendencia == 'alza' else '📉' if pred.tendencia == 'baja' else '➡️'
        
        md = f"""## Predicción de {pred.tipo.title()}

### Resumen
| Métrica | Valor |
|---------|-------|
|  Período | **{pred.periodo}** |
|  Valor actual proyectado | **${pred.valor_actual:,.2f}** |
|  Valor predicho | **${pred.valor_predicho:,.2f}** |
|  Tendencia | **{pred.tendencia.upper()}** |
|  Confianza | **{pred.confianza:.0f}%** |

### 💡 Insights
"""
        for insight in pred.insights:
            md += f"\n{insight}"
        
        if pred.alertas:
            md += "\n\n### Alertas\n"
            for alerta in pred.alertas:
                md += f"\n{alerta}"
        
        return md


# Instancia global
motor_prediccion = MotorPrediccion()


if __name__ == "__main__":
    print("Motor de Predicción - ANDROMEDA")
    print("=" * 50)
