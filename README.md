<p align="center">
  <img src="./frontend/public/logo.png" alt="ANDROMEDA" width="28%">
</p>

<h1 align="center">ANDROMEDA</h1>
<h3 align="center">Advanced Neural Data Resource for Operations, Management &amp; Enterprise Decision Analytics</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.133-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js-14.2-000000?logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Tests-695%20passing-22c55e?logo=pytest&logoColor=white" alt="Tests">
  <img src="https://img.shields.io/badge/Ollama-local%20LLM-FF6B35" alt="Ollama">
  <img src="https://img.shields.io/badge/Odoo-14%20→%2019+-714B67?logo=odoo&logoColor=white" alt="Odoo">
  <img src="https://img.shields.io/badge/i18n-ES%20%7C%20EN%20%7C%20JA-8B5CF6" alt="i18n">
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="License">
</p>

<p align="center">
  <b>🌐 Language / 言語:</b>&nbsp;
  <a href="#versión-en-español">Español</a> &nbsp;|&nbsp;
  <a href="#日本語版">日本語</a>
</p>


---

# Versión en Español

## Descripción

ANDROMEDA es un agente conversacional de IA de propósito empresarial que se conecta directamente a instancias Odoo y responde consultas en **lenguaje natural** sobre datos de negocio en tiempo real. Combina un pipeline NLP multi-capa, orquestación multi-agente con 13 agentes de dominio, RAG con memoria vectorial persistente, ML/DL híbrido, **soporte multiidioma nativo (ES · EN · JA)** y una API REST con frontend React — **100 % local, zero data egress**.

---

## Tabla de Contenido

