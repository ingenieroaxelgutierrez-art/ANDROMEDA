# ============================================================
# CEREBRO ANDROMEDA - Motor Inteligente de Análisis de Datos
# Advanced Neural Data Resource for Operations, 
# Management & Enterprise Decision Analytics
# ============================================================
# Sistema de matrices de datos, generación dinámica de consultas,
# limpieza automática y análisis con 99%+ de confianza
# ============================================================

import os
import sys
import re
import json
import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import pandas as pd
import numpy as np

from app.logging_config import get_logger
logger = get_logger("core.cerebro_andromeda")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ============================================================
# ENUMS Y DATACLASSES
# ============================================================

class TipoReporte(Enum):
    """Tipos de reportes soportados."""
    VENTAS = "ventas"
    INVENTARIO = "inventario"
    FINANZAS = "finanzas"
    COMPRAS = "compras"
    CLIENTES = "clientes"
    PRODUCTOS = "productos"
    RECURSOS_HUMANOS = "rh"
    PRODUCCION = "produccion"
    CRM = "crm"
    GENERAL = "general"


class TipoAnalisis(Enum):
    """Tipos de análisis disponibles."""
    RESUMEN = "resumen"
    DETALLADO = "detallado"
    COMPARATIVO = "comparativo"
    TENDENCIA = "tendencia"
    PREDICCION = "prediccion"
    ANOMALIAS = "anomalias"
    KPI = "kpi"
    RANKING = "ranking"


class NivelConfianza(Enum):
    """Niveles de confianza en los datos."""
    ALTO = 0.99      # 99%+ datos válidos
    MEDIO = 0.95     # 95-99% datos válidos
    BAJO = 0.90      # 90-95% datos válidos
    INSUFICIENTE = 0.0  # <90% datos válidos


@dataclass
class ResultadoAnalisis:
    """Resultado de un análisis con métricas de confianza."""
    exito: bool
    datos: Any
    df: Optional[pd.DataFrame]
    resumen: str
    respuesta_md: str
    confianza: float
    registros_totales: int
    registros_validos: int
    registros_corregidos: int
    alertas: List[str]
    metricas: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConfiguracionReporte:
    """Configuración para generar un reporte."""
    tipo: TipoReporte
    analisis: TipoAnalisis
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    filtros: Dict[str, Any] = field(default_factory=dict)
    agrupacion: List[str] = field(default_factory=list)
    orden: str = "desc"
    limite: int = 100
    incluir_graficos: bool = True
    formato_salida: str = "markdown"  # markdown, html, json, excel


# ============================================================
# MATRICES DE DATOS ODOO
# ============================================================

