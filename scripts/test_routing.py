import sys, os, re
sys.path.insert(0, r'c:\Users\procesos\Documents\ANDROMEDA')
os.chdir(r'c:\Users\procesos\Documents\ANDROMEDA')

from utils.intenciones_extendidas import INTENCIONES_EXTENDIDAS

v2_actions = [
    'ventas_por_canal','margen_por_producto','devolucion_ventas','meta_cumplimiento',
    'ventas_por_hora','concentracion_clientes','descuentos_aplicados','ventas_vs_anterior',
    'abc_inventario','inventario_obsoleto','costo_almacenamiento','trazabilidad_lote',
    'inventario_negativo','inventario_por_categoria','cobertura_stock','merma_inventario',
    'transferencias_pendientes','inventario_valorizado_categoria','comparar_stock_fisico_sistema',
    'conciliacion_bancaria','analisis_antiguedad','notas_credito','impuestos_resumen',
    'margen_operativo','razon_liquidez','capital_trabajo','pagos_pendientes_aplicar',
    'estado_cuenta_cliente','estado_cuenta_proveedor',
    'conversion_leads','actividades_pendientes','oportunidades_estancadas','win_rate',
    'tiempo_cierre_promedio','leads_por_origen','clientes_por_etapa','lifetime_value','reactivacion_clientes',
    'evaluacion_proveedores','comparativa_precios','ordenes_pendientes','cumplimiento_entregas',
    'compras_por_categoria','compras_recurrentes','ahorro_potencial','compras_urgentes',
    'variacion_precios','gasto_por_departamento',
    'productividad_cajero','devoluciones_pos','descuentos_pos','cuadre_caja',
    'pos_por_sucursal','ticket_detalle','productos_mas_vendidos_pos','merma_pos',
    'rendimiento_terminal','ventas_pos_vs_ecommerce',
    'brecha_salarial','horas_extra','vacaciones_pendientes','costo_rotacion',
    'clima_organizacional','cumplimiento_jornada','estructura_organizacional','incapacidades','prestaciones_resumen',
    'validacion_cruzada','consistencia_datos','registros_duplicados','reconciliacion_stock_contable',
    'integridad_referencial','secuencias_rotas','configuraciones_riesgosas','accesos_inusuales','operaciones_masivas',
    'relaciones_modelo','flujo_trabajo_modelo','permisos_usuario','log_acciones_usuario',
    'modulos_instalados','ir_cron_activos','parametros_sistema','mostrar_capacidades','generar_pdf_profesional',
]

acciones_en_extendidas = {cfg['accion'] for cfg in INTENCIONES_EXTENDIDAS.values()}
keys_extendidas = set(INTENCIONES_EXTENDIDAS.keys())

missing = [a for a in v2_actions if a not in acciones_en_extendidas and a not in keys_extendidas]
print(f'Acciones v2 sin patron regex: {len(missing)}')
if missing:
    print('FALTANTES:', missing)
else:
    print('TODAS CUBIERTAS!')

# Test routing simulation
print('\n--- TEST ROUTING SIMULATION ---')
patrones_ext = []
for nombre, config in INTENCIONES_EXTENDIDAS.items():
    accion = config.get('accion', nombre)
    prioridad = config.get('prioridad', 5)
    pats = []
    for p in config.get('patrones', []):
        try:
            pats.append(re.compile(p, re.IGNORECASE))
        except re.error:
            pass
    if pats:
        patrones_ext.append({'nombre': nombre, 'accion': accion, 'prioridad': prioridad, 'patrones': pats})

patrones_ext.sort(key=lambda x: x['prioridad'], reverse=True)

test_msgs = [
    ('productos obsoletos', 'inventario_obsoleto'),
    ('brecha salarial', 'brecha_salarial'),
    ('vacaciones pendientes', 'vacaciones_pendientes'),
    ('horas extra del mes', 'horas_extra'),
    ('cumplimiento de meta de ventas', 'meta_cumplimiento'),
    ('tasa de conversion de leads', 'conversion_leads'),
    ('modulos instalados en odoo', 'modulos_instalados'),
    ('notas de credito pendientes', 'notas_credito'),
    ('comparar stock fisico vs sistema', 'comparar_stock_fisico_sistema'),
    ('compras urgentes', 'compras_urgentes'),
    ('generar pdf de ventas', 'generar_pdf_profesional'),
    ('ventas pos vs ecommerce', 'ventas_pos_vs_ecommerce'),
]

header = 'MENSAJE'.ljust(45) + 'ESPERADO'.ljust(35) + 'DETECTADO'.ljust(35) + 'OK'
print(header)
print('-'*130)
for msg, expected in test_msgs:
    detected = None
    for item in patrones_ext:
        for pat in item['patrones']:
            if pat.search(msg.lower()):
                detected = item['accion']
                break
        if detected:
            break
    ok = 'OK' if detected == expected else 'FAIL'
    print(msg.ljust(45) + expected.ljust(35) + str(detected).ljust(35) + ok)
