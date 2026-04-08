# ============================================================
# MOTOR ML - MACHINE LEARNING PARA ANDROMEDA
# ============================================================
# Sistema de aprendizaje automático práctico con:
# - Predicciones con Random Forest
# - Series temporales
# - Segmentación automática
# - Gráficos interactivos con Plotly
# ============================================================

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Librerías de datos
import pandas as pd
import numpy as np

# Machine Learning
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Gráficos
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

from app.logging_config import get_logger
logger = get_logger("services.prediction.motor_ml")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TipoGrafico(Enum):
    """Tipos de gráficos disponibles."""
    LINEA = "linea"
    BARRAS = "barras"
    PASTEL = "pastel"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    FUNNEL = "funnel"
    GAUGE = "gauge"


@dataclass
class PrediccionML:
    """Resultado de una predicción ML."""
    tipo: str
    valores_predichos: List[float]
    fechas_predichas: List[str]
    confianza: float
    intervalo_inferior: List[float]
    intervalo_superior: List[float]
    metricas: Dict[str, float]
    grafico: Optional[Figure] = None
    insights: List[str] = field(default_factory=list)


@dataclass
class SegmentacionML:
    """Resultado de segmentación."""
    tipo: str
    num_clusters: int
    segmentos: List[Dict[str, Any]]
    grafico: Optional[Figure] = None
    caracteristicas: Dict[str, Any] = field(default_factory=dict)


