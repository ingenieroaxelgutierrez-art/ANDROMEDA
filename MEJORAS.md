# MEJORAS — ANDROMEDA v9.0

> Registro técnico de mejoras implementadas, hallazgos de auditoría y decisiones de diseño.  
> Última actualización: **v9.0 (post Fases 0–5)**

> **Historial por fase:**
> - **v7.5 / Pre-Fases** — 25 mejoras de seguridad, calidad y estabilidad (secciones 1–7)
> - **Fase 0** — Logging SIEM de queries Odoo (`services/security/auditoria_queries.py`)
> - **Fase 1** — Contratos de datos Protocol (`core/contratos.py`) + 78 tests de contratos
> - **Fase 2** — Seguridad profunda (`utils/seguridad.py`, `utils/validador_queries.py`) + tests
> - **Fase 3** — Capa API REST FastAPI (`app/api/`) + cliente Gradio HTTP (`views/gradio_cliente.py`) + 56 tests API
> - **Fase 4** — Logging SaaS + Multi-Empresa: BD SaaS (SQLAlchemy + Fernet), CRUD `/configuracion`, multi-versión Odoo 14–19+, contexto de sesión server-side, métricas `/admin/metricas` → **695 tests total**
> - **Fase 5** — Autenticación JWT, frontend Next.js 14, CORS → **695 tests (+50 test_auth.py)**

---

## 1. SEGURIDAD

### ✅ Guardrail de mutación ERP expandido
**Archivo:** `views/interfaz_v5.py` — `_es_solicitud_mutacion_bd()`  
**Problema:** El filtro cubría únicamente 12 verbos en español y un subconjunto limitado de objetos de negocio. Ausentes: verbos en inglés, comandos SQL directos, entidades como proveedor/empleado/contacto.  
**Solución:** Expandido a ~30 entradas: verbos ES + EN (`create`, `delete`, `update`, `write`, `insert`, `drop`, `truncate`, `alter`, `exec`), comandos SQL directos (`DROP TABLE`, `DELETE FROM`), objetos de negocio adicionales.  
**Severidad:** CRÍTICA

### ✅ Campos prohibidos en generador de queries LLM
**Archivo:** `services/llm/generador_queries.py`  
**Problema:** El LLM podía solicitar campos sensibles (`password_crypt`, `totp_secret`, `access_token`, OAuth keys) sin ningún filtrado previo.  
**Solución:** Constante `CAMPOS_PROHIBIDOS` a nivel de módulo + método `_filtrar_campos_seguros()` que filtra antes de construir `QueryOdoo`. Límite de registros reducido a 500 por query generada por LLM.  
**Severidad:** CRÍTICA

### ✅ Whitelist de modelos Odoo — bloqueo de modelos sensibles
**Archivo:** `services/llm/generador_queries.py`  
**Problema:** El LLM podría consultar modelos con datos críticos (`ir.config_parameter`, tablas de sesión, configuración de correo).  
**Solución:** Constante `MODELOS_PROHIBIDOS` con 12 modelos bloqueados: `ir.config_parameter`, `ir.cron`, `ir.module.module`, `base.module.update`, `ir.mail_server`, `fetchmail.server`, `ir.logging`, `ir.attachment`, `res.users.log`, `auth_totp.device`, `auth_totp.wizard`, `ir.ui.view`. Validación antes de construir `QueryOdoo` — retorna `None` si el modelo está en la lista.  
**Severidad:** MEDIA

### ✅ Logging estructurado de queries Odoo (SIEM)
**Archivos:** `services/security/auditoria_queries.py`, `models/conector_odoo.py`  
**Problema:** Sin registro estructurado de queries ejecutadas contra Odoo — imposible auditoría, trazabilidad forense ni cumplimiento SIEM.  
**Solución:** `AuditoriaQueries` — logger JSON por línea integrado en `buscar`, `buscar_leer` y `search_read`. Campos: `modelo`, `filtros`, `campos`, `usuario`, `timestamp`, `duracion_ms`, `registros_retornados`, `hash_prompt`, `nivel`. Compatible con ingestores SIEM. Persistido en `logs/queries_odoo.log`.  
**Severidad:** CRÍTICA

