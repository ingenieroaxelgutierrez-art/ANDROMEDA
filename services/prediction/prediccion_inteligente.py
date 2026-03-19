# ============================================================
# SISTEMA DE PREDICCIÓN INTELIGENTE - ANDROMEDA v5.0
# ============================================================
# Predicciones claras con:
# - Variables clave consideradas
# - Tendencia detectada
# - Nivel de confianza
# - Alertas accionables
# - Recomendaciones de reposición
# - Score de clientes morosos
# - Explicación textual del análisis
# ============================================================

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

from app.logging_config import get_logger
logger = get_logger("services.prediction.prediccion_inteligente")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class NivelConfianza(Enum):
    """Niveles de confianza."""
    MUY_ALTA = "MUY ALTA"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"
    MUY_BAJA = "MUY BAJA"


class TipoTendencia(Enum):
    """Tipos de tendencia."""
    ALZA_FUERTE = "ALZA FUERTE"
    ALZA_MODERADA = "ALZA MODERADA"
    ESTABLE = "ESTABLE"
    BAJA_MODERADA = "BAJA MODERADA"
    BAJA_FUERTE = "BAJA FUERTE"


class NivelAlerta(Enum):
    """Niveles de alerta."""
    CRITICO = "CRÍTICO"
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"
    INFO = "INFO"


@dataclass
class VariableClave:
    """Variable considerada en el análisis."""
    nombre: str
    valor: Any
    peso: float  # 0-100 indica qué tan importante es
    impacto: str  # 'positivo', 'negativo', 'neutro'
    descripcion: str


@dataclass
class AlertaInteligente:
    """Alerta accionable."""
    titulo: str
    descripcion: str
    nivel: NivelAlerta
    accion_recomendada: str
    impacto_estimado: str
    prioridad: int  # 1 = máxima, 5 = mínima


@dataclass
class RecomendacionReposicion:
    """Recomendación de reposición de inventario."""
    producto_id: int
    producto_nombre: str
    stock_actual: float
    stock_minimo: float
    stock_recomendado: float
    cantidad_reponer: float
    urgencia: NivelAlerta
    costo_estimado: float
    proveedor_sugerido: str
    dias_sin_stock: int


@dataclass
class ScoreClienteMoroso:
    """Score de morosidad de cliente."""
    cliente_id: int
    cliente_nombre: str
    score_morosidad: float  # 0-100 (100 = muy moroso)
    deuda_total: float
    deuda_vencida: float
    dias_promedio_pago: float
    facturas_pendientes: int
    historial_pagos: str  # 'bueno', 'regular', 'malo'
    riesgo: NivelAlerta
    accion_recomendada: str


@dataclass
class PrediccionInteligente:
    """Resultado de predicción inteligente con explicación."""
    # Identificación
    tipo: str
    titulo: str
    fecha_generacion: datetime
    
    # Métricas principales
    valor_actual: float
    valor_predicho: float
    variacion_porcentaje: float
    
    # Tendencia
    tendencia: TipoTendencia
    direccion: str  # 'arriba', 'abajo', 'lateral'
    magnitud: float  # % de cambio
    
    # Confianza
    nivel_confianza: NivelConfianza
    confianza_numerica: float  # 0-100
    factores_confianza: List[str]
    
    # Variables clave
    variables_clave: List[VariableClave]
    
    # Período
    periodo_analizado: str
    periodo_prediccion: str
    
    # Insights y explicación
    resumen_ejecutivo: str
    explicacion_textual: str
    insights: List[str]
    
    # Alertas
    alertas: List[AlertaInteligente]
    
    # Datos adicionales
    datos_historicos: List[Dict] = field(default_factory=list)
    datos_proyectados: List[Dict] = field(default_factory=list)
    
    # Metadatos
    modelo_usado: str = "Regresión Linear + Análisis Estadístico"
    version: str = "ANDROMEDA v5.0"


