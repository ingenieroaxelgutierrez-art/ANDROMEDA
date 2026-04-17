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
        ],
        'prioridad': 11,
        'accion': 'tendencia'
    },

    'proyeccion_ventas': {
        'patrones': [
            r'(proyecci[oó]n|proyectar|forecast)\s*(de)?\s*ventas?',
            r'(ventas?|ingresos?)\s*(para\s*)?(los?\s*pr[oó]ximos?|siguientes?|en\s*los?)\s*\d*\s*(d[ií]as?|semanas?|meses?)',
            r'(cu[aá]nto\s*(se\s*va\s*a|vamos?\s*a)\s*vender|predicci[oó]n\s*de\s*ventas?)',
            r'(estima(r|ci[oó]n)|anticipa(r|ci[oó]n))\s*(de)?\s*(ventas?|ingresos?)',
            r'(gr[aá]fica?\s*)?(la\s*)?(proyecci[oó]n|forecast|predicci[oó]n)\s*(de\s*ventas?)?\s*(para\s*)?(pr[oó]ximos?)',
        ],
        'prioridad': 13,
        'accion': 'proyeccion_ventas'
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

    'ventas_por_marca': {
        'patrones': [
            r'ventas?\s*(por|de|de\s*cada)\s*(marca|fabricante|brand)',
            r'(marca|fabricante|brand)\s*(y|,)?\s*(ventas?|ingresos?|montos?)',
            r'(cu[aá]nto\s*(vende|vendemos?|se\s*vende))\s*(cada|por)\s*(marca|fabricante)',
            r'(an[aá]lisis|desglose|resumen|reporte)\s*(de\s*)?ventas?\s*(por|de)\s*(marca|fabricante)',
            r'(ranking|top)\s*(de\s*)?(marcas?|fabricantes?)\s*(en\s*)?(ventas?|ingresos?)?',
            r'(semana|mes|d[ií]a|a[nñ]o)\s*(por|de)\s*(marca|fabricante)',
            r'(marca|fabricante)\s*(de\s*(la\s*)?semana|del\s*mes|del\s*a[nñ]o)',
        ],
        'prioridad': 16,
        'accion': 'ventas_por_marca'
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
        'prioridad': 12,
        'accion': 'vacaciones_pendientes'
    },

    # ─── VENTAS v2 ────────────────────────────────────────────────────────────

    'meta_cumplimiento': {
        'patrones': [
            r'(cumplimiento|logro|avance)\s*(de\s*)?(meta|objetivo|cuota)',
            r'(meta|objetivo|cuota)\s*(de\s*ventas?)?\s*(cumplida?|alcanzada?|lograda?)',
            r'cu[aá]nto\s*(del?\s*)?(objetivo|meta|cuota)\s*(se\s*ha?\s*)?(cumplido|logrado|alcanzado)',
            r'(porcentaje|%)?\s*(de\s*)?(avance|cumplimiento)\s*(del?\s*)?(objetivo|meta)',
        ],
        'prioridad': 11,
        'accion': 'meta_cumplimiento'
    },

    'ventas_por_hora': {
        'patrones': [
            r'(ventas?|ingresos?)\s*por\s*hora',
            r'(a\s*qu[eé]\s*hora|en\s*qu[eé]\s*horario)\s*(se\s*vende?\s*m[aá]s|hay\s*m[aá]s\s*ventas?)',
            r'(pico|hora\s*pico|mejor\s*hora|peor\s*hora)\s*(de\s*ventas?|de\s*afluencia)',
            r'distribuci[oó]n\s*(de\s*ventas?)?\s*por\s*hora',
        ],
        'prioridad': 11,
        'accion': 'ventas_por_hora'
    },

    'ventas_vs_anterior': {
        'patrones': [
            r'(ventas?|ingresos?)\s*(vs\.?|versus|comparad[ao]s?\s*a?l?)\s*(periodo|mes|a[nñ]o|semana)?\s*anterior',
            r'(crecimiento|variaci[oó]n|cambio)\s*(en\s*ventas?|de\s*ventas?)',
            r'(cu[aá]nto\s*(crecieron?|cayeron?|bajaron?|subieron?))\s*las?\s*ventas?',
            r'(m[aá]s|menos)\s*ventas?\s*(que\s*el)?\s*(mes|a[nñ]o|periodo)\s*pasado',
        ],
        'prioridad': 10,
        'accion': 'ventas_vs_anterior'
    },

    # ─── INVENTARIO v2 ────────────────────────────────────────────────────────

    'costo_almacenamiento': {
        'patrones': [
            r'(costo|coste)\s*(de\s*)?(almacenamiento|bodega|almac[eé]n|warehousing)',
            r'(cu[aá]nto\s*cuesta|cuestan?)\s*(guardar|almacenar|tener\s*en\s*bodega)',
            r'gasto\s*de\s*(bodega|almac[eé]n|almacenamiento)',
        ],
        'prioridad': 11,
        'accion': 'costo_almacenamiento'
    },

    'trazabilidad_lote': {
        'patrones': [
            r'(trazabilidad|rastrear|seguimiento)\s*(de\s*)?(lote|lot[es]?|n[uú]mero\s*de\s*lote)',
            r'(lote|n[uú]mero\s*lote|lot)\s*(n[uú]mero|#)?\s*\w*',
            r'(d[oó]nde\s*(est[aá]|fueron?)|en\s*qu[eé])\s*(almac[eé]n|bodega|ubicaci[oó]n)\s*(est[aá]|se\s*encuentra)\s*(el\s*lote|lote)',
        ],
        'prioridad': 11,
        'accion': 'trazabilidad_lote'
    },

    'inventario_por_categoria': {
        'patrones': [
            r'(inventario|stock|existencias?)\s*por\s*(categor[ií]a|familia|tipo)',
            r'(existencias?|productos?)\s*(de\s*la\s*categor[ií]a|en\s*la\s*categor[ií]a)',
            r'(desglose|detalle|resumen)\s*(de\s*inventario|de\s*stock)\s*por\s*categor[ií]a',
        ],
        'prioridad': 10,
        'accion': 'inventario_por_categoria'
    },

    'transferencias_pendientes': {
        'patrones': [
            r'(transferencias?|traspasos?)\s*pendientes?',
            r'(movimientos?\s*de\s*stock|transferencias?\s*de\s*inventario)\s*pendientes?',
            r'(qu[eé]|cu[aá]ntas?)\s*(transferencias?|traspasos?)\s*(no\s*(se\s*han?\s*)?(procesado|completado|recibido))',
        ],
        'prioridad': 11,
        'accion': 'transferencias_pendientes'
    },

    'inventario_valorizado_categoria': {
        'patrones': [
            r'(valor|valorizaci[oó]n)\s*(del?\s*inventario|de\s*stock)\s*por\s*(categor[ií]a|familia)',
            r'(inventario\s*valorizado|stock\s*valorizado)\s*por\s*(categor[ií]a|familia)',
            r'(cu[aá]nto\s*vale|valor\s*total)\s*(el|del?)\s*(inventario|stock)\s*(por\s*categor[ií]a|de\s*(cada|por)\s*categor[ií]a)',
        ],
        'prioridad': 11,
        'accion': 'inventario_valorizado_categoria'
    },

    'inventario_por_almacen': {
        'patrones': [
            r'(inventario|stock|existencias?)\s*por\s*(almac[eé]n|bodega|ubicaci[oó]n)',
            r'(cu[aá]nto\s*(hay|tenemos?|existe)\s*en\s*(cada|el)?\s*(almac[eé]n|bodega))',
            r'(desglose|distribuci[oó]n|resumen)\s*(de\s*(inventario|stock))\s*por\s*(almac[eé]n|bodega)',
            r'(inventario\s*por\s*sucursal|stock\s*por\s*sucursal)',
            r'(qu[eé]\s*tiene[n]?\s*en\s*)(almac[eé]n|bodega)',
        ],
        'prioridad': 12,
        'accion': 'inventario_por_almacen'
    },

    'inventario_por_empresa': {
        'patrones': [
            r'(inventario|stock|existencias?)\s*por\s*(empresa|compa[ñn][ií]a)',
            r'(cu[aá]nto\s*(hay|tenemos?|existe)\s*en\s*(cada|la)\s*(empresa|compa[ñn][ií]a))',
            r'(desglose|distribuci[oó]n|resumen)\s*(de\s*(inventario|stock))\s*por\s*(empresa|compa[ñn][ií]a)',
            r'(inventario\s*por\s*empresa|stock\s*por\s*empresa)',
        ],
        'prioridad': 12,
        'accion': 'inventario_por_empresa'
    },

    'comparar_stock_fisico_sistema': {
        'patrones': [
            r'(stock|inventario)\s*(f[ií]sico|real)\s*(vs\.?|versus|comparado\s*con)\s*(sistema|odoo)',
            r'(diferencias?|discrepancias?)\s*(entre\s*)?(inventario|stock)\s*(f[ií]sico|real)\s*(y\s*el?\s*sistema)?',
            r'(comparar|reconciliar)\s*(inventario|stock)\s*(f[ií]sico|del?\s*conteo)',
            r'(conteo\s*f[ií]sico|inventario\s*f[ií]sico)\s*(vs\.?|contra)',
        ],
        'prioridad': 12,
        'accion': 'comparar_stock_fisico_sistema'
    },

    # ─── FINANZAS v2 ──────────────────────────────────────────────────────────

    'notas_credito': {
        'patrones': [
            r'(notas?\s*de?\s*cr[eé]dito|nota\s*cr[eé]dito)',
            r'(cu[aá]ntas?|listado\s*de|ver)\s*notas?\s*(de\s*)?cr[eé]dito',
            r'(abono|descuento|devoluci[oó]n)\s*(en\s*)?factura',
        ],
        'prioridad': 11,
        'accion': 'notas_credito'
    },

    'impuestos_resumen': {
        'patrones': [
            r'(resumen\s*de\s*impuestos?|declaraci[oó]n\s*de\s*impuestos?)',
            r'(iva|isr|impuestos?)\s*(del?\s*periodo|del?\s*mes|del?\s*a[nñ]o|a\s*pagar|retenido)',
            r'(cu[aá]nto\s*(es|debo|pago|pagamos?)\s*(de\s*)?(iva|isr|impuesto))',
            r'(reporte|c[aá]lculo)\s*(fiscal|de\s*impuestos?)',
        ],
        'prioridad': 11,
        'accion': 'impuestos_resumen'
    },

    'margen_operativo': {
        'patrones': [
            r'(margen\s*operativo|margen\s*de\s*operaci[oó]n|utilidad\s*operativa)',
            r'(ebitda|ebit|resultado\s*operativo)',
            r'(beneficio|ganancia)\s*operativ[ao]',
        ],
        'prioridad': 11,
        'accion': 'margen_operativo'
    },

    'razon_liquidez': {
        'patrones': [
            r'(raz[oó]n|ratio|[ií]ndice)\s*(de\s*)?liquidez',
            r'(current\s*ratio|quick\s*ratio|acid\s*test)',
            r'(capacidad\s*de\s*pago|liquidez\s*de\s*la\s*empresa)',
            r'(activo|pasivo)\s*circulante',
        ],
        'prioridad': 11,
        'accion': 'razon_liquidez'
    },

    'capital_trabajo': {
        'patrones': [
            r'(capital\s*de\s*trabajo|capital\s*circulante|working\s*capital)',
            r'(necesidades?\s*de\s*capital|capital\s*operativo)',
            r'(activos?\s*corrientes?\s*menos\s*pasivos?\s*corrientes?)',
        ],
        'prioridad': 11,
        'accion': 'capital_trabajo'
    },

    'pagos_pendientes_aplicar': {
        'patrones': [
            r'(pagos?\s*(pendientes?\s*de\s*aplicar|sin\s*aplicar|no\s*aplicados?))',
            r'(abonos?\s*(pendientes?\s*de\s*aplicar|sin\s*aplicar))',
            r'(pagos?\s*sin\s*conciliar|pagos?\s*sin\s*asignar)',
        ],
        'prioridad': 12,
        'accion': 'pagos_pendientes_aplicar'
    },

    'estado_cuenta_proveedor': {
        'patrones': [
            r'(estado\s*de\s*cuenta|saldo|balance)\s*(del?\s*)?(proveedor|supplier)',
            r'(cu[aá]nto\s*(le\s*debemos?|adeudamos?)\s*a(l?\s*proveedor)?)',
            r'(cuenta\s*corriente|historial\s*de\s*pagos?)\s*(del?\s*proveedor)',
        ],
        'prioridad': 11,
        'accion': 'estado_cuenta_proveedor'
    },

    # ─── CRM v2 ───────────────────────────────────────────────────────────────

    'conversion_leads': {
        'patrones': [
            r'(conversi[oó]n|tasa\s*de\s*conversi[oó]n)\s*(de\s*leads?|de\s*prospectos?)',
            r'(leads?\s*convertidos?|prospectos?\s*cerrados?)',
            r'(cu[aá]ntos?\s*leads?\s*(se\s*)?(convirtieron?|cerraron?|se\s*volvieron?\s*clientes?))',
            r'(eficiencia|efectividad)\s*(de\s*(conversi[oó]n|ventas?|cierre))',
        ],
        'prioridad': 13,
        'accion': 'conversion_leads'
    },

    'actividades_pendientes': {
        'patrones': [
            r'(actividades?\s*pendientes?|tareas?\s*pendientes?)\s*(crm|de\s*seguimiento|de\s*ventas?)?',
            r'(llamadas?|correos?|reuniones?|visitas?)\s*pendientes?',
            r'(qu[eé]\s*(actividades?|tareas?|acciones?)\s*(tengo|hay)\s*(pendientes?|por\s*hacer))',
        ],
        'prioridad': 10,
        'accion': 'actividades_pendientes'
    },

    'tiempo_cierre_promedio': {
        'patrones': [
            r'(tiempo|d[ií]as?|semanas?)\s*(promedio\s*)?(de\s*)?(cierre|ciclo\s*de\s*venta)',
            r'(ciclo\s*de\s*venta|sales\s*cycle)',
            r'(cu[aá]nto\s*(tarda|demora|toman?))\s*(en\s*)?(cerrar|vender)',
        ],
        'prioridad': 11,
        'accion': 'tiempo_cierre_promedio'
    },

    'leads_por_origen': {
        'patrones': [
            r'(leads?|prospectos?)\s*por\s*(origen|fuente|canal|source)',
            r'(de\s*d[oó]nde\s*(vienen?|provienen?|llegan?))\s*(los?\s*leads?|prospectos?)',
            r'(fuente|origen|canal)\s*(de\s*leads?|de\s*prospectos?|de\s*captaci[oó]n)',
        ],
        'prioridad': 11,
        'accion': 'leads_por_origen'
    },

    'clientes_por_etapa': {
        'patrones': [
            r'(clientes?|oportunidades?)\s*por\s*(etapa|fase|stage)',
            r'(pipeline|embudo\s*de\s*ventas?)\s*(por\s*etapa)?',
            r'(en\s*qu[eé]\s*etapa\s*(est[aá]n?|hay|tengo))\s*(los?\s*clientes?|las?\s*oportunidades?)',
        ],
        'prioridad': 10,
        'accion': 'clientes_por_etapa'
    },

    'reactivacion_clientes': {
        'patrones': [
            r'(reactivar|recuperar)\s*(clientes?|cuentas?)',
            r'(clientes?\s*(inactivos?|perdidos?|dormidos?|que\s*no\s*(compran?|han\s*comprado)))',
            r'(cu[aá]ntos?\s*clientes?\s*(no\s*(han\s*comprado|compraron))\s*(en\s*\d+\s*(d[ií]as?|meses?|a[nñ]os?)))',
        ],
        'prioridad': 11,
        'accion': 'reactivacion_clientes'
    },

    # ─── COMPRAS v2 ───────────────────────────────────────────────────────────

    'comparativa_precios': {
        'patrones': [
            r'(comparar|comparativa|cotizaci[oó]n\s*comparada?)\s*(de\s*precios?|entre\s*proveedores?)',
            r'(mejor\s*precio|precio\s*m[aá]s\s*bajo|proveedor\s*m[aá]s\s*barato)',
            r'(qu[eé]\s*proveedor\s*(ofrece|tiene|da)\s*mejor\s*precio)',
            r'(an[aá]lisis|comparaci[oó]n)\s*de\s*precios?\s*de\s*proveedores?',
        ],
        'prioridad': 11,
        'accion': 'comparativa_precios'
    },

    'cumplimiento_entregas': {
        'patrones': [
            r'(cumplimiento|puntualidad)\s*(de\s*)?(entregas?|pedidos?)',
            r'(entregas?\s*(a\s*tiempo|puntual(es)?|tard[ií]as?))',
            r'(proveedor(es)?\s*(que\s*)?(entrega[n]?\s*tarde|cumple[n]?\s*con\s*fechas?))',
        ],
        'prioridad': 11,
        'accion': 'cumplimiento_entregas'
    },

    'compras_por_categoria': {
        'patrones': [
            r'(compras?|gastos?\s*de\s*compras?)\s*por\s*(categor[ií]a|familia|tipo)',
            r'(desglose|detalle|resumen)\s*de\s*compras?\s*por\s*(categor[ií]a|familia)',
        ],
        'prioridad': 10,
        'accion': 'compras_por_categoria'
    },

    'compras_recurrentes': {
        'patrones': [
            r'(compras?\s*recurrentes?|[oó]rdenes?\s*repetidas?|pedidos?\s*frecuentes?)',
            r'(productos?\s*(que\s*siempre|que\s*frecuentemente)\s*(compramos?|pedimos?))',
            r'(frecuencia\s*de\s*compra|periodicidad\s*de\s*compras?)',
        ],
        'prioridad': 10,
        'accion': 'compras_recurrentes'
    },

    'ahorro_potencial': {
        'patrones': [
            r'(ahorro\s*potencial|oportunidades?\s*de\s*ahorro)',
            r'(reducir|bajar|optimizar)\s*(costos?\s*de\s*compras?|gasto\s*en\s*compras?)',
            r'(d[oó]nde\s*(podemos?|se\s*puede)\s*(ahorrar|reducir\s*costos?))',
        ],
        'prioridad': 11,
        'accion': 'ahorro_potencial'
    },

    'compras_urgentes': {
        'patrones': [
            r'(compras?\s*urgentes?|[oó]rdenes?\s*urgentes?|pedidos?\s*(urgentes?|de\s*emergencia))',
            r'(qu[eé]\s*(hay|tenemos?)\s*(que\s*comprar|de\s*comprar)\s*(urgente|ya|r[aá]pido))',
        ],
        'prioridad': 12,
        'accion': 'compras_urgentes'
    },

    'gasto_por_departamento': {
        'patrones': [
            r'(gasto|compras?|presupuesto)\s*por\s*(departamento|[aá]rea|secci[oó]n)',
            r'(cu[aá]nto\s*(gasta|compra)\s*(cada|el)?\s*departamento)',
            r'(desglose|distribuci[oó]n)\s*(de\s*(gastos?|compras?))\s*por\s*departamento',
        ],
        'prioridad': 10,
        'accion': 'gasto_por_departamento'
    },

    # ─── PDV v2 ───────────────────────────────────────────────────────────────

    'devoluciones_pos': {
        'patrones': [
            r'(devoluciones?|reembolsos?|refund)\s*(en\s*caja|pos|punto\s*de\s*venta)',
            r'(productos?\s*devueltos?)\s*(en\s*caja|en\s*pos)',
            r'(cu[aá]ntas?\s*devoluciones?)\s*(hay|hubo|se\s*hicieron?)\s*(en\s*(pos|caja))?',
        ],
        'prioridad': 11,
        'accion': 'devoluciones_pos'
    },

    'descuentos_por_tienda': {
        'patrones': [
            r'descuentos?\s*(realizados?|aplicados?|otorgados?)?\s*por\s*(tiendas?|sucursales?|locales?)',
            r'descuentos?\s*(realizados?|aplicados?|dados?)\s*(en\s*)?(tiendas?|sucursales?)',
            r'(p[eé]rdida|impacto|efecto)\s*(de)?\s*utilidad\s*(por|de|en)\s*(descuentos?|promociones?)',
            r'descuentos?\s*(y|,)\s*(p[eé]rdida|impacto|efecto)\s*(de)?\s*utilidad',
            r'(cu[aá]nto\s*(se\s*perdi[oó]|perdimos?))\s*(en|por)\s*descuentos?',
            r'(resumen|reporte|an[aá]lisis)\s*(de)?\s*descuentos?\s*(por|en)\s*(tiendas?|sucursales?)',
        ],
        'prioridad': 15,
        'accion': 'descuentos_por_tienda'
    },

    'descuentos_pos': {
        'patrones': [
            r'(descuentos?|promociones?)\s*(en\s*caja|pos|punto\s*de\s*venta|aplicados?\s*en\s*pos)',
            r'(cu[aá]nto\s*(se\s*descont[oó]|se\s*descontaron?|se\s*dio\s*de\s*descuento))\s*(en\s*(caja|pos))?',
        ],
        'prioridad': 11,
        'accion': 'descuentos_pos'
    },

    'ventas_diarias_por_tienda': {
        'patrones': [
            r'ventas?\s*(diarias?|por\s*d[ií]a)\s*(por\s*)?(tienda|sucursal|local|pos)',
            r'(tienda|sucursal|local|pos)\s*(y\s*)?(gr[aá]fica?|comportamiento|evoluci[oó]n)\s*(diario|por\s*d[ií]a)',
            r'comportamiento\s*(diario|por\s*d[ií]a)\s*(por\s*)?(tienda|sucursal|pos)',
            r'gr[aá]fica?\s*(el?\s*)?(comportamiento|evoluci[oó]n)\s*(diario|de\s*ventas?)\s*(por\s*)?(tienda|sucursal)',
            r'(evoluci[oó]n|tendencia)\s*(diaria|por\s*d[ií]a)\s*(de\s*ventas?)?\s*(por\s*)?(tienda|sucursal)',
            r'(d[ií]a\s*a\s*d[ií]a|diariamente)\s*(por\s*)?(tienda|sucursal|pos)',
        ],
        'prioridad': 14,
        'accion': 'ventas_diarias_por_tienda'
    },

    'pos_por_sucursal': {
        'patrones': [
            r'(ventas?\s*pos|caja)\s*por\s*(sucursal|tienda|local)',
            r'(comparar|rendimiento)\s*(sucursales?|tiendas?)\s*(en\s*pos|en\s*caja)',
            r'(qu[eé]\s*sucursal|qu[eé]\s*tienda)\s*(vende?\s*m[aá]s|tiene\s*mejor\s*rendimiento)\s*(en\s*pos)?',
        ],
        'prioridad': 11,
        'accion': 'pos_por_sucursal'
    },

    'ticket_detalle': {
        'patrones': [
            r'(detalle|ver|consultar|buscar)\s*(el?\s*ticket|la?\s*venta)\s*#?\s*\d+',
            r'(ticket|recibo|comprobante)\s*(de\s*venta)?\s*n[uú]mero\s*\d+',
            r'(ver\s*ticket|abrir\s*ticket|mostrar\s*ticket)',
        ],
        'prioridad': 12,
        'accion': 'ticket_detalle'
    },

    'productos_mas_vendidos_pos': {
        'patrones': [
            r'(m[aá]s\s*vendidos?|top\s*productos?)\s*(en\s*(caja|pos|punto\s*de\s*venta))',
            r'(productos?\s*(que\s*m[aá]s\s*se\s*venden?|con\s*mayor\s*rotaci[oó]n))\s*(en\s*(pos|caja))?',
        ],
        'prioridad': 11,
        'accion': 'productos_mas_vendidos_pos'
    },

    'merma_pos': {
        'patrones': [
            r'(merma|p[eé]rdida|diferencia)\s*(en\s*(caja|pos|punto\s*de\s*venta))',
            r'(diferencias?\s*de\s*caja|faltante\s*en\s*caja)',
        ],
        'prioridad': 12,
        'accion': 'merma_pos'
    },

    'rendimiento_terminal': {
        'patrones': [
            r'(rendimiento|performance|desempe[nñ]o)\s*(de\s*)?(terminal|caja\s*registradora|punto\s*de\s*venta)',
            r'(terminal(es)?\s*(m[aá]s\s*activa|con\s*m[aá]s\s*ventas?|m[aá]s\s*r[aá]pida))',
        ],
        'prioridad': 11,
        'accion': 'rendimiento_terminal'
    },

    'ventas_pos_vs_ecommerce': {
        'patrones': [
            r'(pos|tienda\s*f[ií]sica|canal\s*f[ií]sico)\s*(vs\.?|versus|comparad[ao]\s*con)\s*(ecommerce|tienda\s*online|web)',
            r'(comparar|an[aá]lisis)\s*(ventas?\s*)?(canal\s*f[ií]sico|pos)\s*(y|vs\.?)\s*(online|digital|ecommerce)',
            r'(cu[aá]nto\s*vende)\s*(la\s*tienda\s*f[ií]sica|el\s*pos)\s*(vs\.?|comparado\s*con)\s*(online|web)',
        ],
        'prioridad': 12,
        'accion': 'ventas_pos_vs_ecommerce'
    },

    # ─── RRHH v2 ──────────────────────────────────────────────────────────────

    'costo_rotacion': {
        'patrones': [
            r'(costo\s*(de\s*)?rotaci[oó]n|coste\s*(de\s*)?rotaci[oó]n)',
            r'(cu[aá]nto\s*cuesta\s*(contratar|reemplazar|cambiar)\s*(un\s*empleado|personal))',
            r'(costo\s*(de\s*contrataci[oó]n|de\s*despido|de\s*reemplazo))',
        ],
        'prioridad': 11,
        'accion': 'costo_rotacion'
    },

    'clima_organizacional': {
        'patrones': [
            r'(clima\s*organizacional|ambiente\s*laboral|satisfacci[oó]n\s*(de\s*)?(empleados?|trabajadores?))',
            r'(cultura\s*(organizacional|empresarial)|bienestar\s*(laboral|del\s*empleado))',
            r'(encuesta\s*(de\s*clima|de\s*satisfacci[oó]n)\s*(laboral|organizacional)?)',
        ],
        'prioridad': 10,
        'accion': 'clima_organizacional'
    },

    'cumplimiento_jornada': {
        'patrones': [
            r'(cumplimiento\s*(de\s*)?jornada|asistencia\s*(de\s*)?(empleados?|personal))',
            r'(horas?\s*trabajadas?|horas?\s*de\s*trabajo|jornada\s*laboral)',
            r'(puntualidad|tardanzas?|llegadas?\s*tarde|inasistencias?)',
        ],
        'prioridad': 10,
        'accion': 'cumplimiento_jornada'
    },

    'estructura_organizacional': {
        'patrones': [
            r'(organigrama|estructura\s*(organizacional|de\s*la\s*empresa|jer[aá]rquica))',
            r'(jerarqu[ií]a|niveles?\s*(jer[aá]rquicos?|organizacionales?))',
            r'(qui[eé]n\s*(reporta\s*a|depende\s*de))',
        ],
        'prioridad': 10,
        'accion': 'estructura_organizacional'
    },

    'incapacidades': {
        'patrones': [
            r'(incapacidades?|bajas?\s*m[eé]dicas?|ausencias?\s*por\s*enfermedad)',
            r'(empleados?\s*(de\s*baja|incapacitados?|enfermos?))',
            r'(cu[aá]ntos?\s*(d[ií]as?|horas?)\s*(de\s*)?(incapacidad|baja\s*m[eé]dica))',
        ],
        'prioridad': 11,
        'accion': 'incapacidades'
    },

    'prestaciones_resumen': {
        'patrones': [
            r'(prestaciones?|beneficios?\s*(de\s*)?(empleados?|laborales?))',
            r'(resumen\s*(de\s*)?prestaciones?|detalle\s*(de\s*)?prestaciones?)',
            r'(aguinaldo|prima\s*vacacional|seguro\s*(de\s*vida|m[eé]dico)|fondo\s*de\s*ahorro)',
        ],
        'prioridad': 10,
        'accion': 'prestaciones_resumen'
    },

    # ─── DIAGNÓSTICO v2 ───────────────────────────────────────────────────────

    'validacion_cruzada': {
        'patrones': [
            r'(validaci[oó]n\s*cruzada|cruzar\s*datos?)',
            r'(consistencia\s*entre\s*(m[oó]dulos?|[aá]reas?)|datos?\s*(cruzados?|inconsistentes?\s*entre))',
            r'(comparar|cruzar)\s*(informaci[oó]n|datos?)\s*(entre\s*m[oó]dulos?)',
        ],
        'prioridad': 12,
        'accion': 'validacion_cruzada'
    },

    'reconciliacion_stock_contable': {
        'patrones': [
            r'(reconciliaci[oó]n|conciliar)\s*(stock|inventario)\s*(con\s*)?(contabilidad|contable|libros)',
            r'(diferencias?\s*(entre|de))\s*(inventario|stock)\s*(y\s*contabilidad|contable)',
            r'(stock\s*contable\s*vs\.?\s*f[ií]sico|inventario\s*vs\.?\s*contable)',
        ],
        'prioridad': 12,
        'accion': 'reconciliacion_stock_contable'
    },

    'integridad_referencial': {
        'patrones': [
            r'(integridad\s*referencial|referencias?\s*rotas?|datos?\s*(hu[eé]rfanos?|sin\s*referencia))',
            r'(registros?\s*(sin\s*(padre|referencia)|hu[eé]rfanos?))',
            r'(foreign\s*key|clave\s*for[aá]nea)\s*(rota|inv[aá]lida)',
        ],
        'prioridad': 12,
        'accion': 'integridad_referencial'
    },

    'secuencias_rotas': {
        'patrones': [
            r'(secuencias?\s*(rotas?|interrumpidas?|faltantes?))',
            r'(brechas?\s*en\s*(numeraci[oó]n|secuencia))',
            r'(n[uú]meros?\s*(de\s*facturas?|de\s*pedidos?|de\s*documentos?)\s*(faltantes?|que\s*faltan?))',
        ],
        'prioridad': 12,
        'accion': 'secuencias_rotas'
    },

    'configuraciones_riesgosas': {
        'patrones': [
            r'(configuraciones?\s*(riesgosas?|peligrosas?|inseguras?|de\s*riesgo))',
            r'(seguridad\s*(de\s*configuraci[oó]n|del\s*sistema))',
            r'(configuraciones?\s*(que\s*(representan?|son)\s*(un\s*)?(riesgo|peligro)))',
        ],
        'prioridad': 12,
        'accion': 'configuraciones_riesgosas'
    },

    'accesos_inusuales': {
        'patrones': [
            r'(accesos?\s*(inusuales?|sospechosos?|no\s*autorizados?|extra[nñ]os?))',
            r'(actividad\s*(sospechosa|inusual|an[oó]mala)\s*(de\s*)?(usuarios?|sesiones?))',
            r'(intentos?\s*(de\s*)?(acceso|inicio\s*de\s*sesi[oó]n)\s*(fallidos?|rechazados?))',
        ],
        'prioridad': 12,
        'accion': 'accesos_inusuales'
    },

    'operaciones_masivas': {
        'patrones': [
            r'(operaciones?\s*(masivas?|en\s*lote|bulk))',
            r'(cambios?\s*(masivos?|en\s*lote|bulk))',
            r'(modificaciones?\s*masivas?|actualizaciones?\s*masivas?)',
            r'(eliminaciones?\s*masivas?|borrados?\s*(masivos?|en\s*lote))',
        ],
        'prioridad': 12,
        'accion': 'operaciones_masivas'
    },

    # ─── ODOO v2 ──────────────────────────────────────────────────────────────

    'relaciones_modelo': {
        'patrones': [
            r'(relaciones?\s*(del?\s*modelo|entre\s*modelos?)|campos?\s*relacionados?)',
            r'(c[oó]mo\s*(se\s*relacionan?|est[aá]n?\s*relacionados?)\s*(los?\s*modelos?|las?\s*tablas?))',
            r'(estructura\s*(del?\s*modelo|de\s*la\s*base\s*de\s*datos?))',
        ],
        'prioridad': 11,
        'accion': 'relaciones_modelo'
    },

    'flujo_trabajo_modelo': {
        'patrones': [
            r'(flujo\s*de\s*trabajo|workflow|flujo\s*de\s*estados?)\s*(del?\s*modelo)?',
            r'(estados?\s*(del?\s*modelo|disponibles?|posibles?))',
            r'(c[oó]mo\s*(cambia[n]?|transiciona[n]?|fluyen?)\s*(los?\s*estados?|el\s*workflow))',
        ],
        'prioridad': 11,
        'accion': 'flujo_trabajo_modelo'
    },

    'permisos_usuario': {
        'patrones': [
            r'(permisos?\s*(del?\s*usuario|de\s*acceso)|accesos?\s*(del?\s*usuario))',
            r'(qu[eé]\s*(puede\s*hacer|tiene\s*acceso|permisos?\s*tiene)\s*(el\s*usuario|el\s*rol))',
            r'(roles?\s*y\s*permisos?|derechos?\s*de\s*acceso)',
        ],
        'prioridad': 11,
        'accion': 'permisos_usuario'
    },

    'log_acciones_usuario': {
        'patrones': [
            r'(log\s*(de\s*)?(acciones?|actividad)|historial\s*(de\s*)?(acciones?|actividad))\s*(del?\s*usuario)?',
            r'(qu[eé]\s*(hizo|realiz[oó]|modific[oó])\s*(el\s*usuario|\w+))',
            r'(audit[oó]log|chatter|mensajes?\s*de\s*seguimiento)',
        ],
        'prioridad': 11,
        'accion': 'log_acciones_usuario'
    },

    'modulos_instalados': {
        'patrones': [
            r'(m[oó]dulos?\s*(instalados?|activos?|habilitados?))',
            r'(addons?\s*(instalados?|activos?)|aplicaciones?\s*instaladas?)',
            r'(qu[eé]\s*m[oó]dulos?\s*(hay|tenemos?|est[aá]n?\s*instalados?))',
        ],
        'prioridad': 11,
        'accion': 'modulos_instalados'
    },

    'ir_cron_activos': {
        'patrones': [
            r'(tareas?\s*programadas?|cron\s*(activos?|jobs?)|procesos?\s*(autom[aá]ticos?|programados?))',
            r'(ir\.cron|scheduled\s*actions?|acciones?\s*programadas?)',
            r'(qu[eé]\s*(tareas?|procesos?)\s*(se\s*ejecutan?\s*autom[aá]ticamente|est[aá]n?\s*programados?))',
        ],
        'prioridad': 11,
        'accion': 'ir_cron_activos'
    },

    'parametros_sistema': {
        'patrones': [
            r'(par[aá]metros?\s*(del?\s*sistema|t[eé]cnicos?|de\s*configuraci[oó]n))',
            r'(configuraci[oó]n\s*(del?\s*sistema|t[eé]cnica|de\s*odoo))',
            r'(ir\.config\.parameter|par[aá]metros?\s*del?\s*sistema)',
        ],
        'prioridad': 11,
        'accion': 'parametros_sistema'
    },

    'mostrar_capacidades': {
        'patrones': [
            r'(qu[eé]\s*(puedes?\s*hacer|sabes?\s*hacer|funciones?\s*(tienes?|hay)|capacidades?\s*(tienes?|hay)))',
            r'(funciones?\s*disponibles?|capacidades?\s*del?\s*(bot|asistente))',
            r'(para\s*qu[eé]\s*(sirves?|eres?\s*[uú]til|puedo\s*usarte))',
            r'(listado\s*de\s*(funciones?|capacidades?|comandos?))',
        ],
        'prioridad': 10,
        'accion': 'mostrar_capacidades'
    },

    'generar_pdf_profesional': {
        'patrones': [
            r'(generar|exportar|crear|descargar)\s*(reporte|informe)?\s*pdf',
            r'(reporte|informe)\s*(en\s*pdf|formato\s*pdf)',
            r'(pdf\s*(del?\s*reporte|del?\s*informe|de\s*ventas?|de\s*inventario))',
        ],
        'prioridad': 10,
        'accion': 'generar_pdf_profesional'
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