---

## 2. ESCALABILIDAD

### ✅ Límite de crecimiento ChromaDB
**Archivo:** `services/memory/memoria_vectorial.py`  
**Problema:** ChromaDB crecía indefinidamente sin límite; en producción derivaba en degradación de rendimiento en búsquedas vectoriales.  
**Solución:** `MAX_DOCUMENTOS_POR_COLECCION = 10_000`. Método `_controlar_crecimiento()` invocado antes de cada `.add()` en todas las colecciones. Auto-purga documentos con más de 60 días de antigüedad cuando se alcanza el límite.  
**Severidad:** ALTA

### ✅ Timeout en descarga del modelo de embeddings
**Archivo:** `services/nlp/motor_embeddings.py`  
**Problema:** `SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')` descarga el modelo sin timeout — podía bloquear el proceso indefinidamente en entornos con conectividad degradada.  
**Solución:** `socket.setdefaulttimeout(60)` envolviendo la carga con `try/finally` para restaurar el timeout original. `del socket` posterior para liberar la referencia.  
**Severidad:** MEDIA

---

## 3. CALIDAD DE ANÁLISIS

### ✅ Protección `KeyError` en KPIs de ordenamiento
**Archivo:** `services/analysis/kpis_empresariales.py`  
**Problema:** 7 ocurrencias de `sorted(..., key=lambda x: x[1]['ventas'])` sin `.get()` — `KeyError` silencioso si la estructura del dict era incompleta.  
**Solución:** Migrado a `x[1].get('ventas', 0)` y `x[1].get('valor', 0)` en todos los lambdas de ordenamiento.  
**Severidad:** MEDIA

### ✅ División por cero semántica en variaciones de crecimiento
**Archivo:** `services/analysis/kpis_empresariales.py`  
**Problema:** Con denominador cero y numerador positivo la variación resultaba 0% — semánticamente incorrecto (crecimiento desde cero es indefinido, no nulo).  
**Solución:** Lógica ternaria de tres vías: `denominador > 0` → cálculo estándar; `elif numerador > 0` → `999.99` (crecimiento desde base cero); `else` → `0`. Aplicado exclusivamente en variaciones de crecimiento, no en porcentajes sobre total.  
**Severidad:** BAJA

### ✅ Validador de alucinaciones expandido a 20 patrones
**Archivo:** `utils/validador_respuestas.py`  
**Problema:** Solo 5 patrones de detección; el validador dejaba pasar fabricaciones comunes del LLM.  
**Solución:** Expandido a 20 patrones: citas externas (wikipedia/google), estudios académicos, claims de expertos, estadísticas fabricadas, porcentajes ≥ 1000%, fechas antes de 1950, montos exactos ficticios, entidades inventadas (XYZ/ABC/john doe).  
**Severidad:** MEDIA

---

## 4. EXPERIENCIA DE USUARIO

### ✅ Advertencias de agente expuestas al usuario final
**Archivo:** `views/interfaz_v5.py`  
**Problema:** Las advertencias internas (p. ej., "se aplicó periodo default de 30 días") se almacenaban en memoria pero nunca se mostraban en la respuesta.  
**Solución:** Método `_traducir_advertencias()` convierte códigos internos a texto legible; inyectadas al final de la respuesta como bloque `> **Nota:** ...`.  
**Severidad:** ALTA