class SistemaPrediccionInteligente:
    """Sistema avanzado de predicción con explicación."""
    
    def __init__(self):
        self.conector = None
        self.cache = {}
    
    def set_conector(self, conector):
        """Configura el conector de Odoo."""
        self.conector = conector
    
    # ============================================================
    # PREDICCIÓN DE VENTAS COMPLETA
    # ============================================================
    
    def predecir_ventas_inteligente(self, dias_futuro: int = 7) -> PrediccionInteligente:
        """Genera predicción inteligente de ventas con explicación completa."""
        if not self.conector:
            return self._error_prediccion("ventas", "Sin conexión a Odoo")
        
        try:
            # 1. Obtener datos históricos
            historico = self._obtener_historico_ventas(90)
            
            if len(historico) < 7:
                return self._error_prediccion("ventas", "Datos históricos insuficientes (mínimo 7 días)")
            
            df = pd.DataFrame(historico)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df = df.sort_values('fecha').reset_index(drop=True)
            
            # 2. Calcular estadísticas base
            promedio = df['total'].mean()
            std = df['total'].std()
            mediana = df['total'].median()
            ultimo_valor = df['total'].iloc[-1]
            
            # 3. Calcular tendencia con regresión
            x = np.arange(len(df))
            y = df['total'].values
            n = len(x)
            
            slope = 0
            intercept = promedio
            r_squared = 0
            
            if n > 1:
                # Regresión lineal
                slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2 + 0.0001)
                intercept = (np.sum(y) - slope * np.sum(x)) / n
                
                # R-cuadrado
                y_pred = slope * x + intercept
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - promedio) ** 2)
                r_squared = 1 - (ss_res / (ss_tot + 0.0001))
            
            # 4. Determinar tendencia
            tendencia, direccion, magnitud = self._clasificar_tendencia(slope, promedio, std)
            
            # 5. Calcular predicciones
            predicciones = []
            for i in range(dias_futuro):
                pred = max(0, slope * (len(df) + i) + intercept)
                fecha_pred = datetime.now() + timedelta(days=i+1)
                predicciones.append({
                    'fecha': fecha_pred.strftime('%Y-%m-%d'),
                    'prediccion': round(pred, 2),
                    'limite_inferior': round(pred * 0.85, 2),
                    'limite_superior': round(pred * 1.15, 2)
                })
            
            valor_predicho = sum(p['prediccion'] for p in predicciones)
            valor_actual_periodo = df['total'].tail(dias_futuro).sum()
            variacion = ((valor_predicho - valor_actual_periodo) / (valor_actual_periodo + 0.01)) * 100
            
            # 6. Calcular confianza
            confianza, nivel_conf, factores = self._calcular_confianza(df, r_squared, std, promedio)
            
            # 7. Identificar variables clave
            variables = self._identificar_variables_ventas(df, slope, promedio, std)
            
            # 8. Generar alertas
            alertas = self._generar_alertas_ventas(df, predicciones, tendencia)
            
            # 9. Generar explicación textual
            explicacion = self._generar_explicacion_ventas(
                df, tendencia, variables, confianza, predicciones, valor_predicho
            )
            
            # 10. Resumen ejecutivo
            resumen = self._generar_resumen_ejecutivo_ventas(
                tendencia, valor_predicho, variacion, confianza, len(alertas)
            )
            
            # 11. Generar insights
            insights = self._generar_insights_ventas(df, predicciones, tendencia)
            
            return PrediccionInteligente(
                tipo='ventas',
                titulo='PREDICCIÓN DE VENTAS',
                fecha_generacion=datetime.now(),
                valor_actual=round(valor_actual_periodo, 2),
                valor_predicho=round(valor_predicho, 2),
                variacion_porcentaje=round(variacion, 1),
                tendencia=tendencia,
                direccion=direccion,
                magnitud=round(magnitud, 1),
                nivel_confianza=nivel_conf,
                confianza_numerica=round(confianza, 1),
                factores_confianza=factores,
                variables_clave=variables,
                periodo_analizado=f"Últimos {len(df)} días",
                periodo_prediccion=f"Próximos {dias_futuro} días",
                resumen_ejecutivo=resumen,
                explicacion_textual=explicacion,
                insights=insights,
                alertas=alertas,
                datos_historicos=historico[-30:],
                datos_proyectados=predicciones
            )
            
        except Exception as e:
            return self._error_prediccion("ventas", str(e))
    
    # ============================================================
    # PREDICCIÓN DE INVENTARIO CON RECOMENDACIONES
    # ============================================================
    
    def predecir_inventario_inteligente(self, top: int = 20) -> Dict:
        """Predicción de inventario con recomendaciones de reposición."""
        if not self.conector:
            return {'error': 'Sin conexión'}
        
        try:
            # Obtener stock
            stock = self.conector.stock_disponible()
            if stock.empty:
                return {'error': 'Sin datos de inventario'}
            
            # Obtener ventas últimos 30 días
            hace_30 = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            hoy = datetime.now().strftime('%Y-%m-%d')
            
            try:
                lineas = self.conector.buscar(
                    'sale.order.line',
                    filtro=[
                        ('order_id.date_order', '>=', hace_30),
                        ('order_id.state', 'in', ['sale', 'done'])
                    ],
                    campos=['product_id', 'product_uom_qty', 'price_subtotal'],
                    limite=5000
                )
            except Exception:
                lineas = pd.DataFrame()
            
            recomendaciones = []
            alertas_stock = []
            productos_analizados = []
            
            for _, row in stock.iterrows():
                # Extraer ID del producto de forma segura
                prod_id_raw = row.get('product_id', 0)
                if isinstance(prod_id_raw, (list, tuple)):
                    prod_id = prod_id_raw[0] if len(prod_id_raw) > 0 else 0
                    prod_name = str(prod_id_raw[1])[:50] if len(prod_id_raw) > 1 else f"Producto {prod_id}"
                else:
                    prod_id = prod_id_raw
                    prod_name = f"Producto {prod_id}"
                
                qty = float(row.get('quantity', 0))
                
                # Calcular velocidad de venta
                velocidad = 0
                ingresos_producto = 0
                if not lineas.empty:
                    # Filtrar de forma segura
                    def extraer_id(x):
                        if isinstance(x, (list, tuple)):
                            return x[0] if len(x) > 0 else 0
                        return x
                    
                    prod_ventas = lineas[lineas['product_id'].apply(extraer_id) == prod_id]
                    if not prod_ventas.empty:
                        total_vendido = prod_ventas['product_uom_qty'].sum()
                        velocidad = total_vendido / 30
                        ingresos_producto = prod_ventas['price_subtotal'].sum()
                
                # Calcular días hasta agotamiento
                dias_stock = qty / velocidad if velocidad > 0 else 999
                
                # Clasificar urgencia
                if qty <= 0:
                    urgencia = NivelAlerta.CRITICO
                elif dias_stock < 7:
                    urgencia = NivelAlerta.CRITICO
                elif dias_stock < 14:
                    urgencia = NivelAlerta.ALTO
                elif dias_stock < 30:
                    urgencia = NivelAlerta.MEDIO
                else:
                    urgencia = NivelAlerta.BAJO
                
                # Calcular reposición recomendada (stock para 45 días)
                stock_recomendado = velocidad * 45
                cantidad_reponer = max(0, stock_recomendado - qty)
                
                producto_info = {
                    'producto_id': prod_id,
                    'producto': prod_name,
                    'stock_actual': qty,
                    'velocidad_diaria': round(velocidad, 2),
                    'dias_stock': round(dias_stock, 1) if dias_stock < 999 else 'N/A',
                    'urgencia': urgencia.value,
                    'ingresos_mensual': round(ingresos_producto, 2)
                }
                productos_analizados.append(producto_info)
                
                # Generar recomendación si necesita reposición
                if urgencia in [NivelAlerta.CRITICO, NivelAlerta.ALTO, NivelAlerta.MEDIO]:
                    rec = RecomendacionReposicion(
                        producto_id=prod_id,
                        producto_nombre=prod_name,
                        stock_actual=qty,
                        stock_minimo=velocidad * 7,
                        stock_recomendado=stock_recomendado,
                        cantidad_reponer=cantidad_reponer,
                        urgencia=urgencia,
                        costo_estimado=0,  # Se podría calcular con standard_price
                        proveedor_sugerido="Consultar con compras",
                        dias_sin_stock=max(0, int(-dias_stock)) if dias_stock < 0 else 0
                    )
                    recomendaciones.append(rec)
                
                # Generar alerta
                if urgencia in [NivelAlerta.CRITICO, NivelAlerta.ALTO]:
                    alerta = AlertaInteligente(
                        titulo=f"Stock Crítico: {prod_name[:30]}",
                        descripcion=f"Solo {qty:.0f} unidades. A velocidad actual, se agota en {dias_stock:.0f} días",
                        nivel=urgencia,
                        accion_recomendada=f"Ordenar {cantidad_reponer:.0f} unidades inmediatamente",
                        impacto_estimado=f"Pérdida potencial: ${ingresos_producto:.2f}/mes",
                        prioridad=1 if urgencia == NivelAlerta.CRITICO else 2
                    )
                    alertas_stock.append(alerta)
            
            # Ordenar por urgencia
            productos_analizados.sort(key=lambda x: (
                0 if x['urgencia'] == 'CRÍTICO' else 
                1 if x['urgencia'] == 'ALTO' else 
                2 if x['urgencia'] == 'MEDIO' else 3
            ))
            
            # Estadísticas
            criticos = len([p for p in productos_analizados if p['urgencia'] == 'CRÍTICO'])
            altos = len([p for p in productos_analizados if p['urgencia'] == 'ALTO'])
            
            # Variables clave del análisis
            variables = [
                VariableClave("Productos Analizados", len(productos_analizados), 100, 'neutro', "Total de SKUs en inventario"),
                VariableClave("Productos Críticos", criticos, 90, 'negativo' if criticos > 0 else 'positivo', "Productos con < 7 días de stock"),
                VariableClave("Velocidad Promedio", round(np.mean([p['velocidad_diaria'] for p in productos_analizados]), 2), 70, 'neutro', "Unidades vendidas/día"),
            ]
            
            # Explicación textual
            explicacion = self._generar_explicacion_inventario(
                productos_analizados, criticos, altos, recomendaciones
            )
            
            return {
                'productos': productos_analizados[:top],
                'recomendaciones_reposicion': [
                    {
                        'producto': r.producto_nombre,
                        'stock_actual': r.stock_actual,
                        'cantidad_reponer': r.cantidad_reponer,
                        'urgencia': r.urgencia.value,
                        'stock_recomendado': r.stock_recomendado
                    } for r in recomendaciones[:top]
                ],
                'alertas': [
                    {
                        'titulo': a.titulo,
                        'descripcion': a.descripcion,
                        'nivel': a.nivel.value,
                        'accion': a.accion_recomendada
                    } for a in alertas_stock[:10]
                ],
                'variables_clave': [
                    {'nombre': v.nombre, 'valor': v.valor, 'impacto': v.impacto, 'descripcion': v.descripcion}
                    for v in variables
                ],
                'estadisticas': {
                    'total_productos': len(productos_analizados),
                    'criticos': criticos,
                    'altos': altos,
                    'sin_movimiento': len([p for p in productos_analizados if p['velocidad_diaria'] == 0])
                },
                'explicacion_textual': explicacion,
                'confianza': 95 if len(productos_analizados) > 50 else 85
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # SCORE DE CLIENTES MOROSOS
    # ============================================================
    
    def calcular_score_morosos(self, top: int = 20) -> Dict:
        """Calcula score de morosidad de clientes."""
        if not self.conector:
            return {'error': 'Sin conexión'}
        
        try:
            # Obtener facturas pendientes
            facturas = self.conector.buscar(
                'account.move',
                filtro=[
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', '!=', 'paid')
                ],
                campos=['name', 'partner_id', 'amount_total', 'amount_residual', 
                       'invoice_date', 'invoice_date_due'],
                limite=1000
            )
            
            if facturas.empty:
                return {
                    'clientes_morosos': [],
                    'estadisticas': {'total_morosos': 0, 'deuda_total': 0},
                    'explicacion_textual': "No hay clientes con facturas pendientes. Excelente gestión de cobranza.",
                    'confianza': 100
                }
            
            hoy = datetime.now().date()
            clientes_scores = {}
            
            for _, fac in facturas.iterrows():
                # Extraer cliente de forma segura
                partner_raw = fac.get('partner_id', [0, 'Desconocido'])
                if isinstance(partner_raw, (list, tuple)):
                    cliente_id = partner_raw[0] if len(partner_raw) > 0 else 0
                    cliente_nombre = str(partner_raw[1])[:40] if len(partner_raw) > 1 else 'Desconocido'
                else:
                    cliente_id = partner_raw
                    cliente_nombre = 'Desconocido'
                
                residual = float(fac.get('amount_residual', 0))
                total = float(fac.get('amount_total', 0))
                
                # Calcular días vencidos
                fecha_vence = fac.get('invoice_date_due')
                if isinstance(fecha_vence, str):
                    try:
                        fecha_vence = datetime.strptime(fecha_vence, '%Y-%m-%d').date()
                    except Exception:
                        fecha_vence = hoy
                elif not fecha_vence:
                    fecha_vence = hoy
                
                dias_vencido = (hoy - fecha_vence).days if isinstance(fecha_vence, type(hoy)) else 0
                
                # Acumular por cliente
                if cliente_id not in clientes_scores:
                    clientes_scores[cliente_id] = {
                        'cliente_id': cliente_id,
                        'cliente_nombre': cliente_nombre,
                        'deuda_total': 0,
                        'deuda_vencida': 0,
                        'facturas_pendientes': 0,
                        'max_dias_vencido': 0,
                        'dias_vencidos_lista': []
                    }
                
                clientes_scores[cliente_id]['deuda_total'] += residual
                clientes_scores[cliente_id]['facturas_pendientes'] += 1
                
                if dias_vencido > 0:
                    clientes_scores[cliente_id]['deuda_vencida'] += residual
                    clientes_scores[cliente_id]['dias_vencidos_lista'].append(dias_vencido)
                    clientes_scores[cliente_id]['max_dias_vencido'] = max(
                        clientes_scores[cliente_id]['max_dias_vencido'], 
                        dias_vencido
                    )
            
            # Calcular score de morosidad
            resultados = []
            for cliente_id, datos in clientes_scores.items():
                # Score basado en múltiples factores
                score = 0
                
                # Factor 1: % de deuda vencida (máx 40 puntos)
                if datos['deuda_total'] > 0:
                    pct_vencida = datos['deuda_vencida'] / datos['deuda_total']
                    score += pct_vencida * 40
                
                # Factor 2: Días máximos vencidos (máx 30 puntos)
                if datos['max_dias_vencido'] > 0:
                    score += min(30, datos['max_dias_vencido'] / 3)
                
                # Factor 3: Número de facturas pendientes (máx 15 puntos)
                score += min(15, datos['facturas_pendientes'] * 3)
                
                # Factor 4: Monto total (máx 15 puntos)
                if datos['deuda_total'] > 50000:
                    score += 15
                elif datos['deuda_total'] > 20000:
                    score += 10
                elif datos['deuda_total'] > 5000:
                    score += 5
                
                score = min(100, score)
                
                # Determinar riesgo
                if score >= 75:
                    riesgo = NivelAlerta.CRITICO
                    historial = 'malo'
                    accion = "Suspender crédito y contactar inmediatamente"
                elif score >= 50:
                    riesgo = NivelAlerta.ALTO
                    historial = 'regular'
                    accion = "Llamada de cobranza urgente"
                elif score >= 25:
                    riesgo = NivelAlerta.MEDIO
                    historial = 'regular'
                    accion = "Enviar recordatorio de pago"
                else:
                    riesgo = NivelAlerta.BAJO
                    historial = 'bueno'
                    accion = "Monitoreo regular"
                
                # Días promedio
                dias_prom = np.mean(datos['dias_vencidos_lista']) if datos['dias_vencidos_lista'] else 0
                
                cliente_score = ScoreClienteMoroso(
                    cliente_id=datos['cliente_id'],
                    cliente_nombre=datos['cliente_nombre'],
                    score_morosidad=round(score, 1),
                    deuda_total=datos['deuda_total'],
                    deuda_vencida=datos['deuda_vencida'],
                    dias_promedio_pago=round(dias_prom, 0),
                    facturas_pendientes=datos['facturas_pendientes'],
                    historial_pagos=historial,
                    riesgo=riesgo,
                    accion_recomendada=accion
                )
                resultados.append(cliente_score)
            
            # Ordenar por score (más morosos primero)
            resultados.sort(key=lambda x: x.score_morosidad, reverse=True)
            
            # Estadísticas
            total_deuda = sum(r.deuda_total for r in resultados)
            total_vencida = sum(r.deuda_vencida for r in resultados)
            criticos = len([r for r in resultados if r.riesgo == NivelAlerta.CRITICO])
            altos = len([r for r in resultados if r.riesgo == NivelAlerta.ALTO])
            
            # Explicación textual
            explicacion = f"""## Análisis de Morosidad de Clientes

### Resumen Ejecutivo
Se analizaron **{len(resultados)} clientes** con facturas pendientes por un total de **${total_deuda:,.2f}**.

### Situación de Cartera
-  **Deuda Total:** ${total_deuda:,.2f}
-  **Deuda Vencida:** ${total_vencida:,.2f} ({(total_vencida/total_deuda*100):.1f}%)
-  **Clientes Críticos:** {criticos}
-  **Clientes Alto Riesgo:** {altos}

### Metodología del Score
El score de morosidad (0-100) considera:
- **40%** Porcentaje de deuda vencida
- **30%** Días de mora máximos
- **15%** Número de facturas pendientes
- **15%** Monto total adeudado

### Recomendaciones Inmediatas
{f'1. **URGENTE:** Contactar a los {criticos} clientes críticos' if criticos > 0 else ''}
{f'2. Programar llamadas a los {altos} clientes de alto riesgo' if altos > 0 else ''}
3. Revisar políticas de crédito para nuevos clientes
4. Considerar descuentos por pronto pago
"""
            
            return {
                'clientes_morosos': [
                    {
                        'cliente': r.cliente_nombre,
                        'score': r.score_morosidad,
                        'deuda_total': r.deuda_total,
                        'deuda_vencida': r.deuda_vencida,
                        'dias_promedio': r.dias_promedio_pago,
                        'facturas': r.facturas_pendientes,
                        'riesgo': r.riesgo.value,
                        'accion': r.accion_recomendada
                    } for r in resultados[:top]
                ],
                'estadisticas': {
                    'total_clientes': len(resultados),
                    'criticos': criticos,
                    'altos': altos,
                    'deuda_total': round(total_deuda, 2),
                    'deuda_vencida': round(total_vencida, 2),
                    'pct_vencida': round(total_vencida/total_deuda*100, 1) if total_deuda > 0 else 0
                },
                'explicacion_textual': explicacion,
                'confianza': 95
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # DASHBOARD AUTOMÁTICO
    # ============================================================
    
    def generar_dashboard_automatico(self) -> Dict:
        """Genera un dashboard automático completo."""
        if not self.conector:
            return {'error': 'Sin conexión'}
        
        try:
            resultado = {}
            
            # 1. Predicción de ventas
            pred_ventas = self.predecir_ventas_inteligente(7)
            resultado['ventas'] = {
                'valor_actual': pred_ventas.valor_actual,
                'valor_predicho': pred_ventas.valor_predicho,
                'variacion': pred_ventas.variacion_porcentaje,
                'tendencia': pred_ventas.tendencia.value,
                'confianza': pred_ventas.confianza_numerica,
                'resumen': pred_ventas.resumen_ejecutivo
            }
            
            # 2. Inventario crítico
            pred_inv = self.predecir_inventario_inteligente(10)
            resultado['inventario'] = {
                'productos_criticos': pred_inv.get('estadisticas', {}).get('criticos', 0),
                'productos_altos': pred_inv.get('estadisticas', {}).get('altos', 0),
                'alertas': len(pred_inv.get('alertas', [])),
                'recomendaciones': len(pred_inv.get('recomendaciones_reposicion', [])),
                'confianza': pred_inv.get('confianza', 0)
            }
            
            # 3. Score de morosos
            morosos = self.calcular_score_morosos(5)
            resultado['cartera'] = {
                'clientes_criticos': morosos.get('estadisticas', {}).get('criticos', 0),
                'deuda_total': morosos.get('estadisticas', {}).get('deuda_total', 0),
                'deuda_vencida': morosos.get('estadisticas', {}).get('deuda_vencida', 0),
                'pct_riesgo': morosos.get('estadisticas', {}).get('pct_vencida', 0),
                'top_morosos': morosos.get('clientes_morosos', [])[:3]
            }
            
            # 4. Variables clave globales
            resultado['variables_clave'] = [
                {
                    'nombre': 'Tendencia de Ventas',
                    'valor': pred_ventas.tendencia.value,
                    'impacto': 'positivo' if 'ALZA' in pred_ventas.tendencia.value else 'negativo' if 'BAJA' in pred_ventas.tendencia.value else 'neutro'
                },
                {
                    'nombre': 'Productos Críticos',
                    'valor': pred_inv.get('estadisticas', {}).get('criticos', 0),
                    'impacto': 'negativo' if pred_inv.get('estadisticas', {}).get('criticos', 0) > 5 else 'neutro'
                },
                {
                    'nombre': 'Cartera en Riesgo',
                    'valor': f"${morosos.get('estadisticas', {}).get('deuda_vencida', 0):,.2f}",
                    'impacto': 'negativo' if morosos.get('estadisticas', {}).get('pct_vencida', 0) > 30 else 'neutro'
                }
            ]
            
            # 5. Alertas consolidadas
            alertas = []
            
            # Alertas de ventas
            for a in pred_ventas.alertas[:3]:
                alertas.append({
                    'tipo': 'ventas',
                    'titulo': a.titulo,
                    'nivel': a.nivel.value,
                    'accion': a.accion_recomendada
                })
            
            # Alertas de inventario
            for a in pred_inv.get('alertas', [])[:3]:
                alertas.append({
                    'tipo': 'inventario',
                    'titulo': a['titulo'],
                    'nivel': a['nivel'],
                    'accion': a['accion']
                })
            
            resultado['alertas'] = alertas
            
            # 6. Explicación textual del dashboard
            resultado['explicacion_textual'] = f"""## DASHBOARD INTELIGENTE - ANDROMEDA

### Estado General del Negocio

**Ventas:** {pred_ventas.tendencia.value}
- Valor actual: ${pred_ventas.valor_actual:,.2f}
- Proyección 7 días: ${pred_ventas.valor_predicho:,.2f}
- Variación: {pred_ventas.variacion_porcentaje:+.1f}%

**Inventario:** {'CRÍTICO' if pred_inv.get('estadisticas', {}).get('criticos', 0) > 10 else 'ATENCIÓN' if pred_inv.get('estadisticas', {}).get('criticos', 0) > 0 else 'OK'}
- Productos críticos: {pred_inv.get('estadisticas', {}).get('criticos', 0)}
- Reposiciones urgentes: {len(pred_inv.get('recomendaciones_reposicion', []))}

**Cartera:** {'ALERTA' if morosos.get('estadisticas', {}).get('pct_vencida', 0) > 40 else 'ATENCIÓN' if morosos.get('estadisticas', {}).get('pct_vencida', 0) > 20 else 'SALUDABLE'}
- Deuda vencida: ${morosos.get('estadisticas', {}).get('deuda_vencida', 0):,.2f}
- Clientes en riesgo: {morosos.get('estadisticas', {}).get('criticos', 0) + morosos.get('estadisticas', {}).get('altos', 0)}

### Acciones Recomendadas
1. {pred_ventas.alertas[0].accion_recomendada if pred_ventas.alertas else 'Mantener estrategia actual de ventas'}
2. {pred_inv.get('alertas', [{}])[0].get('accion', 'Monitorear niveles de inventario') if pred_inv.get('alertas') else 'Inventario bajo control'}
3. {morosos.get('clientes_morosos', [{}])[0].get('accion', 'Continuar gestión de cobranza') if morosos.get('clientes_morosos') else 'Cartera saludable'}

---
_Generado por ANDROMEDA v5.0 - {datetime.now().strftime('%d/%m/%Y %H:%M')}_
"""
            
            resultado['confianza_global'] = round(
                (pred_ventas.confianza_numerica + pred_inv.get('confianza', 0) + morosos.get('confianza', 0)) / 3, 1
            )
            
            return resultado
            
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # MÉTODOS AUXILIARES
    # ============================================================
    
    def _obtener_historico_ventas(self, dias: int) -> List[Dict]:
        """Obtiene histórico de ventas por día."""
        historico = []
        hoy = datetime.now()
        
        for i in range(dias, -1, -1):
            fecha = (hoy - timedelta(days=i)).strftime('%Y-%m-%d')
            try:
                ventas = self.conector.ventas_periodo(fecha, fecha)
                total = float(ventas['amount_total'].sum()) if not ventas.empty else 0
                cantidad = len(ventas)
                historico.append({
                    'fecha': fecha,
                    'total': total,
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
    
    def _clasificar_tendencia(self, slope: float, promedio: float, std: float) -> Tuple[TipoTendencia, str, float]:
        """Clasifica la tendencia basada en slope."""
        if promedio == 0:
            return TipoTendencia.ESTABLE, 'lateral', 0
        
        magnitud = (slope / promedio) * 100 * 30  # % mensual
        
        if magnitud > 15:
            return TipoTendencia.ALZA_FUERTE, 'arriba', magnitud
        elif magnitud > 5:
            return TipoTendencia.ALZA_MODERADA, 'arriba', magnitud
        elif magnitud < -15:
            return TipoTendencia.BAJA_FUERTE, 'abajo', magnitud
        elif magnitud < -5:
            return TipoTendencia.BAJA_MODERADA, 'abajo', magnitud
        else:
            return TipoTendencia.ESTABLE, 'lateral', magnitud
    
    def _calcular_confianza(self, df: pd.DataFrame, r_squared: float, std: float, promedio: float) -> Tuple[float, NivelConfianza, List[str]]:
        """Calcula nivel de confianza de la predicción."""
        factores = []
        score = 50  # Base
        
        # Factor 1: Cantidad de datos
        if len(df) >= 90:
            score += 15
            factores.append("Datos suficientes (90+ días)")
        elif len(df) >= 30:
            score += 10
            factores.append("Datos aceptables (30+ días)")
        else:
            score -= 10
            factores.append("Pocos datos históricos")
        
        # Factor 2: R-cuadrado (ajuste del modelo)
        if r_squared > 0.7:
            score += 20
            factores.append("Modelo con buen ajuste")
        elif r_squared > 0.4:
            score += 10
            factores.append("Modelo con ajuste moderado")
        else:
            factores.append("Alta variabilidad en datos")
        
        # Factor 3: Coeficiente de variación
        cv = (std / promedio) * 100 if promedio > 0 else 100
        if cv < 30:
            score += 10
            factores.append("Datos estables")
        elif cv < 60:
            score += 5
            factores.append("Variabilidad moderada")
        else:
            score -= 10
            factores.append("Alta volatilidad")
        
        # Factor 4: Datos recientes
        if len(df) > 7:
            ultimo_valor = df['total'].iloc[-1]
            prom_reciente = df['total'].tail(7).mean()
            if abs(ultimo_valor - prom_reciente) / (prom_reciente + 0.01) < 0.3:
                score += 5
                factores.append("Comportamiento reciente consistente")
        
        score = max(0, min(100, score))
        
        # Clasificar nivel
        if score >= 80:
            nivel = NivelConfianza.MUY_ALTA
        elif score >= 65:
            nivel = NivelConfianza.ALTA
        elif score >= 50:
            nivel = NivelConfianza.MEDIA
        elif score >= 35:
            nivel = NivelConfianza.BAJA
        else:
            nivel = NivelConfianza.MUY_BAJA
        
        return score, nivel, factores
    
    def _identificar_variables_ventas(self, df: pd.DataFrame, slope: float, promedio: float, std: float) -> List[VariableClave]:
        """Identifica variables clave del análisis de ventas."""
        variables = []
        
        # Tendencia
        impacto_tend = 'positivo' if slope > 0 else 'negativo' if slope < 0 else 'neutro'
        variables.append(VariableClave(
            nombre="Pendiente de Tendencia",
            valor=f"${slope:+.2f}/día",
            peso=90,
            impacto=impacto_tend,
            descripcion="Indica cuánto cambian las ventas diariamente en promedio"
        ))
        
        # Promedio
        variables.append(VariableClave(
            nombre="Venta Promedio Diaria",
            valor=f"${promedio:,.2f}",
            peso=85,
            impacto='positivo' if promedio > 5000 else 'neutro',
            descripcion="Promedio de ventas por día en el período analizado"
        ))
        
        # Variabilidad
        cv = (std / promedio) * 100 if promedio > 0 else 0
        variables.append(VariableClave(
            nombre="Coeficiente de Variación",
            valor=f"{cv:.1f}%",
            peso=75,
            impacto='negativo' if cv > 50 else 'neutro',
            descripcion="Mide qué tan predecibles son las ventas (menor es mejor)"
        ))
        
        # Días analizados
        variables.append(VariableClave(
            nombre="Período de Análisis",
            valor=f"{len(df)} días",
            peso=70,
            impacto='positivo' if len(df) >= 60 else 'neutro',
            descripcion="Cantidad de días de historial considerados"
        ))
        
        # Mejor día de la semana
        if len(df) > 7:
            df['dia_semana'] = pd.to_datetime(df['fecha']).dt.dayofweek
            mejor_dia_idx = df.groupby('dia_semana')['total'].mean().idxmax()
            dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            variables.append(VariableClave(
                nombre="Día Más Fuerte",
                valor=dias[mejor_dia_idx],
                peso=60,
                impacto='positivo',
                descripcion="Día de la semana con mayores ventas promedio"
            ))
        
        return variables
    
    def _generar_alertas_ventas(self, df: pd.DataFrame, predicciones: List[Dict], tendencia: TipoTendencia) -> List[AlertaInteligente]:
        """Genera alertas inteligentes de ventas."""
        alertas = []
        
        if len(df) < 3:
            return alertas
        
        promedio = df['total'].mean()
        ultimo = df['total'].iloc[-1]
        pred_promedio = np.mean([p['prediccion'] for p in predicciones])
        
        # Alerta: Caída drástica reciente
        if ultimo < promedio * 0.5:
            alertas.append(AlertaInteligente(
                titulo="Caída Drástica en Ventas",
                descripcion=f"Las ventas del último día (${ultimo:,.2f}) están 50% debajo del promedio (${promedio:,.2f})",
                nivel=NivelAlerta.ALTO,
                accion_recomendada="Investigar causas inmediatamente: revisar inventario, competencia, problemas operativos",
                impacto_estimado=f"Pérdida potencial: ${promedio - ultimo:,.2f}",
                prioridad=1
            ))
        
        # Alerta: Tendencia negativa
        if tendencia in [TipoTendencia.BAJA_FUERTE, TipoTendencia.BAJA_MODERADA]:
            alertas.append(AlertaInteligente(
                titulo="Tendencia Negativa Detectada",
                descripcion=f"Las ventas muestran {tendencia.value}",
                nivel=NivelAlerta.MEDIO,
                accion_recomendada="Implementar estrategias de promoción, revisar precios, analizar competencia",
                impacto_estimado="Reducción proyectada en ingresos",
                prioridad=2
            ))
        
        # Alerta: Proyección baja
        if pred_promedio < promedio * 0.8:
            alertas.append(AlertaInteligente(
                titulo="Proyección por Debajo del Promedio",
                descripcion=f"Se proyectan ventas 20% menores al promedio histórico",
                nivel=NivelAlerta.MEDIO,
                accion_recomendada="Planificar promociones, aumentar esfuerzos de marketing",
                impacto_estimado=f"Reducción estimada: ${(promedio - pred_promedio) * len(predicciones):,.2f}",
                prioridad=2
            ))
        
        return alertas
    
    def _generar_explicacion_ventas(self, df: pd.DataFrame, tendencia: TipoTendencia, 
                                     variables: List[VariableClave], confianza: float,
                                     predicciones: List[Dict], valor_predicho: float) -> str:
        """Genera explicación textual detallada del análisis de ventas."""
        promedio = df['total'].mean()
        
        explicacion = f"""## Explicación del Análisis de Ventas

### ¿Qué analizamos?
Examinamos **{len(df)} días** de historial de ventas para proyectar los **próximos {len(predicciones)} días**.

### ¿Qué encontramos?
La tendencia general es **{tendencia.value}**, lo que significa que las ventas están {
    'creciendo de manera significativa' if 'ALZA FUERTE' in tendencia.value else
    'creciendo de manera moderada' if 'ALZA' in tendencia.value else
    'disminuyendo de manera significativa' if 'BAJA FUERTE' in tendencia.value else
    'disminuyendo moderadamente' if 'BAJA' in tendencia.value else
    'manteniéndose estables'
}.

### Variables Clave Consideradas
"""
        for var in variables[:5]:
            emoji = '✅' if var.impacto == 'positivo' else '⚠️' if var.impacto == 'negativo' else '📊'
            explicacion += f"- {emoji} **{var.nombre}:** {var.valor} - {var.descripcion}\n"
        
        explicacion += f"""
### Proyección
Basado en los datos, proyectamos ventas totales de **${valor_predicho:,.2f}** para los próximos {len(predicciones)} días.
- Promedio histórico diario: ${promedio:,.2f}
- Promedio proyectado diario: ${valor_predicho/len(predicciones):,.2f}

### Nivel de Confianza: {confianza:.0f}%
{'Esta es una proyección con ALTA confiabilidad basada en datos estables.' if confianza >= 70 else
 'La proyección tiene confianza MODERADA. Considere estos valores como guía general.' if confianza >= 50 else
 'La confianza es BAJA debido a alta variabilidad en los datos. Use con precaución.'}

### Metodología
- Modelo: Regresión lineal con análisis estadístico
- Datos: Ventas confirmadas de Odoo
- Período: {len(df)} días de historial

---
_Análisis generado por ANDROMEDA v5.0_
"""
        return explicacion
    
    def _generar_resumen_ejecutivo_ventas(self, tendencia: TipoTendencia, valor_predicho: float, 
                                           variacion: float, confianza: float, num_alertas: int) -> str:
        """Genera resumen ejecutivo de una línea."""
        estado = '📈' if 'ALZA' in tendencia.value else '📉' if 'BAJA' in tendencia.value else '➡️'
        alerta_texto = f" {num_alertas} alertas" if num_alertas > 0 else ""
        
        return f"{estado} Proyección: ${valor_predicho:,.2f} ({variacion:+.1f}%) | Confianza: {confianza:.0f}%{alerta_texto}"
    
    def _generar_insights_ventas(self, df: pd.DataFrame, predicciones: List[Dict], tendencia: TipoTendencia) -> List[str]:
        """Genera insights sobre ventas."""
        insights = []
        
        # Tendencia
        insights.append(f"Tendencia detectada: {tendencia.value}")
        
        # Mejor día reciente
        if len(df) > 0:
            mejor_idx = df['total'].idxmax()
            mejor_dia = df.loc[mejor_idx]
            insights.append(f"Mejor día: {mejor_dia['fecha']} con ${mejor_dia['total']:,.2f}")
        
        # Promedio
        promedio = df['total'].mean()
        insights.append(f"Promedio diario: ${promedio:,.2f}")
        
        # Proyección
        total_pred = sum(p['prediccion'] for p in predicciones)
        insights.append(f"Proyección {len(predicciones)} días: ${total_pred:,.2f}")
        
        # Día de la semana
        if len(df) > 7:
            df['dia_semana'] = pd.to_datetime(df['fecha']).dt.dayofweek
            dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            mejor_dia_sem = df.groupby('dia_semana')['total'].mean().idxmax()
            insights.append(f"Día más fuerte: {dias[mejor_dia_sem]}")
        
        return insights
    
    def _generar_explicacion_inventario(self, productos: List[Dict], criticos: int, altos: int, 
                                         recomendaciones: List[RecomendacionReposicion]) -> str:
        """Genera explicación textual del análisis de inventario."""
        return f"""## Explicación del Análisis de Inventario

### Resumen
Se analizaron **{len(productos)} productos** en inventario.

### Estado Actual
- **Productos Críticos:** {criticos} (menos de 7 días de stock)
- **Productos en Alerta:** {altos} (7-14 días de stock)
- **Total Analizados:** {len(productos)}

### Metodología
1. Se calculó la velocidad de venta de cada producto (últimos 30 días)
2. Se estimaron los días de stock restante
3. Se identificaron productos que requieren reposición

### Productos con Reposición Urgente
{len(recomendaciones)} productos necesitan reposición inmediata.

### Recomendación
{'**ACCIÓN URGENTE:** Generar órdenes de compra para los ' + str(criticos) + ' productos críticos.' if criticos > 0 else '✅ El inventario está en niveles saludables.'}

---
_Análisis generado por ANDROMEDA v5.0_
"""
    
    def _error_prediccion(self, tipo: str, mensaje: str) -> PrediccionInteligente:
        """Genera una predicción de error."""
        return PrediccionInteligente(
            tipo='error',
            titulo=f'Error en Predicción de {tipo.title()}',
            fecha_generacion=datetime.now(),
            valor_actual=0,
            valor_predicho=0,
            variacion_porcentaje=0,
            tendencia=TipoTendencia.ESTABLE,
            direccion='desconocido',
            magnitud=0,
            nivel_confianza=NivelConfianza.MUY_BAJA,
            confianza_numerica=0,
            factores_confianza=[f"Error: {mensaje}"],
            variables_clave=[],
            periodo_analizado='N/A',
            periodo_prediccion='N/A',
            resumen_ejecutivo=f"Error: {mensaje}",
            explicacion_textual=f"No se pudo generar la predicción de {tipo}. Error: {mensaje}",
            insights=[f" {mensaje}"],
            alertas=[]
        )


# ============================================================
# FORMATEADOR DE PREDICCIONES
# ============================================================

class FormateadorPrediccion:
    """Formatea predicciones a Markdown profesional."""
    
    @staticmethod
    def formatear_prediccion_ventas(pred: PrediccionInteligente) -> str:
        """Formatea predicción de ventas a Markdown."""
        if pred.tipo == 'error':
            return f"## Error\n\n{pred.explicacion_textual}"
        
        emoji_conf = '🟢' if pred.confianza_numerica >= 70 else '🟡' if pred.confianza_numerica >= 50 else '🔴'
        
        md = f"""## {pred.titulo}

### Resumen Ejecutivo
{pred.resumen_ejecutivo}

### Métricas Principales
| Métrica | Valor |
|---------|-------|
| Período Analizado | **{pred.periodo_analizado}** |
| Período Proyección | **{pred.periodo_prediccion}** |
| Valor Actual | **${pred.valor_actual:,.2f}** |
| Valor Proyectado | **${pred.valor_predicho:,.2f}** |
| Variación | **{pred.variacion_porcentaje:+.1f}%** |
| {pred.tendencia.value} Tendencia | **{pred.direccion.upper()}** |
| {emoji_conf} Confianza | **{pred.confianza_numerica:.0f}%** ({pred.nivel_confianza.value}) |

### Variables Clave Consideradas
| Variable | Valor | Impacto |
|----------|-------|---------|
"""
        for var in pred.variables_clave[:5]:
            emoji = '✅' if var.impacto == 'positivo' else '⚠️' if var.impacto == 'negativo' else '📊'
            md += f"| {var.nombre} | {var.valor} | {emoji} {var.impacto.capitalize()} |\n"
        
        md += "\n### Factores de Confianza\n"
        for factor in pred.factores_confianza:
            md += f"- {factor}\n"
        
        md += "\n### Insights\n"
        for insight in pred.insights:
            md += f"- {insight}\n"
        
        if pred.alertas:
            md += "\n### Alertas Accionables\n"
            for alerta in pred.alertas:
                nivel_emoji = '🔴' if alerta.nivel == NivelAlerta.CRITICO else '🟠' if alerta.nivel == NivelAlerta.ALTO else '🟡'
                md += f"""
#### {nivel_emoji} {alerta.titulo}
- **Descripción:** {alerta.descripcion}
- **Acción:** {alerta.accion_recomendada}
- **Impacto:** {alerta.impacto_estimado}
"""
        
        md += f"\n---\n_Generado por ANDROMEDA v5.0 | {pred.fecha_generacion.strftime('%d/%m/%Y %H:%M')}_"
        
        return md
    
    @staticmethod
    def formatear_inventario(datos: Dict) -> str:
        """Formatea predicción de inventario a Markdown."""
        if 'error' in datos:
            return f"## Error\n\n{datos['error']}"
        
        stats = datos.get('estadisticas', {})
        emoji_estado = '🔴' if stats.get('criticos', 0) > 10 else '🟡' if stats.get('criticos', 0) > 0 else '🟢'
        
        md = f"""## PREDICCIÓN DE INVENTARIO

### {emoji_estado} Estado General
| Métrica | Valor |
|---------|-------|
| Total Productos | **{stats.get('total_productos', 0)}** |
| Críticos | **{stats.get('criticos', 0)}** |
| En Alerta | **{stats.get('altos', 0)}** |
| Sin Movimiento | **{stats.get('sin_movimiento', 0)}** |
| Confianza | **{datos.get('confianza', 0):.0f}%** |

### Variables Clave
"""
        for var in datos.get('variables_clave', []):
            emoji = '✅' if var.get('impacto') == 'positivo' else '⚠️' if var.get('impacto') == 'negativo' else '📊'
            md += f"| {var.get('nombre')} | {var.get('valor')} | {emoji} |\n"
        
        # Alertas
        if datos.get('alertas'):
            md += "\n### Alertas de Stock Crítico\n"
            for alerta in datos.get('alertas', [])[:5]:
                nivel_emoji = '🔴' if alerta.get('nivel') == 'CRÍTICO' else '🟠'
                md += f"- {nivel_emoji} **{alerta.get('titulo')}**: {alerta.get('accion')}\n"
        
        # Recomendaciones de reposición
        if datos.get('recomendaciones_reposicion'):
            md += "\n### Recomendaciones de Reposición\n"
            md += "| Producto | Stock | Reponer | Urgencia |\n|----------|-------|---------|----------|\n"
            for rec in datos.get('recomendaciones_reposicion', [])[:10]:
                urgencia_emoji = '🔴' if rec.get('urgencia') == 'CRÍTICO' else '🟠' if rec.get('urgencia') == 'ALTO' else '🟡'
                md += f"| {rec.get('producto', '')[:30]} | {rec.get('stock_actual', 0):.0f} | {rec.get('cantidad_reponer', 0):.0f} | {urgencia_emoji} |\n"
        
        md += f"\n---\n{datos.get('explicacion_textual', '')}"
        
        return md
    
    @staticmethod
    def formatear_morosos(datos: Dict) -> str:
        """Formatea score de morosos a Markdown."""
        if 'error' in datos:
            return f"## Error\n\n{datos['error']}"
        
        stats = datos.get('estadisticas', {})
        
        md = f"""## SCORE DE CLIENTES MOROSOS

### Resumen
| Métrica | Valor |
|---------|-------|
| Total Clientes | **{stats.get('total_clientes', 0)}** |
| Críticos | **{stats.get('criticos', 0)}** |
| Alto Riesgo | **{stats.get('altos', 0)}** |
| Deuda Total | **${stats.get('deuda_total', 0):,.2f}** |
| Deuda Vencida | **${stats.get('deuda_vencida', 0):,.2f}** ({stats.get('pct_vencida', 0):.1f}%) |
| Confianza | **{datos.get('confianza', 0):.0f}%** |

### Top Clientes por Riesgo
| Cliente | Score | Deuda | Días Mora | Riesgo | Acción |
|---------|-------|-------|-----------|--------|--------|
"""
        for cliente in datos.get('clientes_morosos', [])[:10]:
            riesgo_emoji = '🔴' if cliente.get('riesgo') == 'CRÍTICO' else '🟠' if cliente.get('riesgo') == 'ALTO' else '🟡' if cliente.get('riesgo') == 'MEDIO' else '🟢'
            md += f"| {cliente.get('cliente', '')[:25]} | {cliente.get('score', 0):.0f} | ${cliente.get('deuda_total', 0):,.2f} | {cliente.get('dias_promedio', 0):.0f} | {riesgo_emoji} | {cliente.get('accion', '')[:30]} |\n"
        
        md += f"\n---\n{datos.get('explicacion_textual', '')}"
        
        return md
    
    @staticmethod
    def formatear_dashboard(datos: Dict) -> str:
        """Formatea dashboard automático a Markdown."""
        if 'error' in datos:
            return f"## Error\n\n{datos['error']}"
        
        return datos.get('explicacion_textual', 'Dashboard generado')


# Instancia global
prediccion_inteligente = SistemaPrediccionInteligente()
formateador_prediccion = FormateadorPrediccion()


if __name__ == "__main__":
    print("Sistema de Predicción Inteligente - ANDROMEDA")
    print("=" * 60)
