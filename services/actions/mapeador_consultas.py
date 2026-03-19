# ============================================================
# ANDROMEDA - Mapeador de Consultas Odoo
# ============================================================
# Módulo extraído de interfaz_v5.py (ARQ-v2-001)
# Mapea acciones v2 a consultas directas Odoo.
# ============================================================

from app.logging_config import get_logger

logger = get_logger("services.actions.mapeador_consultas")


class MapeadorConsultas:
    """Mapea acciones a consultas directas de Odoo.
    
    Extraído de OdooAIProV5._mapear_accion_a_consulta_odoo (ARQ-v2-001).
    """

    def __init__(self, bot):
        self._bot = bot

    def mapear(self, accion: str, fecha_ini: str, fecha_fin: str, params: dict, consulta) -> dict:
        """Punto de entrada principal — delega a _mapear_accion_a_consulta_odoo."""
        return self._mapear_accion_a_consulta_odoo(accion, fecha_ini, fecha_fin, params, consulta)

    def _mapear_accion_a_consulta_odoo(self, accion: str, fecha_ini: str, fecha_fin: str, params: dict, consulta) -> dict:
        """Mapea acciones v2 a consultas directas Odoo cuando es posible."""
        filtro_fecha_venta = [('date_order', '>=', fecha_ini), ('date_order', '<=', fecha_fin), ('state', 'in', ['sale', 'done'])]
        filtro_fecha_factura = [('invoice_date', '>=', fecha_ini), ('invoice_date', '<=', fecha_fin), ('state', '=', 'posted')]
        filtro_fecha_compra = [('date_order', '>=', fecha_ini), ('date_order', '<=', fecha_fin), ('state', 'in', ['purchase', 'done'])]

        mapeo = {
            # Ventas v2
            'margen_por_producto': {
                'modelo': 'sale.order.line',
                'filtro': [('order_id.date_order', '>=', fecha_ini), ('order_id.date_order', '<=', fecha_fin), ('order_id.state', 'in', ['sale', 'done'])],
                'campos': ['product_id', 'price_subtotal', 'product_uom_qty', 'price_unit', 'discount'],
                'limite': 200,
                'orden': 'price_subtotal desc',
            },
            'devolucion_ventas': {
                'modelo': 'account.move',
                'filtro': filtro_fecha_factura + [('move_type', '=', 'out_refund')],
                'campos': ['name', 'partner_id', 'amount_total', 'invoice_date', 'state'],
                'limite': 100,
                'orden': 'amount_total desc',
            },
            'descuentos_aplicados': {
                'modelo': 'sale.order.line',
                'filtro': [('order_id.date_order', '>=', fecha_ini), ('order_id.date_order', '<=', fecha_fin), ('discount', '>', 0)],
                'campos': ['product_id', 'price_unit', 'discount', 'price_subtotal', 'order_id'],
                'limite': 150,
                'orden': 'discount desc',
            },
            'concentracion_clientes': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['partner_id', 'amount_total'],
                'limite': 500,
                'orden': 'amount_total desc',
            },
            'ventas_vs_anterior': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['date_order', 'amount_total', 'partner_id', 'user_id'],
                'limite': 500,
                'orden': 'date_order desc',
            },

            # Inventario v2
            'inventario_negativo': {
                'modelo': 'stock.quant',
                'filtro': [('quantity', '<', 0)],
                'campos': ['product_id', 'location_id', 'quantity', 'reserved_quantity'],
                'limite': 200,
            },
            'inventario_obsoleto': {
                'modelo': 'stock.quant',
                'filtro': [('quantity', '>', 0)],
                'campos': ['product_id', 'location_id', 'quantity', 'write_date'],
                'limite': 300,
                'orden': 'write_date asc',
            },
            'transferencias_pendientes': {
                'modelo': 'stock.picking',
                'filtro': [('state', 'in', ['assigned', 'waiting', 'confirmed'])],
                'campos': ['name', 'partner_id', 'origin', 'scheduled_date', 'state', 'picking_type_id'],
                'limite': 100,
                'orden': 'scheduled_date asc',
            },

            # Finanzas v2
            'notas_credito': {
                'modelo': 'account.move',
                'filtro': filtro_fecha_factura + [('move_type', 'in', ['out_refund', 'in_refund'])],
                'campos': ['name', 'partner_id', 'amount_total', 'invoice_date', 'move_type', 'state'],
                'limite': 100,
                'orden': 'amount_total desc',
            },
            'analisis_antiguedad': {
                'modelo': 'account.move',
                'filtro': [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', 'in', ['not_paid', 'partial'])],
                'campos': ['name', 'partner_id', 'amount_total', 'amount_residual', 'invoice_date', 'invoice_date_due'],
                'limite': 200,
                'orden': 'invoice_date asc',
            },
            'estado_cuenta_cliente': {
                'modelo': 'account.move',
                'filtro': [('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted')],
                'campos': ['name', 'partner_id', 'amount_total', 'amount_residual', 'invoice_date', 'payment_state'],
                'limite': 100,
                'orden': 'invoice_date desc',
            },
            'estado_cuenta_proveedor': {
                'modelo': 'account.move',
                'filtro': [('move_type', 'in', ['in_invoice', 'in_refund']), ('state', '=', 'posted')],
                'campos': ['name', 'partner_id', 'amount_total', 'amount_residual', 'invoice_date', 'payment_state'],
                'limite': 100,
                'orden': 'invoice_date desc',
            },
            'pagos_pendientes_aplicar': {
                'modelo': 'account.payment',
                'filtro': [('state', '=', 'posted'), ('is_reconciled', '=', False)],
                'campos': ['name', 'partner_id', 'amount', 'date', 'payment_type', 'journal_id'],
                'limite': 100,
                'orden': 'date desc',
            },

            # CRM v2
            'pipeline_etapas': {
                'modelo': 'crm.lead',
                'filtro': [('type', '=', 'opportunity'), ('active', '=', True)],
                'campos': ['name', 'partner_id', 'stage_id', 'expected_revenue', 'probability', 'user_id'],
                'limite': 200,
                'orden': 'expected_revenue desc',
            },
            'oportunidades_estancadas': {
                'modelo': 'crm.lead',
                'filtro': [('type', '=', 'opportunity'), ('active', '=', True)],
                'campos': ['name', 'partner_id', 'stage_id', 'expected_revenue', 'write_date', 'user_id'],
                'limite': 100,
                'orden': 'write_date asc',
            },
            'leads_por_origen': {
                'modelo': 'crm.lead',
                'filtro': [('create_date', '>=', fecha_ini), ('create_date', '<=', fecha_fin)],
                'campos': ['name', 'source_id', 'partner_id', 'expected_revenue', 'stage_id'],
                'limite': 200,
            },

            # Compras v2
            'ordenes_pendientes': {
                'modelo': 'purchase.order',
                'filtro': [('state', 'in', ['purchase', 'sent']), ('date_planned', '!=', False)],
                'campos': ['name', 'partner_id', 'amount_total', 'date_order', 'date_planned', 'state'],
                'limite': 100,
                'orden': 'date_planned asc',
            },
            'evaluacion_proveedores': {
                'modelo': 'purchase.order',
                'filtro': filtro_fecha_compra,
                'campos': ['partner_id', 'amount_total', 'date_order', 'date_planned', 'state'],
                'limite': 500,
                'orden': 'partner_id asc',
            },
            'variacion_precios': {
                'modelo': 'purchase.order.line',
                'filtro': [('order_id.date_order', '>=', fecha_ini), ('order_id.date_order', '<=', fecha_fin)],
                'campos': ['product_id', 'price_unit', 'product_qty', 'date_planned', 'partner_id'],
                'limite': 300,
                'orden': 'date_planned desc',
            },

            # PDV v2
            'productividad_cajero': {
                'modelo': 'pos.order',
                'filtro': [('date_order', '>=', fecha_ini), ('date_order', '<=', fecha_fin), ('state', 'in', ['paid', 'done', 'invoiced'])],
                'campos': ['user_id', 'amount_total', 'date_order', 'pos_reference', 'session_id'],
                'limite': 500,
                'orden': 'user_id asc',
            },
            'cuadre_caja': {
                'modelo': 'pos.session',
                'filtro': [('start_at', '>=', fecha_ini), ('start_at', '<=', fecha_fin)],
                'campos': ['name', 'user_id', 'config_id', 'start_at', 'stop_at', 'state', 'cash_register_balance_start', 'cash_register_balance_end_real'],
                'limite': 100,
                'orden': 'start_at desc',
            },

            # RRHH v2
            'vencimiento_contratos': {
                'modelo': 'hr.contract',
                'filtro': [('state', '=', 'open'), ('date_end', '!=', False)],
                'campos': ['employee_id', 'name', 'date_start', 'date_end', 'wage', 'department_id', 'state'],
                'limite': 100,
                'orden': 'date_end asc',
            },
            'horas_extra': {
                'modelo': 'hr.attendance',
                'filtro': [('check_in', '>=', fecha_ini), ('check_in', '<=', fecha_fin)],
                'campos': ['employee_id', 'check_in', 'check_out', 'worked_hours'],
                'limite': 500,
                'orden': 'check_in desc',
            },

            # Diagnóstico v2
            'registros_duplicados': {
                'modelo': 'res.partner',
                'filtro': [('active', '=', True)],
                'campos': ['name', 'email', 'phone', 'vat', 'create_date'],
                'limite': 500,
                'orden': 'name asc',
            },

            # Odoo v2
            'modulos_instalados': {
                'modelo': 'ir.module.module',
                'filtro': [('state', '=', 'installed')],
                'campos': ['name', 'shortdesc', 'state', 'installed_version'],
                'limite': 200,
                'orden': 'name asc',
            },
            'ir_cron_activos': {
                'modelo': 'ir.cron',
                'filtro': [('active', '=', True)],
                'campos': ['name', 'model_id', 'interval_number', 'interval_type', 'nextcall', 'numbercall'],
                'limite': 100,
                'orden': 'nextcall asc',
            },

            # ── Ventas v2 (nuevos) ──
            'ventas_por_canal': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['team_id', 'amount_total', 'date_order', 'partner_id', 'state'],
                'limite': 500,
                'orden': 'date_order desc',
            },
            'ventas_por_hora': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['date_order', 'amount_total', 'partner_id'],
                'limite': 500,
                'orden': 'date_order desc',
            },
            'ventas_por_dia_semana': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['date_order', 'amount_total', 'partner_id'],
                'limite': 500,
                'orden': 'date_order desc',
            },
            'meta_cumplimiento': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['user_id', 'amount_total', 'date_order', 'state'],
                'limite': 500,
                'orden': 'user_id asc',
            },
            'ticket_promedio_evolucion': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['date_order', 'amount_total', 'order_line'],
                'limite': 500,
                'orden': 'date_order desc',
            },
            'clientes_nuevos_vs_recurrentes': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['partner_id', 'date_order', 'amount_total'],
                'limite': 500,
                'orden': 'date_order desc',
            },

            # ── Inventario v2 (nuevos) ──
            'merma_inventario': {
                'modelo': 'stock.scrap',
                'filtro': [('date_done', '>=', fecha_ini), ('date_done', '<=', fecha_fin)],
                'campos': ['product_id', 'scrap_qty', 'date_done', 'location_id', 'origin'],
                'limite': 200,
                'orden': 'date_done desc',
            },
            'inventario_por_categoria': {
                'modelo': 'stock.quant',
                'filtro': [('quantity', '>', 0)],
                'campos': ['product_id', 'location_id', 'quantity', 'reserved_quantity'],
                'limite': 500,
            },
            'inventario_valorizado_categoria': {
                'modelo': 'stock.quant',
                'filtro': [('quantity', '>', 0)],
                'campos': ['product_id', 'location_id', 'quantity', 'value'],
                'limite': 500,
            },
            'costo_almacenamiento': {
                'modelo': 'stock.quant',
                'filtro': [('quantity', '>', 0)],
                'campos': ['product_id', 'location_id', 'quantity', 'value', 'write_date'],
                'limite': 500,
                'orden': 'value desc',
            },
            'trazabilidad_lote': {
                'modelo': 'stock.production.lot',
                'filtro': [('create_date', '>=', fecha_ini), ('create_date', '<=', fecha_fin)],
                'campos': ['name', 'product_id', 'create_date', 'ref'],
                'limite': 200,
                'orden': 'create_date desc',
            },
            'cobertura_stock': {
                'modelo': 'stock.quant',
                'filtro': [('quantity', '>', 0)],
                'campos': ['product_id', 'location_id', 'quantity', 'reserved_quantity'],
                'limite': 500,
            },
            'abc_inventario': {
                'modelo': 'stock.quant',
                'filtro': [('quantity', '>', 0)],
                'campos': ['product_id', 'quantity', 'value'],
                'limite': 500,
                'orden': 'value desc',
            },
            'comparar_stock_fisico_sistema': {
                'modelo': 'stock.quant',
                'filtro': [],
                'campos': ['product_id', 'location_id', 'quantity', 'reserved_quantity', 'inventory_quantity_auto_apply'],
                'limite': 500,
            },

            # ── Finanzas v2 (nuevos) ──
            'conciliacion_bancaria': {
                'modelo': 'account.bank.statement.line',
                'filtro': [('date', '>=', fecha_ini), ('date', '<=', fecha_fin)],
                'campos': ['date', 'payment_ref', 'amount', 'partner_id', 'journal_id', 'is_reconciled'],
                'limite': 300,
                'orden': 'date desc',
            },
            'impuestos_resumen': {
                'modelo': 'account.move.line',
                'filtro': [('move_id.date', '>=', fecha_ini), ('move_id.date', '<=', fecha_fin), ('tax_line_id', '!=', False)],
                'campos': ['tax_line_id', 'debit', 'credit', 'balance', 'move_id'],
                'limite': 500,
                'orden': 'tax_line_id asc',
            },
            'margen_operativo': {
                'modelo': 'account.move',
                'filtro': filtro_fecha_factura + [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')],
                'campos': ['name', 'partner_id', 'amount_total', 'amount_untaxed', 'invoice_date'],
                'limite': 300,
                'orden': 'invoice_date desc',
            },
            'dias_cobro_promedio': {
                'modelo': 'account.move',
                'filtro': [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')],
                'campos': ['name', 'partner_id', 'amount_total', 'amount_residual', 'invoice_date', 'invoice_date_due', 'payment_state'],
                'limite': 300,
                'orden': 'invoice_date desc',
            },
            'dias_pago_promedio': {
                'modelo': 'account.move',
                'filtro': [('move_type', '=', 'in_invoice'), ('state', '=', 'posted')],
                'campos': ['name', 'partner_id', 'amount_total', 'amount_residual', 'invoice_date', 'invoice_date_due', 'payment_state'],
                'limite': 300,
                'orden': 'invoice_date desc',
            },
            'facturacion_por_empresa': {
                'modelo': 'account.move',
                'filtro': filtro_fecha_factura + [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')],
                'campos': ['partner_id', 'amount_total', 'amount_residual', 'invoice_date', 'company_id'],
                'limite': 300,
                'orden': 'amount_total desc',
            },
            'rentabilidad_cliente': {
                'modelo': 'account.move',
                'filtro': filtro_fecha_factura + [('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted')],
                'campos': ['partner_id', 'amount_total', 'amount_untaxed', 'move_type', 'invoice_date'],
                'limite': 500,
                'orden': 'partner_id asc',
            },
            'razon_liquidez': {
                'modelo': 'account.move.line',
                'filtro': [('account_id.account_type', 'in', ['asset_current', 'liability_current']), ('parent_state', '=', 'posted')],
                'campos': ['account_id', 'debit', 'credit', 'balance'],
                'limite': 500,
            },
            'capital_trabajo': {
                'modelo': 'account.move.line',
                'filtro': [('account_id.account_type', 'in', ['asset_current', 'liability_current']), ('parent_state', '=', 'posted')],
                'campos': ['account_id', 'debit', 'credit', 'balance'],
                'limite': 500,
            },

            # ── CRM v2 (nuevos) ──
            'conversion_leads': {
                'modelo': 'crm.lead',
                'filtro': [('create_date', '>=', fecha_ini), ('create_date', '<=', fecha_fin)],
                'campos': ['name', 'type', 'stage_id', 'probability', 'partner_id', 'create_date', 'date_closed'],
                'limite': 300,
                'orden': 'create_date desc',
            },
            'actividades_pendientes': {
                'modelo': 'mail.activity',
                'filtro': [('date_deadline', '<=', fecha_fin)],
                'campos': ['res_model', 'res_id', 'activity_type_id', 'summary', 'date_deadline', 'user_id', 'state'],
                'limite': 200,
                'orden': 'date_deadline asc',
            },
            'valor_pipeline': {
                'modelo': 'crm.lead',
                'filtro': [('type', '=', 'opportunity'), ('active', '=', True)],
                'campos': ['name', 'stage_id', 'expected_revenue', 'probability', 'user_id', 'partner_id'],
                'limite': 300,
                'orden': 'expected_revenue desc',
            },
            'win_rate': {
                'modelo': 'crm.lead',
                'filtro': [('create_date', '>=', fecha_ini), ('create_date', '<=', fecha_fin), ('type', '=', 'opportunity')],
                'campos': ['name', 'stage_id', 'probability', 'active', 'date_closed', 'create_date'],
                'limite': 500,
            },
            'tiempo_cierre_promedio': {
                'modelo': 'crm.lead',
                'filtro': [('date_closed', '>=', fecha_ini), ('date_closed', '<=', fecha_fin), ('type', '=', 'opportunity')],
                'campos': ['name', 'create_date', 'date_closed', 'stage_id', 'expected_revenue'],
                'limite': 300,
                'orden': 'date_closed desc',
            },
            'clientes_por_etapa': {
                'modelo': 'crm.lead',
                'filtro': [('type', '=', 'opportunity'), ('active', '=', True)],
                'campos': ['partner_id', 'stage_id', 'expected_revenue', 'probability'],
                'limite': 300,
            },
            'oportunidades_por_vendedor': {
                'modelo': 'crm.lead',
                'filtro': [('type', '=', 'opportunity'), ('active', '=', True)],
                'campos': ['user_id', 'name', 'stage_id', 'expected_revenue', 'probability', 'partner_id'],
                'limite': 300,
                'orden': 'user_id asc',
            },
            'lifetime_value': {
                'modelo': 'sale.order',
                'filtro': [('state', 'in', ['sale', 'done'])],
                'campos': ['partner_id', 'amount_total', 'date_order'],
                'limite': 500,
                'orden': 'partner_id asc',
            },
            'reactivacion_clientes': {
                'modelo': 'sale.order',
                'filtro': [('state', 'in', ['sale', 'done'])],
                'campos': ['partner_id', 'date_order', 'amount_total'],
                'limite': 500,
                'orden': 'partner_id asc',
            },

            # ── Compras v2 (nuevos) ──
            'lead_time_proveedores': {
                'modelo': 'purchase.order',
                'filtro': filtro_fecha_compra + [('state', 'in', ['purchase', 'done'])],
                'campos': ['partner_id', 'date_order', 'date_planned', 'effective_date', 'amount_total'],
                'limite': 300,
                'orden': 'partner_id asc',
            },
            'concentracion_proveedores': {
                'modelo': 'purchase.order',
                'filtro': filtro_fecha_compra + [('state', 'in', ['purchase', 'done'])],
                'campos': ['partner_id', 'amount_total', 'date_order'],
                'limite': 500,
                'orden': 'amount_total desc',
            },
            'comparativa_precios': {
                'modelo': 'purchase.order.line',
                'filtro': [('order_id.date_order', '>=', fecha_ini), ('order_id.date_order', '<=', fecha_fin)],
                'campos': ['product_id', 'partner_id', 'price_unit', 'product_qty', 'date_planned'],
                'limite': 500,
                'orden': 'product_id asc',
            },
            'cumplimiento_entregas': {
                'modelo': 'purchase.order',
                'filtro': filtro_fecha_compra + [('state', 'in', ['purchase', 'done'])],
                'campos': ['partner_id', 'date_planned', 'effective_date', 'amount_total', 'state'],
                'limite': 300,
                'orden': 'date_planned asc',
            },
            'compras_por_categoria': {
                'modelo': 'purchase.order.line',
                'filtro': [('order_id.date_order', '>=', fecha_ini), ('order_id.date_order', '<=', fecha_fin)],
                'campos': ['product_id', 'price_subtotal', 'product_qty'],
                'limite': 500,
            },
            'compras_recurrentes': {
                'modelo': 'purchase.order',
                'filtro': filtro_fecha_compra + [('state', 'in', ['purchase', 'done'])],
                'campos': ['partner_id', 'date_order', 'amount_total', 'origin'],
                'limite': 500,
                'orden': 'partner_id asc',
            },
            'ahorro_potencial': {
                'modelo': 'purchase.order.line',
                'filtro': [('order_id.date_order', '>=', fecha_ini), ('order_id.date_order', '<=', fecha_fin)],
                'campos': ['product_id', 'partner_id', 'price_unit', 'product_qty', 'price_subtotal'],
                'limite': 500,
                'orden': 'product_id asc',
            },
            'compras_urgentes': {
                'modelo': 'purchase.order',
                'filtro': filtro_fecha_compra + [('priority', '!=', False)],
                'campos': ['name', 'partner_id', 'amount_total', 'date_order', 'date_planned', 'priority', 'state'],
                'limite': 200,
                'orden': 'date_order desc',
            },
            'gasto_por_departamento': {
                'modelo': 'purchase.order',
                'filtro': filtro_fecha_compra + [('state', 'in', ['purchase', 'done'])],
                'campos': ['partner_id', 'amount_total', 'date_order', 'user_id'],
                'limite': 500,
                'orden': 'user_id asc',
            },

            # ── PDV v2 (nuevos) ──
            'horarios_pico': {
                'modelo': 'pos.order',
                'filtro': [('date_order', '>=', fecha_ini), ('date_order', '<=', fecha_fin), ('state', 'in', ['paid', 'done', 'invoiced'])],
                'campos': ['date_order', 'amount_total', 'lines', 'session_id'],
                'limite': 500,
                'orden': 'date_order desc',
            },
            'devoluciones_pos': {
                'modelo': 'pos.order',
                'filtro': [('date_order', '>=', fecha_ini), ('date_order', '<=', fecha_fin), ('amount_total', '<', 0)],
                'campos': ['name', 'partner_id', 'amount_total', 'date_order', 'pos_reference', 'session_id'],
                'limite': 200,
                'orden': 'date_order desc',
            },
            'descuentos_pos': {
                'modelo': 'pos.order.line',
                'filtro': [('order_id.date_order', '>=', fecha_ini), ('order_id.date_order', '<=', fecha_fin), ('discount', '>', 0)],
                'campos': ['product_id', 'price_unit', 'qty', 'discount', 'price_subtotal_incl', 'order_id'],
                'limite': 300,
                'orden': 'discount desc',
            },
            'pos_por_sucursal': {
                'modelo': 'pos.order',
                'filtro': [('date_order', '>=', fecha_ini), ('date_order', '<=', fecha_fin), ('state', 'in', ['paid', 'done', 'invoiced'])],
                'campos': ['config_id', 'amount_total', 'date_order', 'session_id'],
                'limite': 500,
                'orden': 'config_id asc',
            },
            'ticket_detalle': {
                'modelo': 'pos.order',
                'filtro': [('date_order', '>=', fecha_ini), ('date_order', '<=', fecha_fin)],
                'campos': ['name', 'partner_id', 'amount_total', 'amount_tax', 'date_order', 'lines', 'pos_reference'],
                'limite': 100,
                'orden': 'date_order desc',
            },
            'productos_mas_vendidos_pos': {
                'modelo': 'pos.order.line',
                'filtro': [('order_id.date_order', '>=', fecha_ini), ('order_id.date_order', '<=', fecha_fin)],
                'campos': ['product_id', 'qty', 'price_subtotal_incl'],
                'limite': 500,
                'orden': 'qty desc',
            },
            'merma_pos': {
                'modelo': 'pos.order',
                'filtro': [('date_order', '>=', fecha_ini), ('date_order', '<=', fecha_fin), ('amount_total', '<=', 0)],
                'campos': ['name', 'amount_total', 'date_order', 'note', 'session_id'],
                'limite': 200,
                'orden': 'date_order desc',
            },
            'rendimiento_terminal': {
                'modelo': 'pos.session',
                'filtro': [('start_at', '>=', fecha_ini), ('start_at', '<=', fecha_fin)],
                'campos': ['config_id', 'user_id', 'start_at', 'stop_at', 'state', 'order_count', 'total_payments_amount'],
                'limite': 200,
                'orden': 'start_at desc',
            },
            'cierre_caja_pendiente': {
                'modelo': 'pos.session',
                'filtro': [('state', '=', 'opened')],
                'campos': ['name', 'config_id', 'user_id', 'start_at', 'cash_register_balance_start', 'cash_register_balance_end_real'],
                'limite': 50,
                'orden': 'start_at asc',
            },
            'ventas_pos_vs_ecommerce': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['team_id', 'amount_total', 'date_order', 'partner_id', 'website_id'],
                'limite': 500,
                'orden': 'date_order desc',
            },

            # ── RRHH v2 (nuevos) ──
            'costo_por_empleado': {
                'modelo': 'hr.contract',
                'filtro': [('state', '=', 'open')],
                'campos': ['employee_id', 'department_id', 'wage', 'date_start', 'date_end', 'job_id'],
                'limite': 300,
                'orden': 'department_id asc',
            },
            'ausentismo_analisis': {
                'modelo': 'hr.leave',
                'filtro': [('date_from', '>=', fecha_ini), ('date_from', '<=', fecha_fin), ('state', '=', 'validate')],
                'campos': ['employee_id', 'holiday_status_id', 'date_from', 'date_to', 'number_of_days', 'department_id'],
                'limite': 500,
                'orden': 'date_from desc',
            },
            'brecha_salarial': {
                'modelo': 'hr.contract',
                'filtro': [('state', '=', 'open')],
                'campos': ['employee_id', 'department_id', 'job_id', 'wage'],
                'limite': 500,
                'orden': 'job_id asc',
            },
            'productividad_departamento': {
                'modelo': 'hr.employee',
                'filtro': [('active', '=', True)],
                'campos': ['name', 'department_id', 'job_id', 'work_email', 'create_date'],
                'limite': 500,
                'orden': 'department_id asc',
            },
            'antiguedad_empleados': {
                'modelo': 'hr.employee',
                'filtro': [('active', '=', True)],
                'campos': ['name', 'department_id', 'job_id', 'create_date', 'contract_id'],
                'limite': 500,
                'orden': 'create_date asc',
            },
            'vacaciones_pendientes': {
                'modelo': 'hr.leave.allocation',
                'filtro': [('state', '=', 'validate')],
                'campos': ['employee_id', 'holiday_status_id', 'number_of_days', 'leaves_taken', 'department_id'],
                'limite': 300,
                'orden': 'employee_id asc',
            },
            'costo_rotacion': {
                'modelo': 'hr.employee',
                'filtro': [],
                'campos': ['name', 'department_id', 'active', 'create_date', 'departure_date', 'departure_reason_id'],
                'limite': 500,
                'orden': 'create_date desc',
            },
            'clima_organizacional': {
                'modelo': 'hr.leave',
                'filtro': [('date_from', '>=', fecha_ini), ('date_from', '<=', fecha_fin)],
                'campos': ['employee_id', 'holiday_status_id', 'number_of_days', 'date_from', 'state', 'department_id'],
                'limite': 500,
            },
            'cumplimiento_jornada': {
                'modelo': 'hr.attendance',
                'filtro': [('check_in', '>=', fecha_ini), ('check_in', '<=', fecha_fin)],
                'campos': ['employee_id', 'check_in', 'check_out', 'worked_hours'],
                'limite': 500,
                'orden': 'check_in desc',
            },
            'estructura_organizacional': {
                'modelo': 'hr.department',
                'filtro': [('active', '=', True)],
                'campos': ['name', 'parent_id', 'manager_id', 'total_employee', 'company_id'],
                'limite': 200,
                'orden': 'name asc',
            },
            'incapacidades': {
                'modelo': 'hr.leave',
                'filtro': [('date_from', '>=', fecha_ini), ('date_from', '<=', fecha_fin), ('state', '=', 'validate')],
                'campos': ['employee_id', 'holiday_status_id', 'date_from', 'date_to', 'number_of_days', 'department_id'],
                'limite': 300,
                'orden': 'date_from desc',
            },
            'prestaciones_resumen': {
                'modelo': 'hr.contract',
                'filtro': [('state', '=', 'open')],
                'campos': ['employee_id', 'department_id', 'wage', 'date_start', 'structure_type_id', 'job_id'],
                'limite': 300,
                'orden': 'department_id asc',
            },

            # ── Diagnóstico v2 (nuevos) ──
            'campos_vacios_criticos': {
                'modelo': 'res.partner',
                'filtro': [('active', '=', True), ('customer_rank', '>', 0)],
                'campos': ['name', 'email', 'phone', 'vat', 'street', 'city', 'country_id', 'create_date'],
                'limite': 500,
                'orden': 'create_date desc',
            },
            'validacion_cruzada': {
                'modelo': 'account.move',
                'filtro': [('state', '=', 'posted'), ('move_type', 'in', ['out_invoice', 'in_invoice'])],
                'campos': ['name', 'partner_id', 'amount_total', 'invoice_origin', 'invoice_date', 'move_type'],
                'limite': 300,
                'orden': 'invoice_date desc',
            },
            'consistencia_datos': {
                'modelo': 'res.partner',
                'filtro': [('active', '=', True)],
                'campos': ['name', 'email', 'phone', 'vat', 'street', 'country_id', 'create_date', 'write_date'],
                'limite': 500,
                'orden': 'write_date desc',
            },
            'reconciliacion_stock_contable': {
                'modelo': 'stock.quant',
                'filtro': [('quantity', '!=', 0)],
                'campos': ['product_id', 'location_id', 'quantity', 'value', 'accounting_date'],
                'limite': 500,
            },
            'integridad_referencial': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['name', 'partner_id', 'partner_invoice_id', 'partner_shipping_id', 'state'],
                'limite': 300,
                'orden': 'date_order desc',
            },
            'secuencias_rotas': {
                'modelo': 'ir.sequence',
                'filtro': [],
                'campos': ['name', 'code', 'number_next_actual', 'prefix', 'suffix', 'padding'],
                'limite': 200,
                'orden': 'code asc',
            },
            'configuraciones_riesgosas': {
                'modelo': 'res.config.settings',
                'filtro': [],
                'campos': ['create_date'],
                'limite': 1,
            },
            'accesos_inusuales': {
                'modelo': 'res.users',
                'filtro': [('active', '=', True)],
                'campos': ['login', 'name', 'groups_id', 'login_date', 'create_date'],
                'limite': 200,
                'orden': 'login_date desc',
            },
            'operaciones_masivas': {
                'modelo': 'mail.message',
                'filtro': [('date', '>=', fecha_ini), ('date', '<=', fecha_fin), ('message_type', '=', 'notification')],
                'campos': ['model', 'res_id', 'date', 'author_id', 'body'],
                'limite': 300,
                'orden': 'date desc',
            },
            'salud_base_datos': {
                'modelo': 'res.users',
                'filtro': [('active', '=', True)],
                'campos': ['login', 'name', 'login_date', 'create_date', 'groups_id'],
                'limite': 200,
                'orden': 'login_date desc',
            },

            # ── Odoo v2 (nuevos) ──
            'explorar_modelo': {
                'modelo': 'ir.model',
                'filtro': [('transient', '=', False)],
                'campos': ['name', 'model', 'state', 'field_id', 'info'],
                'limite': 200,
                'orden': 'model asc',
            },
            'campos_modelo': {
                'modelo': 'ir.model.fields',
                'filtro': [],
                'campos': ['name', 'model_id', 'field_description', 'ttype', 'required', 'store'],
                'limite': 500,
                'orden': 'model_id asc',
            },
            'relaciones_modelo': {
                'modelo': 'ir.model.fields',
                'filtro': [('ttype', 'in', ['many2one', 'one2many', 'many2many'])],
                'campos': ['name', 'model_id', 'relation', 'ttype', 'field_description'],
                'limite': 500,
                'orden': 'model_id asc',
            },
            'flujo_trabajo_modelo': {
                'modelo': 'ir.model',
                'filtro': [('transient', '=', False)],
                'campos': ['name', 'model', 'state', 'info'],
                'limite': 100,
                'orden': 'model asc',
            },
            'permisos_usuario': {
                'modelo': 'res.users',
                'filtro': [('active', '=', True)],
                'campos': ['login', 'name', 'groups_id', 'company_ids'],
                'limite': 200,
                'orden': 'name asc',
            },
            'log_acciones_usuario': {
                'modelo': 'mail.message',
                'filtro': [('date', '>=', fecha_ini), ('date', '<=', fecha_fin), ('author_id', '!=', False)],
                'campos': ['model', 'res_id', 'date', 'author_id', 'message_type', 'subtype_id'],
                'limite': 500,
                'orden': 'date desc',
            },
            'parametros_sistema': {
                'modelo': 'ir.config_parameter',
                'filtro': [],
                'campos': ['key', 'value', 'write_date'],
                'limite': 200,
                'orden': 'key asc',
            },
            'version_odoo': {
                'modelo': 'ir.module.module',
                'filtro': [('name', '=', 'base')],
                'campos': ['name', 'installed_version', 'latest_version'],
                'limite': 1,
            },
            'consulta_sql_segura': {
                'modelo': 'ir.model',
                'filtro': [('transient', '=', False)],
                'campos': ['name', 'model'],
                'limite': 50,
                'orden': 'model asc',
            },

            # ── Estadística / Matemáticas v2 (nuevos) ──
            'score_salud_negocio': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['date_order', 'amount_total', 'partner_id', 'state'],
                'limite': 500,
                'orden': 'date_order desc',
            },
            'curva_abc_ventas': {
                'modelo': 'sale.order.line',
                'filtro': [('order_id.date_order', '>=', fecha_ini), ('order_id.date_order', '<=', fecha_fin)],
                'campos': ['product_id', 'price_subtotal', 'product_uom_qty'],
                'limite': 500,
                'orden': 'price_subtotal desc',
            },
            'comparativa_tiendas': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['team_id', 'warehouse_id', 'amount_total', 'date_order'],
                'limite': 500,
                'orden': 'team_id asc',
            },
            'calculo_cagr': {
                'modelo': 'sale.order',
                'filtro': [('state', 'in', ['sale', 'done'])],
                'campos': ['date_order', 'amount_total'],
                'limite': 1000,
                'orden': 'date_order asc',
            },
            'calculo_margen_contribucion': {
                'modelo': 'sale.order.line',
                'filtro': [('order_id.date_order', '>=', fecha_ini), ('order_id.date_order', '<=', fecha_fin)],
                'campos': ['product_id', 'price_unit', 'product_uom_qty', 'price_subtotal', 'discount'],
                'limite': 500,
                'orden': 'price_subtotal desc',
            },
            'forecast_estacional': {
                'modelo': 'sale.order',
                'filtro': [('state', 'in', ['sale', 'done'])],
                'campos': ['date_order', 'amount_total', 'partner_id'],
                'limite': 1000,
                'orden': 'date_order asc',
            },
            'prediccion_flujo_caja': {
                'modelo': 'account.move',
                'filtro': [('state', '=', 'posted'), ('move_type', 'in', ['out_invoice', 'in_invoice'])],
                'campos': ['move_type', 'amount_total', 'amount_residual', 'invoice_date', 'invoice_date_due'],
                'limite': 500,
                'orden': 'invoice_date desc',
            },
            'escenarios_what_if': {
                'modelo': 'sale.order',
                'filtro': filtro_fecha_venta,
                'campos': ['date_order', 'amount_total', 'partner_id', 'user_id'],
                'limite': 500,
                'orden': 'date_order desc',
            },
        }

        return mapeo.get(accion, {})


