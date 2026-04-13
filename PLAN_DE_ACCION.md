# ANDROMEDA — Plan de Acción

**Fecha:** 30 de marzo de 2026  
**Principio rector:** *Estabilizar la inteligencia antes de escalar la interfaz. Cambiar por partes, testear cada cambio.*

---

## Resumen de Fases

| Fase | Nombre | Prioridad | Estado |
|------|--------|-----------|--------|
| 0 | Estabilización del sistema actual | CRÍTICA | ✅ Completada |
| 1 | Seguridad y trazabilidad | ALTA | ✅ Completada |
| 2 | Mantenibilidad y contratos | ALTA | ✅ Completada |
| 3 | Migración de interfaz (FastAPI) | MEDIA | ✅ Completada |
| 4 | Logging SaaS + Multi-empresa | MEDIA | ✅ Completada |
| 5 | Frontend final (React/Next.js) + Login | BAJA | ✅ Completada |

---

## ⚙️ FASE 0 — Estabilización del Sistema Actual

> Antes de cualquier mejora, el sistema base debe ser sólido.

### Objetivos
- [x] **Confirmar que todos los tests pasen** — `443/443 PASSED` en 31s ✅  
  - **Bug encontrado y corregido:** `tests/conftest.py` no mockeaba `sentence_transformers`, causando  
    que el import de `motor_nlp.py` disparara la carga de PyTorch/CUDA, congelando `test_core.py`  
  - **Fix:** añadir mock de `sentence_transformers` en `sys.modules` ANTES de cualquier import del proyecto  
- [x] **Tests de calidad de respuesta (IA)** ✅  
  - **Implementado:** Test automático en `tests/test_calidad_respuesta.py`  
  - **Cobertura:**
    - Golden set de preguntas/respuestas relevantes
    - Detección de respuestas vacías y alucinaciones
    - Cobertura de intenciones y agentes principales
  - **Resultado:** 9/9 tests PASSED (sin alucinaciones, sin vacíos, respuestas relevantes)
- [x] **Asegurar que el pipeline anti-breakpoint funcione de extremo a extremo** ✅  
  - **Verificado:** `NormalizadorPrompt` se invoca en `procesar_mensaje()` ANTES del NLP (con flag `NORMALIZADOR_DISPONIBLE`)  
  - **Verificado:** `ValidadorRespuestas` se invoca en `_validar_y_regenerar_respuesta()` DESPUÉS de `_ejecutar_accion()` (línea 2395)  
  - **Verificado:** `ejecutar_cadena_completa()` pasa `mensaje=mensaje` correctamente (bug fix confirmado en línea 2299)  
  - **Verificado:** ambos módulos usan try/except + flags → degradación graceful si fallan
- [x] **Eliminar código muerto o funciones duplicadas del refactor anterior** ✅  
  - **Resultado:** No se encontró código muerto real en el sistema activo  
  - Los métodos con "1x" en `interfaz_v5.py` se usan desde servicios extraídos vía `self._bot.*` (bridge pattern)  
  - Los 3 métodos con mismo nombre en `multi_agente.py` son polimorfismo OOP: `AgenteEspecializadoBase` + 12 subclases  
  - **Artefactos obsoletos identificados** (scripts del refactor ya ejecutado, no son código activo):  
    `scripts/fix_refactor.py`, `scripts/fix_refactor_v2.py`, `scripts/fix_truncated_methods.py`, `scripts/refactor_god_class.py`  
  - ⚠️ Recomendación: mover scripts de refactor a `scripts/archive/` o eliminarlos tras confirmación del equipo
- [x] **Revisar que `interfaz_v5.py` no tenga bugs silenciosos** ✅  
  - **Bug referenciado confirmado CORREGIDO:** `ejecutar_cadena_completa(pasos, consulta, mensaje=mensaje, ...)` — `mensaje=mensaje` presente en L2299 ✅  
  - **Auditoría de `except Exception: pass`:** 13 bloques encontrados, todos son degradación graceful legítima:  
    - L1527: fallback a mapeo estático explícito de agentes  
    - L1618/1634/1888/2324/2375: validaciones `post_ejecucion`/`post_error` opcionales (mejoran pero no bloquean)  
    - L1682/2091: normalizador en paths secundarios (logging y fallback de sugerencias)  
    - L1721: logging solamente  
    - L1777: normalizador en `procesar_mensaje` → sistema usa mensaje original si falla (correcto)  
    - L1843/2174: enriquecimiento de contexto por memoria y grafo (opcionales)  
    - L2598: LLM regeneración → cae a `_resumen_confiable_desde_dataframe`  
  - **Conclusión:** ningún `except: pass` cubre lógica de negocio crítica; todos son envolventes de features opcionales


