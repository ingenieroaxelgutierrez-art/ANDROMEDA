# ============================================================
# MODELOS ODOO - Definición Completa de Todos los Modelos
# ============================================================
# Base de conocimiento exhaustiva para la IA PRO
# ============================================================

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class CampoOdoo:
    """Definición de un campo de Odoo."""
    nombre: str
    tipo: str
    etiqueta: str
    descripcion: str = ""
    requerido: bool = False
    readonly: bool = False
    relacion: str = ""  # Para campos Many2one, One2many, Many2many


@dataclass
class ModeloOdoo:
    """Definición completa de un modelo de Odoo."""
    nombre_tecnico: str
    nombre_display: str
    descripcion: str
    campos: Dict[str, CampoOdoo] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)


# ============================================================
# DEFINICIONES DE MODELOS
# ============================================================

MODELOS_ODOO = {
    
    # ========== VENTAS ==========
    'sale.order': ModeloOdoo(
        nombre_tecnico='sale.order',
        nombre_display='Orden de Venta',
        descripcion='Órdenes de venta (cotizaciones y pedidos confirmados)',
        keywords=['venta', 'ventas', 'orden', 'pedido', 'cotización', 'sale', 'order'],
        campos={
            'name': CampoOdoo('name', 'char', 'Número', 'Número de orden (SO001)'),
            'partner_id': CampoOdoo('partner_id', 'many2one', 'Cliente', relacion='res.partner'),
            'partner_invoice_id': CampoOdoo('partner_invoice_id', 'many2one', 'Dirección Factura', relacion='res.partner'),
            'partner_shipping_id': CampoOdoo('partner_shipping_id', 'many2one', 'Dirección Envío', relacion='res.partner'),
            'date_order': CampoOdoo('date_order', 'datetime', 'Fecha Orden'),
            'validity_date': CampoOdoo('validity_date', 'date', 'Fecha Validez'),
            'confirmation_date': CampoOdoo('confirmation_date', 'datetime', 'Fecha Confirmación'),
            'user_id': CampoOdoo('user_id', 'many2one', 'Vendedor', relacion='res.users'),
            'team_id': CampoOdoo('team_id', 'many2one', 'Equipo de Ventas', relacion='crm.team'),
            'company_id': CampoOdoo('company_id', 'many2one', 'Compañía', relacion='res.company'),
            'order_line': CampoOdoo('order_line', 'one2many', 'Líneas', relacion='sale.order.line'),
            'amount_untaxed': CampoOdoo('amount_untaxed', 'monetary', 'Subtotal'),
            'amount_tax': CampoOdoo('amount_tax', 'monetary', 'Impuestos'),
            'amount_total': CampoOdoo('amount_total', 'monetary', 'Total'),
            'state': CampoOdoo('state', 'selection', 'Estado', 'draft/sent/sale/done/cancel'),
            'invoice_status': CampoOdoo('invoice_status', 'selection', 'Estado Factura'),
            'pricelist_id': CampoOdoo('pricelist_id', 'many2one', 'Lista de Precios', relacion='product.pricelist'),
            'currency_id': CampoOdoo('currency_id', 'many2one', 'Moneda', relacion='res.currency'),
            'payment_term_id': CampoOdoo('payment_term_id', 'many2one', 'Términos de Pago', relacion='account.payment.term'),
            'note': CampoOdoo('note', 'text', 'Notas'),
            'origin': CampoOdoo('origin', 'char', 'Documento Origen'),
            'campaign_id': CampoOdoo('campaign_id', 'many2one', 'Campaña', relacion='utm.campaign'),
        }
    ),
    
    'sale.order.line': ModeloOdoo(
        nombre_tecnico='sale.order.line',
        nombre_display='Línea de Venta',
        descripcion='Detalle de productos en órdenes de venta',
        keywords=['línea', 'detalle', 'producto venta'],
        campos={
            'order_id': CampoOdoo('order_id', 'many2one', 'Orden', relacion='sale.order'),
            'product_id': CampoOdoo('product_id', 'many2one', 'Producto', relacion='product.product'),
            'product_template_id': CampoOdoo('product_template_id', 'many2one', 'Template', relacion='product.template'),
            'name': CampoOdoo('name', 'text', 'Descripción'),
            'product_uom_qty': CampoOdoo('product_uom_qty', 'float', 'Cantidad'),
            'product_uom': CampoOdoo('product_uom', 'many2one', 'Unidad', relacion='uom.uom'),
            'price_unit': CampoOdoo('price_unit', 'float', 'Precio Unitario'),
            'tax_id': CampoOdoo('tax_id', 'many2many', 'Impuestos', relacion='account.tax'),
            'discount': CampoOdoo('discount', 'float', 'Descuento %'),
            'price_subtotal': CampoOdoo('price_subtotal', 'monetary', 'Subtotal'),
            'price_total': CampoOdoo('price_total', 'monetary', 'Total'),
            'qty_delivered': CampoOdoo('qty_delivered', 'float', 'Cantidad Entregada'),
            'qty_invoiced': CampoOdoo('qty_invoiced', 'float', 'Cantidad Facturada'),
            'salesman_id': CampoOdoo('salesman_id', 'many2one', 'Vendedor', relacion='res.users'),
        }
    ),
    
    # ========== PUNTO DE VENTA ==========
    'pos.order': ModeloOdoo(
        nombre_tecnico='pos.order',
        nombre_display='Ticket POS',
        descripcion='Ventas de punto de venta (tickets)',
        keywords=['pos', 'ticket', 'punto de venta', 'caja', 'retail'],
        campos={
            'name': CampoOdoo('name', 'char', 'Número Ticket'),
            'session_id': CampoOdoo('session_id', 'many2one', 'Sesión', relacion='pos.session'),
            'config_id': CampoOdoo('config_id', 'many2one', 'Punto de Venta', relacion='pos.config'),
            'partner_id': CampoOdoo('partner_id', 'many2one', 'Cliente', relacion='res.partner'),
            'user_id': CampoOdoo('user_id', 'many2one', 'Cajero', relacion='res.users'),
            'employee_id': CampoOdoo('employee_id', 'many2one', 'Empleado', relacion='hr.employee'),
            'date_order': CampoOdoo('date_order', 'datetime', 'Fecha'),
            'lines': CampoOdoo('lines', 'one2many', 'Líneas', relacion='pos.order.line'),
            'amount_total': CampoOdoo('amount_total', 'float', 'Total'),
            'amount_tax': CampoOdoo('amount_tax', 'float', 'Impuestos'),
            'amount_paid': CampoOdoo('amount_paid', 'float', 'Pagado'),
            'amount_return': CampoOdoo('amount_return', 'float', 'Cambio'),
            'state': CampoOdoo('state', 'selection', 'Estado', 'draft/paid/done/invoiced/cancel'),
            'payment_ids': CampoOdoo('payment_ids', 'one2many', 'Pagos', relacion='pos.payment'),
            'pricelist_id': CampoOdoo('pricelist_id', 'many2one', 'Lista Precios', relacion='product.pricelist'),
            'fiscal_position_id': CampoOdoo('fiscal_position_id', 'many2one', 'Posición Fiscal', relacion='account.fiscal.position'),
            'table_id': CampoOdoo('table_id', 'many2one', 'Mesa', relacion='restaurant.table'),
            'customer_count': CampoOdoo('customer_count', 'integer', 'Número Clientes'),
            'margin': CampoOdoo('margin', 'monetary', 'Margen'),
        }
    ),
    
    'pos.session': ModeloOdoo(
        nombre_tecnico='pos.session',
        nombre_display='Sesión POS',
        descripcion='Sesiones de caja del punto de venta',
        keywords=['sesión', 'caja', 'turno', 'apertura', 'cierre'],
        campos={
            'name': CampoOdoo('name', 'char', 'Nombre Sesión'),
            'config_id': CampoOdoo('config_id', 'many2one', 'Punto de Venta', relacion='pos.config'),
            'user_id': CampoOdoo('user_id', 'many2one', 'Responsable', relacion='res.users'),
            'start_at': CampoOdoo('start_at', 'datetime', 'Hora Apertura'),
            'stop_at': CampoOdoo('stop_at', 'datetime', 'Hora Cierre'),
            'state': CampoOdoo('state', 'selection', 'Estado', 'opening/opened/closing/closed'),
            'order_ids': CampoOdoo('order_ids', 'one2many', 'Tickets', relacion='pos.order'),
            'order_count': CampoOdoo('order_count', 'integer', 'Número Tickets'),
            'total_payments_amount': CampoOdoo('total_payments_amount', 'monetary', 'Total Ventas'),
            'cash_register_balance_start': CampoOdoo('cash_register_balance_start', 'monetary', 'Saldo Inicial'),
            'cash_register_balance_end': CampoOdoo('cash_register_balance_end', 'monetary', 'Saldo Final'),
            'cash_register_balance_end_real': CampoOdoo('cash_register_balance_end_real', 'monetary', 'Saldo Real'),
            'cash_register_difference': CampoOdoo('cash_register_difference', 'monetary', 'Diferencia'),
        }
    ),
    
    'pos.payment': ModeloOdoo(
        nombre_tecnico='pos.payment',
        nombre_display='Pago POS',
        descripcion='Pagos recibidos en punto de venta',
        keywords=['pago pos', 'método pago', 'efectivo', 'tarjeta'],
        campos={
            'pos_order_id': CampoOdoo('pos_order_id', 'many2one', 'Ticket', relacion='pos.order'),
            'payment_method_id': CampoOdoo('payment_method_id', 'many2one', 'Método', relacion='pos.payment.method'),
            'amount': CampoOdoo('amount', 'monetary', 'Monto'),
            'payment_date': CampoOdoo('payment_date', 'datetime', 'Fecha'),
            'session_id': CampoOdoo('session_id', 'many2one', 'Sesión', relacion='pos.session'),
        }
    ),
    
    # ========== FACTURACIÓN ==========
    'account.move': ModeloOdoo(
        nombre_tecnico='account.move',
        nombre_display='Factura/Asiento',
        descripcion='Facturas, notas de crédito y asientos contables',
        keywords=['factura', 'invoice', 'cfdi', 'nota crédito', 'asiento', 'contabilidad'],
        campos={
            'name': CampoOdoo('name', 'char', 'Número'),
            'move_type': CampoOdoo('move_type', 'selection', 'Tipo', 'entry/out_invoice/out_refund/in_invoice/in_refund'),
            'partner_id': CampoOdoo('partner_id', 'many2one', 'Cliente/Proveedor', relacion='res.partner'),
            'invoice_date': CampoOdoo('invoice_date', 'date', 'Fecha Factura'),
            'invoice_date_due': CampoOdoo('invoice_date_due', 'date', 'Fecha Vencimiento'),
            'date': CampoOdoo('date', 'date', 'Fecha Contable'),
            'ref': CampoOdoo('ref', 'char', 'Referencia'),
            'state': CampoOdoo('state', 'selection', 'Estado', 'draft/posted/cancel'),
            'payment_state': CampoOdoo('payment_state', 'selection', 'Estado Pago', 'not_paid/in_payment/paid/partial/reversed'),
            'amount_untaxed': CampoOdoo('amount_untaxed', 'monetary', 'Subtotal'),
            'amount_tax': CampoOdoo('amount_tax', 'monetary', 'Impuestos'),
            'amount_total': CampoOdoo('amount_total', 'monetary', 'Total'),
            'amount_residual': CampoOdoo('amount_residual', 'monetary', 'Saldo Pendiente'),
            'invoice_line_ids': CampoOdoo('invoice_line_ids', 'one2many', 'Líneas', relacion='account.move.line'),
            'currency_id': CampoOdoo('currency_id', 'many2one', 'Moneda', relacion='res.currency'),
            'company_id': CampoOdoo('company_id', 'many2one', 'Compañía', relacion='res.company'),
            'journal_id': CampoOdoo('journal_id', 'many2one', 'Diario', relacion='account.journal'),
            'invoice_user_id': CampoOdoo('invoice_user_id', 'many2one', 'Vendedor', relacion='res.users'),
            'invoice_origin': CampoOdoo('invoice_origin', 'char', 'Origen'),
            'invoice_payment_term_id': CampoOdoo('invoice_payment_term_id', 'many2one', 'Términos Pago', relacion='account.payment.term'),
            # Campos CFDI México
            'l10n_mx_edi_cfdi_uuid': CampoOdoo('l10n_mx_edi_cfdi_uuid', 'char', 'UUID CFDI'),
            'l10n_mx_edi_usage': CampoOdoo('l10n_mx_edi_usage', 'selection', 'Uso CFDI'),
            'l10n_mx_edi_payment_method_id': CampoOdoo('l10n_mx_edi_payment_method_id', 'many2one', 'Método Pago SAT'),
            'l10n_mx_edi_payment_policy': CampoOdoo('l10n_mx_edi_payment_policy', 'selection', 'Forma Pago'),
        }
    ),
    
    # ========== PAGOS ==========
    'account.payment': ModeloOdoo(
        nombre_tecnico='account.payment',
        nombre_display='Pago',
        descripcion='Pagos de clientes y a proveedores',
        keywords=['pago', 'cobro', 'transferencia', 'payment'],
        campos={
            'name': CampoOdoo('name', 'char', 'Número'),
            'payment_type': CampoOdoo('payment_type', 'selection', 'Tipo', 'outbound/inbound'),
            'partner_type': CampoOdoo('partner_type', 'selection', 'Tipo Partner', 'customer/supplier'),
            'partner_id': CampoOdoo('partner_id', 'many2one', 'Cliente/Proveedor', relacion='res.partner'),
            'amount': CampoOdoo('amount', 'monetary', 'Monto'),
            'currency_id': CampoOdoo('currency_id', 'many2one', 'Moneda', relacion='res.currency'),
            'date': CampoOdoo('date', 'date', 'Fecha'),
            'ref': CampoOdoo('ref', 'char', 'Referencia'),
            'journal_id': CampoOdoo('journal_id', 'many2one', 'Diario', relacion='account.journal'),
            'payment_method_id': CampoOdoo('payment_method_id', 'many2one', 'Método', relacion='account.payment.method'),
            'state': CampoOdoo('state', 'selection', 'Estado', 'draft/posted/sent/reconciled/cancelled'),
            'is_reconciled': CampoOdoo('is_reconciled', 'boolean', 'Conciliado'),
            'is_matched': CampoOdoo('is_matched', 'boolean', 'Emparejado'),
        }
    ),
    
    # ========== INVENTARIO ==========
    'product.template': ModeloOdoo(
        nombre_tecnico='product.template',
        nombre_display='Plantilla Producto',
        descripcion='Plantillas de productos (genérico)',
        keywords=['producto', 'artículo', 'catálogo'],
        campos={
            'name': CampoOdoo('name', 'char', 'Nombre'),
            'default_code': CampoOdoo('default_code', 'char', 'Referencia Interna'),
            'barcode': CampoOdoo('barcode', 'char', 'Código de Barras'),
            'type': CampoOdoo('type', 'selection', 'Tipo', 'consu/service/product'),
            'categ_id': CampoOdoo('categ_id', 'many2one', 'Categoría', relacion='product.category'),
            'list_price': CampoOdoo('list_price', 'float', 'Precio de Venta'),
            'standard_price': CampoOdoo('standard_price', 'float', 'Costo'),
            'qty_available': CampoOdoo('qty_available', 'float', 'Cantidad Disponible'),
            'virtual_available': CampoOdoo('virtual_available', 'float', 'Cantidad Pronosticada'),
            'incoming_qty': CampoOdoo('incoming_qty', 'float', 'Cantidad Entrante'),
            'outgoing_qty': CampoOdoo('outgoing_qty', 'float', 'Cantidad Saliente'),
            'uom_id': CampoOdoo('uom_id', 'many2one', 'Unidad de Medida', relacion='uom.uom'),
            'active': CampoOdoo('active', 'boolean', 'Activo'),
            'sale_ok': CampoOdoo('sale_ok', 'boolean', 'Puede Venderse'),
            'purchase_ok': CampoOdoo('purchase_ok', 'boolean', 'Puede Comprarse'),
            'description_sale': CampoOdoo('description_sale', 'text', 'Descripción Venta'),
            'weight': CampoOdoo('weight', 'float', 'Peso'),
            'volume': CampoOdoo('volume', 'float', 'Volumen'),
        }
    ),
    
    'product.product': ModeloOdoo(
        nombre_tecnico='product.product',
        nombre_display='Variante Producto',
        descripcion='Variantes específicas de productos',
        keywords=['variante', 'sku', 'producto específico'],
        campos={
            'name': CampoOdoo('name', 'char', 'Nombre'),
            'default_code': CampoOdoo('default_code', 'char', 'SKU'),
            'barcode': CampoOdoo('barcode', 'char', 'Código Barras'),
            'product_tmpl_id': CampoOdoo('product_tmpl_id', 'many2one', 'Template', relacion='product.template'),
            'lst_price': CampoOdoo('lst_price', 'float', 'Precio Venta'),
            'standard_price': CampoOdoo('standard_price', 'float', 'Costo'),
            'qty_available': CampoOdoo('qty_available', 'float', 'Stock Disponible'),
            'virtual_available': CampoOdoo('virtual_available', 'float', 'Stock Virtual'),
            'free_qty': CampoOdoo('free_qty', 'float', 'Stock Libre'),
            'active': CampoOdoo('active', 'boolean', 'Activo'),
        }
    ),
    
    'stock.quant': ModeloOdoo(
        nombre_tecnico='stock.quant',
        nombre_display='Cantidad en Stock',
        descripcion='Cantidades de productos por ubicación',
        keywords=['stock', 'inventario', 'existencias', 'almacén'],
        campos={
            'product_id': CampoOdoo('product_id', 'many2one', 'Producto', relacion='product.product'),
            'location_id': CampoOdoo('location_id', 'many2one', 'Ubicación', relacion='stock.location'),
            'lot_id': CampoOdoo('lot_id', 'many2one', 'Lote', relacion='stock.lot'),
            'quantity': CampoOdoo('quantity', 'float', 'Cantidad'),
            'reserved_quantity': CampoOdoo('reserved_quantity', 'float', 'Cantidad Reservada'),
            'available_quantity': CampoOdoo('available_quantity', 'float', 'Cantidad Disponible'),
            'inventory_date': CampoOdoo('inventory_date', 'date', 'Fecha Inventario'),
            'inventory_quantity': CampoOdoo('inventory_quantity', 'float', 'Cantidad Contada'),
            'inventory_diff_quantity': CampoOdoo('inventory_diff_quantity', 'float', 'Diferencia'),
            'value': CampoOdoo('value', 'monetary', 'Valor'),
            'company_id': CampoOdoo('company_id', 'many2one', 'Compañía', relacion='res.company'),
        }
    ),
    
    'stock.picking': ModeloOdoo(
        nombre_tecnico='stock.picking',
        nombre_display='Transferencia',
        descripcion='Movimientos de inventario (entrada/salida/interna)',
        keywords=['transferencia', 'entrada', 'salida', 'picking', 'envío'],
        campos={
            'name': CampoOdoo('name', 'char', 'Referencia'),
            'origin': CampoOdoo('origin', 'char', 'Documento Origen'),
            'partner_id': CampoOdoo('partner_id', 'many2one', 'Contacto', relacion='res.partner'),
            'picking_type_id': CampoOdoo('picking_type_id', 'many2one', 'Tipo Operación', relacion='stock.picking.type'),
            'location_id': CampoOdoo('location_id', 'many2one', 'Ubicación Origen', relacion='stock.location'),
            'location_dest_id': CampoOdoo('location_dest_id', 'many2one', 'Ubicación Destino', relacion='stock.location'),
            'scheduled_date': CampoOdoo('scheduled_date', 'datetime', 'Fecha Programada'),
            'date_done': CampoOdoo('date_done', 'datetime', 'Fecha Efectiva'),
            'state': CampoOdoo('state', 'selection', 'Estado', 'draft/waiting/confirmed/assigned/done/cancel'),
            'move_ids': CampoOdoo('move_ids', 'one2many', 'Movimientos', relacion='stock.move'),
            'backorder_id': CampoOdoo('backorder_id', 'many2one', 'Backorder', relacion='stock.picking'),
            'user_id': CampoOdoo('user_id', 'many2one', 'Responsable', relacion='res.users'),
        }
    ),
    
    'stock.move': ModeloOdoo(
        nombre_tecnico='stock.move',
        nombre_display='Movimiento Stock',
        descripcion='Movimientos individuales de productos',
        keywords=['movimiento', 'move', 'traslado'],
        campos={
            'name': CampoOdoo('name', 'char', 'Descripción'),
            'product_id': CampoOdoo('product_id', 'many2one', 'Producto', relacion='product.product'),
            'product_uom_qty': CampoOdoo('product_uom_qty', 'float', 'Cantidad Demanda'),
            'quantity_done': CampoOdoo('quantity_done', 'float', 'Cantidad Hecha'),
            'product_uom': CampoOdoo('product_uom', 'many2one', 'Unidad', relacion='uom.uom'),
            'location_id': CampoOdoo('location_id', 'many2one', 'Origen', relacion='stock.location'),
            'location_dest_id': CampoOdoo('location_dest_id', 'many2one', 'Destino', relacion='stock.location'),
            'picking_id': CampoOdoo('picking_id', 'many2one', 'Transferencia', relacion='stock.picking'),
            'state': CampoOdoo('state', 'selection', 'Estado'),
            'date': CampoOdoo('date', 'datetime', 'Fecha'),
            'reference': CampoOdoo('reference', 'char', 'Referencia'),
            'origin': CampoOdoo('origin', 'char', 'Origen'),
        }
    ),
    
    # ========== COMPRAS ==========
    'purchase.order': ModeloOdoo(
        nombre_tecnico='purchase.order',
        nombre_display='Orden de Compra',
        descripcion='Órdenes de compra a proveedores',
        keywords=['compra', 'purchase', 'proveedor', 'adquisición'],
        campos={
            'name': CampoOdoo('name', 'char', 'Número'),
            'partner_id': CampoOdoo('partner_id', 'many2one', 'Proveedor', relacion='res.partner'),
            'partner_ref': CampoOdoo('partner_ref', 'char', 'Referencia Proveedor'),
            'date_order': CampoOdoo('date_order', 'datetime', 'Fecha Orden'),
            'date_approve': CampoOdoo('date_approve', 'datetime', 'Fecha Confirmación'),
            'date_planned': CampoOdoo('date_planned', 'datetime', 'Fecha Recepción'),
            'user_id': CampoOdoo('user_id', 'many2one', 'Comprador', relacion='res.users'),
            'order_line': CampoOdoo('order_line', 'one2many', 'Líneas', relacion='purchase.order.line'),
            'amount_untaxed': CampoOdoo('amount_untaxed', 'monetary', 'Subtotal'),
            'amount_tax': CampoOdoo('amount_tax', 'monetary', 'Impuestos'),
            'amount_total': CampoOdoo('amount_total', 'monetary', 'Total'),
            'state': CampoOdoo('state', 'selection', 'Estado', 'draft/sent/to approve/purchase/done/cancel'),
            'invoice_status': CampoOdoo('invoice_status', 'selection', 'Estado Factura'),
            'currency_id': CampoOdoo('currency_id', 'many2one', 'Moneda', relacion='res.currency'),
            'payment_term_id': CampoOdoo('payment_term_id', 'many2one', 'Términos Pago', relacion='account.payment.term'),
            'fiscal_position_id': CampoOdoo('fiscal_position_id', 'many2one', 'Posición Fiscal', relacion='account.fiscal.position'),
            'notes': CampoOdoo('notes', 'text', 'Notas'),
            'origin': CampoOdoo('origin', 'char', 'Origen'),
        }
    ),
    
    'purchase.order.line': ModeloOdoo(
        nombre_tecnico='purchase.order.line',
        nombre_display='Línea de Compra',
        descripcion='Detalle de productos en órdenes de compra',
        keywords=['línea compra', 'detalle compra'],
        campos={
            'order_id': CampoOdoo('order_id', 'many2one', 'Orden', relacion='purchase.order'),
            'product_id': CampoOdoo('product_id', 'many2one', 'Producto', relacion='product.product'),
            'name': CampoOdoo('name', 'text', 'Descripción'),
            'product_qty': CampoOdoo('product_qty', 'float', 'Cantidad'),
            'product_uom': CampoOdoo('product_uom', 'many2one', 'Unidad', relacion='uom.uom'),
            'price_unit': CampoOdoo('price_unit', 'float', 'Precio Unitario'),
            'taxes_id': CampoOdoo('taxes_id', 'many2many', 'Impuestos', relacion='account.tax'),
            'price_subtotal': CampoOdoo('price_subtotal', 'monetary', 'Subtotal'),
            'date_planned': CampoOdoo('date_planned', 'datetime', 'Fecha Esperada'),
            'qty_received': CampoOdoo('qty_received', 'float', 'Cantidad Recibida'),
            'qty_invoiced': CampoOdoo('qty_invoiced', 'float', 'Cantidad Facturada'),
        }
    ),
    
    # ========== RECURSOS HUMANOS ==========
    'hr.employee': ModeloOdoo(
        nombre_tecnico='hr.employee',
        nombre_display='Empleado',
        descripcion='Información de empleados',
        keywords=['empleado', 'trabajador', 'personal', 'rh', 'recursos humanos', 'staff'],
        campos={
            'name': CampoOdoo('name', 'char', 'Nombre'),
            'work_email': CampoOdoo('work_email', 'char', 'Email Trabajo'),
            'mobile_phone': CampoOdoo('mobile_phone', 'char', 'Teléfono Móvil'),
            'work_phone': CampoOdoo('work_phone', 'char', 'Teléfono Trabajo'),
            'department_id': CampoOdoo('department_id', 'many2one', 'Departamento', relacion='hr.department'),
            'job_id': CampoOdoo('job_id', 'many2one', 'Puesto', relacion='hr.job'),
            'job_title': CampoOdoo('job_title', 'char', 'Título del Puesto'),
            'parent_id': CampoOdoo('parent_id', 'many2one', 'Manager', relacion='hr.employee'),
            'coach_id': CampoOdoo('coach_id', 'many2one', 'Coach', relacion='hr.employee'),
            'user_id': CampoOdoo('user_id', 'many2one', 'Usuario', relacion='res.users'),
            'company_id': CampoOdoo('company_id', 'many2one', 'Compañía', relacion='res.company'),
            'active': CampoOdoo('active', 'boolean', 'Activo'),
            'gender': CampoOdoo('gender', 'selection', 'Género', 'male/female/other'),
            'marital': CampoOdoo('marital', 'selection', 'Estado Civil'),
            'birthday': CampoOdoo('birthday', 'date', 'Fecha Nacimiento'),
            'identification_id': CampoOdoo('identification_id', 'char', 'Número Identificación'),
            'passport_id': CampoOdoo('passport_id', 'char', 'Número Pasaporte'),
            'country_id': CampoOdoo('country_id', 'many2one', 'Nacionalidad', relacion='res.country'),
            'emergency_contact': CampoOdoo('emergency_contact', 'char', 'Contacto Emergencia'),
            'emergency_phone': CampoOdoo('emergency_phone', 'char', 'Teléfono Emergencia'),
            'km_home_work': CampoOdoo('km_home_work', 'integer', 'Km Casa-Trabajo'),
            'certificate': CampoOdoo('certificate', 'selection', 'Nivel Educación'),
            'study_field': CampoOdoo('study_field', 'char', 'Campo de Estudio'),
            'study_school': CampoOdoo('study_school', 'char', 'Escuela'),
            'resource_calendar_id': CampoOdoo('resource_calendar_id', 'many2one', 'Horario', relacion='resource.calendar'),
            'contract_id': CampoOdoo('contract_id', 'many2one', 'Contrato Actual', relacion='hr.contract'),
        }
    ),
    
    'hr.department': ModeloOdoo(
        nombre_tecnico='hr.department',
        nombre_display='Departamento',
        descripcion='Departamentos de la empresa',
        keywords=['departamento', 'área', 'división'],
        campos={
            'name': CampoOdoo('name', 'char', 'Nombre'),
            'complete_name': CampoOdoo('complete_name', 'char', 'Nombre Completo'),
            'parent_id': CampoOdoo('parent_id', 'many2one', 'Departamento Padre', relacion='hr.department'),
            'manager_id': CampoOdoo('manager_id', 'many2one', 'Manager', relacion='hr.employee'),
            'member_ids': CampoOdoo('member_ids', 'one2many', 'Miembros', relacion='hr.employee'),
            'total_employee': CampoOdoo('total_employee', 'integer', 'Total Empleados'),
            'company_id': CampoOdoo('company_id', 'many2one', 'Compañía', relacion='res.company'),
        }
    ),
    
    'hr.contract': ModeloOdoo(
        nombre_tecnico='hr.contract',
        nombre_display='Contrato',
        descripcion='Contratos laborales de empleados',
        keywords=['contrato', 'salario', 'sueldo', 'nómina'],
        campos={
            'name': CampoOdoo('name', 'char', 'Referencia'),
            'employee_id': CampoOdoo('employee_id', 'many2one', 'Empleado', relacion='hr.employee'),
            'department_id': CampoOdoo('department_id', 'many2one', 'Departamento', relacion='hr.department'),
            'job_id': CampoOdoo('job_id', 'many2one', 'Puesto', relacion='hr.job'),
            'date_start': CampoOdoo('date_start', 'date', 'Fecha Inicio'),
            'date_end': CampoOdoo('date_end', 'date', 'Fecha Fin'),
            'trial_date_end': CampoOdoo('trial_date_end', 'date', 'Fin Período Prueba'),
            'wage': CampoOdoo('wage', 'monetary', 'Salario'),
            'state': CampoOdoo('state', 'selection', 'Estado', 'draft/open/close/cancel'),
            'structure_type_id': CampoOdoo('structure_type_id', 'many2one', 'Tipo Estructura', relacion='hr.payroll.structure.type'),
            'resource_calendar_id': CampoOdoo('resource_calendar_id', 'many2one', 'Horario', relacion='resource.calendar'),
            'hr_responsible_id': CampoOdoo('hr_responsible_id', 'many2one', 'Responsable RH', relacion='res.users'),
            'notes': CampoOdoo('notes', 'text', 'Notas'),
            'company_id': CampoOdoo('company_id', 'many2one', 'Compañía', relacion='res.company'),
        }
    ),
    
    'hr.payslip': ModeloOdoo(
        nombre_tecnico='hr.payslip',
        nombre_display='Recibo de Nómina',
        descripcion='Recibos de nómina de empleados',
        keywords=['nómina', 'recibo', 'payslip', 'salario', 'pago empleado'],
        campos={
            'name': CampoOdoo('name', 'char', 'Descripción'),
            'number': CampoOdoo('number', 'char', 'Referencia'),
            'employee_id': CampoOdoo('employee_id', 'many2one', 'Empleado', relacion='hr.employee'),
            'date_from': CampoOdoo('date_from', 'date', 'Fecha Inicio'),
            'date_to': CampoOdoo('date_to', 'date', 'Fecha Fin'),
            'state': CampoOdoo('state', 'selection', 'Estado', 'draft/verify/done/cancel'),
            'contract_id': CampoOdoo('contract_id', 'many2one', 'Contrato', relacion='hr.contract'),
            'struct_id': CampoOdoo('struct_id', 'many2one', 'Estructura', relacion='hr.payroll.structure'),
            'company_id': CampoOdoo('company_id', 'many2one', 'Compañía', relacion='res.company'),
            'net_wage': CampoOdoo('net_wage', 'monetary', 'Salario Neto'),
            'basic_wage': CampoOdoo('basic_wage', 'monetary', 'Salario Base'),
            'line_ids': CampoOdoo('line_ids', 'one2many', 'Líneas', relacion='hr.payslip.line'),
            'paid': CampoOdoo('paid', 'boolean', 'Pagado'),
        }
    ),
    
    'hr.attendance': ModeloOdoo(
        nombre_tecnico='hr.attendance',
        nombre_display='Asistencia',
        descripcion='Registros de asistencia de empleados',
        keywords=['asistencia', 'checada', 'entrada', 'salida', 'reloj checador'],
        campos={
            'employee_id': CampoOdoo('employee_id', 'many2one', 'Empleado', relacion='hr.employee'),
            'check_in': CampoOdoo('check_in', 'datetime', 'Entrada'),
            'check_out': CampoOdoo('check_out', 'datetime', 'Salida'),
            'worked_hours': CampoOdoo('worked_hours', 'float', 'Horas Trabajadas'),
        }
    ),
    
    'hr.leave': ModeloOdoo(
        nombre_tecnico='hr.leave',
        nombre_display='Ausencia',
        descripcion='Solicitudes de ausencia (vacaciones, permisos)',
        keywords=['ausencia', 'vacaciones', 'permiso', 'incapacidad', 'leave'],
        campos={
            'name': CampoOdoo('name', 'char', 'Descripción'),
            'employee_id': CampoOdoo('employee_id', 'many2one', 'Empleado', relacion='hr.employee'),
            'holiday_status_id': CampoOdoo('holiday_status_id', 'many2one', 'Tipo Ausencia', relacion='hr.leave.type'),
            'date_from': CampoOdoo('date_from', 'datetime', 'Fecha Inicio'),
            'date_to': CampoOdoo('date_to', 'datetime', 'Fecha Fin'),
            'number_of_days': CampoOdoo('number_of_days', 'float', 'Duración (días)'),
            'state': CampoOdoo('state', 'selection', 'Estado', 'draft/confirm/validate/refuse'),
            'department_id': CampoOdoo('department_id', 'many2one', 'Departamento', relacion='hr.department'),
            'notes': CampoOdoo('notes', 'text', 'Notas'),
            'request_date_from': CampoOdoo('request_date_from', 'date', 'Solicitud Desde'),
            'request_date_to': CampoOdoo('request_date_to', 'date', 'Solicitud Hasta'),
        }
    ),
    
    # ========== CONTACTOS/PARTNERS ==========
    'res.partner': ModeloOdoo(
        nombre_tecnico='res.partner',
        nombre_display='Contacto',
        descripcion='Clientes, proveedores y contactos',
        keywords=['cliente', 'proveedor', 'contacto', 'partner', 'empresa'],
        campos={
            'name': CampoOdoo('name', 'char', 'Nombre'),
            'display_name': CampoOdoo('display_name', 'char', 'Nombre Completo'),
            'company_type': CampoOdoo('company_type', 'selection', 'Tipo', 'person/company'),
            'is_company': CampoOdoo('is_company', 'boolean', 'Es Empresa'),
            'parent_id': CampoOdoo('parent_id', 'many2one', 'Empresa Padre', relacion='res.partner'),
            'email': CampoOdoo('email', 'char', 'Email'),
            'phone': CampoOdoo('phone', 'char', 'Teléfono'),
            'mobile': CampoOdoo('mobile', 'char', 'Móvil'),
            'street': CampoOdoo('street', 'char', 'Calle'),
            'street2': CampoOdoo('street2', 'char', 'Calle 2'),
            'city': CampoOdoo('city', 'char', 'Ciudad'),
            'state_id': CampoOdoo('state_id', 'many2one', 'Estado', relacion='res.country.state'),
            'zip': CampoOdoo('zip', 'char', 'C.P.'),
            'country_id': CampoOdoo('country_id', 'many2one', 'País', relacion='res.country'),
            'vat': CampoOdoo('vat', 'char', 'RFC/NIT'),
            'website': CampoOdoo('website', 'char', 'Sitio Web'),
            'lang': CampoOdoo('lang', 'selection', 'Idioma'),
            'user_id': CampoOdoo('user_id', 'many2one', 'Vendedor', relacion='res.users'),
            'team_id': CampoOdoo('team_id', 'many2one', 'Equipo Ventas', relacion='crm.team'),
            'customer_rank': CampoOdoo('customer_rank', 'integer', 'Es Cliente'),
            'supplier_rank': CampoOdoo('supplier_rank', 'integer', 'Es Proveedor'),
            'credit_limit': CampoOdoo('credit_limit', 'float', 'Límite Crédito'),
            'total_invoiced': CampoOdoo('total_invoiced', 'monetary', 'Total Facturado'),
            'total_due': CampoOdoo('total_due', 'monetary', 'Total Adeudado'),
            'credit': CampoOdoo('credit', 'monetary', 'A Cobrar'),
            'debit': CampoOdoo('debit', 'monetary', 'A Pagar'),
            'property_payment_term_id': CampoOdoo('property_payment_term_id', 'many2one', 'Términos Pago', relacion='account.payment.term'),
            'property_supplier_payment_term_id': CampoOdoo('property_supplier_payment_term_id', 'many2one', 'Términos Pago Proveedor', relacion='account.payment.term'),
            'active': CampoOdoo('active', 'boolean', 'Activo'),
            'category_id': CampoOdoo('category_id', 'many2many', 'Etiquetas', relacion='res.partner.category'),
            # Campos México
            'l10n_mx_edi_fiscal_regime': CampoOdoo('l10n_mx_edi_fiscal_regime', 'selection', 'Régimen Fiscal'),
            'l10n_mx_edi_curp': CampoOdoo('l10n_mx_edi_curp', 'char', 'CURP'),
        }
    ),
    
    # ========== USUARIOS ==========
    'res.users': ModeloOdoo(
        nombre_tecnico='res.users',
        nombre_display='Usuario',
        descripcion='Usuarios del sistema Odoo',
        keywords=['usuario', 'user', 'login', 'acceso'],
        campos={
            'name': CampoOdoo('name', 'char', 'Nombre'),
            'login': CampoOdoo('login', 'char', 'Login'),
            'email': CampoOdoo('email', 'char', 'Email'),
            'partner_id': CampoOdoo('partner_id', 'many2one', 'Contacto', relacion='res.partner'),
            'company_id': CampoOdoo('company_id', 'many2one', 'Compañía', relacion='res.company'),
            'company_ids': CampoOdoo('company_ids', 'many2many', 'Compañías Permitidas', relacion='res.company'),
            'groups_id': CampoOdoo('groups_id', 'many2many', 'Grupos', relacion='res.groups'),
            'active': CampoOdoo('active', 'boolean', 'Activo'),
            'share': CampoOdoo('share', 'boolean', 'Usuario Portal'),
            'signature': CampoOdoo('signature', 'html', 'Firma'),
            'notification_type': CampoOdoo('notification_type', 'selection', 'Notificaciones'),
            'login_date': CampoOdoo('login_date', 'datetime', 'Último Login'),
        }
    ),
    
    # ========== CRM ==========
    'crm.lead': ModeloOdoo(
        nombre_tecnico='crm.lead',
        nombre_display='Oportunidad/Lead',
        descripcion='Oportunidades de venta y leads',
        keywords=['crm', 'oportunidad', 'lead', 'prospecto', 'pipeline'],
        campos={
            'name': CampoOdoo('name', 'char', 'Nombre'),
            'partner_id': CampoOdoo('partner_id', 'many2one', 'Cliente', relacion='res.partner'),
            'email_from': CampoOdoo('email_from', 'char', 'Email'),
            'phone': CampoOdoo('phone', 'char', 'Teléfono'),
            'type': CampoOdoo('type', 'selection', 'Tipo', 'lead/opportunity'),
            'stage_id': CampoOdoo('stage_id', 'many2one', 'Etapa', relacion='crm.stage'),
            'user_id': CampoOdoo('user_id', 'many2one', 'Vendedor', relacion='res.users'),
            'team_id': CampoOdoo('team_id', 'many2one', 'Equipo', relacion='crm.team'),
            'expected_revenue': CampoOdoo('expected_revenue', 'monetary', 'Ingreso Esperado'),
            'probability': CampoOdoo('probability', 'float', 'Probabilidad'),
            'date_deadline': CampoOdoo('date_deadline', 'date', 'Fecha Cierre'),
            'date_closed': CampoOdoo('date_closed', 'datetime', 'Fecha Cerrado'),
            'create_date': CampoOdoo('create_date', 'datetime', 'Fecha Creación'),
            'source_id': CampoOdoo('source_id', 'many2one', 'Fuente', relacion='utm.source'),
            'medium_id': CampoOdoo('medium_id', 'many2one', 'Medio', relacion='utm.medium'),
            'campaign_id': CampoOdoo('campaign_id', 'many2one', 'Campaña', relacion='utm.campaign'),
            'lost_reason_id': CampoOdoo('lost_reason_id', 'many2one', 'Razón Pérdida', relacion='crm.lost.reason'),
            'active': CampoOdoo('active', 'boolean', 'Activo'),
            'description': CampoOdoo('description', 'text', 'Notas'),
        }
    ),
    
    # ========== PROYECTOS ==========
    'project.project': ModeloOdoo(
        nombre_tecnico='project.project',
        nombre_display='Proyecto',
        descripcion='Proyectos',
        keywords=['proyecto', 'project'],
        campos={
            'name': CampoOdoo('name', 'char', 'Nombre'),
            'partner_id': CampoOdoo('partner_id', 'many2one', 'Cliente', relacion='res.partner'),
            'user_id': CampoOdoo('user_id', 'many2one', 'Manager', relacion='res.users'),
            'date_start': CampoOdoo('date_start', 'date', 'Fecha Inicio'),
            'date': CampoOdoo('date', 'date', 'Fecha Fin'),
            'task_count': CampoOdoo('task_count', 'integer', 'Número Tareas'),
            'active': CampoOdoo('active', 'boolean', 'Activo'),
            'description': CampoOdoo('description', 'html', 'Descripción'),
        }
    ),
    
    'project.task': ModeloOdoo(
        nombre_tecnico='project.task',
        nombre_display='Tarea',
        descripcion='Tareas de proyecto',
        keywords=['tarea', 'task', 'actividad'],
        campos={
            'name': CampoOdoo('name', 'char', 'Nombre'),
            'project_id': CampoOdoo('project_id', 'many2one', 'Proyecto', relacion='project.project'),
            'user_ids': CampoOdoo('user_ids', 'many2many', 'Asignados', relacion='res.users'),
            'stage_id': CampoOdoo('stage_id', 'many2one', 'Etapa', relacion='project.task.type'),
            'date_deadline': CampoOdoo('date_deadline', 'date', 'Fecha Límite'),
            'priority': CampoOdoo('priority', 'selection', 'Prioridad', '0/1'),
            'kanban_state': CampoOdoo('kanban_state', 'selection', 'Estado Kanban'),
            'active': CampoOdoo('active', 'boolean', 'Activo'),
            'description': CampoOdoo('description', 'html', 'Descripción'),
            'planned_hours': CampoOdoo('planned_hours', 'float', 'Horas Planeadas'),
            'effective_hours': CampoOdoo('effective_hours', 'float', 'Horas Efectivas'),
            'remaining_hours': CampoOdoo('remaining_hours', 'float', 'Horas Restantes'),
            'progress': CampoOdoo('progress', 'float', 'Progreso'),
        }
    ),
}


