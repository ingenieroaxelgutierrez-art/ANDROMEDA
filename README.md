# ANDROMEDA — Agente IA para Odoo v17.0


# NOTA IMPORTANTE: KAIROS-SYNERGY

> **v7.5** · 25/25 mejoras implementadas · 433 tests · Python 3.11+

---

## En Pocas Palabras

**ANDROMEDA** es un asistente de inteligencia artificial que se conecta directamente a tu ERP Odoo y te deja hablarle como si fuera un compañero de trabajo. Le preguntas en español cosas como _"¿Cómo van las ventas del mes por marca?"_ o _"¿Tengo facturas atoradas?"_ y él se encarga de ir a la base de datos, sacar los números, analizarlos, detectar si algo anda mal, y responderte con tablas, gráficas y hasta un Excel descargable.

No necesitas saber SQL, ni Python, ni la estructura de Odoo. Solo escribe lo que necesitas saber.

**¿Qué hace por dentro?**

1. **Entiende lo que dices** — Un motor NLP (procesamiento de lenguaje natural) con 90+ intenciones detecta qué quieres: ventas, inventario, auditoría, predicciones, etc.
2. **Elige al experto correcto** — Un sistema de 13 agentes especializados (ventas, finanzas, inventario, CRM, RRHH, predicciones, estadística, etc.) se activa dependiendo de tu pregunta. Si la pregunta es compleja, se activan varios en cadena.
3. **Consulta Odoo en tiempo real** — Va directamente a tu base de datos Odoo (40+ modelos: ventas, POS, facturas, inventario, compras, CRM, RRHH) y trae los datos frescos.
4. **Analiza con IA** — Opcionalmente usa un LLM local (Ollama + Llama 3.2 / Mistral) para análisis más profundos, sin enviar tus datos a la nube.
5. **Recuerda contexto** — Memoria vectorial (ChromaDB) + grafo de conocimiento (NetworkX) + memoria jerárquica le permiten recordar conversaciones pasadas y conectar conceptos de tu negocio.
6. **Genera reportes** — Excel profesional, PDF con ReportLab, gráficas interactivas con Plotly/Matplotlib, todo descargable.
7. **Predice el futuro** — Machine Learning (scikit-learn), redes neuronales LSTM (PyTorch) y análisis estadístico para predecir ventas, detectar clientes en riesgo de churn, y alertar sobre inventario que se va a agotar.
8. **Audita tu información** — Auditoría de calidad de datos con triple validación (procesos huérfanos, registros zombi, datos incompletos), auditoría de anomalías financieras (fraude, descuentos excesivos, transacciones sospechosas).

**¿Qué NO es ANDROMEDA?** No es un chatbot genérico. No usa APIs externas como ChatGPT o Google. Todo corre en tu máquina. Tus datos nunca salen de tu servidor.

## Tabla de Contenido

