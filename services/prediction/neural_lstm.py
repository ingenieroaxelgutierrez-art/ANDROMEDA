# ============================================================
# NEURAL LSTM - REDES NEURONALES PARA ANDROMEDA
# ============================================================
# Sistema de Deep Learning con PyTorch para predicciones
# avanzadas de series temporales usando LSTM
# ============================================================

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')

# Librerías de datos
import pandas as pd
import numpy as np

# PyTorch
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Gráficos
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.logging_config import get_logger
logger = get_logger("services.prediction.neural_lstm")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ============================================================
# CONFIGURACIÓN
# ============================================================

@dataclass
class ConfigLSTM:
    """Configuración del modelo LSTM."""
    input_size: int = 1          # Features de entrada
    hidden_size: int = 64        # Neuronas en capa oculta
    num_layers: int = 2          # Capas LSTM apiladas
    output_size: int = 1         # Salida (predicción)
    sequence_length: int = 30    # Días de contexto
    dropout: float = 0.2         # Regularización
    learning_rate: float = 0.001
    epochs: int = 100
    batch_size: int = 32
    patience: int = 10           # Early stopping


# ============================================================
# DATASET PARA SERIES TEMPORALES
# ============================================================

class TimeSeriesDataset(Dataset):
    """Dataset para series temporales con secuencias."""
    
    def __init__(self, data: np.ndarray, seq_length: int):
        self.data = torch.FloatTensor(data)
        self.seq_length = seq_length
    
    def __len__(self):
        return len(self.data) - self.seq_length
    
    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_length]
        y = self.data[idx + self.seq_length]
        return x.unsqueeze(-1), y  # Añadir dimensión de features


# ============================================================
# MODELO LSTM
# ============================================================

class SalesLSTM(nn.Module):
    """Red LSTM para predicción de ventas."""
    
    def __init__(self, config: ConfigLSTM):
        super(SalesLSTM, self).__init__()
        
        self.hidden_size = config.hidden_size
        self.num_layers = config.num_layers
        
        # Capa LSTM
        self.lstm = nn.LSTM(
            input_size=config.input_size,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            batch_first=True,
            dropout=config.dropout if config.num_layers > 1 else 0
        )
        
        # Capa fully connected
        self.fc = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_size // 2, config.output_size)
        )
    
    def forward(self, x):
        # x shape: (batch, seq_len, features)
        batch_size = x.size(0)
        
        # Inicializar estados ocultos
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size)
        
        # LSTM forward
        out, _ = self.lstm(x, (h0, c0))
        
        # Tomar solo la última salida de la secuencia
        out = self.fc(out[:, -1, :])
        
        return out


# ============================================================
# RESULTADO DE PREDICCIÓN
# ============================================================

@dataclass
class PrediccionLSTM:
    """Resultado de predicción con LSTM."""
    tipo: str = "lstm"
    valores_predichos: List[float] = field(default_factory=list)
    fechas_predichas: List[str] = field(default_factory=list)
    confianza: float = 0.0
    intervalo_inferior: List[float] = field(default_factory=list)
    intervalo_superior: List[float] = field(default_factory=list)
    metricas: Dict[str, float] = field(default_factory=dict)
    grafico_json: str = ""
    insights: List[str] = field(default_factory=list)
    perdida_entrenamiento: List[float] = field(default_factory=list)
    perdida_validacion: List[float] = field(default_factory=list)


# ============================================================
# MOTOR NEURAL LSTM
# ============================================================