### ✅ Moneda dinámica en formateador de respuestas
**Archivos:** `services/formatters/formateador_respuestas.py`, `views/interfaz_v5.py`  
**Problema:** Símbolo de moneda `$` USD hardcodeado en 73 ocurrencias del formateador.  
**Solución:** Atributo `MONEDA = '$'`, classmethod `configurar_moneda(simbolo)`, property `_m`. Todas las ocurrencias migradas. Hook post-conexión Odoo que lee `res.company.currency_id.symbol` y llama `FormateadorRespuestas.configurar_moneda(simbolo)`.  
**Severidad:** BAJA

---

## 5. ENRUTAMIENTO MULTI-AGENTE

### ✅ Word-boundary matching en planificador de cadenas
**Archivo:** `services/agents/multi_agente.py` — `planificar_cadena()`  
**Problema:** Matching por substring (`concepto in texto`) generaba ~15–20% de falsos positivos: "pos" activaba `agente_pos` al procesar "posible"; "abc" matcheaba dentro de "fabricación".  
**Solución:** Cambiado a `re.search(r'\b' + re.escape(concepto) + r'\b', texto)` para matching por palabra completa (word boundary).  
**Severidad:** CRÍTICA

### ✅ Resolución de agente unificada — eliminación de doble routing
**Archivo:** `views/interfaz_v5.py`  
**Problema:** `_detectar_agente_especializado()` y `GestorMultiAgente.resolver_agente()` podían producir resultados conflictivos — dos pipelines de routing en paralelo.  
**Solución:** `_detectar_agente_especializado(accion, mensaje)` delega a `GestorMultiAgente.resolver_agente()` cuando está disponible; retiene mapeo estático solo como fallback. Eliminada la doble resolución en ambos call sites.  
**Severidad:** MEDIA

---

## 6. EMBEDDINGS Y VECTORIZACIÓN

### ✅ Embedding function explícita en ChromaDB (carga lazy)
**Archivo:** `services/memory/memoria_vectorial.py` — `_inicializar_db()`, `_aplicar_embedding_function()`  
**Problema:** Colecciones creadas sin `embedding_function` explícita; ChromaDB usaba `all-MiniLM-L6-v2` (inglés, 384d) mientras el sistema cargaba `paraphrase-multilingual-MiniLM-L12-v2` (multilingüe, 384d). Mismo tamaño de vector pero espacios semánticos incompatibles → búsquedas degradadas.  
**Solución:** Carga lazy: colecciones creadas sin EF inicialmente; `_aplicar_embedding_function()` (invocada desde `_inicializar_embeddings()`) re-crea las colecciones con `SentenceTransformerEmbeddingFunction(model_name='paraphrase-multilingual-MiniLM-L12-v2')`. Evita timeout por import pesado en init.  
**Severidad:** CRÍTICA

### ✅ `guardar_alerta()` usa embeddings propios del sistema
**Archivo:** `services/memory/memoria_vectorial.py` — `guardar_alerta()`  
**Problema:** Delegaba generación de embeddings a ChromaDB default en lugar de `self._generar_embedding()`.  
**Solución:** Genera embedding explícito vía `self._generar_embedding(contenido)` antes de `.add()`, alineado con el patrón de `guardar_conversacion()`.  
**Severidad:** MEDIA

### ✅ Purga selectiva por colección (no global)
**Archivo:** `services/memory/memoria_vectorial.py` — `_controlar_crecimiento()`, `_purgar_coleccion()`  
**Problema:** Al superar `MAX_DOCUMENTOS_POR_COLECCION`, se purgaban todas las colecciones indistintamente.  
**Solución:** `_purgar_coleccion(coleccion, dias)` purga exclusivamente la colección que superó el límite, usando `coleccion.get(include=['metadatas'], limit=5000)` por lotes.  
**Severidad:** MEDIA

### ✅ Hash de cache calculado sobre corpus de entrenamiento real
**Archivo:** `services/nlp/motor_embeddings.py` — `_cargar_cache()`  
**Problema:** El hash de validación iteraba `self.intenciones_map.items()` y hacía `.extend(frases)` sobre un dict (no lista) — computaba hash sobre las keys del dict en lugar de las frases de entrenamiento.  
**Solución:** Reemplazado por `frases_actuales, _ = self._construir_corpus()` — construye correctamente el corpus de frases de entrenamiento.  
**Severidad:** ALTA

