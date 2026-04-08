# ============================================================
# ANALIZADOR DE DATOS AVANZADO
# ============================================================
# Análisis estadístico, tendencias, predicciones, KPIs
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter

from app.logging_config import get_logger
logger = get_logger("services.analysis.analizador_datos")


class AnalizadorDatos:
    """Motor de análisis de datos avanzado para Odoo."""
    
    def __init__(self):
        self.cache_analisis = {}
    
    # ========================================
    # ANÁLISIS ESTADÍSTICO
    # ========================================
    
    def estadisticas_basicas(self, df: pd.DataFrame, columna: str = None) -> Dict:
        """Calcula estadísticas básicas de un DataFrame."""
        if df.empty:
            return {'error': 'DataFrame vacío'}
        
        # Si se especifica columna numérica
        if columna and columna in df.columns:
            col = df[columna]
            if pd.api.types.is_numeric_dtype(col):
                return {
                    'columna': columna,
                    'total': col.sum(),
                    'promedio': col.mean(),
                    'mediana': col.median(),
                    'minimo': col.min(),
                    'maximo': col.max(),
                    'desviacion': col.std(),
                    'registros': len(col),
                    'nulos': col.isna().sum()
                }
        
        # Análisis general
        resultado = {
            'total_registros': len(df),
            'columnas': list(df.columns),
            'tipos': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'nulos_por_columna': df.isna().sum().to_dict()
        }
        
        # Estadísticas de columnas numéricas
        numericas = df.select_dtypes(include=[np.number])
        if not numericas.empty:
            resultado['estadisticas_numericas'] = {}
            for col in numericas.columns:
                resultado['estadisticas_numericas'][col] = {
                    'suma': numericas[col].sum(),
                    'promedio': numericas[col].mean(),
                    'min': numericas[col].min(),
                    'max': numericas[col].max()
                }
        
        return resultado
    
    def analisis_ventas(self, df: pd.DataFrame) -> Dict:
        """Análisis completo de ventas."""
        if df.empty:
            return {'mensaje': 'No hay datos de ventas para analizar'}
        
        resultado = {
            'resumen': {},
            'por_estado': {},
            'top_clientes': [],
            'tendencia': {},
            'insights': []
        }
        
        # Resumen general
        if 'amount_total' in df.columns:
            resultado['resumen'] = {
                'total_ordenes': len(df),
                'monto_total': df['amount_total'].sum(),
                'ticket_promedio': df['amount_total'].mean(),
                'ticket_maximo': df['amount_total'].max(),
                'ticket_minimo': df['amount_total'].min()
            }
        
        # Por estado
        if 'state' in df.columns:
            estados = df.groupby('state').agg({
                'id': 'count',
                'amount_total': 'sum' if 'amount_total' in df.columns else 'count'
            }).to_dict('index')
            resultado['por_estado'] = estados
        
        # Top clientes
        if 'partner_id' in df.columns:
            # Manejar valores de Odoo (tuplas)
            df['cliente_nombre'] = df['partner_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else str(x)
            )
            if 'amount_total' in df.columns:
                top = df.groupby('cliente_nombre')['amount_total'].sum().nlargest(5).to_dict()
                resultado['top_clientes'] = [{'cliente': k, 'total': v} for k, v in top.items()]
        
        # Tendencia por fecha
        if 'date_order' in df.columns:
            df['fecha'] = pd.to_datetime(df['date_order']).dt.date
            tendencia = df.groupby('fecha').agg({
                'id': 'count',
                'amount_total': 'sum' if 'amount_total' in df.columns else 'count'
            }).to_dict('index')
            resultado['tendencia'] = {str(k): v for k, v in tendencia.items()}
        
        # Generar insights
        resultado['insights'] = self._generar_insights_ventas(resultado)
        
        return resultado
    
    def analisis_pos(self, df: pd.DataFrame) -> Dict:
        """Análisis de tickets POS."""
        if df.empty:
            return {'mensaje': 'No hay tickets POS para analizar'}
        
        resultado = {
            'resumen': {},
            'por_hora': {},
            'por_sesion': {},
            'insights': []
        }
        
        # Resumen
        if 'amount_total' in df.columns:
            resultado['resumen'] = {
                'total_tickets': len(df),
                'venta_total': df['amount_total'].sum(),
                'ticket_promedio': df['amount_total'].mean(),
                'ticket_maximo': df['amount_total'].max()
            }
        
        # Por hora del día
        if 'date_order' in df.columns:
            try:
                df['hora'] = pd.to_datetime(df['date_order']).dt.hour
                por_hora = df.groupby('hora').agg({
                    'id': 'count',
                    'amount_total': 'sum' if 'amount_total' in df.columns else 'count'
                }).to_dict('index')
                resultado['por_hora'] = por_hora
                
                # Hora pico
                if por_hora:
                    hora_pico = max(por_hora.items(), key=lambda x: x[1].get('id', 0))
                    resultado['hora_pico'] = hora_pico[0]
            except Exception:
                pass
        
        # Por sesión
        if 'session_id' in df.columns:
            df['sesion_nombre'] = df['session_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else str(x)
            )
            por_sesion = df.groupby('sesion_nombre').agg({
                'id': 'count',
                'amount_total': 'sum' if 'amount_total' in df.columns else 'count'
            }).to_dict('index')
            resultado['por_sesion'] = por_sesion
        
        resultado['insights'] = self._generar_insights_pos(resultado)
        
        return resultado
    
    def analisis_inventario(self, df: pd.DataFrame) -> Dict:
        """Análisis de inventario/stock."""
        if df.empty:
            return {'mensaje': 'No hay datos de inventario'}
        
        resultado = {
            'resumen': {},
            'por_ubicacion': {},
            'alertas': [],
            'insights': []
        }
        
        # Resumen
        if 'quantity' in df.columns:
            resultado['resumen'] = {
                'total_items': len(df),
                'total_unidades': df['quantity'].sum(),
                'promedio_por_item': df['quantity'].mean(),
                'items_sin_stock': len(df[df['quantity'] <= 0]),
                'items_bajo_stock': len(df[df['quantity'] < 5])
            }
        
        # Por ubicación
        if 'location_id' in df.columns:
            df['ubicacion'] = df['location_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else str(x)
            )
            por_ubicacion = df.groupby('ubicacion')['quantity'].sum().to_dict()
            resultado['por_ubicacion'] = por_ubicacion
        
        # Alertas de stock bajo
        if 'product_id' in df.columns and 'quantity' in df.columns:
            bajo_stock = df[df['quantity'] < 5].head(10)
            for _, row in bajo_stock.iterrows():
                prod = row['product_id']
                nombre = prod[1] if isinstance(prod, (list, tuple)) and len(prod) > 1 else str(prod)
                resultado['alertas'].append({
                    'producto': nombre,
                    'cantidad': row['quantity'],
                    'tipo': 'stock_bajo' if row['quantity'] > 0 else 'sin_stock'
                })
        
        resultado['insights'] = self._generar_insights_inventario(resultado)
        
        return resultado
    
    def analisis_clientes(self, df: pd.DataFrame) -> Dict:
        """Análisis de clientes."""
        if df.empty:
            return {'mensaje': 'No hay datos de clientes'}
        
        resultado = {
            'resumen': {
                'total_clientes': len(df)
            },
            'por_tipo': {},
            'insights': []
        }
        
        # Clientes con email
        if 'email' in df.columns:
            con_email = len(df[df['email'].notna() & (df['email'] != '')])
            resultado['resumen']['con_email'] = con_email
            resultado['resumen']['sin_email'] = len(df) - con_email
        
        # Clientes con teléfono
        if 'phone' in df.columns:
            con_tel = len(df[df['phone'].notna() & (df['phone'] != '')])
            resultado['resumen']['con_telefono'] = con_tel
        
        # Por país/ciudad si existe
        if 'country_id' in df.columns:
            df['pais'] = df['country_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'Sin país'
            )
            resultado['por_pais'] = df['pais'].value_counts().head(10).to_dict()
        
        return resultado
    
    # ========================================
    # COMPARATIVAS
    # ========================================
    
    def comparar_periodos(self, datos_actual: pd.DataFrame, datos_anterior: pd.DataFrame,
                         columna_valor: str = 'amount_total') -> Dict:
        """Compara dos períodos de datos."""
        
        actual = datos_actual[columna_valor].sum() if not datos_actual.empty and columna_valor in datos_actual.columns else 0
        anterior = datos_anterior[columna_valor].sum() if not datos_anterior.empty and columna_valor in datos_anterior.columns else 0
        
        diferencia = actual - anterior
        porcentaje = (diferencia / anterior * 100) if anterior != 0 else 0
        
        return {
            'periodo_actual': {
                'total': actual,
                'registros': len(datos_actual)
            },
            'periodo_anterior': {
                'total': anterior,
                'registros': len(datos_anterior)
            },
            'variacion': {
                'absoluta': diferencia,
                'porcentaje': porcentaje,
                'tendencia': 'alza' if diferencia > 0 else 'baja' if diferencia < 0 else 'estable'
            }
        }
    
    def ranking_productos(self, df_ventas: pd.DataFrame, top_n: int = 10) -> List[Dict]:
        """Genera ranking de productos más vendidos."""
        # Esto requeriría las líneas de venta, simplificado aquí
        return []
    
    # ========================================
    # INSIGHTS AUTOMÁTICOS
    # ========================================
    
    def _generar_insights_ventas(self, analisis: Dict) -> List[str]:
        """Genera insights automáticos de ventas."""
        insights = []
        
        resumen = analisis.get('resumen', {})
        
        if resumen:
            total = resumen.get('monto_total', 0)
            ordenes = resumen.get('total_ordenes', 0)
            promedio = resumen.get('ticket_promedio', 0)
            
            if ordenes > 0:
                if promedio > 5000:
                    insights.append(f"Ticket promedio alto (${promedio:,.2f})")
                elif promedio < 500:
                    insights.append(f"Ticket promedio bajo (${promedio:,.2f})")
                
                if ordenes > 50:
                    insights.append(f"Buen volumen de órdenes ({ordenes})")
        
        # Por estado
        estados = analisis.get('por_estado', {})
        if 'draft' in estados:
            borradores = estados['draft'].get('id', 0)
            if borradores > 10:
                insights.append(f"Hay {borradores} órdenes en borrador pendientes")
        
        if 'cancel' in estados:
            canceladas = estados['cancel'].get('id', 0)
            if canceladas > 5:
                insights.append(f"{canceladas} órdenes canceladas - revisar causas")
        
        # Top clientes
        top = analisis.get('top_clientes', [])
        if top:
            mejor = top[0]
            insights.append(f"Mejor cliente: {mejor['cliente']} (${mejor['total']:,.2f})")
        
        return insights
    
    def _generar_insights_pos(self, analisis: Dict) -> List[str]:
        """Genera insights de POS."""
        insights = []
        
        resumen = analisis.get('resumen', {})
        hora_pico = analisis.get('hora_pico')
        
        if hora_pico is not None:
            insights.append(f"Hora pico de ventas: {hora_pico}:00 hrs")
        
        if resumen:
            promedio = resumen.get('ticket_promedio', 0)
            if promedio:
                insights.append(f"Ticket promedio en tienda: ${promedio:,.2f}")
        
        return insights
    
    def _generar_insights_inventario(self, analisis: Dict) -> List[str]:
        """Genera insights de inventario."""
        insights = []
        
        resumen = analisis.get('resumen', {})
        alertas = analisis.get('alertas', [])
        
        sin_stock = resumen.get('items_sin_stock', 0)
        bajo_stock = resumen.get('items_bajo_stock', 0)
        
        if sin_stock > 0:
            insights.append(f"{sin_stock} productos SIN STOCK - ¡Atención!")
        
        if bajo_stock > 0:
            insights.append(f"{bajo_stock} productos con stock bajo")
        
        if alertas:
            productos_criticos = [a['producto'] for a in alertas[:3]]
            insights.append(f"Productos críticos: {', '.join(productos_criticos)}")
        
        return insights
    
    # ========================================
    # FORMATEO DE ANÁLISIS
    # ========================================
    
    def formatear_analisis_md(self, tipo: str, analisis: Dict) -> str:
        """Formatea un análisis como Markdown."""
        
        if tipo == 'ventas':
            return self._formatear_ventas_md(analisis)
        elif tipo == 'pos':
            return self._formatear_pos_md(analisis)
        elif tipo == 'inventario':
            return self._formatear_inventario_md(analisis)
        else:
            return self._formatear_generico_md(analisis)
    
    def _formatear_ventas_md(self, analisis: Dict) -> str:
        """Formatea análisis de ventas."""
        resumen = analisis.get('resumen', {})
        insights = analisis.get('insights', [])
        top_clientes = analisis.get('top_clientes', [])
        
        md = "## Análisis de Ventas\n\n"
        
        if resumen:
            md += "### Resumen\n"
            md += f"| Métrica | Valor |\n|---------|-------|\n"
            md += f"| Órdenes | **{resumen.get('total_ordenes', 0):,}** |\n"
            md += f"| Monto Total | **${resumen.get('monto_total', 0):,.2f}** |\n"
            md += f"| Ticket Promedio | **${resumen.get('ticket_promedio', 0):,.2f}** |\n"
            md += f"| Ticket Máximo | **${resumen.get('ticket_maximo', 0):,.2f}** |\n\n"
        
        if top_clientes:
            md += "### Top Clientes\n"
            md += "| Cliente | Total |\n|---------|-------|\n"
            for tc in top_clientes[:5]:
                md += f"| {tc['cliente']} | ${tc['total']:,.2f} |\n"
            md += "\n"
        
        if insights:
            md += "### Insights\n"
            for insight in insights:
                md += f"• {insight}\n"
        
        return md
    
    def _formatear_pos_md(self, analisis: Dict) -> str:
        """Formatea análisis POS."""
        resumen = analisis.get('resumen', {})
        insights = analisis.get('insights', [])
        
        md = "## Análisis de Punto de Venta\n\n"
        
        if resumen:
            md += "### Resumen\n"
            md += f"| Métrica | Valor |\n|---------|-------|\n"
            md += f"| Tickets | **{resumen.get('total_tickets', 0):,}** |\n"
            md += f"| Venta Total | **${resumen.get('venta_total', 0):,.2f}** |\n"
            md += f"| Ticket Promedio | **${resumen.get('ticket_promedio', 0):,.2f}** |\n\n"
        
        hora_pico = analisis.get('hora_pico')
        if hora_pico is not None:
            md += f"**Hora pico:** {hora_pico}:00 hrs\n\n"
        
        if insights:
            md += "### Insights\n"
            for insight in insights:
                md += f"• {insight}\n"
        
        return md
    
    def _formatear_inventario_md(self, analisis: Dict) -> str:
        """Formatea análisis de inventario."""
        resumen = analisis.get('resumen', {})
        alertas = analisis.get('alertas', [])
        insights = analisis.get('insights', [])
        
        md = "## Análisis de Inventario\n\n"
        
        if resumen:
            md += "### Resumen\n"
            md += f"| Métrica | Valor |\n|---------|-------|\n"
            md += f"| Total Items | **{resumen.get('total_items', 0):,}** |\n"
            md += f"| Total Unidades | **{resumen.get('total_unidades', 0):,.0f}** |\n"
            md += f"| Sin Stock | **{resumen.get('items_sin_stock', 0):,}** |\n"
            md += f"| Stock Bajo | **{resumen.get('items_bajo_stock', 0):,}** |\n\n"
        
        if alertas:
            md += "### Alertas de Stock\n"
            md += "| Producto | Cantidad | Estado |\n|----------|----------|--------|\n"
            for a in alertas[:10]:
                estado = "Sin stock" if a['tipo'] == 'sin_stock' else "Bajo"
                md += f"| {a['producto'][:30]} | {a['cantidad']:.0f} | {estado} |\n"
            md += "\n"
        
        if insights:
            md += "### Insights\n"
            for insight in insights:
                md += f"• {insight}\n"
        
        return md
    
    def _formatear_generico_md(self, analisis: Dict) -> str:
        """Formatea análisis genérico."""
        import json
        md = "## Resultados del Análisis\n\n"
        md += "```json\n"
        md += json.dumps(analisis, indent=2, default=str, ensure_ascii=False)
        md += "\n```"
        return md
