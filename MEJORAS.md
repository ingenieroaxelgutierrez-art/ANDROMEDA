# MEJORAS — ANDROMEDA v17.0
> Documento de auditoría y mejoras implementadas.  
> Última actualización: v7.5

---

## 1. SEGURIDAD

### ✅ Guardrail de Mutación Expandido
**Archivo:** `views/interfaz_v5.py` — `_es_solicitud_mutacion_bd()`  
**Problema:** El filtro solo cubría 12 verbos en español y pocos objetos de negocio. Faltaban verbos en inglés, comandos SQL directos, y objetos como proveedor/empleado/contacto.  
**Solución:** Expandido a ~30 líneas: verbos ES + EN (`create`, `delete`, `update`, `write`, `insert`, `drop`, `truncate`, `alter`, `exec`), comandos SQL directos (`DROP TABLE`, `DELETE FROM`, etc.), más objetos de negocio.  
**Severidad:** CRÍTICA

### ✅ Campos Prohibidos en Generador de Queries LLM
**Archivo:** `services/llm/generador_queries.py`  
**Problema:** El LLM podía solicitar campos sensibles (`password_crypt`, `totp_secret`, `access_token`, etc.) sin validación.  
**Solución:** Constante `CAMPOS_PROHIBIDOS` a nivel de módulo + método `_filtrar_campos_seguros()` que filtra antes de crear `QueryOdoo`. También se limitó `limite` a máximo 500.  
**Severidad:** CRÍTICA

### ✅ Validación de Modelos Sensibles
**Archivo:** `services/llm/generador_queries.py`  
**Problema:** El LLM podría consultar modelos con datos sensibles como `ir.config_parameter` o tablas de sesión.  
**Solución:** Constante `MODELOS_PROHIBIDOS` con 12 modelos bloqueados (`ir.config_parameter`, `ir.cron`, `ir.module.module`, `base.module.update`, `ir.mail_server`, `fetchmail.server`, `ir.logging`, `ir.attachment`, `res.users.log`, `auth_totp.device`, `auth_totp.wizard`). Validación antes de crear `QueryOdoo` — retorna `None` si modelo prohibido.  
**Severidad:** MEDIA

---

## 2. ESCALABILIDAD

### ✅ Límite de Crecimiento ChromaDB
**Archivo:** `services/memory/memoria_vectorial.py`  
**Problema:** No existía límite de documentos en ChromaDB. En producción, la memoria crecía indefinidamente causando degradación de rendimiento.  
**Solución:** Constante `MAX_DOCUMENTOS_POR_COLECCION = 10000`. Método `_controlar_crecimiento()` invocado antes de cada `.add()` en todas las colecciones (conversaciones, análisis, errores, alertas). Auto-purga documentos >60 días cuando se alcanza el límite.  
**Severidad:** ALTA

### ✅ Timeout en Descarga de Modelo de Embeddings
**Archivo:** `services/nlp/motor_embeddings.py`  
**Problema:** `SentenceTransformer('all-MiniLM-L6-v2')` se descarga sin timeout.  
**Solución:** `socket.setdefaulttimeout(60)` envolviendo la carga del modelo con `try/finally` para restaurar timeout original. Máximo 60s para descarga.  
**Severidad:** MEDIA

---

## 3. CALIDAD DE ANÁLISIS

### ✅ Protección KeyError en KPIs de Ordenamiento
**Archivo:** `services/analysis/kpis_empresariales.py`  
**Problema:** 7 ocurrencias de `sorted(..., key=lambda x: x[1]['ventas'])` sin `.get()`, riesgo de KeyError si la estructura del dict es incompleta.  
**Solución:** Cambiado a `x[1].get('ventas', 0)` y `x[1].get('valor', 0)` en todas las ocurrencias.  
**Severidad:** MEDIA

### ✅ División por Cero Semántica
**Archivo:** `services/analysis/kpis_empresariales.py`  
**Problema:** Cuando el periodo anterior tiene cero ventas y el actual tiene ventas, la variación era 0%.  
**Solución:** Lógica 3-way: si denominador > 0 → cálculo normal; elif numerador > 0 → `999.99` (crecimiento desde cero); else → `0`. Solo en variación de crecimiento, no en porcentajes sobre total.  
**Severidad:** BAJA

### ✅ Validador de Respuestas Ampliado
**Archivo:** `utils/validador_respuestas.py`  
**Problema:** Solo 5 patrones de detección de alucinaciones.  
**Solución:** Expandido a 20 patrones: citas externas (wikipedia/google), estudios académicos, claims de expertos, estadísticas fabricadas, porcentajes irreales (≥1000%), fechas imposibles (<1950), montos exactos ficticios, entidades inventadas (XYZ/ABC/john doe).  
**Severidad:** MEDIA

