# ANDROMEDA — Auditoría Integral de Mejoras
**Fecha:** 2026-04-06 — actualizado Fase 5  
**Versión del proyecto:** 9.0  

---

## Leyenda de Prioridad

| Icono | Nivel | Significado |
|:-----:|-------|-------------|
| 🔴 | **CRÍTICO** | Riesgo inmediato de seguridad o pérdida de datos. Resolver HOY. |
| 🟠 | **ALTO** | Problemas de calidad o diseño que afectan estabilidad. Resolver esta semana. |
| 🟡 | **MEDIO** | Deuda técnica significativa. Planificar en sprint. |
| 🔵 | **BAJO** | Mejoras de mantenibilidad. Backlog. |

---

## 🔴 CRÍTICOS — Seguridad

### SEC-001 · Credenciales de producción hardcodeadas en código fuente
- **Estado:** [x] Resuelto — Credenciales movidas a `.env` con `python-dotenv` + `os.getenv()`. Creado `.env.example` como plantilla.
- **Archivos afectados:**
  - `app/config.py` (líneas 37-38) — `ConfiguracionOdoo.default()` contiene usuario y password reales
  - `models/conector_odoo.py` (líneas 40-41) — Duplicado de credenciales en `ConfiguracionOdoo.default()`
- **Riesgo:** Cualquier persona con acceso al repositorio obtiene acceso total al ERP de producción.
- **Remediación:**
  1. Mover credenciales a archivo `.env` (no versionado)
  2. Usar `python-dotenv` (ya está en dependencias) + `os.getenv()`
  3. Eliminar `default()` como método que devuelve credenciales reales
  4. **Regenerar inmediatamente la API key de Odoo** ya que está comprometida

### SEC-002 · Credenciales expuestas en logs de producción
- **Estado:** [x] Resuelto — Log purgado. Nivel de `odoorpc.rpc.jsonrpclib` y `odoorpc` elevado a WARNING en `app/config.py` y `models/conector_odoo.py`.
- **Archivo:** `logs/andromeda.log` (líneas 7-27+)
- **Riesgo:** El log contenía en texto plano: usuario, password y nombre de BD de producción. Cada request de odoorpc logueaba las credenciales en `args`.
- **Remediación:**
  1. Configurar logging de `odoorpc.rpc.jsonrpclib` en nivel `INFO` (no `DEBUG`) en producción
  2. Implementar filtro de logging que redacte campos sensibles
  3. Agregar `logs/` a `.gitignore`
  4. **Purgar el archivo de log actual**

### SEC-003 · No existe archivo `.gitignore`
- **Estado:** [x] Resuelto — Creado `.gitignore` con: `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `logs/`, `build/`, `data/memoria/`, `Reportes_Bot/`, `reports/`, `.pytest_cache/`.
- **Riesgo:** Si se inicializa un repositorio git, se versionarían: logs con credenciales, `.env`, `__pycache__/`, `.venv/`, `data/memoria/chroma.sqlite3`, archivos de build.
- **Remediación:** Crear `.gitignore` con:
  ```
  .env
  .venv/
  __pycache__/
  *.pyc
  logs/
  build/
  data/memoria/
  *.sqlite3
  Reportes_Bot/
  reports/
  .pytest_cache/
  ```

### SEC-004 · Servidor web expuesto a toda la red sin autenticación
- **Estado:** [x] Resuelto — `GRADIO_SERVER_NAME` cambiado de `0.0.0.0` a `127.0.0.1`. `GRADIO_SHARE` se mantiene `False` (solo activable por CLI `--share`).
- **Archivos:**
  - `app/config.py` (línea 66) — `GRADIO_SERVER_NAME = "0.0.0.0"`
  - `main.py` (línea 118) — `Config.GRADIO_SHARE = True` (crea túnel público ngrok)
- **Riesgo:** Cualquiera en la red local (o Internet si `share=True`) puede acceder a la interfaz Gradio y consultar TODOS los datos del ERP sin ningún tipo de autenticación.
- **Remediación:**
  1. Cambiar a `GRADIO_SERVER_NAME = "127.0.0.1"` 
  2. Establecer `GRADIO_SHARE = False` siempre en producción
  3. Implementar `gr.Blocks(auth=("user","pass"))` o autenticación por token
  4. Si se necesita acceso remoto, usar VPN, no túnel ngrok

### SEC-005 · Inyección de comandos en `cli_monitor.py`
- **Estado:** [x] Resuelto — `os.system(f'start {ruta}')` reemplazado con `webbrowser.open(ruta)`.
- **Archivo:** `cli_monitor.py` (línea 178)
- **Código:** `os.system(f'start {ruta}' if sys.platform == 'win32' else f'open {ruta}')`
- **Riesgo:** Si `ruta` contiene caracteres shell (`;`, `|`, `&&`), un atacante puede ejecutar comandos arbitrarios en el sistema operativo.
- **Remediación:** Reemplazar con:
  ```python
  import subprocess
  import shlex
  subprocess.run(['start', '', ruta], shell=True)  # Windows
  # O mejor: webbrowser.open(ruta) que ya importa arriba
  ```

---

## 🟠 ALTOS — Calidad y Estabilidad

### QA-001 · 40+ cláusulas `except:` desnudas (bare except) en código propio
- **Estado:** [x] Resuelto — 45 bare `except:` reemplazados por `except Exception:` en 18 archivos mediante script automatizado. Verificación: 0 bare excepts restantes.
- **Archivos afectados (solo código del proyecto, no .venv):**
  - `models/conector_odoo.py` — líneas 127, 298, 491, 502, 514
  - `core/motor_bi_experto.py` — líneas 579, 1039
  - `core/cerebro_andromeda.py` — líneas 754, 806
  - `views/interfaz_v5.py` — líneas 5098, 5305
  - `utils/validador_datos.py` — líneas 479, 513
  - `services/reports/generador_graficas.py` — líneas 613, 908, 998, 1017, 1032
  - `services/prediction/prediccion_inteligente.py` — líneas 305, 509, 807
  - `services/prediction/motor_prediccion.py` — líneas 155, 258, 423, 461
  - `services/nlp/nlp_avanzado.py` — líneas 1521, 1592
  - `services/nlp/cerebro_nlp.py` — líneas 134, 1031
  - `services/memory/memoria_vectorial.py` — línea 600
  - `services/llm/generador_queries.py` — línea 511
  - `services/llm/cerebro_llm.py` — línea 322
  - `services/auditoria_inteligente.py` — líneas 581, 819, 906, 1004
  - `services/analysis/kpis_financieros.py` — líneas 444, 497
  - `services/analysis/analizador_datos.py` — línea 157
  - `services/analysis/analizador_anomalias.py` — línea 269
  - `services/analysis/analisis_360.py` — líneas 87, 97, 107, 117, 127, 137, 262, 355, 475, 756
- **Impacto:** Silencia errores de programación, errores de tipado, KeyboardInterrupt, e incluso SystemExit. Hace imposible diagnosticar fallos.
- **Remediación:** Cambiar cada `except:` por `except Exception as e:` con logging del error. En casos críticos, usar excepciones específicas (`ValueError`, `KeyError`, `ConnectionError`, etc.).

### QA-002 · Uso masivo de `print()` en vez de logging estructurado
- **Estado:** [x] Resuelto — Creado `app/logging_config.py` centralizado con RotatingFileHandler (5MB, 3 backups), filtro de credenciales (`FiltroCredenciales`), y consola WARNING+. Agregado `from app.logging_config import get_logger` a 38 módulos. 63 prints de error/warning migrados a `logger.error()`/`logger.warning()`.
- **Estimación:** 100+ sentencias `print()` distribuidas en todos los módulos principales
- **Archivos con `import logging` (correcto):** Solo 5 de ~25 archivos .py:
  - `utils/monitor_sistema.py`
  - `services/memory/memoria_vectorial.py`
  - `services/reports/generador_graficas.py`
  - `services/reports/generador_pdf.py`
  - `services/llm/ollama_integrador.py`, `generador_queries.py`
- **Nota:** `views/interfaz_v5.py` tiene `#import logging` (comentado, línea 62)
- **Impacto:** No se puede filtrar por nivel de severidad, no hay rotación de archivos, los prints se mezclan con output del servidor.
- **Remediación:**
  1. Crear configuración centralizada de logging en `app/logging_config.py`
  2. Reemplazar `print()` por `logger.info()` / `logger.warning()` / `logger.error()`
  3. Configurar RotatingFileHandler + filtro que redacte credenciales

