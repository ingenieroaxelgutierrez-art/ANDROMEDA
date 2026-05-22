# ============================================================
# ANDROMEDA — Traducción de etiquetas de FormateadorRespuestas
# ============================================================
# Traduce los strings de plantilla (headers, labels, insights)
# generados por FormateadorRespuestas sin tocar el formatter.
#
# Estrategia: dos pasadas
#   1. Reemplazos de cadena exacta (más rápido, para labels estáticos)
#   2. Reemplazos regex (para strings con valores dinámicos intercalados)
#
# NO traduce: nombres de productos/clientes/empresas, números,
#             montos monetarios, porcentajes, códigos SKU.
# ============================================================

import re
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Reemplazos exactos: (string_es, en, ja)
# Orden importa: los más largos primero para evitar solapamientos.
# ---------------------------------------------------------------------------
_EXACT: List[Tuple[str, str, str]] = [
    # ── Manual de Odoo (estructural) ──────────────────────────────────────
    ("## Odooマニュアル\n\nマニュアルインデックスがまだ生成されていません。先に`MANUAL.docx`ファイルを処理してください。",
     "## Odoo Manual\n\nThe manual index has not been generated yet. Please process the `MANUAL.docx` file first.",
     "## Odooマニュアル\n\nマニュアルインデックスがまだ生成されていません。先に`MANUAL.docx`ファイルを処理してください。"),
    ("## Odoo Manual\n\nThe manual index has not been generated yet. Please process the `MANUAL.docx` file first.",
     "## Odoo Manual\n\nThe manual index has not been generated yet. Please process the `MANUAL.docx` file first.",
     "## Odooマニュアル\n\nマニュアルインデックスがまだ生成されていません。先に`MANUAL.docx`ファイルを処理してください。"),
    ("## Manual de Odoo\n\nEl índice del manual aún no está generado. Procesa el archivo `MANUAL.docx` primero.",
     "## Odoo Manual\n\nThe manual index has not been generated yet. Please process the `MANUAL.docx` file first.",
     "## Odooマニュアル\n\nマニュアルインデックスがまだ生成されていません。先に`MANUAL.docx`ファイルを処理してください。"),
    ("## Consultar Manual\n\nNo se pudo acceder al manual de Odoo.",
     "## Manual Query\n\nCould not access the Odoo manual.",
     "## マニュアル照会\n\nOdooマニュアルにアクセスできませんでした。"),
    ("## Manual de Odoo",                  "## Odoo Manual",                "## Odooマニュアル"),
    ("*Información extraída del Manual de Odoo*",
     "*Information extracted from the Odoo Manual*",
     "*Odooマニュアルより抜粋*"),
    ("No encontré información sobre eso en el manual.\n\n¿Podrías reformular tu pregunta o usar otras palabras?",
     "I couldn't find information about that in the Odoo manual.\n\nCould you rephrase your question or use different keywords?",
     "Odooマニュアルにその情報は見つかりませんでした。\n\n質問を言い換えるか、別のキーワードを使ってみてください。"),
    ("(Ver imagen de referencia para:",     "(Reference image for:",         "（参照画像："),
    ("(Ver imagen)",                        "(See image)",                   "（画像参照）"),
    ("*... (ver manual completo para más pasos)*",
     "*... (see the full manual for more steps)*",
     "*... (詳細はマニュアル全文をご覧ください)*"),

    # ── Conclusiones wrapper (FormateadorConclusiones) ─────────────────────
    ("<!-- conclusiones-aplicadas -->", "", ""),

    # ── Títulos de sección (## / ###) ─────────────────────────────────────
    ("## Análisis Especializado de Cuentas por Cobrar",
     "## Specialized Accounts Receivable Analysis",
     "## 売掛金の専門分析"),
    ("## Análisis Especializado de Cuentas por Pagar",
     "## Specialized Accounts Payable Analysis",
     "## 買掛金の専門分析"),
    ("## Análisis Especializado de Ventas",
     "## Specialized Sales Analysis",
     "## 売上の専門分析"),
    ("## Análisis Avanzado de Rotación de Inventario",
     "## Advanced Inventory Turnover Analysis",
     "## 在庫回転の詳細分析"),
    ("## Ventas por Empresa",
     "## Sales by Company",
     "## 企業別売上"),
    ("## Inventario por Almacén",
     "## Inventory by Warehouse",
     "## 倉庫別在庫"),
    ("Productos en Estado Crítico",
     "Products in Critical State",
     "重要状態の商品"),
    ("## 💲 Valoración de Inventario",
     "## 💲 Inventory Valuation",
     "## 💲 在庫評価額"),
    ("## 🔄 Rotación de Inventario",
     "## 🔄 Inventory Turnover",
     "## 🔄 在庫回転"),
    ("## 💼 Ventas por Vendedor",
     "## 💼 Sales by Sales Rep",
     "## 💼 担当者別売上"),
    ("## 💳 Métodos de Pago",
     "## 💳 Payment Methods",
     "## 💳 支払方法"),
    ("## 🖥️ Sesiones POS",
     "## 🖥️ POS Sessions",
     "## 🖥️ POSセッション"),
    ("## 📆 Análisis de Estacionalidad",
     "## 📆 Seasonality Analysis",
     "## 📆 季節性分析"),
    ("## Predicción de Flujo de Caja",
     "## Cash Flow Forecast",
     "## キャッシュフロー予測"),
    ("## Score de Salud del Negocio",
     "## Business Health Score",
     "## 事業健全性スコア"),
    ("Predicción de Agotamiento de Inventario",
     "Inventory Depletion Forecast",
     "在庫切れ予測"),
    ("Punto de Venta",
     "Point of Sale",
     "POS"),
    ("Productos Más Vendidos",
     "Best-Selling Products",
     "売れ筋商品"),

    # ── Sub-secciones (###) ───────────────────────────────────────────────
    ("### Resumen General",        "### General Summary",       "### 全体概要"),
    ("### Puntuación General:",    "### Overall Score:",        "### 総合スコア:"),
    ("### Desglose por Área",      "### Breakdown by Area",     "### 分野別内訳"),
    ("### Recomendaciones",        "### Recommendations",       "### 推奨事項"),
    ("### Patrones Identificados", "### Identified Patterns",   "### 特定されたパターン"),
    ("### 🔎 Insights",           "### 🔎 Insights",           "### 🔎 インサイト"),
    ("### ✅ Recomendaciones",    "### ✅ Recommendations",    "### ✅ 推奨事項"),
    ("### Insights Adicionales",   "### Additional Insights",   "### 追加インサイト"),
    ("### Insights",               "### Insights",              "### インサイト"),
    ("### Alertas",                "### Alerts",                "### アラート"),
    ("### Resumen",                "### Summary",               "### 概要"),
    ("### Ranking",                "### Ranking",               "### ランキング"),
    ("### 📊 Insight Pareto",     "### 📊 Pareto Insight",     "### 📊 パレート分析"),
    ("### 📊 Análisis de Concentración", "### 📊 Concentration Analysis", "### 📊 集中度分析"),
    ("### 📊 Análisis de Desempeño",    "### 📊 Performance Analysis",   "### 📊 パフォーマンス分析"),
    ("### Estado de Stock",        "### Stock Status",          "### 在庫状況"),
    ("### Productos Críticos (< 7 días de stock)",
     "### Critical Products (< 7 days of stock)",
     "### 重要商品（在庫7日未満）"),
    ("### Indicadores de Rotación","### Turnover Indicators",   "### 回転率指標"),
    ("### Clasificación ABC",      "### ABC Classification",    "### ABC分類"),
    ("### Confianza de Datos:",    "### Data Confidence:",      "### データ信頼度:"),
    ("### Confianza:",             "### Confidence:",           "### 信頼度:"),
    ("### Métricas Principales",   "### Main Metrics",          "### 主要指標"),
    ("### Ranking por Empresa",    "### Ranking by Company",    "### 企業別ランキング"),
    ("### Desglose por Almacén",   "### Breakdown by Warehouse","### 倉庫別内訳"),
    ("### Resumen de Criticidad",  "### Criticality Summary",   "### 重要度概要"),
    ("### Productos que Requieren Acción Inmediata",
     "### Products Requiring Immediate Action",
     "### 即時対応が必要な商品"),
    ("### Análisis por Antigüedad","### Aging Analysis",        "### エイジング分析"),
    ("### Top Deudores",           "### Top Debtors",           "### 主要債務者"),
    ("### Top Proveedores",        "### Top Suppliers",         "### 主要仕入先"),
    ("### Indicadores",            "### Indicators",            "### 指標"),
    ("### ⚠️ Alertas",           "### ⚠️ Alerts",            "### ⚠️ アラート"),
    ("### ⚠️ Observaciones",     "### ⚠️ Observations",      "### ⚠️ 観察"),
    ("### Interpretación",         "### Interpretation",        "### 解釈"),
    ("### Cartera",                "### Portfolio",             "### 債権・債務"),
    ("### Estado General:",        "### General Status:",       "### 全体状況:"),

    # ── Encabezados de tabla ──────────────────────────────────────────────
    ("| Métrica | Valor |",
     "| Metric | Value |",
     "| 指標 | 値 |"),
    ("|---------|-------|", "|---------|-------|", "|---------|-------|"),  # divisor sin cambio
    ("| # | Producto | Unidades | Ingresos | % del Total |",
     "| # | Product | Units | Revenue | % of Total |",
     "| # | 商品 | 数量 | 売上 | 合計の% |"),
    ("|---|----------|----------|----------|-------------|",
     "|---|----------|----------|----------|-------------|",
     "|---|----------|----------|----------|-------------|"),
    ("| # | Cliente | Órdenes | Total | % Participación |",
     "| # | Customer | Orders | Total | % Share |",
     "| # | 顧客 | 注文数 | 合計 | 参加率% |"),
    ("|---|---------|---------|-------|----------------|",
     "|---|---------|---------|-------|----------------|",
     "|---|---------|---------|-------|----------------|"),
    ("| # | Vendedor | Órdenes | Total | % del Equipo | vs Promedio |",
     "| # | Sales Rep | Orders | Total | % of Team | vs Average |",
     "| # | 担当者 | 注文数 | 合計 | チームの% | 平均比 |"),
    ("|---|----------|---------|-------|--------------|-------------|",
     "|---|----------|---------|-------|--------------|-------------|",
     "|---|----------|---------|-------|--------------|-------------|"),
    ("| Método | Transacciones | Total | % |",
     "| Method | Transactions | Total | % |",
     "| 方法 | 取引数 | 合計 | % |"),
    ("| Sesión | Tickets | Total | Estado |",
     "| Session | Tickets | Total | Status |",
     "| セッション | チケット | 合計 | 状態 |"),
    ("| Estado | Producto | Vendido/mes | Stock | Días Stock |",
     "| Status | Product | Sold/month | Stock | Stock Days |",
     "| 状態 | 商品 | 月販売数 | 在庫 | 在庫日数 |"),
    ("|--------|----------|-------------|-------|------------|",
     "|--------|----------|-------------|-------|------------|",
     "|--------|----------|-------------|-------|------------|"),
    ("| Nivel | Cantidad |",
     "| Level | Quantity |",
     "| レベル | 数量 |"),
    ("|-------|----------|", "|-------|----------|", "|-------|----------|"),
    ("| # | Empresa | Órdenes | Total | % |",
     "| # | Company | Orders | Total | % |",
     "| # | 企業 | 注文数 | 合計 | % |"),
    ("| Almacén | Empresa | Productos | Cantidad | % |",
     "| Warehouse | Company | Products | Qty | % |",
     "| 倉庫 | 企業 | 商品数 | 数量 | % |"),
    ("| Producto | Stock Actual | Venta/Día | Días Stock | Estado |",
     "| Product | Current Stock | Sales/Day | Stock Days | Status |",
     "| 商品 | 現在庫 | 日販売数 | 在庫日数 | 状態 |"),
    ("| Categoría | Productos | % Valor | Descripción |",
     "| Category | Products | % Value | Description |",
     "| カテゴリ | 商品数 | 価値% | 説明 |"),
    ("| Período | Monto | % |",
     "| Period | Amount | % |",
     "| 期間 | 金額 | % |"),
    ("| Concepto | Monto |",
     "| Concept | Amount |",
     "| 項目 | 金額 |"),
    ("| # | Cliente | Monto | Días Vencido |",
     "| # | Customer | Amount | Overdue Days |",
     "| # | 顧客 | 金額 | 延滞日数 |"),
    ("|---|---------|-------|-------------|",
     "|---|---------|-------|-------------|",
     "|---|---------|-------|-------------|"),

    # ── Filas de tabla con labels (parciales, sin valores dinámicos) ──────
    ("| Productos únicos |",          "| Unique products |",        "| ユニーク商品数 |"),
    ("| Unidades vendidas (total) |", "| Units sold (total) |",     "| 販売数量（合計） |"),
    ("| Ingresos (total) |",          "| Revenue (total) |",        "| 売上（合計） |"),
    ("| Total Órdenes |",             "| Total Orders |",           "| 注文数合計 |"),
    ("| Total Órdenes |",             "| Total Orders |",           "| 注文数合計 |"),
    ("| Ventas Totales |",            "| Total Sales |",            "| 総売上 |"),
    ("| Ticket Promedio |",           "| Average Ticket |",         "| 平均チケット額 |"),
    ("| Venta Máxima |",              "| Max Sale |",               "| 最大売上 |"),
    ("| Venta Mínima |",              "| Min Sale |",               "| 最小売上 |"),
    ("| Mediana |",                   "| Median |",                 "| 中央値 |"),
    ("| Total Almacenes |",           "| Total Warehouses |",       "| 倉庫数合計 |"),
    ("| Total Productos |",           "| Total Products |",         "| 商品数合計 |"),
    ("| Unidades Totales |",          "| Total Units |",            "| 総数量 |"),
    ("| Total por Cobrar |",          "| Total Receivables |",      "| 売掛金合計 |"),
    ("| Facturas Pendientes |",       "| Pending Invoices |",       "| 未処理請求書 |"),
    ("| Clientes Deudores |",         "| Debtor Customers |",       "| 債務顧客数 |"),
    ("| Antigüedad Promedio |",       "| Average Age |",            "| 平均日数 |"),
    ("| Total por Pagar |",           "| Total Payables |",         "| 買掛金合計 |"),
    ("| Proveedores |",               "| Suppliers |",              "| 仕入先数 |"),
    ("| Total productos analizados |","| Total products analyzed |", "| 分析商品数合計 |"),
    ("| Empresas con ventas |",       "| Companies with sales |",   "| 売上のある企業数 |"),
    ("| Productos en catálogo |",     "| Products in catalog |",    "| カタログ商品数 |"),
    ("| Unidades totales |",          "| Total units |",            "| 総数量 |"),
    ("| Total productos |",           "| Total products |",         "| 商品数合計 |"),
    ("| 💲 Valor estimado del inventario |",
     "| 💲 Estimated inventory value |",
     "| 💲 推定在庫評価額 |"),
    ("| Rotación Promedio |",         "| Average Turnover |",       "| 平均回転率 |"),
    ("| Días de Inventario Promedio |","| Avg Inventory Days |",    "| 平均在庫日数 |"),
    ("| Valor Inmovilizado |",        "| Immobilized Value |",      "| 滞留在庫額 |"),
    ("| Órdenes |",                   "| Orders |",                 "| 注文数 |"),
    ("| Total |",                     "| Total |",                  "| 合計 |"),
    ("| Mayor orden |",               "| Largest order |",          "| 最大注文 |"),
    ("| Promedio por orden |",        "| Average per order |",      "| 注文平均額 |"),
    ("| Tickets |",                   "| Tickets |",                "| チケット数 |"),
    ("| Ventas totales |",            "| Total sales |",            "| 総売上 |"),
    ("| Ticket promedio |",           "| Avg ticket |",             "| 平均チケット額 |"),
    ("| 🔴 Críticos (<7 días) |",    "| 🔴 Critical (<7 days) |",  "| 🔴 重要（7日未満） |"),
    ("| 🟡 Alerta (7-14 días) |",    "| 🟡 Alert (7-14 days) |",   "| 🟡 警告（7〜14日） |"),
    ("| ⏸️ Sin movimiento |",        "| ⏸️ No movement |",         "| ⏸️ 動きなし |"),
    ("| 🔴 Urgente (<3 días) |",     "| 🔴 Urgent (<3 days) |",    "| 🔴 緊急（3日未満） |"),
    ("| 🟡 Alerta (3-7 días) |",     "| 🟡 Alert (3-7 days) |",    "| 🟡 警告（3〜7日） |"),
    ("| Total con <7 días |",        "| Total with <7 days |",      "| 7日未満の合計 |"),
    ("| Total analizados |",         "| Total analyzed |",          "| 分析合計 |"),
    ("| Agotado |",                  "| Depleted |",                "| 在庫切れ |"),
    ("| Crítico |",                  "| Critical |",                "| 重要 |"),
    ("| Bajo |",                     "| Low |",                     "| 低い |"),
    ("| Sin stock |",                "| Out of stock |",            "| 在庫なし |"),
    ("| < 7 días de stock |",        "| < 7 days of stock |",       "| 在庫7日未満 |"),
    ("| < 14 días de stock |",       "| < 14 days of stock |",      "| 在庫14日未満 |"),
    ("| Alta rotación |",            "| High turnover |",           "| 高回転 |"),
    ("| Rotación media |",           "| Medium turnover |",         "| 中回転 |"),
    ("| Baja rotación |",            "| Low turnover |",            "| 低回転 |"),
    ("| A (Alto) |",                 "| A (High) |",                "| A（高） |"),
    ("| B (Medio) |",                "| B (Medium) |",              "| B（中） |"),
    ("| C (Bajo) |",                 "| C (Low) |",                 "| C（低） |"),
    ("| Variación % |",              "| Variation % |",             "| 変動率% |"),
    ("| Variación absoluta |",       "| Absolute variation |",      "| 絶対変動 |"),
    ("| Diferencia en órdenes |",    "| Order difference |",        "| 注文数差 |"),
    ("| Vigente (0-30 días) |",      "| Current (0-30 days) |",     "| 正常（0〜30日） |"),
    ("| Vencido 30-60 días |",       "| Overdue 30-60 days |",      "| 延滞30〜60日 |"),
    ("| Vencido 60-90 días |",       "| Overdue 60-90 days |",      "| 延滞60〜90日 |"),
    ("| Vencido +90 días |",         "| Overdue +90 days |",        "| 延滞90日超 |"),
    ("| Por cobrar (CXC) |",         "| Receivables (AR) |",        "| 売掛金（AR） |"),
    ("| Por pagar (CXP) |",          "| Payables (AP) |",           "| 買掛金（AP） |"),
    ("| Entradas proyectadas |",     "| Projected inflows |",       "| 予測入金額 |"),
    ("| Salidas proyectadas |",      "| Projected outflows |",      "| 予測出金額 |"),
    ("| Flujo neto |",               "| Net cash flow |",           "| 純キャッシュフロー |"),
    ("| 🏆 Mejor día de la semana |","| 🏆 Best day of the week |", "| 🏆 最良の曜日 |"),
    ("| 🔽 Peor día de la semana |", "| 🔽 Worst day of the week |","| 🔽 最悪の曜日 |"),
    ("| 🌟 Mejor mes del año |",     "| 🌟 Best month of the year |","| 🌟 最良の月 |"),
    ("| 🔽 Peor mes del año |",      "| 🔽 Worst month of the year |","| 🔽 最悪の月 |"),

    # ── Strings de insight y cierre ───────────────────────────────────────
    ("🟡 **Un solo método de pago**: si falla, no hay alternativa. Considerar activar métodos adicionales para no perder ventas.",
     "🟡 **Single payment method**: if it fails, there is no alternative. Consider activating additional methods to avoid lost sales.",
     "🟡 **支払方法が1つだけ**：障害発生時に代替手段がありません。売上損失を防ぐため追加方法の有効化を検討してください。"),
    ("🟢 **Buena diversidad de métodos de pago",
     "🟢 **Good payment method diversity",
     "🟢 **支払方法の多様性良好"),
    ("el cliente tiene flexibilidad y los riesgos operativos son menores.",
     "customers have flexibility and operational risks are lower.",
     "顧客の選択肢が豊富で運用リスクも低い状態です。"),
    ("🟢 **Todas las sesiones están cerradas**: los datos de este período son confiables para reportes.",
     "🟢 **All sessions are closed**: data for this period is reliable for reporting.",
     "🟢 **全セッション終了**：この期間のデータはレポートに信頼できます。"),
    ("**Venta promedio por sesión:**",
     "**Average sale per session:**",
     "**セッション平均売上:**"),
    ("🟢 **Inventario saludable**: ningún producto con menos de 7 días de cobertura.",
     "🟢 **Healthy inventory**: no products with less than 7 days of coverage.",
     "🟢 **健全な在庫**：7日未満の在庫商品はありません。"),
    ("🟢 **Distribución saludable**: los ingresos están bien distribuidos entre el catálogo de productos.",
     "🟢 **Healthy distribution**: revenue is well distributed across the product catalog.",
     "🟢 **健全な分布**：売上は商品カタログ全体に均等に分散されています。"),
    ("🟡 **Concentración moderada**: fortalecer los siguientes productos en el ranking puede mejorar la estabilidad de ingresos.",
     "🟡 **Moderate concentration**: strengthening the next products in the ranking can improve revenue stability.",
     "🟡 **中程度の集中度**：ランキング上位以外の商品を強化することで売上安定性を高められます。"),
    ("🔴 **Concentración alta**:",
     "🔴 **High concentration**:",
     "🔴 **集中度が高い**："),
    ("Alta dependencia de pocos SKUs. Diversificar el catálogo reduce riesgo.",
     "High dependency on few SKUs. Diversifying the catalog reduces risk.",
     "少数SKUへの依存度が高い状態です。カタログの多様化でリスクを軽減できます。"),
    ("representa más del 80% de ingresos.",
     "represents over 80% of revenue.",
     "が売上の80%以上を占めています。"),
    ("productos representan más del 80% de ingresos.",
     "products represent over 80% of revenue.",
     "商品が売上の80%以上を占めています。"),
    ("🔴 **Riesgo de concentración crítico**: 3 clientes generan más del 70% de los ingresos. Perder uno impactaría gravemente el negocio. Diversificar la base de clientes.",
     "🔴 **Critical concentration risk**: 3 customers generate over 70% of revenue. Losing one would severely impact the business. Diversify the customer base.",
     "🔴 **集中リスク重大**：上位3顧客が売上の70%超を占めています。1社を失うとビジネスへの影響が深刻です。顧客基盤の分散をお勧めします。"),
    ("🟢 **Base de clientes saludable**: buena distribución de ingresos. Bajo riesgo de dependencia.",
     "🟢 **Healthy customer base**: good revenue distribution. Low dependency risk.",
     "🟢 **健全な顧客基盤**：売上分布が良好で依存リスクが低い状態です。"),
    ("🔴 **Desbalance alto en el equipo**: el vendedor líder supera al último por",
     "🔴 **High team imbalance**: the top rep outperforms the last by",
     "🔴 **チームの著しい格差**：トップ担当者が最下位担当者を"),
    ("Revisar asignación de territorios, capacitación o cuentas.",
     "Review territory assignment, training, or accounts.",
     "テリトリー配分、研修、またはアカウントを見直してください。"),
    ("🟡 **Diferencia notable** entre vendedores. Compartir tácticas del líder puede elevar el desempeño general.",
     "🟡 **Notable difference** among sales reps. Sharing the leader's tactics can raise overall performance.",
     "🟡 **担当者間の顕著な格差**。トップ担当者の戦術を共有することで全体パフォーマンスが向上します。"),
    ("🟢 **Equipo equilibrado**: baja dispersión de resultados. Buen rendimiento colectivo.",
     "🟢 **Balanced team**: low dispersion of results. Good collective performance.",
     "🟢 **チームのバランスが良好**：結果のばらつきが低く、全体的に良いパフォーマンスです。"),
    ("🟡 **Pocos registros**: muestra pequeña, los promedios pueden no ser representativos.",
     "🟡 **Few records**: small sample, averages may not be representative.",
     "🟡 **レコード数が少ない**：サンプルが小さく、平均値が代表的でない可能性があります。"),
    ("🟡 **Concentración alta**: la mayor operación representa el",
     "🟡 **High concentration**: the largest transaction represents",
     "🟡 **集中度が高い**：最大取引が"),
    ("del total. Dependencia de pocos pedidos grandes.",
     "of the total. Dependency on a few large orders.",
     "を占めています。大口注文への依存が高い状態です。"),
    ("URGENTE",
     "URGENT",
     "緊急"),
    ("producto(s) se agotarán en menos de 7 días. Emitir órdenes de compra o trasladar stock de inmediato.",
     "product(s) will run out in less than 7 days. Issue purchase orders or transfer stock immediately.",
     "商品が7日以内に在庫切れになります。至急発注書を発行するか在庫を移動してください。"),
    ("producto(s) en zona de alerta (7-14 días). Iniciar proceso de reposición.",
     "product(s) in the alert zone (7-14 days). Start replenishment process.",
     "商品が警告ゾーン（7〜14日）にあります。補充プロセスを開始してください。"),
    ("producto(s) sin ventas recientes. Evaluar si son obsoletos o requieren promoción.",
     "product(s) with no recent sales. Evaluate if they are obsolete or need promotion.",
     "商品に最近の売上がありません。陳腐化しているか、プロモーションが必要か評価してください。"),
    ("producto(s) con menos de 3 días de stock. Ordenar de reposición HOY.",
     "product(s) with less than 3 days of stock. Order replenishment TODAY.",
     "商品の在庫が3日未満です。今日中に補充発注をしてください。"),
    ("producto(s) entre 3 y 7 días. Emitir orden de compra esta semana.",
     "product(s) between 3 and 7 days. Issue a purchase order this week.",
     "商品が3〜7日分の在庫です。今週中に発注書を発行してください。"),
    ("sin costo configurado**: la valoración es parcial. Actualizar costos en Odoo para obtener cifras exactas.",
     "without configured cost**: valuation is partial. Update costs in Odoo for accurate figures.",
     "のコストが未設定です**：評価額が部分的です。正確な数値を得るためOdooでコストを更新してください。"),
    ("El valor del inventario es clave para el balance general. ¿Quieres ver el desglose por categoría, almacén o clasificación ABC?",
     "Inventory value is key for the balance sheet. Want to see the breakdown by category, warehouse, or ABC classification?",
     "在庫評価額は貸借対照表の重要な項目です。カテゴリ別、倉庫別、またはABC分類での内訳をご覧になりますか？"),
    ("Ver tabla de datos para detalles de cada producto",
     "See data table for details on each product",
     "各商品の詳細はデータ表をご覧ください"),
    ("Ver tabla para detalle completo por día de la semana",
     "See table for full detail by day of the week",
     "曜日別の詳細は表をご覧ください"),
    ("Ver tabla de datos para detalle completo",
     "See data table for full detail",
     "詳細はデータ表をご覧ください"),
    ("**Método dominante**:",
     "**Dominant method**:",
     "**主要支払方法**："),
    ("del total)",
     "of the total)",
     "を占める）"),
    ("**Promedio del equipo**:",
     "**Team average**:",
     "**チーム平均**："),
    ("**Líder de ventas**:",
     "**Sales leader**:",
     "**売上トップ**："),
    ("**Brecha líder vs último**:",
     "**Gap: leader vs. last**:",
     "**トップ対最下位の差**："),
    ("de diferencia",
     "difference",
     "の差"),
    ("Costo promedio por unidad:",
     "Average cost per unit:",
     "単位当たり平均コスト："),
    ("Confianza de Datos:",
     "Data Confidence:",
     "データ信頼度："),

    # ── Call-to-action (💡) ────────────────────────────────────────────────
    ("¿Quieres ver la tendencia de ventas de un producto específico, márgenes o predicción de demanda?",
     "Want to see the sales trend for a specific product, margins, or demand forecast?",
     "特定商品の販売トレンド、マージン、需要予測をご覧になりますか？"),
    ("¿Quieres ver el análisis de lealtad, clientes en riesgo de churn o RFM (Recencia, Frecuencia, Monto)?",
     "Want to see loyalty analysis, at-risk churn customers, or RFM (Recency, Frequency, Amount)?",
     "ロイヤルティ分析、離脱リスク顧客、またはRFM（最新性・頻度・金額）をご覧になりますか？"),
    ("¿Quieres ver el rendimiento de un vendedor específico, cumplimiento de metas o comparativa por período?",
     "Want to see a specific rep's performance, goal attainment, or period comparison?",
     "特定担当者のパフォーマンス、目標達成度、または期間比較をご覧になりますか？"),
    ("¿Quieres ver el desglose por vendedor, producto, predicción o comparativa con el período anterior?",
     "Want to see breakdown by sales rep, product, forecast, or comparison with the previous period?",
     "担当者別、商品別、予測、または前期比較の内訳をご覧になりますか？"),
    ("¿Quieres ver productividad por cajero, métodos de pago, sesiones detalladas o comparativa de sucursales?",
     "Want to see cashier productivity, payment methods, detailed sessions, or branch comparison?",
     "キャッシャー別生産性、支払方法、詳細セッション、または支店比較をご覧になりますか？"),
    ("¿Quieres ver métodos de pago por sucursal, cajero o período específico?",
     "Want to see payment methods by branch, cashier, or specific period?",
     "支店別、キャッシャー別、または特定期間の支払方法をご覧になりますか？"),
    ("¿Quieres ver el detalle de una sesión específica, productividad por cajero o comparativa de sucursales?",
     "Want to see the detail of a specific session, cashier productivity, or branch comparison?",
     "特定セッションの詳細、キャッシャー別生産性、または支店比較をご覧になりますか？"),
    ("¿Quieres ver rotación, productos críticos, predicción de agotamiento o clasificación ABC?",
     "Want to see turnover, critical products, depletion forecast, or ABC classification?",
     "回転率、重要商品、在庫切れ予測、またはABC分類をご覧になりますか？"),
    ("¿Quieres ver los montos de reposición, clasificación ABC o simular escenarios de demanda?",
     "Want to see replenishment amounts, ABC classification, or simulate demand scenarios?",
     "補充金額、ABC分類、または需要シナリオのシミュレーションをご覧になりますか？"),
    ("¿Quieres ver la clasificación ABC, valoración de inventario o predicción de agotamiento?",
     "Want to see ABC classification, inventory valuation, or depletion forecast?",
     "ABC分類、在庫評価額、または在庫切れ予測をご覧になりますか？"),
    ("¿Quieres ver el desglose por producto, vendedor o proyección para el siguiente período?",
     "Want to see breakdown by product, sales rep, or projection for the next period?",
     "商品別、担当者別、または次の期間の見込みをご覧になりますか？"),
    ("¿Quieres ver el análisis por hora, producto o sucursal?",
     "Want to see analysis by hour, product, or branch?",
     "時間別、商品別、または支店別の分析をご覧になりますか？"),

    # ── Títulos de sección con valores variables (prefijo seguro) ─────────
    ("Período Actual",   "Current Period",   "今期"),
    ("Período Anterior", "Previous Period",  "前期"),
    ("Próximos 30 días", "Next 30 days",     "今後30日"),
    ("Flujo neto",       "Net cash flow",    "純キャッシュフロー"),
    ("POSITIVO",         "POSITIVE",         "プラス"),
    ("NEGATIVO",         "NEGATIVE",         "マイナス"),
    ("Estado:",          "Status:",          "状態："),

    # ── Valores de estado ─────────────────────────────────────────────────
    ("✅ Cerrada",        "✅ Closed",         "✅ 終了"),
    ("🔴 Abierta",        "🔴 Open",           "🔴 オープン"),
    ("Sin insights",      "No insights",       "インサイトなし"),
    ("Sin alertas",       "No alerts",         "アラートなし"),
    ("No hay datos disponibles.", "No data available.", "データがありません。"),
]