### Criterio de salida (actualizado 2026-04-01)
- ✅ Tests al 100% en modo `pytest` (443/443 PASSED, sin fallos)  
  _Nota: el criterio anterior indicaba incorrectamente 156/156; la suite real siempre tuvo 433 tests al cerrar Fase 0._
- ✅ Respuesta funcional en CLI (`cli_monitor.py`) — todos los comandos principales ejecutados sin errores críticos ni bloqueos
- Cobertura: dashboard, errores, prompts, reporte, usuarios, tendencias, rendimiento, info, ollama
- Sin errores abiertos ni prompts vacíos/alucinados
- ⚠️ **Bug corregido (2026-04-01):** `tests/test_calidad_respuesta.py` tenía una coma faltante en el `@pytest.mark.parametrize` de `test_cobertura_intenciones`, haciendo que las dos últimas preguntas se concatenaran como un solo string. Corregido: 7 casos independientes.
- Estado: Fase 0 COMPLETA y estable

---

## 🔒 FASE 1 — Seguridad y Trazabilidad
> El sistema maneja datos financieros reales. La seguridad no es opcional.

### Objetivos
- [x] **Auditoría de Queries (Log estructurado tipo SIEM)** — `443/443 PASSED` en 34s ✅  
  - **Archivo creado:** `services/security/auditoria_queries.py` — Logger minimalista y robusto, formato JSON por línea, compatible SIEM.  
  - **Integración:** Métodos `buscar`, `buscar_leer` y `search_read` en `models/conector_odoo.py` ahora registran cada query relevante (`modelo`, `filtros`, `campos`, `usuario`, `timestamp`, `duracion_ms`, `registros_retornados`, `hash_prompt`, `nivel`).
  - **Validación:**
    - Todos los tests pasan (`pytest` OK, 442/442 PASSED)
    - CLI y funcionalidades principales sin errores ni regresiones
    - `logs/queries_odoo.log` se genera en runtime ante consultas reales a Odoo; no persiste en el repositorio (esperado: no hay conexión activa en CI)
  - **Conclusión:** Sin sobreingeniería, extensible y seguro.
- [x] **Firma de Prompts (Hash para trazabilidad)** ✅  
  - **Archivo creado:** `utils/seguridad.py` — Función `firmar_prompt(texto: str) -> str` (SHA-256, minimalista, sin dependencias externas).
  - **Integración:** Métodos de consulta en `models/conector_odoo.py` ahora permiten registrar el hash del prompt asociado a cada query (si se provee el prompt, se firma automáticamente).
  - **Validación:**
    - Todos los tests pasan (`pytest` OK, 442/442 PASSED)
    - Log de auditoría de queries incluye el campo `hash_prompt` para trazabilidad
  - **Conclusión:** Sin sobreingeniería, extensible y seguro.
- [x] **Sandbox de Ejecución de Queries** ✅  
  - **Archivo creado:** `utils/validador_queries.py` — Validador simple y robusto: whitelist de modelos, bloqueo de campos sensibles, límite de registros, solo-lectura.
  - **Integración:** Métodos de consulta en `models/conector_odoo.py` ahora validan cada query antes de ejecutarla. Si la query no cumple las reglas, se bloquea y se registra el intento.
  - **Validación:**
    - Todos los tests pasan (`pytest` OK, 443/443 PASSED)
    - Queries bloqueadas correctamente según reglas
  - **Conclusión:** Sin sobreingeniería, extensible y seguro.


### Criterio de salida (actualizado 2026-03-31)
- ✅ Tests al 100% en modo `pytest` (443/443 PASSED, sin fallos)
- ✅ Respuesta funcional en CLI (`cli_monitor.py`) — todos los comandos principales ejecutados sin errores críticos ni bloqueos
- Cobertura: queries, logs, prompts, sandbox, usuarios, trazabilidad
- Sin errores abiertos ni queries inseguras
- Estado: Fase 1 COMPLETA y estable