---

## 4. EXPERIENCIA DE USUARIO (UX)

### ✅ Advertencias del Agente Mostradas al Usuario
**Archivo:** `views/interfaz_v5.py`  
**Problema:** Las advertencias internas de los agentes (ej: "se usó periodo default de 30 días") se guardaban en memoria pero nunca se mostraban al usuario.  
**Solución:** Método `_traducir_advertencias()` convierte códigos internos a texto legible. Se inyectan como nota al final de la respuesta (`> **Nota:** ...`).  
**Severidad:** ALTA

### ✅ Formateador de Respuestas — Moneda Dinámica
**Archivos:** `services/formatters/formateador_respuestas.py`, `views/interfaz_v5.py`  
**Problema:** Moneda siempre era `$` USD hardcodeado (73 ocurrencias).  
**Solución:** Atributo de clase `MONEDA = '$'`, classmethod `configurar_moneda(simbolo)`, property `_m`. 73 ocurrencias migradas a `{self._m}`. Hook en `interfaz_v5.py` que lee `res.company.currency_id` → `res.currency.symbol` tras conexión Odoo y llama `FormateadorRespuestas.configurar_moneda(simbolo)`.  
**Severidad:** BAJA

---

## 5. ENRUTAMIENTO MULTI-AGENTE

### ✅ Word Boundary en Matching de Conceptos
**Archivo:** `services/agents/multi_agente.py` — `planificar_cadena()`  
**Problema:** Matching por substring (`concepto in texto`) causaba ~15-20% de falsos positivos. Ej: "pos" activaba agente_pos al buscar "posible", "abc" matcheaba dentro de "fabricación".  
**Solución:** Cambiado a `re.search(r'\b' + re.escape(concepto) + r'\b', texto)` para matching por palabra completa.  
**Severidad:** CRÍTICA

### ✅ Resolución Unificada de Agentes
**Archivo:** `views/interfaz_v5.py`  
**Problema:** `_detectar_agente_especializado()` y `GestorMultiAgente.resolver_agente()` podían dar resultados conflictivos.  
**Solución:** `_detectar_agente_especializado(accion, mensaje)` ahora delega al `GestorMultiAgente.resolver_agente()` cuando está disponible, manteniendo mapeo estático solo como fallback. Eliminada la doble resolución en ambos call sites (~1870 y ~2170).  
**Severidad:** MEDIA

---

## 6. EMBEDDINGS Y GRAFOS

### ✅ Sincronización de Sistemas de Memoria
**Archivo:** `services/memory/memoria_jerarquica.py`  
**Problema:** Sesión, Vectorial y Grafo operaban independientemente; limpieza en uno no se propagaba.  
**Solución:** Método `limpiar_todo(dias_antiguedad=90)` que coordina: (1) limpia sesión y contexto, (2) purga vectorial con `limpiar_antiguos()`, (3) poda grafo con `_podar_si_necesario()` + `guardar()`. Retorna dict con resultado por subsistema. Logging centralizado.  
**Severidad:** MEDIA

### ✅ Cache de Intenciones NLP Auto-Invalidante
**Archivo:** `services/nlp/motor_embeddings.py`  
**Problema:** Cache usaba `issubset()` — detectaba intenciones eliminadas pero NO nuevas intenciones agregadas ni frases modificadas.  
**Solución:** (1) Comparación exacta de conjuntos (`!=` en vez de `issubset`), invalida si se agregan O eliminan intenciones. (2) Hash SHA-256 de frases de entrenamiento guardado en meta — cache se regenera si cambian frases existentes.  
**Severidad:** BAJA

---

## 7. BUGS EN RUNTIME (v7.4)

### ✅ Typo `Sself` en Auditoría de Calidad de Datos
**Archivo:** `services/auditoria_calidad_datos.py` — `_stock_cantidad_cero()`  
**Problema:** `Sself.odoo.contar(...)` y `Sself.odoo.search_read(...)` generaban `NameError: name 'Sself' is not defined`, crash silencioso en auditoría de stock.  
**Solución:** Corregido a `self.odoo.contar(...)` y `self.odoo.search_read(...)`.  
**Severidad:** ALTA

### ✅ ValueError NaN → int en Tablas HTML
**Archivo:** `views/interfaz_v5.py` — `_df_a_html()`  
**Problema:** `int(val)` sobre un `float('nan')` provocaba `ValueError: cannot convert float NaN to integer`, crash al renderizar DataFrames con valores nulos.  
**Solución:** Guard `pd.isna(val)` al inicio del bloque float — renderiza "—" para NaN. Moneda también migrada a `self.fmt._m` (moneda dinámica).  
**Severidad:** ALTA

