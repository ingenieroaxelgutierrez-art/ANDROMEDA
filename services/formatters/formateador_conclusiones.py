# ============================================================
# ANDROMEDA - Formateador de Conclusiones
# ============================================================
# Estructura conversacional para respuestas del agente:
#   1. Reconocimiento  → "He analizado los datos de X..."
#   2. Datos           → Tablas, métricas (existente)
#   3. Insight Humano  → "Llama la atención que..."
#   4. Cierre          → "¿Quieres que genere el Excel/PDF...?"
# ============================================================


class FormateadorConclusiones:
    """Envuelve respuestas con estructura conversacional humanizada."""

    # Nombres de dominio por idioma: clave → (es, en, ja)
    _DOMINIOS_I18N: dict = {
        'venta':                  ('ventas',                         'sales',                         '売上'),
        'top_producto':           ('productos más vendidos',         'best-selling products',         '売れ筋商品'),
        'top_cliente':            ('mejores clientes',               'top customers',                 '優良顧客'),
        'top_vendedor':           ('mejores vendedores',             'top sales reps',                '優秀な営業担当'),
        'inventario':             ('inventario',                     'inventory',                     '在庫'),
        'stock':                  ('stock',                          'stock',                         '在庫'),
        'producto_critico':       ('productos críticos',             'critical products',             '重要商品'),
        'reorden':                ('puntos de reorden',              'reorder points',                '発注点'),
        'rotacion_inv':           ('rotación de inventario',         'inventory turnover',            '在庫回転率'),
        'financ':                 ('finanzas',                       'finance',                       '財務'),
        'cxc':                    ('cuentas por cobrar',             'accounts receivable',           '売掛金'),
        'cxp':                    ('cuentas por pagar',              'accounts payable',              '買掛金'),
        'flujo':                  ('flujo de caja',                  'cash flow',                     'キャッシュフロー'),
        'factur':                 ('facturación',                    'invoicing',                     '請求'),
        'compra':                 ('compras',                        'purchases',                     '購買'),
        'crm':                    ('CRM',                            'CRM',                           'CRM'),
        'lead':                   ('leads y pipeline',               'leads & pipeline',              'リード＆パイプライン'),
        'rrhh':                   ('recursos humanos',               'HR',                            '人事'),
        'nomina':                 ('nómina',                         'payroll',                       '給与'),
        'pos':                    ('punto de venta',                 'point of sale',                 'POS'),
        'prediccion':             ('predicciones',                   'predictions',                   '予測'),
        'forecast':               ('proyecciones',                   'projections',                   '見込み'),
        'agotamiento':            ('agotamiento de inventario',      'stock depletion',               '在庫切れ予測'),
        'auditoria':              ('auditoría',                      'audit',                         '監査'),
        'anomalia':               ('anomalías',                      'anomalies',                     '異常'),
        'kpi':                    ('indicadores clave',              'key indicators',                '主要指標'),
        'estadistic':             ('análisis estadístico',           'statistical analysis',          '統計分析'),
        '360':                    ('análisis integral',              'comprehensive analysis',        '総合分析'),
        'cliente':                ('clientes',                       'customers',                     '顧客'),
        'proveedor':              ('proveedores',                    'suppliers',                     '仕入先'),
        'morosi':                 ('morosidad',                      'delinquency',                   '延滞'),
        'margen':                 ('márgenes',                       'margins',                       '利益率'),
        'rentab':                 ('rentabilidad',                   'profitability',                 '収益性'),
        'rotacion':               ('rotación',                       'turnover',                      '回転率'),
        'tendencia':              ('tendencias',                     'trends',                        'トレンド'),
        'comparativ':             ('comparativa',                    'comparison',                    '比較'),
        'salud':                  ('salud del negocio',              'business health',               '事業健全性'),
        'churn':                  ('riesgo de fuga de clientes',     'customer churn risk',           '顧客離脱リスク'),
        'segmentacion':           ('segmentación de clientes',       'customer segmentation',         '顧客セグメント'),
        'pareto':                 ('análisis Pareto',                'Pareto analysis',               'パレート分析'),
        'rfm':                    ('análisis RFM',                   'RFM analysis',                  'RFM分析'),
        'estacionalidad':         ('estacionalidad',                 'seasonality',                   '季節性'),
        'merma':                  ('mermas',                         'shrinkage',                     '損耗'),
        'abc':                    ('clasificación ABC',              'ABC classification',            'ABC分類'),
        # RRHH v2
        'rotacion_personal':      ('rotación de personal',           'staff turnover',                '人員離職率'),
        'clima_organ':            ('clima organizacional',           'organizational climate',        '組織風土'),
        'clima':                  ('clima organizacional',           'organizational climate',        '組織風土'),
        'brecha_sal':             ('brecha salarial',                'pay gap',                       '賃金格差'),
        'brecha':                 ('brecha salarial',                'pay gap',                       '賃金格差'),
        'horas_extra':            ('horas extra',                    'overtime',                      '残業'),
        'vacacion':               ('vacaciones',                     'vacation',                      '休暇'),
        'incapacid':              ('incapacidades',                  'sick leave',                    '病欠'),
        'prestacion':             ('prestaciones laborales',         'employee benefits',             '福利厚生'),
        'cumplimiento_jornada':   ('jornada laboral',                'work schedule',                 '労働時間'),
        'jornada':                ('jornada laboral',                'work schedule',                 '労働時間'),
        'estructura_organ':       ('estructura organizacional',      'org structure',                 '組織構造'),
        'organigrama':            ('organigrama',                    'org chart',                     '組織図'),
        'costo_rotacion':         ('costo de rotación',             'turnover cost',                 '離職コスト'),
        # Inventario v2
        'inventario_obsoleto':    ('inventario obsoleto',            'obsolete inventory',            '陳腐化在庫'),
        'obsoleto':               ('inventario obsoleto',            'obsolete inventory',            '陳腐化在庫'),
        'inventario_por_almacen': ('inventario por almacén',        'inventory by warehouse',        '倉庫別在庫'),
        'almacen':                ('inventario por almacén',        'inventory by warehouse',        '倉庫別在庫'),
        'trazabilidad':           ('trazabilidad de lotes',          'lot traceability',              'ロット追跡'),
        'lote':                   ('trazabilidad de lotes',          'lot traceability',              'ロット追跡'),
        'cobertura_stock':        ('cobertura de stock',             'stock coverage',                '在庫カバレッジ'),
        'inventario_negativo':    ('stock negativo',                 'negative stock',                'マイナス在庫'),
        'transferencia':          ('transferencias',                 'transfers',                     '移送'),
        'costo_almacenamiento':   ('costo de almacenamiento',       'storage cost',                  '保管コスト'),
        'comparar_stock':         ('comparativa stock físico vs sistema', 'physical vs system stock', '実地vs帳簿在庫'),
        # Finanzas v2
        'notas_credito':          ('notas de crédito',              'credit notes',                  'クレジットメモ'),
        'impuesto':               ('impuestos',                      'taxes',                         '税金'),
        'margen_operativo':       ('margen operativo',               'operating margin',              '営業利益率'),
        'razon_liquidez':         ('liquidez',                       'liquidity',                     '流動性'),
        'liquidez':               ('liquidez',                       'liquidity',                     '流動性'),
        'capital_trabajo':        ('capital de trabajo',             'working capital',               '運転資本'),
        'pagos_pendientes':       ('pagos pendientes',               'pending payments',              '未払い'),
        'estado_cuenta':          ('estado de cuenta',               'account statement',             '口座明細'),
        'conciliacion':           ('conciliación bancaria',          'bank reconciliation',           '銀行照合'),
        'antiguedad':             ('antigüedad de saldos',           'aging of balances',             '残高エイジング'),
        # CRM v2
        'conversion_lead':        ('conversión de leads',            'lead conversion',               'リード転換'),
        'actividades_pendientes': ('actividades pendientes',         'pending activities',            '未処理活動'),
        'oportunidades':          ('oportunidades CRM',              'CRM opportunities',             'CRM商談'),
        'win_rate':               ('tasa de cierre',                 'win rate',                      '成約率'),
        'lifetime_value':         ('valor de vida del cliente',      'customer lifetime value',       '顧客生涯価値'),
        'reactivacion':           ('reactivación de clientes',       'customer reactivation',         '顧客再活性化'),
        # Compras v2
        'compras_recurrentes':    ('compras recurrentes',            'recurring purchases',           '定期購買'),
        'comparativa_precios':    ('comparativa de precios',         'price comparison',              '価格比較'),
        'cumplimiento_entregas':  ('cumplimiento de entregas',       'delivery compliance',           '納期遵守'),
        'ahorro_potencial':       ('ahorro potencial',               'potential savings',             '節約可能額'),
        'compras_urgentes':       ('compras urgentes',               'urgent purchases',              '緊急購買'),
        'gasto_por_departamento': ('gasto por departamento',         'spend by department',           '部門別支出'),
        # PDV v2
        'descuentos_pos':         ('descuentos en POS',              'POS discounts',                 'POS割引'),
        'devoluciones_pos':       ('devoluciones en POS',            'POS returns',                   'POS返品'),
        'cuadre_caja':            ('cuadre de caja',                 'cash reconciliation',           'キャッシュ照合'),
        'pos_por_sucursal':       ('POS por sucursal',               'POS by branch',                 '支店別POS'),
        'ticket_detalle':         ('detalle de ticket',              'ticket detail',                 'チケット明細'),
        'rendimiento_terminal':   ('rendimiento de terminal',        'terminal performance',          '端末パフォーマンス'),
        'ventas_pos_vs':          ('POS vs e-commerce',              'POS vs e-commerce',             'POS vs Eコマース'),
        # Diagnóstico v2
        'validacion_cruzada':     ('validación cruzada',             'cross-validation',              'クロスバリデーション'),
        'consistencia':           ('consistencia de datos',          'data consistency',              'データ整合性'),
        'registros_duplicados':   ('registros duplicados',           'duplicate records',             '重複レコード'),
        'reconciliacion':         ('reconciliación contable',        'accounting reconciliation',     '会計照合'),
        'integridad':             ('integridad de datos',            'data integrity',                'データ完全性'),
        'secuencias_rotas':       ('secuencias rotas',               'broken sequences',              '連番欠番'),
        'configuraciones_riesgosas': ('configuraciones de riesgo',   'risky configurations',          'リスク設定'),
        'accesos_inusuales':      ('accesos inusuales',              'unusual access',                '異常アクセス'),
        'operaciones_masivas':    ('operaciones masivas',            'bulk operations',               '一括操作'),
        # Odoo/Sistema v2
        'relaciones_modelo':      ('relaciones de modelo Odoo',      'Odoo model relations',          'Odooモデル関係'),
        'flujo_trabajo':          ('flujo de trabajo Odoo',          'Odoo workflow',                 'Odooワークフロー'),
        'permisos_usuario':       ('permisos de usuario',            'user permissions',              'ユーザー権限'),
        'log_acciones':           ('log de acciones',                'action log',                    'アクションログ'),
        'modulos_instalados':     ('módulos instalados',             'installed modules',             'インストール済みモジュール'),
        'ir_cron':                ('tareas programadas',             'scheduled tasks',               'スケジュールタスク'),
        'parametros_sistema':     ('parámetros del sistema',         'system parameters',             'システムパラメータ'),
        'capacidades':            ('capacidades del asistente',      'assistant capabilities',        'アシスタント機能'),
        'generar_pdf':            ('generación de PDF',              'PDF generation',                'PDF生成'),
        'generar_excel':          ('generación de Excel',            'Excel generation',              'Excel生成'),
    }

    # Tabla de lookup plana por idioma (generada en tiempo de clase)
    @classmethod
    def _dominio_por_idioma(cls, clave: str, idioma: str) -> str:
        entry = cls._DOMINIOS_I18N.get(clave)
        if entry is None:
            return clave
        idx = {'es': 0, 'en': 1, 'ja': 2}.get(idioma, 0)
        return entry[idx]

    # Backward compat: acceso a _DOMINIOS como dict español (usado por _detectar_dominio)
    @classmethod
    def _dominios_es(cls) -> dict:
        return {k: v[0] for k, v in cls._DOMINIOS_I18N.items()}

    # Respuestas que NO deben envolverse
    _SKIP_PATTERNS = [
        'error al procesar',
        'consulta crítica',
        'responde **sí**',
        'no pude',
        'no encontré datos',
        'no se encontraron',
        'modo **solo lectura**',
        'intenta reformular',
        'no hay datos',
    ]

    # Marcador interno para evitar doble aplicación (NO se expone al usuario)
    _MARCADOR = '__conclusiones_ok__'

    def aplicar(self, respuesta: str, accion: str, intencion: str,
                es_cadena: bool = False) -> str:
        """Envuelve la respuesta con estructura conversacional.

        Args:
            respuesta: Markdown formateado por los formateadores existentes
            accion: accion_sugerida de la consulta
            intencion: intencion_principal de la consulta
            es_cadena: si fue una cadena multi-agente
        """
        if not respuesta or self._es_skip(respuesta):
            return respuesta

        try:
            from models.conector_odoo import _ctx_idioma
            idioma = _ctx_idioma.get()
        except Exception:
            idioma = "es"

        dominio = self._detectar_dominio(accion, intencion, idioma)
        reconocimiento = self._reconocimiento(dominio, es_cadena, idioma)
        insight = self._extraer_insight(respuesta)
        cierre = self._cierre(idioma)

        partes = [self._MARCADOR, reconocimiento, '', respuesta]

        if insight:
            obs_label = {'en': '💡 **Observation:**', 'ja': '💡 **観察：**'}.get(idioma, '💡 **Observación:**')
            partes.extend(['', f'{obs_label} {insight}'])

        partes.extend(['', cierre])

        return '\n'.join(partes)

    # ── Internos ─────────────────────────────────────────────

    def _es_skip(self, respuesta: str) -> bool:
        """Detecta respuestas de sistema que no deben envolverse."""
        if self._MARCADOR in respuesta:
            return True
        resp_lower = respuesta[:300].lower()
        return any(p in resp_lower for p in self._SKIP_PATTERNS)

    def _detectar_dominio(self, accion: str, intencion: str, idioma: str = "es") -> str:
        # 1. Coincidencia exacta por nombre de acción
        if accion in self._DOMINIOS_I18N:
            return self._dominio_por_idioma(accion, idioma)
        # 2. Substring: gana la clave más larga
        texto = f'{accion} {intencion}'.lower()
        candidatos = [(pat, self._dominio_por_idioma(pat, idioma)) for pat in self._DOMINIOS_I18N if pat in texto]
        if candidatos:
            return max(candidatos, key=lambda x: len(x[0]))[1]
        _defaults = {'en': 'the requested data', 'ja': 'リクエストされたデータ'}
        return _defaults.get(idioma, 'los datos solicitados')

    def _reconocimiento(self, dominio: str, es_cadena: bool, idioma: str = "es") -> str:
        if idioma == "en":
            if es_cadena:
                return (
                    f'📊 I\'ve completed a comprehensive analysis of **{dominio}**, '
                    f'combining multiple perspectives. Here\'s what I found:'
                )
            return f'📊 I\'ve analyzed the **{dominio}** data and here\'s what I found:'
        elif idioma == "ja":
            if es_cadena:
                return (
                    f'📊 **{dominio}**の包括的な分析を完了しました。'
                    f'複数の視点を組み合わせた結果をご報告します：'
                )
            return f'📊 **{dominio}**のデータを分析しました。結果は以下の通りです：'
        # Español (default)
        if es_cadena:
            return (
                f'📊 He realizado un análisis completo de **{dominio}** '
                f'combinando múltiples perspectivas. Esto es lo que encontré:'
            )
        return f'📊 He analizado los datos de **{dominio}** y esto es lo que encontré:'

    def _extraer_insight(self, respuesta: str) -> str:
        """Extrae la observación más relevante: prioriza alertas > insights."""
        lineas = respuesta.split('\n')
        alertas = []
        insights = []
        seccion_actual = None

        for linea in lineas:
            stripped = linea.strip()
            lower = stripped.lower()

            # Detectar inicio de secciones relevantes
            if lower.startswith('### alerta') or lower.startswith('### ⚠'):
                seccion_actual = 'alertas'
                continue
            elif lower.startswith('### insight') or lower.startswith('### 💡'):
                seccion_actual = 'insights'
                continue
            elif stripped.startswith('### ') or stripped.startswith('## '):
                seccion_actual = None
                continue

            # Recolectar items de la sección activa
            if stripped.startswith('- ') and seccion_actual:
                texto = stripped[2:].strip()
                if texto and len(texto) > 10:
                    if seccion_actual == 'alertas':
                        alertas.append(texto)
                    elif seccion_actual == 'insights':
                        insights.append(texto)

        # Priorizar alertas (más accionables)
        if alertas:
            return alertas[0]
        if insights:
            return insights[0]
        return ''

    def _cierre(self, idioma: str = "es") -> str:
        if idioma == "en":
            return (
                '📎 Would you like me to generate an **Excel**, **PDF** '
                'or a **chart** for a detailed review?'
            )
        elif idioma == "ja":
            return '📎 **Excel**、**PDF**、または**グラフ**を生成しましょうか？詳細をご確認いただけます。'
        return (
            '📎 ¿Quieres que genere el **Excel**, **PDF** '
            'o alguna **gráfica** para que lo revises con calma?'
        )
