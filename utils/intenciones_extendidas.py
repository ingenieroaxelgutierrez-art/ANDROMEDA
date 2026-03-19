# ============================================================
# MOTOR NLP EXTENDIDO - Todos los Intents para Odoo
# ============================================================
# Extensión del motor NLP con intenciones para todas las áreas
# ============================================================

# Intenciones adicionales para el motor NLP
# Se agregan a las intenciones base

INTENCIONES_EXTENDIDAS = {
    
    # ========== VENTAS AVANZADAS ==========
    'analisis_ventas': {
        'patrones': [
            r'(anali[zs]a|análisis)\s*(de|las?|los?)?\s*ventas?',
            r'(estadísticas?|stats?)\s*(de)?\s*ventas?',
            r'(insight|insights)\s*(de)?\s*ventas?',
            r'(rendimiento|performance)\s*(de)?\s*ventas?',
        ],
        'prioridad': 12,
        'accion': 'analisis_ventas'
    },
    
    'top_productos': {
        'patrones': [
            r'(top|ranking|mejores|más\s*vendidos?)\s*(de)?\s*productos?',
            r'productos?\s*(más|mas)\s*vendidos?',
            r'(qué|que|cuáles|cuales)\s*(productos?|artículos?)\s*(se\s*)?(vende|venden)\s*(más|mas)',
            r'productos?\s*estrella',
            r'(best|top)\s*sellers?',
        ],
        'prioridad': 11,
        'accion': 'top_productos'
    },
    
    'top_clientes': {
        'patrones': [
            r'(top|ranking|mejores)\s*(de)?\s*clientes?',
            r'clientes?\s*(más|mas)\s*(importantes?|grandes?|frecuentes?)',
            r'(quiénes?|quienes?|cuáles?|cuales?)\s*(son)?\s*(mis|los)?\s*(mejores?|principales?)\s*clientes?',
            r'clientes?\s*vip',
            r'pareto\s*(de)?\s*clientes?',
        ],
        'prioridad': 11,
        'accion': 'top_clientes'
    },
    
    'tendencia': {
        'patrones': [
            r'tendencia\s*(de|del|en)?\s*(ventas?|pos|ingresos?)?',
            r'(cómo|como)\s*(va|van|está|estan)\s*(las?)?\s*ventas?',
            r'(evolución|evolucion)\s*(de|del)',
            r'(histor|histórico|histórial)\s*(de)?\s*ventas?',
            r'(proyección|proyeccion|forecast)\s*(de)?\s*ventas?',
        ],
        'prioridad': 11,
        'accion': 'tendencia'
    },
    
    'ventas_por_vendedor': {
        'patrones': [
            r'ventas?\s*(por|de)\s*(cada|los?)?\s*vendedor(es)?',
            r'(rendimiento|performance|desempeño)\s*(de|por)\s*vendedor(es)?',
            r'(ranking|top)\s*(de)?\s*vendedor(es)?',
            r'(quién|quien)\s*vende?\s*(más|mas)',
            r'mejor\s*vendedor',
        ],
        'prioridad': 11,
        'accion': 'ventas_por_vendedor'
    },
    
    'comparativa': {
        'patrones': [
            r'compara(r|tiva|ción)?',
            r'(hoy|esta\s*semana|este\s*mes)\s*(vs|versus|contra)\s*(ayer|semana\s*pasada|mes\s*pasado)',
            r'(diferencia|variación)\s*(entre|de)',
            r'(crecimiento|decrecimiento)\s*(de|en)',
        ],
        'prioridad': 10,
        'accion': 'comparativa'
    },
    
    # ========== PUNTO DE VENTA (POS) ==========
    'analisis_pos': {
        'patrones': [
            r'(análisis|analisis|anali[zs]a)\s*(de|del)?\s*(pos|punto\s*de\s*venta|tickets?|caja)',
            r'(estadísticas?|stats?)\s*(del?)?\s*(pos|tienda|caja)',
            r'(resumen|reporte)\s*(del?)?\s*(pos|tienda)',
            r'métricas?\s*(del?)?\s*pos',
        ],
        'prioridad': 11,
        'accion': 'analisis_pos'
    },
    
    'sesiones_pos': {
        'patrones': [
            r'(sesiones?|turnos?|cajas?)\s*(de|del)?\s*pos',
            r'(cierre|apertura)\s*(de)?\s*(caja|sesión)',
            r'(arqueo|cuadre)\s*(de)?\s*caja',
            r'(diferencias?|faltantes?)\s*(en|de)?\s*caja',
        ],
        'prioridad': 10,
        'accion': 'sesiones_pos'
    },
    
    'sesiones_abiertas': {
        'patrones': [
            r'(sesiones?|cajas?)\s*(de\s*pos\s*)?(abiertas?|activas?|sin\s*cerrar)',
            r'(cajas?|sesiones?)\s*que\s*(están?|estan?)\s*(abiertas?|activas?)',
            r'(pos|tiendas?)\s*(abiert[oa]s?|sin\s*cerrar)',
            r'(cuántas?|cuantas?|cuál|cual|qué|que)\s*(cajas?|sesiones?)\s*(están?|hay)\s*(abiert|activ)',
        ],
        'prioridad': 12,
        'accion': 'sesiones_abiertas'
    },
    
    'kpi_ticket_promedio': {
        'patrones': [
            r'ticket\s*promedio',
            r'ticket\s*medio',
            r'(venta|orden)\s*promedio',
            r'promedio\s*(de|por)\s*(venta|ticket|orden)',
            r'(cuál|cual|cuánto|cuanto)\s*(es)?\s*(el)?\s*ticket\s*promedio',
        ],
        'prioridad': 12,
        'accion': 'kpi_ticket_promedio'
    },
    
    'productos_costo_cero': {
        'patrones': [
            r'productos?\s*(con|sin)\s*costo\s*(cero|0)',
            r'productos?\s*costo\s*(cero|0|\$0)',
            r'(sin|con)\s*precio\s*(de)?\s*costo',
            r'costo\s*(igual|=)\s*(a)?\s*(cero|0)',
        ],
        'prioridad': 12,
        'accion': 'productos_costo_cero'
    },
    
    'productos_sin_categoria': {
        'patrones': [
            r'productos?\s*sin\s*categor[ií]a',
            r'productos?\s*sin\s*clasificar',
            r'(cuántos|cuantos|qué|que)\s*productos?\s*sin\s*categor[ií]a',
            r'productos?\s*(no|sin)\s*(tienen?|asignada)\s*categor[ií]a',
        ],
        'prioridad': 12,
        'accion': 'productos_sin_categoria'
    },
    
    'metodos_pago': {
        'patrones': [
            r'(métodos?|formas?)\s*(de)?\s*pago',
            r'(pagos?)\s*(en)?\s*(efectivo|tarjeta|transferencia)',
            r'(cuánto|cuanto)\s*(se\s*)?(cobró|cobro)\s*(en|con)\s*(efectivo|tarjeta)',
            r'(distribución|distribucion)\s*(de)?\s*(pagos?|formas?)',
        ],
        'prioridad': 10,
        'accion': 'metodos_pago'
    },
    
    # ========== FACTURACIÓN ==========
    'consultar_facturas': {
        'patrones': [
            r'(facturas?|facturación|facturacion)\s*(de|del|hoy|mes|semana)?',
            r'(cuántas?|cuantas?)\s*facturas?',
            r'(cfdi|timbrado|timbre)',
            r'(notas?\s*de\s*crédito|notas?\s*credito)',
            r'(ver|mostrar|consultar)\s*(las?)?\s*facturas?',
        ],
        'prioridad': 10,
        'accion': 'consultar_facturas'
    },
    
    'analisis_facturacion': {
        'patrones': [
            r'(análisis|analisis)\s*(de)?\s*(facturación|facturacion|facturas?)',
            r'(estadísticas?|stats?)\s*(de)?\s*(facturación|facturacion)',
            r'(resumen|reporte)\s*(de)?\s*facturación',
            r'(cfdi|timbres?)\s*(emitidos?|cancelados?)',
        ],
        'prioridad': 11,
        'accion': 'analisis_facturacion'
    },
    
    'cuentas_por_cobrar': {
        'patrones': [
            r'(cuentas?\s*(por)?\s*cobrar|cxc|cartera)',
            r'(clientes?\s*)(que\s*)?(deben|adeuda[nr]?|pendientes?)',
            r'(facturas?\s*)(sin\s*(cobrar|pagar)|pendientes?|vencidas?)',
            r'(cobranza|morosidad)',
            r'(antigüedad|antiguedad)\s*(de)?\s*(cartera|saldos?)',
            r'(deuda|saldo)\s*(de|del)\s*cliente',
        ],
        'prioridad': 11,
        'accion': 'cuentas_por_cobrar'
    },
    
    'cuentas_por_pagar': {
        'patrones': [
            r'(cuentas?\s*(por)?\s*pagar|cxp)',
            r'(proveedores?\s*)(que\s*)?(debemos|adeudamos?|pendientes?)',
            r'(facturas?\s*de\s*proveedores?)\s*(pendientes?|vencidas?)',
            r'(deuda|saldo)\s*(a|con)\s*(proveedores?)',
            r'(qué|que)\s*(debemos|adeudamos)\s*(a)?\s*proveedores?',
        ],
        'prioridad': 11,
        'accion': 'cuentas_por_pagar'
    },
    
    # ========== PAGOS ==========
    'consultar_pagos': {
        'patrones': [
            r'(pagos?|cobros?)\s*(de|del|recibidos?|realizados?)',
            r'(cuánto|cuanto)\s*(se\s*)?(cobró|pago|pagó)',
            r'(ver|mostrar|consultar)\s*(los?)?\s*(pagos?|cobros?)',
            r'(transferencias?|depósitos?|depositos?)',
        ],
        'prioridad': 10,
        'accion': 'consultar_pagos'
    },
    
    # ========== INVENTARIO AVANZADO ==========
    'analisis_inventario': {
        'patrones': [
            r'(análisis|analisis)\s*(de|del)?\s*(inventario|stock|almacén|almacen)',
            r'(estadísticas?|métricas?)\s*(de|del)?\s*(inventario|stock)',
            r'(resumen|reporte)\s*(de|del)?\s*inventario',
            r'(estado|situación)\s*(del?)?\s*almacén',
        ],
        'prioridad': 11,
        'accion': 'analisis_inventario'
    },
    
    'rotacion_inventario': {
        'patrones': [
            r'(rotación|rotacion)\s*(de|del)?\s*(inventario|productos?|stock)',
            r'(días?|dias?)\s*(de)?\s*(inventario|stock)',
            r'(velocidad|rapidez)\s*(de)?\s*(rotación|venta)',
            r'(productos?)\s*(lentos?|obsoletos?|estancados?)',
            r'(lento|sin)\s*(movimiento|rotación)',
        ],
        'prioridad': 10,
        'accion': 'rotacion_inventario'
    },
    
    'productos_sin_stock': {
        'patrones': [
            r'(productos?|artículos?)\s*(sin|con\s*cero|agotados?)',
            r'(sin|cero|falta\s*de)\s*stock',
            r'(qué|que|cuáles?|cuales?)\s*(productos?)\s*(no\s*hay|falta[nr]?|agotados?)',
            r'(desabasto|faltantes?)',
        ],
        'prioridad': 10,
        'accion': 'productos_sin_stock'
    },
    
    'productos_bajo_minimo': {
        'patrones': [
            r'(productos?|stock)\s*(bajo|debajo)\s*(del?)?\s*(mínimo|minimo)',
            r'(alertas?|advertencias?)\s*(de)?\s*(stock|inventario)',
            r'(qué|que)\s*(productos?)\s*(hay\s*que)?\s*(pedir|ordenar|comprar)',
            r'(falta[nr]?\s*)(de)?\s*stock',
        ],
        'prioridad': 10,
        'accion': 'productos_bajo_minimo'
    },
    
    'valoracion_inventario': {
        'patrones': [
            r'(valoración|valoracion|valor)\s*(del?)?\s*(inventario|stock)',
            r'(cuánto|cuanto)\s*(vale|cuesta)\s*(el|mi)?\s*(inventario|stock)',
            r'(costo|coste)\s*(del?)?\s*inventario',
            r'(capital|inversión)\s*(en)?\s*(inventario|productos?)',
        ],
        'prioridad': 10,
        'accion': 'valoracion_inventario'
    },
    
    'movimientos_stock': {
        'patrones': [
            r'(movimientos?|traslados?|transferencias?)\s*(de|del)?\s*(stock|inventario)',
            r'(entradas?|salidas?)\s*(de|del)?\s*(almacén|stock|inventario)',
            r'(historial|kardex)\s*(de)?\s*movimientos?',
        ],
        'prioridad': 9,
        'accion': 'movimientos_stock'
    },
    
    # ========== COMPRAS ==========
    'consultar_compras': {
        'patrones': [
            r'(compras?|órdenes?\s*de\s*compra|purchase)',
            r'(pedidos?\s*a)\s*proveedores?',
            r'(ver|mostrar|consultar)\s*(las?)?\s*compras?',
            r'(cuánto|cuanto)\s*(gastamos|compramos)',
        ],
        'prioridad': 10,
        'accion': 'consultar_compras'
    },
    
    'analisis_compras': {
        'patrones': [
            r'(análisis|analisis)\s*(de)?\s*(compras?|adquisiciones?)',
            r'(estadísticas?|métricas?)\s*(de)?\s*compras?',
            r'(resumen|reporte)\s*(de)?\s*compras?',
            r'(gasto|gastos)\s*(con)?\s*proveedores?',
        ],
        'prioridad': 11,
        'accion': 'analisis_compras'
    },
    
    'top_proveedores': {
        'patrones': [
            r'(top|ranking|principales?|mejores?)\s*(de)?\s*proveedores?',
            r'proveedores?\s*(principales?|importantes?|top)',
            r'(a\s*quién|a\s*quien|qué\s*proveedor)\s*(le\s*)?(compramos?)\s*(más|mas)',
            r'(mayor|mayores?)\s*(proveedor|proveedores?)',
        ],
        'prioridad': 10,
        'accion': 'top_proveedores'
    },
    
    # ========== RECURSOS HUMANOS ==========
    'consultar_empleados': {
        'patrones': [
            r'(empleados?|personal|trabajadores?|staff|colaboradores?)',
            r'(cuántos?|cuantos?)\s*empleados?',
            r'(lista|listado|nómina)\s*(de)?\s*empleados?',
            r'(ver|mostrar|consultar)\s*(los?)?\s*empleados?',
            r'(plantilla|headcount)',
        ],
        'prioridad': 10,
        'accion': 'consultar_empleados'
    },
    
    'analisis_rh': {
        'patrones': [
            r'(análisis|analisis)\s*(de)?\s*(rh|recursos?\s*humanos?|personal)',
            r'(estadísticas?|métricas?)\s*(de)?\s*(rh|personal|empleados?)',
            r'(dashboard|resumen)\s*(de)?\s*(rh|personal)',
            r'(indicadores?|kpis?)\s*(de)?\s*(rh|personal)',
        ],
        'prioridad': 11,
        'accion': 'analisis_rh'
    },
    
    'headcount': {
        'patrones': [
            r'headcount',
            r'(número|numero)\s*(de)?\s*(empleados?|personal)',
            r'(cuántos?|cuantos?)\s*(somos|empleados?|personas?)',
            r'(tamaño|size)\s*(del?)?\s*(equipo|empresa|plantilla)',
            r'(empleados?\s*por)\s*(departamento|área|puesto)',
        ],
        'prioridad': 11,
        'accion': 'headcount'
    },
    
    'departamentos': {
        'patrones': [
            r'(departamentos?|áreas?|areas?|divisiones?)',
            r'(estructura|organigrama)',
            r'(ver|mostrar|cuáles?|cuales?)\s*(son\s*los?)?\s*departamentos?',
            r'(empleados?\s*por|en\s*cada)\s*departamento',
        ],
        'prioridad': 9,
        'accion': 'departamentos'
    },
    
    'rotacion_personal': {
        'patrones': [
            r'(rotación|rotacion)\s*(de)?\s*(personal|empleados?)',
            r'(índice|indice|tasa)\s*(de)?\s*(rotación|rotacion)',
            r'(altas?|bajas?)\s*(de)?\s*(personal|empleados?)',
            r'(turnover)',
            r'(quiénes?|quienes?)\s*(renunciaron?|salieron?|se\s*fueron)',
        ],
        'prioridad': 10,
        'accion': 'rotacion_personal'
    },
    
    'asistencia': {
        'patrones': [
            r'(asistencia|checadas?|reloj\s*checador)',
            r'(entradas?|salidas?)\s*(de)?\s*(personal|empleados?)',
            r'(horas?\s*trabajadas?)',
            r'(registro|control)\s*(de)?\s*asistencia',
            r'(quién|quien|quiénes|quienes)\s*(llegó?|llego?|falto?|faltó?)',
        ],
        'prioridad': 10,
        'accion': 'asistencia'
    },
    
    'ausencias': {
        'patrones': [
            r'(ausencias?|faltas?|inasistencias?)',
            r'(vacaciones?|permisos?|incapacidades?)',
            r'(días?|dias?)\s*(de\s*)?(vacaciones?|descanso|permisos?)',
            r'(quién|quien|quiénes|quienes)\s*(está|esta)\s*(de\s*)?(vacaciones?|permiso)',
            r'(solicitudes?)\s*(de)?\s*(vacaciones?|permisos?)',
        ],
        'prioridad': 10,
        'accion': 'ausencias'
    },
    
    'nomina': {
        'patrones': [
            r'(nómina|nomina|payroll)',
            r'(recibos?\s*de\s*nómina|recibos?\s*nomina)',
            r'(salarios?|sueldos?|pagos?\s*de\s*nómina)',
            r'(cuánto|cuanto)\s*(pagamos?|gastamos?)\s*(en\s*)?(nómina|sueldos?)',
            r'(dispersión|dispersion)\s*(de)?\s*(nómina|sueldos?)',
        ],
        'prioridad': 10,
        'accion': 'nomina'
    },
    
    'contratos': {
        'patrones': [
            r'(contratos?)\s*(de\s*)?(empleados?|personal|trabajo)?',
            r'(contratos?\s*)(por\s*vencer|vencidos?|vigentes?)',
            r'(vencimiento|renovación)\s*(de)?\s*contratos?',
            r'(tipos?\s*de)?\s*contratación',
        ],
        'prioridad': 10,
        'accion': 'contratos'
    },
    
    # ========== USUARIOS ==========
    'consultar_usuarios': {
        'patrones': [
            r'(usuarios?|users?)\s*(del?\s*)?(sistema|odoo)?',
            r'(cuántos?|cuantos?)\s*usuarios?',
            r'(quién|quien|quiénes|quienes)\s*(tiene[nr]?|usa[nr]?)\s*(acceso|odoo)',
            r'(accesos?|permisos?|roles?)\s*(de)?\s*usuarios?',
            r'(ver|mostrar|lista)\s*(de)?\s*usuarios?',
        ],
        'prioridad': 9,
        'accion': 'consultar_usuarios'
    },
    
    'actividad_usuarios': {
        'patrones': [
            r'(actividad|uso)\s*(de)?\s*(usuarios?|sistema)',
            r'(último|ultimo)\s*(login|acceso|conexión)',
            r'(usuarios?\s*)(activos?|inactivos?)',
            r'(quién|quien)\s*(usa|usó|accedió)\s*(el)?\s*sistema',
        ],
        'prioridad': 9,
        'accion': 'actividad_usuarios'
    },
    
    # ========== CRM ==========
    'consultar_crm': {
        'patrones': [
            r'(crm|pipeline|oportunidades?|leads?|prospectos?)',
            r'(cuántas?|cuantas?)\s*(oportunidades?|leads?)',
            r'(ver|mostrar|consultar)\s*(el)?\s*(pipeline|crm)',
            r'(etapas?|embudo)\s*(de)?\s*(ventas?|crm)',
        ],
        'prioridad': 10,
        'accion': 'consultar_crm'
    },
    
    'analisis_crm': {
        'patrones': [
            r'(análisis|analisis)\s*(de|del)?\s*(crm|pipeline|oportunidades?)',
            r'(estadísticas?|métricas?)\s*(de|del)?\s*(crm|ventas?|oportunidades?)',
            r'(conversión|conversion|tasa)\s*(de)?\s*(leads?|oportunidades?)',
            r'(valor|monto)\s*(del?)?\s*pipeline',
        ],
        'prioridad': 11,
        'accion': 'analisis_crm'
    },
    
    # ========== PROYECTOS ==========
    'consultar_proyectos': {
        'patrones': [
            r'(proyectos?)\s*(activos?|en\s*curso)?',
            r'(cuántos?|cuantos?)\s*proyectos?',
            r'(ver|mostrar|consultar)\s*(los?)?\s*proyectos?',
            r'(estado|progreso|avance)\s*(de)?\s*(proyectos?|tareas?)',
        ],
        'prioridad': 9,
        'accion': 'consultar_proyectos'
    },
    
    'tareas': {
        'patrones': [
            r'(tareas?)\s*(pendientes?|atrasadas?|vencidas?)?',
            r'(cuántas?|cuantas?)\s*tareas?',
            r'(mis|las)\s*tareas?',
            r'(asignaciones?|actividades?)\s*(pendientes?)?',
        ],
        'prioridad': 9,
        'accion': 'tareas'
    },
    
    # ========== INFORMACIÓN DEL SISTEMA ==========
    'info_sistema': {
        'patrones': [
            r'(información|info)\s*(del?)?\s*sistema',
            r'(a\s*qué|a\s*que)\s*(estoy)?\s*conectado',
            r'(datos?\s*de)\s*(conexión|conexion)',
            r'(versión|version)\s*(de|del)?\s*(odoo|sistema)',
            r'(configuración|config)\s*(del?)?\s*sistema',
        ],
        'prioridad': 8,
        'accion': 'info_sistema'
    },
    
    # ========== AYUDA Y DOCUMENTACIÓN ==========
    'explicar_modelo': {
        'patrones': [
            r'(qué\s*es|que\s*es|explica|explicar)\s*(\w+\.?\w*)',
            r'(para\s*qué|para\s*que)\s*(sirve|se\s*usa)\s*(\w+\.?\w*)',
            r'(definición|definicion)\s*(de)?\s*(\w+)',
            r'(cómo|como)\s*(funciona|trabaja)\s*(\w+)',
        ],
        'prioridad': 7,
        'accion': 'explicar_modelo'
    },
    
    'ayuda_general': {
        'patrones': [
            r'^(ayuda|help|\?)$',
            r'(qué|que)\s*(puedes?|sabes?)\s*(hacer|ayudarme)',
            r'(cómo|como)\s*(te\s*)?(uso|utilizo|funciona)',
            r'(opciones?|comandos?|funciones?)\s*(disponibles?)?',
            r'(qué|que)\s*(análisis|consultas?|reportes?)\s*(puedo|hay)',
        ],
        'prioridad': 5,
        'accion': 'ayuda'
    },

    # ============================================================
    # INTENCIONES EXTENDIDAS V2 — Nuevas Capacidades
    # ============================================================

    # ========== VENTAS v2 ==========
    'ventas_por_canal': {
        'patrones': [
            r'ventas?\s*(por|de)\s*(canal|canales?)',
            r'(web|ecommerce|marketplace|tienda\s*en\s*línea|online)\s*(vs|versus|contra)\s*(tienda|pos|físic)',
            r'(desglose|distribuci[oó]n)\s*(por)?\s*canal',
        ],
        'prioridad': 11,
        'accion': 'ventas_por_canal'
    },

    'ventas_por_categoria': {
        'patrones': [
            r'ventas?\s*(por|de)\s*(categor[ií]a|categor[ií]as|línea|familia)',
            r'(desglose|distribuci[oó]n)\s*(de\s*ventas)?\s*(por)?\s*categor[ií]a',
            r'(categor[ií]as?|familias?|l[ií]neas?)\s*(que|m[aá]s)\s*vende',
        ],
        'prioridad': 11,
        'accion': 'ventas_por_categoria'
    },

    'margen_por_producto': {
        'patrones': [
            r'(margen|rentabilidad|utilidad)\s*(por|de)\s*(producto|art[ií]culo)',
            r'productos?\s*(m[aá]s|menos)\s*(rentables?|margen)',
            r'(cu[aá]nto|cuánto)\s*(gano|ganamos)\s*(por|con)\s*(cada|producto)',
        ],
        'prioridad': 12,
        'accion': 'margen_por_producto'
    },

    'devolucion_ventas': {
        'patrones': [
            r'(devoluciones?|refund|reembolso|notas?\s*de\s*cr[eé]dito)\s*(de)?\s*ventas?',
            r'(cu[aá]ntas?)\s*(devoluciones?|notas?\s*de\s*cr[eé]dito)',
            r'(productos?|ventas?)\s*(devueltos?|devueltas?)',
            r'raz[oó]n\s*(de)?\s*(devoluci[oó]n|reembolso)',
        ],
        'prioridad': 11,
        'accion': 'devolucion_ventas'
    },

    'clientes_nuevos_vs_recurrentes': {
        'patrones': [
            r'clientes?\s*(nuevos?|recurrentes?|frecuentes?)',
            r'(nuevos?|recurrentes?)\s*(vs|versus|contra)?\s*clientes?',
            r'(cu[aá]ntos?)\s*clientes?\s*(nuevos?|primavez|primera\s*vez)',
            r'(retenci[oó]n|fidelizaci[oó]n)\s*(de)?\s*clientes?',
        ],
        'prioridad': 11,
        'accion': 'clientes_nuevos_vs_recurrentes'
    },

    'descuentos_aplicados': {
        'patrones': [
            r'(descuentos?)\s*(aplicados?|otorgados?|dados?)',
            r'(cu[aá]nto)\s*(descuento|rebaja)\s*(se\s*)?di(o|mos|eron)',
            r'(promoci[oó]n|promociones?)\s*(de)?\s*ventas?',
            r'(impacto|efecto)\s*(de)?\s*(descuentos?|promociones?)',
        ],
        'prioridad': 10,
        'accion': 'descuentos_aplicados'
    },

    'concentracion_clientes': {
        'patrones': [
            r'(concentraci[oó]n|pareto|80.?20)\s*(de)?\s*clientes?',
            r'(cu[aá]ntos?)\s*clientes?\s*(generan?|representan?)\s*(el)?\s*(80|mayor[ií]a)',
            r'(dependencia|riesgo)\s*(de)?\s*(clientes?|concentraci[oó]n)',
        ],
        'prioridad': 11,
        'accion': 'concentracion_clientes'
    },

    # ========== INVENTARIO v2 ==========
    'abc_inventario': {
        'patrones': [
            r'(clasificaci[oó]n|an[aá]lisis)\s*abc\s*(de|del)?\s*(inventario|productos?|stock)',
            r'abc\s*(inventario|productos?)',
            r'(productos?\s*)(clase|categor[ií]a)\s*(a|b|c)',
        ],
        'prioridad': 12,
        'accion': 'abc_inventario'
    },

    'inventario_obsoleto': {
        'patrones': [
            r'(inventario|productos?|stock)\s*(obsoleto|obsoletos?|sin\s*movimiento)',
            r'(productos?\s*)(que\s*no\s*se\s*mueven?|parados?|estancados?)',
            r'(cu[aá]ntos?|qu[eé])\s*(productos?)\s*(no\s*)(se\s*)?(vendieron?|movieron?)',
            r'(mercanc[ií]a|stock)\s*(viejo?|antiguo?|caduco)',
        ],
        'prioridad': 11,
        'accion': 'inventario_obsoleto'
    },

    'inventario_negativo': {
        'patrones': [
            r'(inventario|stock|productos?)\s*(negativo|negativos?)',
            r'(stock)\s*(debajo|menos)\s*(de)?\s*(cero|0)',
            r'(cantidades?\s*negativas?)',
        ],
        'prioridad': 12,
        'accion': 'inventario_negativo'
    },

    'cobertura_stock': {
        'patrones': [
            r'(cobertura|d[ií]as?\s*de\s*cobertura)\s*(de|del)?\s*(stock|inventario)',
            r'(para\s*cu[aá]ntos?\s*d[ií]as?)\s*(alcanza|me\s*alcanza)\s*(el)?\s*(inventario|stock)',
            r'(cu[aá]ntos?\s*d[ií]as?)\s*(dura|aguanta)\s*(el)?\s*stock',
        ],
        'prioridad': 11,
        'accion': 'cobertura_stock'
    },

    'merma_inventario': {
        'patrones': [
            r'(merma|mermas?|ajustes?)\s*(de|del)?\s*(inventario|stock)',
            r'(p[eé]rdida|p[eé]rdidas?)\s*(de)?\s*(inventario|productos?|stock)',
            r'(diferencias?\s*de)\s*(inventario|conteo)',
        ],
        'prioridad': 11,
        'accion': 'merma_inventario'
    },

    # ========== FINANZAS v2 ==========
    'conciliacion_bancaria': {
        'patrones': [
            r'(conciliaci[oó]n)\s*(bancaria|de\s*pagos?)',
            r'(pagos?\s*sin\s*aplicar|sin\s*conciliar)',
            r'(cruce|cuadre)\s*(de)?\s*(pagos?|facturas?)',
        ],
        'prioridad': 11,
        'accion': 'conciliacion_bancaria'
    },

    'analisis_antiguedad': {
        'patrones': [
            r'(antig[uü]edad)\s*(de)?\s*(cartera|cxc|cxp|saldos?)',
            r'(aging)\s*(report|an[aá]lisis)',
            r'(cu[aá]nto\s*tiempo)\s*(deben|llevan?\s*sin\s*pagar)',
        ],
        'prioridad': 12,
        'accion': 'analisis_antiguedad'
    },

    'estado_cuenta_cliente': {
        'patrones': [
            r'(estado\s*de\s*cuenta)\s*(de|del|para)?\s*(cliente|proveedor)?',
            r'(saldo|adeudo|deuda)\s*(de|del|para)\s*(el\s*)?cliente',
            r'(historial|movimientos?)\s*(financieros?|contables?)\s*(de|del)?\s*cliente',
        ],
        'prioridad': 11,
        'accion': 'estado_cuenta_cliente'
    },

    'dias_cobro_promedio': {
        'patrones': [
            r'(d[ií]as?\s*(de)?\s*cobro\s*promedio|dso)',
            r'(cu[aá]ntos?\s*d[ií]as?)\s*(tardamos?|nos\s*toma)\s*(en)?\s*(cobrar)',
            r'(per[ií]odo|periodo)\s*(promedio|medio)\s*(de)?\s*(cobro|cobranza)',
        ],
        'prioridad': 12,
        'accion': 'dias_cobro_promedio'
    },

    'dias_pago_promedio': {
        'patrones': [
            r'(d[ií]as?\s*(de)?\s*pago\s*promedio|dpo)',
            r'(cu[aá]ntos?\s*d[ií]as?)\s*(tardamos?|nos\s*toma)\s*(en)?\s*(pagar)',
            r'(per[ií]odo|periodo)\s*(promedio|medio)\s*(de)?\s*(pago)',
        ],
        'prioridad': 12,
        'accion': 'dias_pago_promedio'
    },

    # ========== CRM v2 ==========
    'pipeline_etapas': {
        'patrones': [
            r'(etapas?|embudo|funnel)\s*(del?)?\s*(pipeline|crm|ventas?)',
            r'(oportunidades?\s*por)\s*etapa',
            r'(en\s*qu[eé]\s*etapa)\s*(est[aá]n?|hay)',
        ],
        'prioridad': 11,
        'accion': 'pipeline_etapas'
    },

    'oportunidades_estancadas': {
        'patrones': [
            r'(oportunidades?|leads?)\s*(estancad[oa]s?|sin\s*movimiento|parad[oa]s?)',
            r'(cu[aá]les?|qu[eé])\s*(oportunidades?)\s*(no\s*)(avanzan?|mueven?)',
            r'(pipeline)\s*(detenido|parado|sin\s*avance)',
        ],
        'prioridad': 11,
        'accion': 'oportunidades_estancadas'
    },

    'win_rate': {
        'patrones': [
            r'(win\s*rate|tasa\s*de\s*cierre|tasa\s*de\s*conversi[oó]n)',
            r'(cu[aá]ntas?)\s*(oportunidades?)\s*(cerramos|ganamos?)',
            r'(porcentaje|%)\s*(de)?\s*(cierre|[eé]xito|conversi[oó]n)',
        ],
        'prioridad': 12,
        'accion': 'win_rate'
    },

    'lifetime_value': {
        'patrones': [
            r'(lifetime\s*value|ltv|valor\s*de\s*vida)',
            r'(cu[aá]nto\s*vale)\s*(un|cada)\s*cliente',
            r'(valor|ingreso)\s*(promedio|total)\s*(por|de)\s*(cliente|cada\s*cliente)',
        ],
        'prioridad': 12,
        'accion': 'lifetime_value'
    },

    # ========== COMPRAS v2 ==========
    'evaluacion_proveedores': {
        'patrones': [
            r'(evaluaci[oó]n|scorecard|calificaci[oó]n)\s*(de)?\s*proveedores?',
            r'(cu[aá]l|qu[eé])\s*(proveedor)\s*(es)?\s*(mejor|peor|cumple)',
            r'(cumplimiento|desempe[nñ]o)\s*(de)?\s*proveedores?',
        ],
        'prioridad': 11,
        'accion': 'evaluacion_proveedores'
    },

    'ordenes_pendientes': {
        'patrones': [
            r'([oó]rdenes?|pedidos?)\s*(de\s*compra\s*)?(pendientes?|por\s*recibir)',
            r'(qu[eé]|cu[aá]ntas?)\s*(compras?|[oó]rdenes?)\s*(faltan?|pendientes?)',
            r'(material|mercanc[ií]a)\s*(por\s*recibir|en\s*tr[aá]nsito)',
        ],
        'prioridad': 11,
        'accion': 'ordenes_pendientes'
    },

    'variacion_precios': {
        'patrones': [
            r'(variaci[oó]n|cambio|fluctuaci[oó]n)\s*(de|en)?\s*(precios?|costos?)',
            r'(precios?)\s*(subieron?|bajaron?|cambiaron?)',
            r'(comparar|comparativa)\s*(de)?\s*precios?\s*(de)?\s*proveedores?',
        ],
        'prioridad': 10,
        'accion': 'variacion_precios'
    },

    # ========== PDV v2 ==========
    'productividad_cajero': {
        'patrones': [
            r'(productividad|rendimiento|desempe[nñ]o)\s*(del?|por)\s*(cajero|cajer[oa]s?)',
            r'(ventas?|tickets?)\s*(por)\s*cajero',
            r'(mejor|peor|cu[aá]l)\s*cajero',
        ],
        'prioridad': 11,
        'accion': 'productividad_cajero'
    },

    'horarios_pico': {
        'patrones': [
            r'(horarios?|horas?)\s*(pico|punta|m[aá]s\s*venta)',
            r'(cu[aá]ndo|a\s*qu[eé]\s*hora)\s*(se\s*vende|hay)\s*(m[aá]s)',
            r'(picos?\s*de)\s*(venta|afluencia|tr[aá]fico)',
        ],
        'prioridad': 11,
        'accion': 'horarios_pico'
    },

    'cuadre_caja': {
        'patrones': [
            r'(cuadre|diferencias?)\s*(de)?\s*(caja|sesi[oó]n)',
            r'(faltante|sobrante)\s*(de|en)?\s*caja',
            r'(cu[aá]nto)\s*(falta|sobra)\s*(en)?\s*(la)?\s*caja',
        ],
        'prioridad': 12,
        'accion': 'cuadre_caja'
    },

    # ========== PREDICCIONES v2 ==========
    'escenarios_what_if': {
        'patrones': [
            r'(qu[eé]\s*pasa\s*si|what\s*if|escenario)',
            r'(simular|simulaci[oó]n)\s*(de)?\s*(escenario|ventas?|demanda)',
            r'(optimista|pesimista|base)\s*(escenario)?',
        ],
        'prioridad': 11,
        'accion': 'escenarios_what_if'
    },

    'alertas_predictivas': {
        'patrones': [
            r'(alertas?\s*predictiv[oa]s?|alarmas?\s*autom[aá]tic)',
            r'(avisarme|alertarme|notificarme)\s*(cuando|si)',
            r'(umbrales?|l[ií]mites?)\s*(de)?\s*(alerta|aviso)',
        ],
        'prioridad': 10,
        'accion': 'alertas_predictivas'
    },

    # ========== MATEMÁTICAS v2 ==========
    'calculo_payback': {
        'patrones': [
            r'(payback|per[ií]odo\s*de\s*recuperaci[oó]n)',
            r'(en\s*cu[aá]nto\s*tiempo)\s*(recupero|regresa)\s*(la)?\s*(inversi[oó]n)',
            r'(recuperaci[oó]n)\s*(de)?\s*(inversi[oó]n|capital)',
        ],
        'prioridad': 12,
        'accion': 'calculo_payback'
    },

    'analisis_sensibilidad': {
        'patrones': [
            r'(an[aá]lisis\s*de\s*sensibilidad)',
            r'(qu[eé]\s*pasa\s*si)\s*(cambio?|subo?|bajo?)\s*(el)?\s*(precio|costo|volumen)',
            r'(sensibilidad)\s*(al?|del?)\s*(precio|costo|volumen)',
        ],
        'prioridad': 11,
        'accion': 'analisis_sensibilidad'
    },

    'proyeccion_financiera': {
        'patrones': [
            r'(proyecci[oó]n|proyectar)\s*(financiera|de\s*ingresos)',
            r'(c[oó]mo\s*vamos?\s*a)\s*(cerrar|terminar|quedar)\s*(el)?\s*(a[nñ]o|trimestre|mes)',
            r'(estimaci[oó]n)\s*(de)?\s*(ingresos?|gastos?|utilidad)',
        ],
        'prioridad': 11,
        'accion': 'proyeccion_financiera'
    },

    # ========== ESTADÍSTICA v2 ==========
    'analisis_canasta': {
        'patrones': [
            r'(an[aá]lisis\s*de\s*canasta|market\s*basket|productos?\s*asociados?)',
            r'(qu[eé]\s*productos?)\s*(se\s*compran?|se\s*venden?)\s*(juntos?|junto)',
            r'(cross\s*selling|venta\s*cruzada|sugerencia\s*producto)',
        ],
        'prioridad': 11,
        'accion': 'analisis_canasta'
    },

    'mapa_calor': {
        'patrones': [
            r'(mapa\s*de\s*calor|heatmap)',
            r'(correlaci[oó]n)\s*(de|entre)\s*(variables?|indicadores?|m[eé]tricas?)',
            r'(relaci[oó]n\s*entre)\s*(ventas?|productos?|clientes?)',
        ],
        'prioridad': 10,
        'accion': 'mapa_calor'
    },

    'score_salud_negocio': {
        'patrones': [
            r'(score|[ií]ndice|puntuaci[oó]n)\s*(de)?\s*(salud|estado)\s*(del?)?\s*(negocio|empresa)',
            r'(c[oó]mo\s*est[aá])\s*(el|mi)?\s*(negocio|empresa)\s*(en\s*general)?',
            r'(salud\s*general|estado\s*general)\s*(del?)?\s*(negocio|empresa)',
        ],
        'prioridad': 12,
        'accion': 'score_salud_negocio'
    },

    # ========== DIAGNÓSTICO v2 ==========
    'registros_duplicados': {
        'patrones': [
            r'(registros?|datos?|clientes?|productos?)\s*(duplicados?)',
            r'(duplicados?)\s*(en|de)\s*(clientes?|productos?|contactos?)',
            r'(buscar|encontrar|detectar)\s*(duplicados?)',
        ],
        'prioridad': 11,
        'accion': 'registros_duplicados'
    },

    'consistencia_datos': {
        'patrones': [
            r'(consistencia|integridad)\s*(de)?\s*(datos?|base\s*de\s*datos?)',
            r'(verificar|revisar)\s*(la)?\s*(integridad|consistencia)',
            r'(datos?\s*inconsistentes?|registros?\s*inconsistentes?)',
        ],
        'prioridad': 11,
        'accion': 'consistencia_datos'
    },

    # ========== RRHH v2 ==========
    'brecha_salarial': {
        'patrones': [
            r'(brecha|equidad|diferencia)\s*salarial',
            r'(equidad\s*de\s*g[eé]nero|brecha\s*de\s*g[eé]nero)',
            r'(comparaci[oó]n|diferencia)\s*(de)?\s*(sueldos?|salarios?)',
        ],
        'prioridad': 11,
        'accion': 'brecha_salarial'
    },

    'vencimiento_contratos': {
        'patrones': [
            r'(contratos?\s*por\s*vencer|vencimiento\s*de\s*contratos?)',
            r'(cu[aá]les?)\s*(contratos?)\s*(vencen?|est[aá]n?\s*por\s*vencer)',
            r'(renovaci[oó]n|pr[oó]rroga)\s*(de)?\s*contratos?',
        ],
        'prioridad': 11,
        'accion': 'vencimiento_contratos'
    },

    'horas_extra': {
        'patrones': [
            r'(horas?\s*extra|overtime|tiempo\s*extra)',
            r'(cu[aá]ntas?\s*horas?\s*extra)',
            r'(qui[eé]n|quienes?)\s*(tiene|trabaja)\s*(m[aá]s)?\s*(horas?\s*extra|overtime)',
        ],
        'prioridad': 10,
        'accion': 'horas_extra'
    },

    'vacaciones_pendientes': {
        'patrones': [
            r'(vacaciones?\s*pendientes?)',
            r'(cu[aá]ntos?\s*d[ií]as?\s*de\s*vacaciones?)\s*(quedan?|tienen?|faltan?)',
            r'(qui[eé]n|quienes?)\s*(no\s*ha\s*tomado|tiene)\s*vacaciones?',
        ],
        'prioridad': 10,
        'accion': 'vacaciones_pendientes'
    },
}


def obtener_todas_las_intenciones():
    """Devuelve todas las intenciones extendidas."""
    return INTENCIONES_EXTENDIDAS


def obtener_accion_sugerida(texto: str) -> str:
    """
    Dado un texto, sugiere la acción más probable.
    Útil para autocompletado.
    """
    import re
    texto_lower = texto.lower()
    
    # Buscar la mejor coincidencia
    mejor_match = None
    mejor_prioridad = 0
    
    for nombre, config in INTENCIONES_EXTENDIDAS.items():
        for patron in config['patrones']:
            if re.search(patron, texto_lower):
                if config['prioridad'] > mejor_prioridad:
                    mejor_match = config['accion']
                    mejor_prioridad = config['prioridad']
    
    return mejor_match or 'desconocido'