class MatrizDatosOdoo:
    """
    Matriz completa de modelos, campos y relaciones de Odoo.
    Conocimiento experto del esquema de datos para consultas precisas.
    """

    # ── Constantes de modelos Odoo ────────────────────────────────────────────
    M_SALE_ORDER = 'sale.order'
    M_POS_ORDER = 'pos.order'
    M_STOCK_QUANT = 'stock.quant'
    M_STOCK_PICKING = 'stock.picking'
    M_ACCOUNT_MOVE = 'account.move'
    M_ACCOUNT_PAYMENT = 'account.payment'
    M_PURCHASE_ORDER = 'purchase.order'
    M_HR_EMPLOYEE = 'hr.employee'
    M_CRM_LEAD = 'crm.lead'
    M_PRODUCT_PRODUCT = 'product.product'
    M_PRODUCT_TEMPLATE = 'product.template'
    M_PRODUCT_CATEGORY = 'product.category'
    M_RES_PARTNER = 'res.partner'
    M_RES_USERS = 'res.users'
    M_RES_COMPANY = 'res.company'
    M_STOCK_WAREHOUSE = 'stock.warehouse'
    M_STOCK_LOCATION = 'stock.location'
    M_HR_DEPARTMENT = 'hr.department'

    # ── Constantes de descripción comunes ────────────────────────────────────
    D_ID_UNICO = 'ID único'
    D_DESCRIPCION = 'Descripción'
    D_PRECIO_UNITARIO = 'Precio unitario'
    D_LINEAS = 'Líneas'
    D_NUMERO = 'Número'

    # Modelos principales con campos y relaciones
    MODELOS = {
        # ======== VENTAS ========
        'sale.order': {
            'descripcion': 'Órdenes de Venta / Pedidos',
            'tabla_alias': 'ventas',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Número de orden'},
                'partner_id': {'tipo': 'many2one', 'relacion': 'res.partner', 'descripcion': 'Cliente'},
                'user_id': {'tipo': 'many2one', 'relacion': 'res.users', 'descripcion': 'Vendedor'},
                'team_id': {'tipo': 'many2one', 'relacion': 'crm.team', 'descripcion': 'Equipo de ventas'},
                'date_order': {'tipo': 'datetime', 'descripcion': 'Fecha de orden'},
                'validity_date': {'tipo': 'date', 'descripcion': 'Fecha de vencimiento'},
                'amount_untaxed': {'tipo': 'monetary', 'descripcion': 'Subtotal sin IVA'},
                'amount_tax': {'tipo': 'monetary', 'descripcion': 'Impuestos'},
                'amount_total': {'tipo': 'monetary', 'descripcion': 'Total'},
                'state': {'tipo': 'selection', 'descripcion': 'Estado', 'opciones': ['draft', 'sent', 'sale', 'done', 'cancel']},
                'order_line': {'tipo': 'one2many', 'relacion': 'sale.order.line', 'descripcion': 'Líneas de orden'},
                'invoice_ids': {'tipo': 'many2many', 'relacion': 'account.move', 'descripcion': 'Facturas'},
                'company_id': {'tipo': 'many2one', 'relacion': 'res.company', 'descripcion': 'Empresa'},
                'warehouse_id': {'tipo': 'many2one', 'relacion': 'stock.warehouse', 'descripcion': 'Almacén'},
                'pricelist_id': {'tipo': 'many2one', 'relacion': 'product.pricelist', 'descripcion': 'Lista de precios'},
            },
            'campos_clave': ['date_order', 'partner_id', 'amount_total', 'state'],
            'campo_fecha': 'date_order',
            'campo_monto': 'amount_total',
            'filtro_confirmado': [('state', 'in', ['sale', 'done'])],
        },
        
        'sale.order.line': {
            'descripcion': 'Líneas de Órdenes de Venta',
            'tabla_alias': 'lineas_venta',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'order_id': {'tipo': 'many2one', 'relacion': 'sale.order', 'descripcion': 'Orden'},
                'product_id': {'tipo': 'many2one', 'relacion': 'product.product', 'descripcion': 'Producto'},
                'product_template_id': {'tipo': 'many2one', 'relacion': 'product.template', 'descripcion': 'Plantilla'},
                'name': {'tipo': 'text', 'descripcion': 'Descripción'},
                'product_uom_qty': {'tipo': 'float', 'descripcion': 'Cantidad'},
                'qty_delivered': {'tipo': 'float', 'descripcion': 'Cantidad entregada'},
                'qty_invoiced': {'tipo': 'float', 'descripcion': 'Cantidad facturada'},
                'price_unit': {'tipo': 'float', 'descripcion': 'Precio unitario'},
                'price_subtotal': {'tipo': 'monetary', 'descripcion': 'Subtotal'},
                'discount': {'tipo': 'float', 'descripcion': 'Descuento %'},
            },
            'campos_clave': ['order_id', 'product_id', 'product_uom_qty', 'price_subtotal'],
        },
        
        # ======== POS (Punto de Venta) ========
        'pos.order': {
            'descripcion': 'Órdenes de Punto de Venta / Tickets',
            'tabla_alias': 'pos',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Número de ticket'},
                'partner_id': {'tipo': 'many2one', 'relacion': 'res.partner', 'descripcion': 'Cliente'},
                'user_id': {'tipo': 'many2one', 'relacion': 'res.users', 'descripcion': 'Cajero'},
                'session_id': {'tipo': 'many2one', 'relacion': 'pos.session', 'descripcion': 'Sesión'},
                'config_id': {'tipo': 'many2one', 'relacion': 'pos.config', 'descripcion': 'Punto de venta'},
                'date_order': {'tipo': 'datetime', 'descripcion': 'Fecha/Hora'},
                'amount_total': {'tipo': 'monetary', 'descripcion': 'Total'},
                'amount_tax': {'tipo': 'monetary', 'descripcion': 'Impuestos'},
                'amount_paid': {'tipo': 'monetary', 'descripcion': 'Pagado'},
                'amount_return': {'tipo': 'monetary', 'descripcion': 'Cambio'},
                'state': {'tipo': 'selection', 'descripcion': 'Estado', 'opciones': ['draft', 'paid', 'done', 'invoiced', 'cancel']},
                'lines': {'tipo': 'one2many', 'relacion': 'pos.order.line', 'descripcion': 'Líneas'},
                'payment_ids': {'tipo': 'one2many', 'relacion': 'pos.payment', 'descripcion': 'Pagos'},
                'company_id': {'tipo': 'many2one', 'relacion': 'res.company', 'descripcion': 'Empresa'},
            },
            'campos_clave': ['date_order', 'session_id', 'amount_total', 'state'],
            'campo_fecha': 'date_order',
            'campo_monto': 'amount_total',
            'filtro_confirmado': [('state', 'in', ['paid', 'done', 'invoiced'])],
        },
        
        'pos.order.line': {
            'descripcion': 'Líneas de Tickets POS',
            'tabla_alias': 'lineas_pos',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'order_id': {'tipo': 'many2one', 'relacion': 'pos.order', 'descripcion': 'Ticket'},
                'product_id': {'tipo': 'many2one', 'relacion': 'product.product', 'descripcion': 'Producto'},
                'qty': {'tipo': 'float', 'descripcion': 'Cantidad'},
                'price_unit': {'tipo': 'float', 'descripcion': 'Precio unitario'},
                'price_subtotal': {'tipo': 'monetary', 'descripcion': 'Subtotal'},
                'price_subtotal_incl': {'tipo': 'monetary', 'descripcion': 'Subtotal con IVA'},
                'discount': {'tipo': 'float', 'descripcion': 'Descuento %'},
            },
            'campos_clave': ['order_id', 'product_id', 'qty', 'price_subtotal_incl'],
        },
        
        'pos.session': {
            'descripcion': 'Sesiones de Caja / Turnos',
            'tabla_alias': 'sesiones_pos',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Nombre de sesión'},
                'user_id': {'tipo': 'many2one', 'relacion': 'res.users', 'descripcion': 'Responsable'},
                'config_id': {'tipo': 'many2one', 'relacion': 'pos.config', 'descripcion': 'Punto de venta'},
                'start_at': {'tipo': 'datetime', 'descripcion': 'Inicio'},
                'stop_at': {'tipo': 'datetime', 'descripcion': 'Cierre'},
                'state': {'tipo': 'selection', 'descripcion': 'Estado', 'opciones': ['opening_control', 'opened', 'closing_control', 'closed']},
                'cash_control': {'tipo': 'boolean', 'descripcion': 'Control de caja'},
                'cash_register_balance_start': {'tipo': 'monetary', 'descripcion': 'Saldo inicial'},
                'cash_register_balance_end_real': {'tipo': 'monetary', 'descripcion': 'Saldo final'},
                'total_payments_amount': {'tipo': 'monetary', 'descripcion': 'Total pagos'},
                'order_count': {'tipo': 'integer', 'descripcion': 'Número de órdenes'},
            },
            'campos_clave': ['start_at', 'state', 'total_payments_amount'],
            'campo_fecha': 'start_at',
        },
        
        'pos.payment': {
            'descripcion': 'Pagos de POS',
            'tabla_alias': 'pagos_pos',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'pos_order_id': {'tipo': 'many2one', 'relacion': 'pos.order', 'descripcion': 'Ticket'},
                'payment_method_id': {'tipo': 'many2one', 'relacion': 'pos.payment.method', 'descripcion': 'Método de pago'},
                'amount': {'tipo': 'monetary', 'descripcion': 'Monto'},
                'payment_date': {'tipo': 'datetime', 'descripcion': 'Fecha de pago'},
            },
            'campos_clave': ['pos_order_id', 'payment_method_id', 'amount'],
        },
        
        # ======== INVENTARIO / STOCK ========
        'stock.quant': {
            'descripcion': 'Existencias / Stock por Ubicación',
            'tabla_alias': 'stock',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'product_id': {'tipo': 'many2one', 'relacion': 'product.product', 'descripcion': 'Producto'},
                'location_id': {'tipo': 'many2one', 'relacion': 'stock.location', 'descripcion': 'Ubicación'},
                'quantity': {'tipo': 'float', 'descripcion': 'Cantidad disponible'},
                'reserved_quantity': {'tipo': 'float', 'descripcion': 'Cantidad reservada'},
                'lot_id': {'tipo': 'many2one', 'relacion': 'stock.lot', 'descripcion': 'Lote/Serie'},
                'company_id': {'tipo': 'many2one', 'relacion': 'res.company', 'descripcion': 'Empresa'},
            },
            'campos_clave': ['product_id', 'location_id', 'quantity'],
        },
        
        'stock.location': {
            'descripcion': 'Ubicaciones de Almacén',
            'tabla_alias': 'ubicaciones',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Nombre'},
                'complete_name': {'tipo': 'char', 'descripcion': 'Nombre completo'},
                'usage': {'tipo': 'selection', 'descripcion': 'Tipo', 'opciones': ['supplier', 'view', 'internal', 'customer', 'inventory', 'production', 'transit']},
                'warehouse_id': {'tipo': 'many2one', 'relacion': 'stock.warehouse', 'descripcion': 'Almacén'},
                'company_id': {'tipo': 'many2one', 'relacion': 'res.company', 'descripcion': 'Empresa'},
            },
            'campos_clave': ['name', 'usage', 'warehouse_id'],
        },
        
        'stock.warehouse': {
            'descripcion': 'Almacenes / Tiendas',
            'tabla_alias': 'almacenes',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Nombre'},
                'code': {'tipo': 'char', 'descripcion': 'Código corto'},
                'lot_stock_id': {'tipo': 'many2one', 'relacion': 'stock.location', 'descripcion': 'Ubicación de stock'},
                'company_id': {'tipo': 'many2one', 'relacion': 'res.company', 'descripcion': 'Empresa'},
                'partner_id': {'tipo': 'many2one', 'relacion': 'res.partner', 'descripcion': 'Dirección'},
            },
            'campos_clave': ['name', 'code', 'company_id'],
        },
        
        'stock.picking': {
            'descripcion': 'Transferencias / Movimientos',
            'tabla_alias': 'transferencias',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Referencia'},
                'origin': {'tipo': 'char', 'descripcion': 'Documento origen'},
                'partner_id': {'tipo': 'many2one', 'relacion': 'res.partner', 'descripcion': 'Contacto'},
                'picking_type_id': {'tipo': 'many2one', 'relacion': 'stock.picking.type', 'descripcion': 'Tipo'},
                'location_id': {'tipo': 'many2one', 'relacion': 'stock.location', 'descripcion': 'Origen'},
                'location_dest_id': {'tipo': 'many2one', 'relacion': 'stock.location', 'descripcion': 'Destino'},
                'scheduled_date': {'tipo': 'datetime', 'descripcion': 'Fecha programada'},
                'date_done': {'tipo': 'datetime', 'descripcion': 'Fecha realizado'},
                'state': {'tipo': 'selection', 'descripcion': 'Estado', 'opciones': ['draft', 'waiting', 'confirmed', 'assigned', 'done', 'cancel']},
            },
            'campos_clave': ['picking_type_id', 'scheduled_date', 'state'],
            'campo_fecha': 'scheduled_date',
        },
        
        # ======== PRODUCTOS ========
        'product.product': {
            'descripcion': 'Productos / Variantes',
            'tabla_alias': 'productos',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Nombre'},
                'default_code': {'tipo': 'char', 'descripcion': 'Referencia interna / SKU'},
                'barcode': {'tipo': 'char', 'descripcion': 'Código de barras'},
                'product_tmpl_id': {'tipo': 'many2one', 'relacion': 'product.template', 'descripcion': 'Plantilla'},
                'categ_id': {'tipo': 'many2one', 'relacion': 'product.category', 'descripcion': 'Categoría'},
                'list_price': {'tipo': 'float', 'descripcion': 'Precio de venta'},
                'standard_price': {'tipo': 'float', 'descripcion': 'Costo'},
                'qty_available': {'tipo': 'float', 'descripcion': 'Cantidad disponible'},
                'virtual_available': {'tipo': 'float', 'descripcion': 'Cantidad proyectada'},
                'type': {'tipo': 'selection', 'descripcion': 'Tipo', 'opciones': ['consu', 'service', 'product']},
                'active': {'tipo': 'boolean', 'descripcion': 'Activo'},
                'company_id': {'tipo': 'many2one', 'relacion': 'res.company', 'descripcion': 'Empresa'},
            },
            'campos_clave': ['name', 'default_code', 'categ_id', 'list_price', 'qty_available'],
        },
        
        'product.template': {
            'descripcion': 'Plantillas de Producto',
            'tabla_alias': 'plantillas',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Nombre'},
                'default_code': {'tipo': 'char', 'descripcion': 'Referencia interna'},
                'type': {'tipo': 'selection', 'descripcion': 'Tipo de producto'},
                'categ_id': {'tipo': 'many2one', 'relacion': 'product.category', 'descripcion': 'Categoría'},
                'list_price': {'tipo': 'float', 'descripcion': 'Precio de venta'},
                'standard_price': {'tipo': 'float', 'descripcion': 'Costo'},
                'active': {'tipo': 'boolean', 'descripcion': 'Activo'},
            },
            'campos_clave': ['name', 'categ_id', 'list_price'],
        },
        
        'product.category': {
            'descripcion': 'Categorías de Producto',
            'tabla_alias': 'categorias',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Nombre'},
                'complete_name': {'tipo': 'char', 'descripcion': 'Nombre completo'},
                'parent_id': {'tipo': 'many2one', 'relacion': 'product.category', 'descripcion': 'Categoría padre'},
            },
            'campos_clave': ['name', 'parent_id'],
        },
        
        # ======== FACTURACIÓN / CONTABILIDAD ========
        'account.move': {
            'descripcion': 'Asientos Contables / Facturas',
            'tabla_alias': 'facturas',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Número'},
                'partner_id': {'tipo': 'many2one', 'relacion': 'res.partner', 'descripcion': 'Cliente/Proveedor'},
                'invoice_user_id': {'tipo': 'many2one', 'relacion': 'res.users', 'descripcion': 'Vendedor'},
                'invoice_date': {'tipo': 'date', 'descripcion': 'Fecha de factura'},
                'invoice_date_due': {'tipo': 'date', 'descripcion': 'Fecha de vencimiento'},
                'move_type': {'tipo': 'selection', 'descripcion': 'Tipo', 'opciones': ['entry', 'out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt']},
                'state': {'tipo': 'selection', 'descripcion': 'Estado', 'opciones': ['draft', 'posted', 'cancel']},
                'payment_state': {'tipo': 'selection', 'descripcion': 'Estado de pago', 'opciones': ['not_paid', 'in_payment', 'paid', 'partial', 'reversed', 'invoicing_legacy']},
                'amount_untaxed': {'tipo': 'monetary', 'descripcion': 'Subtotal'},
                'amount_tax': {'tipo': 'monetary', 'descripcion': 'IVA'},
                'amount_total': {'tipo': 'monetary', 'descripcion': 'Total'},
                'amount_residual': {'tipo': 'monetary', 'descripcion': 'Saldo pendiente'},
                'company_id': {'tipo': 'many2one', 'relacion': 'res.company', 'descripcion': 'Empresa'},
                'invoice_line_ids': {'tipo': 'one2many', 'relacion': 'account.move.line', 'descripcion': 'Líneas'},
            },
            'campos_clave': ['invoice_date', 'partner_id', 'amount_total', 'state', 'payment_state'],
            'campo_fecha': 'invoice_date',
            'campo_monto': 'amount_total',
            'filtro_facturas_cliente': [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')],
            'filtro_facturas_proveedor': [('move_type', '=', 'in_invoice'), ('state', '=', 'posted')],
        },
        
        'account.move.line': {
            'descripcion': 'Líneas de Asientos / Facturas',
            'tabla_alias': 'lineas_factura',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'move_id': {'tipo': 'many2one', 'relacion': 'account.move', 'descripcion': 'Factura'},
                'account_id': {'tipo': 'many2one', 'relacion': 'account.account', 'descripcion': 'Cuenta contable'},
                'product_id': {'tipo': 'many2one', 'relacion': 'product.product', 'descripcion': 'Producto'},
                'name': {'tipo': 'char', 'descripcion': 'Descripción'},
                'quantity': {'tipo': 'float', 'descripcion': 'Cantidad'},
                'price_unit': {'tipo': 'float', 'descripcion': 'Precio unitario'},
                'price_subtotal': {'tipo': 'monetary', 'descripcion': 'Subtotal'},
                'debit': {'tipo': 'monetary', 'descripcion': 'Debe'},
                'credit': {'tipo': 'monetary', 'descripcion': 'Haber'},
                'balance': {'tipo': 'monetary', 'descripcion': 'Balance'},
            },
            'campos_clave': ['move_id', 'product_id', 'quantity', 'price_subtotal'],
        },
        
        'account.payment': {
            'descripcion': 'Pagos / Cobros',
            'tabla_alias': 'pagos',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Número'},
                'partner_id': {'tipo': 'many2one', 'relacion': 'res.partner', 'descripcion': 'Cliente/Proveedor'},
                'payment_type': {'tipo': 'selection', 'descripcion': 'Tipo', 'opciones': ['outbound', 'inbound']},
                'partner_type': {'tipo': 'selection', 'descripcion': 'Tipo de contacto', 'opciones': ['customer', 'supplier']},
                'amount': {'tipo': 'monetary', 'descripcion': 'Monto'},
                'date': {'tipo': 'date', 'descripcion': 'Fecha'},
                'state': {'tipo': 'selection', 'descripcion': 'Estado', 'opciones': ['draft', 'posted', 'sent', 'reconciled', 'cancelled']},
                'journal_id': {'tipo': 'many2one', 'relacion': 'account.journal', 'descripcion': 'Diario'},
            },
            'campos_clave': ['date', 'partner_id', 'amount', 'payment_type', 'state'],
            'campo_fecha': 'date',
            'campo_monto': 'amount',
        },
        
        # ======== COMPRAS ========
        'purchase.order': {
            'descripcion': 'Órdenes de Compra',
            'tabla_alias': 'compras',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Número'},
                'partner_id': {'tipo': 'many2one', 'relacion': 'res.partner', 'descripcion': 'Proveedor'},
                'user_id': {'tipo': 'many2one', 'relacion': 'res.users', 'descripcion': 'Comprador'},
                'date_order': {'tipo': 'datetime', 'descripcion': 'Fecha de orden'},
                'date_approve': {'tipo': 'datetime', 'descripcion': 'Fecha de confirmación'},
                'date_planned': {'tipo': 'datetime', 'descripcion': 'Fecha prevista'},
                'amount_untaxed': {'tipo': 'monetary', 'descripcion': 'Subtotal'},
                'amount_tax': {'tipo': 'monetary', 'descripcion': 'IVA'},
                'amount_total': {'tipo': 'monetary', 'descripcion': 'Total'},
                'state': {'tipo': 'selection', 'descripcion': 'Estado', 'opciones': ['draft', 'sent', 'to approve', 'purchase', 'done', 'cancel']},
                'order_line': {'tipo': 'one2many', 'relacion': 'purchase.order.line', 'descripcion': 'Líneas'},
                'company_id': {'tipo': 'many2one', 'relacion': 'res.company', 'descripcion': 'Empresa'},
            },
            'campos_clave': ['date_order', 'partner_id', 'amount_total', 'state'],
            'campo_fecha': 'date_order',
            'campo_monto': 'amount_total',
            'filtro_confirmado': [('state', 'in', ['purchase', 'done'])],
        },
        
        'purchase.order.line': {
            'descripcion': 'Líneas de Órdenes de Compra',
            'tabla_alias': 'lineas_compra',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'order_id': {'tipo': 'many2one', 'relacion': 'purchase.order', 'descripcion': 'Orden'},
                'product_id': {'tipo': 'many2one', 'relacion': 'product.product', 'descripcion': 'Producto'},
                'name': {'tipo': 'text', 'descripcion': 'Descripción'},
                'product_qty': {'tipo': 'float', 'descripcion': 'Cantidad'},
                'qty_received': {'tipo': 'float', 'descripcion': 'Cantidad recibida'},
                'price_unit': {'tipo': 'float', 'descripcion': 'Precio unitario'},
                'price_subtotal': {'tipo': 'monetary', 'descripcion': 'Subtotal'},
            },
            'campos_clave': ['order_id', 'product_id', 'product_qty', 'price_subtotal'],
        },
        
        # ======== CLIENTES / CONTACTOS ========
        'res.partner': {
            'descripcion': 'Contactos / Clientes / Proveedores',
            'tabla_alias': 'contactos',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Nombre'},
                'display_name': {'tipo': 'char', 'descripcion': 'Nombre mostrado'},
                'email': {'tipo': 'char', 'descripcion': 'Email'},
                'phone': {'tipo': 'char', 'descripcion': 'Teléfono'},
                'mobile': {'tipo': 'char', 'descripcion': 'Móvil'},
                'street': {'tipo': 'char', 'descripcion': 'Calle'},
                'city': {'tipo': 'char', 'descripcion': 'Ciudad'},
                'state_id': {'tipo': 'many2one', 'relacion': 'res.country.state', 'descripcion': 'Estado'},
                'country_id': {'tipo': 'many2one', 'relacion': 'res.country', 'descripcion': 'País'},
                'zip': {'tipo': 'char', 'descripcion': 'CP'},
                'vat': {'tipo': 'char', 'descripcion': 'RFC'},
                'customer_rank': {'tipo': 'integer', 'descripcion': 'Es cliente'},
                'supplier_rank': {'tipo': 'integer', 'descripcion': 'Es proveedor'},
                'company_id': {'tipo': 'many2one', 'relacion': 'res.company', 'descripcion': 'Empresa'},
                'create_date': {'tipo': 'datetime', 'descripcion': 'Fecha creación'},
                'credit_limit': {'tipo': 'monetary', 'descripcion': 'Límite de crédito'},
                'total_invoiced': {'tipo': 'monetary', 'descripcion': 'Total facturado'},
            },
            'campos_clave': ['name', 'email', 'customer_rank', 'supplier_rank'],
            'filtro_clientes': [('customer_rank', '>', 0)],
            'filtro_proveedores': [('supplier_rank', '>', 0)],
        },
        
        # ======== EMPRESA / MULTI-COMPAÑÍA ========
        'res.company': {
            'descripcion': 'Empresas / Compañías',
            'tabla_alias': 'empresas',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Nombre'},
                'currency_id': {'tipo': 'many2one', 'relacion': 'res.currency', 'descripcion': 'Moneda'},
                'partner_id': {'tipo': 'many2one', 'relacion': 'res.partner', 'descripcion': 'Contacto'},
            },
            'campos_clave': ['name'],
        },
        
        # ======== RECURSOS HUMANOS ========
        'hr.employee': {
            'descripcion': 'Empleados',
            'tabla_alias': 'empleados',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Nombre'},
                'job_id': {'tipo': 'many2one', 'relacion': 'hr.job', 'descripcion': 'Puesto'},
                'department_id': {'tipo': 'many2one', 'relacion': 'hr.department', 'descripcion': 'Departamento'},
                'work_email': {'tipo': 'char', 'descripcion': 'Email de trabajo'},
                'work_phone': {'tipo': 'char', 'descripcion': 'Teléfono'},
                'company_id': {'tipo': 'many2one', 'relacion': 'res.company', 'descripcion': 'Empresa'},
                'active': {'tipo': 'boolean', 'descripcion': 'Activo'},
            },
            'campos_clave': ['name', 'job_id', 'department_id'],
        },
        
        'hr.department': {
            'descripcion': 'Departamentos',
            'tabla_alias': 'departamentos',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Nombre'},
                'manager_id': {'tipo': 'many2one', 'relacion': 'hr.employee', 'descripcion': 'Responsable'},
                'company_id': {'tipo': 'many2one', 'relacion': 'res.company', 'descripcion': 'Empresa'},
            },
            'campos_clave': ['name', 'manager_id'],
        },
        
        # ======== CRM ========
        'crm.lead': {
            'descripcion': 'Oportunidades / Leads',
            'tabla_alias': 'oportunidades',
            'campos': {
                'id': {'tipo': 'integer', 'descripcion': 'ID único'},
                'name': {'tipo': 'char', 'descripcion': 'Nombre'},
                'partner_id': {'tipo': 'many2one', 'relacion': 'res.partner', 'descripcion': 'Cliente'},
                'user_id': {'tipo': 'many2one', 'relacion': 'res.users', 'descripcion': 'Vendedor'},
                'team_id': {'tipo': 'many2one', 'relacion': 'crm.team', 'descripcion': 'Equipo'},
                'stage_id': {'tipo': 'many2one', 'relacion': 'crm.stage', 'descripcion': 'Etapa'},
                'expected_revenue': {'tipo': 'monetary', 'descripcion': 'Ingreso esperado'},
                'probability': {'tipo': 'float', 'descripcion': 'Probabilidad %'},
                'date_deadline': {'tipo': 'date', 'descripcion': 'Cierre esperado'},
                'create_date': {'tipo': 'datetime', 'descripcion': 'Creación'},
                'type': {'tipo': 'selection', 'descripcion': 'Tipo', 'opciones': ['lead', 'opportunity']},
                'active': {'tipo': 'boolean', 'descripcion': 'Activo'},
            },
            'campos_clave': ['name', 'stage_id', 'expected_revenue', 'probability'],
            'campo_fecha': 'create_date',
            'campo_monto': 'expected_revenue',
        },
    }
    
    # Mapeo de alias/sinónimos a modelos
    ALIAS_MODELOS = {
        # Ventas
        'ventas': 'sale.order',
        'pedidos': 'sale.order',
        'ordenes': 'sale.order',
        'sales': 'sale.order',
        
        # POS
        'pos': 'pos.order',
        'tickets': 'pos.order',
        'caja': 'pos.order',
        'punto de venta': 'pos.order',
        'tienda': 'pos.order',
        'PdV': 'pos.order',
        
        # Inventario
        'inventario': 'stock.quant',
        'stock': 'stock.quant',
        'existencias': 'stock.quant',
        'almacen': 'stock.warehouse',
        'almacenes': 'stock.warehouse',
        'bodega': 'stock.warehouse',
        'ubicaciones': 'stock.location',
        'transferencias': 'stock.picking',
        'movimientos': 'stock.picking',
        
        # Productos
        'productos': 'product.product',
        'articulos': 'product.product',
        'items': 'product.product',
        'categorias': 'product.category',
        
        # Facturación
        'facturas': 'account.move',
        'facturacion': 'account.move',
        'cfdi': 'account.move',
        'cobros': 'account.payment',
        'pagos': 'account.payment',
        
        # Compras
        'compras': 'purchase.order',
        'proveedores': 'res.partner',
        
        # Clientes
        'clientes': 'res.partner',
        'contactos': 'res.partner',
        
        # RH
        'empleados': 'hr.employee',
        'personal': 'hr.employee',
        'departamentos': 'hr.department',
        
        # CRM
        'oportunidades': 'crm.lead',
        'leads': 'crm.lead',
        'prospectos': 'crm.lead',
        'crm': 'crm.lead',
        
        # Empresa
        'empresas': 'res.company',
        'compania': 'res.company',
    }
    
    @classmethod
    def obtener_modelo(cls, alias: str) -> Optional[str]:
        """Obtiene el nombre del modelo Odoo desde un alias."""
        alias_lower = alias.lower().strip()
        
        # Buscar en alias directos
        if alias_lower in cls.ALIAS_MODELOS:
            return cls.ALIAS_MODELOS[alias_lower]
        
        # Buscar en modelos directamente
        if alias_lower in cls.MODELOS:
            return alias_lower
        
        # Buscar similitudes parciales
        for key in cls.ALIAS_MODELOS:
            if alias_lower in key or key in alias_lower:
                return cls.ALIAS_MODELOS[key]
        
        return None
    
    @classmethod
    def obtener_info_modelo(cls, modelo: str) -> Optional[Dict]:
        """Obtiene información completa de un modelo."""
        if modelo in cls.MODELOS:
            return cls.MODELOS[modelo]
        
        # Buscar por alias
        modelo_real = cls.obtener_modelo(modelo)
        if modelo_real and modelo_real in cls.MODELOS:
            return cls.MODELOS[modelo_real]
        
        return None
    
    @classmethod
    def obtener_campos_clave(cls, modelo: str) -> List[str]:
        """Obtiene los campos clave de un modelo."""
        info = cls.obtener_info_modelo(modelo)
        if info:
            return info.get('campos_clave', [])
        return []
    
    @classmethod
    def obtener_campo_fecha(cls, modelo: str) -> Optional[str]:
        """Obtiene el campo de fecha principal de un modelo."""
        info = cls.obtener_info_modelo(modelo)
        if info:
            return info.get('campo_fecha')
        return None
    
    @classmethod
    def obtener_campo_monto(cls, modelo: str) -> Optional[str]:
        """Obtiene el campo de monto principal de un modelo."""
        info = cls.obtener_info_modelo(modelo)
        if info:
            return info.get('campo_monto')
        return None