class MotorNeuralLSTM:
    """Motor de predicciones con LSTM."""
    
    def __init__(self):
        self.conector = None
        self.modelo = None
        self.scaler_min = 0
        self.scaler_max = 1
        self.config = ConfigLSTM()
        self.device = torch.device('cpu')  # CPU por ahora
        
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
        
        print("Motor Neural LSTM inicializado (PyTorch CPU)")
    
    def set_conector(self, conector):
        """Configura el conector de Odoo."""
        self.conector = conector
    
    def _normalizar(self, data: np.ndarray) -> np.ndarray:
        """Normaliza datos a [0, 1]."""
        self.scaler_min = data.min()
        self.scaler_max = data.max()
        if self.scaler_max - self.scaler_min == 0:
            return np.zeros_like(data)
        return (data - self.scaler_min) / (self.scaler_max - self.scaler_min)
    
    def _desnormalizar(self, data: np.ndarray) -> np.ndarray:
        """Desnormaliza datos de [0, 1] a escala original."""
        return data * (self.scaler_max - self.scaler_min) + self.scaler_min
    
    def _preparar_datos_ventas(self) -> Tuple[np.ndarray, pd.DataFrame]:
        """Obtiene y prepara datos de ventas para LSTM."""
        # Obtener datos históricos (máximo posible)
        fecha_inicio = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')  # 2 años
        df = self.conector.ventas_periodo(fecha_inicio, None)
        
        if df.empty:
            return np.array([]), pd.DataFrame()
        
        # Agrupar por día
        df['fecha'] = pd.to_datetime(df['date_order'])
        df_diario = df.groupby(df['fecha'].dt.date).agg({
            'amount_total': 'sum'
        }).reset_index()
        df_diario.columns = ['fecha', 'ventas']
        df_diario['fecha'] = pd.to_datetime(df_diario['fecha'])
        df_diario = df_diario.sort_values('fecha').reset_index(drop=True)
        
        # Rellenar días faltantes
        fecha_rango = pd.date_range(df_diario['fecha'].min(), df_diario['fecha'].max())
        df_completo = pd.DataFrame({'fecha': fecha_rango})
        df_diario = df_completo.merge(df_diario, on='fecha', how='left')
        df_diario['ventas'] = df_diario['ventas'].fillna(0)
        
        return df_diario['ventas'].values, df_diario
    
    def entrenar_modelo(self, epochs: int = None) -> Dict[str, Any]:
        """Entrena el modelo LSTM con datos históricos."""
        try:
            # Obtener datos
            ventas, df_diario = self._preparar_datos_ventas()
            
            if len(ventas) < self.config.sequence_length + 50:
                return {
                    'exito': False,
                    'error': f'Se necesitan al menos {self.config.sequence_length + 50} días de datos'
                }
            
            # Normalizar
            ventas_norm = self._normalizar(ventas)
            
            # Crear dataset
            dataset = TimeSeriesDataset(ventas_norm, self.config.sequence_length)
            
            # Split train/val (80/20)
            train_size = int(len(dataset) * 0.8)
            val_size = len(dataset) - train_size
            
            train_dataset, val_dataset = torch.utils.data.random_split(
                dataset, [train_size, val_size]
            )
            
            train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=self.config.batch_size)
            
            # Crear modelo
            self.modelo = SalesLSTM(self.config).to(self.device)
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(self.modelo.parameters(), lr=self.config.learning_rate)
            
            # Entrenamiento con early stopping
            train_losses = []
            val_losses = []
            mejor_val_loss = float('inf')
            paciencia_actual = 0
            mejor_modelo = None
            
            num_epochs = epochs or self.config.epochs
            
            for epoch in range(num_epochs):
                # Training
                self.modelo.train()
                train_loss = 0
                for X_batch, y_batch in train_loader:
                    X_batch = X_batch.to(self.device)
                    y_batch = y_batch.to(self.device)
                    
                    optimizer.zero_grad()
                    outputs = self.modelo(X_batch)
                    loss = criterion(outputs.squeeze(), y_batch)
                    loss.backward()
                    optimizer.step()
                    train_loss += loss.item()
                
                train_loss /= len(train_loader)
                train_losses.append(train_loss)
                
                # Validation
                self.modelo.eval()
                val_loss = 0
                with torch.no_grad():
                    for X_batch, y_batch in val_loader:
                        X_batch = X_batch.to(self.device)
                        y_batch = y_batch.to(self.device)
                        outputs = self.modelo(X_batch)
                        loss = criterion(outputs.squeeze(), y_batch)
                        val_loss += loss.item()
                
                val_loss /= len(val_loader)
                val_losses.append(val_loss)
                
                # Early stopping
                if val_loss < mejor_val_loss:
                    mejor_val_loss = val_loss
                    paciencia_actual = 0
                    mejor_modelo = self.modelo.state_dict().copy()
                else:
                    paciencia_actual += 1
                    if paciencia_actual >= self.config.patience:
                        print(f"Early stopping en epoch {epoch + 1}")
                        break
                
                if (epoch + 1) % 10 == 0:
                    print(f"Epoch {epoch + 1}/{num_epochs} - Train Loss: {train_loss:.6f} - Val Loss: {val_loss:.6f}")
            
            # Cargar mejor modelo
            if mejor_modelo:
                self.modelo.load_state_dict(mejor_modelo)
            
            return {
                'exito': True,
                'epochs_entrenados': len(train_losses),
                'train_loss_final': train_losses[-1],
                'val_loss_final': val_losses[-1],
                'train_losses': train_losses,
                'val_losses': val_losses,
                'dias_datos': len(ventas)
            }
            
        except Exception as e:
            return {'exito': False, 'error': str(e)}
    
    def predecir_ventas_lstm(self, dias_prediccion: int = 30, 
                              entrenar: bool = True) -> PrediccionLSTM:
        """Predice ventas usando LSTM."""
        try:
            # Obtener datos
            ventas, df_diario = self._preparar_datos_ventas()
            
            if len(ventas) < self.config.sequence_length + 20:
                return PrediccionLSTM(
                    metricas={'error': 'Datos insuficientes para LSTM'},
                    insights=['Se necesitan al menos 50 días de datos históricos']
                )
            
            # Entrenar si es necesario
            train_result = None
            if entrenar or self.modelo is None:
                print("Entrenando modelo LSTM...")
                train_result = self.entrenar_modelo()
                if not train_result.get('exito'):
                    return PrediccionLSTM(
                        metricas={'error': train_result.get('error', 'Error de entrenamiento')},
                        insights=['Error durante el entrenamiento del modelo']
                    )
            
            # Normalizar datos
            ventas_norm = self._normalizar(ventas)
            
            # Predicción
            self.modelo.eval()
            
            # Usar últimos N días como secuencia inicial
            secuencia = ventas_norm[-self.config.sequence_length:].copy()
            predicciones_norm = []
            
            with torch.no_grad():
                for _ in range(dias_prediccion):
                    # Preparar input
                    x = torch.FloatTensor(secuencia[-self.config.sequence_length:]).unsqueeze(0).unsqueeze(-1)
                    x = x.to(self.device)
                    
                    # Predecir
                    pred = self.modelo(x).item()
                    predicciones_norm.append(pred)
                    
                    # Añadir a secuencia para siguiente predicción
                    secuencia = np.append(secuencia, pred)
            
            # Desnormalizar
            predicciones = self._desnormalizar(np.array(predicciones_norm))
            predicciones = np.maximum(predicciones, 0)  # No negativos
            
            # Generar fechas
            ultima_fecha = df_diario['fecha'].max()
            fechas_pred = [
                (ultima_fecha + timedelta(days=i+1)).strftime('%Y-%m-%d')
                for i in range(dias_prediccion)
            ]
            
            # Calcular intervalos de confianza (basados en varianza histórica)
            std_historico = ventas.std()
            intervalo_inf = [max(0, p - 1.5 * std_historico) for p in predicciones]
            intervalo_sup = [p + 1.5 * std_historico for p in predicciones]
            
            # Calcular métricas
            metricas = {
                'total_predicho': float(sum(predicciones)),
                'promedio_predicho': float(np.mean(predicciones)),
                'dias_datos_historicos': len(ventas),
                'dias_predichos': dias_prediccion
            }
            
            if train_result:
                metricas['train_loss'] = train_result.get('train_loss_final', 0)
                metricas['val_loss'] = train_result.get('val_loss_final', 0)
                metricas['epochs'] = train_result.get('epochs_entrenados', 0)
            
            # Calcular confianza (inverso del error de validación)
            if train_result and train_result.get('val_loss_final', 1) > 0:
                confianza = max(0, min(1, 1 - train_result['val_loss_final']))
            else:
                confianza = 0.7
            
            # Generar gráfico
            grafico = self._grafico_prediccion_lstm(
                df_diario, fechas_pred, predicciones.tolist(),
                intervalo_inf, intervalo_sup, train_result
            )
            
            # Insights
            insights = self._generar_insights_lstm(
                predicciones, ventas.mean(), ventas.std(), train_result
            )
            
            return PrediccionLSTM(
                tipo='lstm',
                valores_predichos=predicciones.tolist(),
                fechas_predichas=fechas_pred,
                confianza=confianza,
                intervalo_inferior=intervalo_inf,
                intervalo_superior=intervalo_sup,
                metricas=metricas,
                grafico_json=grafico,
                insights=insights,
                perdida_entrenamiento=train_result.get('train_losses', []) if train_result else [],
                perdida_validacion=train_result.get('val_losses', []) if train_result else []
            )
            
        except Exception as e:
            return PrediccionLSTM(
                metricas={'error': str(e)},
                insights=[f'Error en predicción LSTM: {str(e)}']
            )
    
    def _grafico_prediccion_lstm(self, df_historico: pd.DataFrame,
                                   fechas_pred: List[str], predicciones: List[float],
                                   intervalo_inf: List[float], intervalo_sup: List[float],
                                   train_result: Dict = None) -> str:
        """Genera gráfico profesional de predicción LSTM."""
        
        # Crear subplots
        if train_result and train_result.get('train_losses'):
            fig = make_subplots(
                rows=2, cols=1,
                row_heights=[0.7, 0.3],
                subplot_titles=(
                    '<b>🔮 Predicción de Ventas con Red Neuronal LSTM</b>',
                    '<b>📉 Curva de Aprendizaje del Modelo</b>'
                ),
                vertical_spacing=0.15
            )
        else:
            fig = go.Figure()
        
        # ============== GRÁFICO PRINCIPAL ==============
        # Datos históricos (últimos 60 días para no saturar)
        df_reciente = df_historico.tail(60)
        
        row = 1 if train_result and train_result.get('train_losses') else None
        
        # Histórico (línea más suave)
        fig.add_trace(go.Scatter(
            x=df_reciente['fecha'],
            y=df_reciente['ventas'],
            mode='lines',
            name='📊 Histórico Real',
            line=dict(color=self.colores[0], width=2.5, shape='spline'),
            hovertemplate='<b>Fecha:</b> %{x|%Y-%m-%d}<br><b>Ventas:</b> $%{y:,.2f}<extra></extra>'
        ), row=row, col=1 if row else None)
        
        # Predicción (con marcadores más visibles)
        fechas_pred_dt = pd.to_datetime(fechas_pred)
        
        fig.add_trace(go.Scatter(
            x=fechas_pred_dt,
            y=predicciones,
            mode='lines+markers',
            name='🤖 Predicción LSTM',
            line=dict(color=self.colores[1], width=3.5, shape='spline', dash='dash'),
            marker=dict(size=8, symbol='diamond', line=dict(width=2, color='white')),
            hovertemplate='<b>Fecha:</b> %{x|%Y-%m-%d}<br><b>Predicción:</b> $%{y:,.2f}<extra></extra>'
        ), row=row, col=1 if row else None)
        
        # Intervalo de confianza (más sutil)
        fig.add_trace(go.Scatter(
            x=list(fechas_pred_dt) + list(fechas_pred_dt)[::-1],
            y=intervalo_sup + intervalo_inf[::-1],
            fill='toself',
            fillcolor='rgba(238, 90, 111, 0.15)',
            line=dict(color='rgba(238, 90, 111, 0.3)', width=1),
            name='📊 Intervalo Confianza',
            hoverinfo='skip',
            showlegend=True
        ), row=row, col=1 if row else None)
        
        # ============== CURVA DE APRENDIZAJE ==============
        if train_result and train_result.get('train_losses'):
            epochs = list(range(1, len(train_result['train_losses']) + 1))
            
            # Training loss
            fig.add_trace(go.Scatter(
                x=epochs,
                y=train_result['train_losses'],
                mode='lines',
                name='📈 Loss Entrenamiento',
                line=dict(color=self.colores[2], width=2.5),
                hovertemplate='<b>Época:</b> %{x}<br><b>Loss:</b> %{y:.6f}<extra></extra>'
            ), row=2, col=1)
            
            # Validation loss
            fig.add_trace(go.Scatter(
                x=epochs,
                y=train_result['val_losses'],
                mode='lines',
                name='📉 Loss Validación',
                line=dict(color=self.colores[3], width=2.5, dash='dot'),
                hovertemplate='<b>Época:</b> %{x}<br><b>Loss:</b> %{y:.6f}<extra></extra>'
            ), row=2, col=1)
            
            # Mejor época (mínimo val loss)
            mejor_epoch = np.argmin(train_result['val_losses']) + 1
            mejor_loss = min(train_result['val_losses'])
            
            fig.add_trace(go.Scatter(
                x=[mejor_epoch],
                y=[mejor_loss],
                mode='markers',
                name='⭐ Mejor Modelo',
                marker=dict(size=15, symbol='star', color=self.colores[4], line=dict(width=2, color='white')),
                hovertemplate=f'<b>Mejor Época:</b> {mejor_epoch}<br><b>Val Loss:</b> {mejor_loss:.6f}<extra></extra>',
                showlegend=False
            ), row=2, col=1)
            
            # Anotación en mejor punto
            fig.add_annotation(
                x=mejor_epoch,
                y=mejor_loss,
                text=f"⭐ Época {mejor_epoch}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor=self.colores[4],
                ax=30,
                ay=-30,
                font=dict(size=11, color=self.colores[4], family='Arial Black'),
                row=2, col=1
            )
            
            fig.update_xaxes(
                title_text="<b>Época de Entrenamiento</b>",
                title_font=dict(size=13),
                gridcolor='rgba(128,128,128,0.2)',
                row=2, col=1
            )
            fig.update_yaxes(
                title_text="<b>Error (MSE)</b>",
                title_font=dict(size=13),
                gridcolor='rgba(128,128,128,0.2)',
                row=2, col=1
            )
        
        # ============== LAYOUT PROFESIONAL ==============
        fig.update_layout(
            title=dict(
                text='<b>🧠 ANDROMEDA - Predicción Avanzada con Red Neuronal LSTM</b>',
                font=dict(size=20, family='Arial Black', color='#2C3E50'),
                x=0.5,
                xanchor='center'
            ),
            template='plotly_white',  # ← Cambio crítico: fondo blanco profesional
            height=800 if train_result and train_result.get('train_losses') else 550,
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='white',
                font_size=13,
                font_family='Arial'
            ),
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
        
        # ============== EJES CON FORMATO ==============
        if row:
            fig.update_xaxes(
                title_text="<b>Fecha</b>",
                title_font=dict(size=14),
                gridcolor='rgba(128,128,128,0.2)',
                showline=True,
                linewidth=2,
                linecolor='#2C3E50',
                row=1, col=1
            )
            fig.update_yaxes(
                title_text="<b>Ventas ($)</b>",
                title_font=dict(size=14),
                tickformat='$,.0f',  # ← Formato de moneda
                gridcolor='rgba(128,128,128,0.2)',
                showline=True,
                linewidth=2,
                linecolor='#2C3E50',
                row=1, col=1
            )
        else:
            fig.update_xaxes(
                title_text="<b>Fecha</b>",
                title_font=dict(size=14),
                gridcolor='rgba(128,128,128,0.2)',
                showline=True,
                linewidth=2,
                linecolor='#2C3E50'
            )
            fig.update_yaxes(
                title_text="<b>Ventas ($)</b>",
                title_font=dict(size=14),
                tickformat='$,.0f',
                gridcolor='rgba(128,128,128,0.2)',
                showline=True,
                linewidth=2,
                linecolor='#2C3E50'
            )
        
        return fig.to_json()
    
    def _generar_insights_lstm(self, predicciones: np.ndarray,
                                media_hist: float, std_hist: float,
                                train_result: Dict = None) -> List[str]:
        """Genera insights de la predicción LSTM."""
        insights = []
        
        media_pred = np.mean(predicciones)
        total_pred = sum(predicciones)
        
        # Info del entrenamiento
        if train_result:
            insights.append(f"🧠 Modelo entrenado en {train_result.get('epochs_entrenados', 0)} épocas")
            insights.append(f"📊 Datos históricos utilizados: {train_result.get('dias_datos', 0)} días")
        
        # Comparar con histórico
        if media_pred > media_hist * 1.1:
            pct = ((media_pred - media_hist) / media_hist) * 100
            insights.append(f"📈 Tendencia al ALZA: +{pct:.1f}% sobre promedio histórico")
        elif media_pred < media_hist * 0.9:
            pct = ((media_hist - media_pred) / media_hist) * 100
            insights.append(f"📉 Tendencia a la BAJA: -{pct:.1f}% bajo promedio histórico")
        else:
            insights.append("📊 Ventas ESTABLES según el modelo neuronal")
        
        # Mejor/peor día
        max_idx = np.argmax(predicciones)
        min_idx = np.argmin(predicciones)
        insights.append(f"🏆 Mejor día proyectado: Día {max_idx + 1} (${predicciones[max_idx]:,.2f})")
        insights.append(f"⚠️ Día más bajo: Día {min_idx + 1} (${predicciones[min_idx]:,.2f})")
        
        # Total
        insights.append(f"💰 Total esperado ({len(predicciones)} días): **${total_pred:,.2f}**")
        
        return insights