---

## RESUMEN DE ESTADO

| # | Mejora | Severidad | Estado |
|---|--------|-----------|--------|
| 1 | Guardrail mutación expandido | CRÍTICA | ✅ Implementada |
| 2 | Campos prohibidos LLM | CRÍTICA | ✅ Implementada |
| 3 | Word boundary multi-agente | CRÍTICA | ✅ Implementada |
| 4 | Límite ChromaDB | ALTA | ✅ Implementada |
| 5 | Advertencias al usuario | ALTA | ✅ Implementada |
| 6 | KPI sort safety | MEDIA | ✅ Implementada |
| 7 | Modelos prohibidos | MEDIA | ✅ Implementada |
| 8 | Timeout modelo embeddings | MEDIA | ✅ Implementada |
| 9 | División por cero semántica | BAJA | ✅ Implementada |
| 10 | Validador alucinaciones | MEDIA | ✅ Implementada |
| 11 | Moneda dinámica | BAJA | ✅ Implementada |
| 12 | Resolución dual agentes | MEDIA | ✅ Implementada |
| 13 | Sincronización memorias | MEDIA | ✅ Implementada |
| 14 | Cache intenciones NLP | BAJA | ✅ Implementada |
| 15 | Typo Sself auditoría | ALTA | ✅ Implementada |
| 16 | NaN crash tablas HTML | ALTA | ✅ Implementada |

---

## 8. AUDITORÍA DE EMBEDDINGS Y COHERENCIA VECTORIAL (v7.5)

### ✅ V1/V2 — Embedding Function Explícita en ChromaDB (Lazy)
**Archivo:** `services/memory/memoria_vectorial.py` — `_inicializar_db()`, `_aplicar_embedding_function()`  
**Problema:** Las colecciones ChromaDB se creaban sin `embedding_function` explícita. ChromaDB usaba `all-MiniLM-L6-v2` (inglés) mientras el sistema usaba `paraphrase-multilingual-MiniLM-L12-v2` (multilingüe). Ambos generan 384 dims pero espacios vectoriales incompatibles → búsquedas semánticas retornaban resultados degradados.  
**Solución:** Carga lazy: colecciones se crean sin EF inicialmente, luego `_aplicar_embedding_function()` (llamada desde `_inicializar_embeddings()`) re-crea las colecciones con `SentenceTransformerEmbeddingFunction(model_name='paraphrase-multilingual-MiniLM-L12-v2')`. Evita timeout por import pesado durante init.  
**Severidad:** CRÍTICA

### ✅ V3 — guardar_alerta() Usa Embeddings Propios
**Archivo:** `services/memory/memoria_vectorial.py` — `guardar_alerta()`  
**Problema:** `guardar_alerta()` delegaba embeddings a ChromaDB default en vez de usar `self._generar_embedding()`.  
**Solución:** Genera embedding vía `self._generar_embedding(contenido)` antes de `.add()`, mismo patrón que `guardar_conversacion()`.  
**Severidad:** MEDIA

### ✅ V5 — Purga Selectiva por Colección
**Archivo:** `services/memory/memoria_vectorial.py` — `_controlar_crecimiento()`, `_purgar_coleccion()`  
**Problema:** Al exceder `MAX_DOCUMENTOS_POR_COLECCION`, se purgaban TODAS las colecciones indistintamente.  
**Solución:** Nuevo método `_purgar_coleccion(coleccion, dias)` que purga solo la colección afectada. Usa `coleccion.get(include=['metadatas'], limit=5000)` con batch.  
**Severidad:** MEDIA

### ✅ E2 — Hash de Cache Calculado sobre Corpus Real
**Archivo:** `services/nlp/motor_embeddings.py` — `_cargar_cache()`  
**Problema:** El hash de validación de cache iteraba `self.intenciones_map.items()` y hacía `.extend(frases)` donde `frases` era un dict (no lista), computando hash sobre keys del dict en vez de frases de entrenamiento reales.  
**Solución:** Reemplazado por `frases_actuales, _ = self._construir_corpus()` que construye correctamente las frases de entrenamiento.  
**Severidad:** ALTA

### ✅ E4 — Validación de Dimensionalidad en Cache
**Archivo:** `services/nlp/motor_embeddings.py` — `_cargar_cache()`  
**Problema:** No se validaba que la dimensionalidad del cache cargado coincidiera con la del modelo actual. Un cambio de modelo invalidaba el cache silenciosamente.  
**Solución:** Tras cargar cache, se verifica `self.embeddings_intenciones.shape[1] == self.modelo.get_sentence_embedding_dimension()`. Si no coincide, invalida cache.  
**Severidad:** MEDIA