# ============================================================
# LIMPIADOR Y VALIDADOR DE DATOS
# ============================================================

class LimpiadorDatos:
    """
    Sistema de limpieza y validación de datos con 99%+ de confianza.
    Detecta, corrige y documenta problemas en los datos.
    """
    
    def __init__(self):
        self.estadisticas_limpieza = {
            'registros_procesados': 0,
            'registros_validos': 0,
            'registros_corregidos': 0,
            'registros_eliminados': 0,
            'errores_encontrados': [],
        }
        self.reset_estadisticas()
    
    def reset_estadisticas(self):
        """Reinicia las estadísticas de limpieza."""
        self.estadisticas_limpieza = {
            'registros_procesados': 0,
            'registros_validos': 0,
            'registros_corregidos': 0,
            'registros_eliminados': 0,
            'errores_encontrados': [],
        }
    
    def limpiar_dataframe(self, df: pd.DataFrame, modelo: str = None) -> Tuple[pd.DataFrame, float, Dict]:  # noqa: ARG002
        """
        Limpia un DataFrame y retorna confianza del resultado.
        
        Returns:
            (df_limpio, confianza, estadisticas)
        """
        if df is None or df.empty:
            return pd.DataFrame(), 0.0, self.estadisticas_limpieza
        
        self.reset_estadisticas()
        df_limpio = df.copy()
        self.estadisticas_limpieza['registros_procesados'] = len(df)
        
        # 1. Eliminar duplicados
        antes = len(df_limpio)
        df_limpio = df_limpio.drop_duplicates()
        dups = antes - len(df_limpio)
        if dups > 0:
            self.estadisticas_limpieza['errores_encontrados'].append(f'{dups} duplicados eliminados')
        
        # 2. Limpiar valores nulos en campos críticos
        for col in df_limpio.columns:
            nulos_antes = df_limpio[col].isna().sum()
            if nulos_antes > 0:
                # Intentar rellenar según tipo de dato
                if df_limpio[col].dtype in ['float64', 'int64']:
                    df_limpio[col] = df_limpio[col].fillna(0)
                    self.estadisticas_limpieza['registros_corregidos'] += int(nulos_antes)
                elif df_limpio[col].dtype == 'object':
                    df_limpio[col] = df_limpio[col].fillna('N/A')
                    self.estadisticas_limpieza['registros_corregidos'] += int(nulos_antes)
        
        # 3. Limpiar valores de relaciones Many2one de Odoo
        for col in df_limpio.columns:
            if df_limpio[col].dtype == 'object':
                # Detectar tuples (id, nombre) de Odoo
                df_limpio[col] = df_limpio[col].apply(self._limpiar_valor_odoo)
        
        # 4. Normalizar números
        for col in df_limpio.select_dtypes(include=[np.number]).columns:
            # Reemplazar infinitos
            df_limpio[col] = df_limpio[col].replace([np.inf, -np.inf], 0)
            # Limitar valores muy grandes
            if df_limpio[col].abs().max() > 1e15:
                self.estadisticas_limpieza['errores_encontrados'].append(
                    f'Valores extremos detectados en {col}'
                )
        
        # 5. Normalizar fechas
        for col in df_limpio.columns:
            if 'date' in col.lower() or 'fecha' in col.lower():
                try:
                    df_limpio[col] = pd.to_datetime(df_limpio[col], errors='coerce')
                except Exception:
                    pass
        
        # Calcular confianza
        self.estadisticas_limpieza['registros_validos'] = len(df_limpio)
        
        if self.estadisticas_limpieza['registros_procesados'] > 0:
            confianza = (
                self.estadisticas_limpieza['registros_validos'] / 
                self.estadisticas_limpieza['registros_procesados']
            )
            # Ajustar por correcciones
            if self.estadisticas_limpieza['registros_corregidos'] > 0:
                confianza *= 0.98  # Penalizar ligeramente por correcciones
        else:
            confianza = 0.0
        
        return df_limpio, confianza, self.estadisticas_limpieza
    
    def _limpiar_valor_odoo(self, valor) -> Any:
        """Limpia un valor que puede ser una tupla de Odoo."""
        if isinstance(valor, (list, tuple)):
            if len(valor) >= 2:
                return valor[1]  # Retornar el nombre
            elif len(valor) == 1:
                return valor[0]
        return valor
    
    def validar_numerico(self, valor: Any, default: float = 0.0) -> float:
        """Valida y garantiza un valor numérico."""
        if valor is None:
            return default
        try:
            resultado = float(valor)
            if math.isnan(resultado) or math.isinf(resultado):
                return default
            return resultado
        except (ValueError, TypeError):
            return default
    
    def validar_fecha(self, valor: Any, formato: str = '%Y-%m-%d') -> Optional[str]:
        """Valida y formatea una fecha."""
        if valor is None:
            return None
        
        if isinstance(valor, datetime):
            return valor.strftime(formato)
        
        if isinstance(valor, str):
            try:
                datetime.strptime(valor[:10], formato)
                return valor[:10]
            except Exception:
                pass
        
        return None
    
    def detectar_anomalias_estadisticas(self, df: pd.DataFrame, columna: str) -> Dict:
        """Detecta anomalías estadísticas en una columna numérica."""
        if columna not in df.columns:
            return {'error': f'Columna {columna} no existe'}
        
        datos = df[columna].dropna()
        if len(datos) < 3:
            return {'error': 'Datos insuficientes para análisis'}
        
        media = datos.mean()
        std = datos.std()
        mediana = datos.median()
        q1 = datos.quantile(0.25)
        q3 = datos.quantile(0.75)
        iqr = q3 - q1
        
        # Detectar outliers
        limite_inferior = q1 - 1.5 * iqr
        limite_superior = q3 + 1.5 * iqr
        outliers = datos[(datos < limite_inferior) | (datos > limite_superior)]
        
        return {
            'media': media,
            'mediana': mediana,
            'std': std,
            'min': datos.min(),
            'max': datos.max(),
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'outliers_count': len(outliers),
            'outliers_pct': len(outliers) / len(datos) * 100 if len(datos) > 0 else 0,
            'limite_inferior': limite_inferior,
            'limite_superior': limite_superior,
        }