1. [Arquitectura](#arquitectura)
2. [Stack Tecnológico](#stack-tecnológico)
3. [Capacidades Técnicas](#capacidades-técnicas)
4. [Pipeline de Ejecución](#pipeline-de-ejecución)
5. [Seguridad y Auditoría de Código](#seguridad-y-auditoría-de-código)
6. [Requisitos del Sistema](#requisitos-del-sistema)
7. [Instalación](#instalación)
8. [Testing](#testing)
9. [Estructura del Proyecto](#estructura-del-proyecto)
10. [Documentación UML](#documentación-uml)
11. [Despliegue](#despliegue)
12. [Troubleshooting](#troubleshooting)

## Arquitectura

Arquitectura híbrida: **Layered Modular Application** con pipeline cognitivo **RAG + Agentic Workflow** superpuesto.

### Capa Aplicativa

| Capa | Responsabilidad | Componentes clave |
|------|----------------|-------------------|
| **Presentación** | Interfaz, formateo, I/O | `InterfazAndromeda` (Gradio Blocks), `FormateadorRespuestas` (41 métodos), audio/file handlers |
| **Orquestación** | Routing, cadenas multi-agente, validación | `OdooBotPro`, `GestorMultiAgente` (13 agentes), `ValidadorFinal` |
| **Servicios** | Lógica de dominio (ML/DL, NLP, BI, auditoría) | 25+ clases, 12 ejecutores dedicados por agente |
| **Integración** | Comunicación ERP | `ConectorOdoo` (OdooRPC / XML-RPC), 40+ modelos, cache de conexión |
| **Persistencia** | Almacenamiento vectorial, grafos, estado | ChromaDB (6 col.), SQLite (logs), NetworkX DiGraph, JSON |

### Capa Cognitiva (RAG + Agentic)

```
Input → Normalización → NLP (intención + entidades) → Agent Routing
  → Pre-Validación → Ejecución Odoo → Enriquecimiento Determinístico
  → Validación Triple → Regeneración Condicional → Output
```

| Componente | Implementación | Detalle |
|-----------|---------------|--------|
| Embedding Engine | `paraphrase-multilingual-MiniLM-L12-v2` | 384d, multilingüe, cache SHA-256 auto-invalidante |
| Semantic Store | ChromaDB | 6 colecciones, EF lazy post-init, max 10K docs/col, purga selectiva |
| Knowledge Graph | NetworkX DiGraph | 14 tipos nodo, 9 relaciones, poda proactiva, decay 90d, límites 500/2000 |
| Prompt Builder | Dinámico | Inyección: memoria vectorial + grafo + datos Odoo real-time |
| LLM Backend | Ollama local | Llama 3.2, Mistral, DeepSeek-R1:8b — zero data egress |
| Query Generator | `GeneradorQueries` | NL → Query Odoo, guardrails: `CAMPOS_PROHIBIDOS` + `MODELOS_PROHIBIDOS` |

## Stack Tecnológico

| Capa | Tecnología | Especificación |
|------|-----------|----------------|
| Runtime | Python 3.11+ | Tipado estricto en interfaces públicas |
| ERP | OdooRPC (XML-RPC) | Odoo 17, 40+ modelos mapeados |
| LLM | Ollama | Llama 3.2, Mistral, DeepSeek-R1:8b |
| NLP | spaCy (`es_core_news_sm`) + SentenceTransformers | Pipeline lingüístico + embeddings semánticos |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` | 384d, cache SHA-256, auto-invalidación por cambio de corpus |
| Vector Store | ChromaDB (persistente) | 6 colecciones, max 10K docs/col, purga selectiva |
| Knowledge Graph | NetworkX DiGraph | 500 nodos max, 2000 aristas max, decay 90 días |
| ML | scikit-learn | Random Forest, K-Means, Isolation Forest |
| Deep Learning | PyTorch | LSTM 2 capas, 64 hidden units, dropout 0.2 |
| Visualización | Plotly + Matplotlib | Interactivas (HTML embed) + estáticas (PDF embed) |
| Reportes | OpenPyXL + ReportLab | Excel multi-hoja + PDF profesional |
| UI | Gradio Blocks | Chat + sidebar + audio + file download, `127.0.0.1:7860` |
| Logging | SQLite + RotatingFileHandler | Métricas operativas, `FiltroCredenciales` para redacción |
| Conocimiento | python-docx → JSON | Extracción de manuales corporativos con imágenes |

## Capacidades Técnicas

### Integración Odoo

Conexión directa vía OdooRPC (XML-RPC) contra Odoo 17. Soporte para 40+ modelos (`sale.order`, `account.move`, `stock.picking`, `purchase.order`, `crm.lead`, `hr.employee`, `pos.order`, etc.). Consultas ejecutadas en tiempo real por cada request — sin réplica local de datos. Autenticación segura mediante `API_KEY` almacenada en `.env`. Cache de conexión para evitar handshakes redundantes.

### Sistema Multi-Agente

Orquestación de **13 agentes** (12 de dominio + 1 validador) con **routing de 3 niveles** de prioridad (acción directa → sugerencia del router → clasificación por prompt LLM):

| Agente | Dominio | Executor Backend |
|--------|---------|-----------------|
| Ventas | Análisis comercial, top productos/clientes, comparativas período | `AnalizadorAvanzado` (25+ métodos) |
| Inventarios | Stock, rotación, reorden, movimientos, Just-in-Time | `ConsultasEspecializadas` (12+ queries) |
| Finanzas | CxC/CxP, flujo de caja, morosidad, facturación | `KPIsFinancieros` |
| Diagnóstico | Anomalías, fraude, salud del sistema | `AnalizadorAnomalias` |
| Consultas Odoo | Modelos, usuarios, proyectos, configuración | `ConectorOdoo` (directo) |
| CRM | Pipeline, leads, conversión, churn, retención | `Analizador360` |
| Compras | Procurement, proveedores, costeo, adquisiciones | `ConsultasEspecializadas` |
| PDV | Sesiones POS, caja, métodos de pago | `AnalizadorAvanzado` |
| Predicciones | Monte Carlo, LSTM, forecast, series temporales | `PrediccionInteligente` |
| Matemáticas | ROI, TIR, VPN, márgenes, break-even, amortización | `MotorBIExperto` |
| Estadística | 360°, correlación, segmentación, KPIs, Pareto, RFM | `Analizador360` |
| RRHH | Nómina, headcount, asistencia, contratos, rotación | `ConsultasEspecializadas` |
| ValidadorFinal | Gatekeeper: verifica respuesta vs pregunta original | Pipeline interno |

**Ejecución en cadena multi-agente:** Un prompt activa N agentes colaborativos, cada uno ejecuta su propio paso con executor dedicado (no solo valida). Confianza consolidada: `(principal × 2 + soporte × 1 + validador × 1.5) / Σ pesos`.

**Pipeline Anti-Alucinación — 4 capas:**

| Capa | Momento | Acción |
|:----:|---------|--------|
| 1 | Pre-ejecución | Auto-validación de campos, auto-relleno de parámetros faltantes |
| 2 | Post-ejecución | Verificación de coherencia entre datos retornados y respuesta |
| 3 | ValidadorFinal | Gatekeeper independiente: respuesta ↔ pregunta original |
| 4 | Regeneración | Confianza < 78% → regenera automáticamente (máx. ×3) |

**Métricas del sistema:** 120+ acciones mapeadas a agentes · 212+ keywords de clasificación · 95+ reglas de encadenamiento · 107+ mapeos directos Odoo.

### Motor NLP

| Componente | Clase | Función |
|-----------|-------|---------|
| Detección de intenciones | `MotorNLPAvanzado` | 90+ intenciones vía `intenciones_extendidas.py` |
| Análisis lingüístico | `CerebroNLP` + spaCy | Tokenización, POS tagging, NER, dependencias |
| Extracción de entidades | `ExtractorEntidades` | Fechas, filtros, modelos, marcas, clientes, tiendas |
| Embeddings semánticos | `MotorEmbeddings` | MiniLM-L12-v2 (384d), cache SHA-256, auto-invalidación por corpus |
| Motor empático | `MotorEmpatico` | Detección de estado emocional (frustración, confusión, humor) |
| Normalización | `NormalizadorPrompt` | Corrección de typos, expansión de abreviaciones, resolución de sinónimos |

### Predicción (ML + Deep Learning)

| Modelo | Framework | Aplicación |
|--------|-----------|------------|
| Random Forest | scikit-learn | Predicción de ventas (7-30d), scoring de churn |
| K-Means | scikit-learn | Segmentación de clientes (clusters comportamentales) |
| Isolation Forest | scikit-learn | Detección de anomalías en transacciones |
| LSTM (2 capas) | PyTorch | Series temporales, tendencias de venta |
| Monte Carlo | Implementación propia | Intervalos de confianza sobre predicciones |

Sistema híbrido ML + DL con evaluación de confianza cruzada. Predicción de ventas, agotamiento de inventario y riesgo de morosidad con horizonte configurable.

### Auditoría

**Auditoría Nocturna Automática:** Ejecución programada sobre la totalidad de la base Odoo. Detección de facturas $0, stock negativo, pagos duplicados, predicción de churn y alertas de reposición de inventario.

**Auditoría de Calidad de Datos — Triple Validación:**

| Fase | Tipo | Hallazgos |
|:----:|------|-----------|
| 1 | Estado vs Vínculo | Facturas con pago incompleto, ventas sin facturar, pickings sin origen, pagos sin conciliar |
| 2 | Tiempo de Vida / SLA | Facturas draft estancadas, cotizaciones abandonadas, OC sin movimiento, CRM sin actividad |
| 3 | Datos Incompletos | Clientes sin contacto, productos sin precio, facturas $0, líneas sin producto |

Enriquecimiento automático por hallazgo: empresa, unidad operativa y usuario creador. Output: Excel profesional de 8 hojas (Resumen, Hallazgos, Categoría, Severidad, Modelo, Empresa, Unidad Operativa, Top Usuarios) con porcentaje de datos confiables vs basura.

### Análisis y Business Intelligence

- **Análisis 360°** por entidad (marca, producto, cliente, proveedor, vendedor) con desgloses dimensionales
- **Detección de anomalías** financieras con Isolation Forest + Z-Score
- **30+ KPIs empresariales** (comerciales, talento, operaciones, retail)
- **Dashboard ejecutivo financiero** (ventas, rentabilidad, liquidez, eficiencia, riesgo)
- **Motor BI** con scoring de outliers y alertas automáticas

### Memoria y Conocimiento

**Memoria Vectorial — ChromaDB**

| Propiedad | Valor |
|-----------|-------|
| Colecciones | `conversaciones`, `analisis`, `errores`, `alertas`, `reportes`, `conocimiento` |
| Embedding Function | `SentenceTransformerEmbeddingFunction` (aplicación lazy post-init) |
| Límite por colección | 10,000 documentos |
| Purga | Selectiva por colección |
| Persistencia | `data/memoria/chroma.sqlite3` |

**Grafo de Conocimiento — NetworkX**

| Propiedad | Valor |
|-----------|-------|
| Estructura | DiGraph |
| Tipos de nodo (`TipoNodo`) | 14: CLIENTE, PRODUCTO, PROVEEDOR, EMPLEADO, FACTURA, ORDEN, ACCION, INTENCION, PERIODO, MONTO, CATEGORIA, TIENDA, ALMACEN, ANALISIS |
| Tipos de relación (`TipoRelacion`) | 9: CONSULTO, INVOLUCRA, PERIODO_DE, COMPRA, PROVEE, VENDE, RELACIONADO, CONTIENE, RESULTADO |
| Límites | 500 nodos, 2000 aristas |
| Decay | 90 días |
| Poda | Nodos huérfanos (sin aristas, accesos < 2) cuando grafo > 10 nodos |
| Persistencia | Auto-save cada 5 interacciones (contador determinístico) |

**Memoria Jerárquica:** Tres niveles — sesión (últimas 25 interacciones) + contexto operacional + preferencias de usuario (persistentes entre sesiones). Sanitización automática de metadatos para compatibilidad ChromaDB (solo `str`, `int`, `float`, `bool`).

**Extractor de Entidades:** Parseo automático de entidades desde mensajes, DataFrames y parámetros de ejecución para alimentar relaciones en el grafo.

### Motor LLM

Integración con Ollama para inferencia 100% local (**zero data egress**):

| Aspecto | Detalle |
|---------|---------|
| Modelos | Llama 3.2, Mistral, DeepSeek-R1:8b |
| NL → Query | `GeneradorQueries` convierte lenguaje natural a queries técnicas Odoo |
| Contexto | Prompts dinámicos con inyección de datos Odoo + memoria vectorial + grafo |
| Seguridad | `CAMPOS_PROHIBIDOS` (password, tokens, OAuth) · `MODELOS_PROHIBIDOS` (ir.config_parameter, ir.cron, etc.) |

### Gestión de Manuales

Procesamiento de documentos `.docx` corporativos: extracción de texto e imágenes (python-docx), indexación a JSON para búsqueda semántica. Consultas en lenguaje natural devuelven pasos relevantes con capturas asociadas.

### Interfaz

| Funcionalidad | Implementación |
|--------------|----------------|
| Framework UI | Gradio Blocks (diseño tipo ChatGPT) |
| Chat | Texto libre + botones de acciones rápidas (prompts predefinidos) |
| Navegación | Sidebar con módulos Odoo |
| Entrada por voz | Google Speech Recognition |
| Reportes | Excel (OpenPyXL) + PDF (ReportLab), descarga directa |
| Gráficas | Plotly (interactivas) + Matplotlib (estáticas para PDF) |
| Binding | `127.0.0.1:7860` (acceso local exclusivo) |

## Pipeline de Ejecución

Flujo completo desde input en lenguaje natural hasta respuesta enriquecida con datos reales:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE ANDROMEDA — 9 PASOS                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. 💬 ENTRADA LIBRE                                                    │
│     Usuario escribe: "¿Cómo van las ventas por marca y su tendencia?"  │
│                              ↓                                          │
│  2. 🔧 NORMALIZACIÓN                                                    │
│     Corrige typos, abreviaciones, normaliza texto                       │
│                              ↓                                          │
│  3. 🧠 NLP ANALIZA                                                      │
│     cerebro_nlp.entender() → intención + acción + parámetros + confianza│
│     (Opcionalmente Ollama enriquece la detección)                       │
│                              ↓                                          │
│  4. 🕵️ SELECCIÓN DE AGENTE(S)                                           │
│     GestorMultiAgente.resolver_agente() → agente principal              │
│     Si detecta múltiples cosas → activa CADENA MULTI-AGENTE            │
│     (ej: Ventas + Estadística + Predicciones)                           │
│                              ↓                                          │
│  5. ✅ PRE-VALIDACIÓN                                                    │
│     Cada agente enriquece la consulta: auto-rellena fechas, valida      │
│     campos, ajusta parámetros según su expertise                        │
│                              ↓                                          │
│  6. ⚡ EJECUCIÓN REAL                                                    │
│     Executor dedicado por agente consulta Odoo (107+ mapeos directos)   │
│     Usa backends ricos: AnalizadorAvanzado, ConsultasEspecializadas,    │
│     Predictor, Analizador360, MotorBI, MotorKPIs                       │
│     En cadena: cada agente soporte ejecuta su propio paso               │
│                              ↓                                          │
│  7. 📊 ENRIQUECIMIENTO                                                   │
│     enriquecer_respuesta() añade análisis determinístico sobre          │
│     datos reales (Pareto, concentración, promedios, anomalías)          │
│                              ↓                                          │
│  8. 🛡️ VALIDACIÓN TRIPLE + REGENERACIÓN                                 │
│     Capa 1: Agente de dominio valida coherencia                         │
│     Capa 2: ValidadorFinal verifica respuesta vs pregunta               │
│     Capa 3: Si confianza < 78% → REGENERA hasta 3 veces                │
│                              ↓                                          │
│  9. 📋 RESPUESTA AL USUARIO                                              │
│     Texto enriquecido + tabla HTML + indicador (agente + confianza %)   │
│     + Excel/PDF descargable (si aplica) + resumen de cadena             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Requisitos del Sistema

| Requisito | Mínimo |
|-----------|--------|
| Python | 3.11+ |
| RAM | 8 GB |
| Dependencias | `requirements.txt` (rangos acotados) |
| Ollama | Opcional — requerido solo para funcionalidades LLM |

## Instalación

```bash
git clone https://github.com/tuusuario/ANDROMEDA.git
cd ANDROMEDA
pip install -r requirements.txt
```

Configurar entorno:

```bash
cp .env.example .env
# Editar .env con credenciales Odoo (URL, DB, USER, API_KEY)
```

Iniciar:

```bash
python main.py web    # Interfaz web → http://localhost:7860
python main.py        # Modo consola
```

## Seguridad y Auditoría de Código

Auditoría integral completada: **19/19 hallazgos originales + 25 mejoras acumuladas en v7.5**.

| Categoría | Items | Estado |
|-----------|:-----:|--------|
| 🔴 Seguridad (críticos) | 5+4 | ✅ Resueltos — Credenciales a `.env`, logs purgados, `.gitignore`, bind `127.0.0.1`, fix inyección, **guardrail mutación expandido**, **CAMPOS_PROHIBIDOS**, **MODELOS_PROHIBIDOS**, **typo Sself corregido en auditoría** |
| 🟠 Calidad (altos) | 3+5 | ✅ Resueltos — Bare excepts, logging, validación, **word boundary**, **advertencias al usuario**, **validador alucinaciones (20 patrones)**, **división por cero semántica**, **NaN crash en tablas HTML** |
| 🟡 Arquitectura/QA (medios) | 7+5 | ✅ Resueltos — God class refactorizada, ejecutores, odoorpc, deps, pytest, **ChromaDB auto-purga**, **KPI sort**, **resolución unificada agentes**, **sincronización memorias**, **cache NLP auto-invalidante** |
| 🟢 UX (bajos) | 4+2 | ✅ Resueltos — Type hints, `__pycache__`, Logging.py, build, **moneda dinámica**, **timeout embeddings** |
| 🔵 Embeddings/Grafos (v7.5) | 9 | ✅ Resueltos — **EF explícita ChromaDB (lazy)**, **hash cache sobre corpus real**, **purga selectiva por colección**, **validación dimensionalidad**, **poda proactiva huérfanos**, **auto-save predecible**, **sanitización metadatos**, **guardar_alerta con embeddings propios**, **limpieza socket** |

Detalle: [`AUDITORIA_MEJORAS.md`](AUDITORIA_MEJORAS.md) · [`MEJORAS.md`](MEJORAS.md)

### Controles de Seguridad

| Control | Implementación |
|---------|----------------|
| Credenciales | Aisladas en `.env` (python-dotenv), excluidas de VCS |
| Logging | `FiltroCredenciales` — redacción automática de datos sensibles |
| Red | Bind exclusivo `127.0.0.1` — sin exposición externa |
| Input | Truncamiento a 2,000 chars + rate limiting (30 req/min) |
| VCS | `.gitignore`: `.env`, logs, builds, cache, datos de memoria |
| LLM | `CAMPOS_PROHIBIDOS` + `MODELOS_PROHIBIDOS` como guardrails |

## Testing

```bash
python -m pytest tests/ -v
python -m pytest tests/ --cov=. --cov-report=term-missing
```

| Métrica | Valor |
|---------|-------|
| Total tests | 433 |
| Tiempo promedio | ~30s |
| Configuración | `pytest.ini` + `.coveragerc` |
| Archivos | 11 archivos de test (NLP, Odoo, Config, Core, Multi-Agente, Utils, Memory, Analysis, LLM, Grafo, Interfaz) |
## Estructura del Proyecto

```
ANDROMEDA/
│
├── app/                                # Configuración general
│   ├── __init__.py
│   ├── config.py                       # ConfiguracionOdoo, Config (.env con python-dotenv)
│   └── logging_config.py               # Logging centralizado: RotatingFileHandler, FiltroCredenciales, get_logger()
│
├── assets/                             # Recursos estáticos
│   └── logo.png
│
├── core/                               # Núcleo de negocio
│   ├── __init__.py
│   ├── bot_principal.py                # OdooBotPro — Motor principal del agente
│   ├── cerebro_andromeda.py            # CerebroAndromeda — Análisis avanzado, limpieza, estadística
│   └── motor_bi_experto.py             # MotorBIExperto — Business Intelligence, KPIs, anomalías
│
├── data/                               # Datos persistentes
│   ├── memoria_bot.json                # Memoria del bot
│   ├── manuales/                       # Manuales empresariales
│   │   ├── imagenes/                   # Imágenes extraídas de manuales
│   │   └── indice_conocimiento.json    # Índice de búsqueda de manuales
│   ├── memoria/                        # Base de datos vectorial
│   │   └── chroma.sqlite3              # ChromaDB para embeddings
│   └── reportes/                       # Reportes generados
│
├── docs/                               # Documentación técnica
│   ├── CONFIGURACION_OLLAMA.md         # Guía de configuración de Ollama
│   ├── SISTEMA_HIBRIDO_GRAFICAS.md     # Documentación del sistema de gráficas
│   └── UML_ANDROMEDA.md                # Diagramas UML (Clases, Secuencia, Componentes)
│
├── models/                             # Modelos y conexión con Odoo
│   ├── __init__.py
│   ├── conector_odoo.py                # ConectorOdoo — Conexión odoorpc, cache, DataFrame, search_read()
│   └── modelos_odoo.py                 # ModeloOdoo — Definición de 40+ modelos Odoo
│
├── scripts/                            # Scripts de inicio para Windows
│   ├── INICIAR_BOT_CONSOLA.bat
│   ├── INICIAR_BOT_WEB.bat
│   └── INSTALAR_DEPENDENCIAS.bat
│
├── services/                           # Servicios especializados (ML, DL, NLP, BI)
│   ├── __init__.py
│   ├── auditoria_inteligente.py        # AuditoriaInteligente — Nocturna, churn, reposición
│   ├── auditoria_calidad_datos.py      # AuditoriaCalidadDatos — Triple validación + Excel
│   │
│   ├── agents/                         # Sistema Multi-Agente (13 agentes + cadena + ejecutores)
│   │   ├── __init__.py
│   │   ├── multi_agente.py             # GestorMultiAgente, 12 Agentes + ValidadorFinal, Cadena con ejecución real
│   │   └── ejecutores.py               # EjecutoresAgente — 12 ejecutores dedicados (extraídos de interfaz_v5)
│   │
│   ├── analysis/                       # Análisis especializado
│   │   ├── __init__.py
│   │   ├── analisis_360.py             # Analizador360, DetectorEntidades
│   │   ├── analisis_inteligente.py     # DetectorContexto — Agrupaciones y comparativas
│   │   ├── analizador_anomalias.py     # AnalizadorAnomalias — Fraude, riesgos
│   │   ├── analizador_avanzado.py      # AnalizadorAvanzado — Ventas, POS, comparativas
│   │   ├── analizador_datos.py         # AnalizadorDatos — Estadísticas básicas
│   │   ├── kpis_empresariales.py       # MotorKPIsEmpresariales — 30+ KPIs
│   │   └── kpis_financieros.py         # KPIsFinancieros — Dashboard ejecutivo
│   │
│   ├── formatters/                     # Formateo de respuestas (extraído de interfaz_v5)
│   │   ├── __init__.py
│   │   └── formateador_respuestas.py   # FormateadorRespuestas — 41 métodos de formateo Markdown
│   │
│   ├── knowledge/                      # Gestión de conocimiento
│   │   ├── __init__.py
│   │   └── procesador_manuales.py      # ProcesadorManuales — Indexa .docx a JSON
│   │
│   ├── llm/                            # Integración con LLM (Ollama)
│   │   ├── __init__.py
│   │   ├── cerebro_llm.py              # AgenteAndromeda — Orquestador LLM
│   │   ├── generador_queries.py        # GeneradorQueries — NL → Query Odoo
│   │   └── ollama_integrador.py        # ConectorOllama — Conexión con Ollama
│   │
│   ├── memory/                         # Memoria y contexto
│   │   ├── __init__.py
│   │   ├── memoria_vectorial.py        # MemoriaVectorial — ChromaDB 6 colecciones, EF explícita (lazy), purga selectiva
│   │   ├── memoria_jerarquica.py       # MemoriaJerarquica — Sesión + contexto + preferencias + sanitización metadatos
│   │   └── grafo_conocimiento.py       # GrafoConocimiento — NetworkX DiGraph, 14 tipos nodo, 9 relaciones, poda proactiva
│   │
│   ├── nlp/                            # Procesamiento de Lenguaje Natural
│   │   ├── __init__.py
│   │   ├── cerebro_nlp.py              # CerebroNLP — Procesamiento lingüístico avanzado
│   │   ├── motor_empatico.py           # MotorEmpatico — Respuestas empáticas contextuales
│   │   ├── motor_nlp.py                # MotorNLP — Detección de intenciones base
│   │   ├── motor_embeddings.py         # MotorEmbeddings — paraphrase-multilingual-MiniLM-L12-v2, cache auto-invalidante
│   │   └── nlp_avanzado.py             # MotorNLPAvanzado — NLP avanzado con 90+ intenciones
│   │
│   ├── prediction/                     # Predicción y ML/DL
│   │   ├── __init__.py
│   │   ├── motor_ml.py                 # MotorML — Machine Learning (scikit-learn)
│   │   ├── motor_prediccion.py         # MotorPrediccion — Predicciones básicas
│   │   ├── neural_lstm.py              # MotorNeuralLSTM — Redes LSTM (PyTorch)
│   │   └── prediccion_inteligente.py   # SistemaPrediccionInteligente — Sistema híbrido
│   │
│   └── reports/                        # Generación de reportes
│       ├── __init__.py
│       ├── generador_graficas.py       # GeneradorGraficas — Matplotlib / Plotly
│       └── generador_pdf.py            # GeneradorPDF — PDFs con ReportLab
│
├── tests/                              # Suite de tests (433 tests)
│   ├── test_cerebro_nlp.py             # Tests NLP
│   ├── test_conector_odoo.py           # Tests Conector Odoo
│   ├── test_config.py                  # Tests Configuración
│   ├── test_core.py                    # Tests Core (bot_principal, cerebro_andromeda)
│   ├── test_interfaz_reportes.py       # Tests Interfaz + Reportes
│   ├── test_multi_agente.py            # Tests Multi-Agente
│   └── test_utils.py                   # Tests Utilidades
│
├── utils/                              # Utilidades y validación
│   ├── __init__.py
│   ├── asistente_errores.py            # AsistenteErroresOdoo — Diagnóstico de errores
│   ├── consultas_especializadas.py     # ConsultasEspecializadas — Queries complejas (12+ métodos)
│   ├── intenciones_extendidas.py       # INTENCIONES_EXTENDIDAS — 90+ intenciones mapeadas
│   ├── logging_avanzado.py             # LoggerAvanzado — Logging con SQLite y análisis avanzado
│   ├── monitor_sistema.py              # MonitorSistema — Monitoreo y estadísticas
│   ├── normalizador_prompt.py          # NormalizadorPrompt — Corrección de typos/abreviaciones
│   ├── validador_datos.py              # ValidadorDatos — Validación y autocorrección
│   └── validador_respuestas.py         # ValidadorRespuestas — Verificación respuesta vs pregunta
│
├── views/                              # Capa de presentación
│   ├── __init__.py
│   ├── generador_reportes.py           # GeneradorReportes — Excel, PDF, HTML profesionales
│   └── interfaz_v5.py                  # InterfazAndromeda — Interfaz Gradio + pipeline completo (delega a FormateadorRespuestas y EjecutoresAgente)
│
├── Reportes_Bot/                       # Carpeta de reportes generados automáticamente
│
├── __init__.py
├── main.py                             # Punto de entrada (web / consola)
├── cli_monitor.py                      # CLI de monitoreo y logging
├── INSTALAR_CEREBRO_LLM.bat            # Instalador de Ollama + modelos
├── requirements.txt                    # Dependencias Python (fijadas con rangos)
├── pytest.ini                          # Configuración pytest (markers, coverage)
├── .coveragerc                         # Configuración de cobertura
├── .gitignore                          # Exclusiones git (.env, logs/, build/, etc.)
├── .env.example                        # Plantilla de variables de entorno
├── AUDITORIA_MEJORAS.md                # Auditoría integral (19/19 resueltos)
└── README.md
```

## Documentación UML

Diagramas técnicos completos en [`docs/UML_ANDROMEDA.md`](docs/UML_ANDROMEDA.md):

| Diagrama | Alcance |
|----------|---------|
| Clases | 50+ clases, atributos, métodos, relaciones (composición, herencia, agregación, delegación) |
| Secuencia (Consulta) | Pipeline 24 pasos: NLP → MultiAgente → Ejecutor → Enriquecimiento → Validación ×3 |
| Secuencia (Cadena) | Ejecución real multi-agente: ejecuta → enriquece → valida → consolida |
| Secuencia (Auditoría) | Triple validación: Huérfanos → Zombis → Incompletos → Enriquecimiento → Excel |
| Componentes | Arquitectura por capas, módulos, formatters, ejecutores, sistemas externos |

> Visualización: extensión "Markdown Preview Mermaid Support" en VS Code, o directamente en GitHub.
## Despliegue

### Inicialización del repositorio

```bash
cd ANDROMEDA
git init
git add .
git commit -m "Initial commit: ANDROMEDA v7.5"
```

### Push a remoto

```bash
git remote add origin https://github.com/USER/ANDROMEDA.git
git branch -M main
git push -u origin main
```

El `.gitignore` incluido excluye: `.env`, `.venv/`, `__pycache__/`, `logs/`, `build/`, `data/memoria/`, `Reportes_Bot/`, `reports/`, `.pytest_cache/`.

---

## Troubleshooting

| Síntoma | Resolución |
|---------|-----------|
| **Ollama Connection Error** | Verificar que el servicio Ollama esté activo (`ollama serve`). Endpoint: `http://localhost:11434` |
| **OdooRPC Authentication** | Revisar URL, base de datos y credenciales en `.env` / `app/config.py` |
| **Gradio Port Conflict** | Modificar puerto en `interfaz_v5.py`: `demo.launch(server_port=XXXX)` |
| **CUDA Memory Error** | Reducir tamaño del modelo en Ollama o forzar modo CPU |
| **Docx Reading Error** | Cerrar el `.docx` en Word antes de que ANDROMEDA lo procese |
| **ChromaDB Lock** | Cerrar todas las instancias de ANDROMEDA y reiniciar |
| **Import Error** | Ejecutar `pip install -r requirements.txt` para resolver dependencias |


---

## Autor

**Ing. Axel Gutiérrez** — Tech Lead | Software Engineer

[LinkedIn](https://www.linkedin.com/in/axel-ismael-gutierrez-gutierrez-01b959333) · [Portfolio](https://ingenieroaxelgutierrez-art.github.io/Portafolio/)