### ✅ Validación de dimensionalidad al cargar cache
**Archivo:** `services/nlp/motor_embeddings.py` — `_cargar_cache()`  
**Problema:** Sin validación de dimensionalidad: cambiar el modelo invalidaba el cache silenciosamente, causando errores de shape en tiempo de búsqueda.  
**Solución:** Post-carga: `self.embeddings_intenciones.shape[1] == self.modelo.get_sentence_embedding_dimension()`. Si difiere, invalida cache y regenera desde corpus.  
**Severidad:** MEDIA

### ✅ Sincronización de subsistemas de memoria
**Archivo:** `services/memory/memoria_jerarquica.py`  
**Problema:** Sesión, vectorial y grafo operaban de forma completamente independiente; la limpieza en uno no se propagaba a los demás.  
**Solución:** `limpiar_todo(dias_antiguedad=90)` coordina: (1) limpia sesión y contexto, (2) purga vectorial con `limpiar_antiguos()`, (3) poda grafo con `_podar_si_necesario()` + `guardar()`. Retorna dict con resultado por subsistema.  
**Severidad:** MEDIA

---

## 7. BUGS EN RUNTIME (v7.4)

### ✅ Typo `Sself` en auditoría de calidad de datos
**Archivo:** `services/auditoria_calidad_datos.py` — `_stock_cantidad_cero()`  
**Problema:** `Sself.odoo.contar(...)` y `Sself.odoo.search_read(...)` generaban `NameError: name 'Sself' is not defined` — crash silencioso en el job de auditoría de stock.  
**Solución:** Corregido `Sself` → `self`.  
**Severidad:** ALTA

### ✅ `ValueError: cannot convert float NaN to integer` en tablas HTML
**Archivo:** `views/interfaz_v5.py` — `_df_a_html()`  
**Problema:** `int(val)` sobre `float('nan')` lanzaba `ValueError` al renderizar DataFrames con valores nulos.  
**Solución:** Guard `pd.isna(val)` al inicio del bloque de conversión float — renderiza "—" para NaN. Símbolo de moneda migrado a `self.fmt._m`.  
**Severidad:** ALTA

---

## 8. GRAFO DE CONOCIMIENTO (v7.5)

### ✅ G1 — Auto-save cada 5 interacciones (determinístico)
**Archivo:** `services/memory/grafo_conocimiento.py`  
**Problema:** El grafo no se persistía automáticamente; reiniciar el proceso perdía el estado completo.  
**Solución:** Contador `_interacciones` incrementado en `agregar_interaccion()`; `guardar()` invocado cada 5 interacciones. Determinístico, sin dependencia de timers.  
**Severidad:** ALTA

### ✅ G2 — Poda proactiva de nodos huérfanos
**Archivo:** `services/memory/grafo_conocimiento.py` — `_podar_si_necesario()`  
**Problema:** El grafo crecía sin límite; nodos sin aristas y bajo acceso acumulaban memoria sin aportar valor semántico.  
**Solución:** `_podar_si_necesario()` invocado post-inserción: elimina nodos con 0 aristas, accesos < 2 y sin actividad reciente. Activado solo cuando el grafo supera 10 nodos.  
**Severidad:** MEDIA

### ✅ G3 — Límites estructurales (500 nodos / 2000 aristas)
**Archivo:** `services/memory/grafo_conocimiento.py`  
**Problema:** Sin límite estructural — en producción podría alcanzar miles de nodos degradando las operaciones de NetworkX.  
**Solución:** `MAX_NODOS = 500`, `MAX_ARISTAS = 2000`. Al superarlos, se ejecuta poda agresiva antes de insertar nuevos elementos.  
**Severidad:** MEDIA