## 🏗️ FASE 2 — Mantenibilidad y Contratos

> El sistema tiene ML, DL, NLP, multi-agentes, RAG, grafos y BI. Riesgo real: solo una persona lo entiende.

### Objetivos
- [x] **Contratos Estrictos (Interfaces)** — `521/521 PASSED` en 52.92s ✅
  - **Archivo creado:** `core/contratos.py` — 4 protocolos `typing.Protocol` con `@runtime_checkable`, sin lógica, sin herencia forzada.
  - **Contratos implementados:**
    - `ConectorOdooBase` → cumplido por `models/conector_odoo.py::ConectorOdoo` (conectar, desconectar, buscar, buscar_leer)
    - `AgenteEspecializadoProtocol` → cumplido por `AgenteEspecializadoBase` y sus **12 subclases** (`AgentVentas`, `AgentInventarios`, `AgentFinanzas`, `AgentDiagnostico`, `AgentCRM`, `AgentCompras`, `AgentPDV`, `AgentPredicciones`, `AgentMatematicas`, `AgentEstadistica`, `AgentRRHH`, `AgentConsultasOdoo`)
    - `MotorPrediccionBase` → cumplido por `services/prediction/motor_prediccion.py::MotorPrediccion` (set_conector, predecir_ventas, predecir_agotamiento)
    - `ConectorLLMBase` → cumplido por `services/llm/cerebro_llm.py::ConectorOllama` (disponible, generar, esta_disponible)
  - **Fix aplicado:** `ConectorOllama` no tenía `esta_disponible()`. Se añadió el método (retorna `self.disponible`, sin HTTP, no bloquea el pipeline).
  - **Corrección al nombre del método:** `predecir_inventario` era incorrecto — el método real se llama `predecir_agotamiento`. Contrato y tests corregidos.
  - **Validación:** 78 tests de contratos (en `tests/test_contratos.py`), todos PASSED. Ninguna regresión en la suite.

- [x] **Documentar Flows Críticos** ✅
  - **Flows documentados con Mermaid + descripción por etapa:**

    | Flow | Archivo | Contenido |
    |------|---------|-----------|
    | Pipeline completo usuario → respuesta | `docs/FLOW_PIPELINE_PRINCIPAL.md` | 10 etapas, diagrama completo, tabla de archivos clave |
    | Cómo conectar un nuevo agente | `docs/FLOW_NUEVO_AGENTE.md` | 8 pasos, ejemplos de código reales, checklist |
    | Soporte a nueva versión de Odoo | `docs/FLOW_SOPORTE_ODOO_VERSION.md` | Tablas de modelos por versión, whitelist, fixtures de test |

  - **Pendiente Fase 4:** `docs/FLOW_MULTI_EMPRESA.md` (depende de la base de datos SaaS de Fase 4)
  - **Descartado (correcto):** UML completo de todas las clases

- [x] **Diagramas de Decisión (NLP + multi-agente + LLM fallback)** ✅
  - **Implementados dentro de los documentos de flow:**
    - Diagrama completo del pipeline NLP (normalización → intención → agente → validación) en `FLOW_PIPELINE_PRINCIPAL.md`
    - Diagrama de routing multi-agente (score_prompt, pre_ejecucion, cadena) en `FLOW_PIPELINE_PRINCIPAL.md`
    - Diagrama de fallback LLM (cuándo usa LLM vs datos reales) en `FLOW_PIPELINE_PRINCIPAL.md`
    - Diagrama de decisión para alta de nuevo agente en `FLOW_NUEVO_AGENTE.md`
    - Diagrama de compatibilidad de versiones Odoo en `FLOW_SOPORTE_ODOO_VERSION.md`
  - **Formato:** Mermaid `flowchart TD` en todos los archivos de docs


### Criterio de salida (actualizado 2026-04-01)
- ✅ Tests al 100% en modo `pytest` (521/521 PASSED, sin fallos)  
  _Nota: 78 tests nuevos de contratos añadidos en `tests/test_contratos.py`_
- ✅ Los 4 contratos de `core/contratos.py` verificados con `isinstance()` en runtime
- ✅ 3 archivos de documentación con diagramas Mermaid reales (no conceptuales)
- ✅ Sin regresiones en ninguna de las fases anteriores
- Estado: Fase 2 COMPLETA y estable