# ============================================================
# GENERADOR DE CONSULTAS DINÁMICO
# ============================================================

class GeneradorConsultas:
    """
    Generador dinámico de consultas Odoo.
    Construye filtros, campos y agregaciones de forma inteligente.
    """
    
    def __init__(self, matriz: MatrizDatosOdoo = None):
        self.matriz = matriz or MatrizDatosOdoo()
    
    def construir_filtro_fecha(
        self, 
        campo: str, 
        fecha_inicio: str = None, 
        fecha_fin: str = None
    ) -> List[Tuple]:
        """Construye filtro de fechas."""
        filtros = []
        
        if fecha_inicio:
            filtros.append((campo, '>=', fecha_inicio))
        if fecha_fin:
            filtros.append((campo, '<=', fecha_fin))
        
        return filtros
    
    def construir_filtro_estado(self, modelo: str, solo_confirmados: bool = True) -> List[Tuple]:
        """Construye filtro de estado según el modelo."""
        info = self.matriz.obtener_info_modelo(modelo)
        if not info:
            return []
        
        if solo_confirmados and 'filtro_confirmado' in info:
            return info['filtro_confirmado']
        
        return []
    
    def obtener_campos_consulta(
        self, 
        modelo: str, 
        incluir_relaciones: bool = True,
        campos_extra: List[str] = None
    ) -> List[str]:
        """Obtiene los campos óptimos para una consulta."""
        info = self.matriz.obtener_info_modelo(modelo)
        if not info:
            return ['id', 'name']
        
        campos = list(info.get('campos_clave', []))
        if 'id' not in campos:
            campos.insert(0, 'id')
        
        if incluir_relaciones:
            for campo, info_campo in info.get('campos', {}).items():
                if info_campo.get('tipo') in ['many2one'] and campo not in campos:
                    campos.append(campo)
        
        if campos_extra:
            for c in campos_extra:
                if c not in campos:
                    campos.append(c)
        
        return campos
    
    def generar_consulta_completa(
        self,
        modelo: str,
        fecha_inicio: str = None,
        fecha_fin: str = None,
        filtros_adicionales: List[Tuple] = None,
        campos: List[str] = None,
        limite: int = None,
        orden: str = None
    ) -> Dict:
        """
        Genera una consulta completa para Odoo.
        
        Returns:
            Dict con modelo, domain, fields, limit, order
        """
        modelo_real = self.matriz.obtener_modelo(modelo)
        if not modelo_real:
            modelo_real = modelo
        
        info = self.matriz.obtener_info_modelo(modelo_real)
        
        # Construir domain
        domain = []
        
        # Filtro de fechas
        campo_fecha = info.get('campo_fecha') if info else None
        if campo_fecha and (fecha_inicio or fecha_fin):
            domain.extend(self.construir_filtro_fecha(campo_fecha, fecha_inicio, fecha_fin))
        
        # Filtro de confirmados
        domain.extend(self.construir_filtro_estado(modelo_real))
        
        # Filtros adicionales
        if filtros_adicionales:
            domain.extend(filtros_adicionales)
        
        # Campos
        if campos:
            fields = campos
        else:
            fields = self.obtener_campos_consulta(modelo_real)
        
        # Orden
        if not orden:
            if campo_fecha:
                orden = f'{campo_fecha} desc'
            else:
                orden = 'id desc'
        
        return {
            'modelo': modelo_real,
            'domain': domain,
            'fields': fields,
            'limit': limite,
            'order': orden,
        }