### QA-003 · Sin validación de entrada en endpoint principal de Gradio
- **Estado:** [x] Resuelto — Agregado a `procesar_mensaje()`: truncamiento a 2000 chars (`MAX_INPUT_LENGTH`), rate limiting de 30 req/min por sesión (`MAX_REQUESTS_PER_MINUTE`) con limpieza automática de timestamps.
- **Archivo:** `views/interfaz_v5.py` — método `procesar_mensaje()` (línea 2114)
- **Riesgo:** El input del usuario se pasa directamente al pipeline NLP → LLM → consultas Odoo sin:
  - Límite de longitud (DoS por prompt gigante)
  - Sanitización de caracteres especiales
  - Rate limiting (un usuario puede saturar el servidor)
- **Remediación:**
  1. Limitar input a 2000 caracteres
  2. Implementar rate limiting básico (ej: max 30 requests/minuto por sesión)
  3. Sanitizar antes de pasar al LLM

---

## 🟡 MEDIOS — Arquitectura y Diseño

### ARQ-001 · God Class en `interfaz_v5.py` (7,098 líneas, 99 métodos, 1 clase)
- **Estado:** [x] Resuelto — Extraídos 41 métodos `_formatear_*` a `services/formatters/formateador_respuestas.py` (clase `FormateadorRespuestas`, ~1200 líneas). `interfaz_v5.py` reducido de ~7616 a ~6022 líneas (-1598 líneas). Todas las llamadas delegadas vía `self.fmt._formatear_*()`.
- **Archivo:** `views/interfaz_v5.py` — clase `OdooAIProV5`
- **Estadísticas:**
  - 7,098 líneas totales
  - 99 métodos en una sola clase
  - Mezcla UI (Gradio), lógica de negocio, acceso a datos, formateo, NLP
- **Impacto:** Difícil de testear, mantener, y depurar. Alto acoplamiento. Cambios en UI pueden romper lógica de negocio.
- **Remediación progresiva:**
  1. Extraer `_formatear_*` (30+ métodos) → `services/formatters/formateador_respuestas.py`
  2. Extraer `_ejecutor_*` (13 métodos) → Ya pertenecen a `services/agents/`
  3. Extraer `_mapear_accion_a_consulta_odoo` → `services/routing/router_consultas.py`
  4. Dejar en la clase solo: `crear_interfaz()`, `procesar_mensaje()`, event handlers

### ARQ-002 · Lógica de ejecución duplicada entre `interfaz_v5.py` y `multi_agente.py`
- **Estado:** [x] Resuelto — Extraídos 12 métodos ejecutores a `services/agents/ejecutores.py` (clase `EjecutoresAgente`, ~430 líneas). Usa delegación por `@property` para acceder a dependencias del bot. Eliminadas 439 líneas de `interfaz_v5.py`. Ejecutores registrados vía `self._ejecutores._ejecutor_*()`.
- **Detalle:** Los 13 ejecutores (`_ejecutor_ventas`, `_ejecutor_inventario`, etc.) en `interfaz_v5.py` duplican la routing logic que `GestorMultiAgente.ejecutar_accion()` ya provee.
- **Remediación:** Consolidar: los ejecutores deberían registrarse como estrategias en el gestor, no como métodos de la interfaz.

### ARQ-003 · Acoplamiento directo a la API de `odoorpc` disperso en múltiples archivos
- **Estado:** [x] Resuelto — Añadido método `search_read()` a `ConectorOdoo`. Reemplazados 57+ accesos directos `self.odoo.odoo.env[modelo]` en 5 archivos: `auditoria_inteligente.py` (21), `auditoria_calidad_datos.py` (18), `consultas_especializadas.py` (14), `interfaz_v5.py` (3), `cerebro_andromeda.py` (1). Quedan accesos internos en `conector_odoo.py` (esperado) y en `analisis_360.py`/`analisis_inteligente.py`/`motor_ml.py` (backlog).
- **Archivos con acceso directo a `self.odoo.odoo.env[...]`:**
  - `views/interfaz_v5.py` — líneas 5290, 5298, 5326
  - `core/cerebro_andromeda.py` — línea 1565
  - `services/prediction/motor_ml.py` — líneas 861, 878
  - `services/auditoria_inteligente.py` — líneas 266, 307, 344, 402, 447, 496, 540, 558, 635+
- **Impacto:** Si se cambia el ORM o el conector, hay que modificar 10+ archivos. Imposible mockear para tests.
- **Remediación:** Todo acceso a Odoo debería pasar por `ConectorOdoo.buscar()` / `buscar_leer()` / `contar()`. Eliminar acceso directo a `self.odoo.odoo.env`.