---

---

## 🌐 FASE 3 — Migración de Interfaz (FastAPI)

> Gradio es válido para demo y producto temporal. Pero FastAPI es OBLIGATORIO para escalar.

### Objetivos
- [x] **FastAPI Backend — Estructura y entrypoint** — `577/577 PASSED` en 52.30s ✅
  - **Archivos creados:**
    - `app/api/__init__.py` — módulo de la capa HTTP
    - `app/api/main_api.py` — instancia FastAPI, registro de routers y middlewares
    - `app/api/schemas.py` — modelos Pydantic para I/O (sin lógica de negocio)
    - `app/api/dependencies.py` — singleton del bot (double-checked locking, thread-safe, lazy init)
    - `app/api/routers/__init__.py`
    - `app/api/middlewares/__init__.py`
  - **Diseño:** El bot (`OdooAIProV5`) nunca importa nada de `app/api/`. La dependencia va en una sola dirección: `api → bot`, no al revés.
  - **Ejecución:** `uvicorn app.api.main_api:app --host 127.0.0.1 --port 8000 --reload`

- [x] **Routers: `/chat`, `/reportes`, `/health`, `/status`** ✅
  - **`app/api/routers/salud.py`:**
    - `GET /health` — retorna 200 + `{status, version, nombre}` sin instanciar el bot (útil para health checks de infra)
    - `GET /status` — estado operativo del bot, LLM y Odoo; usa `Depends(get_bot)`
  - **`app/api/routers/chat.py`:**
    - `POST /chat` — recibe `MensajeRequest` (mensaje, session_id, empresa_id, historial), llama a `bot.procesar_mensaje()`, extrae la última respuesta del asistente, retorna `RespuestaAPI`
    - **Diseño stateless:** el cliente mantiene y envía el historial en cada request; el servidor no guarda estado de sesión (preparado para escalar horizontalmente en Fase 4)
    - Validación: mensaje 1–2000 chars (Pydantic), session_id autogenerado (UUID4) si no se provee, HTTP 500 con detalle si el bot lanza excepción
  - **`app/api/routers/reportes.py`:**
    - `GET /reportes` — catálogo estático de 5 tipos de reporte disponibles
    - `POST /reportes/generar` — delega al bot con un mensaje NLP construido; HTTP 422 si el tipo no existe; extrae ruta de archivo de la respuesta del bot si aplica

- [x] **Middleware de logging HTTP** ✅
  - **Archivo creado:** `app/api/middlewares/logging.py`
  - Registra `METHOD /path → STATUS_CODE (XX.Xms)` para cada request
  - Usa `time.perf_counter()` (alta resolución); no modifica headers ni body
  - Logger: `andromeda.api.requests` (configurable por `logging_config`)

- [x] **Gradio como Cliente HTTP (3.2)** ✅
  - **Archivo creado:** `views/gradio_cliente.py`
  - Gradio llama a `POST http://127.0.0.1:8000/chat` vía `requests` — NO instancia `OdooAIProV5` localmente
  - `GET /health` al arrancar para mostrar estado del backend en la UI
  - Fallback claro con mensaje de error si el backend no está disponible
  - Puerto 7861 (diferente al modo directo 7860 de `interfaz_v5.py`)
  - La URL del backend es configurable con `ANDROMEDA_API_URL` (env var)
  - `views/interfaz_v5.py` permanece INTACTO (modo directo sigue funcionando)

- [x] **Actualizar `requirements.txt`** ✅
  - Añadido: `fastapi>=0.100.0,<1.0.0`, `uvicorn[standard]>=0.20.0,<1.0.0`, `httpx>=0.25.0,<1.0.0`
  - Todos ya estaban instalados (fastapi 0.133.1 / uvicorn 0.41.0 / httpx 0.28.1); se agregan para builds reproducibles


### Criterio de salida (actualizado 2026-04-06)
- ✅ Tests al 100% en modo `pytest` (577/577 PASSED en 52.30s, sin fallos)
  _Nota: 56 tests nuevos de API creados en `tests/test_api.py` (endpoints, schemas, middleware, validación)_
