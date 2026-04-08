"""
Fix truncated methods in ejecutor_acciones.py
The refactoring script cut off f-strings, causing 8 methods to bleed into each other.
This script:
1. Keeps lines 1-1271 (intact: _ejecutar_accion + _generar_tendencia)
2. Rewrites lines 1272-1622 (8 broken methods) with proper implementations
3. Keeps lines 1623-1740 (intact: _ejecutar_consulta_avanzada_v2 + _respuesta_accion_no_disponible)
"""

import os

filepath = os.path.join(os.path.dirname(__file__), '..', 'services', 'actions', 'ejecutor_acciones.py')
filepath = os.path.abspath(filepath)

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Find the exact boundary lines
# Part 1: lines 0..1270 (1-indexed 1..1271) = good code (up to _generar_tendencia return)
# Part 3: from 'def _ejecutar_consulta_avanzada_v2' to end = good code

# Find line index for _ejecutar_consulta_avanzada_v2
avanzada_idx = None
for i, line in enumerate(lines):
    if '    def _ejecutar_consulta_avanzada_v2(' in line:
        avanzada_idx = i
        break

if avanzada_idx is None:
    print("ERROR: Could not find _ejecutar_consulta_avanzada_v2")
    exit(1)

print(f"_ejecutar_consulta_avanzada_v2 starts at line {avanzada_idx + 1}")

# Part 1: everything up to and including _generar_tendencia (line 1271 = index 1270)
part1 = lines[:1271]

# Part 3: from _ejecutar_consulta_avanzada_v2 to end
part3 = lines[avanzada_idx:]