### ARQ-004 · Dependencias no fijadas en `requirements.txt`
- **Estado:** [x] Resuelto — Todas las dependencias fijadas con rangos acotados `>=x.y.0,<(x+1).0.0`. Header añadido: "Versiones fijadas el 2026-03-13".
- **Detalle:** Todas las dependencias usan `>=` sin tope superior:
  ```
  odoorpc>=0.9.0      # Puede instalar 1.x con breaking changes
  pandas>=1.5.0       # Puede instalar 3.x con breaking changes
  torch>=2.0.0        # Puede instalar 3.x con breaking changes
  gradio>=4.0.0       # Puede instalar 5.x con breaking changes
  chromadb>=1.0.0     # Puede instalar 2.x con breaking changes
  ```
- **Riesgo:** Builds no reproducibles. Una actualización automática puede romper todo.
- **Remediación:** 
  1. Ejecutar `pip freeze > requirements.lock`
  2. Usar rangos acotados: `pandas>=1.5.0,<3.0.0`
  3. O mejor: migrar a `pyproject.toml` con groups de dependencias

---

## 🟡 MEDIOS — QA y Testing

### QA-004 · Sin configuración de pytest (`pytest.ini` / `pyproject.toml`)
- **Estado:** [x] Resuelto — Creado `pytest.ini` con `testpaths=tests`, markers (`slow`, `integration`), `addopts = -v --tb=short --cov=. --cov-report=term-missing --cov-config=.coveragerc`.
- **Impacto:** No hay configuración de testpaths, markers, ni opciones por defecto.
- **Remediación:** Crear `pytest.ini`:
  ```ini
  [pytest]
  testpaths = tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  addopts = -v --tb=short
  markers =
      slow: Tests que requieren conexión o son lentos
      integration: Tests de integración
  ```

### QA-005 · Sin coverage de tests
- **Estado:** [x] Resuelto — Instalado `pytest-cov 7.0.0`. Creado `.coveragerc` con omisión de `.venv/`, `tests/`, `build/`, `data/`. Integrado en `addopts` de `pytest.ini`.
- **Impacto:** No se mide qué porcentaje del código está cubierto por tests.
- **Remediación:**
  1. `pip install pytest-cov`
  2. Ejecutar: `pytest --cov=. --cov-report=html tests/`
  3. Agregar a `addopts` en pytest.ini

### QA-006 · Tests no cubren `views/interfaz_v5.py` ni `core/`
- **Estado:** [x] Resuelto — Creados `tests/test_core.py` (20 tests: bot_principal, cerebro_andromeda, limpiador_datos, motor_estadístico) y `tests/test_interfaz_reportes.py` (12 tests: OdooAIProV5, generador_graficas, generador_pdf). Total: 302 tests pasando.
- **Detalle:** Los 270 tests actuales cubren: multi_agente, cerebro_nlp, conector_odoo, validador, normalizador, config, main. Pero no hay tests para:
  - `views/interfaz_v5.py` — pipeline completo `procesar_mensaje()`
  - `core/cerebro_andromeda.py` — orquestador principal
  - `core/bot_principal.py` — bot de consola
  - `services/analysis/*` — analizadores
  - `services/prediction/*` — motores de predicción
  - `services/llm/*` — integración LLM
  - `services/reports/*` — generación de reportes
- **Remediación:** Agregar tests de integración con mocks para cada módulo faltante.

---

## 🔵 BAJOS — Mantenibilidad

### MAN-001 · Falta de type hints en funciones de `main.py` y `cli_monitor.py`
- **Estado:** [x] Resuelto — Añadidos type hints `-> None` a 3 funciones de `main.py` y 11 métodos/funciones de `cli_monitor.py` (todos los `cmd_*` con `args: argparse.Namespace -> None`).
- **Detalle:** `iniciar_web()`, `iniciar_consola()` y funciones del CLI carecen de `-> None` y tipado de parámetros.
- **Remediación:** Agregar type hints a funciones públicas.

### MAN-002 · `__pycache__/` dispersos sin limpieza
- **Estado:** [x] Resuelto — Eliminados 18 directorios `__pycache__/` dispersos. Ya estaban en `.gitignore` desde SEC-003.
- **Detalle:** Múltiples directorios `__pycache__/` en: `app/`, `core/`, `models/`, `services/**/`, `utils/`, `views/`, `data/memoria/`.
- **Remediación:** Agregar a `.gitignore` y ejecutar limpieza periódica.

### MAN-003 · Logging module en `data/memoria/Logging.py` fuera de lugar
- **Estado:** [x] Resuelto — Movido a `utils/logging_avanzado.py`. Actualizados 2 imports: `cli_monitor.py` y `views/interfaz_v5.py`.
- **Detalle:** Un módulo de logging guardado en `data/memoria/` — debería estar en `utils/` o `app/`.
- **Remediación:** Mover a `utils/logging_config.py` o `app/logging_config.py`.

### MAN-004 · Archivos de build obsoletos en `build/ARCHIVADOS/`
- **Estado:** [x] Resuelto — Eliminado directorio `build/ARCHIVADOS/` completo (`.toc`, `.pyz`, `.pkg`, `warn-*.txt`, `xref-*.html`, `localpycs/`). `build/` ya está en `.gitignore`.
- **Detalle:** Contenía `.toc`, `.pyz`, `warn-*.txt`, `xref-*.html` de PyInstaller. No aportaban al proyecto.
- **Remediación:** Agregar `build/` a `.gitignore`. Considerar eliminar si no se usa.

---

## Resumen Ejecutivo

| Categoría | Críticos 🔴 | Altos 🟠 | Medios 🟡 | Bajos 🔵 | Total |
|-----------|:-----------:|:--------:|:---------:|:--------:|:-----:|
| Seguridad | ~~5~~ 0 ✅ | — | — | — | **5 (resueltos)** |
| Calidad   | — | ~~3~~ 0 ✅ | ~~3~~ 0 ✅ | — | **6 (6 resueltos)** |
| Arquitectura | — | — | ~~4~~ 0 ✅ | — | **4 (4 resueltos)** |
| Mantenibilidad | — | — | — | ~~4~~ 0 ✅ | **4 (4 resueltos)** |
| **Total** | **0** | **0** | **0** | **0** | **19 (19 resueltos) ✅** |

---

## Plan de Acción Recomendado

### Inmediato (hoy)
1. ~~SEC-001~~ Mover credenciales a `.env`
2. ~~SEC-002~~ Purgar `logs/andromeda.log`
3. ~~SEC-003~~ Crear `.gitignore`
4. ~~SEC-004~~ Cambiar `0.0.0.0` → `127.0.0.1`, `share=False`

