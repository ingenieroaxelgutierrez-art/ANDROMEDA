import sys, os, re
sys.path.insert(0, r'c:\Users\procesos\Documents\ANDROMEDA')
os.chdir(r'c:\Users\procesos\Documents\ANDROMEDA')

from utils.intenciones_extendidas import INTENCIONES_EXTENDIDAS

# Build compiled patterns sorted by priority
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
    ("productos obsoletos", "inventario_obsoleto"),
    ("brecha salarial entre hombres y mujeres", "brecha_salarial"),
    ("vacaciones pendientes de los empleados", "vacaciones_pendientes"),
    ("horas extra del mes", "horas_extra"),
    ("cumplimiento de meta de ventas del trimestre", "meta_cumplimiento"),
    ("tasa de conversion de leads del mes", "conversion_leads"),
    ("modulos instalados en odoo", "modulos_instalados"),
    ("notas de credito pendientes", "notas_credito"),
    ("comparar stock fisico vs sistema", "comparar_stock_fisico_sistema"),
    ("compras urgentes que hay", "compras_urgentes"),
    ("generar pdf de ventas", "generar_pdf_profesional"),
    ("ventas pos vs ecommerce", "ventas_pos_vs_ecommerce"),
    ("win rate del equipo de ventas", "win_rate"),
    ("razon de liquidez de la empresa", "razon_liquidez"),
    ("transferencias pendientes de stock", "transferencias_pendientes"),
    ("organigrama de la empresa", "estructura_organizacional"),
    ("accesos inusuales de usuarios", "accesos_inusuales"),
    ("tareas programadas en odoo", "ir_cron_activos"),
    ("validacion cruzada entre modulos", "validacion_cruzada"),
    ("que puedes hacer", "mostrar_capacidades"),
]

passed = 0
failed = 0
print(f"{'MENSAJE':<50} {'ESPERADO':<35} {'DETECTADO':<35} {'OK'}")
print("-"*130)
for msg, expected in test_msgs:
    detected = None
    for item in patrones_ext:
        for pat in item['patrones']:
            if pat.search(msg.lower()):
                detected = item['accion']
                break
        if detected:
            break
    ok = "+" if detected == expected else "X"
    if detected == expected:
        passed += 1
    else:
        failed += 1
    print(f"{msg:<50} {expected:<35} {str(detected):<35} {ok}")

print(f"\nResultado: {passed}/{len(test_msgs)} correctos")