class FormateadorLSTM:
    """Formatea resultados LSTM a Markdown."""
    
    @staticmethod
    def formatear_prediccion(pred: PrediccionLSTM) -> str:
        """Formatea predicción LSTM."""
        if pred.metricas.get('error'):
            return f"## ⚠️ Error LSTM\n\n{pred.metricas['error']}"
        
        md = f"""## 🧠 Predicción de Ventas (Red Neuronal LSTM)

**Modelo:** PyTorch LSTM | **Confianza:** {pred.confianza:.1%}

### 📊 Arquitectura del Modelo
- **Tipo:** LSTM (Long Short-Term Memory)
- **Framework:** PyTorch {torch.__version__}
- **Épocas entrenadas:** {pred.metricas.get('epochs', 'N/A')}
- **Loss final (Train):** {pred.metricas.get('train_loss', 0):.6f}
- **Loss final (Val):** {pred.metricas.get('val_loss', 0):.6f}

### 📈 Métricas de Predicción
| Métrica | Valor |
|---------|-------|
| Días Históricos | **{pred.metricas.get('dias_datos_historicos', 0):,}** |
| Días Predichos | **{pred.metricas.get('dias_predichos', 0)}** |
| Total Predicho | **${pred.metricas.get('total_predicho', 0):,.2f}** |
| Promedio Diario | **${pred.metricas.get('promedio_predicho', 0):,.2f}** |

### 📅 Proyección Detallada
| Fecha | Predicción | Intervalo |
|-------|------------|-----------|
"""
        for i, (fecha, pred_val) in enumerate(zip(pred.fechas_predichas[:10], pred.valores_predichos[:10])):
            inf = pred.intervalo_inferior[i]
            sup = pred.intervalo_superior[i]
            md += f"| {fecha} | **${pred_val:,.2f}** | ${inf:,.0f} - ${sup:,.0f} |\n"
        
        if len(pred.valores_predichos) > 10:
            md += f"| ... | *{len(pred.valores_predichos) - 10} días más* | ... |\n"
        
        md += "\n### 💡 Insights del Modelo\n"
        for insight in pred.insights:
            md += f"- {insight}\n"
        
        md += "\n---\n_🧠 Gráfico interactivo con curva de aprendizaje generado_"
        
        return md


# ============================================================
# INSTANCIAS GLOBALES
# ============================================================

motor_lstm = MotorNeuralLSTM()
formateador_lstm = FormateadorLSTM()


def set_conector_lstm(conector):
    """Configura el conector para el motor LSTM."""
    motor_lstm.set_conector(conector)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" NEURAL LSTM - Test de Redes Neuronales")
    print("=" * 60)
    
    print(f"\n✅ PyTorch: {torch.__version__}")
    print(f"✅ Device: {motor_lstm.device}")
    print("\n📊 Funcionalidades disponibles:")
    print("  - entrenar_modelo(epochs)")
    print("  - predecir_ventas_lstm(dias, entrenar)")
    print("\n🧠 Arquitectura LSTM configurada:")
    print(f"  - Hidden Size: {motor_lstm.config.hidden_size}")
    print(f"  - Num Layers: {motor_lstm.config.num_layers}")
    print(f"  - Sequence Length: {motor_lstm.config.sequence_length}")
    print(f"  - Dropout: {motor_lstm.config.dropout}")