# ============================================================
# ANÁLISIS DISPONIBLES
# ============================================================

ANALISIS_DISPONIBLES = {
    # Ventas
    'ventas_periodo': {
        'nombre': 'Ventas por Período',
        'descripcion': 'Análisis de ventas en un rango de fechas',
        'modelo': 'sale.order',
        'metricas': ['total', 'cantidad', 'promedio', 'por_dia', 'por_cliente', 'por_vendedor']
    },
    'top_productos': {
        'nombre': 'Top Productos Vendidos',
        'descripcion': 'Ranking de productos más vendidos',
        'modelo': 'sale.order.line',
        'metricas': ['unidades', 'ingresos', 'frecuencia']
    },
    'ventas_por_cliente': {
        'nombre': 'Ventas por Cliente',
        'descripcion': 'Análisis de clientes por volumen de compra',
        'modelo': 'sale.order',
        'metricas': ['total', 'ordenes', 'ticket_promedio']
    },
    'ventas_por_vendedor': {
        'nombre': 'Rendimiento por Vendedor',
        'descripcion': 'Métricas de desempeño de vendedores',
        'modelo': 'sale.order',
        'metricas': ['total', 'ordenes', 'conversion', 'ticket_promedio']
    },
    'tendencia_ventas': {
        'nombre': 'Tendencia de Ventas',
        'descripcion': 'Evolución de ventas en el tiempo',
        'modelo': 'sale.order',
        'metricas': ['tendencia', 'proyeccion', 'estacionalidad']
    },
    
    # POS
    'pos_periodo': {
        'nombre': 'Tickets POS por Período',
        'descripcion': 'Análisis de ventas en punto de venta',
        'modelo': 'pos.order',
        'metricas': ['tickets', 'total', 'promedio', 'por_hora', 'por_cajero']
    },
    'pos_metodos_pago': {
        'nombre': 'Métodos de Pago POS',
        'descripcion': 'Distribución por forma de pago',
        'modelo': 'pos.payment',
        'metricas': ['efectivo', 'tarjeta', 'otros', 'porcentaje']
    },
    'pos_sesiones': {
        'nombre': 'Análisis de Sesiones',
        'descripcion': 'Rendimiento por sesión de caja',
        'modelo': 'pos.session',
        'metricas': ['ventas', 'diferencias', 'duracion']
    },
    
    # Facturación
    'facturacion_periodo': {
        'nombre': 'Facturación por Período',
        'descripcion': 'Análisis de facturación',
        'modelo': 'account.move',
        'metricas': ['total', 'cantidad', 'cobrado', 'pendiente']
    },
    'cuentas_por_cobrar': {
        'nombre': 'Cuentas por Cobrar',
        'descripcion': 'Análisis de cartera de clientes',
        'modelo': 'account.move',
        'metricas': ['vencido', 'por_vencer', 'antigüedad', 'por_cliente']
    },
    'cuentas_por_pagar': {
        'nombre': 'Cuentas por Pagar',
        'descripcion': 'Análisis de deuda con proveedores',
        'modelo': 'account.move',
        'metricas': ['vencido', 'por_vencer', 'por_proveedor']
    },
    
    # Inventario
    'stock_actual': {
        'nombre': 'Stock Actual',
        'descripcion': 'Estado del inventario',
        'modelo': 'stock.quant',
        'metricas': ['total', 'valor', 'por_ubicacion', 'por_categoria']
    },
    'rotacion_inventario': {
        'nombre': 'Rotación de Inventario',
        'descripcion': 'Velocidad de rotación de productos',
        'modelo': 'stock.move',
        'metricas': ['rotacion', 'dias_inventario', 'obsoletos']
    },
    'stock_minimos': {
        'nombre': 'Productos Bajo Mínimo',
        'descripcion': 'Alertas de stock bajo',
        'modelo': 'product.product',
        'metricas': ['bajo_minimo', 'agotados', 'reorden']
    },
    'valoracion_inventario': {
        'nombre': 'Valoración de Inventario',
        'descripcion': 'Valor monetario del inventario',
        'modelo': 'stock.valuation.layer',
        'metricas': ['valor_total', 'por_categoria', 'por_producto']
    },
    
    # Compras
    'compras_periodo': {
        'nombre': 'Compras por Período',
        'descripcion': 'Análisis de órdenes de compra',
        'modelo': 'purchase.order',
        'metricas': ['total', 'cantidad', 'por_proveedor']
    },
    'proveedores_top': {
        'nombre': 'Top Proveedores',
        'descripcion': 'Ranking de proveedores por compras',
        'modelo': 'purchase.order',
        'metricas': ['total', 'ordenes', 'tiempo_entrega']
    },
    'cumplimiento_proveedores': {
        'nombre': 'Cumplimiento Proveedores',
        'descripcion': 'Análisis de entregas a tiempo',
        'modelo': 'stock.picking',
        'metricas': ['a_tiempo', 'retrasados', 'porcentaje']
    },
    
    # Recursos Humanos
    'headcount': {
        'nombre': 'Headcount',
        'descripcion': 'Conteo de empleados',
        'modelo': 'hr.employee',
        'metricas': ['total', 'por_departamento', 'por_puesto', 'activos', 'inactivos']
    },
    'rotacion_personal': {
        'nombre': 'Rotación de Personal',
        'descripcion': 'Índice de rotación',
        'modelo': 'hr.employee',
        'metricas': ['altas', 'bajas', 'indice_rotacion']
    },
    'asistencia': {
        'nombre': 'Análisis de Asistencia',
        'descripcion': 'Métricas de asistencia',
        'modelo': 'hr.attendance',
        'metricas': ['horas_trabajadas', 'tardanzas', 'faltas']
    },
    'ausencias': {
        'nombre': 'Análisis de Ausencias',
        'descripcion': 'Vacaciones, permisos, incapacidades',
        'modelo': 'hr.leave',
        'metricas': ['vacaciones', 'incapacidades', 'permisos', 'por_departamento']
    },
    'nomina': {
        'nombre': 'Análisis de Nómina',
        'descripcion': 'Métricas de nómina',
        'modelo': 'hr.payslip',
        'metricas': ['total', 'por_departamento', 'percepciones', 'deducciones']
    },
    'contratos': {
        'nombre': 'Estado de Contratos',
        'descripcion': 'Contratos vigentes y próximos a vencer',
        'modelo': 'hr.contract',
        'metricas': ['vigentes', 'por_vencer', 'temporales', 'indefinidos']
    },
    
    # CRM
    'pipeline_crm': {
        'nombre': 'Pipeline de Ventas',
        'descripcion': 'Oportunidades por etapa',
        'modelo': 'crm.lead',
        'metricas': ['por_etapa', 'valor_total', 'probabilidad_ponderada']
    },
    'conversion_leads': {
        'nombre': 'Tasa de Conversión',
        'descripcion': 'Conversión de leads a oportunidades',
        'modelo': 'crm.lead',
        'metricas': ['leads', 'oportunidades', 'ganados', 'perdidos', 'tasa']
    },
    
    # Usuarios
    'actividad_usuarios': {
        'nombre': 'Actividad de Usuarios',
        'descripcion': 'Uso del sistema por usuarios',
        'modelo': 'res.users',
        'metricas': ['activos', 'ultimo_login', 'por_grupo']
    },
}


def obtener_modelo(nombre: str) -> Optional[ModeloOdoo]:
    """Obtiene un modelo por su nombre técnico o keywords."""
    # Búsqueda exacta
    if nombre in MODELOS_ODOO:
        return MODELOS_ODOO[nombre]
    
    # Búsqueda por keywords
    nombre_lower = nombre.lower()
    for key, modelo in MODELOS_ODOO.items():
        if any(kw in nombre_lower for kw in modelo.keywords):
            return modelo
    
    return None


def listar_modelos() -> List[Dict]:
    """Lista todos los modelos disponibles."""
    return [
        {
            'nombre_tecnico': m.nombre_tecnico,
            'nombre_display': m.nombre_display,
            'descripcion': m.descripcion
        }
        for m in MODELOS_ODOO.values()
    ]


def listar_analisis() -> List[Dict]:
    """Lista todos los análisis disponibles."""
    return [
        {
            'id': key,
            'nombre': a['nombre'],
            'descripcion': a['descripcion'],
            'modelo': a['modelo']
        }
        for key, a in ANALISIS_DISPONIBLES.items()
    ]