# ============================================================
# MOTOR DE ANÁLISIS ESTADÍSTICO
# ============================================================

class MotorEstadistico:
    """
    Motor de análisis estadístico avanzado.
    Calcula métricas, tendencias y predicciones con alta precisión.
    """
    
    @staticmethod
    def calcular_metricas_basicas(datos: List[float]) -> Dict:
        """Calcula métricas estadísticas básicas."""
        if not datos or len(datos) == 0:
            return {
                'count': 0,
                'sum': 0,
                'mean': 0,
                'median': 0,
                'std': 0,
                'min': 0,
                'max': 0,
                'range': 0,
            }
        
        datos_limpios = [x for x in datos if x is not None and not math.isnan(x) and not math.isinf(x)]
        
        if not datos_limpios:
            return {
                'count': len(datos),
                'sum': 0,
                'mean': 0,
                'median': 0,
                'std': 0,
                'min': 0,
                'max': 0,
                'range': 0,
            }
        
        return {
            'count': len(datos_limpios),
            'sum': sum(datos_limpios),
            'mean': statistics.mean(datos_limpios),
            'median': statistics.median(datos_limpios),
            'std': statistics.stdev(datos_limpios) if len(datos_limpios) > 1 else 0,
            'min': min(datos_limpios),
            'max': max(datos_limpios),
            'range': max(datos_limpios) - min(datos_limpios),
        }
    
    @staticmethod
    def calcular_crecimiento(valor_actual: float, valor_anterior: float) -> float:
        """Calcula el porcentaje de crecimiento."""
        if valor_anterior == 0:
            return 100.0 if valor_actual > 0 else 0.0
        return ((valor_actual - valor_anterior) / abs(valor_anterior)) * 100
    
    @staticmethod
    def calcular_tendencia(datos: List[float]) -> Dict:
        """Calcula la tendencia de una serie temporal."""
        if not datos or len(datos) < 2:
            return {
                'tendencia': 'insuficiente',
                'pendiente': 0,
                'direccion': 'estable',
                'fuerza': 0,
            }
        
        n = len(datos)
        x = list(range(n))
        
        # Calcular regresión lineal simple
        x_mean = sum(x) / n
        y_mean = sum(datos) / n
        
        numerador = sum((x[i] - x_mean) * (datos[i] - y_mean) for i in range(n))
        denominador = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        pendiente = numerador / denominador if denominador != 0 else 0
        
        # Calcular R²
        ss_tot = sum((y - y_mean) ** 2 for y in datos)
        intercepto = y_mean - pendiente * x_mean
        predicciones = [pendiente * xi + intercepto for xi in x]
        ss_res = sum((datos[i] - predicciones[i]) ** 2 for i in range(n))
        r_cuadrado = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determinar dirección y fuerza
        if abs(pendiente) < 0.01 * y_mean:
            direccion = 'estable'
        elif pendiente > 0:
            direccion = 'creciente'
        else:
            direccion = 'decreciente'
        
        fuerza = abs(r_cuadrado) * 100
        
        return {
            'tendencia': 'calculada',
            'pendiente': pendiente,
            'direccion': direccion,
            'fuerza': fuerza,
            'r_cuadrado': r_cuadrado,
        }
    
    @staticmethod
    def predecir_valor(datos: List[float], periodos_adelante: int = 1) -> List[float]:
        """Predice valores futuros usando regresión lineal."""
        if not datos or len(datos) < 2:
            return [0] * periodos_adelante
        
        n = len(datos)
        x = list(range(n))
        
        x_mean = sum(x) / n
        y_mean = sum(datos) / n
        
        numerador = sum((x[i] - x_mean) * (datos[i] - y_mean) for i in range(n))
        denominador = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        pendiente = numerador / denominador if denominador != 0 else 0
        intercepto = y_mean - pendiente * x_mean
        
        predicciones = []
        for i in range(1, periodos_adelante + 1):
            valor = pendiente * (n + i - 1) + intercepto
            predicciones.append(max(0, valor))  # No permitir valores negativos
        
        return predicciones
    
    @staticmethod
    def calcular_percentiles(datos: List[float], percentiles: List[int] = None) -> Dict:
        """Calcula percentiles de una distribución."""
        if percentiles is None:
            percentiles = [10, 25, 50, 75, 90, 95, 99]
        
        if not datos or len(datos) == 0:
            return {f'p{p}': 0 for p in percentiles}
        
        datos_ordenados = sorted([x for x in datos if x is not None])
        n = len(datos_ordenados)
        
        resultado = {}
        for p in percentiles:
            idx = (p / 100) * (n - 1)
            lower = int(idx)
            upper = min(lower + 1, n - 1)
            frac = idx - lower
            
            if frac == 0:
                resultado[f'p{p}'] = datos_ordenados[lower]
            else:
                resultado[f'p{p}'] = datos_ordenados[lower] * (1 - frac) + datos_ordenados[upper] * frac
        
        return resultado