class MotorML:
    """Motor de Machine Learning para análisis empresarial."""
    
    def __init__(self):
        self.conector = None
        self.modelos_entrenados = {}
        self.scalers = {}
        self.encoders = {}
        
        # Paleta de colores profesionales (más diferenciados)
        self.colores = [
            '#2E86DE',  # Azul corporativo
            '#EE5A6F',  # Rojo coral
            '#10AC84',  # Verde esmeralda
            '#F79F1F',  # Naranja
            '#5F27CD',  # Púrpura
            '#00D2D3',  # Cyan
            '#C23616',  # Rojo oscuro
            '#0097E6'   # Azul cielo
        ]
        
        print("Motor ML inicializado")
    
    def set_conector(self, conector):
        """Configura el conector de Odoo."""
        self.conector = conector
    
    # ============================================================
    # PREDICCIONES
    # ============================================================
    
    def predecir_ventas_ml(self, dias_prediccion: int = 30) -> PrediccionML:
        """Predice ventas futuras usando Random Forest."""
        try:
            # Obtener datos históricos
            fecha_inicio = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            df = self.conector.ventas_periodo(fecha_inicio, None)
            
            if df.empty or len(df) < 30:
                return PrediccionML(
                    tipo='ventas',
                    valores_predichos=[],
                    fechas_predichas=[],
                    confianza=0,
                    intervalo_inferior=[],
                    intervalo_superior=[],
                    metricas={'error': 'Datos insuficientes'},
                    insights=['Se necesitan al menos 30 días de datos históricos']
                )
            
            # Preparar datos
            df['fecha'] = pd.to_datetime(df['date_order'])
            df_diario = df.groupby(df['fecha'].dt.date).agg({
                'amount_total': 'sum',
                'id': 'count'
            }).reset_index()
            df_diario.columns = ['fecha', 'ventas', 'ordenes']
            df_diario['fecha'] = pd.to_datetime(df_diario['fecha'])
            df_diario = df_diario.sort_values('fecha')
            
            # Features temporales
            df_diario['dia_semana'] = df_diario['fecha'].dt.dayofweek
            df_diario['dia_mes'] = df_diario['fecha'].dt.day
            df_diario['mes'] = df_diario['fecha'].dt.month
            df_diario['semana_año'] = df_diario['fecha'].dt.isocalendar().week
            df_diario['es_fin_semana'] = (df_diario['dia_semana'] >= 5).astype(int)
            
            # Media móvil como feature
            df_diario['media_7d'] = df_diario['ventas'].rolling(7, min_periods=1).mean()
            df_diario['media_30d'] = df_diario['ventas'].rolling(30, min_periods=1).mean()
            
            # Preparar X, y
            features = ['dia_semana', 'dia_mes', 'mes', 'semana_año', 'es_fin_semana', 'media_7d', 'media_30d']
            X = df_diario[features].fillna(0)
            y = df_diario['ventas']
            
            # Split y entrenar
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            
            modelo = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            modelo.fit(X_train, y_train)
            
            # Evaluar
            y_pred_test = modelo.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred_test)
            r2 = r2_score(y_test, y_pred_test)
            
            # Predicción futura
            ultima_fecha = df_diario['fecha'].max()
            ultima_media_7d = df_diario['media_7d'].iloc[-1]
            ultima_media_30d = df_diario['media_30d'].iloc[-1]
            
            fechas_futuras = []
            predicciones = []
            
            for i in range(1, dias_prediccion + 1):
                fecha_pred = ultima_fecha + timedelta(days=i)
                fechas_futuras.append(fecha_pred.strftime('%Y-%m-%d'))
                
                X_pred = pd.DataFrame([{
                    'dia_semana': fecha_pred.weekday(),
                    'dia_mes': fecha_pred.day,
                    'mes': fecha_pred.month,
                    'semana_año': fecha_pred.isocalendar().week,
                    'es_fin_semana': 1 if fecha_pred.weekday() >= 5 else 0,
                    'media_7d': ultima_media_7d,
                    'media_30d': ultima_media_30d
                }])
                
                pred = modelo.predict(X_pred)[0]
                predicciones.append(max(0, pred))
                
                # Actualizar medias móviles para siguiente predicción
                ultima_media_7d = (ultima_media_7d * 6 + pred) / 7
                ultima_media_30d = (ultima_media_30d * 29 + pred) / 30
            
            # Intervalos de confianza (basados en error histórico)
            error_std = np.std(y_test - y_pred_test)
            intervalo_inf = [max(0, p - 1.96 * error_std) for p in predicciones]
            intervalo_sup = [p + 1.96 * error_std for p in predicciones]
            
            # Generar gráfico
            grafico = self._grafico_prediccion_ventas(
                df_diario, fechas_futuras, predicciones, intervalo_inf, intervalo_sup
            )
            
            # Insights
            insights = self._generar_insights_prediccion(
                predicciones, df_diario['ventas'].mean(), df_diario['ventas'].std()
            )
            
            # Guardar modelo
            self.modelos_entrenados['ventas_rf'] = modelo
            
            return PrediccionML(
                tipo='ventas',
                valores_predichos=predicciones,
                fechas_predichas=fechas_futuras,
                confianza=max(0, min(1, r2)),
                intervalo_inferior=intervalo_inf,
                intervalo_superior=intervalo_sup,
                metricas={
                    'mae': mae,
                    'r2': r2,
                    'total_predicho': sum(predicciones),
                    'promedio_predicho': np.mean(predicciones)
                },
                grafico_json=grafico,
                insights=insights
            )
            
        except Exception as e:
            return PrediccionML(
                tipo='ventas',
                valores_predichos=[],
                fechas_predichas=[],
                confianza=0,
                intervalo_inferior=[],
                intervalo_superior=[],
                metricas={'error': str(e)},
                insights=[f'Error en predicción: {str(e)}']
            )
    
    def _grafico_prediccion_ventas(self, df_historico: pd.DataFrame, 
                                    fechas_pred: List[str], predicciones: List[float],
                                    intervalo_inf: List[float], intervalo_sup: List[float]) -> str:
        """Genera gráfico profesional de predicción con Random Forest."""
        fig = go.Figure()
        
        # Datos históricos (últimos 60 días para no saturar)
        df_reciente = df_historico.tail(60)
        
        fig.add_trace(go.Scatter(
            x=df_reciente['fecha'],
            y=df_reciente['ventas'],
            mode='lines',
            name='📊 Histórico Real',
            line=dict(color=self.colores[0], width=2.5, shape='spline'),
            hovertemplate='<b>Fecha:</b> %{x|%Y-%m-%d}<br><b>Ventas:</b> $%{y:,.2f}<extra></extra>'
        ))
        
        # Predicciones
        fechas_pred_dt = pd.to_datetime(fechas_pred)
        
        fig.add_trace(go.Scatter(
            x=fechas_pred_dt,
            y=predicciones,
            mode='lines+markers',
            name='🤖 Predicción RF',
            line=dict(color=self.colores[1], width=3.5, dash='dash', shape='spline'),
            marker=dict(size=8, symbol='diamond', line=dict(width=2, color='white')),
            hovertemplate='<b>Fecha:</b> %{x|%Y-%m-%d}<br><b>Predicción:</b> $%{y:,.2f}<extra></extra>'
        ))
        
        # Intervalo de confianza
        fig.add_trace(go.Scatter(
            x=list(fechas_pred_dt) + list(fechas_pred_dt)[::-1],
            y=intervalo_sup + intervalo_inf[::-1],
            fill='toself',
            fillcolor='rgba(238, 90, 111, 0.15)',
            line=dict(color='rgba(238, 90, 111, 0.3)', width=1),
            name='📊 Intervalo 95%',
            hoverinfo='skip',
            showlegend=True
        ))
        
        fig.update_layout(
            title=dict(
                text='<b>🌲 Predicción de Ventas con Random Forest</b>',
                font=dict(size=18, family='Arial Black', color='#2C3E50'),
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title='<b>Fecha</b>',
                title_font=dict(size=14),
                gridcolor='rgba(128,128,128,0.2)',
                showline=True,
                linewidth=2,
                linecolor='#2C3E50'
            ),
            yaxis=dict(
                title='<b>Ventas ($)</b>',
                title_font=dict(size=14),
                tickformat='$,.0f',
                gridcolor='rgba(128,128,128,0.2)',
                showline=True,
                linewidth=2,
                linecolor='#2C3E50'
            ),
            template='plotly_white',
            height=550,
            hovermode='x unified',
            hoverlabel=dict(bgcolor='white', font_size=13, font_family='Arial'),
            legend=dict(
                orientation='v',
                yanchor='top',
                y=0.98,
                xanchor='left',
                x=0.01,
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='#2C3E50',
                borderwidth=2,
                font=dict(size=12)
            ),
            plot_bgcolor='rgba(245,245,245,0.5)',
            paper_bgcolor='white',
            font=dict(family='Arial', size=12, color='#2C3E50')
        )
        
        return fig.to_json()
    
    def _generar_insights_prediccion(self, predicciones: List[float], 
                                      media_hist: float, std_hist: float) -> List[str]:
        """Genera insights de la predicción."""
        insights = []
        
        media_pred = np.mean(predicciones)
        total_pred = sum(predicciones)
        
        # Comparar con histórico
        if media_pred > media_hist * 1.1:
            pct = ((media_pred - media_hist) / media_hist) * 100
            insights.append(f"Se espera un incremento del {pct:.1f}% respecto al promedio histórico")
        elif media_pred < media_hist * 0.9:
            pct = ((media_hist - media_pred) / media_hist) * 100
            insights.append(f"Se proyecta una disminución del {pct:.1f}% respecto al promedio histórico")
        else:
            insights.append("Las ventas se mantienen estables según la predicción")
        
        # Mejor/peor día
        max_idx = np.argmax(predicciones)
        min_idx = np.argmin(predicciones)
        insights.append(f"Mejor día proyectado: Día {max_idx + 1} (${predicciones[max_idx]:,.2f})")
        insights.append(f"Día más bajo: Día {min_idx + 1} (${predicciones[min_idx]:,.2f})")
        
        # Total esperado
        insights.append(f"Total esperado en el período: ${total_pred:,.2f}")
        
        return insights
    
    # ============================================================
    # SEGMENTACIÓN
    # ============================================================
    
    def segmentar_clientes(self, n_clusters: int = 4) -> SegmentacionML:
        """Segmenta clientes usando K-Means (RFM Analysis)."""
        try:
            # Obtener ventas de los últimos 12 meses
            fecha_inicio = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            df = self.conector.ventas_periodo(fecha_inicio, None)
            
            if df.empty:
                return SegmentacionML(
                    tipo='clientes',
                    num_clusters=0,
                    segmentos=[],
                    caracteristicas={'error': 'Sin datos de ventas'}
                )
            
            # Extraer cliente
            df['cliente'] = df['partner_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'Sin cliente'
            )
            df['cliente_id'] = df['partner_id'].apply(
                lambda x: x[0] if isinstance(x, (list, tuple)) else 0
            )
            df['fecha'] = pd.to_datetime(df['date_order'])
            
            hoy = datetime.now()
            
            # Calcular RFM
            rfm = df.groupby(['cliente_id', 'cliente']).agg({
                'fecha': lambda x: (hoy - x.max()).days,  # Recency
                'id': 'count',  # Frequency
                'amount_total': 'sum'  # Monetary
            }).reset_index()
            rfm.columns = ['cliente_id', 'cliente', 'recency', 'frequency', 'monetary']
            
            # Filtrar clientes válidos
            rfm = rfm[rfm['monetary'] > 0]
            
            if len(rfm) < n_clusters:
                return SegmentacionML(
                    tipo='clientes',
                    num_clusters=0,
                    segmentos=[],
                    caracteristicas={'error': f'Se necesitan al menos {n_clusters} clientes'}
                )
            
            # Escalar para clustering
            scaler = StandardScaler()
            rfm_scaled = scaler.fit_transform(rfm[['recency', 'frequency', 'monetary']])
            
            # K-Means
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            rfm['segmento'] = kmeans.fit_predict(rfm_scaled)
            
            # Nombrar segmentos
            nombres_segmentos = {
                0: 'VIP / Champions',
                1: 'Leales',
                2: 'En Desarrollo',
                3: 'Dormidos',
            }
            
            if n_clusters > 4:
                for i in range(4, n_clusters):
                    nombres_segmentos[i] = f'Segmento {i + 1}'
            
            # Ordenar por valor monetario promedio
            segmento_valor = rfm.groupby('segmento')['monetary'].mean().sort_values(ascending=False)
            mapeo_orden = {seg: i for i, seg in enumerate(segmento_valor.index)}
            rfm['segmento_ordenado'] = rfm['segmento'].map(mapeo_orden)
            
            # Estadísticas por segmento
            segmentos = []
            for seg_id in sorted(rfm['segmento'].unique()):
                seg_data = rfm[rfm['segmento'] == seg_id]
                orden = mapeo_orden.get(seg_id, seg_id)
                
                segmentos.append({
                    'id': seg_id,
                    'nombre': nombres_segmentos.get(orden, f'Segmento {seg_id}'),
                    'num_clientes': len(seg_data),
                    'recency_promedio': seg_data['recency'].mean(),
                    'frecuencia_promedio': seg_data['frequency'].mean(),
                    'valor_promedio': seg_data['monetary'].mean(),
                    'valor_total': seg_data['monetary'].sum(),
                    'top_clientes': seg_data.nlargest(5, 'monetary')[['cliente', 'monetary']].to_dict('records')
                })
            
            # Generar gráfico
            grafico = self._grafico_segmentacion_clientes(rfm, segmentos)
            
            # Guardar modelo
            self.modelos_entrenados['segmentacion_clientes'] = kmeans
            self.scalers['rfm'] = scaler
            
            return SegmentacionML(
                tipo='clientes',
                num_clusters=n_clusters,
                segmentos=segmentos,
                grafico_json=grafico,
                caracteristicas={
                    'total_clientes': len(rfm),
                    'recency_promedio': rfm['recency'].mean(),
                    'frecuencia_promedio': rfm['frequency'].mean(),
                    'valor_promedio': rfm['monetary'].mean()
                }
            )
            
        except Exception as e:
            return SegmentacionML(
                tipo='clientes',
                num_clusters=0,
                segmentos=[],
                caracteristicas={'error': str(e)}
            )
    
    def _grafico_segmentacion_clientes(self, rfm: pd.DataFrame, segmentos: List[Dict]) -> str:
        """Genera gráfico profesional de segmentación de clientes."""
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "scatter", "colspan": 2}, None]],
            subplot_titles=(
                '<b>📊 Distribución de Clientes</b>',
                '<b>💰 Valor por Segmento</b>',
                '<b>📈 Frecuencia vs Valor Monetario</b>'
            ),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # Pie chart (con porcentajes)
        fig.add_trace(
            go.Pie(
                labels=[s['nombre'] for s in segmentos],
                values=[s['num_clientes'] for s in segmentos],
                marker_colors=self.colores[:len(segmentos)],
                hole=0.4,
                textposition='inside',
                textinfo='percent+label',
                textfont=dict(size=12, color='white', family='Arial Black'),
                hovertemplate='<b>%{label}</b><br>Clientes: %{value}<br>Porcentaje: %{percent}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Bar chart valor (con anotaciones)
        valores = [s['valor_total'] for s in segmentos]
        nombres = [s['nombre'] for s in segmentos]
        
        fig.add_trace(
            go.Bar(
                x=nombres,
                y=valores,
                marker=dict(
                    color=self.colores[:len(segmentos)],
                    line=dict(color='#2C3E50', width=2)
                ),
                text=[f'${v:,.0f}' for v in valores],
                textposition='outside',
                textfont=dict(size=11, family='Arial Black'),
                hovertemplate='<b>%{x}</b><br>Valor Total: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # Scatter (Frecuencia vs Valor)
        for i, seg in enumerate(segmentos):
            seg_data = rfm[rfm['segmento'] == seg['id']]
            fig.add_trace(
                go.Scatter(
                    x=seg_data['frequency'],
                    y=seg_data['monetary'],
                    mode='markers',
                    name=seg['nombre'],
                    marker=dict(
                        color=self.colores[i % len(self.colores)],
                        size=10,
                        opacity=0.7,
                        line=dict(width=1, color='white')
                    ),
                    hovertemplate='<b>' + seg['nombre'] + '</b><br>Frecuencia: %{x}<br>Valor: $%{y:,.0f}<extra></extra>'
                ),
                row=2, col=1
            )
        
        fig.update_layout(
            title=dict(
                text='<b>🎯 Segmentación Inteligente de Clientes (RFM + K-Means)</b>',
                font=dict(size=18, family='Arial Black', color='#2C3E50'),
                x=0.5,
                xanchor='center'
            ),
            template='plotly_white',
            height=750,
            showlegend=True,
            legend=dict(
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='#2C3E50',
                borderwidth=2,
                font=dict(size=11)
            ),
            plot_bgcolor='rgba(245,245,245,0.5)',
            paper_bgcolor='white',
            font=dict(family='Arial', size=12, color='#2C3E50')
        )
        
        # Actualizar ejes del scatter
        fig.update_xaxes(
            title_text='<b>Frecuencia de Compra</b>',
            gridcolor='rgba(128,128,128,0.2)',
            showline=True,
            linewidth=2,
            linecolor='#2C3E50',
            row=2, col=1
        )
        fig.update_yaxes(
            title_text='<b>Valor Monetario ($)</b>',
            tickformat='$,.0f',
            gridcolor='rgba(128,128,128,0.2)',
            showline=True,
            linewidth=2,
            linecolor='#2C3E50',
            row=2, col=1
        )
        
        # Actualizar eje Y del bar chart
        fig.update_yaxes(
            tickformat='$,.0f',
            gridcolor='rgba(128,128,128,0.2)',
            row=1, col=2
        )
        
        return fig.to_json()
    
    # ============================================================
    # DETECCIÓN DE ANOMALÍAS
    # ============================================================
    
    def detectar_anomalias_ventas(self) -> Dict[str, Any]:
        """Detecta anomalías en ventas usando Isolation Forest."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            df = self.conector.ventas_periodo(fecha_inicio, None)
            
            if df.empty or len(df) < 30:
                return {'error': 'Datos insuficientes para detección de anomalías'}
            
            df['fecha'] = pd.to_datetime(df['date_order'])
            df_diario = df.groupby(df['fecha'].dt.date).agg({
                'amount_total': 'sum',
                'id': 'count'
            }).reset_index()
            df_diario.columns = ['fecha', 'ventas', 'ordenes']
            df_diario['fecha'] = pd.to_datetime(df_diario['fecha'])
            
            # Features
            df_diario['dia_semana'] = df_diario['fecha'].dt.dayofweek
            
            # Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            features = df_diario[['ventas', 'ordenes', 'dia_semana']]
            df_diario['anomalia'] = iso_forest.fit_predict(features)
            df_diario['es_anomalia'] = df_diario['anomalia'] == -1
            
            # Filtrar anomalías
            anomalias = df_diario[df_diario['es_anomalia']].copy()
            
            # Clasificar anomalías
            media_ventas = df_diario['ventas'].mean()
            anomalias['tipo'] = anomalias['ventas'].apply(
                lambda x: '📈 Pico Positivo' if x > media_ventas else '📉 Caída'
            )
            
            # Generar gráfico
            fig = go.Figure()
            
            # Línea de ventas normales
            normales = df_diario[~df_diario['es_anomalia']]
            fig.add_trace(go.Scatter(
                x=normales['fecha'],
                y=normales['ventas'],
                mode='lines',
                name='Ventas Normales',
                line=dict(color=self.colores[0], width=2)
            ))
            
            # Anomalías
            if len(anomalias) > 0:
                picos = anomalias[anomalias['ventas'] > media_ventas]
                caidas = anomalias[anomalias['ventas'] <= media_ventas]
                
                if len(picos) > 0:
                    fig.add_trace(go.Scatter(
                        x=picos['fecha'],
                        y=picos['ventas'],
                        mode='markers',
                        name='Picos Positivos',
                        marker=dict(color='green', size=15, symbol='triangle-up')
                    ))
                
                if len(caidas) > 0:
                    fig.add_trace(go.Scatter(
                        x=caidas['fecha'],
                        y=caidas['ventas'],
                        mode='markers',
                        name='Caídas',
                        marker=dict(color='red', size=15, symbol='triangle-down')
                    ))
            
            fig.update_layout(
                title='Detección de Anomalías en Ventas (Isolation Forest)',
                xaxis_title='Fecha',
                yaxis_title='Ventas ($)',
                template='plotly_dark'
            )
            
            self.modelos_entrenados['anomalias_ventas'] = iso_forest
            
            return {
                'tipo': 'anomalias',
                'total_anomalias': len(anomalias),
                'picos_positivos': len(anomalias[anomalias['ventas'] > media_ventas]),
                'caidas': len(anomalias[anomalias['ventas'] <= media_ventas]),
                'anomalias': anomalias[['fecha', 'ventas', 'ordenes', 'tipo']].to_dict('records'),
                'grafico_json': fig,
                'insights': [
                    f"Se detectaron {len(anomalias)} días con comportamiento anómalo",
                    f"📈 {len(anomalias[anomalias['ventas'] > media_ventas])} fueron picos positivos",
                    f"📉 {len(anomalias[anomalias['ventas'] <= media_ventas])} fueron caídas"
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # ANÁLISIS DE TENDENCIAS
    # ============================================================
    
    def analizar_tendencias(self, tipo: str = 'ventas') -> Dict[str, Any]:
        """Analiza tendencias de ventas con gráficos."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            df = self.conector.ventas_periodo(fecha_inicio, None)
            
            if df.empty:
                return {'error': 'Sin datos para análisis de tendencias'}
            
            df['fecha'] = pd.to_datetime(df['date_order'])
            
            # Agrupar por diferentes períodos
            df_diario = df.groupby(df['fecha'].dt.date)['amount_total'].sum().reset_index()
            df_diario.columns = ['fecha', 'ventas']
            df_diario['fecha'] = pd.to_datetime(df_diario['fecha'])
            
            df_semanal = df.groupby(df['fecha'].dt.to_period('W'))['amount_total'].sum().reset_index()
            df_semanal.columns = ['semana', 'ventas']
            df_semanal['semana'] = df_semanal['semana'].dt.to_timestamp()
            
            df_mensual = df.groupby(df['fecha'].dt.to_period('M'))['amount_total'].sum().reset_index()
            df_mensual.columns = ['mes', 'ventas']
            df_mensual['mes'] = df_mensual['mes'].dt.to_timestamp()
            
            # Calcular tendencia lineal
            x = np.arange(len(df_mensual))
            y = df_mensual['ventas'].values
            coef = np.polyfit(x, y, 1)
            tendencia = coef[0]  # pendiente
            
            # Media móvil
            df_diario['mm_7d'] = df_diario['ventas'].rolling(7).mean()
            df_diario['mm_30d'] = df_diario['ventas'].rolling(30).mean()
            
            # Crear gráfico
            fig = make_subplots(
                rows=2, cols=2,
                specs=[[{"type": "scatter"}, {"type": "bar"}],
                       [{"type": "scatter", "colspan": 2}, None]],
                subplot_titles=('Ventas Mensuales', 'Ventas por Día de Semana',
                              'Tendencia con Media Móvil')
            )
            
            # Mensual con línea de tendencia
            fig.add_trace(
                go.Bar(
                    x=df_mensual['mes'],
                    y=df_mensual['ventas'],
                    name='Ventas Mensuales',
                    marker_color=self.colores[0]
                ),
                row=1, col=1
            )
            
            # Línea de tendencia
            y_tendencia = coef[0] * x + coef[1]
            fig.add_trace(
                go.Scatter(
                    x=df_mensual['mes'],
                    y=y_tendencia,
                    mode='lines',
                    name='Tendencia',
                    line=dict(color='red', dash='dash')
                ),
                row=1, col=1
            )
            
            # Por día de semana
            df['dia_semana'] = df['fecha'].dt.day_name()
            orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            df_dia = df.groupby('dia_semana')['amount_total'].mean().reindex(orden_dias).reset_index()
            df_dia.columns = ['dia', 'promedio']
            
            fig.add_trace(
                go.Bar(
                    x=df_dia['dia'],
                    y=df_dia['promedio'],
                    name='Promedio por Día',
                    marker_color=self.colores[1]
                ),
                row=1, col=2
            )
            
            # Media móvil
            fig.add_trace(
                go.Scatter(
                    x=df_diario['fecha'],
                    y=df_diario['ventas'],
                    mode='lines',
                    name='Ventas Diarias',
                    line=dict(color=self.colores[4], width=1),
                    opacity=0.5
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df_diario['fecha'],
                    y=df_diario['mm_7d'],
                    mode='lines',
                    name='MM 7 días',
                    line=dict(color=self.colores[0], width=2)
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df_diario['fecha'],
                    y=df_diario['mm_30d'],
                    mode='lines',
                    name='MM 30 días',
                    line=dict(color=self.colores[3], width=2)
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                title='Análisis de Tendencias de Ventas',
                template='plotly_dark',
                height=700
            )
            
            # Insights
            tendencia_texto = '📈 creciente' if tendencia > 0 else '📉 decreciente'
            mejor_dia = df_dia.loc[df_dia['promedio'].idxmax(), 'dia']
            peor_dia = df_dia.loc[df_dia['promedio'].idxmin(), 'dia']
            
            return {
                'tipo': 'tendencias',
                'tendencia_mensual': tendencia,
                'tendencia_texto': tendencia_texto,
                'mejor_dia_semana': mejor_dia,
                'peor_dia_semana': peor_dia,
                'total_periodo': float(df['amount_total'].sum()),
                'promedio_diario': float(df_diario['ventas'].mean()),
                'grafico_json': fig,
                'insights': [
                    f"La tendencia general es {tendencia_texto}",
                    f"El mejor día de la semana es {mejor_dia}",
                    f"El día más bajo es {peor_dia}",
                    f"Total en el período: ${df['amount_total'].sum():,.2f}",
                    f"Promedio diario: ${df_diario['ventas'].mean():,.2f}"
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # GRÁFICOS ESPECÍFICOS
    # ============================================================
    
    def grafico_ventas_por_categoria(self) -> str:
        """Genera gráfico de ventas por categoría (treemap)."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            
            SaleOrderLine = self.conector.odoo.env['sale.order.line']
            line_ids = SaleOrderLine.search([
                ('order_id.state', 'in', ['sale', 'done']),
                ('order_id.date_order', '>=', fecha_inicio)
            ], limit=10000)
            
            if not line_ids:
                return json.dumps({'error': 'Sin datos'})
            
            lineas = SaleOrderLine.read(line_ids, ['product_id', 'price_subtotal'])
            
            # Obtener categorías
            product_ids = list(set(
                l['product_id'][0] if isinstance(l.get('product_id'), (list, tuple)) else 0
                for l in lineas if l.get('product_id')
            ))
            
            Product = self.conector.odoo.env['product.product']
            productos = Product.read(product_ids, ['id', 'categ_id'])
            
            mapa_categ = {}
            for p in productos:
                categ = p.get('categ_id')
                mapa_categ[p['id']] = categ[1] if isinstance(categ, (list, tuple)) else 'Sin categoría'
            
            # Agrupar
            por_categ = {}
            for linea in lineas:
                prod_id = linea['product_id'][0] if isinstance(linea.get('product_id'), (list, tuple)) else 0
                categ = mapa_categ.get(prod_id, 'Sin categoría')
                
                if categ not in por_categ:
                    por_categ[categ] = 0
                por_categ[categ] += linea.get('price_subtotal', 0)
            
            # Crear treemap
            data = [{'categoria': k, 'ventas': v} for k, v in por_categ.items()]
            df = pd.DataFrame(data)
            
            fig = px.treemap(
                df,
                path=['categoria'],
                values='ventas',
                color='ventas',
                color_continuous_scale='RdYlGn',
                title='<b>🗂️ Ventas por Categoría (Treemap Interactivo)</b>',
                hover_data={'ventas': ':$,.2f'}
            )
            
            fig.update_layout(
                template='plotly_white',
                title_font=dict(size=18, family='Arial Black', color='#2C3E50'),
                font=dict(family='Arial', size=12, color='#2C3E50'),
                paper_bgcolor='white',
                height=600
            )
            
            fig.update_traces(
                textfont=dict(size=14, family='Arial Black', color='white'),
                hovertemplate='<b>%{label}</b><br>Ventas: $%{value:,.2f}<extra></extra>'
            )
            
            return fig.to_json()
            
        except Exception as e:
            return json.dumps({'error': str(e)})
    
    def grafico_gauge_objetivo(self, actual: float, objetivo: float, titulo: str = "Progreso") -> str:
        """Genera gráfico de gauge/velocímetro."""
        porcentaje = (actual / objetivo * 100) if objetivo > 0 else 0
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=actual,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={
                'text': f'<b>{titulo}</b>',
                'font': {'size': 20, 'family': 'Arial Black', 'color': '#2C3E50'}
            },
            delta={
                'reference': objetivo,
                'relative': True,
                'valueformat': '.1%',
                'font': {'size': 16}
            },
            number={
                'prefix': '$',
                'valueformat': ',.0f',
                'font': {'size': 24, 'family': 'Arial Black'}
            },
            gauge={
                'axis': {
                    'range': [None, objetivo * 1.2],
                    'tickformat': '$,.0f',
                    'tickfont': {'size': 12}
                },
                'bar': {'color': self.colores[0], 'thickness': 0.8},
                'steps': [
                    {'range': [0, objetivo * 0.5], 'color': 'rgba(255, 68, 68, 0.3)'},
                    {'range': [objetivo * 0.5, objetivo * 0.8], 'color': 'rgba(255, 170, 0, 0.3)'},
                    {'range': [objetivo * 0.8, objetivo], 'color': 'rgba(0, 170, 0, 0.3)'}
                ],
                'threshold': {
                    'line': {'color': '#2C3E50', 'width': 5},
                    'thickness': 0.85,
                    'value': objetivo
                },
                'borderwidth': 2,
                'bordercolor': '#2C3E50'
            }
        ))
        
        fig.update_layout(
            template='plotly_white',
            height=450,
            paper_bgcolor='white',
            font=dict(family='Arial', color='#2C3E50')
        )
        
        return fig.to_json()


class FormateadorML:
    """Formatea resultados de ML a Markdown."""
    
    @staticmethod
    def formatear_prediccion(pred: PrediccionML) -> str:
        """Formatea una predicción ML."""
        md = f"""## Predicción de Ventas (Machine Learning)

**Modelo:** Random Forest | **Confianza (R²):** {pred.confianza:.1%}

### Métricas del Modelo
| Métrica | Valor |
|---------|-------|
| Error Absoluto Medio | ${pred.metricas.get('mae', 0):,.2f} |
| R² Score | {pred.metricas.get('r2', 0):.3f} |
| Total Predicho | **${pred.metricas.get('total_predicho', 0):,.2f}** |
| Promedio Diario Esperado | ${pred.metricas.get('promedio_predicho', 0):,.2f} |

### Proyección ({len(pred.valores_predichos)} días)
| Fecha | Predicción | Intervalo 95% |
|-------|------------|---------------|
"""
        for i, (fecha, pred_val) in enumerate(zip(pred.fechas_predichas[:10], pred.valores_predichos[:10])):
            inf = pred.intervalo_inferior[i]
            sup = pred.intervalo_superior[i]
            md += f"| {fecha} | ${pred_val:,.2f} | ${inf:,.0f} - ${sup:,.0f} |\n"
        
        if len(pred.valores_predichos) > 10:
            md += f"| ... | *{len(pred.valores_predichos) - 10} días más* | ... |\n"
        
        md += "\n### 💡 Insights\n"
        for insight in pred.insights:
            md += f"- {insight}\n"
        
        md += "\n_Gráfico interactivo generado_"
        
        return md
    
    @staticmethod
    def formatear_segmentacion(seg: SegmentacionML) -> str:
        """Formatea una segmentación ML."""
        md = f"""## 👥 Segmentación de Clientes (K-Means RFM)

**Clusters:** {seg.num_clusters} | **Total Clientes:** {seg.caracteristicas.get('total_clientes', 0):,}

### Segmentos Identificados

"""
        for s in seg.segmentos:
            md += f"""#### {s['nombre']}
- Clientes: **{s['num_clientes']:,}**
- Última compra promedio: **{s['recency_promedio']:.0f} días**
- Frecuencia promedio: **{s['frecuencia_promedio']:.1f} órdenes**
- Valor promedio: **${s['valor_promedio']:,.2f}**
- Valor total del segmento: **${s['valor_total']:,.2f}**

"""
        
        md += "_Gráfico interactivo generado (segmentación visual)_"
        
        return md
    
    @staticmethod
    def formatear_anomalias(datos: Dict) -> str:
        """Formatea detección de anomalías."""
        if 'error' in datos:
            return f"## {datos['error']}"
        
        md = f"""## Detección de Anomalías (Isolation Forest)

**Total Anomalías Detectadas:** {datos['total_anomalias']}

| Tipo | Cantidad |
|------|----------|
| 📈 Picos Positivos | {datos['picos_positivos']} |
| 📉 Caídas | {datos['caidas']} |

### Días Anómalos Detectados
"""
        for anomalia in datos.get('anomalias', [])[:10]:
            fecha = anomalia['fecha']
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%Y-%m-%d')
            md += f"- **{fecha}**: ${anomalia['ventas']:,.2f} ({anomalia['tipo']})\n"
        
        md += "\n### 💡 Insights\n"
        for insight in datos.get('insights', []):
            md += f"- {insight}\n"
        
        return md
    
    @staticmethod
    def formatear_tendencias(datos: Dict) -> str:
        """Formatea análisis de tendencias."""
        if 'error' in datos:
            return f"## {datos['error']}"
        
        md = f"""## Análisis de Tendencias

### Resumen General
| Métrica | Valor |
|---------|-------|
| Tendencia | **{datos['tendencia_texto']}** |
| Total del Período | **${datos['total_periodo']:,.2f}** |
| Promedio Diario | **${datos['promedio_diario']:,.2f}** |
| Mejor Día | **{datos['mejor_dia_semana']}** |
| Peor Día | **{datos['peor_dia_semana']}** |

### Insights
"""
        for insight in datos.get('insights', []):
            md += f"- {insight}\n"
        
        md += "\n_Gráfico interactivo de tendencias generado_"
        
        return md


# Instancias globales
motor_ml = MotorML()
formateador_ml = FormateadorML()


def set_conector_ml(conector):
    """Configura el conector para el motor ML."""
    motor_ml.set_conector(conector)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" MOTOR ML - Test de Funcionalidades")
    print("=" * 60)
    
    print("\nMotor ML creado correctamente")
    print("Funcionalidades disponibles:")
    print("  - predecir_ventas_ml(dias)")
    print("  - segmentar_clientes(n_clusters)")
    print("  - detectar_anomalias_ventas()")
    print("  - analizar_tendencias()")
    print("  - grafico_ventas_por_categoria()")
    print("  - grafico_gauge_objetivo(actual, objetivo)")
   
