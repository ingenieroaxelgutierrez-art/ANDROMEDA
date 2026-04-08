# ============================================================
# KPIs FINANCIEROS Y MÉTRICAS DE RENDIMIENTO
# Dashboard Ejecutivo para Toma de Decisiones
# ============================================================

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import math

from app.logging_config import get_logger
logger = get_logger("services.analysis.kpis_financieros")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class CategoriaKPI(Enum):
    """Categorías de KPIs empresariales."""
    VENTAS = "ventas"
    RENTABILIDAD = "rentabilidad"
    LIQUIDEZ = "liquidez"
    EFICIENCIA = "eficiencia"
    CRECIMIENTO = "crecimiento"
    RIESGO = "riesgo"


class EstadoKPI(Enum):
    """Estado del KPI respecto a objetivo."""
    EXCELENTE = "excelente"     # >110% del objetivo
    BUENO = "bueno"             # 100-110% del objetivo
    EN_META = "en_meta"         # 90-100% del objetivo
    ATENCION = "atencion"       # 70-90% del objetivo
    CRITICO = "critico"         # <70% del objetivo


@dataclass
class MetricaFinanciera:
    """Métrica financiera con contexto completo."""
    codigo: str
    nombre: str
    valor: float
    unidad: str
    categoria: CategoriaKPI
    estado: EstadoKPI
    objetivo: float
    cumplimiento_porcentaje: float
    tendencia: str  # "up", "down", "stable"
    cambio_periodo: float  # % de cambio vs período anterior
    interpretacion: str
    formula: str
    recomendacion: str
    prioridad_dashboard: int  # 1-10, menor=más importante
    datos_historicos: List[float] = field(default_factory=list)


@dataclass
class DashboardEjecutivo:
    """Dashboard completo para ejecutivos."""
    fecha_generacion: datetime
    periodo: str
    score_general: float
    metricas: List[MetricaFinanciera]
    alertas_criticas: int
    tendencia_general: str
    resumen_ceo: str
    proximas_acciones: List[str]