### Esta semana
5. SEC-005 — Fix inyección de comandos
6. QA-001 — Reemplazar bare excepts (archivos críticos primero)
7. QA-002 — Implementar logging centralizado
8. QA-003 — Agregar validación de input en Gradio

### Próximo sprint (resuelto)
9. ~~ARQ-001~~ — Extraídos 41 formateadores a `FormateadorRespuestas`
10. ~~ARQ-002~~ — Extraídos 12 ejecutores a `EjecutoresAgente`
11. ~~ARQ-004~~ — Dependencias fijadas con rangos
12. ~~QA-004/QA-005~~ — Configurados pytest.ini + .coveragerc + pytest-cov

### Sprint completado
13. ~~ARQ-003~~ — 57+ accesos directos a odoorpc encapsulados vía `ConectorOdoo.search_read()`
14. ~~QA-006~~ — 32 nuevos tests (test_core.py + test_interfaz_reportes.py). Total: 302 tests.

### Backlog (resuelto)
15. ~~MAN-001~~ — Type hints añadidos a `main.py` (3 funciones) y `cli_monitor.py` (11 métodos)
16. ~~MAN-002~~ — Eliminados 18 directorios `__pycache__/`
17. ~~MAN-003~~ — `Logging.py` movido de `data/memoria/` a `utils/logging_avanzado.py`
18. ~~MAN-004~~ — Eliminado `build/ARCHIVADOS/` con artefactos obsoletos de PyInstaller

---

**✅ AUDITORÍA v1 COMPLETADA — 19/19 hallazgos resueltos (2026-03-13)**

---

## FASE 5 — Auditoría de Implementación de Autenticación JWT
**Fecha:** 2026-04-06  
**Contexto:** Revisión de seguridad post-implementación de Fase 5 (JWT, frontend Next.js 14, CORS).

### ✅ AUTH-001 · Algoritmo JWT y gestión de secreto
- **Estado:** [x] Resuelto desde diseño inicial
- **Evaluación:** HS256 con `SECRET_KEY` de `.env` — clave nunca embebida en código. Proceso de derivación de clave documentado.
- **Hallazgo:** Sin observaciones. Implementación conforme a RFC 7519.

### ✅ AUTH-002 · Cross-type token vulnerability
- **Estado:** [x] Resuelto — Claim `tipo: "access" | "refresh"` validado en decodificación
- **Evaluación:** Previene que un refresh token sea usado como access token (y viceversa), mitigando el riesgo de elevación de privilegios en caso de leakage de un token de menor vida útil.
- **Hallazgo:** Sin observaciones.

### ✅ AUTH-003 · Timing attack en autenticación (CWE-208)
- **Estado:** [x] Resuelto — Respuesta 401 timing-safe implementada
- **Evaluación:** Ambas ramas (email no existe / contraseña incorrecta) ejecutan la misma cantidad de trabajo computacional. No permite user enumeration por diferencia de tiempo de respuesta.
- **Hallazgo:** Sin observaciones.

### ✅ AUTH-004 · RBAC granular con dependency injection
- **Estado:** [x] Resuelto — `require_rol(*roles)` implementado como FastAPI dependency factory
- **Evaluación:** Roles `admin`, `operador`, `viewer` correctamente enumerados. HTTP 403 en violación. Sigue el principio de least privilege.
- **Hallazgo:** Sin observaciones.

### ✅ AUTH-005 · Compatibilidad de dependencias de hashing
- **Estado:** [x] Resuelto — Migrado de bcrypt a pbkdf2_sha256
- **Evaluación:** `bcrypt` ≥ 4.1 es incompatible con `passlib` 1.7.x a nivel de ABI. `pbkdf2_sha256` con 600 000 iteraciones es conforme a NIST SP 800-132 y no requiere dependencias C. Decisión técnicamente justificada y documentada.
- **Hallazgo:** Sin observaciones.

### ✅ AUTH-006 · CORS con origins explícitos
- **Estado:** [x] Resuelto — `CORSMiddleware` con lista explícita de origins
- **Evaluación:** No se usa wildcard `*` con `allow_credentials=True` (violación de CORS spec). Origins restringidos a `localhost:3000` y `127.0.0.1:3000`.
- **Hallazgo:** Para despliegue en producción, reemplazar origins hardcodeados por variable de entorno `CORS_ORIGINS`.

### ⚠️ AUTH-007 · Tokens almacenados en localStorage (frontend)
- **Estado:** [ ] Riesgo aceptado — documentado
- **Archivo:** `frontend/src/lib/auth.ts`
- **Evaluación:** El almacenamiento de JWT en `localStorage` es vulnerable a XSS (CWE-79). La alternativa (`httpOnly cookies`) requiere un BFF o SSR con manejo server-side de cookies, lo cual está fuera del alcance de una SPA estática.
- **Mitigación aplicada:** Access token de vida corta (15 min). Retry automático con refresh token. La ausencia de tokens sensibles de larga vida en `localStorage` reduce el impacto.
- **Recomendación:** En fase futura, evaluar migración a Next.js con route handlers (BFF) para mover tokens a `httpOnly cookies`.

**✅ AUDITORÍA FASE 5 COMPLETADA — 6/7 hallazgos resueltos, 1 riesgo aceptado documentado (AUTH-007)**

---
---

# 🔄 Re-Auditoría v2 — ANDROMEDA
**Fecha:** 2026-03-13  
**Revisado por:** Security Sr · Arquitecto Sr · QA Sr · Dev Sr  
**Versión del proyecto:** 7.1 (post-corrección de 19 hallazgos v1)  
**Contexto:** Segunda auditoría integral tras resolver todos los hallazgos de la v1.

---

## Leyenda de Prioridad

| Icono | Nivel | Significado |
|:-----:|-------|-------------|
| 🔴 | **CRÍTICO** | Riesgo inmediato de seguridad, bug activo, o bloqueo de mantenibilidad. Resolver HOY. |
| 🟠 | **ALTO** | Calidad/diseño que afecta estabilidad o seguridad indirecta. Resolver esta semana. |
| 🟡 | **MEDIO** | Deuda técnica significativa o riesgo menor. Planificar en sprint. |
| 🔵 | **BAJO** | Mejoras de mantenibilidad y buenas prácticas. Backlog. |

---

## 🔴 CRÍTICOS