### ✅ E3 — Limpieza de Socket Timeout
**Archivo:** `services/nlp/motor_embeddings.py`  
**Problema:** Referencia al socket no se liberaba tras restaurar timeout, reteniendo recurso.  
**Solución:** `del socket` tras restaurar `socket.setdefaulttimeout(timeout_original)`.  
**Severidad:** BAJA

---

## 9. AUDITORÍA DE GRAFO DE CONOCIMIENTO (v7.5)

### ✅ G1/G2 — Poda Proactiva de Nodos Huérfanos
**Archivo:** `services/memory/grafo_conocimiento.py` — `_podar_si_necesario()`  
**Problema:** Los nodos huérfanos (degree == 0) solo se limpiaban al superar `MAX_NODOS` (500). Después de eliminar aristas, los nodos quedaban huérfanos indefinidamente.  
**Solución:** Poda de huérfanos se ejecuta cuando `number_of_nodes() > 10` (no requiere superar MAX_NODOS). Limpia nodos sin aristas con `accesos < 2`, límite 200 por ciclo.  
**Severidad:** MEDIA

### ✅ G5 — Auto-Save Predecible con Contador
**Archivo:** `services/memory/grafo_conocimiento.py` — `registrar_interaccion()`  
**Problema:** Lógica `total_accesos % 5 == 0` sumaba todos los accesos de nodos ACCION, resultando en guardados impredecibles y no uniformes.  
**Solución:** `self._contador_interacciones` inicializado en `__init__`, incrementado en cada llamada. Guarda cuando `% 5 == 0`. Determinístico y uniforme.  
**Severidad:** MEDIA

---

## 10. AUDITORÍA DE LATENCIA Y METADATOS (v7.5)

### ✅ J3 — Sanitización de Metadatos para ChromaDB
**Archivo:** `services/memory/memoria_jerarquica.py` — `registrar_interaccion()`  
**Problema:** Metadatos non-serializable (listas, dicts, objetos) podían llegar a ChromaDB, causando errores silenciosos o crashes.  
**Solución:** Validación explícita de tipos: solo `str`, `int`, `float`, `bool` pasan directamente; otros tipos se convierten a `str(v)[:500]`. Valores `None` se omiten.  
**Severidad:** MEDIA

---

## RESUMEN DE ESTADO

| # | Mejora | Severidad | Estado |
|---|--------|-----------|--------|
| 1 | Guardrail mutación expandido | CRÍTICA | ✅ Implementada |
| 2 | Campos prohibidos LLM | CRÍTICA | ✅ Implementada |
| 3 | Word boundary multi-agente | CRÍTICA | ✅ Implementada |
| 4 | Límite ChromaDB | ALTA | ✅ Implementada |
| 5 | Advertencias al usuario | ALTA | ✅ Implementada |
| 6 | KPI sort safety | MEDIA | ✅ Implementada |
| 7 | Modelos prohibidos | MEDIA | ✅ Implementada |
| 8 | Timeout modelo embeddings | MEDIA | ✅ Implementada |
| 9 | División por cero semántica | BAJA | ✅ Implementada |
| 10 | Validador alucinaciones | MEDIA | ✅ Implementada |
| 11 | Moneda dinámica | BAJA | ✅ Implementada |
| 12 | Resolución dual agentes | MEDIA | ✅ Implementada |
| 13 | Sincronización memorias | MEDIA | ✅ Implementada |
| 14 | Cache intenciones NLP | BAJA | ✅ Implementada |
| 15 | Typo Sself auditoría | ALTA | ✅ Implementada |
| 16 | NaN crash tablas HTML | ALTA | ✅ Implementada |
| 17 | Embedding function ChromaDB (lazy) | CRÍTICA | ✅ Implementada |
| 18 | guardar_alerta embeddings propios | MEDIA | ✅ Implementada |
| 19 | Purga selectiva por colección | MEDIA | ✅ Implementada |
| 20 | Hash cache sobre corpus real | ALTA | ✅ Implementada |
| 21 | Validación dimensionalidad cache | MEDIA | ✅ Implementada |
| 22 | Limpieza socket timeout | BAJA | ✅ Implementada |
| 23 | Poda proactiva nodos huérfanos | MEDIA | ✅ Implementada |
| 24 | Auto-save predecible con contador | MEDIA | ✅ Implementada |
| 25 | Sanitización metadatos ChromaDB | MEDIA | ✅ Implementada |