class KPIsFinancieros:
    """
    Sistema de KPIs Financieros para Dashboard Ejecutivo.
    
    Diseñado con mentalidad de CFO/Controller con 20 años de experiencia.
    Métricas que realmente importan para la toma de decisiones.
    """
    
    # Objetivos estándar (pueden personalizarse por empresa)
    OBJETIVOS = {
        "margen_bruto": 0.35,           # 35%
        "margen_neto": 0.15,            # 15%
        "rotacion_inventario": 6,        # 6 veces al año
        "dias_cobro": 30,               # 30 días
        "dias_pago": 45,                # 45 días
        "ratio_liquidez": 1.5,          # 1.5:1
        "crecimiento_ventas": 0.15,     # 15% anual
        "concentracion_cliente": 0.20,  # 20% máximo
        "tasa_conversion": 0.30,        # 30%
        "ticket_promedio": 5000,        # $5,000
    }
    
    def __init__(self, conector_odoo=None):
        """Inicializar sistema de KPIs."""
        self.odoo = conector_odoo
        self.metricas: List[MetricaFinanciera] = []
        
        print("Sistema de KPIs Financieros inicializado")
    
    def set_conector(self, conector_odoo):
        """Establecer conector Odoo."""
        self.odoo = conector_odoo
    
    # ============================================================
    # GENERACIÓN DE DASHBOARD
    # ============================================================
    
    def generar_dashboard_ejecutivo(self) -> DashboardEjecutivo:
        """
        Generar dashboard ejecutivo completo.
        
        Este es el reporte que un CEO/CFO debería ver cada mañana.
        """
        self.metricas = []
        
        if not self.odoo or not self.odoo.conectado:
            return self._dashboard_vacio()
        
        print("\nGenerando Dashboard Ejecutivo de KPIs...")
        
        # Calcular todas las métricas
        self._calcular_kpis_ventas()
        self._calcular_kpis_rentabilidad()
        self._calcular_kpis_liquidez()
        self._calcular_kpis_eficiencia()
        self._calcular_kpis_riesgo()
        
        # Ordenar por prioridad
        self.metricas.sort(key=lambda x: x.prioridad_dashboard)
        
        # Calcular score general
        score = self._calcular_score_general()
        
        # Determinar tendencia general
        tendencia = self._determinar_tendencia_general()
        
        # Generar resumen para CEO
        resumen = self._generar_resumen_ceo()
        
        # Generar próximas acciones
        acciones = self._generar_proximas_acciones()
        
        # Contar alertas críticas
        alertas = len([m for m in self.metricas if m.estado == EstadoKPI.CRITICO])
        
        return DashboardEjecutivo(
            fecha_generacion=datetime.now(),
            periodo="Mes actual vs anterior",
            score_general=score,
            metricas=self.metricas,
            alertas_criticas=alertas,
            tendencia_general=tendencia,
            resumen_ceo=resumen,
            proximas_acciones=acciones
        )
    
    def _dashboard_vacio(self) -> DashboardEjecutivo:
        """Retornar dashboard vacío cuando no hay conexión."""
        return DashboardEjecutivo(
            fecha_generacion=datetime.now(),
            periodo="N/A",
            score_general=0,
            metricas=[],
            alertas_criticas=0,
            tendencia_general="unknown",
            resumen_ceo="No hay conexión a Odoo para generar el dashboard.",
            proximas_acciones=["Verificar conexión a Odoo"]
        )
    
    # ============================================================
    # KPIs DE VENTAS
    # ============================================================
    
    def _calcular_kpis_ventas(self):
        """Calcular KPIs relacionados con ventas."""
        try:
            hoy = datetime.now()
            inicio_mes = hoy.replace(day=1)
            inicio_mes_anterior = (inicio_mes - timedelta(days=1)).replace(day=1)
            fin_mes_anterior = inicio_mes - timedelta(days=1)
            
            # Datos mes actual
            facturas_actual = self.odoo.buscar_leer(
                'account.move',
                [
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', inicio_mes.strftime('%Y-%m-%d'))
                ],
                ['amount_total', 'partner_id']
            )
            
            # Datos mes anterior
            facturas_anterior = self.odoo.buscar_leer(
                'account.move',
                [
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', inicio_mes_anterior.strftime('%Y-%m-%d')),
                    ('invoice_date', '<=', fin_mes_anterior.strftime('%Y-%m-%d'))
                ],
                ['amount_total', 'partner_id']
            )
            
            ventas_actual = sum(f.get('amount_total', 0) for f in facturas_actual)
            ventas_anterior = sum(f.get('amount_total', 0) for f in facturas_anterior)
            
            # 1. Ventas Totales
            cambio_ventas = ((ventas_actual - ventas_anterior) / ventas_anterior * 100) if ventas_anterior > 0 else 0
            estado = self._determinar_estado_kpi(ventas_actual, ventas_anterior * (1 + self.OBJETIVOS['crecimiento_ventas']/12))
            
            self.metricas.append(MetricaFinanciera(
                codigo="VEN-001",
                nombre="Ventas del Mes",
                valor=ventas_actual,
                unidad="MXN",
                categoria=CategoriaKPI.VENTAS,
                estado=estado,
                objetivo=ventas_anterior * (1 + self.OBJETIVOS['crecimiento_ventas']/12),
                cumplimiento_porcentaje=(ventas_actual / (ventas_anterior * 1.01) * 100) if ventas_anterior > 0 else 0,
                tendencia="up" if cambio_ventas > 0 else "down",
                cambio_periodo=cambio_ventas,
                interpretacion=f"Ventas {'crecen' if cambio_ventas > 0 else 'decrecen'} {abs(cambio_ventas):.1f}% vs mes anterior",
                formula="∑ Facturas de venta del período",
                recomendacion="Mantener momentum" if cambio_ventas > 0 else "Activar campañas comerciales",
                prioridad_dashboard=1
            ))
            
            # 2. Número de Transacciones
            num_actual = len(facturas_actual)
            num_anterior = len(facturas_anterior)
            cambio_trans = ((num_actual - num_anterior) / num_anterior * 100) if num_anterior > 0 else 0
            
            self.metricas.append(MetricaFinanciera(
                codigo="VEN-002",
                nombre="Número de Ventas",
                valor=num_actual,
                unidad="transacciones",
                categoria=CategoriaKPI.VENTAS,
                estado=self._determinar_estado_kpi(num_actual, num_anterior),
                objetivo=num_anterior * 1.05,
                cumplimiento_porcentaje=(num_actual / num_anterior * 100) if num_anterior > 0 else 0,
                tendencia="up" if cambio_trans > 0 else "down",
                cambio_periodo=cambio_trans,
                interpretacion=f"{num_actual} ventas, {cambio_trans:+.1f}% vs anterior",
                formula="Count(Facturas)",
                recomendacion="Aumentar leads" if cambio_trans < 0 else "Mantener captación",
                prioridad_dashboard=3
            ))
            
            # 3. Ticket Promedio
            ticket_actual = ventas_actual / num_actual if num_actual > 0 else 0
            ticket_anterior = ventas_anterior / num_anterior if num_anterior > 0 else 0
            cambio_ticket = ((ticket_actual - ticket_anterior) / ticket_anterior * 100) if ticket_anterior > 0 else 0
            
            self.metricas.append(MetricaFinanciera(
                codigo="VEN-003",
                nombre="Ticket Promedio",
                valor=ticket_actual,
                unidad="MXN",
                categoria=CategoriaKPI.VENTAS,
                estado=self._determinar_estado_kpi(ticket_actual, self.OBJETIVOS['ticket_promedio']),
                objetivo=self.OBJETIVOS['ticket_promedio'],
                cumplimiento_porcentaje=(ticket_actual / self.OBJETIVOS['ticket_promedio'] * 100),
                tendencia="up" if cambio_ticket > 0 else "down",
                cambio_periodo=cambio_ticket,
                interpretacion=f"${ticket_actual:,.2f} por venta, {cambio_ticket:+.1f}% vs anterior",
                formula="Ventas / Transacciones",
                recomendacion="Implementar estrategias de upselling" if ticket_actual < self.OBJETIVOS['ticket_promedio'] else "Excelente valor por cliente",
                prioridad_dashboard=4
            ))
            
            # 4. Clientes Únicos
            clientes_actual_set = []
            for f in facturas_actual:
                partner = f.get('partner_id', 0)
                if isinstance(partner, (list, tuple)) and len(partner) > 0:
                    partner = partner[0]
                if partner and partner not in clientes_actual_set:
                    clientes_actual_set.append(partner)
            clientes_actual = len(clientes_actual_set)
            
            clientes_anterior_set = []
            for f in facturas_anterior:
                partner = f.get('partner_id', 0)
                if isinstance(partner, (list, tuple)) and len(partner) > 0:
                    partner = partner[0]
                if partner and partner not in clientes_anterior_set:
                    clientes_anterior_set.append(partner)
            clientes_anterior = len(clientes_anterior_set)
            cambio_clientes = ((clientes_actual - clientes_anterior) / clientes_anterior * 100) if clientes_anterior > 0 else 0
            
            self.metricas.append(MetricaFinanciera(
                codigo="VEN-004",
                nombre="Clientes Activos",
                valor=clientes_actual,
                unidad="clientes",
                categoria=CategoriaKPI.VENTAS,
                estado=self._determinar_estado_kpi(clientes_actual, clientes_anterior),
                objetivo=clientes_anterior * 1.05,
                cumplimiento_porcentaje=(clientes_actual / clientes_anterior * 100) if clientes_anterior > 0 else 0,
                tendencia="up" if cambio_clientes > 0 else "down",
                cambio_periodo=cambio_clientes,
                interpretacion=f"{clientes_actual} clientes compraron, {cambio_clientes:+.1f}% vs anterior",
                formula="Count(Distinct Partner)",
                recomendacion="Expandir base de clientes" if cambio_clientes < 0 else "Buena retención",
                prioridad_dashboard=5
            ))
        
        except Exception as e:
            logger.error(f"Error en KPIs de ventas: {e}")
    
    # ============================================================
    # KPIs DE RENTABILIDAD
    # ============================================================
    
    def _calcular_kpis_rentabilidad(self):
        """Calcular KPIs de rentabilidad."""
        try:
            inicio_mes = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            
            # Obtener líneas de factura con productos
            lineas = self.odoo.buscar_leer(
                'account.move.line',
                [
                    ('move_id.move_type', '=', 'out_invoice'),
                    ('move_id.state', '=', 'posted'),
                    ('move_id.invoice_date', '>=', inicio_mes),
                    ('product_id', '!=', False)
                ],
                ['price_subtotal', 'quantity', 'product_id'],
                limite=500
            )
            
            if not lineas:
                return
            
            total_venta = sum(l.get('price_subtotal', 0) for l in lineas)
            
            # Obtener costos de productos
            productos_ids = []
            for l in lineas:
                prod_id = l.get('product_id')
                if isinstance(prod_id, (list, tuple)) and len(prod_id) > 0:
                    prod_id = prod_id[0]
                if prod_id and prod_id not in productos_ids:
                    productos_ids.append(prod_id)
            
            productos = self.odoo.buscar_leer(
                'product.product',
                [('id', 'in', productos_ids)],
                ['id', 'standard_price']
            ) if productos_ids else []
            
            costos = {p['id']: p.get('standard_price', 0) for p in productos}
            
            total_costo = 0
            for linea in lineas:
                prod_id = linea.get('product_id')
                if isinstance(prod_id, (list, tuple)) and len(prod_id) > 0:
                    prod_id = prod_id[0]
                qty = linea.get('quantity', 0)
                costo_unit = costos.get(prod_id, 0) if prod_id else 0
                total_costo += qty * costo_unit
            
            # 1. Margen Bruto
            margen_bruto = ((total_venta - total_costo) / total_venta * 100) if total_venta > 0 else 0
            
            self.metricas.append(MetricaFinanciera(
                codigo="REN-001",
                nombre="Margen Bruto",
                valor=margen_bruto,
                unidad="%",
                categoria=CategoriaKPI.RENTABILIDAD,
                estado=self._determinar_estado_kpi(margen_bruto / 100, self.OBJETIVOS['margen_bruto']),
                objetivo=self.OBJETIVOS['margen_bruto'] * 100,
                cumplimiento_porcentaje=(margen_bruto / (self.OBJETIVOS['margen_bruto'] * 100) * 100),
                tendencia="stable",
                cambio_periodo=0,
                interpretacion=f"Por cada $100, quedan ${margen_bruto:.0f} de utilidad bruta",
                formula="(Ventas - Costo) / Ventas × 100",
                recomendacion="Revisar costos y precios" if margen_bruto < 30 else "Margen saludable",
                prioridad_dashboard=2
            ))
            
            # 2. Utilidad Bruta
            utilidad_bruta = total_venta - total_costo
            
            self.metricas.append(MetricaFinanciera(
                codigo="REN-002",
                nombre="Utilidad Bruta",
                valor=utilidad_bruta,
                unidad="MXN",
                categoria=CategoriaKPI.RENTABILIDAD,
                estado=self._determinar_estado_kpi(utilidad_bruta, total_venta * 0.30),
                objetivo=total_venta * 0.35,
                cumplimiento_porcentaje=(utilidad_bruta / (total_venta * 0.30) * 100) if total_venta > 0 else 0,
                tendencia="stable",
                cambio_periodo=0,
                interpretacion=f"Utilidad bruta del mes: ${utilidad_bruta:,.2f}",
                formula="Ventas - Costo de Ventas",
                recomendacion="Maximizar productos de alto margen",
                prioridad_dashboard=3
            ))
        
        except Exception as e:
            logger.error(f"Error en KPIs de rentabilidad: {e}")
    
    # ============================================================
    # KPIs DE LIQUIDEZ
    # ============================================================
    
    def _calcular_kpis_liquidez(self):
        """Calcular KPIs de liquidez y flujo de caja."""
        try:
            # Cuentas por cobrar
            cxc = self.odoo.buscar_leer(
                'account.move',
                [
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial'])
                ],
                ['amount_residual', 'invoice_date', 'invoice_date_due']
            )
            
            total_cxc = sum(f.get('amount_residual', 0) for f in cxc)
            
            # Calcular días promedio de cobro (DSO - Days Sales Outstanding)
            hoy = datetime.now().date()
            dias_acumulados = 0
            facturas_con_dias = 0
            
            for f in cxc:
                fecha_factura = f.get('invoice_date', '')
                if fecha_factura:
                    try:
                        if isinstance(fecha_factura, str):
                            fecha = datetime.strptime(fecha_factura, '%Y-%m-%d').date()
                        else:
                            fecha = fecha_factura
                        dias = (hoy - fecha).days
                        dias_acumulados += dias
                        facturas_con_dias += 1
                    except Exception:
                        pass
            
            dso = dias_acumulados / facturas_con_dias if facturas_con_dias > 0 else 0
            
            # 1. Días de Cobro (DSO)
            self.metricas.append(MetricaFinanciera(
                codigo="LIQ-001",
                nombre="Días de Cobro (DSO)",
                valor=dso,
                unidad="días",
                categoria=CategoriaKPI.LIQUIDEZ,
                estado=self._determinar_estado_kpi(self.OBJETIVOS['dias_cobro'], dso),  # Invertido: menor es mejor
                objetivo=self.OBJETIVOS['dias_cobro'],
                cumplimiento_porcentaje=(self.OBJETIVOS['dias_cobro'] / dso * 100) if dso > 0 else 100,
                tendencia="stable",
                cambio_periodo=0,
                interpretacion=f"En promedio, tardamos {dso:.0f} días en cobrar",
                formula="(CXC / Ventas) × Días del período",
                recomendacion="Acelerar cobranza" if dso > self.OBJETIVOS['dias_cobro'] else "Cobranza eficiente",
                prioridad_dashboard=6
            ))
            
            # 2. Cuentas por Cobrar Total
            self.metricas.append(MetricaFinanciera(
                codigo="LIQ-002",
                nombre="Cuentas por Cobrar",
                valor=total_cxc,
                unidad="MXN",
                categoria=CategoriaKPI.LIQUIDEZ,
                estado=EstadoKPI.EN_META,  # Depende del contexto
                objetivo=0,  # Idealmente 0, pero no realista
                cumplimiento_porcentaje=100,
                tendencia="stable",
                cambio_periodo=0,
                interpretacion=f"${total_cxc:,.2f} pendientes de cobro en {len(cxc)} facturas",
                formula="∑ Saldo de facturas pendientes",
                recomendacion="Gestión activa de cartera" if total_cxc > 100000 else "Nivel manejable",
                prioridad_dashboard=7
            ))
            
            # Cartera vencida
            vencida = 0
            for f in cxc:
                fecha_venc = f.get('invoice_date_due', '')
                if fecha_venc:
                    try:
                        if isinstance(fecha_venc, str):
                            fv = datetime.strptime(fecha_venc, '%Y-%m-%d').date()
                        else:
                            fv = fecha_venc
                        if fv < hoy:
                            vencida += f.get('amount_residual', 0)
                    except Exception:
                        pass
            
            porcentaje_vencido = (vencida / total_cxc * 100) if total_cxc > 0 else 0
            
            # 3. Porcentaje Cartera Vencida
            self.metricas.append(MetricaFinanciera(
                codigo="LIQ-003",
                nombre="Cartera Vencida",
                valor=porcentaje_vencido,
                unidad="%",
                categoria=CategoriaKPI.LIQUIDEZ,
                estado=self._determinar_estado_kpi(20, porcentaje_vencido),  # Invertido
                objetivo=20,
                cumplimiento_porcentaje=(20 / porcentaje_vencido * 100) if porcentaje_vencido > 0 else 100,
                tendencia="up" if porcentaje_vencido > 30 else "stable",
                cambio_periodo=0,
                interpretacion=f"{porcentaje_vencido:.1f}% de CXC está vencido (${vencida:,.2f})",
                formula="CXC Vencida / CXC Total × 100",
                recomendacion="URGENTE: Intensificar cobranza" if porcentaje_vencido > 30 else "Monitorear mensualmente",
                prioridad_dashboard=5 if porcentaje_vencido > 30 else 8
            ))
        
        except Exception as e:
            logger.error(f"Error en KPIs de liquidez: {e}")
    
    # ============================================================
    # KPIs DE EFICIENCIA
    # ============================================================
    
    def _calcular_kpis_eficiencia(self):
        """Calcular KPIs de eficiencia operacional."""
        try:
            # Valor de inventario
            productos = self.odoo.buscar_leer(
                'product.product',
                [('type', '=', 'product'), ('qty_available', '>', 0)],
                ['qty_available', 'standard_price'],
                limite=500
            )
            
            valor_inventario = sum(
                p.get('qty_available', 0) * p.get('standard_price', 0)
                for p in productos
            )
            num_skus = len(productos)
            
            # Calcular rotación (simplificado)
            inicio_mes = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            
            costo_ventas = 0
            lineas = self.odoo.buscar_leer(
                'account.move.line',
                [
                    ('move_id.move_type', '=', 'out_invoice'),
                    ('move_id.state', '=', 'posted'),
                    ('move_id.invoice_date', '>=', inicio_mes),
                    ('product_id', '!=', False)
                ],
                ['quantity', 'product_id'],
                limite=500
            )
            
            productos_ids_eficiencia = []
            for l in lineas:
                prod_id = l.get('product_id')
                if isinstance(prod_id, (list, tuple)) and len(prod_id) > 0:
                    prod_id = prod_id[0]
                if prod_id and prod_id not in productos_ids_eficiencia:
                    productos_ids_eficiencia.append(prod_id)
            
            productos_costo = self.odoo.buscar_leer(
                'product.product',
                [('id', 'in', productos_ids_eficiencia)],
                ['id', 'standard_price']
            ) if productos_ids_eficiencia else []
            
            costos = {p['id']: p.get('standard_price', 0) for p in productos_costo}
            
            for linea in lineas:
                prod_id = linea.get('product_id')
                if isinstance(prod_id, (list, tuple)) and len(prod_id) > 0:
                    prod_id = prod_id[0]
                qty = linea.get('quantity', 0)
                costo_unit = costos.get(prod_id, 0) if prod_id else 0
                costo_ventas += qty * costo_unit
            
            # Rotación mensual (anualizada)
            rotacion = (costo_ventas * 12 / valor_inventario) if valor_inventario > 0 else 0
            
            # 1. Valor de Inventario
            self.metricas.append(MetricaFinanciera(
                codigo="EFI-001",
                nombre="Valor de Inventario",
                valor=valor_inventario,
                unidad="MXN",
                categoria=CategoriaKPI.EFICIENCIA,
                estado=EstadoKPI.EN_META,
                objetivo=valor_inventario,  # No hay objetivo fijo
                cumplimiento_porcentaje=100,
                tendencia="stable",
                cambio_periodo=0,
                interpretacion=f"${valor_inventario:,.2f} en {num_skus} productos",
                formula="∑ (Cantidad × Costo unitario)",
                recomendacion="Optimizar mix de productos" if valor_inventario > 500000 else "Nivel adecuado",
                prioridad_dashboard=9
            ))
            
            # 2. Rotación de Inventario
            self.metricas.append(MetricaFinanciera(
                codigo="EFI-002",
                nombre="Rotación de Inventario",
                valor=rotacion,
                unidad="veces/año",
                categoria=CategoriaKPI.EFICIENCIA,
                estado=self._determinar_estado_kpi(rotacion, self.OBJETIVOS['rotacion_inventario']),
                objetivo=self.OBJETIVOS['rotacion_inventario'],
                cumplimiento_porcentaje=(rotacion / self.OBJETIVOS['rotacion_inventario'] * 100),
                tendencia="stable",
                cambio_periodo=0,
                interpretacion=f"El inventario rota {rotacion:.1f} veces al año",
                formula="Costo de Ventas Anual / Inventario Promedio",
                recomendacion="Aumentar rotación" if rotacion < 4 else "Rotación saludable",
                prioridad_dashboard=10
            ))
            
            # 3. Meses de Inventario
            meses_inventario = 12 / rotacion if rotacion > 0 else 99
            
            self.metricas.append(MetricaFinanciera(
                codigo="EFI-003",
                nombre="Meses de Inventario",
                valor=meses_inventario,
                unidad="meses",
                categoria=CategoriaKPI.EFICIENCIA,
                estado=self._determinar_estado_kpi(3, meses_inventario),  # Invertido: menor es mejor
                objetivo=2,
                cumplimiento_porcentaje=(2 / meses_inventario * 100) if meses_inventario > 0 else 100,
                tendencia="stable",
                cambio_periodo=0,
                interpretacion=f"El inventario actual duraría {meses_inventario:.1f} meses",
                formula="12 / Rotación",
                recomendacion="Liquidar excesos" if meses_inventario > 4 else "Nivel óptimo",
                prioridad_dashboard=11
            ))
        
        except Exception as e:
            logger.error(f"Error en KPIs de eficiencia: {e}")
    
    # ============================================================
    # KPIs DE RIESGO
    # ============================================================
    
    def _calcular_kpis_riesgo(self):
        """Calcular KPIs de riesgo empresarial."""
        try:
            # Concentración de clientes
            inicio_mes = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            
            facturas = self.odoo.buscar_leer(
                'account.move',
                [
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', inicio_mes)
                ],
                ['amount_total', 'partner_id']
            )
            
            if not facturas:
                return
            
            ventas_por_cliente = {}
            total_ventas = 0
            
            for f in facturas:
                partner = f.get('partner_id', [0, 'Cliente'])
                partner_id = partner[0] if isinstance(partner, list) else partner
                partner_nombre = partner[1] if isinstance(partner, list) else str(partner)
                monto = f.get('amount_total', 0)
                
                if partner_id not in ventas_por_cliente:
                    ventas_por_cliente[partner_id] = {'nombre': partner_nombre, 'total': 0}
                
                ventas_por_cliente[partner_id]['total'] += monto
                total_ventas += monto
            
            # Calcular concentración del top 1 cliente
            if ventas_por_cliente and total_ventas > 0:
                top_cliente = max(ventas_por_cliente.values(), key=lambda x: x['total'])
                concentracion_top1 = (top_cliente['total'] / total_ventas * 100)
                
                # 1. Concentración Top Cliente
                self.metricas.append(MetricaFinanciera(
                    codigo="RIE-001",
                    nombre="Concentración Top Cliente",
                    valor=concentracion_top1,
                    unidad="%",
                    categoria=CategoriaKPI.RIESGO,
                    estado=self._determinar_estado_kpi(self.OBJETIVOS['concentracion_cliente'] * 100, concentracion_top1),
                    objetivo=self.OBJETIVOS['concentracion_cliente'] * 100,
                    cumplimiento_porcentaje=(self.OBJETIVOS['concentracion_cliente'] * 100 / concentracion_top1 * 100) if concentracion_top1 > 0 else 100,
                    tendencia="up" if concentracion_top1 > 30 else "stable",
                    cambio_periodo=0,
                    interpretacion=f"'{top_cliente['nombre']}' representa {concentracion_top1:.1f}% de ventas",
                    formula="Ventas Top Cliente / Ventas Totales × 100",
                    recomendacion="Diversificar cartera" if concentracion_top1 > 25 else "Buena diversificación",
                    prioridad_dashboard=6
                ))
                
                # 2. Número de Clientes
                num_clientes = len(ventas_por_cliente)
                
                self.metricas.append(MetricaFinanciera(
                    codigo="RIE-002",
                    nombre="Diversificación de Clientes",
                    valor=num_clientes,
                    unidad="clientes",
                    categoria=CategoriaKPI.RIESGO,
                    estado=EstadoKPI.BUENO if num_clientes > 10 else EstadoKPI.ATENCION,
                    objetivo=20,
                    cumplimiento_porcentaje=(num_clientes / 20 * 100),
                    tendencia="stable",
                    cambio_periodo=0,
                    interpretacion=f"Ventas distribuidas entre {num_clientes} clientes",
                    formula="Count(Distinct Cliente con ventas)",
                    recomendacion="Captar más clientes" if num_clientes < 10 else "Base diversificada",
                    prioridad_dashboard=12
                ))
        
        except Exception as e:
            logger.error(f"Error en KPIs de riesgo: {e}")
    
    # ============================================================
    # FUNCIONES AUXILIARES
    # ============================================================
    
    def _determinar_estado_kpi(self, valor: float, objetivo: float) -> EstadoKPI:
        """Determinar estado del KPI respecto al objetivo."""
        if objetivo == 0:
            return EstadoKPI.EN_META
        
        ratio = valor / objetivo
        
        if ratio >= 1.10:
            return EstadoKPI.EXCELENTE
        elif ratio >= 1.00:
            return EstadoKPI.BUENO
        elif ratio >= 0.90:
            return EstadoKPI.EN_META
        elif ratio >= 0.70:
            return EstadoKPI.ATENCION
        else:
            return EstadoKPI.CRITICO
    
    def _calcular_score_general(self) -> float:
        """Calcular score general del dashboard (0-100)."""
        if not self.metricas:
            return 0
        
        score = 0
        pesos = 0
        
        estado_puntos = {
            EstadoKPI.EXCELENTE: 100,
            EstadoKPI.BUENO: 85,
            EstadoKPI.EN_META: 75,
            EstadoKPI.ATENCION: 50,
            EstadoKPI.CRITICO: 20
        }
        
        for metrica in self.metricas:
            peso = 1 / metrica.prioridad_dashboard  # Mayor prioridad = menor número = mayor peso
            score += estado_puntos[metrica.estado] * peso
            pesos += peso
        
        return score / pesos if pesos > 0 else 0
    
    def _determinar_tendencia_general(self) -> str:
        """Determinar tendencia general del negocio."""
        ups = sum(1 for m in self.metricas if m.tendencia == "up")
        downs = sum(1 for m in self.metricas if m.tendencia == "down")
        
        if ups > downs + 2:
            return "positive"
        elif downs > ups + 2:
            return "negative"
        else:
            return "stable"
    
    def _generar_resumen_ceo(self) -> str:
        """Generar resumen ejecutivo para CEO."""
        score = self._calcular_score_general()
        tendencia = self._determinar_tendencia_general()
        criticos = [m for m in self.metricas if m.estado == EstadoKPI.CRITICO]
        
        if score >= 80:
            estado = "EXCELENTE"
            emoji = "🟢"
        elif score >= 60:
            estado = "BUENO"
            emoji = "🟡"
        elif score >= 40:
            estado = "ATENCIÓN REQUERIDA"
            emoji = "🟠"
        else:
            estado = "CRÍTICO"
            emoji = "🔴"
        
        resumen = f"""
{emoji} **ESTADO GENERAL: {estado}** (Score: {score:.0f}/100)

**Tendencia:** {'📈 Positiva' if tendencia == 'positive' else '📉 Negativa' if tendencia == 'negative' else '➡️ Estable'}
"""
        
        # Top KPI destacado
        ventas_kpi = next((m for m in self.metricas if m.codigo == "VEN-001"), None)
        if ventas_kpi:
            resumen += f"\n**Ventas del Mes:** ${ventas_kpi.valor:,.2f} ({ventas_kpi.cambio_periodo:+.1f}%)"
        
        margen_kpi = next((m for m in self.metricas if m.codigo == "REN-001"), None)
        if margen_kpi:
            resumen += f"\n**Margen Bruto:** {margen_kpi.valor:.1f}%"
        
        if criticos:
            resumen += f"\n\n **{len(criticos)} KPI(s) en estado CRÍTICO requieren atención inmediata.**"
        
        return resumen
    
    def _generar_proximas_acciones(self) -> List[str]:
        """Generar lista de próximas acciones prioritarias."""
        acciones = []
        
        criticos = [m for m in self.metricas if m.estado == EstadoKPI.CRITICO]
        atencion = [m for m in self.metricas if m.estado == EstadoKPI.ATENCION]
        
        for m in criticos[:3]:
            acciones.append(f"🔴 {m.nombre}: {m.recomendacion}")
        
        for m in atencion[:2]:
            acciones.append(f"🟡 {m.nombre}: {m.recomendacion}")
        
        if not acciones:
            acciones.append("Todos los KPIs están en objetivo. Mantener estrategia actual.")
        
        return acciones
    
    # ============================================================
    # FORMATEO PARA INTERFAZ
    # ============================================================
    
    def formatear_dashboard_markdown(self, dashboard: DashboardEjecutivo) -> str:
        """Formatear dashboard en Markdown."""
        estado_emoji = {
            EstadoKPI.EXCELENTE: "🟢",
            EstadoKPI.BUENO: "🟢",
            EstadoKPI.EN_META: "🟡",
            EstadoKPI.ATENCION: "🟠",
            EstadoKPI.CRITICO: "🔴"
        }
        
        tendencia_emoji = {
            "up": "📈",
            "down": "📉",
            "stable": "➡️"
        }
        
        md = f"""# DASHBOARD EJECUTIVO DE KPIs
*Generado: {dashboard.fecha_generacion.strftime('%Y-%m-%d %H:%M')}*

---

{dashboard.resumen_ceo}

---

## MÉTRICAS CLAVE

| KPI | Valor | Estado | Tendencia | vs Objetivo | Acción |
|-----|-------|--------|-----------|-------------|--------|
"""
        
        for m in dashboard.metricas:
            estado = estado_emoji[m.estado]
            tendencia = tendencia_emoji.get(m.tendencia, "➡️")
            
            if m.unidad == "MXN":
                valor_str = f"${m.valor:,.0f}"
            elif m.unidad == "%":
                valor_str = f"{m.valor:.1f}%"
            else:
                valor_str = f"{m.valor:,.0f} {m.unidad}"
            
            md += f"| {m.nombre} | {valor_str} | {estado} | {tendencia} {m.cambio_periodo:+.1f}% | {m.cumplimiento_porcentaje:.0f}% | {m.recomendacion[:40]}... |\n"
        
        md += """
---

## PRÓXIMAS ACCIONES

"""
        
        for i, accion in enumerate(dashboard.proximas_acciones, 1):
            md += f"{i}. {accion}\n"
        
        md += f"""
---

## DETALLES POR CATEGORÍA

"""
        
        # Agrupar por categoría
        categorias = {}
        for m in dashboard.metricas:
            cat = m.categoria.value.title()
            if cat not in categorias:
                categorias[cat] = []
            categorias[cat].append(m)
        
        for cat, metricas in categorias.items():
            md += f"### {cat}\n\n"
            for m in metricas:
                md += f"- **{m.nombre}:** {m.interpretacion}\n"
            md += "\n"
        
        md += f"""---

**Score General:** {dashboard.score_general:.0f}/100
**Alertas Críticas:** {dashboard.alertas_criticas}
**Tendencia:** {dashboard.tendencia_general.title()}

---
*ANDROMEDA - Dashboard de Business Intelligence*
"""
        
        return md


# ============================================================
# FUNCIÓN DE PRUEBA
# ============================================================

def main():
    """Probar el sistema de KPIs."""
    print("=" * 60)
    print("Probando Sistema de KPIs Financieros")
    print("=" * 60)
    
    from models.conector_odoo import ConectorOdoo
    
    odoo = ConectorOdoo()
    if not odoo.conectado:
        print("No se pudo conectar a Odoo")
        return
    
    kpis = KPIsFinancieros(odoo)
    dashboard = kpis.generar_dashboard_ejecutivo()
    
    print(kpis.formatear_dashboard_markdown(dashboard))


if __name__ == "__main__":
    main()