# ============================================================
# GENERADOR DE PROMPTS INTELIGENTE
# ============================================================

class GeneradorPrompts:
    """
    Sistema de generación de prompts y respuestas profesionales.
    Formatea datos en reportes claros y accionables.
    """
    
    # Templates de respuestas profesionales
    TEMPLATES = {
        'encabezado_reporte': """
## {titulo}

**Período:** {periodo} | **Generado:** {fecha_generacion}  
**Confianza de datos:** {confianza}% | **Registros analizados:** {registros:,}

---
""",
        
        'resumen_ejecutivo': """
### Resumen Ejecutivo

{resumen}
""",
        
        'metricas_principales': """
### Métricas Principales

| Métrica | Valor | Variación |
|---------|-------|-----------|
{filas_metricas}
""",
        
        'tabla_datos': """
### {titulo_tabla}

{tabla}
""",
        
        'alertas': """
### Alertas y Recomendaciones

{alertas}
""",
        
        'tendencia': """
### Análisis de Tendencia

- **Dirección:** {direccion}
- **Fuerza:** {fuerza:.1f}%
- **Proyección:** {proyeccion}
""",
        
        'footer': """
---
*Análisis generado por ANDROMEDA - IA Predictiva Empresarial*
""",
    }
    
    @classmethod
    def generar_reporte_completo(
        cls,
        titulo: str,
        periodo: str,
        datos: Dict,
        df: pd.DataFrame = None,
        metricas: Dict = None,
        alertas: List[str] = None,
        tendencia: Dict = None,
        confianza: float = 99.0,
    ) -> str:
        """Genera un reporte completo en formato Markdown."""
        partes = []
        
        # Encabezado
        partes.append(cls.TEMPLATES['encabezado_reporte'].format(
            titulo=titulo,
            periodo=periodo,
            fecha_generacion=datetime.now().strftime('%d/%m/%Y %H:%M'),
            confianza=f'{confianza:.1f}',
            registros=datos.get('total_registros', len(df) if df is not None else 0),
        ))
        
        # Resumen ejecutivo
        if 'resumen' in datos:
            partes.append(cls.TEMPLATES['resumen_ejecutivo'].format(
                resumen=datos['resumen']
            ))
        
        # Métricas principales
        if metricas:
            filas = []
            for nombre, info in metricas.items():
                valor = info.get('valor', 0)
                variacion = info.get('variacion', 0)
                icono_var = '🟢' if variacion >= 0 else '🔴'
                filas.append(f"| {nombre} | {cls._formatear_valor(valor, info.get('tipo', 'numero'))} | {icono_var} {variacion:+.1f}% |")
            
            partes.append(cls.TEMPLATES['metricas_principales'].format(
                filas_metricas='\n'.join(filas)
            ))
        
        # Tabla de datos
        if df is not None and not df.empty:
            tabla_md = cls._df_a_markdown(df.head(20))
            partes.append(cls.TEMPLATES['tabla_datos'].format(
                titulo_tabla="Detalle de Datos",
                tabla=tabla_md
            ))
        
        # Tendencia
        if tendencia:
            partes.append(cls.TEMPLATES['tendencia'].format(
                direccion=tendencia.get('direccion', 'estable'),
                fuerza=tendencia.get('fuerza', 0),
                proyeccion=tendencia.get('proyeccion', 'Sin proyección disponible'),
            ))
        
        # Alertas
        if alertas:
            alertas_md = '\n'.join([f"- {a}" for a in alertas])
            partes.append(cls.TEMPLATES['alertas'].format(alertas=alertas_md))
        
        # Footer
        partes.append(cls.TEMPLATES['footer'])
        
        return '\n'.join(partes)
    
    @classmethod
    def _formatear_valor(cls, valor: Any, tipo: str = 'numero') -> str:
        """Formatea un valor según su tipo."""
        if valor is None:
            return 'N/A'
        
        if tipo == 'moneda':
            return f"${valor:,.2f}"
        elif tipo == 'porcentaje':
            return f"{valor:.1f}%"
        elif tipo == 'entero':
            return f"{int(valor):,}"
        elif tipo == 'numero':
            if isinstance(valor, float):
                return f"{valor:,.2f}"
            return f"{valor:,}"
        else:
            return str(valor)
    
    @classmethod
    def _df_a_markdown(cls, df: pd.DataFrame) -> str:
        """Convierte un DataFrame a tabla Markdown."""
        if df is None or df.empty:
            return "*Sin datos*"
        
        # Limpiar valores de Odoo (tuplas)
        df_limpio = df.copy()
        for col in df_limpio.columns:
            df_limpio[col] = df_limpio[col].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else x
            )
        
        # Generar Markdown
        columnas = list(df_limpio.columns)
        header = "| " + " | ".join(str(c).replace('_', ' ').title() for c in columnas) + " |"
        separator = "| " + " | ".join("---" for _ in columnas) + " |"
        
        filas = []
        for _, row in df_limpio.iterrows():
            valores = []
            for col in columnas:
                val = row[col]
                if isinstance(val, float):
                    if 'total' in col.lower() or 'monto' in col.lower() or 'precio' in col.lower():
                        valores.append(f"${val:,.2f}")
                    else:
                        valores.append(f"{val:,.2f}")
                else:
                    valores.append(str(val) if val is not None else '')
            filas.append("| " + " | ".join(valores) + " |")
        
        return '\n'.join([header, separator] + filas)
    
    @classmethod
    def generar_respuesta_error(cls, error: str, sugerencia: str = None) -> str:
        """Genera una respuesta de error amigable."""
        respuesta = f"""
##No fue posible completar el análisis

**Problema detectado:** {error}

"""
        if sugerencia:
            respuesta += f"""
### Sugerencias

{sugerencia}
"""
        
        respuesta += """
---
*Si el problema persiste, intenta reformular tu consulta o contacta soporte.*
"""
        return respuesta


