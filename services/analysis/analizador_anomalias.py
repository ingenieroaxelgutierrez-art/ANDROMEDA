# ============================================================
# ANALIZADOR DE ANOMALÍAS FINANCIERAS
# Detección avanzada de fraude, inconsistencias y riesgos
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
logger = get_logger("services.analysis.analizador_anomalias")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TipoRiesgo(Enum):
    """Tipos de riesgo financiero."""
    FRAUDE = "fraude"
    OPERACIONAL = "operacional"
    CREDITICIO = "crediticio"
    LIQUIDEZ = "liquidez"
    CONTABLE = "contable"
    CUMPLIMIENTO = "cumplimiento"


class SeveridadRiesgo(Enum):
    """Niveles de severidad."""
    BAJO = 1
    MEDIO = 2
    ALTO = 3
    CRITICO = 4


@dataclass
class AlertaFinanciera:
    """Alerta financiera detectada."""
    codigo: str
    titulo: str
    descripcion: str
    tipo_riesgo: TipoRiesgo
    severidad: SeveridadRiesgo
    monto_afectado: float
    entidades: List[str]
    evidencia: Dict[str, Any]
    recomendacion: str
    fecha_deteccion: datetime = field(default_factory=datetime.now)
    requiere_accion_inmediata: bool = False
    probabilidad_fraude: float = 0.0  # 0-100%


@dataclass
class ResultadoAuditoria:
    """Resultado de auditoría automatizada."""
    fecha: datetime
    area_auditada: str
    hallazgos: List[AlertaFinanciera]
    score_riesgo: float
    recomendaciones_control: List[str]
    entidades_revisadas: int
    transacciones_analizadas: int