# ---------------------------------------------------------------------------
# Reemplazos con regex: (patron, reemplazo_en, reemplazo_ja)
# Grupos de captura usados para preservar valores dinámicos.
# ---------------------------------------------------------------------------
_REGEX: List[Tuple[str, str, str]] = [    # "**Paso N.** texto..." → "**Step N.** texto..." / "**ステップN.** texto..."
    (
        r"\*\*Paso (\d+)\.\*\*",
        r"**Step \1.**",
        r"**ステップ\1.**",
    ),
    # "**N.** texto..." (formato sin "Paso", usado en lista sin pasos estructurados)
    # Solo traducir si va al inicio de línea para evitar falsos positivos
    (
        r"^(\*\*)(\d+)(\.\*\*)",
        r"\g<1>\2\3",
        r"\g<1>\2\3",
    ),    # "Los top 10 productos generan el **45.3%** de los ingresos totales."
    (
        r"Los top (\d+) productos generan el \*\*(.+?)\*\* de los ingresos totales\.",
        r"The top \1 products generate **\2** of total revenue.",
        r"上位\1製品が総売上の**\2**を占めています。",
    ),
    # "Los top 3 clientes representan el **65.2%** del total."
    (
        r"Los top (\d+) clientes representan el \*\*(.+?)\*\* del total\.",
        r"The top \1 customers represent **\2** of the total.",
        r"上位\1顧客が合計の**\2**を占めています。",
    ),
    # "🟡 **Concentración moderada**: los top 3 representan 55.0%. Evaluar..."
    (
        r"🟡 \*\*Concentración moderada\*\*: los top (\d+) representan (.+?)\. Evaluar estrategias de retención y captación de nuevos clientes\.",
        r"🟡 **Moderate concentration**: the top \1 represent \2. Evaluate retention and new customer acquisition strategies.",
        r"🟡 **中程度の集中度**：上位\1が\2を占めています。リテンションと新規顧客獲得戦略を評価してください。",
    ),
    # "🔴 **Concentración alta**: 10 productos representan más del 80% de ingresos."
    (
        r"🔴 \*\*Concentración alta\*\*: (\d+) productos representan más del 80% de ingresos\.",
        r"🔴 **High concentration**: \1 products represent over 80% of revenue.",
        r"🔴 **集中度が高い**：\1商品が売上の80%以上を占めています。",
    ),
    # "🔴 **URGENTE**: 3 producto(s) se agotarán en menos de 7 días."
    (
        r"🔴 \*\*URGENTE\*\*: (\d+) producto\(s\) se agotarán en menos de 7 días\.",
        r"🔴 **URGENT**: \1 product(s) will run out in less than 7 days.",
        r"🔴 **緊急**：\1商品が7日以内に在庫切れになります。",
    ),
    # "🟡 **Atención**: 5 producto(s) en zona de alerta (7-14 días)."
    (
        r"🟡 \*\*Atención\*\*: (\d+) producto\(s\) en zona de alerta \(7-14 días\)\.",
        r"🟡 **Attention**: \1 product(s) in the alert zone (7-14 days).",
        r"🟡 **注意**：\1商品が警告ゾーン（7〜14日）にあります。",
    ),
    # "⏸️ **Sin movimiento**: 12 producto(s) sin ventas recientes."
    (
        r"⏸️ \*\*Sin movimiento\*\*: (\d+) producto\(s\) sin ventas recientes\.",
        r"⏸️ **No movement**: \1 product(s) with no recent sales.",
        r"⏸️ **動きなし**：\1商品に最近の売上がありません。",
    ),
    # "🔴 **ACCIÓN INMEDIATA**: N producto(s) con menos de 3 días de stock."
    (
        r"🔴 \*\*ACCIÓN INMEDIATA\*\*: (\d+) producto\(s\) con menos de 3 días de stock\.",
        r"🔴 **IMMEDIATE ACTION**: \1 product(s) with less than 3 days of stock.",
        r"🔴 **即時対応**：\1商品の在庫が3日未満です。",
    ),
    # "🟡 **Iniciar proceso de compra**: N producto(s) entre 3 y 7 días."
    (
        r"🟡 \*\*Iniciar proceso de compra\*\*: (\d+) producto\(s\) entre 3 y 7 días\.",
        r"🟡 **Start purchasing process**: \1 product(s) between 3 and 7 days.",
        r"🟡 **購買プロセス開始**：\1商品が3〜7日分の在庫です。",
    ),
    # "N sesión(es) abierta(s): deben cerrarse..."
    (
        r"(\d+) sesión\(es\) abierta\(s\): deben cerrarse para que los reportes financieros sean precisos",
        r"\1 open session(s): must be closed so financial reports are accurate",
        r"\1セッションがオープン状態です。財務レポートの精度のためにクローズしてください",
    ),
    # "N sesión(es) abierta(s) (formato corto)"
    (
        r"🔴 \*\*(\d+) sesión\(es\) abierta\(s\)\*\*:",
        r"🔴 **\1 open session(s)**:",
        r"🔴 **\1セッションがオープン**：",
    ),
    # "N transacción(es) negativa(s) (posibles devoluciones)"
    (
        r"🟡 \*\*(\d+) transacción\(es\) negativa\(s\)\*\* \(posibles devoluciones\)\.",
        r"🟡 **\1 negative transaction(s)** (possible returns).",
        r"🟡 **\1件のマイナス取引**（返品の可能性）。",
    ),
    # "🟡 **Ticket promedio bajo** ($X.XX):"
    (
        r"🟡 \*\*Ticket promedio bajo\*\* \((\$.+?)\):",
        r"🟡 **Low average ticket** (\1):",
        r"🟡 **低い平均チケット額** （\1）：",
    ),
    # "N productos únicos, los promedios..."
    (
        r"\*\*Promedio del equipo\*\*: (\S+)",
        r"**Team average**: \1",
        r"**チーム平均**: \1",
    ),
    # "el vendedor líder supera al último por N% de diferencia"
    (
        r"el vendedor líder supera al último por \*\*(.+?)\*\%\*\* de diferencia\.",
        r"the top sales rep outperforms the last by **\1%** difference.",
        r"トップ担当者が最下位担当者を**\1%**上回っています。",
    ),
    # "el X es el día más fuerte. Concentrar campañas..."
    (
        r"💡 \*\*Oportunidad\*\*: el (.+?) es el día más fuerte\.",
        r"💡 **Opportunity**: \1 is the strongest day.",
        r"💡 **機会**：\1は最も売上の高い曜日です。",
    ),
    # "el X es el día más débil."
    (
        r"🔍 \*\*Para mejorar\*\*: el (.+?) es el día más débil\.",
        r"🔍 **To improve**: \1 is the weakest day.",
        r"🔍 **改善のため**：\1は最も弱い曜日です。",
    ),
    # Venta Promedio por sesión dinámica
    (
        r"Venta promedio por sesión: \*\*(\S+)\*\*",
        r"Average sale per session: **\1**",
        r"セッション平均売上：**\1**",
    ),
    # Estado general con % de riesgo
    (
        r"### Estado General: (.+?) (.+?)% de productos en riesgo",
        r"### General Status: \1 \2% of products at risk",
        r"### 全体状況：\1 商品の\2%がリスク状態",
    ),
    # Tendencia del período
    (
        r"\| Tendencia del período \| \*\*(.+?)\*\* \|",
        r"| Period trend | **\1** |",
        r"| 期間トレンド | **\1** |",
    ),
    # 🟡 Alta concentración en X método
    (
        r"🟡 \*\*Alta concentración en (.+?)\*\*:",
        r"🟡 **High concentration in \1**:",
        r"🟡 **\1への高集中**：",
    ),
    # "N producto(s) sin existencias"
    (
        r"🟡 \*\*(\d+) producto\(s\) sin existencias\*\* \(stock = 0\)\. Evaluar si requieren reposición\.",
        r"🟡 **\1 product(s) with no stock** (stock = 0). Evaluate if replenishment is needed.",
        r"🟡 **\1商品が在庫ゼロ**（stock = 0）。補充が必要かどうか評価してください。",
    ),
    # "N producto(s) con menos de 10 unidades"
    (
        r"🟡 \*\*(\d+) producto\(s\) con menos de 10 unidades\*\*\. Stock crítico\.",
        r"🟡 **\1 product(s) with fewer than 10 units**. Critical stock.",
        r"🟡 **\1商品が10個未満**。重要在庫水準です。",
    ),
    # "N producto(s) con stock negativo"
    (
        r"🔴 \*\*(\d+) producto\(s\) con stock negativo\*\*\. Revisar movimientos pendientes\.",
        r"🔴 **\1 product(s) with negative stock**. Review pending movements.",
        r"🔴 **\1商品のマイナス在庫**。保留中の移動を確認してください。",
    ),
    # Brecha del equipo de ventas (dinámica)
    (
        r"el vendedor líder supera al último por \*\*(\d+)%\*\*\.",
        r"the top rep outperforms the last by **\1%**.",
        r"トップ担当者が最下位を**\1%**上回っています。",
    ),
    # 🟡 Concentración moderada clientes
    (
        r"🟡 \*\*Concentración moderada\*\*: los top 3 representan (.+?)\%\.",
        r"🟡 **Moderate concentration**: the top 3 represent \1%.",
        r"🟡 **中程度の集中度**：上位3社が\1%を占めています。",
    ),
    # "N producto(s) sin costo"
    (
        r"🟡 \*\*(\d+) producto\(s\) sin costo configurado\*\*:",
        r"🟡 **\1 product(s) without configured cost**:",
        r"🟡 **\1商品のコストが未設定**：",
    ),
    # Costo promedio por unidad
    (
        r"💰 Costo promedio por unidad: \*\*(.+?)\*\*",
        r"💰 Average cost per unit: **\1**",
        r"💰 単位当たり平均コスト：**\1**",
    ),
    # Ventas | fecha a fecha (titulo)
    (
        r"## Ventas \| (.+?) a (.+)",
        r"## Sales | \1 to \2",
        r"## 売上 | \1 〜 \2",
    ),
    # No hay tickets POS
    (
        r"No hay tickets POS entre (.+?) y (.+)",
        r"No POS tickets between \1 and \2",
        r"\1から\2の間にPOSチケットがありません",
    ),
    # No hay ventas entre fechas
    (
        r"No hay ventas entre (.+?) y (.+)",
        r"No sales between \1 and \2",
        r"\1から\2の間に売上がありません",
    ),
    # Punto de Venta | fecha a fecha
    (
        r"## Punto de Venta \| (.+?) a (.+)",
        r"## Point of Sale | \1 to \2",
        r"## POS | \1 〜 \2",
    ),
    # Inventario (simple)
    (
        r"## Inventario\b",
        r"## Inventory",
        r"## 在庫",
    ),
    # "No hay datos de inventario"
    (
        r"No hay datos de inventario",
        r"No inventory data",
        r"在庫データがありません",
    ),
    # Comparativa variación
    (
        r"🟢 \*\*Crecimiento excepcional\*\* \((\+.+?)\):",
        r"🟢 **Exceptional growth** (\1):",
        r"🟢 **驚異的な成長** （\1）：",
    ),
    (
        r"🟢 \*\*Crecimiento positivo\*\* \((\+.+?)\):",
        r"🟢 **Positive growth** (\1):",
        r"🟢 **成長** （\1）：",
    ),
    (
        r"🟡 \*\*Crecimiento leve\*\* \((\+.+?)\):",
        r"🟡 **Slight growth** (\1):",
        r"🟡 **わずかな成長** （\1）：",
    ),
    (
        r"➡️ \*\*Sin cambio\*\*:",
        r"➡️ **No change**:",
        r"➡️ **変化なし**：",
    ),
    (
        r"🟡 \*\*Caída leve\*\* \((.+?)\):",
        r"🟡 **Slight decline** (\1):",
        r"🟡 **わずかな低下** （\1）：",
    ),
    (
        r"🔴 \*\*Caída significativa\*\* \((.+?)\):",
        r"🔴 **Significant decline** (\1):",
        r"🔴 **大幅な下落** （\1）：",
    ),
    (
        r"🔴 \*\*Caída crítica\*\* \((.+?)\):",
        r"🔴 **Critical decline** (\1):",
        r"🔴 **深刻な下落** （\1）：",
    ),
    # Comparativa dinámica
    (
        r"las ventas se dispararon\. Identificar qué lo causó para replicarlo\.",
        r"sales surged. Identify what caused it to replicate the success.",
        r"売上が急増しました。要因を特定して再現してください。",
    ),
    (
        r"el período actual supera al anterior\. Buen desempeño\.",
        r"the current period exceeds the previous one. Good performance.",
        r"今期が前期を上回っています。良好なパフォーマンスです。",
    ),
    (
        r"mejora marginal\. Monitorear si se mantiene la tendencia\.",
        r"marginal improvement. Monitor whether the trend continues.",
        r"わずかな改善。トレンドが継続するか監視してください。",
    ),
    (
        r"resultados idénticos\. Verificar si es por factores estacionales\.",
        r"identical results. Verify if it is due to seasonal factors.",
        r"結果が同一です。季節要因によるものか確認してください。",
    ),
    (
        r"ligera disminución\. Vigilar causas antes de que se profundice\.",
        r"slight decrease. Monitor causes before it worsens.",
        r"わずかな減少。悪化する前に原因を監視してください。",
    ),
    (
        r"las ventas bajaron\. Analizar causas: mercado, competencia, operaciones\.",
        r"sales declined. Analyze causes: market, competition, operations.",
        r"売上が減少しました。市場、競合、業務の原因を分析してください。",
    ),
    (
        r"disminución severa\. Requiere plan de recuperación inmediato\.",
        r"severe decrease. Requires an immediate recovery plan.",
        r"深刻な減少。即時の回復計画が必要です。",
    ),
    # Período dinámico del flujo de caja
    (
        r"### Período: (.+)",
        r"### Period: \1",
        r"### 期間： \1",
    ),
    # 💡 Oportunidad estacionalidad
    (
        r"💡 \*\*Oportunidad\*\*: el (.+?) es el día más fuerte\. Concentrar campañas, personal y stock para ese día\.",
        r"💡 **Opportunity**: \1 is the strongest day. Focus campaigns, staff, and stock on that day.",
        r"💡 **機会**：\1が最も好調な曜日です。キャンペーン・人員・在庫をその日に集中させてください。",
    ),
    (
        r"🔍 \*\*Para mejorar\*\*: el (.+?) es el día más débil\. Considerar promociones o descuentos para mover inventario ese día\.",
        r"🔍 **To improve**: \1 is the weakest day. Consider promotions or discounts to move inventory on that day.",
        r"🔍 **改善のため**：\1が最も弱い曜日です。その日に在庫を動かすためのプロモーションや割引を検討してください。",
    ),
]

# Pre-compilar regexes para velocidad
_REGEX_COMPILED: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(pat, re.IGNORECASE), en, ja) for pat, en, ja in _REGEX
]


def traducir_etiquetas(texto: str, idioma: str) -> str:
    """Aplica traducciones de etiquetas al texto Markdown.

    Args:
        texto: Respuesta formateada en español.
        idioma: Código de idioma objetivo ("en" o "ja").

    Returns:
        Texto con etiquetas traducidas. Preserva datos dinámicos
        (números, nombres de productos, montos, etc.).
    """
    if idioma not in ("en", "ja"):
        return texto

    idx = 1 if idioma == "en" else 2

    # Pasada 1: reemplazos exactos (más rápido, cadenas largas primero)
    for entry in _EXACT:
        es_label, en_label, ja_label = entry
        replacement = en_label if idioma == "en" else ja_label
        if es_label and es_label in texto:
            texto = texto.replace(es_label, replacement)

    # Pasada 2: reemplazos regex para strings con valores dinámicos
    for pattern, en_repl, ja_repl in _REGEX_COMPILED:
        replacement = en_repl if idioma == "en" else ja_repl
        texto = pattern.sub(replacement, texto)

    return texto