# ============================================================
# CEREBRO PRINCIPAL - INTEGRACIÓN COMPLETA
# ============================================================

class CerebroAndromeda:
    """
    Cerebro principal de ANDROMEDA.
    Integra matrices, limpieza, análisis y generación de reportes.
    """
    
    def __init__(self, conector_odoo=None):
        """Inicializa el cerebro con todos sus componentes."""
        self.odoo = conector_odoo
        
        # Componentes
        self.matriz = MatrizDatosOdoo()
        self.limpiador = LimpiadorDatos()
        self.generador_consultas = GeneradorConsultas(self.matriz)
        self.estadistico = MotorEstadistico()
        self.generador_prompts = GeneradorPrompts()
        
        # Cache de datos
        self.cache = {}
        self.cache_timeout = 300  # 5 minutos
        
        # Estadísticas de sesión
        self.stats = {
            'consultas_procesadas': 0,
            'datos_analizados': 0,
            'errores': 0,
            'confianza_promedio': 0,
        }
        
        print("Cerebro ANDROMEDA inicializado")
    
    def set_conector(self, conector_odoo):
        """Establece el conector Odoo."""
        self.odoo = conector_odoo
    
    def analizar(
        self,
        consulta: str,
        tipo_reporte: TipoReporte = TipoReporte.GENERAL,
        tipo_analisis: TipoAnalisis = TipoAnalisis.DETALLADO,
        fecha_inicio: str = None,
        fecha_fin: str = None,
        filtros: Dict = None,
        limite: int = 100,
    ) -> ResultadoAnalisis:
        """
        Ejecuta un análisis completo basado en la consulta.
        
        Este es el método principal que procesa cualquier tipo de solicitud.
        """
        self.stats['consultas_procesadas'] += 1
        
        try:
            # 1. Interpretar la consulta
            modelo, _ = self._interpretar_consulta(consulta, tipo_reporte)
            
            if not modelo:
                return ResultadoAnalisis(
                    exito=False,
                    datos={},
                    df=None,
                    resumen="No se pudo interpretar la consulta",
                    respuesta_md=self.generador_prompts.generar_respuesta_error(
                        "No entendí qué tipo de análisis necesitas",
                        "Prueba con frases como: 'ventas de hoy', 'inventario por tienda', 'facturación del mes'"
                    ),
                    confianza=0,
                    registros_totales=0,
                    registros_validos=0,
                    registros_corregidos=0,
                    alertas=[],
                    metricas={},
                )
            
            # 2. Obtener datos de Odoo
            df, _ = self._obtener_datos(modelo, fecha_inicio, fecha_fin, filtros, limite)
            
            if df is None or df.empty:
                return ResultadoAnalisis(
                    exito=False,
                    datos={},
                    df=None,
                    resumen="No se encontraron datos",
                    respuesta_md=self.generador_prompts.generar_respuesta_error(
                        "No hay datos para el período o filtros especificados",
                        "Intenta con un período más amplio o verifica los filtros"
                    ),
                    confianza=0,
                    registros_totales=0,
                    registros_validos=0,
                    registros_corregidos=0,
                    alertas=["Sin datos disponibles"],
                    metricas={},
                )
            
            # 3. Limpiar y validar datos
            df_limpio, confianza, stats_limpieza = self.limpiador.limpiar_dataframe(df, modelo)
            
            # 4. Ejecutar análisis según tipo
            resultado_analisis = self._ejecutar_analisis(
                df_limpio, 
                modelo, 
                tipo_analisis,
                fecha_inicio,
                fecha_fin
            )
            
            # 5. Generar respuesta
            respuesta_md = self._generar_respuesta(
                modelo,
                resultado_analisis,
                df_limpio,
                confianza,
                fecha_inicio,
                fecha_fin,
                tipo_analisis
            )
            
            self.stats['datos_analizados'] += len(df_limpio)
            
            # Actualizar confianza promedio
            total = self.stats['consultas_procesadas']
            self.stats['confianza_promedio'] = (
                (self.stats['confianza_promedio'] * (total - 1) + confianza * 100) / total
            )
            
            return ResultadoAnalisis(
                exito=True,
                datos=resultado_analisis,
                df=df_limpio,
                resumen=resultado_analisis.get('resumen', ''),
                respuesta_md=respuesta_md,
                confianza=confianza * 100,
                registros_totales=stats_limpieza['registros_procesados'],
                registros_validos=stats_limpieza['registros_validos'],
                registros_corregidos=stats_limpieza['registros_corregidos'],
                alertas=resultado_analisis.get('alertas', []),
                metricas=resultado_analisis.get('metricas', {}),
            )
            
        except Exception as e:
            self.stats['errores'] += 1
            return ResultadoAnalisis(
                exito=False,
                datos={'error': str(e)},
                df=None,
                resumen=f"Error: {str(e)}",
                respuesta_md=self.generador_prompts.generar_respuesta_error(
                    str(e),
                    "Verifica la conexión a Odoo e intenta de nuevo"
                ),
                confianza=0,
                registros_totales=0,
                registros_validos=0,
                registros_corregidos=0,
                alertas=[f"Error: {str(e)}"],
                metricas={},
            )
    
    def _interpretar_consulta(self, consulta: str, tipo_reporte: TipoReporte) -> Tuple[str, str]:
        """Interpreta la consulta y determina modelo y acción."""
        consulta_lower = consulta.lower()
        
        # Mapeo de palabras clave a modelos
        keywords = {
            'ventas': ('sale.order', 'analizar'),
            'pedidos': ('sale.order', 'analizar'),
            'pos': ('pos.order', 'analizar'),
            'tickets': ('pos.order', 'analizar'),
            'caja': ('pos.order', 'analizar'),
            'inventario': ('stock.quant', 'analizar'),
            'stock': ('stock.quant', 'analizar'),
            'existencias': ('stock.quant', 'analizar'),
            'almacen': ('stock.warehouse', 'listar'),
            'almacenes': ('stock.warehouse', 'listar'),
            'tienda': ('stock.warehouse', 'listar'),
            'tiendas': ('stock.warehouse', 'listar'),
            'facturas': ('account.move', 'analizar'),
            'facturacion': ('account.move', 'analizar'),
            'clientes': ('res.partner', 'analizar'),
            'productos': ('product.product', 'analizar'),
            'compras': ('purchase.order', 'analizar'),
            'empleados': ('hr.employee', 'listar'),
            'empresas': ('res.company', 'listar'),
        }
        
        for keyword, (modelo, accion) in keywords.items():
            if keyword in consulta_lower:
                return modelo, accion
        
        # Default basado en tipo de reporte
        defaults = {
            TipoReporte.VENTAS: ('sale.order', 'analizar'),
            TipoReporte.INVENTARIO: ('stock.quant', 'analizar'),
            TipoReporte.FINANZAS: ('account.move', 'analizar'),
            TipoReporte.CLIENTES: ('res.partner', 'analizar'),
            TipoReporte.PRODUCTOS: ('product.product', 'analizar'),
        }
        
        return defaults.get(tipo_reporte, (None, None))
    
    def _obtener_datos(
        self, 
        modelo: str, 
        fecha_inicio: str, 
        fecha_fin: str,
        filtros: Dict,
        limite: int
    ) -> Tuple[pd.DataFrame, List]:
        """Obtiene datos de Odoo."""
        if not self.odoo or not self.odoo.conectado:
            return None, []
        
        # Generar consulta
        query = self.generador_consultas.generar_consulta_completa(
            modelo=modelo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            filtros_adicionales=list(filtros.items()) if filtros else None,
            limite=limite,
        )
        
        try:
            # Ejecutar consulta via ConectorOdoo (ARQ-003)
            registros = self.odoo.search_read(
                query['modelo'],
                query['domain'],
                campos=query['fields'],
                limite=query['limit'],
                orden=query.get('order')
            )
            
            if not registros:
                return pd.DataFrame(), []
            
            df = pd.DataFrame(registros)
            
            return df, registros
            
        except Exception as e:
            logger.error(f"Error obteniendo datos: {e}")
            return None, []
    
    def _ejecutar_analisis(
        self,
        df: pd.DataFrame,
        modelo: str,
        tipo_analisis: TipoAnalisis,
        fecha_inicio: str,
        fecha_fin: str
    ) -> Dict:
        """Ejecuta el análisis según el tipo solicitado."""
        resultado = {
            'modelo': modelo,
            'tipo_analisis': tipo_analisis.value,
            'registros': len(df),
            'metricas': {},
            'alertas': [],
        }
        
        info_modelo = self.matriz.obtener_info_modelo(modelo)
        campo_monto = info_modelo.get('campo_monto') if info_modelo else None
        
        # Calcular métricas según el modelo
        if campo_monto and campo_monto in df.columns:
            montos = df[campo_monto].tolist()
            stats = self.estadistico.calcular_metricas_basicas(montos)
            
            resultado['metricas'] = {
                'Total': {'valor': stats['sum'], 'tipo': 'moneda', 'variacion': 0},
                'Promedio': {'valor': stats['mean'], 'tipo': 'moneda', 'variacion': 0},
                'Máximo': {'valor': stats['max'], 'tipo': 'moneda', 'variacion': 0},
                'Mínimo': {'valor': stats['min'], 'tipo': 'moneda', 'variacion': 0},
                'Transacciones': {'valor': stats['count'], 'tipo': 'entero', 'variacion': 0},
            }
            
            # Análisis de tendencia
            if tipo_analisis in [TipoAnalisis.TENDENCIA, TipoAnalisis.DETALLADO]:
                tendencia = self.estadistico.calcular_tendencia(montos[-30:])  # Últimos 30 registros
                resultado['tendencia'] = tendencia
            
            # Detectar alertas
            if stats['std'] > stats['mean'] * 0.5:
                resultado['alertas'].append('Alta variabilidad en los montos')
            
            if stats['count'] < 10:
                resultado['alertas'].append('Pocos registros para análisis estadístico robusto')
        
        # Generar resumen
        periodo = f"{fecha_inicio or 'inicio'} a {fecha_fin or 'hoy'}"
        resultado['resumen'] = self._generar_resumen(modelo, resultado, periodo)
        
        return resultado
    
    def _generar_resumen(self, modelo: str, datos: Dict, periodo: str) -> str:
        """Genera un resumen textual del análisis."""
        info = self.matriz.obtener_info_modelo(modelo)
        nombre_modelo = info['descripcion'] if info else modelo
        
        metricas = datos.get('metricas', {})
        total = metricas.get('Total', {}).get('valor', 0)
        count = metricas.get('Transacciones', {}).get('valor', 0)
        
        resumen = f"Se analizaron **{count:,.0f}** registros de **{nombre_modelo}** "
        resumen += f"para el período {periodo}. "
        
        if total:
            resumen += f"El monto total es de **${total:,.2f}**. "
        
        if datos.get('tendencia'):
            direccion = datos['tendencia'].get('direccion', 'estable')
            resumen += f"La tendencia es **{direccion}**."
        
        return resumen
    
    def _generar_respuesta(
        self,
        modelo: str,
        datos: Dict,
        df: pd.DataFrame,
        confianza: float,
        fecha_inicio: str,
        fecha_fin: str,
        tipo_analisis: TipoAnalisis
    ) -> str:
        """Genera la respuesta completa en Markdown."""
        info = self.matriz.obtener_info_modelo(modelo)
        titulo = info['descripcion'] if info else modelo.replace('.', ' ').title()
        
        periodo = f"{fecha_inicio or 'inicio'} a {fecha_fin or 'hoy'}"
        
        return self.generador_prompts.generar_reporte_completo(
            titulo=f"Análisis de {titulo}",
            periodo=periodo,
            datos=datos,
            df=df,
            metricas=datos.get('metricas'),
            alertas=datos.get('alertas'),
            tendencia=datos.get('tendencia'),
            confianza=confianza * 100,
        )
    
    # ============================================================
    # MÉTODOS DE CONSULTAS ESPECÍFICAS
    # ============================================================
    
    def ventas_por_empresa(self, fecha_inicio: str = None, fecha_fin: str = None) -> ResultadoAnalisis:
        """Análisis de ventas agrupado por empresa."""
        return self.analizar(
            consulta="ventas por empresa",
            tipo_reporte=TipoReporte.VENTAS,
            tipo_analisis=TipoAnalisis.COMPARATIVO,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
    
    def inventario_por_tienda(self, fecha_inicio: str = None, fecha_fin: str = None) -> ResultadoAnalisis:
        """Análisis de inventario por tienda/almacén."""
        return self.analizar(
            consulta="inventario por almacen tienda",
            tipo_reporte=TipoReporte.INVENTARIO,
            tipo_analisis=TipoAnalisis.DETALLADO,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
    
    def analisis_completo(self, fecha_inicio: str = None, fecha_fin: str = None) -> str:
        """Genera un análisis completo del negocio."""
        partes = []
        
        partes.append("# Análisis Integral del Negocio\n")
        partes.append(f"**Período:** {fecha_inicio or 'Histórico'} a {fecha_fin or 'Hoy'}\n")
        partes.append("---\n")
        
        # Ventas
        ventas = self.analizar("ventas", TipoReporte.VENTAS, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        if ventas.exito:
            partes.append("## Ventas\n")
            partes.append(ventas.resumen + "\n")
        
        # Inventario
        inv = self.analizar("inventario", TipoReporte.INVENTARIO)
        if inv.exito:
            partes.append("## Inventario\n")
            partes.append(inv.resumen + "\n")
        
        # Facturación
        fact = self.analizar("facturas", TipoReporte.FINANZAS, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        if fact.exito:
            partes.append("## Facturación\n")
            partes.append(fact.resumen + "\n")
        
        return '\n'.join(partes)


# ============================================================
# FUNCIONES DE UTILIDAD
# ============================================================

def obtener_cerebro(conector_odoo=None) -> CerebroAndromeda:
    """Factory function para obtener instancia del cerebro."""
    return CerebroAndromeda(conector_odoo)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" CEREBRO ANDROMEDA - Test")
    print("=" * 60)
    
    # Test de matriz de datos
    print("\nTest de Matriz de Datos:")
    print(f"  Modelo 'ventas' -> {MatrizDatosOdoo.obtener_modelo('ventas')}")
    print(f"  Modelo 'inventario' -> {MatrizDatosOdoo.obtener_modelo('inventario')}")
    print(f"  Campos clave sale.order: {MatrizDatosOdoo.obtener_campos_clave('sale.order')}")
    
    # Test de estadísticas
    print("\nTest de Motor Estadístico:")
    datos_test = [100, 150, 200, 180, 220, 190, 250]
    stats = MotorEstadistico.calcular_metricas_basicas(datos_test)
    print(f"  Datos: {datos_test}")
    print(f"  Media: {stats['mean']:.2f}")
    print(f"  Mediana: {stats['median']:.2f}")
    print(f"  Std: {stats['std']:.2f}")
    
    tendencia = MotorEstadistico.calcular_tendencia(datos_test)
    print(f"  Tendencia: {tendencia['direccion']} (fuerza: {tendencia['fuerza']:.1f}%)")
    
    # Test de prompts
    print("\nTest de Generador de Prompts:")
    respuesta = GeneradorPrompts.generar_reporte_completo(
        titulo="Test de Ventas",
        periodo="Enero 2026",
        datos={'resumen': 'Este es un test del generador de reportes.', 'total_registros': 100},
        metricas={
            'Total Ventas': {'valor': 150000, 'tipo': 'moneda', 'variacion': 12.5},
            'Transacciones': {'valor': 450, 'tipo': 'entero', 'variacion': -3.2},
        },
        confianza=99.5,
    )
    print(respuesta[:500] + "...")
    
    print("\nTests completados")