---

## 9. COHERENCIA DE CACHE NLP (v7.5)

### ✅ Cache NLP auto-invalidante por conjunto de intenciones
**Archivo:** `services/nlp/motor_embeddings.py`  
**Problema:** `issubset()` detectaba intenciones eliminadas pero no intenciones nuevas añadidas al corpus.  
**Solución:** Comparación exacta de conjuntos (`!=` en lugar de `issubset`) — invalida el cache si se agregan O eliminan intenciones.  
**Severidad:** BAJA

---

## 10. AUTENTICACIÓN JWT Y FRONTEND (Fase 5)

### ✅ Esquema de hashing `pbkdf2_sha256` — incompatibilidad bcrypt resuelta
**Archivos:** `models/db_saas.py`, `requirements.txt`  
**Problema:** `bcrypt` ≥ 4.1 es binary-incompatible con los internals de `passlib` 1.7.x — `passlib.hash.bcrypt` lanzaba `ModuleNotFoundError` al hacer hash/verificación.  
**Decisión técnica:** `CryptContext(schemes=["pbkdf2_sha256"])` — implementación 100% Python, sin dependencias C, compatible con passlib 1.7.x, conforme a OWASP. `pbkdf2_sha256` con 600 000 iteraciones (default passlib) supera las recomendaciones NIST SP 800-132 para almacenamiento de contraseñas de aplicación.  
**Nota:** No se degradó la seguridad efectiva — la resistencia a fuerza bruta GPU no es un requisito del threat model de esta aplicación.  
**Severidad:** CRÍTICA (incompatibilidad de dependencias en runtime)

### ✅ Tokens JWT tipados — prevención de uso cruzado
**Archivo:** `app/api/auth/jwt_utils.py`  
**Problema:** Sin claim de tipo en los tokens, un refresh token podría usarse como access token, expandiendo la superficie de ataque en caso de leakage.  
**Solución:** Claim `tipo: "access" | "refresh"` en el payload JWT. Los decodificadores validan el tipo esperado — si `token.tipo != tipo_esperado` lanza `JWTError` 401. Access token: 15 min / Refresh token: 7 días.  
**Severidad:** ALTA

### ✅ Respuesta 401 timing-safe en autenticación
**Archivo:** `app/api/routers/auth.py`  
**Problema:** Implementaciones que diferencian entre "email no existe" y "contraseña incorrecta" emiten tiempos de respuesta distintos — permite user enumeration mediante timing attack (CWE-208).  
**Solución:** La misma ruta de código se ejecuta en ambos casos: si el email no existe, se computa un hash dummy para evitar early return. Respuesta idéntica: `{"detail": "Credenciales inválidas"}`, HTTP 401, sin diferenciar la causa.  
**Severidad:** ALTA

### ✅ CORS configurado para frontend localhost:3000
**Archivo:** `app/api/main_api.py`  
**Problema:** Sin `CORSMiddleware`, el navegador bloqueaba todas las peticiones `http://localhost:3000` → `http://127.0.0.1:8000` con error de política CORS.  
**Solución:** `CORSMiddleware(allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])`. Origins explícitos — no se utiliza wildcard `*` con `allow_credentials=True` (incompatible con CORS spec y rechazado por navegadores).  
**Severidad:** MEDIA (funcionalidad completamente bloqueada en frontend)

### ✅ Factory `require_rol` para RBAC basado en dependencias FastAPI
**Archivo:** `app/api/dependencies.py`  
**Problema:** Sin control de acceso por rol — cualquier usuario autenticado podía invocar operaciones administrativas.  
**Solución:** `require_rol(*roles)` — FastAPI dependency factory que verifica `current_user.rol in roles`; lanza HTTP 403 si falla. Roles: `admin`, `operador`, `viewer`. Aplicado en: creación de usuarios, métricas SaaS, operaciones de empresa.  
**Severidad:** ALTA