- ✅ `app.api.main_api:app` importable y funcional sin errores (verificado vía TestClient en CI)
- ✅ `POST /chat` valida entrada (1–2000 chars), retorna `respuesta`, `historial`, `session_id`, `timestamp`, `status`
- ✅ `GET /health` responde 200 sin necesitar el bot activo
- ✅ Gradio client (`views/gradio_cliente.py`) llama a FastAPI, no al bot directamente
- ✅ Sin regresiones en ninguna de las fases anteriores (521 tests previos inalterados)
- Estado: Fase 3 COMPLETA y estable

---

## 📊 FASE 4 — Logging SaaS + Multi-Empresa

> El sistema se comporta como un producto SaaS real desde el inicio.

### Objetivos
- [x] **Base de Datos de Usuarios y Empresas** — `645/645 PASSED` en 43s ✅
  - **Archivo creado:** `models/db_saas.py` — ORM SQLAlchemy 2.x, motor SQLite por defecto (PostgreSQL vía `DB_URL`).
  - **Modelos implementados:**
    - `Empresa`: id UUID, nombre, odoo_url, odoo_db, odoo_usuario, `odoo_clave_cifrada` (Fernet), version_odoo, tipo_erp, activa
    - `Usuario`: id, nombre, email, empresa_id FK, rol (admin/operador/viewer), activo
    - `SesionLog`: id, empresa_id, session_id, timestamp, accion, tipo_consulta, resultado, duracion_ms, error_msg
    - `SesionContexto`: session_id PK, empresa_id, historial_json, ultima_actividad
  - **Cifrado Fernet:** clave derivada de `SECRET_KEY` via SHA-256 → base64url; acepta cualquier string en `.env`
  - **`to_dict(include_credentials=False)`** — contraseña nunca expuesta en respuestas de API
  - **`inicializar_db()`** — idempotente, thread-safe, init único por proceso; llamado en lifespan de FastAPI

- [x] **Configuración por Empresa — CRUD `/configuracion`** ✅
  - **Archivo creado:** `app/api/routers/configuracion.py` — 5 endpoints REST completos.
  - **Endpoints:** `GET /configuracion`, `POST /configuracion`, `GET /configuracion/{id}`, `PUT /configuracion/{id}`, `DELETE /configuracion/{id}`
  - **Soft-delete** (`activa=False`): datos preservados para auditoría, sin eliminación física
  - Contraseñas cifradas en creación y **re-cifradas** en actualización; nunca expuestas en texto plano
  - Validación Pydantic: `tipo_erp` (odoo|sap|netsuite|holded), `version_odoo` (14–25)
  - `.env` del servidor solo guarda `SECRET_KEY`, `DB_URL`, `LLM_URL` — sin credenciales de empresa

- [x] **Multi-Versión Odoo 14→19+ + Fundación Multi-ERP** ✅
  - **Archivo creado:** `models/odoo_versions.py` — mapa de compatibilidad de campos y modelos por versión.
  - **`ODOO_VERSION_MAP`** cubre v14–v19: renombres de campo (`move_type → type` en v14), omisión de campos inexistentes (`None`), renombres de modelo (`hr.leave → hr.holidays` en v14)
  - **`adaptar_campos(modelo, campos, version)`** — transforma la lista de campos; campos marcados `None` se omiten sin fallar
  - **`detectar_version_odoo(instancia)`** — auto-detección desde instancia OdooRPC con fallback a v17
  - **`ERPAdapterProtocol`** (`@runtime_checkable`) — interfaz para futuros ERPs (SAP, NetSuite, Holded)
  - `ERP_SOPORTADOS` con stubs para 3 ERPs adicionales; extensible sin romper nada existente

- [x] **Multi-Usuarios Simultáneos — Pipeline Stateless** ✅
  - **Archivos modificados:** `app/api/dependencies.py` + `app/api/routers/chat.py`
  - Pipeline `/chat` completamente stateless — sin variables globales de sesión entre requests
  - Contexto de conversación almacenado server-side en `SesionContexto` por `session_id`
  - Si el cliente envía historial vacío + `session_id` existente → el servidor **restaura el contexto desde BD**
  - Pool thread-safe de `ConectorOdoo` por `empresa_id` (`get_conector_empresa()`); `invalidar_pool_empresa()` para rotación de credenciales sin reinicio
  - `get_db()` generador FastAPI: commit automático, rollback ante excepción, cierre garantizado

