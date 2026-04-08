# ANDROMEDA — Conversational AI Agent for Odoo ERP

> **v9.0** · Fases 0–5 completadas · **695 tests** · Python 3.11 · FastAPI 0.133 · Next.js 14

ANDROMEDA es un agente conversacional de IA de propósito empresarial diseñado para conectarse directamente a instancias Odoo y responder consultas en lenguaje natural sobre datos de negocio en tiempo real. El sistema combina un pipeline NLP multi-capa, un motor de orquestación multi-agente, RAG con memoria vectorial persistente, ML/DL híbrido y una capa API REST con frontend React — todo ejecutado de forma local, sin dependencias de servicios externos.

---

## Tabla de Contenido

1. [Arquitectura del sistema](#1-arquitectura-del-sistema)
2. [Stack tecnológico](#2-stack-tecnológico)
3. [Pipeline de ejecución](#3-pipeline-de-ejecución)
4. [Sistema multi-agente](#4-sistema-multi-agente)
5. [Motor NLP](#5-motor-nlp)
6. [Memoria y conocimiento](#6-memoria-y-conocimiento)
7. [Motor LLM (Ollama)](#7-motor-llm-ollama)
8. [Predicción ML/DL](#8-predicción-mldl)
9. [Auditoría de datos](#9-auditoría-de-datos)
10. [Capa API REST (FastAPI)](#10-capa-api-rest-fastapi)
11. [Frontend (Next.js 14)](#11-frontend-nextjs-14)
12. [Seguridad](#12-seguridad)
13. [Estructura del proyecto](#13-estructura-del-proyecto)
14. [Instalación y configuración](#14-instalación-y-configuración)
15. [Testing](#15-testing)
16. [Despliegue](#16-despliegue)
17. [Troubleshooting](#17-troubleshooting)

---

## 1. Arquitectura del sistema

ANDROMEDA implementa una arquitectura **Layered Modular Application** con un pipeline cognitivo **RAG + Agentic Workflow** superpuesto. La separación de responsabilidades es estricta: ninguna capa inferior importa de capas superiores.

### Capas aplicativas

```
┌─────────────────────────────────────────────────────────┐
│  PRESENTACIÓN   Gradio Blocks · Next.js 14 · FastAPI    │
├─────────────────────────────────────────────────────────┤
│  ORQUESTACIÓN   OdooBotPro · GestorMultiAgente (13)     │
├─────────────────────────────────────────────────────────┤
│  SERVICIOS      NLP · LLM · ML/DL · BI · Auditoría      │
├─────────────────────────────────────────────────────────┤
│  INTEGRACIÓN    ConectorOdoo (OdooRPC/XML-RPC, 40+ m.)  │
├─────────────────────────────────────────────────────────┤
│  PERSISTENCIA   ChromaDB · SQLite · NetworkX · JSON     │
└─────────────────────────────────────────────────────────┘
```

### Capa cognitiva (RAG + Agentic)

```
Input ──► Normalización ──► NLP (intención + entidades) ──► Agent Routing
  ──► Pre-Validación ──► Ejecución Odoo ──► Enriquecimiento
  ──► Validación Triple ──► Regeneración Condicional ──► Output
```

| Componente | Implementación | Especificación |
|---|---|---|
| Embedding engine | `paraphrase-multilingual-MiniLM-L12-v2` | 384d, multilingüe, cache SHA-256 auto-invalidante |
| Semantic store | ChromaDB persistente | 6 colecciones, EF lazy post-init, max 10K docs/col, purga selectiva |
| Knowledge graph | NetworkX DiGraph | 14 tipos nodo, 9 relaciones, decay 90d, poda proactiva, límites 500/2000 |
| Prompt builder | Dinámico | Inyección: memoria vectorial + grafo + datos Odoo real-time |
| LLM backend | Ollama local | Llama 3.2, Mistral, DeepSeek-R1:8b — zero data egress |
| Query generator | `GeneradorQueries` | NL → Query Odoo; guardrails: `CAMPOS_PROHIBIDOS` + `MODELOS_PROHIBIDOS` |

---

## 2. Stack tecnológico

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
| Visualización | Plotly + Matplotlib | Interactivas (HTML) + estáticas (PDF) |
| Reportes | OpenPyXL + ReportLab | Excel multi-hoja + PDF profesional |
| UI debug | Gradio Blocks | Chat + sidebar + voz + file download |
| Logging | SQLite + RotatingFileHandler | `FiltroCredenciales` para redacción automática |

---

## 3. Pipeline de ejecución

Flujo determinístico desde input en lenguaje natural hasta respuesta enriquecida con datos Odoo en tiempo real:

```
 1  INPUT LIBRE          "¿Cómo van las ventas por marca este mes?"
        │
 2  NORMALIZACIÓN        NormalizadorPrompt → typos, abreviaciones, sinónimos
        │
 3  NLP                  CerebroNLP + MotorNLPAvanzado → intención + acción
                         + entidades + confianza (spaCy + embeddings semánticos)
        │
 4  AGENT ROUTING        GestorMultiAgente.resolver_agente()
                         Si prompt multi-dominio → activa CADENA de agentes
        │
 5  PRE-VALIDACIÓN       Cada agente enriquece la consulta:
                         auto-rellena fechas, valida campos, ajusta parámetros
        │
 6  EJECUCIÓN ODOO       Executor dedicado por agente → consulta en tiempo real
                         107+ mapeos directos: AnalizadorAvanzado,
                         ConsultasEspecializadas, Predictor, Analizador360,
                         MotorBI, MotorKPIs
        │
 7  ENRIQUECIMIENTO      enriquecer_respuesta() → análisis determinístico:
                         Pareto, concentración, promedios, anomalías
        │
 8  VALIDACIÓN TRIPLE    Capa 1: agente de dominio verifica coherencia
    + REGENERACIÓN       Capa 2: ValidadorFinal — respuesta ↔ pregunta
                         Capa 3: confianza < 78% → regenera (máx. ×3)
        │
 9  OUTPUT               Texto + tabla HTML + indicador (agente + confianza %)
                         + Excel/PDF descargable (si aplica)
```

---

## 4. Sistema multi-agente

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

## 5. Motor NLP

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

## 6. Memoria y conocimiento

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

---

## 7. Motor LLM (Ollama)

Inferencia 100% local — **zero data egress**. Los datos de Odoo nunca salen del servidor.

| Aspecto | Detalle |
|---|---|
| Modelos soportados | Llama 3.2, Mistral, DeepSeek-R1:8b |
| NL → Query | `GeneradorQueries` convierte lenguaje natural a queries técnicas Odoo con validación de campos y modelos |
| Contexto | Prompts dinámicos: datos Odoo en tiempo real + memoria vectorial + grafo de conocimiento |
| Guardrails | `CAMPOS_PROHIBIDOS` (password, tokens, OAuth keys), `MODELOS_PROHIBIDOS` (ir.config_parameter, auth_totp, etc.) |
| Límite de registros | Máximo 500 por query generada por LLM |

---

## 8. Predicción ML/DL

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

## 9. Auditoría de datos

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

## 10. Capa API REST (FastAPI)

Backend HTTP desacoplado: la dependencia es unidireccional `api → bot`, nunca al revés.

### Endpoints

| Método | Ruta | Descripción | Auth |
|---|---|---|:---:|
| `GET` | `/health` | Estado del servicio sin instanciar el bot | — |
| `GET` | `/status` | Estado operativo: bot, LLM, Odoo | — |
| `POST` | `/chat` | Consulta al agente (NL → respuesta enriquecida) | Bearer |
| `GET` | `/reportes` | Catálogo de tipos de reporte disponibles | Bearer |
| `POST` | `/reportes/generar` | Genera reporte del tipo especificado | Bearer |
| `GET/POST/PUT/DELETE` | `/configuracion` | CRUD de empresas con cifrado Fernet | Bearer + admin |
| `GET` | `/admin/metricas` | Dashboard de métricas SaaS agregadas | Bearer + admin |
| `POST` | `/auth/login` | Autenticación — emite access + refresh token | — |
| `POST` | `/auth/refresh` | Renovación de access token | — |
| `GET` | `/auth/me` | Perfil del usuario autenticado | Bearer |
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
| `Usuario` | id, nombre, email, empresa_id FK, rol (admin/operador/viewer), activo, password_hash |
| `SesionLog` | empresa_id, session_id, timestamp, accion, tipo_consulta, resultado, duracion_ms |
| `SesionContexto` | session_id PK, empresa_id, historial_json, ultima_actividad |

Cifrado Fernet: clave derivada de `SECRET_KEY` via SHA-256 → base64url. Credenciales de empresa nunca expuestas en respuestas API (`to_dict(include_credentials=False)`).

### Ejecución

```bash
# Backend REST
uvicorn app.api.main_api:app --host 127.0.0.1 --port 8000 --reload

# Documentación interactiva (Swagger UI)
http://127.0.0.1:8000/docs
```

---

## 11. Frontend (Next.js 14)

SPA completa con autenticación JWT, protección de rutas y consumo de la API REST.

| Aspecto | Implementación |
|---|---|
| Framework | Next.js 14.2, TypeScript 5.5, Tailwind CSS 3.4 |
| Routing | App Router con grupos de rutas protegidas `(app)/` |
| Auth client | `src/lib/auth.ts` — tokens en `localStorage`, `guardarTokens`, `clearTokens`, `estaLogueado` |
| HTTP client | `src/lib/api.ts` — wrapper tipado, `ApiError`, retry automático en 401 con refresh token |
| Páginas | `/login`, `/chat`, `/metricas`, `/configuracion` |
| Componentes | `NavBar`, `ChatBubble`, `MetricsCard` |
| Visualización | recharts `BarChart` para métricas |
| Protección | `(app)/layout.tsx` redirige a `/login` si no hay access token |
| Build | `next build` — 0 errores TypeScript, 5 rutas estáticas |

```bash
# Desarrollo
cd frontend && npm run dev   # → http://localhost:3000

# Producción
npm run build && npm start
```

---

## 12. Seguridad

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

## 13. Estructura del proyecto

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
│       │   ├── auth.py              # /auth/* — login, refresh, me, usuarios, logout
│       │   ├── chat.py              # POST /chat — stateless, contexto server-side
│       │   ├── salud.py             # GET /health, GET /status
│       │   ├── reportes.py          # GET /reportes, POST /reportes/generar
│       │   ├── configuracion.py     # CRUD /configuracion — Fernet encrypt
│       │   └── admin.py             # GET /admin/metricas — dashboard SaaS
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
│   ├── conector_odoo.py             # ConectorOdoo — OdooRPC, cache, DataFrame, SIEM audit
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
│   ├── llm/
│   │   ├── cerebro_llm.py           # AgenteAndromeda — orquestador LLM
│   │   ├── generador_queries.py     # GeneradorQueries — NL → Query Odoo + guardrails
│   │   └── ollama_integrador.py     # ConectorOllama — HTTP Ollama + esta_disponible()
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
├── frontend/                        # Next.js 14 — SPA con auth JWT
│   ├── src/lib/auth.ts              # Gestión de tokens en localStorage
│   ├── src/lib/api.ts               # Wrapper fetch tipado, retry 401, ApiError
│   └── src/app/
│       ├── login/page.tsx           # Formulario de autenticación
│       ├── (app)/chat/page.tsx      # Chat con historial y typing indicator
│       ├── (app)/metricas/page.tsx  # KPIs + recharts BarChart
│       └── (app)/configuracion/page.tsx  # Gestión de empresas
│
├── tests/                           # 695 tests — 18 archivos de test
│   ├── test_auth.py                 # 50 tests — JWT, password, login, CORS (Fase 5)
│   ├── test_saas.py                 # 68 tests — SaaS, cifrado, multi-empresa (Fase 4)
│   ├── test_api.py                  # 56 tests — endpoints FastAPI (Fase 3)
│   ├── test_contratos.py            # 78 tests — contratos Protocol (Fase 2)
│   └── ...                          # 14 archivos adicionales: NLP, Core, ML, Memoria, etc.
│
├── data/
│   ├── andromeda_saas.db            # BD SaaS SQLite (dev)
│   ├── memoria/chroma.sqlite3       # ChromaDB persistente
│   └── embeddings_cache/            # Cache .npz + .json de embeddings NLP
│
├── docs/
│   ├── FLOW_PIPELINE_PRINCIPAL.md   # Pipeline completo con diagrama Mermaid
│   ├── FLOW_NUEVO_AGENTE.md         # Guía para añadir un nuevo agente (8 pasos)
│   ├── FLOW_SOPORTE_ODOO_VERSION.md # Soporte a nueva versión Odoo
│   └── UML_ANDROMEDA.md             # Diagramas UML: Clases, Secuencia, Componentes
│
├── main.py                          # Entrypoint: web (Gradio) / consola / api
├── requirements.txt                 # Dependencias fijadas con rangos semver
├── pytest.ini                       # Configuración pytest + markers
└── .env.example                     # Plantilla de variables de entorno
```

---

## 14. Instalación y configuración

### Requisitos

| Requisito | Mínimo |
|---|---|
| Python | 3.11+ |
| RAM | 8 GB (16 GB recomendado con LLM local) |
| Node.js | 18+ (solo para frontend) |
| Ollama | Opcional — requerido para funcionalidades LLM |

### Setup

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
| `LLM_URL` | Endpoint Ollama (default: `http://localhost:11434`) | — |

---

## 15. Testing

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

## 16. Despliegue

```bash
# Inicializar repositorio
git init && git add . && git commit -m "KAIROS-SYNERGY - feat: ANDROMEDA v9.0 complete - KAIROS-SYNERGY"

# Push a remoto
git remote add origin https://github.com/USER/ANDROMEDA.git
git branch -M main && git push -u origin main
```

**Archivos excluidos del VCS** (`.gitignore`): `.env`, `.venv/`, `__pycache__/`, `logs/`, `build/`, `data/memoria/`, `data/andromeda_saas.db`, `Reportes_Bot/`, `reports/`, `.pytest_cache/`, `frontend/.next/`, `frontend/node_modules/`.

Para producción, configurar `DB_URL=postgresql://...` en `.env` y servir el frontend compilado con `npm run build`.

---

## 17. Troubleshooting

| Síntoma | Causa probable | Resolución |
|---|---|---|
| `Ollama Connection Error` | Servicio Ollama inactivo | `ollama serve` → verificar `http://localhost:11434` |
| `OdooRPC AuthenticationError` | Credenciales incorrectas en `.env` | Revisar `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_API_KEY` |
| `no such column: usuarios.password_hash` | BD creada antes de Fase 5 | `ALTER TABLE usuarios ADD COLUMN password_hash TEXT` |
| `ChromaDB Lock` | Múltiples instancias abiertas | Cerrar todos los procesos ANDROMEDA y reiniciar |
| `CUDA Memory Error` | Modelo LLM supera VRAM disponible | Usar modelo más pequeño en Ollama o forzar CPU |
| Frontend `connection refused` | Backend FastAPI no está corriendo | Arrancar uvicorn en puerto 8000 |
| `Import Error` en tests | Dependencias desactualizadas | `pip install -r requirements.txt` |
| Backend se detiene solo | Terminal cerrada | Usar gestor de procesos (systemd, PM2, screen) |

---

## Autor

**Ing. Axel Gutiérrez** — Tech Lead · Software Engineer

[LinkedIn](https://www.linkedin.com/in/axel-ismael-gutierrez-gutierrez-01b959333) · [Portfolio](https://ingenieroaxelgutierrez-art.github.io/Portafolio/)