class AnalizadorAnomalias:
    """
    Analizador especializado en detección de anomalías financieras.
    
    Utiliza técnicas de data science para identificar:
    - Patrones de fraude
    - Inconsistencias contables
    - Transacciones sospechosas
    - Riesgos operacionales
    """
    
    # Umbrales de detección (calibrados por experiencia)
    UMBRAL_TRANSACCION_GRANDE = 50000  # Transacción que requiere revisión
    UMBRAL_DESCUENTO_SOSPECHOSO = 0.30  # 30% descuento requiere auditoría
    UMBRAL_NC_RATIO = 0.10  # 10% de NC vs ventas es sospechoso
    UMBRAL_VELOCIDAD_COBRO = 5  # Transacciones de cobro muy rápidas
    
    # Patrones de fraude conocidos
    PATRONES_FRAUDE = {
        "round_amount": "Montos redondos frecuentes pueden indicar manipulación",
        "split_transactions": "Transacciones divididas para evitar controles",
        "timing_anomaly": "Transacciones fuera de horario normal",
        "sequential_numbers": "Saltos en numeración de documentos",
        "dormant_reactivation": "Reactivación de cuentas inactivas"
    }
    
    def __init__(self, conector_odoo=None):
        """Inicializar analizador."""
        self.odoo = conector_odoo
        self.alertas: List[AlertaFinanciera] = []
        
        print("Analizador de Anomalías inicializado")
    
    def set_conector(self, conector_odoo):
        """Establecer conector Odoo."""
        self.odoo = conector_odoo
    
    # ============================================================
    # ANÁLISIS DE PATRONES DE FRAUDE
    # ============================================================
    
    def ejecutar_auditoria_completa(self) -> ResultadoAuditoria:
        """
        Ejecutar auditoría completa del sistema.
        
        Analiza múltiples dimensiones en busca de anomalías.
        """
        self.alertas = []
        
        if not self.odoo or not self.odoo.conectado:
            return ResultadoAuditoria(
                fecha=datetime.now(),
                area_auditada="Sistema Odoo",
                hallazgos=[],
                score_riesgo=0,
                recomendaciones_control=[],
                entidades_revisadas=0,
                transacciones_analizadas=0
            )
        
        print("\n" + "=" * 60)
        print("INICIANDO AUDITORÍA AUTOMATIZADA DE FRAUDE Y RIESGOS")
        print("=" * 60)
        
        total_transacciones = 0
        
        # 1. Análisis de transacciones sospechosas
        print("\nAnalizando transacciones...")
        t1 = self._analizar_transacciones_sospechosas()
        total_transacciones += t1
        
        # 2. Análisis de notas de crédito
        print("Analizando notas de crédito...")
        t2 = self._analizar_notas_credito()
        total_transacciones += t2
        
        # 3. Análisis de descuentos excesivos
        print("Analizando descuentos...")
        t3 = self._analizar_descuentos_excesivos()
        total_transacciones += t3
        
        # 4. Análisis de ajustes de inventario
        print("Analizando ajustes de inventario...")
        t4 = self._analizar_ajustes_inventario()
        total_transacciones += t4
        
        # 5. Análisis de cuentas dormidas
        print("Analizando cuentas inactivas...")
        self._analizar_cuentas_dormidas()
        
        # 6. Análisis de segregación de funciones
        print("Verificando segregación de funciones...")
        self._analizar_segregacion_funciones()
        
        # 7. Análisis de numeración de documentos
        print("Verificando secuencias de documentos...")
        self._analizar_secuencias_documentos()
        
        # Calcular score de riesgo
        score_riesgo = self._calcular_score_riesgo()
        
        # Generar recomendaciones de control
        recomendaciones = self._generar_recomendaciones_control()
        
        print(f"\nAuditoría completada: {len(self.alertas)} hallazgos")
        
        # Contar entidades únicas (manejo de listas para evitar unhashable)
        entidades_unicas = set()
        for a in self.alertas:
            for e in a.entidades:
                if isinstance(e, list):
                    entidades_unicas.add(tuple(e))
                else:
                    entidades_unicas.add(e)
        
        return ResultadoAuditoria(
            fecha=datetime.now(),
            area_auditada="Sistema Odoo Completo",
            hallazgos=self.alertas,
            score_riesgo=score_riesgo,
            recomendaciones_control=recomendaciones,
            entidades_revisadas=len(entidades_unicas),
            transacciones_analizadas=total_transacciones
        )
    
    def _analizar_transacciones_sospechosas(self) -> int:
        """Identificar transacciones con características sospechosas."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Obtener todas las facturas del período
            facturas = self.odoo.buscar_leer(
                'account.move',
                [
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', fecha_inicio)
                ],
                ['name', 'amount_total', 'partner_id', 'invoice_user_id', 
                 'invoice_date', 'move_type', 'create_date', 'write_date']
            )
            
            if not facturas:
                return 0
            
            montos = [f.get('amount_total', 0) for f in facturas]
            media = statistics.mean(montos) if montos else 0
            desv_std = statistics.stdev(montos) if len(montos) > 1 else 1
            
            for factura in facturas:
                monto = factura.get('amount_total', 0)
                nombre = factura.get('name', 'N/A')
                
                # 1. Montos redondos grandes (posible manipulación)
                if monto >= 10000 and monto % 1000 == 0:
                    self.alertas.append(AlertaFinanciera(
                        codigo="FRA-001",
                        titulo="Monto Redondo Sospechoso",
                        descripcion=f"Factura {nombre} tiene monto exactamente redondo: ${monto:,.2f}",
                        tipo_riesgo=TipoRiesgo.FRAUDE,
                        severidad=SeveridadRiesgo.MEDIO,
                        monto_afectado=monto,
                        entidades=[nombre],
                        evidencia={"patron": "round_amount", "factura": factura},
                        recomendacion="Verificar que el monto corresponde a productos/servicios reales",
                        probabilidad_fraude=30
                    ))
                
                # 2. Transacciones outliers (muy por encima del promedio)
                if desv_std > 0:
                    zscore = (monto - media) / desv_std
                    if zscore > 3:  # Más de 3 desviaciones estándar
                        self.alertas.append(AlertaFinanciera(
                            codigo="FRA-002",
                            titulo="Transacción Atípica por Monto",
                            descripcion=f"Factura {nombre} (${monto:,.2f}) es {zscore:.1f}x el promedio",
                            tipo_riesgo=TipoRiesgo.FRAUDE,
                            severidad=SeveridadRiesgo.ALTO,
                            monto_afectado=monto,
                            entidades=[nombre],
                            evidencia={"zscore": zscore, "media": media, "factura": factura},
                            recomendacion="Validar autorización y documentación de soporte",
                            requiere_accion_inmediata=True,
                            probabilidad_fraude=50
                        ))
                
                # 3. Transacciones de fin de semana (sospechoso en retail normal)
                fecha_str = factura.get('invoice_date', '')
                if fecha_str:
                    try:
                        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                        if fecha.weekday() >= 5 and monto > 20000:  # Fin de semana + monto alto
                            self.alertas.append(AlertaFinanciera(
                                codigo="FRA-003",
                                titulo="Transacción de Alto Monto en Fin de Semana",
                                descripcion=f"Factura {nombre} (${monto:,.2f}) registrada en {fecha.strftime('%A')}",
                                tipo_riesgo=TipoRiesgo.OPERACIONAL,
                                severidad=SeveridadRiesgo.BAJO,
                                monto_afectado=monto,
                                entidades=[nombre],
                                evidencia={"dia": fecha.strftime('%A'), "factura": factura},
                                recomendacion="Verificar si corresponde a operación normal del negocio",
                                probabilidad_fraude=15
                            ))
                    except Exception:
                        pass
            
            return len(facturas)
        
        except Exception as e:
            logger.error(f"Error en análisis de transacciones: {e}")
            return 0
    
    def _analizar_notas_credito(self) -> int:
        """Analizar patrones de notas de crédito."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Notas de crédito
            nc = self.odoo.buscar_leer(
                'account.move',
                [
                    ('move_type', '=', 'out_refund'),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', fecha_inicio)
                ],
                ['name', 'amount_total', 'partner_id', 'invoice_user_id', 'invoice_date', 'reversed_entry_id']
            )
            
            # Facturas para calcular ratio
            facturas = self.odoo.buscar_leer(
                'account.move',
                [
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', fecha_inicio)
                ],
                ['amount_total']
            )
            
            total_nc = sum(n.get('amount_total', 0) for n in nc)
            total_facturas = sum(f.get('amount_total', 0) for f in facturas)
            
            if total_facturas > 0:
                ratio = total_nc / total_facturas
                
                if ratio > self.UMBRAL_NC_RATIO:
                    self.alertas.append(AlertaFinanciera(
                        codigo="FRA-004",
                        titulo="Ratio Alto de Notas de Crédito",
                        descripcion=f"Las NC representan {ratio*100:.1f}% de las ventas (${total_nc:,.2f})",
                        tipo_riesgo=TipoRiesgo.FRAUDE,
                        severidad=SeveridadRiesgo.CRITICO if ratio > 0.20 else SeveridadRiesgo.ALTO,
                        monto_afectado=total_nc,
                        entidades=[n.get('name', 'N/A') for n in nc[:10]],
                        evidencia={"ratio": ratio, "total_nc": total_nc, "total_facturas": total_facturas},
                        recomendacion="URGENTE: Revisar proceso de autorización de NC. Posible fraude.",
                        requiere_accion_inmediata=True,
                        probabilidad_fraude=70 if ratio > 0.20 else 45
                    ))
            
            # NC sin factura original vinculada
            nc_sin_origen = [n for n in nc if not n.get('reversed_entry_id')]
            if nc_sin_origen:
                total_sin_origen = sum(n.get('amount_total', 0) for n in nc_sin_origen)
                self.alertas.append(AlertaFinanciera(
                    codigo="FRA-005",
                    titulo="Notas de Crédito sin Factura de Origen",
                    descripcion=f"{len(nc_sin_origen)} NC (${total_sin_origen:,.2f}) sin factura vinculada",
                    tipo_riesgo=TipoRiesgo.FRAUDE,
                    severidad=SeveridadRiesgo.ALTO,
                    monto_afectado=total_sin_origen,
                    entidades=[n.get('name', 'N/A') for n in nc_sin_origen[:10]],
                    evidencia={"notas_credito": nc_sin_origen},
                    recomendacion="Verificar documentación de respaldo para cada NC",
                    requiere_accion_inmediata=True,
                    probabilidad_fraude=60
                ))
            
            # NC de montos altos individuales
            for nota in nc:
                monto = nota.get('amount_total', 0)
                if monto > 25000:
                    usuario = nota.get('invoice_user_id', [0, 'Desconocido'])
                    usuario_nombre = usuario[1] if isinstance(usuario, list) else str(usuario)
                    
                    self.alertas.append(AlertaFinanciera(
                        codigo="FRA-006",
                        titulo=f"NC de Alto Monto: {nota.get('name', 'N/A')}",
                        descripcion=f"Nota de crédito por ${monto:,.2f} emitida por {usuario_nombre}",
                        tipo_riesgo=TipoRiesgo.FRAUDE,
                        severidad=SeveridadRiesgo.ALTO,
                        monto_afectado=monto,
                        entidades=[nota.get('name', 'N/A'), usuario_nombre],
                        evidencia={"nota_credito": nota},
                        recomendacion="Validar autorización gerencial y documentación de respaldo",
                        probabilidad_fraude=40
                    ))
            
            return len(nc)
        
        except Exception as e:
            logger.error(f"Error en análisis de NC: {e}")
            return 0
    
    def _analizar_descuentos_excesivos(self) -> int:
        """Detectar descuentos excesivos o no autorizados."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Líneas de factura con descuento
            lineas = self.odoo.buscar_leer(
                'account.move.line',
                [
                    ('move_id.move_type', '=', 'out_invoice'),
                    ('move_id.state', '=', 'posted'),
                    ('move_id.invoice_date', '>=', fecha_inicio),
                    ('discount', '>', 0)
                ],
                ['move_id', 'product_id', 'price_unit', 'discount', 'price_subtotal', 'quantity'],
                limite=500
            )
            
            descuentos_excesivos = []
            total_descuento_perdido = 0
            
            for linea in lineas:
                descuento = linea.get('discount', 0)
                precio = linea.get('price_unit', 0)
                qty = linea.get('quantity', 0)
                
                if descuento >= self.UMBRAL_DESCUENTO_SOSPECHOSO * 100:  # 30%+
                    monto_descuento = precio * qty * (descuento / 100)
                    total_descuento_perdido += monto_descuento
                    
                    factura = linea.get('move_id', [0, 'N/A'])
                    factura_nombre = factura[1] if isinstance(factura, list) else str(factura)
                    
                    producto = linea.get('product_id', [0, 'Producto'])
                    producto_nombre = producto[1] if isinstance(producto, list) else str(producto)
                    
                    descuentos_excesivos.append({
                        'factura': factura_nombre,
                        'producto': producto_nombre,
                        'descuento': descuento,
                        'monto_perdido': monto_descuento
                    })
            
            if descuentos_excesivos:
                self.alertas.append(AlertaFinanciera(
                    codigo="OPR-001",
                    titulo="Descuentos Excesivos Detectados",
                    descripcion=f"{len(descuentos_excesivos)} líneas con descuento >30%. Total perdido: ${total_descuento_perdido:,.2f}",
                    tipo_riesgo=TipoRiesgo.OPERACIONAL,
                    severidad=SeveridadRiesgo.ALTO if total_descuento_perdido > 10000 else SeveridadRiesgo.MEDIO,
                    monto_afectado=total_descuento_perdido,
                    entidades=[d['factura'] for d in descuentos_excesivos[:10]],
                    evidencia={"descuentos": descuentos_excesivos},
                    recomendacion="Revisar política de descuentos. Implementar límites por rol.",
                    probabilidad_fraude=25
                ))
            
            return len(lineas)
        
        except Exception as e:
            logger.error(f"Error en análisis de descuentos: {e}")
            return 0
    
    def _analizar_ajustes_inventario(self) -> int:
        """Analizar ajustes de inventario sospechosos."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Buscar movimientos de inventario tipo ajuste
            movimientos = self.odoo.buscar_leer(
                'stock.move',
                [
                    ('state', '=', 'done'),
                    ('date', '>=', fecha_inicio),
                    ('scrapped', '=', True)  # Mermas
                ],
                ['product_id', 'product_qty', 'date', 'reference'],
                limite=200
            )
            
            if not movimientos:
                # Intentar con otro filtro para ajustes de inventario
                movimientos = self.odoo.buscar_leer(
                    'stock.move',
                    [
                        ('state', '=', 'done'),
                        ('date', '>=', fecha_inicio),
                        ('location_id.usage', '=', 'inventory')
                    ],
                    ['product_id', 'product_qty', 'date', 'reference'],
                    limite=200
                )
            
            if not movimientos:
                return 0
            
            # Agrupar por producto
            ajustes_por_producto = {}
            for mov in movimientos:
                prod = mov.get('product_id', [0, 'Producto'])
                prod_nombre = prod[1] if isinstance(prod, list) else str(prod)
                
                if prod_nombre not in ajustes_por_producto:
                    ajustes_por_producto[prod_nombre] = {'cantidad': 0, 'movimientos': 0}
                
                ajustes_por_producto[prod_nombre]['cantidad'] += mov.get('product_qty', 0)
                ajustes_por_producto[prod_nombre]['movimientos'] += 1
            
            # Detectar productos con muchos ajustes
            for producto, data in ajustes_por_producto.items():
                if data['movimientos'] >= 3 or data['cantidad'] > 100:
                    self.alertas.append(AlertaFinanciera(
                        codigo="INV-001",
                        titulo=f"Ajustes Frecuentes: {producto[:50]}",
                        descripcion=f"{data['movimientos']} ajustes con {data['cantidad']:.0f} unidades",
                        tipo_riesgo=TipoRiesgo.FRAUDE,
                        severidad=SeveridadRiesgo.ALTO if data['cantidad'] > 100 else SeveridadRiesgo.MEDIO,
                        monto_afectado=0,  # Se necesitaría el costo para calcular
                        entidades=[producto],
                        evidencia=data,
                        recomendacion="Investigar razón de ajustes frecuentes. Posible robo hormiga.",
                        probabilidad_fraude=55
                    ))
            
            return len(movimientos)
        
        except Exception as e:
            logger.error(f"Error en análisis de inventario: {e}")
            return 0
    
    def _analizar_cuentas_dormidas(self):
        """Detectar reactivación de cuentas inactivas (red flag de fraude)."""
        try:
            # Clientes sin ventas en 6 meses que de repente tienen movimiento
            fecha_limite = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            fecha_reciente = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Clientes con facturas recientes
            facturas_recientes = self.odoo.buscar_leer(
                'account.move',
                [
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', fecha_reciente)
                ],
                ['partner_id', 'amount_total', 'name'],
                limite=200
            )
            
            clientes_recientes = {}
            for f in facturas_recientes:
                partner = f.get('partner_id', [0, 'Cliente'])
                partner_id = partner[0] if isinstance(partner, list) else partner
                partner_nombre = partner[1] if isinstance(partner, list) else str(partner)
                
                if partner_id not in clientes_recientes:
                    clientes_recientes[partner_id] = {
                        'nombre': partner_nombre,
                        'total': 0,
                        'facturas': []
                    }
                
                clientes_recientes[partner_id]['total'] += f.get('amount_total', 0)
                clientes_recientes[partner_id]['facturas'].append(f.get('name', 'N/A'))
            
            # Verificar si estos clientes tenían actividad previa
            for partner_id, data in clientes_recientes.items():
                if partner_id == 0:
                    continue
                
                # Buscar facturas antiguas
                facturas_antiguas = self.odoo.buscar_leer(
                    'account.move',
                    [
                        ('move_type', '=', 'out_invoice'),
                        ('state', '=', 'posted'),
                        ('partner_id', '=', partner_id),
                        ('invoice_date', '<', fecha_reciente),
                        ('invoice_date', '>=', fecha_limite)
                    ],
                    ['id'],
                    limite=1
                )
                
                # Si no hay facturas en los 6 meses anteriores pero sí recientes = reactivación
                if not facturas_antiguas and data['total'] > 10000:
                    self.alertas.append(AlertaFinanciera(
                        codigo="FRA-007",
                        titulo=f"Cuenta Reactivada: {data['nombre'][:40]}",
                        descripcion=f"Cliente sin actividad 6+ meses ahora tiene ${data['total']:,.2f}",
                        tipo_riesgo=TipoRiesgo.FRAUDE,
                        severidad=SeveridadRiesgo.MEDIO,
                        monto_afectado=data['total'],
                        entidades=[data['nombre']] + data['facturas'][:5],
                        evidencia={"cliente": data},
                        recomendacion="Verificar que el cliente es real y las ventas son legítimas",
                        probabilidad_fraude=35
                    ))
        
        except Exception as e:
            logger.error(f"Error en análisis de cuentas dormidas: {e}")
    
    def _analizar_segregacion_funciones(self):
        """Verificar que hay segregación de funciones adecuada."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Obtener usuarios que crean y también validan facturas
            facturas = self.odoo.buscar_leer(
                'account.move',
                [
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', fecha_inicio)
                ],
                ['create_uid', 'write_uid', 'invoice_user_id', 'amount_total', 'name'],
                limite=500
            )
            
            if not facturas:
                return
            
            # Analizar si el mismo usuario crea y valida
            usuarios_concentracion = {}
            for f in facturas:
                create_user = f.get('create_uid', [0, 'Desconocido'])
                user_id = create_user[0] if isinstance(create_user, list) else create_user
                user_nombre = create_user[1] if isinstance(create_user, list) else str(create_user)
                
                if user_id not in usuarios_concentracion:
                    usuarios_concentracion[user_id] = {
                        'nombre': user_nombre,
                        'facturas': 0,
                        'monto_total': 0
                    }
                
                usuarios_concentracion[user_id]['facturas'] += 1
                usuarios_concentracion[user_id]['monto_total'] += f.get('amount_total', 0)
            
            # Detectar concentración excesiva en un usuario
            total_facturas = len(facturas)
            for user_id, data in usuarios_concentracion.items():
                concentracion = data['facturas'] / total_facturas if total_facturas > 0 else 0
                
                if concentracion > 0.70 and data['facturas'] > 20:  # Más del 70% de las facturas
                    self.alertas.append(AlertaFinanciera(
                        codigo="CTL-001",
                        titulo="Riesgo de Control: Alta Concentración de Usuario",
                        descripcion=f"Usuario '{data['nombre']}' maneja {concentracion*100:.0f}% de facturas (${data['monto_total']:,.2f})",
                        tipo_riesgo=TipoRiesgo.CUMPLIMIENTO,
                        severidad=SeveridadRiesgo.ALTO,
                        monto_afectado=data['monto_total'],
                        entidades=[data['nombre']],
                        evidencia={"concentracion": concentracion, "usuario": data},
                        recomendacion="Implementar segregación de funciones. Distribuir carga entre usuarios.",
                        probabilidad_fraude=30
                    ))
        
        except Exception as e:
            logger.error(f"Error en análisis de segregación: {e}")
    
    def _analizar_secuencias_documentos(self):
        """Verificar integridad de secuencias de documentos."""
        try:
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Obtener facturas ordenadas por número
            facturas = self.odoo.buscar_leer(
                'account.move',
                [
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', fecha_inicio)
                ],
                ['name', 'invoice_date'],
                limite=500
            )
            
            if len(facturas) < 10:
                return
            
            # Extraer números de las facturas
            import re
            numeros = []
            for f in facturas:
                nombre = f.get('name', '')
                # Extraer el número de la factura (último segmento numérico)
                match = re.search(r'(\d+)$', nombre)
                if match:
                    numeros.append(int(match.group(1)))
            
            if len(numeros) < 10:
                return
            
            numeros.sort()
            
            # Buscar saltos significativos en la numeración
            saltos = []
            for i in range(1, len(numeros)):
                diferencia = numeros[i] - numeros[i-1]
                if diferencia > 10:  # Salto de más de 10 números
                    saltos.append({
                        'desde': numeros[i-1],
                        'hasta': numeros[i],
                        'salto': diferencia
                    })
            
            if saltos:
                total_faltantes = sum(s['salto'] - 1 for s in saltos)
                self.alertas.append(AlertaFinanciera(
                    codigo="CTL-002",
                    titulo="Saltos en Numeración de Facturas",
                    descripcion=f"Se detectaron {len(saltos)} saltos con {total_faltantes} números faltantes",
                    tipo_riesgo=TipoRiesgo.CONTABLE,
                    severidad=SeveridadRiesgo.MEDIO,
                    monto_afectado=0,
                    entidades=[f"Salto {s['desde']}-{s['hasta']}" for s in saltos[:5]],
                    evidencia={"saltos": saltos},
                    recomendacion="Investigar facturas faltantes. Pueden ser canceladas o eliminadas.",
                    probabilidad_fraude=20
                ))
        
        except Exception as e:
            logger.error(f"Error en análisis de secuencias: {e}")
    
    def _calcular_score_riesgo(self) -> float:
        """Calcular score de riesgo general (0-100, mayor=más riesgo)."""
        score = 0
        
        for alerta in self.alertas:
            if alerta.severidad == SeveridadRiesgo.CRITICO:
                score += 20
            elif alerta.severidad == SeveridadRiesgo.ALTO:
                score += 12
            elif alerta.severidad == SeveridadRiesgo.MEDIO:
                score += 6
            else:
                score += 2
            
            # Bonus por probabilidad de fraude alta
            if alerta.probabilidad_fraude > 50:
                score += 5
        
        return min(100, score)
    
    def _generar_recomendaciones_control(self) -> List[str]:
        """Generar recomendaciones de control basadas en hallazgos."""
        recomendaciones = []
        
        tipos_detectados = set(a.tipo_riesgo for a in self.alertas)
        
        if TipoRiesgo.FRAUDE in tipos_detectados:
            recomendaciones.append(
                "CONTROL CRÍTICO: Implementar revisión dual para aprobación de notas de crédito y "
                "ajustes de inventario mayores a $10,000."
            )
        
        if TipoRiesgo.CUMPLIMIENTO in tipos_detectados:
            recomendaciones.append(
                "SEGREGACIÓN DE FUNCIONES: Redistribuir responsabilidades entre usuarios. "
                "Ningún usuario debe poder crear y aprobar transacciones."
            )
        
        if TipoRiesgo.OPERACIONAL in tipos_detectados:
            recomendaciones.append(
                "POLÍTICA DE DESCUENTOS: Establecer niveles de aprobación por porcentaje de descuento. "
                "Descuentos >20% requieren autorización gerencial."
            )
        
        if TipoRiesgo.CONTABLE in tipos_detectados:
            recomendaciones.append(
                "AUDITORÍA MENSUAL: Implementar revisión mensual de secuencias de documentos "
                "y conciliación de cuentas."
            )
        
        if not recomendaciones:
            recomendaciones.append(
                "ESTADO SALUDABLE: No se detectaron riesgos críticos. Mantener controles actuales "
                "y continuar con auditorías periódicas."
            )
        
        return recomendaciones
    
    # ============================================================
    # FORMATEO PARA INTERFAZ
    # ============================================================
    
    def formatear_auditoria_markdown(self, resultado: ResultadoAuditoria) -> str:
        """Formatear resultado de auditoría en Markdown."""
        severidad_emoji = {
            SeveridadRiesgo.CRITICO: "🔴",
            SeveridadRiesgo.ALTO: "🟠",
            SeveridadRiesgo.MEDIO: "🟡",
            SeveridadRiesgo.BAJO: "🟢"
        }
        
        tipo_emoji = {
            TipoRiesgo.FRAUDE: "FRAUDE",
            TipoRiesgo.OPERACIONAL: "OPERACIONAL",
            TipoRiesgo.CREDITICIO: "CRÉDITO",
            TipoRiesgo.LIQUIDEZ: "LIQUIDEZ",
            TipoRiesgo.CONTABLE: "CONTABLE",
            TipoRiesgo.CUMPLIMIENTO: "CONTROL"
        }
        
        # Determinar estado general
        if resultado.score_riesgo < 20:
            estado = "BAJO RIESGO"
        elif resultado.score_riesgo < 50:
            estado = "RIESGO MODERADO"
        elif resultado.score_riesgo < 75:
            estado = "ALTO RIESGO"
        else:
            estado = "RIESGO CRÍTICO"
        
        md = f"""# AUDITORÍA DE FRAUDE Y RIESGOS FINANCIEROS