# Part 2: reconstructed methods with proper f-strings
part2 = '''\

    def _generar_kpis_por_tienda(self, fecha_ini: str, fecha_fin: str) -> str:
        """Genera KPIs desglosados por tienda/sucursal."""
        try:
            # Obtener datos de POS por tienda
            pos_data = self._bot.odoo.buscar(
                'pos.order',
                filtro=[
                    ('date_order', '>=', fecha_ini),
                    ('date_order', '<=', fecha_fin),
                    ('state', 'in', ['paid', 'done', 'invoiced'])
                ],
                campos=['id', 'name', 'amount_total', 'session_id', 'config_id', 'date_order', 'partner_id'],
                limite=5000
            )

            if pos_data.empty:
                return "No hay datos de punto de venta en el período seleccionado."

            # Extraer nombre de tienda del config_id
            pos_data['tienda'] = pos_data['config_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else 'Sin Tienda'
            )

            # Agrupar por tienda
            kpis_tienda = pos_data.groupby('tienda').agg({
                'amount_total': ['sum', 'mean', 'count'],
                'id': 'count'
            }).reset_index()
            kpis_tienda.columns = ['Tienda', 'Ventas_Total', 'Ticket_Promedio', 'Transacciones', 'Ordenes']
            kpis_tienda = kpis_tienda.sort_values('Ventas_Total', ascending=False)

            total_general = kpis_tienda['Ventas_Total'].sum()

            # Construir tabla markdown
            header = (
                f"## KPIs por Tienda/Sucursal\\n\\n"
                f"### Período: {fecha_ini} a {fecha_fin}\\n\\n"
                f"| # | Tienda | Total Ventas | Ticket Promedio | Transacciones | % Participación |\\n"
                f"|---|--------|-------------|-----------------|---------------|-----------------|\\n"
            )
            rows = ""
            for i, row in enumerate(kpis_tienda.itertuples(), 1):
                pct = (row.Ventas_Total / total_general * 100) if total_general > 0 else 0
                rows += (
                    f"| {i} | {row.Tienda} "
                    f"| ${row.Ventas_Total:,.2f} "
                    f"| ${row.Ticket_Promedio:,.2f} "
                    f"| {row.Transacciones:,.0f} "
                    f"| {pct:.1f}% |\\n"
                )

            footer = (
                f"\\n| **Total** | **{len(kpis_tienda)} tiendas** "
                f"| **${total_general:,.2f}** | | | |\\n\\n"
            )

            # Insights
            mejor = kpis_tienda.iloc[0] if len(kpis_tienda) > 0 else None
            insights = ""
            if mejor is not None:
                insights = (
                    f"### 💡 Insights\\n"
                    f"- **Mejor tienda:** {mejor['Tienda']} "
                    f"(${mejor['Ventas_Total']:,.2f})\\n"
                    f"- **Total tiendas activas:** {len(kpis_tienda)}\\n"
                )

            return header + rows + footer + insights

        except Exception as e:
            return f"Error al generar KPIs por tienda: {str(e)}"

    def _consultar_facturas_filtradas(self, consulta, fecha_ini: str, fecha_fin: str) -> tuple:
        """Consulta facturas con filtros avanzados (estado, tienda, cliente)."""
        try:
            filtros = [
                ('invoice_date', '>=', fecha_ini),
                ('invoice_date', '<=', fecha_fin),
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ]

            # Extraer filtros de las entidades del cerebro
            estado_factura = None
            tienda_filtro = None

            for ent in self._bot._obtener_entidades_cerebro(consulta):
                if hasattr(ent, 'tipo'):
                    if ent.tipo == 'estado_factura':
                        estado_factura = ent.valor
                    elif ent.tipo == 'tienda':
                        tienda_filtro = ent.valor

            # También buscar en parámetros
            if consulta.parametros:
                estado_factura = estado_factura or consulta.parametros.get('estado')
                tienda_filtro = tienda_filtro or consulta.parametros.get('tienda')

            # Aplicar filtro de estado
            if estado_factura == 'pendiente':
                filtros.append(('amount_residual', '>', 0))
                filtros.append(('payment_state', 'in', ['not_paid', 'partial']))
            elif estado_factura == 'pagada':
                filtros.append(('payment_state', '=', 'paid'))

            # Obtener facturas con campo de journal (diario contable que indica tienda)
            facturas = self._bot.odoo.buscar(
                'account.move',
                filtro=filtros,
                campos=['id', 'name', 'partner_id', 'invoice_date', 'amount_total',
                        'amount_residual', 'payment_state', 'state', 'invoice_user_id', 'journal_id'],
                limite=500
            )

            if facturas.empty:
                return "No se encontraron facturas con los filtros especificados.", None

            # Limpiar campos many2one
            facturas['Cliente'] = facturas['partner_id'].apply(
                lambda x: x[1][:35] if isinstance(x, (list, tuple)) and len(x) > 1 else 'Sin Cliente'
            )

            # Extraer nombre del diario (tienda)
            facturas['Diario'] = facturas['journal_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else ''
            )

            # Extraer nombre del vendedor
            facturas['Vendedor'] = facturas['invoice_user_id'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else ''
            )

            # Filtrar por tienda si se especificó
            if tienda_filtro:
                tienda_normalizada = tienda_filtro.lower().strip()

                variantes_tienda = [tienda_normalizada]
                if tienda_normalizada == 'moral':
                    variantes_tienda.extend(['la moral', 'moral', 'pos moral', 'pdv moral', 'tienda moral', 'premium.*moral'])
                elif tienda_normalizada == 'aeropuerto':
                    variantes_tienda.extend(['aero', 'pos aeropuerto', 'pdv aeropuerto', 'premium.*aero'])
                elif tienda_normalizada == 'centro':
                    variantes_tienda.extend(['centro', 'pos centro', 'pdv centro', 'tienda centro', 'premium.*centro'])

                pattern = '|'.join(variantes_tienda)
                mask = (
                    facturas['Diario'].str.lower().str.contains(pattern, na=False, regex=True) |
                    facturas['Cliente'].str.lower().str.contains(pattern, na=False, regex=True) |
                    facturas['Vendedor'].str.lower().str.contains(pattern, na=False, regex=True)
                )
                facturas_filtradas = facturas[mask]

                if facturas_filtradas.empty:
                    diarios_unicos = facturas['Diario'].unique().tolist()
                    diarios_str = ", ".join([d for d in diarios_unicos if d])[:200]

                    msg = f"No se encontraron facturas para la tienda '{tienda_filtro}'.\\n\\n"
                    msg += f"**Diarios disponibles:** {diarios_str}\\n\\n"
                    msg += f"**Nota:** Las facturas de cliente no suelen tener información de tienda/sucursal. "
                    msg += f"Para ver ventas por tienda, usa mejor: \\"**ventas de {tienda_filtro}**\\" o \\"**pos de {tienda_filtro}**\\""
                    return msg, None

                facturas = facturas_filtradas

            # Calcular totales
            total_facturas = len(facturas)
            monto_total = facturas['amount_total'].sum()
            saldo_pendiente = facturas['amount_residual'].sum()

            titulo_estado = ""
            if estado_factura == 'pendiente':
                titulo_estado = " Pendientes de Pago"
            elif estado_factura == 'pagada':
                titulo_estado = " Pagadas"

            titulo_tienda = f" - {tienda_filtro}" if tienda_filtro else ""

            md = (
                f"## Facturas{titulo_estado}{titulo_tienda}\\n\\n"
                f"**Período:** {fecha_ini} a {fecha_fin}\\n"
                f"**Total facturas:** {total_facturas}\\n"
                f"**Monto total:** ${monto_total:,.2f}\\n"
                f"**Saldo pendiente:** ${saldo_pendiente:,.2f}\\n\\n"
            )

            # Crear DataFrame limpio para la tabla
            df_display = facturas[['name', 'Cliente', 'invoice_date', 'amount_total', 'amount_residual', 'payment_state']].copy()
            df_display.columns = ['Factura', 'Cliente', 'Fecha', 'Monto', 'Saldo', 'Estado Pago']

            return md, df_display

        except Exception as e:
            return f"Error al consultar facturas: {str(e)}", None

    def _generar_reporte(self, formato: str) -> str:
        if self._bot.ultimo_df is None or self._bot.ultimo_df.empty:
            return "No hay datos. Primero consulta algo."

        archivo = self._bot.reportes.generar_reporte(
            {self._bot.ultimo_modelo or 'Datos': self._bot.ultimo_df},
            "Reporte",
            formato
        )
        return f"## Reporte Generado\\n\\n**{formato.upper()}**: `{archivo}`"

    def _generar_pdf_profesional(self, contexto: str = "") -> str:
        """Genera un PDF profesional con ReportLab."""
        if not self._bot.generador_pdf_reportlab:
            return "El generador de PDFs profesionales no está disponible. Instala reportlab."

        try:
            from services.reports import SeccionReporte, ConfiguracionReporte

            secciones = []

            # Si hay datos en el último DataFrame, incluirlos
            if self._bot.ultimo_df is not None and not self._bot.ultimo_df.empty:
                datos_tabla = self._bot.ultimo_df.head(50).values.tolist()
                encabezados = list(self._bot.ultimo_df.columns)

                secciones.append(SeccionReporte(
                    titulo="Datos Analizados",
                    contenido=datos_tabla,
                    tipo='tabla',
                    metadata={'encabezados': encabezados}
                ))

            # Si hay auditoría disponible, generar resumen
            if self._bot.auditoria and hasattr(self._bot.auditoria, 'ejecutar_auditoria_express'):
                try:
                    resultado_auditoria = self._bot.auditoria.ejecutar_auditoria_express()
                    if resultado_auditoria and 'metricas' in resultado_auditoria:
                        secciones.append(SeccionReporte(
                            titulo="Resumen de Auditoría",
                            contenido=resultado_auditoria.get('metricas', {}),
                            tipo='resumen_ejecutivo'
                        ))
                except Exception:
                    pass

            if not secciones:
                return "No hay datos para generar el PDF. Primero realiza una consulta o análisis."

            # Generar el PDF
            config = ConfiguracionReporte(
                titulo="Reporte Ejecutivo ANDROMEDA",
                subtitulo=contexto[:100] if contexto else "Análisis de Datos Empresariales",
                empresa=os.getenv("ODOO_EMPRESA", "Mi Empresa")
            )

            exito, ruta = self._bot.generador_pdf_reportlab.generar_reporte(secciones, config=config)

            if exito:
                return (
                    f"## PDF Profesional Generado\\n\\n"
                    f"**Archivo:** `{ruta}`\\n\\n"
                    f"El reporte incluye {len(secciones)} sección(es) con datos actualizados."
                )
            else:
                return "Error al generar el PDF. Verifica que reportlab esté instalado correctamente."

        except Exception as e:
            return f"Error generando PDF: {str(e)}"

    def _ejecutar_consulta_dinamica(self, pregunta: str, parametros: dict = None) -> tuple:
        """Ejecuta una consulta dinámica generada por el LLM."""
        if not self._bot.generador_queries:
            return "El generador de queries no está disponible.", None

        try:
            # Si hay parámetros específicos del LLM, usar directamente
            if parametros and 'modelo' in parametros and 'dominio' in parametros:
                from services.llm.generador_queries import QueryOdoo
                query = QueryOdoo(
                    modelo=parametros['modelo'],
                    dominio=parametros.get('dominio', []),
                    campos=parametros.get('campos', ['name', 'id']),
                    limite=parametros.get('limite', 50),
                    orden=parametros.get('orden'),
                    descripcion=pregunta
                )
                resultado = self._bot.generador_queries.ejecutar_query(query)
            else:
                resultado = self._bot.generador_queries.procesar_pregunta(pregunta)

            if not resultado.exito:
                return f"Error en consulta: {resultado.error}", None

            if not resultado.datos:
                return "No se encontraron datos para esta consulta.", None

            # Crear DataFrame con los resultados
            df = pd.DataFrame(resultado.datos)
            self._bot.ultimo_df = df

            # Interpretar resultados con el LLM si está disponible
            interpretacion = self._bot.generador_queries.interpretar_resultados(resultado, pregunta)

            respuesta = (
                f"## Consulta Dinámica\\n\\n"
                f"**Pregunta:** {pregunta}\\n"
                f"**Registros encontrados:** {len(df)}\\n\\n"
            )
            if interpretacion:
                respuesta += f"**Análisis:** {interpretacion}\\n"

            return respuesta, df

        except Exception as e:
            return f"Error en consulta dinámica: {str(e)}", None

    def _contar_chiste(self) -> str:
        """Cuenta un chiste relacionado con datos y negocios."""
        import random
        chistes = [
            "## ¡Un chiste para ti!\\n\\n¿Por qué el contador siempre lleva una calculadora? ¡Por si las facturas no cuadran! 📊😄",
            "## ¡Un chiste para ti!\\n\\n¿Qué le dijo Excel a la base de datos? 'Tú sí que tienes buenos registros' 💻😂",
            "## ¡Un chiste para ti!\\n\\n¿Por qué los datos en Odoo nunca se pierden? ¡Porque tienen buenos respaldos! 🔄😜",
            "## ¡Un chiste para ti!\\n\\n¿Qué le dice un ERP a otro? '¿Módulos este fin de semana?' 🤓",
            "## ¡Un chiste para ti!\\n\\nMi función favorita es SUM... porque siempre suma al equipo 📈",
            "## ¡Un chiste para ti!\\n\\n¿Por qué el inventario fue al psicólogo? Tenía problemas de stock emocional 📦😅",
            "## ¡Un chiste para ti!\\n\\nUn cliente entra en la tienda y pregunta: '¿Tienen facturas?' El sistema responde: '¿Las quiere timbradas o sin timbrar?' 🧾",
            "## ¡Un chiste para ti!\\n\\n¿Cuál es el colmo de un analista de datos? Tener una vida sin gráficas 📊",
            "## ¡Un chiste para ti!\\n\\n¿Por qué el dashboard estaba triste? Porque nadie lo consultaba 📉😢",
            "## ¡Un chiste para ti!\\n\\n¿Qué hace un KPI cuando se siente solo? Se compara con el mes anterior 📈"
        ]
        return random.choice(chistes) + "\\n\\n💡 **¿En qué más puedo ayudarte?** Pregúntame sobre ventas, inventario, clientes..."

    def _mostrar_capacidades(self) -> str:
        """Muestra un resumen de las capacidades del sistema."""
        return (
            "## 🌌 Soy ANDROMEDA - Tu Asistente de Inteligencia de Negocios\\n\\n"
            "**Consultas de datos:**\\n"
            "- 📊 Ventas, facturación, ingresos\\n"
            "- 📦 Inventario y stock\\n"
            "- 👥 Clientes y proveedores\\n"
            "- 🏪 Punto de Venta (POS)\\n\\n"
            "**Análisis avanzado:**\\n"
            "- 📈 Tendencias y predicciones\\n"
            "- 🎯 KPIs empresariales\\n"
            "- 🔍 Detección de anomalías\\n"
            "- 💡 Insights automáticos\\n\\n"
            "**Reportes:**\\n"
            "- 📄 PDF profesionales\\n"
            "- 📊 Gráficas interactivas\\n"
            "- 📋 Excel y CSV\\n\\n"
            "**Pregúntame lo que necesites en lenguaje natural.**"
        )

    def _responder_despedida(self) -> str:
        """Responde a una despedida con calidez."""
        import random
        despedidas = [
            "## 👋 ¡Hasta luego campeón!\\n\\nFue un placer analizar datos contigo. Cuando vuelvas, aquí estaré. ¡Éxito en todo! 🌟💪",
            "## 👋 ¡Nos vemos!\\n\\nGracias por confiar en ANDROMEDA. Que tus negocios vayan al 100%. Cualquier consulta, aquí ando. 🚀",
            "## 👋 ¡Hasta pronto!\\n\\nFue genial ayudarte. Recuerda: cuando necesites analizar, predecir o entender tus datos, cuento conmigo. 😊📊",
            "## 👋 ¡Chao!\\n\\n¡Acabas de ver el poder del análisis inteligente! Vuelve pronto para descubrir más insights. Nos vemos, campeón. 🔥✨"
        ]
        return random.choice(despedidas)

    def _responder_agradecimiento(self) -> str:
        """Responde a un agradecimiento con empatía y humor."""
        import random
        respuestas = [
            "## 🙌 ¡Para ti!\\n\\n¡Ese es mi trabajo, hacer que los datos hablen! 📊 ¿Hay algo más que quieras saber sobre tu negocio?",
            "## 😊 ¡Con todo el gusto!\\n\\nPara eso estoy aquí, para darte insights que de verdad importen. ¿Otra pregunta? 💡",
            "## ✨ ¡Claro que sí!\\n\\nSi hay algo que me encanta es desbloquear el potencial de tus datos. ¿Qué más te atormenta analizando? 😄📈",
            "## 🌟 ¡Para servirte!\\n\\nEstoy aquí para hacer tu vida más fácil. ¿Seguimos descubriendo cosas increíbles sobre tu negocio? 🚀"
        ]
        return random.choice(respuestas)

    def _responder_saludo(self) -> str:
        """Responde a un saludo con empatía y calidez."""
        import random
        from datetime import datetime

        hora = datetime.now().hour
        if hora < 12:
            momento = "Buenos días"
        elif hora < 19:
            momento = "Buenas tardes"
        else:
            momento = "Buenas noches"

        respuestas = [
            f"## 👋 ¡{momento}!\\n\\n¡Qué onda! Aquí estoy para ayudarte con todo lo que necesites sobre tu negocio. 😊\\n\\n💡 **Puedo ayudarte con:**\\n- 📊 Análisis de ventas y tendencias\\n- 🎯 Predicciones y pronósticos\\n- 📈 KPIs y métricas clave\\n- 🔍 Anomalías y oportunidades\\n\\n**¿Qué necesitas ahora?**",
            f"## 🌟 ¡Hola!\\n\\n¡Me encanta verte por aquí! 😄 Soy ANDROMEDA, tu compañero de análisis de negocios.\\n\\nEsto es lo que puedo hacer por ti:\\n- 💰 Consultas sobre ventas, ingresos y rentabilidad\\n- 📦 Información de inventario y stock\\n- 👥 Análisis de clientes y comportamientos\\n- 🎲 Predicciones inteligentes basadas en datos\\n\\n**¿Por dónde empezamos?**",
            f"## 🚀 ¡{momento}!\\n\\n¡Bienvenido! Aquí estoy para hacer tus análisis mucho más fáciles y útiles. 💪\\n\\nSin complicaciones, solo preguntas naturales como:\\n- \\"¿Cómo vamos con las ventas?\\"\\n- \\"Top 10 productos esta semana\\"\\n- \\"¿Hay clientes en riesgo?\\"\\n- \\"Grafica mi inventario por categoría\\"\\n\\n**¿Con qué te ayudo?**",
            f"## 😊 ¡{momento}!\\n\\n¡Qué bueno que estés aquí! Aquí va mi magia de análisis para tu negocio.\\n\\nPuedo hacer de todo:\\n✅ Reportes instantáneos\\n✅ Gráficas espectaculares\\n✅ Predicciones inteligentes\\n✅ Alertas de problemas\\n✅ 10+ idiomas disponibles\\n\\n**¿Qué consultamos primero?**"
        ]
        return random.choice(respuestas)

    def _ventas_tienda_especifica(self, tienda: str, fecha_ini: str, fecha_fin: str) -> str:
        """Consulta ventas de una tienda/unidad operativa específica."""
        try:
            # Buscar el warehouse/operating unit que coincida
            warehouses = self._bot.odoo.search_read('stock.warehouse',
                [('name', 'ilike', tienda)],
                campos=['id', 'name', 'code']
            )

            if not warehouses:
                try:
                    ous = self._bot.odoo.search_read('operating.unit',
                        [('name', 'ilike', tienda)],
                        campos=['id', 'name', 'code']
                    )
                    if ous:
                        warehouses = ous
                except Exception:
                    pass

            if not warehouses:
                return (
                    f"## Tienda no encontrada\\n\\n"
                    f"No se encontró una tienda con el nombre **{tienda}**.\\n\\n"
                    f"Intenta con el nombre exacto o usa **\\"ventas por tienda\\"** para ver todas."
                )

            # Obtener ventas de POS para la tienda
            pos_data = self._bot.odoo.buscar(
                'pos.order',
                filtro=[
                    ('date_order', '>=', fecha_ini),
                    ('date_order', '<=', fecha_fin),
                    ('state', 'in', ['paid', 'done', 'invoiced']),
                    ('config_id.name', 'ilike', tienda)
                ],
                campos=['id', 'name', 'amount_total', 'date_order', 'partner_id'],
                limite=1000
            )

            if pos_data.empty:
                return f"No se encontraron ventas para **{tienda}** en el período {fecha_ini} a {fecha_fin}."

            total = pos_data['amount_total'].sum()
            ticket_prom = pos_data['amount_total'].mean()
            n_ventas = len(pos_data)

            return (
                f"## Ventas de {tienda}\\n\\n"
                f"**Período:** {fecha_ini} a {fecha_fin}\\n"
                f"**Total ventas:** ${total:,.2f}\\n"
                f"**Ticket promedio:** ${ticket_prom:,.2f}\\n"
                f"**Transacciones:** {n_ventas:,}\\n"
            )

        except Exception as e:
            return f"Error al consultar ventas de {tienda}: {str(e)}"

    def _generar_ayuda_completa(self) -> str:
        return (
            "## 🌌 ANDROMEDA - Capacidades\\n\\n"
            "**Consultas:**\\n"
            "- Ventas, facturas, inventario, clientes, productos\\n"
            "- KPIs por tienda, marca, vendedor\\n"
            "- Estados de cuenta y cobranza\\n\\n"
            "**Análisis:**\\n"
            "- Tendencias y predicciones\\n"
            "- Detección de anomalías\\n"
            "- Análisis 360° de negocio\\n\\n"
            "**Reportes:**\\n"
            "- PDF profesionales\\n"
            "- Gráficas y dashboards\\n"
            "- Excel y CSV\\n\\n"
            "**Solo pregunta en lenguaje natural.**"
        )

    def _info_conexion(self) -> str:
        url = getattr(self._bot, 'odoo_url', 'N/D')
        db = getattr(self._bot, 'odoo_db', 'N/D')
        user = getattr(self._bot, 'odoo_user', 'N/D')
        conectado = "Sí ✅" if getattr(self._bot, 'conector', None) else "No ❌"
        return (
            f"## 🔗 Información del Sistema\\n\\n"
            f"**URL Odoo:** {url}\\n"
            f"**Base de datos:** {db}\\n"
            f"**Usuario:** {user}\\n"
            f"**Conectado:** {conectado}\\n"
        )

'''

# Write the new file
with open(filepath, 'w', encoding='utf-8') as f:
    # Part 1: original good code
    f.writelines(part1)
    # Part 2: reconstructed methods
    f.write(part2)
    # Part 3: original good tail
    f.writelines(part3)

# Verify
with open(filepath, 'r', encoding='utf-8') as f:
    new_lines = f.readlines()
print(f"New total lines: {len(new_lines)}")
print("Done!")
