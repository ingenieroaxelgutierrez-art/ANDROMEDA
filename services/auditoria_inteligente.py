# ============================================================
# AUDITORÍA INTELIGENTE - SISTEMA DE DETECCIÓN DE ANOMALÍAS
# ============================================================
# Motor de auditoría avanzada para detección de errores,
# inconsistencias fiscales, predicción preventiva y más
# ============================================================

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import json
import math

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pandas as pd
    import numpy as np
    PANDAS_DISPONIBLE = True
except ImportError:
    PANDAS_DISPONIBLE = False

try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

from app.logging_config import get_logger
logger = get_logger("services.auditoria_inteligente")

try:
    from models.conector_odoo import ConectorOdoo
    ODOO_DISPONIBLE = True
except ImportError:
    ODOO_DISPONIBLE = False


# ============================================================
# ESTRUCTURAS DE DATOS
# ============================================================

@dataclass
class AlertaAuditoria:
    """Representa una alerta de auditoría."""
    tipo: str  # error, warning, info, critical
    categoria: str  # fiscal, stock, captura, cliente, etc.
    titulo: str
    descripcion: str
    impacto: str  # alto, medio, bajo
    accion_sugerida: str
    datos: Dict = field(default_factory=dict)
    fecha_deteccion: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'tipo': self.tipo,
            'categoria': self.categoria,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'impacto': self.impacto,
            'accion_sugerida': self.accion_sugerida,
            'datos': self.datos,
            'fecha': self.fecha_deteccion.strftime('%Y-%m-%d %H:%M')
        }


@dataclass
class ResultadoAuditoria:
    """Resultado completo de una auditoría."""
    fecha_ejecucion: datetime
    tipo_auditoria: str
    alertas_criticas: List[AlertaAuditoria]
    alertas_warning: List[AlertaAuditoria]
    alertas_info: List[AlertaAuditoria]
    score_salud: float  # 0-100
    resumen: Dict
    recomendaciones: List[str]
    
    @property
    def total_alertas(self) -> int:
        return len(self.alertas_criticas) + len(self.alertas_warning) + len(self.alertas_info)
    
    @property
    def estado(self) -> str:
        if self.score_salud >= 90:
            return "EXCELENTE"
        elif self.score_salud >= 75:
            return "BUENO"
        elif self.score_salud >= 60:
            return "REGULAR"
        elif self.score_salud >= 40:
            return "CRÍTICO"
        else:
            return "EMERGENCIA"
    
    @property
    def emoji_estado(self) -> str:
        if self.score_salud >= 90:
            return "🟢"
        elif self.score_salud >= 75:
            return "🟡"
        elif self.score_salud >= 60:
            return "🟠"
        else:
            return "🔴"


@dataclass
class PrediccionChurn:
    """Predicción de riesgo de abandono de cliente."""
    cliente_id: int
    cliente_nombre: str
    frecuencia_habitual_dias: float
    dias_sin_comprar: int
    ultima_compra: datetime
    total_historico: float
    riesgo_churn: float  # 0-100
    accion_sugerida: str
    valor_potencial_perdido: float = 0.0  # Valor estimado que se podría perder


@dataclass
class AlertaReposicion:
    """Alerta de reposición de inventario."""
    producto_id: int
    producto_nombre: str
    stock_actual: float
    consumo_diario: float
    dias_cobertura: float
    fecha_agotamiento: datetime
    cantidad_sugerida: float
    proveedor: str
    tiempo_entrega_dias: int
    urgencia: str  # critica, alta, media, baja


# ============================================================
# MOTOR DE AUDITORÍA INTELIGENTE
# ============================================================