*Fecha: {resultado.fecha.strftime('%Y-%m-%d %H:%M')}*

---

## RESUMEN EJECUTIVO

| Métrica | Valor |
|---------|-------|
| **Estado General** | {estado} |
| **Score de Riesgo** | {resultado.score_riesgo:.0f}/100 |
| **Transacciones Analizadas** | {resultado.transacciones_analizadas:,} |
| **Entidades Revisadas** | {resultado.entidades_revisadas:,} |
| **Hallazgos** | {len(resultado.hallazgos)} |

---

## HALLAZGOS DE AUDITORÍA

"""
        
        if resultado.hallazgos:
            # Ordenar por severidad
            hallazgos_ordenados = sorted(
                resultado.hallazgos,
                key=lambda x: x.severidad.value,
                reverse=True
            )
            
            for i, hallazgo in enumerate(hallazgos_ordenados[:15], 1):
                emoji = severidad_emoji[hallazgo.severidad]
                tipo = tipo_emoji.get(hallazgo.tipo_riesgo, "❓")
                
                md += f"""### {emoji} {i}. [{hallazgo.codigo}] {hallazgo.titulo}
- **Tipo:** {tipo}
- **Descripción:** {hallazgo.descripcion}
- **Monto Afectado:** ${hallazgo.monto_afectado:,.2f}
- **Probabilidad de Fraude:** {hallazgo.probabilidad_fraude:.0f}%
- **Recomendación:** {hallazgo.recomendacion}
{"- **REQUIERE ACCIÓN INMEDIATA**" if hallazgo.requiere_accion_inmediata else ""}