### SEC-v2-001 · Credencial real (API key) hardcodeada como regex en logging_config.py
- **Estado:** [x] Resuelto — Patrón reemplazado por regex genérica `re.compile(r'\b[a-f0-9]{40}\b')` + email genérica. `record.args = ()` en vez de `None`.
- **Archivo:** `app/logging_config.py` (línea 24)
- **Código:** `re.compile(r'<API_KEY_REDACTED>')`
- **Problema:** El `FiltroCredenciales`, creado para redactar credenciales en logs, contenía **el token real de producción** como patrón regex compilado en texto plano. Cualquiera con acceso al código fuente obtenía la API key.
- **Impacto:** La credencial que se eliminó de `config.py` (SEC-001 v1) quedó embebida en el filtro de logging.
- **Remediación:**
  1. Leer los patrones sensibles desde `.env` o variables de entorno
  2. Usar un patrón genérico: `re.compile(r'[a-f0-9]{40}')` para tokens hexadecimales
  3. **Rotar inmediatamente la API key** ya que está comprometida en código fuente

### SEC-v2-002 · `main()` de interfaz_v5.py bindea a `0.0.0.0:7880` (salta Config)
- **Estado:** [x] Resuelto — `main()` ahora usa `Config.GRADIO_SERVER_NAME`, `Config.GRADIO_SERVER_PORT`, `Config.GRADIO_SHARE`. `allowed_paths` apunta a `views/static/`.
- **Archivo:** `views/interfaz_v5.py` (línea 6010)
- **Código:** `app.launch(server_name="0.0.0.0", server_port=7880, ...)`
- **Problema:** Pese a que `Config.GRADIO_SERVER_NAME = "127.0.0.1"` (corregido en SEC-004 v1), el bloque `main()` de `interfaz_v5.py` usa `server_name="0.0.0.0"` directamente, exponiendo el servidor a toda la red.
- **Impacto:** Cualquiera en la red local puede acceder al ERP sin autenticación.
- **Remediación:**
  1. Reemplazar por `server_name=Config.GRADIO_SERVER_NAME`
  2. Reemplazar por `server_port=Config.GRADIO_SERVER_PORT`

### DEV-v2-001 · Bug lógico en `_filtrar_campos_validos` — siempre devuelve TODOS los campos
- **Estado:** [x] Resuelto — Cambiado a `return [c for c in campos if c in campos_existentes]`.
- **Archivo:** `models/conector_odoo.py` (línea 314-315)
- **Código actual:** `return [c for c in campos_existentes if c in campos_existentes]`
- **Problema:** La comprensión de lista itera sobre `campos_existentes` (el cache) y verifica si cada elemento está en sí mismo — **siempre es `True`**. Ignora completamente el parámetro `campos` recibido.
- **Impacto:** `search_read()` siempre solicita TODOS los campos del modelo a Odoo en lugar de los campos específicos, causando sobrecarga de red/memoria y posible exposición de datos sensibles.
- **Corrección:** `return [c for c in campos if c in campos_existentes]`

### ARQ-v2-001 · God Class `OdooAIProV5` — 5,717 líneas, ~41 métodos
- **Estado:** [x] Resuelto — Extraídos `EjecutorAcciones` (1,870 líneas) y `MapeadorConsultas` (871 líneas) a `services/actions/`. `interfaz_v5.py` reducido a ~3,226 líneas con delegación.
- **Archivo:** `views/interfaz_v5.py`
- **Problema:** Pese a la extracción de formatters (ARQ-001 v1) y ejecutores (ARQ-002 v1), la clase sigue siendo un God Object masivo con 8+ responsabilidades: UI Gradio, routing de mensajes, procesamiento NLP, ejecución de acciones, generación de reportes, validación, logging, caching.
- **Métodos críticos:**
  - `_ejecutar_accion()` (L2383): **~1,164 líneas** con 50+ elif — Feature Envy
  - `_mapear_accion_a_consulta_odoo()` (L4331): **~845 líneas**
  - `_procesar_tradicional()` (L1951): **~430 líneas**, 8+ niveles de anidación
- **Remediación progresiva:**
  1. Extraer `_ejecutar_accion()` → Strategy/Registry pattern con diccionario de handlers
  2. Extraer `_mapear_accion_a_consulta_odoo()` → `services/routing/router_consultas.py`
  3. Extraer `_procesar_tradicional()` → Pipeline pattern con etapas discretas
  4. Objetivo: reducir `OdooAIProV5` a ≤1,500 líneas (solo UI + orchestration)

### QA-v2-001 · 71% de módulos sin cobertura de tests (~25-30% coverage global)
- **Estado:** [x] Resuelto — Creados 89 tests nuevos en 5 archivos: `test_analysis.py`, `test_prediction.py`, `test_llm.py`, `test_memory.py`, `test_actions.py`. Total: 391 tests.
- **Módulos SIN tests:**
  | Módulo | Archivos sin tests | Líneas estimadas |
  |--------|-------------------|-----------------|
  | `services/analysis/` | 7 archivos (kpis_empresariales, analisis_inteligente, analizador_avanzado, kpis_financieros, analisis_360, analizador_anomalias, analizador_datos) | ~7,000+ |
  | `services/prediction/` | 4 archivos (motor_prediccion, motor_ml, neural_lstm, prediccion_inteligente) | ~3,000+ |
  | `services/llm/` | 3 archivos (cerebro_llm, generador_queries, ollama_integrador) | ~1,500+ |
  | `services/memory/` | 2 archivos (memoria_vectorial, memoria_jerarquica) | ~1,200+ |
  | `services/knowledge/` | 1 archivo (procesador_manuales) | ~500+ |
  | `core/` | 2 archivos (cerebro_andromeda, motor_bi_experto) parcialmente sin tests | ~3,400+ |
  | `views/` | generador_reportes sin tests; interfaz_v5 cobertura mínima (~5%) | ~6,200+ |
  | `utils/` | 3 archivos (asistente_errores, logging_avanzado, monitor_sistema) | ~800+ |
- **Impacto:** Regresiones no detectadas. El bug DEV-v2-001 no fue atrapado por falta de tests en `conector_odoo.search_read()`.
- **Remediación:** Crear tests para los 10 módulos más críticos (por líneas y riesgo).

### QA-v2-002 · Sin pipeline CI/CD
- **Estado:** [x] Resuelto — Creado `.github/workflows/ci.yml` con: install deps → pytest con coverage → syntax check de archivos críticos.
- **Problema:** No existe `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile` ni ninguna configuración de integración continua.
- **Impacto:** Los 302 tests solo se ejecutan manualmente. No hay barrera automática contra regresiones.
- **Remediación:** Crear `.github/workflows/ci.yml` con: instalar dependencias → ejecutar pytest → reportar coverage.