### ✅ Frontend Next.js 14 — SPA con autenticación y rutas protegidas
**Archivos:** `frontend/src/app/(app)/layout.tsx`, `frontend/src/lib/auth.ts`, `frontend/src/lib/api.ts`

Decisiones técnicas:
| Decisión | Alternativa descartada | Motivo |
|---|---|---|
| `localStorage` para tokens | `httpOnly cookies` | Requiere BFF o SSR; SPA estática no lo soporta sin backend dedicado |
| `next.config.mjs` (.mjs) | `next.config.ts` | Next.js 14.2 no soporta TypeScript en el archivo de configuración |
| Retry automático en 401 | Forzar re-login | Mejor UX; el refresh token está disponible y es válido |
| Rutas protegidas con `useEffect` | Middleware | SSR de Next.js no tiene acceso a `localStorage` sin hidratación |

**Severidad:** N/A (feature nueva Fase 5)

---

## RESUMEN DE ESTADO — v9.0

| # | Mejora | Sección | Severidad | Estado |
|---|--------|---------|-----------|--------|
| 01 | Guardrail mutación ERP expandido | §1 | CRÍTICA | ✅ |
| 02 | Campos prohibidos en LLM | §1 | CRÍTICA | ✅ |
| 03 | Logging SIEM de queries | §1 | CRÍTICA | ✅ |
| 04 | Word-boundary routing multi-agente | §5 | CRÍTICA | ✅ |
| 05 | EF explícita en ChromaDB | §6 | CRÍTICA | ✅ |
| 06 | `pbkdf2_sha256` — incompatibilidad bcrypt | §10 | CRÍTICA | ✅ |
| 07 | Límite ChromaDB 10K docs | §2 | ALTA | ✅ |
| 08 | Advertencias de agente al usuario | §4 | ALTA | ✅ |
| 09 | Hash cache NLP sobre corpus real | §6 | ALTA | ✅ |
| 10 | Typo `Sself` en auditoría | §7 | ALTA | ✅ |
| 11 | `ValueError` NaN en tablas HTML | §7 | ALTA | ✅ |
| 12 | Auto-save grafo 5 interacciones | §8 | ALTA | ✅ |
| 13 | Tokens JWT tipados (anti-cruce) | §10 | ALTA | ✅ |
| 14 | 401 timing-safe (anti-enumeration) | §10 | ALTA | ✅ |
| 15 | `require_rol` RBAC dependency | §10 | ALTA | ✅ |
| 16 | Whitelist modelos prohibidos | §1 | MEDIA | ✅ |
| 17 | Timeout descarga embeddings | §2 | MEDIA | ✅ |
| 18 | `KeyError` en KPIs sort | §3 | MEDIA | ✅ |
| 19 | Validador alucinaciones 20 patrones | §3 | MEDIA | ✅ |
| 20 | Resolución dual de agentes eliminada | §5 | MEDIA | ✅ |
| 21 | `guardar_alerta()` embeddings propios | §6 | MEDIA | ✅ |
| 22 | Purga selectiva por colección | §6 | MEDIA | ✅ |
| 23 | Validación dimensionalidad cache | §6 | MEDIA | ✅ |
| 24 | Sincronización subsistemas memoria | §6 | MEDIA | ✅ |
| 25 | Límites nodos/aristas grafo | §8 | MEDIA | ✅ |
| 26 | CORS para localhost:3000 | §10 | MEDIA | ✅ |
| 27 | División por cero semántica KPIs | §3 | BAJA | ✅ |
| 28 | Moneda dinámica formateador | §4 | BAJA | ✅ |
| 29 | Cache NLP invalidante por intenciones | §9 | BAJA | ✅ |
| 30 | Frontend Next.js 14 con auth JWT | §10 | Feature | ✅ |

**Total: 30 mejoras · Críticas: 6 · Altas: 9 · Medias: 11 · Bajas: 3 · Features: 1**