class AuditoriaInteligente:
    """
    Sistema de auditoría inteligente para Odoo.
    
    Capacidades:
    - Auditoría nocturna completa
    - Detección de inconsistencias fiscales
    - Predicción de churn de clientes
    - Optimización de compras Just-in-Time
    - Análisis de ventas muertas
    - Semáforo de salud operativa
    """
    
    def __init__(self, odoo: Optional['ConectorOdoo'] = None):
        """Inicializa el motor de auditoría."""
        self.odoo = odoo
        self.alertas: List[AlertaAuditoria] = []
        self.cache_clientes = {}
        self.cache_productos = {}
        
    def set_conector(self, odoo: 'ConectorOdoo'):
        """Establece el conector de Odoo."""
        self.odoo = odoo
        
    def conectar_odoo(self, odoo: 'ConectorOdoo'):
        """Conecta con el conector de Odoo (alias de set_conector)."""
        self.set_conector(odoo)
    
    # ============================================================
    # AUDITORÍA NOCTURNA COMPLETA
    # ============================================================
    
    def auditoria_nocturna_completa(self) -> ResultadoAuditoria:
        """
        Ejecuta una auditoría completa de la base de datos.
        Busca errores de captura, inconsistencias y problemas.
        """
        print("Iniciando Auditoría Nocturna Completa...")
        
        alertas_criticas = []
        alertas_warning = []
        alertas_info = []
        resumen = {}
        
        # 1. Detectar facturas con precio 0
        facturas_precio_cero = self._detectar_facturas_precio_cero()
        for alerta in facturas_precio_cero:
            if alerta.tipo == 'critical':
                alertas_criticas.append(alerta)
            else:
                alertas_warning.append(alerta)
        resumen['facturas_precio_cero'] = len(facturas_precio_cero)
        
        # 2. Detectar stock negativo
        stock_negativo = self._detectar_stock_negativo()
        for alerta in stock_negativo:
            alertas_criticas.append(alerta)
        resumen['stock_negativo'] = len(stock_negativo)
        
        # 3. Detectar pagos duplicados
        pagos_duplicados = self._detectar_pagos_duplicados()
        for alerta in pagos_duplicados:
            alertas_criticas.append(alerta)
        resumen['pagos_duplicados'] = len(pagos_duplicados)
        
        # 4. Pedidos modificados después de confirmar
        pedidos_modificados = self._detectar_pedidos_modificados()
        for alerta in pedidos_modificados:
            alertas_warning.append(alerta)
        resumen['pedidos_modificados'] = len(pedidos_modificados)
        
        # 5. Márgenes peligrosos (bajo costo)
        margenes_peligrosos = self._detectar_margenes_peligrosos()
        for alerta in margenes_peligrosos:
            alertas_criticas.append(alerta)
        resumen['margenes_peligrosos'] = len(margenes_peligrosos)
        
        # 6. Diferencias de centavos en facturas
        diferencias_centavos = self._detectar_diferencias_centavos()
        for alerta in diferencias_centavos:
            alertas_warning.append(alerta)
        resumen['diferencias_centavos'] = len(diferencias_centavos)
        
        # 7. Pagos fantasma
        pagos_fantasma = self._detectar_pagos_fantasma()
        for alerta in pagos_fantasma:
            alertas_criticas.append(alerta)
        resumen['pagos_fantasma'] = len(pagos_fantasma)
        
        # Calcular score de salud
        total_criticos = len(alertas_criticas)
        total_warning = len(alertas_warning)
        total_info = len(alertas_info)
        
        # Penalización por tipo de alerta
        penalizacion = (total_criticos * 10) + (total_warning * 3) + (total_info * 1)
        score_salud = max(0, 100 - penalizacion)
        
        # Generar recomendaciones
        recomendaciones = self._generar_recomendaciones(
            alertas_criticas, alertas_warning, alertas_info
        )
        
        return ResultadoAuditoria(
            fecha_ejecucion=datetime.now(),
            tipo_auditoria="nocturna_completa",
            alertas_criticas=alertas_criticas,
            alertas_warning=alertas_warning,
            alertas_info=alertas_info,
            score_salud=score_salud,
            resumen=resumen,
            recomendaciones=recomendaciones
        )
    
    def _detectar_facturas_precio_cero(self) -> List[AlertaAuditoria]:
        """Detecta facturas con líneas en precio 0."""
        alertas = []
        
        if not self.odoo or not self.odoo.conectado:
            return alertas
        
        try:
            # Buscar líneas de factura con precio 0
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            lineas = self.odoo.search_read('account.move.line',
                [
                    ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
                    ('price_unit', '=', 0),
                    ('quantity', '>', 0),
                    ('move_id.state', '=', 'posted')
                ],
                ['move_id', 'product_id', 'quantity', 'name'],
                limit=100
            )
            
            for linea in lineas:
                alertas.append(AlertaAuditoria(
                    tipo='critical',
                    categoria='facturacion',
                    titulo='Factura con precio $0',
                    descripcion=f"La factura {linea.get('move_id', ['', 'N/A'])[1]} tiene una línea con precio unitario $0",
                    impacto='alto',
                    accion_sugerida='Revisar y corregir el precio en la factura o cancelar si es error',
                    datos={
                        'factura_id': linea.get('move_id', [None])[0],
                        'factura_nombre': linea.get('move_id', ['', 'N/A'])[1],
                        'producto': linea.get('product_id', ['', 'N/A'])[1] if linea.get('product_id') else 'Sin producto',
                        'cantidad': linea.get('quantity', 0)
                    }
                ))
        except Exception as e:
            logger.error(f"Error detectando facturas precio 0: {e}")
        
        return alertas
    
    def _detectar_stock_negativo(self) -> List[AlertaAuditoria]:
        """Detecta productos con stock negativo."""
        alertas = []
        
        if not self.odoo or not self.odoo.conectado:
            return alertas
        
        try:
            # Buscar quants con cantidad negativa
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            quants = self.odoo.search_read('stock.quant',
                [('quantity', '<', 0)],
                ['product_id', 'location_id', 'quantity'],
                limit=100
            )
            
            for quant in quants:
                alertas.append(AlertaAuditoria(
                    tipo='critical',
                    categoria='inventario',
                    titulo='Stock Negativo Detectado',
                    descripcion=f"El producto '{quant.get('product_id', ['', 'N/A'])[1]}' tiene stock negativo: {quant.get('quantity', 0)}",
                    impacto='alto',
                    accion_sugerida='Realizar ajuste de inventario o revisar movimientos de stock',
                    datos={
                        'producto_id': quant.get('product_id', [None])[0],
                        'producto_nombre': quant.get('product_id', ['', 'N/A'])[1],
                        'ubicacion': quant.get('location_id', ['', 'N/A'])[1],
                        'cantidad': quant.get('quantity', 0)
                    }
                ))
        except Exception as e:
            logger.error(f"Error detectando stock negativo: {e}")
        
        return alertas
    
    def _detectar_pagos_duplicados(self) -> List[AlertaAuditoria]:
        """Detecta posibles pagos duplicados."""
        alertas = []
        
        if not self.odoo or not self.odoo.conectado:
            return alertas
        
        try:
            # Buscar pagos del último mes
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            pagos = self.odoo.search_read('account.payment',
                [
                    ('date', '>=', fecha_inicio),
                    ('state', '=', 'posted')
                ],
                ['partner_id', 'amount', 'date', 'name', 'payment_type'],
                limit=500
            )
            
            # Agrupar por partner y monto para detectar duplicados
            pagos_por_partner = defaultdict(list)
            for pago in pagos:
                # partner_id puede ser False o una lista [id, name]
                partner = pago.get('partner_id')
                partner_id = None
                if partner and isinstance(partner, (list, tuple)) and len(partner) > 0:
                    partner_id = partner[0]
                elif isinstance(partner, int):
                    partner_id = partner
                # Ignorar si no hay partner o monto
                if partner_id is None or pago.get('amount') is None:
                    continue
                key = (partner_id, pago.get('amount'), pago.get('date'))
                pagos_por_partner[key].append(pago)
            
            # Detectar duplicados
            for key, lista_pagos in pagos_por_partner.items():
                if len(lista_pagos) > 1:
                    nombres = [p.get('name', 'N/A') for p in lista_pagos]
                    alertas.append(AlertaAuditoria(
                        tipo='critical',
                        categoria='tesoreria',
                        titulo='Posible Pago Duplicado',
                        descripcion=f"Se encontraron {len(lista_pagos)} pagos con el mismo monto ${key[1]:,.2f} al mismo partner en la misma fecha",
                        impacto='alto',
                        accion_sugerida='Verificar si los pagos son correctos o si hay duplicación',
                        datos={
                            'partner_id': key[0],
                            'monto': key[1],
                            'fecha': key[2],
                            'pagos': nombres
                        }
                    ))
        except Exception as e:
            logger.error(f"Error detectando pagos duplicados: {e}")
        
        return alertas
    
    def _detectar_pedidos_modificados(self) -> List[AlertaAuditoria]:
        """Detecta pedidos que fueron modificados después de confirmar."""
        alertas = []
        
        if not self.odoo or not self.odoo.conectado:
            return alertas
        
        try:
            # Buscar mensajes de modificación en pedidos confirmados
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            pedidos = self.odoo.search_read('sale.order',
                [
                    ('state', 'in', ['sale', 'done']),
                    ('date_order', '>=', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
                ],
                ['name', 'partner_id', 'write_date', 'date_order', 'amount_total'],
                limit=200
            )
            
            for pedido in pedidos:
                # Verificar si write_date es muy posterior a date_order
                fecha_orden = datetime.strptime(pedido.get('date_order', '')[:10], '%Y-%m-%d') if pedido.get('date_order') else None
                fecha_mod = datetime.strptime(pedido.get('write_date', '')[:10], '%Y-%m-%d') if pedido.get('write_date') else None
                
                if fecha_orden and fecha_mod and (fecha_mod - fecha_orden).days > 1:
                    alertas.append(AlertaAuditoria(
                        tipo='warning',
                        categoria='captura',
                        titulo='Pedido Modificado Post-Confirmación',
                        descripcion=f"El pedido {pedido.get('name')} fue modificado {(fecha_mod - fecha_orden).days} días después de crearse",
                        impacto='medio',
                        accion_sugerida='Verificar que las modificaciones fueron autorizadas',
                        datos={
                            'pedido': pedido.get('name'),
                            'cliente': pedido.get('partner_id', ['', 'N/A'])[1],
                            'fecha_orden': str(fecha_orden.date()),
                            'fecha_modificacion': str(fecha_mod.date()),
                            'monto': pedido.get('amount_total', 0)
                        }
                    ))
        except Exception as e:
            logger.error(f"Error detectando pedidos modificados: {e}")
        
        return alertas[:20]  # Limitar a 20
    
    def _detectar_margenes_peligrosos(self) -> List[AlertaAuditoria]:
        """Detecta ventas con margen muy bajo o negativo."""
        alertas = []
        
        if not self.odoo or not self.odoo.conectado:
            return alertas
        
        try:
            # Buscar líneas de venta recientes
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            lineas = self.odoo.search_read('sale.order.line',
                [
                    ('order_id.state', 'in', ['sale', 'done']),
                    ('order_id.date_order', '>=', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
                ],
                ['order_id', 'product_id', 'price_unit', 'product_uom_qty', 'purchase_price'],
                limit=500
            )
            
            for linea in lineas:
                precio_venta = linea.get('price_unit', 0)
                costo = linea.get('purchase_price', 0)
                
                if costo and costo > 0 and precio_venta > 0:
                    margen = ((precio_venta - costo) / costo) * 100
                    
                    if margen < 5:  # Margen menor a 5%
                        tipo = 'critical' if margen < 0 else 'warning'
                        alertas.append(AlertaAuditoria(
                            tipo=tipo,
                            categoria='ventas',
                            titulo='Margen Peligroso Detectado',
                            descripcion=f"Producto vendido con margen de {margen:.1f}% en pedido {linea.get('order_id', ['', 'N/A'])[1]}",
                            impacto='alto' if margen < 0 else 'medio',
                            accion_sugerida='Revisar precio de venta o actualizar costo del producto',
                            datos={
                                'pedido': linea.get('order_id', ['', 'N/A'])[1],
                                'producto': linea.get('product_id', ['', 'N/A'])[1],
                                'precio_venta': precio_venta,
                                'costo': costo,
                                'margen_pct': round(margen, 2),
                                'cantidad': linea.get('product_uom_qty', 0)
                            }
                        ))
        except Exception as e:
            logger.error(f"Error detectando márgenes peligrosos: {e}")
        
        return alertas[:30]
    
    def _detectar_diferencias_centavos(self) -> List[AlertaAuditoria]:
        """Detecta facturas con saldo residual de centavos."""
        alertas = []
        
        if not self.odoo or not self.odoo.conectado:
            return alertas
        
        try:
            # Buscar facturas con residual pequeño (centavos)
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            facturas = self.odoo.search_read('account.move',
                [
                    ('move_type', 'in', ['out_invoice', 'in_invoice']),
                    ('state', '=', 'posted'),
                    ('amount_residual', '>', 0),
                    ('amount_residual', '<', 10)  # Menos de $10
                ],
                ['name', 'partner_id', 'amount_residual', 'amount_total', 'invoice_date'],
                limit=100
            )
            
            for factura in facturas:
                residual = factura.get('amount_residual', 0)
                if residual > 0 and residual < 10:
                    alertas.append(AlertaAuditoria(
                        tipo='warning',
                        categoria='contabilidad',
                        titulo='Diferencia de Centavos',
                        descripcion=f"Factura {factura.get('name')} con saldo residual de ${residual:.2f}",
                        impacto='bajo',
                        accion_sugerida='Aplicar ajuste por diferencia de centavos',
                        datos={
                            'factura': factura.get('name'),
                            'partner': factura.get('partner_id', ['', 'N/A'])[1],
                            'residual': residual,
                            'total_original': factura.get('amount_total', 0),
                            'fecha': factura.get('invoice_date')
                        }
                    ))
        except Exception as e:
            logger.error(f"Error detectando diferencias de centavos: {e}")
        
        return alertas
    
    def _detectar_pagos_fantasma(self) -> List[AlertaAuditoria]:
        """Detecta facturas pagadas sin flujo de caja real."""
        alertas = []
        
        if not self.odoo or not self.odoo.conectado:
            return alertas
        
        try:
            # Buscar facturas pagadas (residual = 0)
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            facturas = self.odoo.search_read('account.move',
                [
                    ('move_type', 'in', ['out_invoice']),
                    ('state', '=', 'posted'),
                    ('payment_state', '=', 'paid'),
                    ('amount_total', '>', 1000),  # Facturas significativas
                    ('invoice_date', '>=', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
                ],
                ['name', 'partner_id', 'amount_total', 'invoice_date'],
                limit=100
            )
            
            # Para cada factura, verificar si tiene pagos asociados
            for factura in facturas[:20]:  # Limitar verificación
                try:
                    # Buscar pagos que reconciliaron esta factura
                    # Esto es una simplificación, en realidad deberías revisar las reconciliaciones
                    # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
                    pagos = self.odoo.contar('account.payment', [
                        ('partner_id', '=', factura.get('partner_id', [None])[0]),
                        ('amount', '>=', factura.get('amount_total', 0) * 0.9),
                        ('amount', '<=', factura.get('amount_total', 0) * 1.1),
                        ('state', '=', 'posted')
                    ])
                    
                    if pagos == 0:
                        alertas.append(AlertaAuditoria(
                            tipo='critical',
                            categoria='tesoreria',
                            titulo='Posible Pago Fantasma',
                            descripcion=f"Factura {factura.get('name')} marcada como pagada pero sin pago directo identificable",
                            impacto='alto',
                            accion_sugerida='Verificar cómo se liquidó esta factura y si hay flujo de caja real',
                            datos={
                                'factura': factura.get('name'),
                                'partner': factura.get('partner_id', ['', 'N/A'])[1],
                                'monto': factura.get('amount_total', 0),
                                'fecha': factura.get('invoice_date')
                            }
                        ))
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error detectando pagos fantasma: {e}")
        
        return alertas
    
    def _generar_recomendaciones(self, criticas: List, warnings: List, infos: List) -> List[str]:
        """Genera recomendaciones basadas en las alertas encontradas."""
        recomendaciones = []
        
        # Contar por categoría
        categorias = defaultdict(int)
        for alerta in criticas + warnings:
            categorias[alerta.categoria] += 1
        
        if categorias.get('inventario', 0) > 5:
            recomendaciones.append("URGENTE: Realizar inventario físico completo para corregir diferencias de stock")
        
        if categorias.get('facturacion', 0) > 3:
            recomendaciones.append("Revisar proceso de facturación - múltiples facturas con errores de captura")
        
        if categorias.get('tesoreria', 0) > 0:
            recomendaciones.append("Auditar movimientos de tesorería - hay inconsistencias en pagos")
        
        if categorias.get('ventas', 0) > 5:
            recomendaciones.append("Actualizar lista de precios - hay ventas con márgenes muy bajos")
        
        if categorias.get('contabilidad', 0) > 10:
            recomendaciones.append("Ejecutar proceso de conciliación masiva para cerrar diferencias de centavos")
        
        if not recomendaciones:
            recomendaciones.append("Sistema en buen estado - mantener los controles actuales")
        
        return recomendaciones
    
    # ============================================================
    # PREDICCIÓN DE CHURN DE CLIENTES
    # ============================================================
    
    def analizar_churn_clientes(self, dias_analisis: int = 180) -> List[PrediccionChurn]:
        """
        Analiza riesgo de abandono de clientes.
        Compara frecuencia habitual vs tiempo sin comprar.
        """
        predicciones = []
        
        if not self.odoo or not self.odoo.conectado:
            return predicciones
        
        try:
            fecha_inicio = (datetime.now() - timedelta(days=dias_analisis)).strftime('%Y-%m-%d')
            
            # Obtener todas las ventas del periodo
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            ventas = self.odoo.search_read('sale.order',
                [
                    ('state', 'in', ['sale', 'done']),
                    ('date_order', '>=', fecha_inicio)
                ],
                ['partner_id', 'date_order', 'amount_total'],
                limit=5000
            )
            
            # Agrupar por cliente
            clientes_ventas = defaultdict(list)
            for venta in ventas:
                partner_id = venta.get('partner_id', [None])[0]
                if partner_id:
                    fecha = datetime.strptime(venta.get('date_order', '')[:10], '%Y-%m-%d')
                    clientes_ventas[partner_id].append({
                        'fecha': fecha,
                        'monto': venta.get('amount_total', 0),
                        'nombre': venta.get('partner_id', ['', 'N/A'])[1]
                    })
            
            hoy = datetime.now()
            
            # Analizar cada cliente
            for partner_id, compras in clientes_ventas.items():
                if len(compras) < 2:
                    continue
                
                # Ordenar por fecha
                compras.sort(key=lambda x: x['fecha'])
                
                # Calcular frecuencia habitual (promedio de días entre compras)
                diferencias = []
                for i in range(1, len(compras)):
                    diff = (compras[i]['fecha'] - compras[i-1]['fecha']).days
                    diferencias.append(diff)
                
                frecuencia_habitual = sum(diferencias) / len(diferencias) if diferencias else 30
                
                # Días desde última compra
                primera_compra = compras[0]['fecha']
                ultima_compra = compras[-1]['fecha']
                dias_sin_comprar = (hoy - ultima_compra).days
                
                # Total histórico
                total_historico = sum(c['monto'] for c in compras)
                
                # Calcular riesgo de churn
                if frecuencia_habitual > 0:
                    ratio = dias_sin_comprar / frecuencia_habitual
                    if ratio > 1.5:
                        # Cliente está tardando más de lo habitual
                        riesgo = min(100, 50 + (ratio - 1.5) * 25)
                        
                        # Determinar acción
                        if riesgo > 80:
                            accion = "URGENTE: Llamar al cliente inmediatamente"
                        elif riesgo > 60:
                            accion = "Enviar cupón de descuento personalizado"
                        else:
                            accion = "Enviar recordatorio amigable"
                        
                        # Calcular valor potencial perdido (promedio mensual * 6 meses)
                        meses_historico = max(1, (datetime.now() - primera_compra).days / 30)
                        promedio_mensual = total_historico / meses_historico
                        valor_perdido = promedio_mensual * 6  # Proyección 6 meses
                        
                        predicciones.append(PrediccionChurn(
                            cliente_id=partner_id,
                            cliente_nombre=compras[0]['nombre'],
                            frecuencia_habitual_dias=round(frecuencia_habitual, 1),
                            dias_sin_comprar=dias_sin_comprar,
                            ultima_compra=ultima_compra,
                            total_historico=total_historico,
                            riesgo_churn=round(riesgo, 1),
                            accion_sugerida=accion,
                            valor_potencial_perdido=round(valor_perdido, 2)
                        ))
            
            # Ordenar por riesgo descendente
            predicciones.sort(key=lambda x: x.riesgo_churn, reverse=True)
            
        except Exception as e:
            logger.error(f"Error analizando churn: {e}")
        
        return predicciones[:50]  # Top 50 en riesgo
    
    # ============================================================
    # OPTIMIZACIÓN DE COMPRAS JUST-IN-TIME
    # ============================================================
    
    def calcular_reposicion_jit(self, dias_proyeccion: int = 14) -> List[AlertaReposicion]:
        """
        Calcula necesidades de reposición basado en consumo y tiempos de entrega.
        Just-in-Time: Cuándo y cuánto pedir.
        """
        alertas = []
        
        if not self.odoo or not self.odoo.conectado:
            return alertas
        
        try:
            # Obtener productos con stock
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            quants = self.odoo.search_read('stock.quant',
                [
                    ('location_id.usage', '=', 'internal'),
                    ('quantity', '>', 0)
                ],
                ['product_id', 'quantity', 'location_id'],
                limit=500
            )
            
            # Agrupar stock por producto
            stock_por_producto = defaultdict(float)
            for quant in quants:
                prod_id = quant.get('product_id', [None])[0]
                if prod_id:
                    stock_por_producto[prod_id] += quant.get('quantity', 0)
            
            # Obtener movimientos de salida (últimos 30 días) para calcular consumo
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            movimientos = self.odoo.search_read('stock.move',
                [
                    ('date', '>=', fecha_inicio),
                    ('state', '=', 'done'),
                    ('location_dest_id.usage', '=', 'customer')  # Salidas a cliente
                ],
                ['product_id', 'product_uom_qty', 'date'],
                limit=2000
            )
            
            # Calcular consumo diario por producto
            consumo_por_producto = defaultdict(float)
            for mov in movimientos:
                prod_id = mov.get('product_id', [None])[0]
                if prod_id:
                    consumo_por_producto[prod_id] += mov.get('product_uom_qty', 0)
            
            # Convertir a consumo diario (30 días)
            hoy = datetime.now()
            
            for prod_id, stock_actual in stock_por_producto.items():
                consumo_mensual = consumo_por_producto.get(prod_id, 0)
                consumo_diario = consumo_mensual / 30 if consumo_mensual > 0 else 0
                
                if consumo_diario > 0:
                    dias_cobertura = stock_actual / consumo_diario
                    
                    # Si la cobertura es menor a la proyección, alertar
                    if dias_cobertura < dias_proyeccion:
                        fecha_agotamiento = hoy + timedelta(days=dias_cobertura)
                        cantidad_sugerida = consumo_diario * (dias_proyeccion + 7)  # Pedir para 3 semanas
                        
                        # Determinar urgencia
                        if dias_cobertura < 3:
                            urgencia = 'critica'
                        elif dias_cobertura < 7:
                            urgencia = 'alta'
                        elif dias_cobertura < 10:
                            urgencia = 'media'
                        else:
                            urgencia = 'baja'
                        
                        # Obtener info del producto
                        try:
                            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
                            prod_info = (self.odoo.search_read('product.product', [('id', '=', prod_id)], campos=['name', 'seller_ids'], limite=1) or [{}])[0]
                            proveedor = "Sin proveedor definido"
                            tiempo_entrega = 5
                            
                            alertas.append(AlertaReposicion(
                                producto_id=prod_id,
                                producto_nombre=prod_info.get('name', f'Producto {prod_id}'),
                                stock_actual=round(stock_actual, 2),
                                consumo_diario=round(consumo_diario, 2),
                                dias_cobertura=round(dias_cobertura, 1),
                                fecha_agotamiento=fecha_agotamiento,
                                cantidad_sugerida=round(cantidad_sugerida, 2),
                                proveedor=proveedor,
                                tiempo_entrega_dias=tiempo_entrega,
                                urgencia=urgencia
                            ))
                        except Exception:
                            pass
            
            # Ordenar por urgencia
            orden_urgencia = {'critica': 0, 'alta': 1, 'media': 2, 'baja': 3}
            alertas.sort(key=lambda x: (orden_urgencia.get(x.urgencia, 4), x.dias_cobertura))
            
        except Exception as e:
            logger.error(f"Error calculando reposición JIT: {e}")
        
        return alertas[:50]
    
    # ============================================================
    # ANÁLISIS DE VENTAS MUERTAS / STOCK LENTO
    # ============================================================
    
    def analizar_stock_lento(self, meses_sin_movimiento: int = 3) -> Dict:
        """
        Analiza productos con lento o nulo movimiento.
        Identifica capital detenido.
        """
        resultado = {
            'productos_sin_movimiento': [],
            'valor_total_detenido': 0,
            'recomendaciones': []
        }
        
        if not self.odoo or not self.odoo.conectado:
            return resultado
        
        try:
            fecha_corte = (datetime.now() - timedelta(days=meses_sin_movimiento * 30)).strftime('%Y-%m-%d')
            
            # Obtener todos los productos con stock
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            quants = self.odoo.search_read('stock.quant',
                [
                    ('location_id.usage', '=', 'internal'),
                    ('quantity', '>', 0)
                ],
                ['product_id', 'quantity'],
                limit=1000
            )
            
            # Obtener productos que SÍ tuvieron movimiento
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            movimientos = self.odoo.search_read('stock.move',
                [
                    ('date', '>=', fecha_corte),
                    ('state', '=', 'done'),
                    ('location_dest_id.usage', '=', 'customer')
                ],
                ['product_id'],
                limit=5000
            )
            
            productos_con_movimiento = set()
            for mov in movimientos:
                if mov.get('product_id'):
                    productos_con_movimiento.add(mov.get('product_id')[0])
            
            # Identificar productos sin movimiento
            valor_total = 0
            productos_lentos = []
            
            for quant in quants:
                prod_id = quant.get('product_id', [None])[0]
                if prod_id and prod_id not in productos_con_movimiento:
                    cantidad = quant.get('quantity', 0)
                    
                    # Obtener costo del producto
                    try:
                        # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
                        prod_info = (self.odoo.search_read('product.product', [('id', '=', prod_id)], campos=['name', 'standard_price', 'categ_id'], limite=1) or [{}])[0]
                        costo = prod_info.get('standard_price', 0)
                        valor_detenido = cantidad * costo
                        valor_total += valor_detenido
                        
                        productos_lentos.append({
                            'producto_id': prod_id,
                            'nombre': prod_info.get('name', 'N/A'),
                            'categoria': prod_info.get('categ_id', ['', 'N/A'])[1] if prod_info.get('categ_id') else 'N/A',
                            'cantidad': cantidad,
                            'costo_unitario': costo,
                            'valor_detenido': valor_detenido,
                            'meses_sin_venta': meses_sin_movimiento
                        })
                    except Exception:
                        pass
            
            # Ordenar por valor detenido
            productos_lentos.sort(key=lambda x: x['valor_detenido'], reverse=True)
            
            resultado['productos_sin_movimiento'] = productos_lentos[:50]
            resultado['valor_total_detenido'] = valor_total
            
            # Generar recomendaciones
            if valor_total > 100000:
                resultado['recomendaciones'].append(f"URGENTE: Tienes ${valor_total:,.2f} MXN detenidos en inventario lento")
                resultado['recomendaciones'].append("Considera promociones del 20-30% para liberar liquidez")
            
            if len(productos_lentos) > 20:
                resultado['recomendaciones'].append(f"{len(productos_lentos)} productos sin movimiento en {meses_sin_movimiento} meses")
                resultado['recomendaciones'].append("Evalúa crear una sección de 'Liquidación' o 'Remate'")
            
        except Exception as e:
            logger.error(f"Error analizando stock lento: {e}")
        
        return resultado
    
    def analizar_clientes_olvidados(self, meses_inactivo: int = 3, monto_minimo: float = 10000) -> Dict:
        """
        Identifica clientes que antes compraban mucho y dejaron de hacerlo.
        
        Returns:
            Dict con 'clientes' (lista), 'resumen' (métricas)
        """
        clientes_olvidados = []
        resultado = {
            'clientes': [],
            'resumen': {
                'total_clientes': 0,
                'valor_historico': 0,
                'dias_promedio_inactivos': 0
            }
        }
        
        if not self.odoo or not self.odoo.conectado:
            return resultado
        
        try:
            fecha_corte = (datetime.now() - timedelta(days=meses_inactivo * 30)).strftime('%Y-%m-%d')
            fecha_historica = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # Obtener ventas del último año antes del corte
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            ventas_historicas = self.odoo.search_read('sale.order',
                [
                    ('state', 'in', ['sale', 'done']),
                    ('date_order', '>=', fecha_historica),
                    ('date_order', '<', fecha_corte)
                ],
                ['partner_id', 'amount_total'],
                limit=5000
            )
            
            # Agrupar por cliente
            historico_por_cliente = defaultdict(float)
            for venta in ventas_historicas:
                partner_id = venta.get('partner_id', [None])[0]
                if partner_id:
                    historico_por_cliente[partner_id] += venta.get('amount_total', 0)
            
            # Obtener ventas recientes
            ventas_recientes = self.odoo.search_read('sale.order',
                [
                    ('state', 'in', ['sale', 'done']),
                    ('date_order', '>=', fecha_corte)
                ],
                ['partner_id', 'amount_total'],
                limit=5000
            )
            
            clientes_activos = set()
            for venta in ventas_recientes:
                if venta.get('partner_id'):
                    clientes_activos.add(venta.get('partner_id')[0])
            
            # Identificar clientes olvidados
            for partner_id, monto_historico in historico_por_cliente.items():
                if partner_id not in clientes_activos and monto_historico >= monto_minimo:
                    try:
                        # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
                        partner_info = (self.odoo.search_read('res.partner', [('id', '=', partner_id)], campos=['name', 'email', 'phone', 'user_id'], limite=1) or [{}])[0]
                        
                        clientes_olvidados.append({
                            'cliente_id': partner_id,
                            'nombre': partner_info.get('name', 'N/A'),
                            'email': partner_info.get('email', ''),
                            'telefono': partner_info.get('phone', ''),
                            'vendedor': partner_info.get('user_id', ['', 'N/A'])[1] if partner_info.get('user_id') else 'Sin asignar',
                            'compra_historica': monto_historico,
                            'meses_inactivo': meses_inactivo,
                            'accion': 'Llamar para reactivar relación comercial'
                        })
                    except Exception:
                        pass
            
            # Ordenar por monto histórico
            clientes_olvidados.sort(key=lambda x: x['compra_historica'], reverse=True)
            
            # Limitar a 30 resultados
            clientes_olvidados = clientes_olvidados[:30]
            
            # Calcular resumen
            total_historico = sum(c['compra_historica'] for c in clientes_olvidados)
            
            resultado['clientes'] = clientes_olvidados
            resultado['resumen'] = {
                'total_clientes': len(clientes_olvidados),
                'valor_historico': total_historico,
                'dias_promedio_inactivos': meses_inactivo * 30
            }
            
        except Exception as e:
            logger.error(f"Error analizando clientes olvidados: {e}")
        
        return resultado
    
    # ============================================================
    # SEMÁFORO DE SALUD OPERATIVA
    # ============================================================
    
    def generar_semaforo_salud(self) -> Dict:
        """
        Genera un dashboard tipo semáforo con indicadores de salud.
        """
        semaforo = {
            'fecha_generacion': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'indicadores': {},
            'score_general': 0,
            'estado_general': '',
            'alertas_destacadas': []
        }
        
        indicadores = {}
        total_score = 0
        num_indicadores = 0
        
        if not self.odoo or not self.odoo.conectado:
            semaforo['estado_general'] = 'SIN_CONEXION'
            return semaforo
        
        try:
            # 1. Índice de Error de Captura (pedidos modificados)
            fecha_mes = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            pedidos = self.odoo.search_read('sale.order',
                [('date_order', '>=', fecha_mes), ('state', 'in', ['sale', 'done'])],
                ['name', 'write_date', 'date_order'],
                limit=500
            )
            
            modificados = 0
            for p in pedidos:
                if p.get('date_order') and p.get('write_date'):
                    f1 = datetime.strptime(p['date_order'][:10], '%Y-%m-%d')
                    f2 = datetime.strptime(p['write_date'][:10], '%Y-%m-%d')
                    if (f2 - f1).days > 1:
                        modificados += 1
            
            tasa_error = (modificados / len(pedidos) * 100) if pedidos else 0
            score_captura = max(0, 100 - tasa_error * 5)
            
            indicadores['error_captura'] = {
                'nombre': 'Índice Error de Captura',
                'valor': f'{tasa_error:.1f}%',
                'score': score_captura,
                'estado': 'verde' if score_captura >= 80 else 'amarillo' if score_captura >= 60 else 'rojo',
                'detalle': f'{modificados} de {len(pedidos)} pedidos modificados post-confirmación'
            }
            total_score += score_captura
            num_indicadores += 1
            
            # 2. Stock Negativo
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            stock_neg = self.odoo.contar('stock.quant', [('quantity', '<', 0)])
            score_stock = 100 if stock_neg == 0 else max(0, 100 - stock_neg * 10)
            
            indicadores['stock_negativo'] = {
                'nombre': 'Stock Negativo',
                'valor': str(stock_neg),
                'score': score_stock,
                'estado': 'verde' if stock_neg == 0 else 'rojo',
                'detalle': 'Productos con existencias negativas'
            }
            total_score += score_stock
            num_indicadores += 1
            
            # 3. Facturas con diferencias
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            diferencias = self.odoo.contar('account.move', [
                ('move_type', 'in', ['out_invoice']),
                ('state', '=', 'posted'),
                ('amount_residual', '>', 0),
                ('amount_residual', '<', 10)
            ])
            score_diferencias = max(0, 100 - diferencias * 2)
            
            indicadores['diferencias_centavos'] = {
                'nombre': 'Diferencias de Centavos',
                'valor': str(diferencias),
                'score': score_diferencias,
                'estado': 'verde' if diferencias < 10 else 'amarillo' if diferencias < 30 else 'rojo',
                'detalle': 'Facturas con saldo residual menor a $10'
            }
            total_score += score_diferencias
            num_indicadores += 1
            
            # 4. Cartera Vencida
            facturas_vencidas = self.odoo.contar('account.move', [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('amount_residual', '>', 0),
                ('invoice_date_due', '<', datetime.now().strftime('%Y-%m-%d'))
            ])
            total_facturas = self.odoo.contar('account.move', [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('amount_residual', '>', 0)
            ])
            
            pct_vencido = (facturas_vencidas / total_facturas * 100) if total_facturas else 0
            score_cartera = max(0, 100 - pct_vencido)
            
            indicadores['cartera_vencida'] = {
                'nombre': 'Cartera Vencida',
                'valor': f'{pct_vencido:.1f}%',
                'score': score_cartera,
                'estado': 'verde' if pct_vencido < 20 else 'amarillo' if pct_vencido < 40 else 'rojo',
                'detalle': f'{facturas_vencidas} de {total_facturas} facturas vencidas'
            }
            total_score += score_cartera
            num_indicadores += 1
            
            # 5. Márgenes Saludables
            # Acceso encapsulado via ConectorOdoo.search_read (ARQ-003)
            lineas = self.odoo.search_read('sale.order.line',
                [('order_id.date_order', '>=', fecha_mes), ('order_id.state', 'in', ['sale', 'done'])],
                ['price_unit', 'purchase_price'],
                limit=500
            )
            
            margenes_bajos = 0
            for l in lineas:
                if l.get('purchase_price', 0) > 0 and l.get('price_unit', 0) > 0:
                    margen = ((l['price_unit'] - l['purchase_price']) / l['purchase_price']) * 100
                    if margen < 5:
                        margenes_bajos += 1
            
            pct_malos = (margenes_bajos / len(lineas) * 100) if lineas else 0
            score_margenes = max(0, 100 - pct_malos * 3)
            
            indicadores['margenes_peligrosos'] = {
                'nombre': 'Márgenes Saludables',
                'valor': f'{100 - pct_malos:.1f}%',
                'score': score_margenes,
                'estado': 'verde' if pct_malos < 5 else 'amarillo' if pct_malos < 15 else 'rojo',
                'detalle': f'{margenes_bajos} ventas con margen menor a 5%'
            }
            total_score += score_margenes
            num_indicadores += 1
            
        except Exception as e:
            logger.error(f"Error generando semáforo: {e}")
        
        # Calcular score general
        semaforo['indicadores'] = indicadores
        semaforo['score_general'] = round(total_score / num_indicadores, 1) if num_indicadores > 0 else 0
        
        if semaforo['score_general'] >= 80:
            semaforo['estado_general'] = 'EXCELENTE'
            semaforo['emoji'] = '🟢'
        elif semaforo['score_general'] >= 60:
            semaforo['estado_general'] = 'BUENO'
            semaforo['emoji'] = '🟡'
        elif semaforo['score_general'] >= 40:
            semaforo['estado_general'] = 'REGULAR'
            semaforo['emoji'] = '🟠'
        else:
            semaforo['estado_general'] = 'CRÍTICO'
            semaforo['emoji'] = '🔴'
        
        return semaforo
    
    # ============================================================
    # DIAGNÓSTICO DE ERRORES DE ODOO
    # ============================================================
    
    def diagnosticar_error(self, descripcion_error: str) -> Dict:
        """
        Diagnostica un error de Odoo basado en la descripción.
        Puede ser texto extraído de una imagen o descripción manual.
        """
        diagnostico = {
            'error_detectado': descripcion_error,
            'tipo_error': 'desconocido',
            'causa_probable': '',
            'solucion': '',
            'pasos': [],
            'modulo_afectado': ''
        }
        
        descripcion = descripcion_error.lower()
        
        # Base de conocimiento de errores comunes de Odoo
        errores_conocidos = [
            {
                'patrones': ['periodo cerrado', 'period is closed', 'fecha contable', 'lock date'],
                'tipo': 'Período Contable Cerrado',
                'modulo': 'Contabilidad',
                'causa': 'Estás intentando registrar un movimiento en un período contable que ya fue cerrado',
                'solucion': 'Abrir el período contable o cambiar la fecha del documento',
                'pasos': [
                    '1. Ve a Contabilidad → Configuración → Fechas de Bloqueo',
                    '2. Revisa la "Fecha de Bloqueo para Usuarios" y "Fecha de Bloqueo Fiscal"',
                    '3. Si necesitas modificar un asiento anterior, desbloquea la fecha temporalmente',
                    '4. Realiza la operación y vuelve a bloquear',
                    'Solo usuarios con permisos de Asesor Contable pueden desbloquear'
                ]
            },
            {
                'patrones': ['not enough', 'stock insuficiente', 'insufficient', 'negative stock'],
                'tipo': 'Stock Insuficiente',
                'modulo': 'Inventario',
                'causa': 'No hay suficiente existencia para completar la operación',
                'solucion': 'Verificar stock o ajustar inventario',
                'pasos': [
                    '1. Ve a Inventario → Reportes → Valoración de Inventario',
                    '2. Busca el producto y verifica la existencia real',
                    '3. Si hay diferencia, haz un ajuste de inventario',
                    '4. Inventario → Operaciones → Ajustes de Inventario',
                    '5. Crea un nuevo ajuste y corrige la cantidad'
                ]
            },
            {
                'patrones': ['access denied', 'acceso denegado', 'permission', 'permiso'],
                'tipo': 'Permiso Denegado',
                'modulo': 'Usuarios',
                'causa': 'Tu usuario no tiene permisos para realizar esta acción',
                'solucion': 'Solicitar permisos al administrador',
                'pasos': [
                    '1. Contacta al administrador del sistema',
                    '2. Indica qué operación necesitas realizar',
                    '3. El admin debe ir a Ajustes → Usuarios',
                    '4. Editar tu usuario y ajustar los permisos del módulo',
                    '5. Cerrar sesión y volver a entrar'
                ]
            },
            {
                'patrones': ['already posted', 'ya publicado', 'cannot modify', 'no se puede modificar'],
                'tipo': 'Documento Ya Publicado',
                'modulo': 'Contabilidad/Ventas',
                'causa': 'Estás intentando modificar un documento que ya fue validado/publicado',
                'solucion': 'Cancelar el documento primero o crear una nota de crédito',
                'pasos': [
                    '1. Si necesitas anular, ve al documento y presiona "Cancelar"',
                    '2. Si es una factura, considera crear una Nota de Crédito',
                    '3. Facturación → Notas de Crédito → Crear',
                    '4. Selecciona la factura original y el motivo',
                    '5. Valida la nota de crédito'
                ]
            },
            {
                'patrones': ['duplicate', 'duplicado', 'already exists', 'ya existe', 'unique constraint'],
                'tipo': 'Registro Duplicado',
                'modulo': 'General',
                'causa': 'Estás intentando crear un registro que ya existe (mismo código, nombre, etc.)',
                'solucion': 'Buscar y usar el registro existente o cambiar el identificador',
                'pasos': [
                    '1. Busca el registro existente usando el filtro',
                    '2. Si necesitas uno nuevo, usa un código/nombre diferente',
                    '3. Si el original está archivado, desarchívalo',
                    '4. Filtros → Archivado → Desactivar filtro'
                ]
            },
            {
                'patrones': ['validation error', 'error de validación', 'required field', 'campo requerido', 'obligatorio'],
                'tipo': 'Campo Requerido Faltante',
                'modulo': 'General',
                'causa': 'Falta llenar un campo obligatorio',
                'solucion': 'Completar todos los campos marcados con *',
                'pasos': [
                    '1. Revisa el formulario, los campos con * son obligatorios',
                    '2. Completa los campos faltantes',
                    '3. Si no ves el campo, puede estar en otra pestaña',
                    '4. Revisa todas las pestañas del formulario'
                ]
            },
            {
                'patrones': ['journal', 'diario', 'no journal', 'sin diario'],
                'tipo': 'Diario No Configurado',
                'modulo': 'Contabilidad',
                'causa': 'No hay un diario contable configurado para esta operación',
                'solucion': 'Configurar o seleccionar el diario correcto',
                'pasos': [
                    '1. Ve a Contabilidad → Configuración → Diarios',
                    '2. Verifica que exista un diario para el tipo de operación',
                    '3. Si no existe, créalo con el tipo correcto (Venta, Compra, Banco, etc.)',
                    '4. Asigna las cuentas contables correspondientes'
                ]
            },
            {
                'patrones': ['reconcile', 'conciliar', 'reconciliation', 'balance'],
                'tipo': 'Error de Conciliación',
                'modulo': 'Contabilidad',
                'causa': 'Los montos no cuadran para la conciliación',
                'solucion': 'Verificar montos y aplicar diferencias de cambio si aplica',
                'pasos': [
                    '1. Verifica que los montos coincidan exactamente',
                    '2. Si hay diferencia de centavos, usa "Tolerancia de Pago"',
                    '3. Contabilidad → Configuración → Ajustes → Tolerancia de Pago',
                    '4. Para diferencias mayores, crea un asiento de ajuste'
                ]
            }
        ]
        
        # Buscar coincidencia
        for error in errores_conocidos:
            for patron in error['patrones']:
                if patron in descripcion:
                    diagnostico['tipo_error'] = error['tipo']
                    diagnostico['modulo_afectado'] = error['modulo']
                    diagnostico['causa_probable'] = error['causa']
                    diagnostico['solucion'] = error['solucion']
                    diagnostico['pasos'] = error['pasos']
                    return diagnostico
        
        # Si no se encontró, dar respuesta genérica
        diagnostico['tipo_error'] = 'Error No Catalogado'
        diagnostico['causa_probable'] = 'Este error no está en la base de conocimiento'
        diagnostico['solucion'] = 'Contacta al soporte técnico con el mensaje completo del error'
        diagnostico['pasos'] = [
            '1. Toma captura de pantalla del error completo',
            '2. Anota qué operación estabas realizando',
            '3. Contacta a soporte técnico',
            '4. Mientras tanto, intenta cerrar sesión y volver a entrar'
        ]
        
        return diagnostico


# ============================================================
# GENERADOR DE REPORTES PDF
# ============================================================

class GeneradorReportePDF:
    """Genera reportes PDF de acciones correctivas."""
    
    def __init__(self):
        self.pdf = None
        
    def generar_reporte_auditoria(self, resultado: ResultadoAuditoria, 
                                   filename: str = None) -> str:
        """Genera un PDF con el reporte de auditoría."""
        
        if not FPDF_DISPONIBLE:
            return "Librería FPDF no disponible. Instala con: pip install fpdf2"
        
        if not filename:
            filename = f"auditoria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Crear directorio si no existe
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reportes')
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        pdf = FPDF()
        pdf.add_page()
        
        # Título
        pdf.set_font('Helvetica', 'B', 20)
        pdf.cell(0, 15, 'REPORTE DE AUDITORIA', ln=True, align='C')
        pdf.set_font('Helvetica', '', 12)
        pdf.cell(0, 10, f'Fecha: {resultado.fecha_ejecucion.strftime("%d/%m/%Y %H:%M")}', ln=True, align='C')
        pdf.ln(5)
        
        # Score de Salud
        pdf.set_font('Helvetica', 'B', 16)
        estado_texto = f'{resultado.emoji_estado} Score: {resultado.score_salud:.0f}/100 - {resultado.estado}'
        pdf.cell(0, 12, estado_texto, ln=True, align='C')
        pdf.ln(10)
        
        # Resumen
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'RESUMEN DE HALLAZGOS', ln=True)
        pdf.set_font('Helvetica', '', 11)
        
        pdf.cell(0, 8, f'- Alertas Criticas: {len(resultado.alertas_criticas)}', ln=True)
        pdf.cell(0, 8, f'- Alertas Warning: {len(resultado.alertas_warning)}', ln=True)
        pdf.cell(0, 8, f'- Alertas Info: {len(resultado.alertas_info)}', ln=True)
        pdf.ln(5)
        
        # Alertas Críticas
        if resultado.alertas_criticas:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_fill_color(255, 200, 200)
            pdf.cell(0, 10, 'ALERTAS CRITICAS', ln=True, fill=True)
            pdf.set_font('Helvetica', '', 10)
            
            for i, alerta in enumerate(resultado.alertas_criticas[:20], 1):
                pdf.ln(3)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.multi_cell(0, 6, f'{i}. {alerta.titulo}')
                pdf.set_font('Helvetica', '', 9)
                pdf.multi_cell(0, 5, f'   {alerta.descripcion}')
                pdf.set_font('Helvetica', 'I', 9)
                pdf.multi_cell(0, 5, f'   Accion: {alerta.accion_sugerida}')
        
        # Alertas Warning
        if resultado.alertas_warning:
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_fill_color(255, 255, 200)
            pdf.cell(0, 10, 'ALERTAS DE ADVERTENCIA', ln=True, fill=True)
            pdf.set_font('Helvetica', '', 10)
            
            for i, alerta in enumerate(resultado.alertas_warning[:20], 1):
                pdf.ln(3)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.multi_cell(0, 6, f'{i}. {alerta.titulo}')
                pdf.set_font('Helvetica', '', 9)
                pdf.multi_cell(0, 5, f'   {alerta.descripcion}')
        
        # Recomendaciones
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'RECOMENDACIONES', ln=True)
        pdf.set_font('Helvetica', '', 11)
        
        for rec in resultado.recomendaciones:
            pdf.multi_cell(0, 8, f'* {rec}')
        
        # Guardar
        pdf.output(filepath)
        
        return filepath
    
    def generar_reporte_churn(self, predicciones: List[PrediccionChurn], 
                              filename: str = None) -> str:
        """Genera PDF con análisis de churn."""
        
        if not FPDF_DISPONIBLE:
            return "Librería FPDF no disponible"
        
        if not filename:
            filename = f"churn_clientes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reportes')
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font('Helvetica', 'B', 18)
        pdf.cell(0, 15, 'REPORTE DE RIESGO DE ABANDONO', ln=True, align='C')
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 8, f'Fecha: {datetime.now().strftime("%d/%m/%Y")}', ln=True, align='C')
        pdf.cell(0, 8, f'Total clientes en riesgo: {len(predicciones)}', ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(60, 8, 'Cliente', border=1)
        pdf.cell(30, 8, 'Riesgo', border=1, align='C')
        pdf.cell(40, 8, 'Dias sin compra', border=1, align='C')
        pdf.cell(50, 8, 'Total Historico', border=1, align='C')
        pdf.ln()
        
        pdf.set_font('Helvetica', '', 10)
        for pred in predicciones[:40]:
            nombre = pred.cliente_nombre[:25] if len(pred.cliente_nombre) > 25 else pred.cliente_nombre
            pdf.cell(60, 7, nombre, border=1)
            pdf.cell(30, 7, f'{pred.riesgo_churn:.0f}%', border=1, align='C')
            pdf.cell(40, 7, str(pred.dias_sin_comprar), border=1, align='C')
            pdf.cell(50, 7, f'${pred.total_historico:,.0f}', border=1, align='C')
            pdf.ln()
        
        pdf.output(filepath)
        return filepath
    
    def generar_reporte_reposicion(self, alertas: List[AlertaReposicion], 
                                    filename: str = None) -> str:
        """Genera PDF con plan de reposición."""
        
        if not FPDF_DISPONIBLE:
            return "Librería FPDF no disponible"
        
        if not filename:
            filename = f"reposicion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reportes')
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font('Helvetica', 'B', 18)
        pdf.cell(0, 15, 'PLAN DE REPOSICION DE INVENTARIO', ln=True, align='C')
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 8, f'Fecha: {datetime.now().strftime("%d/%m/%Y")}', ln=True, align='C')
        pdf.ln(10)
        
        # Por urgencia
        urgencias = {'critica': [], 'alta': [], 'media': [], 'baja': []}
        for a in alertas:
            urgencias[a.urgencia].append(a)
        
        for nivel, lista in urgencias.items():
            if lista:
                pdf.set_font('Helvetica', 'B', 14)
                colores = {'critica': (255, 100, 100), 'alta': (255, 180, 100), 
                          'media': (255, 255, 150), 'baja': (200, 255, 200)}
                pdf.set_fill_color(*colores.get(nivel, (255, 255, 255)))
                pdf.cell(0, 10, f'URGENCIA {nivel.upper()}', ln=True, fill=True)
                
                pdf.set_font('Helvetica', '', 10)
                for a in lista[:15]:
                    nombre = a.producto_nombre[:40] if len(a.producto_nombre) > 40 else a.producto_nombre
                    pdf.cell(0, 6, f'* {nombre}', ln=True)
                    pdf.cell(0, 5, f'    Stock: {a.stock_actual:.0f} | Pedir: {a.cantidad_sugerida:.0f} | Se agota: {a.fecha_agotamiento.strftime("%d/%m")}', ln=True)
                pdf.ln(5)
        
        pdf.output(filepath)
        return filepath


# Función de utilidad para uso rápido
def ejecutar_auditoria_rapida(odoo) -> ResultadoAuditoria:
    """Ejecuta una auditoría rápida y retorna el resultado."""
    auditor = AuditoriaInteligente(odoo)
    return auditor.auditoria_nocturna_completa()