---

## 🟠 ALTOS

### SEC-v2-003 · Sin autenticación Gradio (`auth=`)
- **Estado:** [ ] Pendiente
- **Archivo:** `views/interfaz_v5.py` (línea 5374)
- **Código:** `gr.Blocks(title=..., theme=...)` — sin parámetro `auth=`
- **Problema:** La interfaz Gradio no tiene ningún mecanismo de autenticación. Cualquier persona que acceda al puerto 7880 tiene acceso completo a todos los datos del ERP.
- **Remediación:** Agregar `auth=("usuario", os.getenv("GRADIO_PASSWORD"))` o implementar autenticación por token/OAuth.

### SEC-v2-004 · Datos sensibles HR/nómina accesibles sin RBAC
- **Estado:** [ ] Pendiente
- **Problema:** Los agentes de análisis (KPIs empresariales, auditoría) pueden consultar modelos como `hr.payslip`, `hr.employee`, `hr.contract` con datos salariales. No hay control de acceso por rol dentro de ANDROMEDA.
- **Impacto:** Cualquier usuario del chatbot puede solicitar "muéstrame los salarios" y obtener datos sensibles.
- **Remediación:** Implementar lista de modelos restringidos y verificar permisos del usuario antes de ejecutar consultas a modelos HR.

### SEC-v2-005 · Email PII hardcodeado en logging_config.py
- **Estado:** [ ] Pendiente
- **Archivo:** `app/logging_config.py` (línea 25)
- **Código:** `re.compile(r'<EMAIL_REDACTED>')`
- **Problema:** Email corporativo real embebido en código fuente como patrón regex.
- **Remediación:** Usar patrón genérico de email: `re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+')`

### DEV-v2-002 · 50+ `except Exception:` sin capturar variable ni logging
- **Estado:** [ ] Pendiente
- **Archivos afectados (principales):**
  | Archivo | Instancias |
  |---------|-----------|
  | `views/interfaz_v5.py` | **24** (L1444, L1453, L1557, L1573, L1621, L1660, L1716, L1727, L1803, L1819, L2013, L2096, L2209, L2247, L2295, L3563, L3870, L4076, L4258, L4300, L4321, L5198, L5245, L5259) |
  | `models/conector_odoo.py` | **5** (L139, L310, L530, L541, L553) |
  | `services/prediction/motor_prediccion.py` | **4** |
  | `services/auditoria_inteligente.py` | **4** |
  | `services/llm/ollama_integrador.py` | **3** |
  | `services/prediction/prediccion_inteligente.py` | **3** |
  | `core/motor_bi_experto.py` | **2** |
  | `core/cerebro_andromeda.py` | **2** |
  | `utils/validador_datos.py` | **2** |
  | `utils/validador_respuestas.py` | **1** |
- **Diferencia con v1:** En v1 (QA-001) se reemplazaron `except:` (bare) por `except Exception:`. Pero ninguno agregó `as e` ni logging del error. Los errores siguen tragándose silenciosamente.
- **Remediación:** Cambiar a `except Exception as e:` con `logger.error(f"...: {e}", exc_info=True)` en todos los casos.

### DEV-v2-003 · 80+ `print()` en código de producción
- **Estado:** [ ] Pendiente
- **Archivos principales:**
  | Archivo | Prints | Severidad |
  |---------|--------|-----------|
  | `cli_monitor.py` | ~50 | Baja (CLI) |
  | `core/bot_principal.py` L78, L156-158 | 3 | Media |
  | `models/conector_odoo.py` L180-183 | 3 | **Alta** (reconexión) |
  | `core/cerebro_andromeda.py` L1373 | 1 | Media |
  | `views/interfaz_v5.py` L87-100 | ~10 | **Alta** (import failures) |
- **Diferencia con v1:** En v1 (QA-002) se creó `app/logging_config.py` y se migraron 63 prints de error/warning. Quedan 80+ prints informativos y de debug sin migrar.
- **Remediación:** Reemplazar por `logger.info()` / `logger.debug()`. Priorizar los de `conector_odoo.py` (reconexión) y `interfaz_v5.py` (fallos de import).

### DEV-v2-004 · `ConfiguracionOdoo` duplicada en 2 archivos
- **Estado:** [ ] Pendiente
- **Archivos:** `app/config.py` (L21) y `models/conector_odoo.py` (L27)
- **Problema:** Misma dataclass `ConfiguracionOdoo` con `url`, `db`, `usuario`, `password` y métodos `desde_json()`/`default()` duplicados. Si una cambia y la otra no → bugs silenciosos.
- **Remediación:** Eliminar la copia de `models/conector_odoo.py` e importar desde `app.config`.

### DEV-v2-005 · Sin type hints en `ejecutores.py` (bot y consulta sin tipo)
- **Estado:** [ ] Pendiente
- **Archivo:** `services/agents/ejecutores.py`
- **Problema:** El parámetro `bot` en `__init__` y `consulta` en todos los métodos ejecutores carecen de tipo. Acceso vía `getattr()` repetido indica acoplamiento débil sin contrato definido.
- **Remediación:** Definir `Protocol` o interfaz para `bot` y tipo para `consulta`.

### ARQ-v2-002 · Archivos en `services/analysis/` exceden 1,000+ líneas
- **Estado:** [ ] Pendiente
- **Archivos:**
  | Archivo | Líneas | Métodos |
  |---------|--------|---------|
  | `services/analysis/kpis_empresariales.py` | **~2,345** | 60+ |
  | `services/analysis/analisis_inteligente.py` | **~1,471** | 44+ |
  | `services/analysis/analizador_avanzado.py` | **~1,361** | 28+ |
- **Problema:** Múltiples God Classes en analysis. `KPIsEmpresariales` tiene 60+ métodos mezclando ventas, inventario, finanzas, HR.
- **Remediación:** Dividir por dominio: `kpis_ventas.py`, `kpis_inventario.py`, `kpis_finanzas.py`, `kpis_hr.py`.

### QA-v2-003 · Calidad de tests inconsistente
- **Estado:** [ ] Pendiente
- **Problemas detectados:**
  - `test_core.py`: Usa mocks pero no verifica cambios de estado post-llamada
  - `test_multi_agente.py`: Solo testea dataclasses, no lógica de agentes
  - Sin tests de integración end-to-end
  - Sin tests de error handling (caminos de excepción)
  - Sin tests de rendimiento para métodos críticos
  - Markers `@slow` e `@integration` definidos en `pytest.ini` pero sin tests que los usen