- [x] **Logging de Comportamiento SaaS + Dashboard de Métricas** ✅
  - **Archivo creado:** `services/logging_saas.py` — registro fire-and-forget; nunca bloquea el pipeline principal.
  - **Archivo creado:** `app/api/routers/admin.py` — endpoints de métricas administrativas.
  - `registrar_consulta()` tolera fallos de BD sin propagar excepción al llamador
  - Métricas agregadas: total, ok/error, tasa_error, duracion_promedio_ms, por_tipo, por_dia, empresas_activas
  - `GET /admin/metricas?empresa_id=&dias=` — dashboard global o filtrado por empresa y período
  - `rotar_logs_antiguos(dias=30)` — ejecutado en lifespan de FastAPI; previene crecimiento indefinido de BD
  - Chat registra `duracion_ms` con `time.perf_counter()` e infiere tipo de consulta desde el status del bot
  - **Fix incluido:** `@app.on_event("startup")` reemplazado por patrón `lifespan` (0 DeprecationWarnings)


### Criterio de salida (actualizado 2026-04-06)
- ✅ Tests al 100% en modo `pytest` (645/645 PASSED en 43s, sin fallos)  
  _Nota: 68 tests nuevos de Fase 4 creados en `tests/test_saas.py` (cifrado, ORM, versiones Odoo, logging SaaS, CRUD, métricas, sesión, dependencias)_
- ✅ `lifespan` pattern en FastAPI — build 100% limpio, 0 DeprecationWarnings
- ✅ Credenciales de empresa cifradas con Fernet en BD; nunca expuestas en respuestas de API
- ✅ Pipeline `/chat` stateless con contexto de sesión server-side verificado
- ✅ `GET /admin/metricas` retorna métricas reales desde `SesionLog`
- ✅ Sin regresiones en ninguna de las fases anteriores (577 tests previos inalterados)
- Estado: Fase 4 COMPLETA y estable

---

## 🖥️ FASE 5 — Frontend Final (React/Next.js) + Login

> Solo iniciada tras confirmar desacoplamiento total: `frontend → HTTP → api → bot`. Gradio se mantiene como UI de laboratorio.

### Objetivos

- [x] **JWT Auth Backend — `695/695 PASSED`, sin fallos** ✅
  - **Archivo modificado:** `models/db_saas.py` — campo `password_hash` (nullable para migración gradual), `set_password()`, `check_password()`; esquema `pbkdf2_sha256` (puro Python, OWASP-recomendado; bcrypt 5.x es incompatible con passlib 1.7.x)
  - **Archivos creados:** `app/api/auth/__init__.py` + `app/api/auth/jwt_utils.py` — `crear_access_token` (15 min, claims: sub/email/rol/empresa_id), `crear_refresh_token` (7 días); decodificadores con validación de tipo (`tipo: "access"|"refresh"`) para prevenir uso cruzado
  - **Algoritmo:** HS256, clave desde variable de entorno `SECRET_KEY`
  - **Schemas Pydantic:** `LoginRequest`, `TokenResponse`, `RefreshRequest`, `UsuarioActual`, `UsuarioCrearRequest` (validador de rol: admin|operador|viewer) en `app/api/schemas.py`
  - **Archivo modificado:** `app/api/dependencies.py` — `get_current_user(Bearer) → dict`, `require_rol(*roles)` como fábrica de dependencias FastAPI
  - **Archivo creado:** `app/api/routers/auth.py` — 5 endpoints:
    - `POST /auth/login` — 401 genérico (timing-safe, no distingue email vs password)
    - `POST /auth/refresh` — re-verifica usuario en BD antes de emitir nuevo access token
    - `GET /auth/me` — retorna perfil sin `password_hash`
    - `POST /auth/usuarios` — creación solo por admin (403 si otro rol)
    - `POST /auth/logout` — 204 stateless (el cliente descarta el token)
  - **Archivo modificado:** `app/api/main_api.py` — `CORSMiddleware` para `localhost:3000`; auth router registrado primero
  - **Validación:** 50 tests en `tests/test_auth.py`: JWT utils (11), password model (5), login (9), refresh (6), logout (3), /me (6), crear_usuario (8), CORS (2)