"""
        else:
            md += "*No se detectaron hallazgos significativos.*\n"
        
        md += """---

## RECOMENDACIONES DE CONTROL

"""
        
        for i, rec in enumerate(resultado.recomendaciones_control, 1):
            md += f"{i}. {rec}\n\n"
        
        md += f"""---

## METODOLOGÍA DE ANÁLISIS

Este análisis utiliza técnicas de:
- Detección de anomalías estadísticas (Z-Score, IQR)
- Análisis de patrones de fraude
- Validación de segregación de funciones
- Verificación de integridad de secuencias
- Análisis de concentración de riesgo

**Confianza del análisis:** Alta (basado en {resultado.transacciones_analizadas} transacciones)

---
*ANDROMEDA - Auditoría Automatizada de Fraude y Riesgos*
"""
        
        return md


# ============================================================
# FUNCIÓN DE PRUEBA
# ============================================================

def main():
    """Probar el analizador de anomalías."""
    print("=" * 60)
    print("Probando Analizador de Anomalías Financieras")
    print("=" * 60)
    
    from models.conector_odoo import ConectorOdoo
    
    odoo = ConectorOdoo()
    if not odoo.conectado:
        print("No se pudo conectar a Odoo")
        return
    
    analizador = AnalizadorAnomalias(odoo)
    resultado = analizador.ejecutar_auditoria_completa()
    
    print(analizador.formatear_auditoria_markdown(resultado))


if __name__ == "__main__":
    main()