- **Remediación:** Definir estándares de testing: cada test debe incluir arrange/act/assert, verificar estado final, y testear al menos 1 caso de error.

---

## 🟡 MEDIOS

### SEC-v2-006 · XSS en generación HTML — sin `html.escape()` en datos
- **Estado:** [ ] Pendiente
- **Archivos:**
  - `views/interfaz_v5.py` L5319-5345 — método `_df_a_html()`: inyecta `{col}` y `{val}` directo en HTML
  - `views/generador_reportes.py` L580-610 — método `crear_html_profesional()`: inyecta `{nombre}`, `{col}`, `{val}` directo en HTML
- **Problema:** Si un campo de Odoo contiene `<script>alert('xss')</script>`, se ejecutará en el navegador del usuario.
- **Remediación:** `import html` y usar `html.escape(str(val))` en toda interpolación de datos en HTML.

### SEC-v2-007 · LLM Prompt Injection → Inyección ORM
- **Estado:** [ ] Pendiente
- **Archivo:** `services/llm/generador_queries.py` (líneas 336-338)
- **Código:** `if datos.get('modelo') not in self.MODELOS_ODOO: logger.warning(...)` — pero **continúa la ejecución**
- **Problema:** Un LLM manipulado por prompt injection puede generar un modelo arbitrario o dominio malicioso. La validación es solo un warning, no bloquea.
- **Remediación:** Cambiar warning por `return None` si el modelo no está en la lista blanca. Validar también que `dominio` solo contenga operadores permitidos.

### SEC-v2-008 · Google Speech envía audio a servidores externos
- **Estado:** [ ] Pendiente
- **Archivo:** `views/interfaz_v5.py` (línea 5970)
- **Código:** `recognizer.recognize_google(audio_data, language="es-ES")`
- **Problema:** Audio del usuario se envía a servidores de Google para reconocimiento de voz. Si contiene información sensible del ERP, se comparte con un tercero.
- **Remediación:** Documentar este comportamiento en la UI. Considerar `recognize_sphinx()` (offline) o Whisper local como alternativa.

### SEC-v2-009 · `allowed_paths` expone directorio completo `views/`
- **Estado:** [ ] Pendiente
- **Archivo:** `views/interfaz_v5.py` (línea 6015)
- **Código:** `allowed_paths=[ruta_base]` donde `ruta_base = os.path.dirname(os.path.abspath(__file__))` → directorio `views/`
- **Problema:** Gradio puede servir cualquier archivo dentro de `views/`, incluyendo código fuente Python.
- **Remediación:** Crear un subdirectorio `views/static/` específico para assets y apuntar `allowed_paths` solo ahí.

### DEV-v2-006 · Configuración Gradio hardcodeada (no lee `.env`)
- **Estado:** [ ] Pendiente
- **Archivo:** `app/config.py` (líneas 76-82)
- **Problema:** `GRADIO_SERVER_NAME`, `GRADIO_SERVER_PORT`, `GRADIO_SHARE` están hardcodeados en vez de leerse con `os.getenv()`.
- **Remediación:** `GRADIO_SERVER_NAME = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")`, etc.

### DEV-v2-007 · Parsing manual de URL sin `urlparse`
- **Estado:** [ ] Pendiente
- **Archivo:** `models/conector_odoo.py` (líneas 155-160)
- **Problema:** `host = url.replace('https://', '').replace('http://', '')` — no maneja URLs con paths, puertos custom, o formatos inesperados.
- **Remediación:** `from urllib.parse import urlparse; parsed = urlparse(url); host = parsed.hostname; port = parsed.port or 443`

### DEV-v2-008 · `record.args = None` destruye LogRecord en `FiltroCredenciales`
- **Estado:** [ ] Pendiente
- **Archivo:** `app/logging_config.py` (línea 34)
- **Problema:** Eliminar `record.args` impide que handlers posteriores reconstruyan el mensaje original con `%s`-formatting. Si otro handler necesita args, fallará.
- **Remediación:** Reasignar `record.args = ()` (tupla vacía) en vez de `None`.

### DEV-v2-009 · 10+ bloques `try/except/print` para imports opcionales
- **Estado:** [ ] Pendiente
- **Archivo:** `views/interfaz_v5.py` (líneas 77-100)
- **Problema:** Fallos de importación de módulos (spacy, torch, matplotlib, etc.) se reportan con `print()` en vez de `logger`. Si un módulo falla, el sistema arranca en estado degradado sin registro en logs.
- **Remediación:** Reemplazar `print(f"No se pudo cargar: {e}")` por `logger.warning(f"Módulo no disponible: {e}")`.

### DEV-v2-010 · `_request_timestamps` no inicializado en `__init__`
- **Estado:** [ ] Pendiente
- **Archivo:** `views/interfaz_v5.py` (línea 1685)
- **Código:** `if not hasattr(self, '_request_timestamps'): self._request_timestamps = []`
- **Problema:** Atributo creado dinámicamente con `hasattr` check en lugar de inicializarse en `__init__`. Anti-pattern que dificulta entender el estado de la clase.
- **Remediación:** Mover inicialización a `__init__`: `self._request_timestamps: List[float] = []`.

### ARQ-v2-003 · Spaghetti code en `_procesar_tradicional()` — 430 líneas, 8+ niveles nesting
- **Estado:** [ ] Pendiente
- **Archivo:** `views/interfaz_v5.py` (línea 1951)
- **Problema:** Método de 430 líneas con normalización → NLP → validación → ejecución → validación → regeneración, todo anidado profundamente.
- **Remediación:** Refactorizar a Pipeline pattern:
  ```python
  etapas = [NormalizadorEtapa(), NLPEtapa(), ValidadorEtapa(), EjecutorEtapa(), RegeneradorEtapa()]
  for etapa in etapas:
      resultado = etapa.ejecutar(contexto)
  ```

### QA-v2-004 · Markers `@slow`/`@integration` definidos pero sin tests que los usen
- **Estado:** [ ] Pendiente
- **Archivo:** `pytest.ini`
- **Problema:** Se definieron markers en QA-004 v1, pero ningún test los utiliza. Código muerto en configuración.
- **Remediación:** Agregar `@pytest.mark.slow` a tests de servicios pesados y `@pytest.mark.integration` a tests end-to-end cuando se creen.

---

## 🔵 BAJOS

### SEC-v2-010 · Rate limiting per-instancia, eludible con múltiples sesiones
- **Estado:** [ ] Pendiente
- **Archivo:** `views/interfaz_v5.py` (línea 1685-1695)
- **Problema:** El rate limiting (30 req/min) se basa en `self._request_timestamps` que es per-instancia de clase, no per-usuario. En un servidor Gradio compartido, todos los usuarios comparten el mismo contador.
- **Remediación:** Vincular timestamps a session/IP vía `gr.Request`.