- [x] **React/Next.js 14 — Frontend completo, `next build` limpio** ✅
  - **Directorio creado:** `frontend/` — Next.js 14.2, TypeScript 5.5, Tailwind CSS 3.4, recharts 2.12, lucide-react
  - **Archivos creados:** `src/lib/auth.ts` (gestión de tokens en localStorage: guardar, leer, limpiar, verificar sesión) + `src/lib/api.ts` (wrapper fetch tipado con `ApiError`, retry automático en 401 usando refresh token, helpers `login`, `logout`, `getMe`, `enviarMensaje`, `getMetricas`, `getConfiguracion`)
  - **Páginas implementadas:**
    - `/login` — formulario con feedback de error; redirige a `/chat` tras éxito
    - `/` — redirige a `/chat` o `/login` según estado de sesión
    - `/(app)/chat` — chat con historial, UI optimista, typing indicator, `crypto.randomUUID()` como session_id
    - `/(app)/configuracion` — listado de empresas con indicador activo/inactivo
    - `/(app)/metricas` — KPIs en tarjetas + gráfico de barras (recharts `BarChart`)
  - **Componentes:** `NavBar` (links + logout), `ChatBubble` (burbujas user/assistant), `MetricsCard` (tarjeta KPI con tendencia)
  - **Layout protegido:** `(app)/layout.tsx` — redirige a `/login` si no hay access token en localStorage
  - **Fix aplicado:** `next.config.mjs` (no `.ts`) — Next.js 14.2 no soporta archivo de configuración TypeScript
  - **Validación:** `next build` — ✓ Compiled, ✓ Linting and checking validity of types, ✓ 5 rutas estáticas generadas, 0 errores TypeScript

### Criterio de salida (actualizado 2026-04-06)
- ✅ Tests al 100% en modo `pytest` (695/695 PASSED en 48s, sin fallos)
  _Nota: 50 tests nuevos de Fase 5 en `tests/test_auth.py` (JWT utils, password model, login, refresh, logout, /me, crear_usuario, CORS)_
- ✅ `pbkdf2_sha256` como esquema de hashing (OWASP; solución definitiva a incompatibilidad passlib 1.7.x + bcrypt 5.x)
- ✅ Access token (15 min) + Refresh token (7 días) con validación de tipo cruzado — ningún token puede usarse fuera de su rol
- ✅ CORS configurado para `localhost:3000` — verificado con test `TestCors` (preflight + header en respuesta)
- ✅ `next build` limpio — 0 errores TypeScript, 5 rutas estáticas compiladas (/, /login, /chat, /configuracion, /metricas)
- ✅ 0 DeprecationWarnings en pytest — patrón `lifespan` heredado de Fase 4 inalterado
- ✅ Sin regresiones en ninguna de las fases anteriores (645 tests previos inalterados)
- Estado: Fase 5 COMPLETA y estable

---

## ❌ Descartado / Pospuesto Indefinidamente

| Item | Razón |
|------|-------|
| Sandbox en proceso aislado (Docker/subprocess) | Overkill para etapa actual. Revisar en v3.0 |
| LSTM/Deep Learning en producción | Requiere muchos datos históricos que aún no existen. Mantener ML clásico (Random Forest) |
| Multi-idioma (i18n) | No mencionado, no prioritario |
| Odoo On-Premise con módulos custom | Demasiado variable. Documentar como limitación |
| React Native / App Móvil | Fuera de alcance actual |

---

## 📋 Reglas del Flujo de Trabajo

1. **Una fase a la vez.** No empezar Fase 2 sin completar Fase 1.
2. **Testear cada cambio.** Antes de avanzar, `pytest` debe pasar al 100%.
3. **No escalar la interfaz antes de estabilizar la inteligencia.** (Fase 3 solo inicia después de Fases 0-2)
4. **Cambios pequeños y reversibles.** Cada PR/commit modifica un solo componente.
5. **Si algo se descarta, documentarlo aquí** como "Descartado" con la razón.

---

## 🗂️ Archivos Nuevos Previstos por Fase