1. [Arquitectura del sistema](#1-arquitectura-del-sistema)
2. [Sistema multiidioma](#2-sistema-multiidioma)
3. [Stack tecnológico](#3-stack-tecnológico)
4. [Pipeline de ejecución](#4-pipeline-de-ejecución)
5. [Sistema multi-agente](#5-sistema-multi-agente)
6. [Motor NLP](#6-motor-nlp)
7. [Memoria y conocimiento](#7-memoria-y-conocimiento)
8. [Motor LLM (Ollama)](#8-motor-llm-ollama)
9. [Predicción ML/DL](#9-predicción-mldl)
10. [Auditoría de datos](#10-auditoría-de-datos)
11. [Capa API REST (FastAPI)](#11-capa-api-rest-fastapi)
12. [Frontend (Next.js 14)](#12-frontend-nextjs-14)
13. [Seguridad](#13-seguridad)
14. [Estructura del proyecto](#14-estructura-del-proyecto)
15. [Instalación y configuración](#15-instalación-y-configuración)
16. [Docker](#16-docker)
17. [Testing](#17-testing)
18. [Despliegue](#18-despliegue)
19. [Troubleshooting](#19-troubleshooting)

---

## 1. Arquitectura del sistema

ANDROMEDA implementa una arquitectura **Layered Modular Application** con un pipeline cognitivo **RAG + Agentic Workflow** superpuesto. La separación de responsabilidades es estricta: ninguna capa inferior importa de capas superiores.

### Capas aplicativas

```
┌─────────────────────────────────────────────────────────────────┐
│  PRESENTACIÓN   Gradio Blocks · Next.js 14 · FastAPI REST       │
├─────────────────────────────────────────────────────────────────┤
│  I18N           ES · EN · JA — ContextVar propagation           │
├─────────────────────────────────────────────────────────────────┤
│  ORQUESTACIÓN   OdooBotPro · GestorMultiAgente (13 agentes)     │
├─────────────────────────────────────────────────────────────────┤
│  SERVICIOS      NLP · LLM · ML/DL · BI · Auditoría · Manuales  │
├─────────────────────────────────────────────────────────────────┤
│  INTEGRACIÓN    ConectorOdoo (OdooRPC/XML-RPC, 40+ modelos)     │
├─────────────────────────────────────────────────────────────────┤
│  PERSISTENCIA   ChromaDB · SQLite · NetworkX · JSON             │
└─────────────────────────────────────────────────────────────────┘
```

### Capa cognitiva (RAG + Agentic)

```
Input ──► Normalización ──► NLP (intención + entidades) ──► Agent Routing
  ──► Pre-Validación ──► Ejecución Odoo ──► Enriquecimiento
  ──► Validación Triple ──► Regeneración Condicional
  ──► Traducción i18n ──► Output final en idioma del usuario
```

| Componente | Implementación | Especificación |
|---|---|---|
| Embedding engine | `paraphrase-multilingual-MiniLM-L12-v2` | 384d, multilingüe, cache SHA-256 auto-invalidante |
| Semantic store | ChromaDB persistente | 6 colecciones, EF lazy post-init, max 10K docs/col |
| Knowledge graph | NetworkX DiGraph | 14 tipos nodo, 9 relaciones, decay 90d, poda proactiva, límites 500/2000 |
| Prompt builder | Dinámico | Inyección: memoria vectorial + grafo + datos Odoo real-time |
| LLM runtime | Ollama local | Llama 3.2, Mistral, DeepSeek-R1:8b — zero data egress |
| Query generator | `GeneradorQueries` | NL → Query Odoo; guardrails: `CAMPOS_PROHIBIDOS` + `MODELOS_PROHIBIDOS` |
| i18n propagation | `_ctx_idioma` ContextVar | Idioma inyectado una vez en el request; visible en toda la cadena de ejecución |

---

## 2. Sistema multiidioma

ANDROMEDA implementa soporte multiidioma completo (ES · EN · JA) en tres capas independientes. El idioma se propaga como `ContextVar` sin necesidad de pasar parámetros explícitos por la cadena de llamadas.

### 2.1 Propagación del idioma

```python
# models/conector_odoo.py
_ctx_idioma: ContextVar[str] = ContextVar("_ctx_idioma", default="es")

# app/api/routers/chat.py  — se establece una vez al inicio del request
idioma: str = request.idioma or "es"
_token_idioma = _ctx_idioma.set(idioma)
_ctx_copy = contextvars.copy_context()   # copia hacia todos los ejecutores
```

Cualquier capa del sistema puede leer el idioma activo sin acoplamiento:

```python
from models.conector_odoo import _ctx_idioma
idioma = _ctx_idioma.get()   # disponible en formatters, agentes, manuales, etc.
```

### 2.2 Textos de envoltura — `FormateadorConclusiones`

El texto wrapper que ANDROMEDA genera alrededor de los datos (contexto analítico, reconocimiento del dominio, cierre) se emite directamente en el idioma del usuario, sin post-procesamiento:

| Idioma | Muestra de reconocimiento de dominio |
|---|---|
| `es` | `📊 Analicé los datos de ventas del período. Los resultados son los siguientes:` |
| `en` | `📊 I analyzed the sales data for the period. Here are the results:` |
| `ja` | `📊 売上データを分析しました。結果は以下の通りです：` |

Implementación: `_DOMINIOS_I18N` — diccionario de tripletas `(es, en, ja)` para ~100 dominios de negocio.

### 2.3 Etiquetas de tablas y secciones — `labels_i18n.py`

`services/formatters/labels_i18n.py` traduce post-proceso todas las etiquetas que `FormateadorRespuestas` genera en español:

| Tipo | Cobertura |
|---|---|
| Reemplazos exactos | ~150 strings: encabezados `###`, columnas de tabla `\|…\|`, filas de métricas, alertas, call-to-action |
| Patrones regex | ~50 expresiones con grupos de captura para strings dinámicos con valores intercalados |

```python
from services.formatters.labels_i18n import traducir_etiquetas
texto_ja = traducir_etiquetas(texto_es, "ja")
```

La función se aplica en `_traducir_respuesta_datos()` como **Capa 1** (sin LLM, siempre activa). Si el LLM está habilitado actúa como **Capa 2** para traducir cualquier residuo no cubierto por el diccionario.

### 2.4 Manuales de Odoo — traducción completa por Google Translate

La base de conocimiento (índice del manual `.docx`) se pre-traduce en la **primera consulta** en un idioma no español y se persiste en el JSON de índice. Las consultas posteriores son instantáneas.

#### Flujo de búsqueda multiidioma

```
Query JA: "請求書をキャンセルするには？"
    │
    ▼
traducir_consulta_i18n("ja")
    → "cancelar anular cancelación factura facturas timbrado CFDI …"
    │
    ▼
buscar(consulta_es)  →  sección "CANCELACIÓN DE FACTURACIÓN TIMBRADA"  ✓
    │
    ▼
formatear_respuesta(idioma="ja")
    → titulo_ja / pasos_ja  (pre-traducidos vía Google Translate)
```

| Componente | Responsabilidad |
|---|---|
| `traducir_consulta_i18n(consulta, idioma)` | ~120 términos JA/EN → keywords ES para el índice (sin red) |
| `_traducir_google(texto, lang)` | Google Translate API gratuita (`client=gtx`), sin API key |
| `_traducir_pasos_batch(pasos, lang)` | Concatena textos con separador `\|\|\|S\|\|\|`, 1 sola llamada HTTP por sección |
| `traducir_indice(idioma)` | Pre-traduce todo el índice y guarda en `indice_conocimiento.json` |
| `tiene_traducciones(idioma)` | Check rápido para evitar re-traducciones en memoria |
| `SeccionManual.titulo_ja/en` | Campo cacheado en el JSON del índice |
| `SeccionManual.pasos_ja/en` | Lista de pasos traducidos, cacheada en el JSON |

#### Campos añadidos a `SeccionManual`

```python
@dataclass
class SeccionManual:
    # … campos originales …
    titulo_en: Optional[str] = None
    titulo_ja: Optional[str] = None
    pasos_en: List[Dict] = field(default_factory=list)
    pasos_ja: List[Dict] = field(default_factory=list)
```

#### Compatibilidad del índice

El cargador de índice filtra claves desconocidas para garantizar compatibilidad hacia adelante y hacia atrás:

```python
campos_validos = {f.name for f in SeccionManual.__dataclass_fields__.values()}
sec_filtrado = {k: v for k, v in sec_dict.items() if k in campos_validos}
self.secciones[id_seccion] = SeccionManual(**sec_filtrado)
```

### 2.5 Resumen de cobertura

| Componente | ES | EN | JA |
|---|:---:|:---:|:---:|
| Texto de contexto analítico (conclusiones) | ✅ | ✅ | ✅ |
| Etiquetas de tablas de datos | ✅ | ✅ | ✅ |
| Alertas e insights determinísticos | ✅ | ✅ | ✅ |
| Títulos de sección del manual | ✅ | ✅* | ✅* |
| Pasos del manual (contenido .docx) | ✅ | ✅* | ✅* |
| Estructura del manual (Step/ステップ) | ✅ | ✅ | ✅ |
| Búsqueda semántica en manual | ✅ | ✅ | ✅ |

*Pre-traducido vía Google Translate en primera consulta; cacheado en el índice JSON.

---

## 3. Stack tecnológico

| Capa | Tecnología | Versión / Especificación |
|---|---|---|
| Runtime | Python | 3.11+ |
| API backend | FastAPI + Uvicorn | 0.133.1 / 0.41.0 |
| Frontend | Next.js + TypeScript | 14.2.29 / 5.5 |
| ORM / BD SaaS | SQLAlchemy | 2.x — SQLite dev / PostgreSQL prod |
| Cifrado | cryptography (Fernet) | Clave derivada de `SECRET_KEY` via SHA-256 |
| Autenticación | python-jose + passlib | JWT HS256, pbkdf2_sha256 (OWASP) |
| ERP | OdooRPC (XML-RPC) | Odoo 14–19+, 40+ modelos |
| LLM runtime | Ollama | Llama 3.2, Mistral, DeepSeek-R1:8b |
| NLP | spaCy + SentenceTransformers | `es_core_news_sm` + MiniLM-L12-v2 (384d) |
| Vector store | ChromaDB | Persistente, 6 colecciones, EF explícita |
| Knowledge graph | NetworkX | DiGraph, poda proactiva, auto-save |
| ML | scikit-learn | Random Forest, K-Means, Isolation Forest |
| Deep learning | PyTorch | LSTM 2 capas, 64 hidden units, dropout 0.2 |
| i18n — diccionario | `labels_i18n.py` | ~200 traducciones ES→EN/JA (exactas + regex) |
| i18n — manuales | Google Translate API (`client=gtx`) | Gratuita, sin API key, via `requests` |
| Visualización | Plotly + Matplotlib | Interactivas (HTML) + estáticas (PDF) |
| Reportes | OpenPyXL + ReportLab | Excel multi-hoja + PDF profesional |
| UI debug | Gradio Blocks | Chat + sidebar + voz + file download |
| Contenedores | Docker + Compose | Dev (hot reload) + Prod (Gunicorn 2w + Next.js standalone) |
| Logging | SQLite + RotatingFileHandler | `FiltroCredenciales` para redacción automática |

---

## 4. Pipeline de ejecución

Flujo determinístico desde input en lenguaje natural hasta respuesta final en el idioma del usuario:

```
 1  INPUT LIBRE          "請求書をキャンセルするには？" / "Cancel invoice" / "¿Cómo cancelo?"
        │
 2  IDIOMA               request.idioma → _ctx_idioma.set() → ContextVar propagado
        │
 3  NORMALIZACIÓN        NormalizadorPrompt → typos, abreviaciones, sinónimos
        │
 4  NLP                  CerebroNLP + MotorNLPAvanzado → intención + acción
                         + entidades + confianza (spaCy + embeddings semánticos)
        │
 5  AGENT ROUTING        GestorMultiAgente.resolver_agente()
                         Si prompt multi-dominio → activa CADENA de agentes
        │
 6  PRE-VALIDACIÓN       Cada agente enriquece la consulta:
                         auto-rellena fechas, valida campos, ajusta parámetros
        │
 7  EJECUCIÓN ODOO       Executor dedicado por agente → consulta en tiempo real
                         107+ mapeos directos: AnalizadorAvanzado,
                         ConsultasEspecializadas, Predictor, Analizador360,
                         MotorBI, MotorKPIs
        │
 8  ENRIQUECIMIENTO      enriquecer_respuesta() → análisis determinístico:
                         Pareto, concentración, promedios, anomalías
        │
 9  VALIDACIÓN TRIPLE    Capa 1: agente de dominio verifica coherencia
    + REGENERACIÓN       Capa 2: ValidadorFinal — respuesta ↔ pregunta
                         Capa 3: confianza < 78% → regenera (máx. ×3)
        │
10  TRADUCCIÓN i18n      FormateadorConclusiones → wrapper en idioma destino
                         labels_i18n.traducir_etiquetas() → tablas y etiquetas
                         LLM (si disponible) → residuos no cubiertos
        │
11  OUTPUT               Texto + tabla Markdown + indicador (agente + confianza %)
                         TODO en el idioma del usuario · Excel/PDF descargable
```

---

## 5. Sistema multi-agente

Orquestación de **13 agentes** (12 de dominio + 1 validador) con routing de **3 niveles** de prioridad:

1. Acción directa mapeada (107+ mapeos)
2. Sugerencia del router por keyword (212+ keywords)
3. Clasificación semántica por embeddings

| Agente | Dominio | Backend |
|---|---|---|
| Ventas | Análisis comercial, top productos/clientes, comparativas | `AnalizadorAvanzado` (25+ métodos) |
| Inventarios | Stock, rotación, reorden, JIT, movimientos | `ConsultasEspecializadas` (12+ queries) |
| Finanzas | CxC/CxP, flujo de caja, morosidad, facturación | `KPIsFinancieros` |
| Diagnóstico | Anomalías, fraude, salud operativa | `AnalizadorAnomalias` |
| Consultas Odoo | Modelos, usuarios, proyectos, configuración | `ConectorOdoo` directo |
| CRM | Pipeline, leads, conversión, churn, retención | `Analizador360` |
| Compras | Procurement, proveedores, costeo | `ConsultasEspecializadas` |
| PDV | Sesiones POS, caja, métodos de pago | `AnalizadorAvanzado` |
| Predicciones | Monte Carlo, LSTM, forecast, series temporales | `SistemaPrediccionInteligente` |
| Matemáticas | ROI, TIR, VPN, márgenes, break-even | `MotorBIExperto` |
| Estadística | 360°, correlación, segmentación, Pareto, RFM | `Analizador360` |
| RRHH | Nómina, headcount, asistencia, rotación | `ConsultasEspecializadas` |
| ValidadorFinal | Gatekeeper — respuesta ↔ pregunta original | Pipeline interno |

**Confianza consolidada en cadena multi-agente:**

$$\text{confianza} = \frac{\text{principal} \times 2 + \text{soporte} \times 1 + \text{validador} \times 1.5}{\sum_i w_i}$$

**Pipeline anti-alucinación — 4 capas:**

| # | Momento | Acción |
|:---:|---|---|
| 1 | Pre-ejecución | Auto-validación de campos, auto-relleno de parámetros faltantes |
| 2 | Post-ejecución | Verificación de coherencia entre datos retornados y respuesta generada |
| 3 | ValidadorFinal | Gatekeeper independiente: respuesta ↔ pregunta original |
| 4 | Regeneración condicional | Confianza < 78% → regenera automáticamente (máx. ×3) |

---

## 6. Motor NLP

| Componente | Clase | Función |
|---|---|---|
| Detección de intenciones | `MotorNLPAvanzado` | 90+ intenciones via `INTENCIONES_EXTENDIDAS` |
| Análisis lingüístico | `CerebroNLP` + spaCy | Tokenización, POS tagging, NER, análisis de dependencias |
| Extracción de entidades | `ExtractorEntidades` | Fechas relativas, filtros, modelos Odoo, marcas, clientes, tiendas |
| Embeddings semánticos | `MotorEmbeddings` | MiniLM-L12-v2 (384d), cache `.npz` con hash SHA-256 auto-invalidante |
| Motor empático | `MotorEmpatico` | Detección de estado emocional del usuario (frustración, confusión, humor) |
| Normalización | `NormalizadorPrompt` | Corrección de typos, expansión de abreviaciones, resolución de sinónimos de negocio |

**Cache de embeddings:**
- Persistido en `data/embeddings_cache/` (`.npz` + `.json` de metadatos)
- Invalidación automática si: se añaden/eliminan intenciones **o** cambian las frases de entrenamiento (hash SHA-256 sobre corpus real)
- Validación de dimensionalidad al cargar: `shape[1] == modelo.get_sentence_embedding_dimension()`

---

## 7. Memoria y conocimiento

### Memoria vectorial — ChromaDB

| Propiedad | Valor |
|---|---|
| Colecciones | `conversaciones`, `analisis`, `errores`, `alertas`, `reportes`, `conocimiento` |
| Embedding function | `SentenceTransformerEmbeddingFunction` — aplicación lazy post-init |
| Límite por colección | 10,000 documentos |
| Purga | Selectiva por colección, documentos > 60 días al exceder límite |
| Persistencia | `data/memoria/chroma.sqlite3` |

### Grafo de conocimiento — NetworkX DiGraph

| Propiedad | Valor |
|---|---|
| Tipos de nodo (`TipoNodo`) | 14: CLIENTE, PRODUCTO, PROVEEDOR, EMPLEADO, FACTURA, ORDEN, ACCION, INTENCION, PERIODO, MONTO, CATEGORIA, TIENDA, ALMACEN, ANALISIS |
| Tipos de relación (`TipoRelacion`) | 9: CONSULTO, INVOLUCRA, PERIODO_DE, COMPRA, PROVEE, VENDE, RELACIONADO, CONTIENE, RESULTADO |
| Límites | 500 nodos · 2,000 aristas |
| Decay | 90 días |
| Poda proactiva | Nodos huérfanos sin aristas y accesos < 2, cuando grafo > 10 nodos |
| Auto-save | Cada 5 interacciones (contador determinístico); persistido en `data/memoria/grafo_conocimiento.json` |

### Memoria jerárquica

Tres niveles de persistencia:
1. **Sesión** — últimas 25 interacciones; contexto de conversación activa
2. **Contexto operacional** — estado de módulo y parámetros de la sesión actual
3. **Preferencias de usuario** — persistentes entre sesiones; preferencias de formato, moneda, idioma

Sanitización automática de metadatos para compatibilidad ChromaDB: solo tipos `str`, `int`, `float`, `bool`.

### Base de conocimiento — Manuales de Odoo

`ProcesadorManuales` indexa documentos `.docx` y construye un índice JSON con búsqueda semántica y soporte multiidioma completo:

- **Extracción**: secciones, pasos numerados, imágenes inline vía `python-docx`
- **Índice**: palabras clave ES ponderadas por frecuencia + índice invertido
- **Búsqueda contextual**: 8+ reglas de bonus/penalización (POS, kardex, cierre de mes, etc.)
- **Multiidioma**: pre-traducción de títulos y pasos vía Google Translate; cache en JSON

---

## 8. Motor LLM (Ollama)

Inferencia 100% local — **zero data egress**. Los datos de Odoo nunca salen del servidor.

| Aspecto | Detalle |
|---|---|
| Modelos soportados | Llama 3.2, Mistral, DeepSeek-R1:8b |
| NL → Query | `GeneradorQueries` convierte lenguaje natural a queries técnicas Odoo con validación de campos y modelos |
| Contexto | Prompts dinámicos: datos Odoo en tiempo real + memoria vectorial + grafo de conocimiento |
| Guardrails | `CAMPOS_PROHIBIDOS` (password, tokens, OAuth keys), `MODELOS_PROHIBIDOS` (ir.config_parameter, auth_totp, etc.) |
| Límite de registros | Máximo 500 por query generada por LLM |
| Configuración | Variable `OLLAMA_HOST` — por defecto `http://localhost:11434`; en Docker: `http://host.docker.internal:11434` |

---

## 9. Predicción ML/DL

Sistema híbrido con evaluación de confianza cruzada entre modelos:

| Modelo | Framework | Aplicación |
|---|---|---|
| Random Forest | scikit-learn | Predicción de ventas (7–30 días), scoring de riesgo de churn |
| K-Means | scikit-learn | Segmentación de clientes por comportamiento de compra |
| Isolation Forest | scikit-learn | Detección de anomalías en transacciones financieras |
| LSTM (2 capas, 64 hidden) | PyTorch | Series temporales, tendencias de venta a largo plazo |
| Monte Carlo | Implementación propia | Intervalos de confianza sobre predicciones de forecast |

Casos de uso: predicción de ventas, agotamiento de inventario, riesgo de morosidad, churn de clientes, reposición automática de stock.

---

## 10. Auditoría de datos

### Auditoría de calidad — Triple validación

| Fase | Tipo | Hallazgos detectados |
|:---:|---|---|
| 1 | Estado vs vínculo | Facturas con pago incompleto, ventas sin facturar, pickings sin origen, pagos sin conciliar |
| 2 | Tiempo de vida / SLA | Facturas draft estancadas, cotizaciones abandonadas, OC sin movimiento, CRM sin actividad |
| 3 | Datos incompletos | Clientes sin contacto, productos sin precio, facturas en $0, líneas sin producto asignado |

Output: Excel profesional de **8 hojas** (Resumen, Hallazgos, Categoría, Severidad, Modelo, Empresa, Unidad Operativa, Top Usuarios) con porcentaje de datos confiables vs basura. Enriquecimiento automático por hallazgo: empresa, unidad operativa, usuario creador.

### Auditoría nocturna automática

Ejecución programada sobre la totalidad de la base Odoo: detección de facturas $0, stock negativo, pagos duplicados, predicción de churn y alertas de reposición de inventario.

### Logging SIEM de queries

`services/security/auditoria_queries.py` registra cada query ejecutada contra Odoo en formato JSON por línea, compatible con ingestores SIEM. Campos: `modelo`, `filtros`, `campos`, `usuario`, `timestamp`, `duracion_ms`, `registros_retornados`, `hash_prompt`, `nivel`. Integrado en los métodos `buscar`, `buscar_leer` y `search_read` del `ConectorOdoo`.

---

## 11. Capa API REST (FastAPI)

Backend HTTP desacoplado: la dependencia es unidireccional `api → bot`, nunca al revés.

### Endpoints

| Método | Ruta | Descripción | Auth |
|---|---|---|:---:|
| `GET` | `/health` | Estado del servicio sin instanciar el bot | — |
| `GET` | `/status` | Estado operativo: bot, LLM, Odoo | — |
| `POST` | `/chat` | Consulta al agente — campo `idioma`: `"es"` / `"en"` / `"ja"` | Bearer |
| `GET` | `/reportes` | Catálogo de tipos de reporte disponibles | Bearer |
| `POST` | `/reportes/generar` | Genera reporte del tipo especificado | Bearer |
| `GET/POST/PUT/DELETE` | `/configuracion` | CRUD de empresas con cifrado Fernet (legacy) | Bearer + admin |
| `GET` | `/admin/dashboard` | KPIs globales SaaS (empresas, usuarios, consultas) | Bearer + admin |
| `GET` | `/admin/metricas` | Métricas de comportamiento agregadas | Bearer + admin |
| `GET/POST/PUT/DELETE` | `/admin/empresas` | CRUD completo de empresas | Bearer + admin |
| `GET/POST/PUT/DELETE` | `/admin/usuarios` | CRUD completo de usuarios | Bearer + admin |
| `GET/PUT` | `/admin/configuracion-sistema` | Config LLM, Odoo, sesiones (JSON persistido) | Bearer + admin |
| `GET/PUT` | `/agente/empresa` | Datos y configuración de la empresa propia | Bearer + agente |
| `GET` | `/agente/metricas` | Métricas de la empresa propia | Bearer + agente |
| `POST` | `/auth/login` | Autenticación — emite access + refresh token | — |
| `POST` | `/auth/refresh` | Renovación de access token | — |
| `GET` | `/auth/me` | Perfil del usuario autenticado | Bearer |
| `PUT` | `/auth/perfil` | Actualizar nombre, email y contraseña propios | Bearer |
| `POST` | `/auth/usuarios` | Alta de usuario (solo admin) | Bearer + admin |
| `POST` | `/auth/logout` | Cierre de sesión stateless | Bearer |

### Autenticación JWT

- **Algoritmo:** HS256, clave de `SECRET_KEY` en `.env`
- **Access token:** 15 minutos, claims: `sub`, `email`, `rol`, `empresa_id`, `tipo: "access"`
- **Refresh token:** 7 días, claims: `sub`, `tipo: "refresh"`
- **Validación de tipo cruzado:** un refresh token no puede usarse como access y viceversa
- **Hashing de contraseñas:** `pbkdf2_sha256` (puro Python, compatible passlib 1.7.x + bcrypt 5.x)

### Base de datos SaaS

SQLAlchemy 2.x con SQLite por defecto (configurable a PostgreSQL via `DB_URL`):

| Modelo | Campos clave |
|---|---|
| `Empresa` | id UUID, nombre, odoo_url, odoo_db, `odoo_clave_cifrada` (Fernet), version_odoo, tipo_erp, activa |
| `Usuario` | id, nombre, email, empresa_id FK, rol (**admin/agente/usuario**), sub_rol, area_id FK, activo, password_hash |
| `Area` | id UUID, empresa_id FK, nombre, codigo, tipo (tienda/almacen/oficina/planta), activa |
| `SesionLog` | empresa_id, session_id, timestamp, accion, tipo_consulta, resultado, duracion_ms |
| `SesionContexto` | session_id PK, empresa_id, historial_json, ultima_actividad |

Cifrado Fernet: clave derivada de `SECRET_KEY` via SHA-256 → base64url. Credenciales de empresa nunca expuestas en respuestas API (`to_dict(include_credentials=False)`).

### Sistema de roles y permisos

ANDROMEDA implementa un modelo de roles de 3 niveles con sub-roles que controlan tanto el acceso a endpoints como el filtrado de datos en Odoo.

#### Roles principales (JWT claim `rol`)

| Rol | Acceso a endpoints | Filtrado Odoo |
|---|---|---|
| `admin` | Total — `/admin/*`, `/agente/*`, `/chat`, `/reportes` | Sin filtro (visión global) |
| `agente` | `/agente/*`, `/chat`, `/reportes`, `/auth/me`, `/auth/perfil` | Según su sub_rol y área |
| `usuario` | `/chat`, `/auth/me`, `/auth/perfil` | Sin filtro directo |

#### Sub-roles (JWT claim `sub_rol`)

Refinan el perfil del usuario dentro de su rol principal y determinan qué datos ve en Odoo:

| Sub-rol | Tipo de filtro Odoo | Descripción |
|---|---|---|
| `admin` | **Sin filtro** — visión global | Administrador de la empresa |
| `director` | **Sin filtro** — visión global | Dirección general |
| `gerente` | **Sin filtro** — visión global | Gerencia de área |
| `jefe` | Filtrado por **equipo/área** (`team_id.name ilike area_codigo`) | Jefatura operativa |
| `coordinador` | Filtrado por **equipo/área** | Coordinación de procesos |
| `auxiliar` | Filtrado por **tienda/almacén** (`warehouse_id.code = area_codigo`) | Operaciones en punto de venta |
| `tienda` | Filtrado por **tienda/almacén** | Personal de tienda |

#### Áreas canónicas

Las áreas representan unidades funcionales dentro de una empresa. Cada área tiene un `codigo` que se usa como valor de filtro en las consultas Odoo:

`Finanzas` · `Tiendas` · `Marketing` · `Sistemas` · `Almacén` · `Operaciones` · `Franquicias` · `Auditoria` · `Talento` · `Proyectos` · `Compras` · `Ventas`

El endpoint `POST /chat` resuelve el `area_id` del JWT (UUID o nombre canónico) contra la tabla `areas` para obtener el `codigo` real que se inyecta como filtro de dominio Odoo.

### Ejecución

```bash
# Backend REST
uvicorn app.api.main_api:app --host 127.0.0.1 --port 8000 --reload

# Documentación interactiva (Swagger UI)
http://127.0.0.1:8000/docs
```

---

## 12. Frontend (Next.js 14)

SPA completa con autenticación JWT, protección de rutas y consumo de la API REST.

| Aspecto | Implementación |
|---|---|
| Framework | Next.js 14.2, TypeScript 5.5, Tailwind CSS 3.4 |
| Routing | App Router con grupos de rutas protegidas `(app)/` |
| Auth client | `src/lib/auth.ts` — tokens + **rol** en `localStorage`; `guardarTokens`, `guardarRol`, `getRol`, `clearTokens` |
| HTTP client | `src/lib/api.ts` — wrapper tipado, `ApiError`, retry automático en 401 con refresh token; **15 funciones nuevas** |
| Vistas rol admin | `/admin` (dashboard KPIs), `/admin/chat`, `/admin/empresas` (CRUD), `/admin/usuarios` (CRUD), `/admin/metricas`, `/admin/configuracion` |
| Vistas rol agente | `/agente/chat`, `/agente/metricas`, `/agente/configuracion` (Odoo propia) |
| Vistas rol usuario | `/chat`, `/configuracion` (perfil personal) |
| Componentes | `NavBar` (role-aware, links dinámicos + badge de rol), `ChatBubble`, `MetricsCard` |
| Visualización | recharts `BarChart` + `LineChart` para métricas |
| Protección | Guards por rol: `admin/layout.tsx`, `agente/layout.tsx`, `(app)/layout.tsx` |
| Login | Redirige automáticamente según rol: admin → `/admin`, agente → `/agente/chat`, usuario → `/chat` |
| Build | `next build` — 0 errores TypeScript |

```bash
# Desarrollo
cd frontend && npm run dev   # → http://localhost:3000

# Producción
npm run build && npm start
```

---

## 13. Seguridad

### Controles implementados

| Control | Implementación |
|---|---|
| Credenciales | Aisladas en `.env` (python-dotenv); `.gitignore` las excluye del VCS |
| Logging | `FiltroCredenciales` — redacción automática de datos sensibles en logs |
| Binding de red | `127.0.0.1` exclusivo — sin exposición a red externa |
| Input | Truncamiento a 2,000 chars + validación Pydantic en todos los endpoints |
| LLM guardrails | `CAMPOS_PROHIBIDOS` (password, tokens, OAuth) + `MODELOS_PROHIBIDOS` (ir.config_parameter, etc.) |
| Queries | `ValidadorQueries` — whitelist de modelos, bloqueo de campos sensibles, solo-lectura |
| Mutación ERP | `_es_solicitud_mutacion_bd()` — 30+ verbos (ES + EN) + comandos SQL directos bloqueados |
| JWT | Validación de tipo cruzado; tokens tipados para prevenir reutilización |
| Contraseñas | `pbkdf2_sha256` — resistente a bcrypt 5.x, OWASP-recomendado |
| BD | Credenciales Odoo cifradas con Fernet en BD; nunca expuestas en API responses |

### Auditorías completadas

Ver detalle completo en [`AUDITORIA_MEJORAS.md`](AUDITORIA_MEJORAS.md):

| Categoría | Hallazgos | Estado |
|---|:---:|---|
| Seguridad críticos (SEC-001…009) | 9 | ✅ Todos resueltos |
| Calidad y estabilidad (QA-001…008) | 8 | ✅ Todos resueltos |
| Arquitectura (ARCH-001…007) | 7 | ✅ Todos resueltos |
| UX / mantenibilidad (UX-001…006) | 6 | ✅ Todos resueltos |
| Embeddings / grafo (v7.5, E1…E9) | 9 | ✅ Todos resueltos |

---

## 14. Estructura del proyecto

```
ANDROMEDA/
├── app/
│   ├── config.py                    # ConfiguracionOdoo, Config (.env + python-dotenv)
│   ├── logging_config.py            # RotatingFileHandler, FiltroCredenciales, get_logger()
│   └── api/
│       ├── main_api.py              # FastAPI app, CORS, lifespan pattern
│       ├── schemas.py               # Pydantic I/O: Login, Token, Chat, Reporte, Empresa
│       ├── dependencies.py          # Bot singleton (double-checked locking) + get_db()
│       ├── auth/
│       │   └── jwt_utils.py         # crear_access_token, crear_refresh_token, decodificadores
│       ├── routers/
│       │   ├── auth.py              # /auth/* — login, refresh, me, perfil, usuarios, logout
│       │   ├── chat.py              # POST /chat — async, run_in_executor, stateless
│       │   ├── salud.py             # GET /health, GET /status
│       │   ├── reportes.py          # GET /reportes, POST /reportes/generar
│       │   ├── configuracion.py     # CRUD /configuracion — Fernet encrypt (legacy)
│       │   ├── admin.py             # /admin/* — dashboard, CRUD empresas/usuarios, config sistema
│       │   └── agente.py            # /agente/* — empresa propia, métricas
│       └── middlewares/
│           └── logging.py           # METHOD /path → STATUS (ms)
│
├── core/
│   ├── bot_principal.py             # OdooBotPro — motor principal del agente
│   ├── cerebro_andromeda.py         # CerebroAndromeda — análisis, estadística, limpieza
│   ├── contratos.py                 # typing.Protocol @runtime_checkable — 4 contratos
│   └── motor_bi_experto.py          # MotorBIExperto — BI, KPIs, outliers
│
├── models/
│   ├── conector_odoo.py             # ConectorOdoo — OdooRPC, cache TTL 3min, search_read, SIEM
│   ├── modelos_odoo.py              # ModeloOdoo — 40+ modelos Odoo mapeados
│   ├── db_saas.py                   # ORM SaaS: Empresa, Usuario, SesionLog, SesionContexto
│   └── odoo_versions.py             # ODOO_VERSION_MAP v14–v19, ERPAdapterProtocol
│
├── services/
│   ├── agents/
│   │   ├── multi_agente.py          # GestorMultiAgente, 12 agentes + ValidadorFinal, cadena
│   │   └── ejecutores.py            # 12 ejecutores dedicados por agente
│   ├── analysis/
│   │   ├── analisis_360.py          # Analizador360, DetectorEntidades
│   │   ├── analizador_anomalias.py  # AnalizadorAnomalias — fraude, Isolation Forest
│   │   ├── analizador_avanzado.py   # AnalizadorAvanzado — ventas, POS (25+ métodos)
│   │   ├── kpis_empresariales.py    # MotorKPIsEmpresariales — 30+ KPIs
│   │   └── kpis_financieros.py      # KPIsFinancieros — dashboard ejecutivo
│   ├── formatters/
│   │   └── formateador_respuestas.py  # FormateadorRespuestas — 41 métodos Markdown
│   ├── knowledge/
│   │   └── procesador_manuales.py   # ProcesadorManuales — indexación + URLs de imágenes
│   ├── llm/
│       ├── cerebro_llm.py           # AgenteAndromeda — orquestador LLM, lee OLLAMA_HOST
│       ├── generador_queries.py     # GeneradorQueries — NL → Query Odoo + guardrails
│       └── ollama_integrador.py     # ConectorOllama — HTTP Ollama, lee OLLAMA_HOST
│   ├── memory/
│   │   ├── memoria_vectorial.py     # MemoriaVectorial — ChromaDB, EF lazy, purga selectiva
│   │   ├── memoria_jerarquica.py    # MemoriaJerarquica — 3 niveles + sanitización metadatos
│   │   └── grafo_conocimiento.py    # GrafoConocimiento — DiGraph, 14 tipos, poda, auto-save
│   ├── nlp/
│   │   ├── cerebro_nlp.py           # CerebroNLP — lingüístico avanzado
│   │   ├── motor_embeddings.py      # MotorEmbeddings — MiniLM-L12-v2, cache SHA-256
│   │   ├── nlp_avanzado.py          # MotorNLPAvanzado — 90+ intenciones
│   │   └── motor_empatico.py        # MotorEmpatico — estado emocional del usuario
│   ├── prediction/
│   │   ├── prediccion_inteligente.py  # SistemaPrediccionInteligente — híbrido ML+DL
│   │   ├── motor_ml.py              # MotorML — scikit-learn (RF, KMeans, IsoForest)
│   │   └── neural_lstm.py           # MotorNeuralLSTM — PyTorch, 2 capas, dropout 0.2
│   ├── reports/
│   │   ├── generador_graficas.py    # GeneradorGraficas — Plotly / Matplotlib
│   │   └── generador_pdf.py         # GeneradorPDF — ReportLab
│   ├── security/
│   │   └── auditoria_queries.py     # AuditoriaQueries — SIEM JSON por línea
│   ├── auditoria_inteligente.py     # AuditoriaInteligente — nocturna, churn, reposición
│   ├── auditoria_calidad_datos.py   # AuditoriaCalidadDatos — triple validación + Excel 8h
│   └── logging_saas.py              # LoggingSaaS — fire-and-forget, rotar_logs_antiguos()
│
├── utils/
│   ├── intenciones_extendidas.py    # INTENCIONES_EXTENDIDAS — 90+ intenciones mapeadas
│   ├── consultas_especializadas.py  # ConsultasEspecializadas — 12+ queries complejas
│   ├── normalizador_prompt.py       # NormalizadorPrompt — typos, abreviaciones, sinónimos
│   ├── seguridad.py                 # firmar_prompt() — SHA-256 trazabilidad
│   ├── validador_queries.py         # ValidadorQueries — whitelist, campos sensibles
│   ├── validador_respuestas.py      # ValidadorRespuestas — 20 patrones anti-alucinación
│   ├── validador_datos.py           # ValidadorDatos — autocorrección de parámetros
│   └── logging_avanzado.py          # LoggerAvanzado — SQLite + análisis de errores
│
├── views/
│   ├── interfaz_v5.py               # InterfazAndromeda — Gradio Blocks (modo directo)
│   └── gradio_cliente.py            # GradioCliente — Gradio como cliente HTTP de la API
│
├── frontend/                        # Next.js 14 — SPA multi-rol con auth JWT
│   ├── src/lib/auth.ts              # Tokens + rol en localStorage; guardarRol, getRol
│   ├── src/lib/api.ts               # Wrapper fetch tipado, retry 401, 15 funciones SaaS nuevas
│   ├── src/components/NavBar.tsx    # Sidebar role-aware (links + badge de rol dinámicos)
│   └── src/app/
│       ├── login/page.tsx           # Auth + redirect por rol
│       ├── (app)/chat/page.tsx      # Chat usuario
│       ├── (app)/configuracion/page.tsx  # Perfil personal usuario
│       ├── (app)/admin/             # Sección Admin (layout guard)
│       │   ├── page.tsx             # Dashboard KPIs globales
│       │   ├── chat/page.tsx        # Chat admin
│       │   ├── empresas/page.tsx    # CRUD empresas
│       │   ├── usuarios/page.tsx    # CRUD usuarios
│       │   ├── metricas/page.tsx    # Métricas sistema
│       │   └── configuracion/page.tsx  # Config LLM/Odoo/sesiones
│       └── (app)/agente/            # Sección Agente (layout guard)
│           ├── chat/page.tsx        # Chat agente
│           ├── metricas/page.tsx    # Métricas empresa propia
│           └── configuracion/page.tsx  # Config Odoo empresa
│
├── tests/                           # 695 tests — 18 archivos de test
│   ├── test_auth.py                 # 50 tests — JWT, password, login, CORS (Fase 5)
│   ├── test_saas.py                 # 68 tests — SaaS, cifrado, multi-empresa (Fase 4)
│   ├── test_api.py                  # 56 tests — endpoints FastAPI (Fase 3)
│   ├── test_contratos.py            # 78 tests — contratos Protocol (Fase 2)
│   └── ...                          # 14 archivos adicionales: NLP, Core, ML, Memoria, etc.
│
│   ├── data/
│   │   ├── andromeda_saas.db            # BD SaaS SQLite (dev)
│   │   ├── memoria/chroma.sqlite3       # ChromaDB persistente
│   │   ├── manuales/                    # PDFs + imágenes extraídas + indice_conocimiento.json
│   │   └── embeddings_cache/            # Cache .npz + .json de embeddings NLP
│   │
│   ├── docs/
│   │   ├── FLOW_PIPELINE_PRINCIPAL.md   # Pipeline completo con diagrama Mermaid
│   │   ├── FLOW_NUEVO_AGENTE.md         # Guía para añadir un agente (8 pasos)
│   │   ├── FLOW_SOPORTE_ODOO_VERSION.md # Soporte a nueva versión Odoo
│   │   └── UML_ANDROMEDA.md             # Diagramas UML: Clases, Secuencia, Componentes
│   │
│   ├── Dockerfile                       # Backend dev (uvicorn --reload)
│   ├── Dockerfile.prod                  # Backend prod (gunicorn 2 workers)
│   ├── compose.yml                      # Entorno de desarrollo con volúmenes + hot reload
│   ├── compose.prod.yml                 # Entorno de producción
│   ├── .dockerignore
│   ├── main.py                          # Entrypoint: web (Gradio) / consola / api
│   ├── requirements.txt                 # Dependencias fijadas con rangos semver
│   ├── pytest.ini                       # Configuración pytest + markers
│   └── .env.example                     # Plantilla de variables de entorno
```

---

## 15. Instalación y configuración

### Requisitos del sistema

| Requisito | Mínimo | Recomendado |
|---|---|---|
| Python | 3.11+ | 3.11 |
| RAM | 8 GB | 16 GB (con LLM local) |
| Node.js | 18+ | 20 LTS (solo frontend) |
| Docker | 24+ | 29+ con Compose v2 |
| Ollama | — | Requerido para funcionalidades LLM |

### Setup manual (sin Docker)

```bash
# 1. Clonar e instalar
git clone https://github.com/tuusuario/ANDROMEDA.git
cd ANDROMEDA
pip install -r requirements.txt

# 2. Configurar entorno
cp .env.example .env
# Editar .env:
#   ODOO_URL, ODOO_DB, ODOO_USER, ODOO_API_KEY
#   SECRET_KEY (mínimo 32 chars, aleatorio)
#   DB_URL (opcional, SQLite por defecto)

# 3. Instalar modelo NLP
python -m spacy download es_core_news_sm

# 4. (Opcional) Instalar LLM local
# Ejecutar INSTALAR_CEREBRO_LLM.bat  o:
# ollama pull llama3.2
```

### Arranque

```bash
# Backend API REST
uvicorn app.api.main_api:app --host 127.0.0.1 --port 8000 --reload

# Frontend Next.js (terminal separada)
cd frontend && npm install && npm run dev

# Interfaz Gradio (modo debug/laboratorio)
python main.py web
```

### Variables de entorno

| Variable | Descripción | Requerida |
|---|---|:---:|
| `ODOO_URL` | URL base de la instancia Odoo | ✅ |
| `ODOO_DB` | Nombre de la base de datos Odoo | ✅ |
| `ODOO_USER` | Usuario de API Odoo | ✅ |
| `ODOO_API_KEY` | API key de Odoo | ✅ |
| `SECRET_KEY` | Clave para JWT + Fernet (≥ 32 chars) | ✅ |
| `DB_URL` | SQLAlchemy URL (default: SQLite local) | — |
| `OLLAMA_HOST` | Endpoint Ollama (default: `http://localhost:11434`) | — |
| `API_BASE_URL` | URL pública del backend para URLs de imágenes de manuales (default: `http://localhost:8000`) | — |

---

## 16. Docker

El entorno Docker está disponible para desarrollo con hot reload y para producción optimizada.

### Desarrollo (hot reload)

```bash
# Levantar backend + frontend con volúmenes
docker compose up -d

# Solo backend
docker compose up -d backend

# Solo frontend
docker compose up -d frontend

# Ver logs en tiempo real
docker compose logs -f backend
docker compose logs -f frontend
```

El `compose.yml` monta el código fuente como volumen: cualquier cambio en el editor se refleja automáticamente sin reconstruir la imagen.

| Servicio | URL | Puerto |
|---|---|---|
| Backend FastAPI | `http://localhost:8000` | 8000 |
| Swagger UI | `http://localhost:8000/docs` | 8000 |
| Frontend Next.js | `http://localhost:3000` | 3000 |

### Variables de entorno en Docker

El `compose.yml` inyecta automáticamente:

```yaml
environment:
  - PYTHONPATH=/app
  - API_BASE_URL=http://localhost:8000
  - OLLAMA_HOST=http://host.docker.internal:11434  # Ollama en el host Windows/Mac
```

> **Nota:** `host.docker.internal` resuelve al host desde dentro del contenedor. Ollama debe estar ejecutándose en el host (`ollama serve`).

### Producción

```bash
# Build y arranque en modo producción
docker compose -f compose.prod.yml up -d --build

# Gunicorn 2 workers (backend) + Next.js standalone (frontend)
```

### Archivos Docker

| Archivo | Descripción |
|---|---|
| `Dockerfile` | Backend dev — uvicorn `--reload` |
| `Dockerfile.prod` | Backend prod — Gunicorn 2 workers |
| `frontend/Dockerfile` | Frontend dev — `next dev` con hot reload |
| `frontend/Dockerfile.prod` | Frontend prod — multistage: `next build --standalone` |
| `compose.yml` | Desarrollo: volúmenes + hot reload |
| `compose.prod.yml` | Producción: imágenes build con `NEXT_PUBLIC_API_URL` como build arg |
| `.dockerignore` | Excluye `.env`, `__pycache__`, `frontend/`, etc. |
| `frontend/.dockerignore` | Excluye `node_modules`, `.next/`, etc. |

---

## 17. Testing

```bash
# Suite completa
python -m pytest tests/ -v

# Con reporte de cobertura
python -m pytest tests/ --cov=. --cov-report=term-missing

# Módulo específico
python -m pytest tests/test_auth.py -v
```

| Métrica | Valor |
|---|---|
| Total tests | **695** |
| Tiempo de ejecución | ~48 s |
| Warnings | 0 |
| Archivos de test | 18 |
| Distribución | Auth (50) · SaaS (68) · API (56) · Contratos (78) · NLP/Core/ML/Memoria (443) |
| Configuración | `pytest.ini` + `.coveragerc` |

---

## 18. Despliegue

### Git

```bash
# Inicializar repositorio
git init && git add . && git commit -m "KAIROS-SYNERGY - feat: ANDROMEDA v9.0 complete - KAIROS-SYNERGY"

# Push a remoto
git remote add origin https://github.com/USER/ANDROMEDA.git
git branch -M main && git push -u origin main
```

**Archivos excluidos del VCS** (`.gitignore`): `.env`, `.venv/`, `__pycache__/`, `logs/`, `build/`, `data/memoria/`, `data/andromeda_saas.db`, `Reportes_Bot/`, `reports/`, `.pytest_cache/`, `frontend/.next/`, `frontend/node_modules/`.

Para producción, configurar `DB_URL=postgresql://...` en `.env` y servir el frontend compilado con `npm run build`.

### Producción sin Docker

```bash
# Backend con Gunicorn
gunicorn app.api.main_api:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend compilado
cd frontend && npm run build && npm start
```

### Producción con Docker Compose

```bash
docker compose -f compose.prod.yml up -d --build
```

### Migración SQLite → PostgreSQL

Cambiar `DB_URL` en `.env`:

```env
DB_URL=postgresql://usuario:clave@host:5432/andromeda
```

SQLAlchemy crea las tablas automáticamente en el primer arranque.

---

## 19. Troubleshooting

| Síntoma | Causa probable | Resolución |
|---|---|---|
| `No se puede conectar a Ollama en http://localhost:11434` | Servicio Ollama inactivo | Ejecutar `ollama serve` en el host |
| `No se puede conectar a Ollama` dentro de Docker | `OLLAMA_HOST` apuntando a `localhost` | Verificar que `compose.yml` tiene `OLLAMA_HOST=http://host.docker.internal:11434` |
| `OdooRPC AuthenticationError` | Credenciales incorrectas en `.env` | Revisar `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_API_KEY` |
| Imágenes de manuales no cargan | Rutas absolutas de Windows en el JSON | Fix aplicado en `procesador_manuales.py` — verificar que el contenedor está actualizado |
| `no such column: usuarios.password_hash` | BD creada antes de Fase 5 | `ALTER TABLE usuarios ADD COLUMN password_hash TEXT` |
| `404 en /admin/dashboard` | Backend sin routers nuevos | Reiniciar uvicorn con el código actualizado |
| `403 Solo administradores` | Token con rol incorrecto | Hacer logout → login de nuevo para regenerar el token con el rol correcto |
| `rol_usuario enum` en SQLite | BD creada con roles antiguos (operador/viewer) | Borrar `data/andromeda_saas.db` y reiniciar (SQLite no soporta ALTER ENUM) |
| `ChromaDB Lock` | Múltiples instancias abiertas | Cerrar todos los procesos ANDROMEDA y reiniciar |
| `CUDA Memory Error` | Modelo LLM supera VRAM disponible | Usar modelo más pequeño en Ollama o forzar CPU con `OLLAMA_NUM_GPU=0` |
| Frontend `connection refused` | Backend FastAPI no está corriendo | Arrancar uvicorn / `docker compose up -d backend` |
| `Object of type DataFrame is not JSON serializable` | Resultado de query no serializable | Bug conocido en `conector_odoo.py` para `stock.warehouse` — en seguimiento |
| `Import Error` en tests | Dependencias desactualizadas | `pip install -r requirements.txt` |
| Backend en Docker no recarga cambios | Volumen no montado correctamente | Verificar `volumes:` en `compose.yml`; reiniciar con `docker compose up -d` |
| Manual devuelve sección incorrecta en JA/EN | Primera vez que se traduce el índice | Esperar ~10 s en la primera consulta; las siguientes son instantáneas desde el cache |
| Texto del manual en español pese a JA | Traducciones no guardadas en el JSON | Verificar acceso a internet del contenedor; revisar logs de `traducir_indice` |

---

## Autor

**Ing. Axel Gutiérrez** — Tech Lead · Software Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Axel%20Gutiérrez-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/axel-ismael-gutierrez-gutierrez-01b959333)
[![Portfolio](https://img.shields.io/badge/Portfolio-ingenieroaxelgutierrez-FF6B35)](https://ingenieroaxelgutierrez-art.github.io/Portafolio/)
[![GitHub](https://img.shields.io/badge/GitHub-ingenieroaxelgutierrez--art-181717?logo=github&logoColor=white)](https://github.com/ingenieroaxelgutierrez-art)

---

---

# 日本語版

## 概要

ANDROMEDAは、Odooインスタンスに直接接続し、ビジネスデータに関する**自然言語**クエリにリアルタイムで回答するエンタープライズ向けAI会話エージェントです。多層NLPパイプライン、13のドメインエージェントによるマルチエージェントオーケストレーション、永続的なベクトルメモリを持つRAG、ハイブリッドML/DL、**ネイティブ多言語対応（ES・EN・JA）**、Next.jsフロントエンドを持つREST APIを組み合わせています — **100%ローカル動作、データ外部流出ゼロ**。

---

## 目次

1. [システムアーキテクチャ](#1-システムアーキテクチャ)
2. [多言語システム](#2-多言語システム)
3. [技術スタック](#3-技術スタック)
4. [実行パイプライン](#4-実行パイプライン)
5. [マルチエージェントシステム](#5-マルチエージェントシステム)
6. [NLPエンジン](#6-nlpエンジン)
7. [メモリと知識ベース](#7-メモリと知識ベース)
8. [LLMエンジン（Ollama）](#8-llmエンジンollama)
9. [ML/DL予測](#9-mldl予測)
10. [データ監査](#10-データ監査)
11. [REST APIレイヤー（FastAPI）](#11-rest-apiレイヤーfastapi)
12. [フロントエンド（Next.js 14）](#12-フロントエンドnextjs-14)
13. [セキュリティ](#13-セキュリティ)
14. [プロジェクト構造](#14-プロジェクト構造)
15. [インストールと設定](#15-インストールと設定)
16. [Docker](#16-docker)
17. [テスト](#17-テスト)
18. [デプロイ](#18-デプロイ)
19. [トラブルシューティング](#19-トラブルシューティング)

---

## 1. システムアーキテクチャ

ANDROMEDAは**レイヤードモジュラーアプリケーション**アーキテクチャと**RAG + Agentikワークフロー**認知パイプラインを実装しています。責務の分離は厳格で、下位レイヤーが上位レイヤーをインポートすることは一切ありません。

### アプリケーションレイヤー

```
┌────────────────────────────────────────────────────────────────────┐
│  プレゼンテーション   Gradio Blocks · Next.js 14 · FastAPI REST    │
├────────────────────────────────────────────────────────────────────┤
│  国際化（i18n）      ES · EN · JA — ContextVar による伝播         │
├────────────────────────────────────────────────────────────────────┤
│  オーケストレーション  OdooBotPro · GestorMultiAgente（13エージェント）│
├────────────────────────────────────────────────────────────────────┤
│  サービス            NLP · LLM · ML/DL · BI · 監査 · マニュアル   │
├────────────────────────────────────────────────────────────────────┤
│  インテグレーション   ConectorOdoo（OdooRPC/XML-RPC、40+モデル）   │
├────────────────────────────────────────────────────────────────────┤
│  パーシステンス       ChromaDB · SQLite · NetworkX · JSON          │
└────────────────────────────────────────────────────────────────────┘
```

### 認知レイヤー（RAG + Agentic）

```
入力 ──► 正規化 ──► NLP（意図 + エンティティ）──► エージェントルーティング
  ──► 事前検証 ──► Odoo実行 ──► エンリッチメント
  ──► 三重検証 ──► 条件付き再生成
  ──► i18n翻訳 ──► ユーザーの言語での最終出力
```

| コンポーネント | 実装 | 仕様 |
|---|---|---|
| 埋め込みエンジン | `paraphrase-multilingual-MiniLM-L12-v2` | 384次元、多言語対応 |
| セマンティックストア | ChromaDB（永続化） | 6コレクション、最大10Kドキュメント |
| 知識グラフ | NetworkX DiGraph | 14ノードタイプ、9リレーション、90日減衰 |
| LLMランタイム | Ollama（ローカル） | Llama 3.2、Mistral、DeepSeek-R1:8b |
| 言語伝播 | `_ctx_idioma` ContextVar | リクエスト開始時に一度設定、実行チェーン全体で参照可能 |

---

## 2. 多言語システム

ANDROMEDAは3つの独立したレイヤーで完全な多言語対応（ES・EN・JA）を実装しています。

### 2.1 言語の伝播

```python
# models/conector_odoo.py
_ctx_idioma: ContextVar[str] = ContextVar("_ctx_idioma", default="es")

# app/api/routers/chat.py — リクエスト開始時に一度設定
idioma: str = request.idioma or "es"
_token_idioma = _ctx_idioma.set(idioma)
_ctx_copy = contextvars.copy_context()
```

### 2.2 分析ラッパーテキスト — `FormateadorConclusiones`

| 言語 | サンプル |
|---|---|
| `es` | `📊 Analicé los datos de ventas del período. Los resultados son los siguientes:` |
| `en` | `📊 I analyzed the sales data for the period. Here are the results:` |
| `ja` | `📊 売上データを分析しました。結果は以下の通りです：` |

### 2.3 テーブルラベルとセクション — `labels_i18n.py`

| タイプ | カバレッジ |
|---|---|
| 完全一致置換 | 約150のstring：ヘッダー、テーブル列、メトリクス行 |
| 正規表現パターン | 約50の式：動的な値が混在するstring向け |

### 2.4 Odooマニュアル — Google Translateによる完全翻訳

```
日本語クエリ: "請求書をキャンセルするには？"
    │
    ▼
traducir_consulta_i18n("ja")  →  ESキーワード
    │
    ▼
buscar(consulta_es)  →  正しいセクション  ✓
    │
    ▼
formatear_respuesta(idioma="ja")  →  titulo_ja / pasos_ja（キャッシュ済み）
```

### 2.5 カバレッジサマリー

| コンポーネント | ES | EN | JA |
|---|:---:|:---:|:---:|
| 分析コンテキストテキスト | ✅ | ✅ | ✅ |
| データテーブルのラベル | ✅ | ✅ | ✅ |
| マニュアルのセクションタイトル | ✅ | ✅* | ✅* |
| マニュアルのセマンティック検索 | ✅ | ✅ | ✅ |

---

## 3. 技術スタック

| レイヤー | 技術 | バージョン / 仕様 |
|---|---|---|
| ランタイム | Python | 3.11+ |
| APIバックエンド | FastAPI + Uvicorn | 0.133.1 / 0.41.0 |
| フロントエンド | Next.js + TypeScript | 14.2.29 / 5.5 |
| ORM / SaaS DB | SQLAlchemy | 2.x — SQLite開発 / PostgreSQL本番 |
| 認証 | python-jose + passlib | JWT HS256、pbkdf2_sha256 |
| ERP | OdooRPC（XML-RPC） | Odoo 14–19+、40+モデル |
| LLMランタイム | Ollama | Llama 3.2、Mistral、DeepSeek-R1:8b |
| NLP | spaCy + SentenceTransformers | `es_core_news_sm` + MiniLM-L12-v2 |
| ベクターストア | ChromaDB | 永続化、6コレクション |
| 知識グラフ | NetworkX | DiGraph、積極的枝刈り |
| ML | scikit-learn | ランダムフォレスト、K-Means、Isolation Forest |
| ディープラーニング | PyTorch | LSTM 2層、64ユニット |
| i18n — 辞書 | `labels_i18n.py` | 約200のES→EN/JA翻訳 |
| i18n — マニュアル | Google Translate API | 無料、APIキー不要 |
| コンテナ | Docker + Compose | 開発 + 本番 |

---

## 4. 実行パイプライン

```
 1  自由入力             "請求書をキャンセルするには？" / "Cancel invoice" / "¿Cómo cancelo?"
        │
 2  言語設定             request.idioma → _ctx_idioma.set() → ContextVar伝播
        │
 3  正規化               NormalizadorPrompt
        │
 4  NLP                  CerebroNLP → 意図 + アクション + エンティティ
        │
 5  エージェントルーティング GestorMultiAgente
        │
 6  事前検証              クエリエンリッチメント
        │
 7  Odoo実行             専用エグゼキューター → リアルタイムクエリ（107+マッピング）
        │
 8  エンリッチメント      パレート、集中度、平均値、異常値
        │
 9  三重検証 + 再生成     信頼度 < 78% → 自動再生成（最大×3）
        │
10  i18n翻訳             FormateadorConclusiones + labels_i18n + LLM
        │
11  最終出力             全てユーザーの言語でのテキスト + テーブル
```

---

## 5. マルチエージェントシステム

**13エージェント**（12ドメイン + 1バリデーター）の3レベルプライオリティルーティング：

| エージェント | ドメイン | バックエンド |
|---|---|---|
| 販売 | 商業分析、トップ製品/顧客 | `AnalizadorAvanzado`（25+メソッド） |
| 在庫 | 在庫、回転率、再注文 | `ConsultasEspecializadas` |
| 財務 | 売掛金/買掛金、キャッシュフロー | `KPIsFinancieros` |
| 診断 | 異常値、不正検知 | `AnalizadorAnomalias` |
| Odooクエリ | モデル、ユーザー | `ConectorOdoo`直接 |
| CRM | パイプライン、リード、チャーン | `Analizador360` |
| 購買 | 調達、サプライヤー | `ConsultasEspecializadas` |
| POS | POSセッション、レジ | `AnalizadorAvanzado` |
| 予測 | モンテカルロ、LSTM | `SistemaPrediccionInteligente` |
| 数学 | ROI、IRR、NPV | `MotorBIExperto` |
| 統計 | 360°、相関、RFM | `Analizador360` |
| 人事 | 給与、人員数 | `ConsultasEspecializadas` |
| ValidadorFinal | ゲートキーパー | 内部パイプライン |

---

## 6. NLPエンジン

| コンポーネント | クラス | 機能 |
|---|---|---|
| 意図検出 | `MotorNLPAvanzado` | 90+意図 |
| 言語分析 | `CerebroNLP` + spaCy | NER、依存関係分析 |
| セマンティック埋め込み | `MotorEmbeddings` | MiniLM-L12-v2（384次元） |
| 正規化 | `NormalizadorPrompt` | タイポ修正、略語展開 |

---

## 7. メモリと知識ベース

### ベクターメモリ — ChromaDB

| プロパティ | 値 |
|---|---|
| コレクション | 6（`conversaciones`、`analisis`、`errores`、`alertas`、`reportes`、`conocimiento`） |
| 上限 | 10,000ドキュメント/コレクション |
| 永続化 | `data/memoria/chroma.sqlite3` |

### 知識グラフ — NetworkX DiGraph

| プロパティ | 値 |
|---|---|
| ノードタイプ | 14種 |
| リレーションタイプ | 9種 |
| 上限 | 500ノード · 2,000エッジ |
| 自動保存 | 5インタラクションごと |

### Odooマニュアル知識ベース

`.docx`ドキュメントのインデックス化、セマンティック検索、Google Translateによる多言語対応（JA・EN）、JSONキャッシュ。

---

## 8. LLMエンジン（Ollama）

100%ローカル推論 — **データ外部流出ゼロ**。

| 側面 | 詳細 |
|---|---|
| サポートモデル | Llama 3.2、Mistral、DeepSeek-R1:8b |
| ガードレール | `CAMPOS_PROHIBIDOS`、`MODELOS_PROHIBIDOS` |
| レコード制限 | LLM生成クエリあたり最大500件 |
| 設定 | `OLLAMA_HOST`変数 |

---

## 9. ML/DL予測

| モデル | フレームワーク | 用途 |
|---|---|---|
| ランダムフォレスト | scikit-learn | 販売予測、チャーンリスク |
| K-Means | scikit-learn | 顧客セグメンテーション |
| Isolation Forest | scikit-learn | 異常値検出 |
| LSTM（2層、64ユニット） | PyTorch | 時系列、長期トレンド |
| モンテカルロ | 独自実装 | フォーキャスト信頼区間 |

---

## 10. データ監査

### 品質監査 — 三重検証

| フェーズ | 検出される問題 |
|:---:|---|
| 1 | 支払い不完全な請求書、請求書なし売上 |
| 2 | 停滞したドラフト、放棄された見積 |
| 3 | 連絡先なし顧客、価格なし製品 |

出力：**8シートのプロフェッショナルExcel**。

---

## 11. REST APIレイヤー（FastAPI）

| メソッド | パス | 説明 | 認証 |
|---|---|---|:---:|
| `GET` | `/health` | サービス状態 | — |
| `POST` | `/chat` | NLクエリ（`idioma`：`es`/`en`/`ja`） | Bearer |
| `POST` | `/reportes/generar` | レポート生成 | Bearer |
| `GET/POST/PUT/DELETE` | `/admin/empresas` | 企業CRUD | Bearer + admin |
| `POST` | `/auth/login` | JWT発行 | — |

---

## 12. フロントエンド（Next.js 14）

| 側面 | 実装 |
|---|---|
| フレームワーク | Next.js 14.2、TypeScript 5.5、Tailwind CSS |
| ルーティング | App Router、保護されたルートグループ |
| 認証クライアント | `src/lib/auth.ts` — JWT + ロール |
| 管理者ビュー | `/admin`、`/admin/empresas`、`/admin/usuarios` |
| エージェントビュー | `/agente/chat`、`/agente/metricas` |

---

## 13. セキュリティ

| コントロール | 実装 |
|---|---|
| 認証情報 | `.env`に分離；VCSから除外 |
| ログ | `FiltroCredenciales` — 機密データの自動編集 |
| 入力検証 | 2,000文字に切り詰め + Pydantic検証 |
| LLMガードレール | `CAMPOS_PROHIBIDOS` + `MODELOS_PROHIBIDOS` |
| JWT | HS256、15分アクセス、7日リフレッシュ |
| パスワード | `pbkdf2_sha256`（OWASP推奨） |

---

## 14. プロジェクト構造

```
ANDROMEDA/
├── app/api/main_api.py          # FastAPI app
├── models/conector_odoo.py      # _ctx_idioma ContextVar
├── services/
│   ├── formatters/
│   │   ├── formateador_conclusiones.py  # ES/EN/JA ラッパー
│   │   └── labels_i18n.py       # ~200 翻訳
│   ├── knowledge/procesador_manuales.py  # i18n マニュアル
│   ├── memory/                  # ChromaDB + 知識グラフ
│   └── prediction/              # ML/DL モデル
├── tests/                       # 695テスト
├── data/manuales/indice_conocimiento.json  # 翻訳キャッシュ
└── frontend/src/                # Next.js 14 SPA
```

---

## 15. インストールと設定

```bash
git clone https://github.com/tuusuario/ANDROMEDA.git
cd ANDROMEDA
pip install -r requirements.txt
python -m spacy download es_core_news_sm
cp .env.example .env
# .envを編集：ODOO_URL、ODOO_DB、ODOO_USER、ODOO_API_KEY、SECRET_KEY
```

### 起動

```bash
uvicorn app.api.main_api:app --host 127.0.0.1 --port 8000 --reload
cd frontend && npm install && npm run dev
```

---

## 16. Docker

```bash
docker compose up -d
```

| サービス | URL |
|---|---|
| バックエンドFastAPI | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| フロントエンドNext.js | `http://localhost:3000` |

---

## 17. テスト

```bash
python -m pytest tests/ -v
```

| メトリクス | 値 |
|---|---|
| 総テスト数 | **695** |
| 実行時間 | 約48秒 |
| テストファイル数 | 18 |

---

## 18. デプロイ

```bash
# 本番環境
docker compose -f compose.prod.yml up -d --build
# またはDockerなし
gunicorn app.api.main_api:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 19. トラブルシューティング

| 症状 | 考えられる原因 | 解決策 |
|---|---|---|
| DockerでOllamaに接続できない | `OLLAMA_HOST`が`localhost` | `OLLAMA_HOST=http://host.docker.internal:11434` |
| `OdooRPC AuthenticationError` | 認証情報が間違っている | `.env`を確認 |
| 日本語でマニュアルが誤ったセクションを返す | インデックスが未翻訳 | 初回は約10秒待つ |
| マニュアルのテキストがスペイン語のまま | 翻訳がJSONに保存されていない | コンテナのインターネットアクセスを確認 |
| `ChromaDB Lock` | 複数のインスタンスが開いている | 全プロセスを閉じて再起動 |
| `403 Solo administradores` | トークンのロールが間違っている | ログアウト → 再ログイン |
| フロントエンドの接続拒否 | FastAPIが起動していない | `docker compose up -d backend` |

---

## 著者

**Ing. Axel Gutiérrez** — Tech Lead · Software Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Axel%20Gutiérrez-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/axel-ismael-gutierrez-gutierrez-01b959333)
[![Portfolio](https://img.shields.io/badge/Portfolio-ingenieroaxelgutierrez-FF6B35)](https://ingenieroaxelgutierrez-art.github.io/Portafolio/)
[![GitHub](https://img.shields.io/badge/GitHub-ingenieroaxelgutierrez--art-181717?logo=github&logoColor=white)](https://github.com/ingenieroaxelgutierrez-art)

---

<p align="center">
  <b>ANDROMEDA</b> — Enterprise AI Agent for Odoo · MIT License<br>
  <sub>Built for operations teams who demand precision, speed and multilingual intelligence.</sub><br>
  <sub>精度、速度、多言語インテリジェンスを求める運用チームのために構築されました。</sub>
</p>