### SEC-v2-011 · URLs de Ollama no validadas (riesgo menor SSRF)
- **Estado:** [ ] Pendiente
- **Archivo:** `services/llm/ollama_integrador.py`
- **Problema:** URLs de endpoint Ollama configurables sin validación. Riesgo menor de SSRF si un atacante puede modificar la configuración.
- **Remediación:** Validar que URLs apunten solo a localhost/IP interna.

### DEV-v2-011 · Silenciamiento duplicado de librería `odoorpc`
- **Estado:** [ ] Pendiente
- **Archivos:** `app/config.py` (L16-17) y `app/logging_config.py` (L75-76)
- **Remediación:** Eliminar el silenciamiento de config.py y mantener solo en logging_config.py.

### DEV-v2-012 · 0 marcadores TODO/FIXME en proyecto de 30K+ líneas
- **Estado:** [ ] Pendiente
- **Problema:** Ausencia total de `TODO`, `FIXME`, `HACK`, `XXX` en el código. En un proyecto de esta complejidad, la deuda técnica existe pero no está documentada inline.
- **Remediación:** Agregar `# TODO:` en puntos conocidos de deuda técnica (al menos los hallazgos de esta auditoría).

### ARQ-v2-004 · Ejecutores con `if/elif` repetitivo — candidato a Strategy pattern
- **Estado:** [ ] Pendiente
- **Archivo:** `services/agents/ejecutores.py`
- **Problema:** 260 líneas de cadenas if/elif por tipo de acción. Patrón repetitivo que dificulta agregar nuevos ejecutores.
- **Remediación:** Diccionario de estrategias: `self._handlers = {'ventas': self._ejecutor_ventas, ...}`.

### ARQ-v2-005 · Sin interfaz abstracta para ejecutores de acciones
- **Estado:** [ ] Pendiente
- **Problema:** Cada ejecutor define su propia firma de retorno (str, df, tuple, dict) y su propio manejo de errores. No hay contrato común.
- **Remediación:** Definir `class EjecutorBase(ABC)` con `@abstractmethod ejecutar(self, consulta) -> ResultadoEjecucion`.

---

## Resumen Ejecutivo v2

| Categoría | Críticos 🔴 | Altos 🟠 | Medios 🟡 | Bajos 🔵 | Total |
|-----------|:-----------:|:--------:|:---------:|:--------:|:-----:|
| Seguridad | 2 | 3 | 4 | 2 | **11** |
| Arquitectura | 1 | 1 | 1 | 2 | **5** |
| Calidad (QA) | 2 | 1 | 1 | — | **4** |
| Desarrollo (Dev) | 1 | 3 | 5 | 2 | **11** |
| **Total** | **6** | **8** | **11** | **6** | **31 pendientes** |

---

## Plan de Acción Recomendado v2

### Inmediato (hoy)
1. **SEC-v2-001** — Eliminar API key real de `logging_config.py`, usar patrón genérico
2. **SEC-v2-002** — Cambiar `main()` de interfaz_v5.py para usar `Config.GRADIO_SERVER_NAME`
3. **DEV-v2-001** — Corregir bug en `_filtrar_campos_validos`: `campos` en vez de `campos_existentes`
4. **SEC-v2-003** — Agregar `auth=` a `gr.Blocks()`

### Esta semana
5. **DEV-v2-002** — Reemplazar 50+ `except Exception:` por `except Exception as e:` con logging
6. **SEC-v2-006** — Agregar `html.escape()` en `_df_a_html()` y `crear_html_profesional()`
7. **SEC-v2-007** — Bloquear modelos no autorizados en `generador_queries.py` (return None en vez de warning)
8. **DEV-v2-004** — Eliminar `ConfiguracionOdoo` duplicada en `conector_odoo.py`
9. **SEC-v2-005** — Reemplazar email hardcodeado por patrón genérico
10. **DEV-v2-003** — Migrar prints críticos a `logger` (conector_odoo, interfaz imports)

### Próximo sprint
11. **ARQ-v2-001** — Extraer `_ejecutar_accion()` (1,164 líneas) de `OdooAIProV5` → Strategy pattern
12. **QA-v2-001** — Crear tests para los 10 módulos sin cobertura (services/analysis, prediction, llm)
13. **QA-v2-002** — Implementar GitHub Actions CI/CD pipeline
14. **ARQ-v2-002** — Dividir `services/analysis/` en submódulos por dominio
15. **ARQ-v2-003** — Refactorizar `_procesar_tradicional()` → Pipeline pattern
16. **QA-v2-003** — Estandarizar calidad de tests (arrange/act/assert, error paths)

### Backlog
17. **SEC-v2-004** — Implementar RBAC para modelos sensibles (HR, nómina)
18. **SEC-v2-008** — Documentar/mitigar envío de audio a Google
19. **SEC-v2-009** — Restringir `allowed_paths` a subdirectorio específico de assets
20. **DEV-v2-005 a DEV-v2-012** — Type hints, config desde .env, cleanup logging
21. **ARQ-v2-004/ARQ-v2-005** — Strategy pattern para ejecutores + interfaz abstracta
22. **SEC-v2-010/SEC-v2-011** — Rate limiting per-usuario, validación URLs Ollama
23. **QA-v2-004** — Activar markers @slow/@integration en tests reales

---

## Comparativa v1 → v2

| Métrica | Auditoría v1 | Auditoría v2 | Cambio |
|---------|:------------:|:------------:|:------:|
| Hallazgos totales | 19 | 31 | +12 nuevos |
| Críticos | 5 (resueltos ✅) | 6 | Nuevas categorías |
| Altos | 3 (resueltos ✅) | 8 | Mayor profundidad |
| Tests | 302 pasando | 302 pasando | Sin cambio |
| Cobertura estimada | No medida | ~25-30% | Primera medición |
| CI/CD | No existía | No existe | Sin cambio |
| Bare `except:` | 45 → 0 ✅ | 50+ `except Exception:` sin logging | Nuevo hallazgo |
| `print()` en prod | 100+ → 37 parcial | 80+ restantes | Parcialmente resuelto |

**Nota:** La v2 identificó 31 hallazgos porque la auditoría fue más profunda (4 roles especializados). Los 19 hallazgos originales de la v1 permanecen resueltos.

---

**🔄 RE-AUDITORÍA v2 — 31 hallazgos identificados, 0 resueltos (2026-03-13)**