| Fase | Archivo | Propósito |
|------|---------|-----------|
| 1 | `services/security/__init__.py` | Módulo de seguridad ✅ |
| 1 | `services/security/auditoria_queries.py` | Log SIEM de queries ✅ |
| 1 | `utils/seguridad.py` | Hash SHA-256 de prompts ✅ |
| 1 | `utils/validador_queries.py` | Sandbox/whitelist ✅ |
| 2 | `core/contratos.py` | Interfaces/Protocols ✅ |
| 2 | `docs/FLOW_PIPELINE_PRINCIPAL.md` | Diagrama principal ✅ |
| 2 | `docs/FLOW_NUEVO_AGENTE.md` | Guía extensión ✅ |
| 2 | `docs/FLOW_SOPORTE_ODOO_VERSION.md` | Guía soporte versiones Odoo ✅ |
| 2 | `tests/test_contratos.py` | 78 tests de contratos ✅ |
| 3 | `app/api/__init__.py` | Paquete capa HTTP ✅ |
| 3 | `app/api/main_api.py` | FastAPI entrypoint ✅ |
| 3 | `app/api/schemas.py` | Modelos Pydantic I/O ✅ |
| 3 | `app/api/dependencies.py` | Singleton del bot ✅ |
| 3 | `app/api/routers/__init__.py` | Paquete routers ✅ |
| 3 | `app/api/routers/chat.py` | Endpoint /chat ✅ |
| 3 | `app/api/routers/salud.py` | Endpoints /health /status ✅ |
| 3 | `app/api/routers/reportes.py` | Endpoints /reportes ✅ |
| 3 | `app/api/middlewares/__init__.py` | Paquete middlewares ✅ |
| 3 | `app/api/middlewares/logging.py` | Logging HTTP middleware ✅ |
| 3 | `views/gradio_cliente.py` | Gradio como cliente HTTP ✅ |
| 3 | `tests/test_api.py` | 56 tests de API REST ✅ |
| 4 | `models/db_saas.py` | BD empresas/usuarios ✅ |
| 4 | `models/odoo_versions.py` | Mapa versiones Odoo ✅ |
| 4 | `services/logging_saas.py` | Métricas SaaS ✅ |
| 4 | `app/api/routers/configuracion.py` | CRUD /configuracion ✅ |
| 4 | `app/api/routers/admin.py` | Dashboard /admin/metricas ✅ |
| 4 | `tests/test_saas.py` | 68 tests Fase 4 ✅ |
| 5 | `app/api/auth/__init__.py` | Módulo JWT ✅ |
| 5 | `app/api/auth/jwt_utils.py` | Generación/validación JWT ✅ |
| 5 | `app/api/routers/auth.py` | Endpoints /auth/* ✅ |
| 5 | `tests/test_auth.py` | 50 tests autenticación ✅ |
| 5 | `frontend/` | App Next.js 14 (5 páginas) ✅ |
| 5 | `frontend/src/lib/api.ts` | Wrapper fetch tipado ✅ |
| 5 | `frontend/src/lib/auth.ts` | Gestión de tokens ✅ |

---

## 🚀 POST-LANZAMIENTO — Mejoras Continuas (v10.0 · abril 2026)

### Completadas

| Área | Cambio | Severidad |
|------|--------|-----------|
| Backend | 14 rutas SaaS nuevas (admin CRUD, agente, PUT /auth/perfil) | CRÍTICA |
| Backend | Roles DB actualizados: `admin/agente/usuario` | CRÍTICA |
| Frontend | Vistas SaaS multi-rol: 11 páginas nuevas + layouts + guards | FEATURE |
| Frontend | NavBar role-aware (6 links admin, 3 agente, 2 usuario) | ALTA |
| Orquestador | `kpi_ticket_promedio` — implementación completa | MEDIA |
| Schemas | `DashboardAdmin`, `UsuarioRespuesta`, `PerfilActualizar`, `ConfigSistema` | ALTA |
| Config | `data/config_sistema.json` para configuración LLM/Odoo persistida | MEDIA |

### En progreso / backlog

- [ ] Tests para routers `admin.py` y `agente.py` (actualmente 0 tests de rutas nuevas)
- [ ] Schema de migración para BD existentes con rol enum antiguo
- [ ] Paginación en `GET /admin/usuarios` y `GET /admin/empresas`
- [ ] Caché de métricas en `/admin/dashboard` (actualmente consulta BD en cada llamada)
- [ ] Refresh token automático en el frontend (actualmente fuerza re-login al expirar)

---

*Este documento es vivo. Actualizar el estado de cada tarea a medida que se complete.*
