# ANDROMEDA — Plan de Mejoras y Rediseño de Roles
**Revisión:** 30 de abril de 2026 | **Última actualización:** Sprint 4 completado  
**Estado:** Documento de trabajo — Sprint 4 implementado

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Auditoría Técnica del Proyecto](#2-auditoría-técnica-del-proyecto)
3. [Mejoras Prioritarias](#3-mejoras-prioritarias)
4. [Caso de Uso: Sistema de Roles Granular](#4-caso-de-uso-sistema-de-roles-granular)
5. [Diseño de la Nueva Jerarquía de Roles](#5-diseño-de-la-nueva-jerarquía-de-roles)
6. [Cambios Requeridos por Capa](#6-cambios-requeridos-por-capa)
7. [Matriz de Permisos Completa](#7-matriz-de-permisos-completa)
8. [Hoja de Ruta de Implementación](#8-hoja-de-ruta-de-implementación)

---

## 1. Resumen Ejecutivo

El sistema ANDROMEDA tiene una base técnica sólida (FastAPI, Next.js, SQLAlchemy, JWT, Docker) pero opera actualmente con un modelo de roles plano de **3 niveles** (`admin`, `agente`, `usuario`) que no refleja la realidad organizacional del cliente. Este documento detalla las mejoras técnicas identificadas y propone un rediseño completo del sistema de roles para soportar una jerarquía de **7 sub-roles** con permisos diferenciados por área, tienda y nivel jerárquico.

---

## 2. Auditoría Técnica del Proyecto

### 2.1 Backend (Python / FastAPI)

| Archivo | Estado | Observación |
|---|---|---|
| `app/api/schemas.py` | ⚠️ Parcial | `UsuarioCrearRequest.rol` solo valida `admin\|agente\|usuario` — sin sub-roles |
| `models/db_saas.py` | ⚠️ Parcial | `SAEnum("admin","agente","usuario")` hardcodeado en BD — requiere migración |
| `app/api/routers/admin.py` | ⚠️ Incompleto | `_solo_admin` verifica rol pero no sub-rol ni área |
| `app/api/routers/agente.py` | ⚠️ Incompleto | `_req_agente` acepta `admin\|agente` pero no distingue Dirección vs Gerencia |
| `app/api/routers/chat.py` | ❌ Sin auth | El endpoint `POST /chat` **no valida token JWT** — cualquier petición pasa |
| `app/api/routers/configuracion.py` | ❌ Sin auth | `GET/POST/PUT /configuracion` no requiere autenticación |
| `app/api/routers/manuales.py` | ❌ Sin auth | `GET /manuales/imagenes/{filename}` es completamente público |
| `app/api/auth/jwt_utils.py` | ✅ OK | HS256, access 15 min, refresh 7 días — correcto |
| `app/api/dependencies.py` | ⚠️ Pool | Pool de conectores Odoo sin TTL ni invalidación por inactividad |
| `services/agents/ejecutores.py` | ⚠️ Sin filtros | Los ejecutores no filtran datos por área/tienda del usuario |
| `services/knowledge/procesador_manuales.py` | ✅ OK | Funcional; sin control de acceso por rol |
| `utils/seguridad.py` | ⚠️ Mínimo | Solo firma SHA-256; sin rate limiting ni detección de anomalías |

### 2.2 Frontend (Next.js / TypeScript)

| Archivo | Estado | Observación |
|---|---|---|
| `frontend/src/lib/auth.ts` | ⚠️ Riesgo | `refresh_token` en `localStorage` — vulnerable a XSS; debería ser `httpOnly cookie` |
| `frontend/src/lib/api.ts` | ✅ OK | Interceptor de 401 con renovación automática del token |
| `frontend/src/components/NavBar.tsx` | ✅ Responsive | Drawer mobile implementado; roles básicos funcionales |
| `frontend/src/app/(app)/layout.tsx` | ⚠️ Auth | Solo verifica `estaLogueado()` — no valida sub-rol para rutas protegidas |
| `frontend/src/app/(app)/admin/*` | ⚠️ Incompleto | Solo rol `admin`; sin diferenciación de vistas por sub-rol |
| `frontend/src/app/(app)/agente/*` | ⚠️ Incompleto | Sin distinción Dirección vs Gerencia |
| `frontend/src/app/(app)/chat/page.tsx` | ⚠️ Sin filtros | El chat no filtra por área del usuario |

### 2.3 Infraestructura

| Elemento | Estado | Observación |
|---|---|---|
| `compose.yml` | ✅ OK | Hot reload correcto; `OLLAMA_HOST` via `host.docker.internal` |
| `Dockerfile` | ✅ OK | Python 3.11-slim con spaCy es_core_news_sm |
| `compose.prod.yml` | ⚠️ Revisar | Verificar Gunicorn workers y variables de entorno prod |
| CORS en `main_api.py` | ⚠️ Dev only | `localhost:3000` hardcodeado — en prod debe venir de env |

---

## 3. Mejoras Prioritarias

### 🔴 CRÍTICO — Seguridad

#### M-01: Proteger `POST /chat` con JWT
**Problema:** El endpoint principal del chat no requiere autenticación.  
**Impacto:** Cualquier usuario anónimo puede consultar datos del ERP.  
**Acción:** Agregar dependencia `get_usuario_autenticado` en `chat.py` e inyectar `empresa_id` y `sub_rol` desde el token, no desde el body.

```python
# app/api/routers/chat.py  — AGREGAR
from app.api.routers.auth import get_usuario_autenticado

@router.post("", response_model=RespuestaAPI)
async def procesar_chat(
    request: MensajeRequest,
    bot=Depends(get_bot),
    usuario=Depends(get_usuario_autenticado),   # ← NUEVO
) -> RespuestaAPI:
    empresa_id = usuario["empresa_id"]   # Desde token, no del body
    sub_rol    = usuario["sub_rol"]      # Determina qué datos puede ver
```

#### M-02: Proteger `GET/POST /configuracion`
**Problema:** Las rutas de configuración de empresa son públicas.  
**Acción:** Agregar `Depends(_solo_admin)` o `Depends(_req_agente_admin)` según la ruta.

#### M-03: Proteger `GET /manuales/imagenes/{filename}`
**Problema:** Las imágenes de manuales son accesibles sin autenticación.  
**Acción:** Agregar verificación JWT mínima (cualquier usuario autenticado puede ver manuales salvo `auxiliar` que ya tiene acceso por diseño).

#### M-04: Mover `refresh_token` a `httpOnly Cookie`
**Problema:** El refresh token en `localStorage` es accesible desde JavaScript — riesgo XSS.  
**Acción:**  
- Backend: emitir `refresh_token` como `Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict`  
- Frontend: eliminar `localStorage.setItem(REFRESH_KEY, ...)` en `lib/auth.ts`  
- Frontend: en `POST /auth/refresh` no enviar el token en body, el cookie se envía automáticamente

---

### 🟠 ALTO — Funcionalidad

#### M-05: Filtrado de datos por área/tienda en el chat
**Problema:** Los ejecutores en `ejecutores.py` no aplican filtros por área organizacional.  
**Acción:** Pasar `contexto_usuario = {sub_rol, area_id, tienda_id}` a los ejecutores y agregar filtros Odoo correspondientes (e.g. `[('warehouse_id', '=', tienda_id)]`).

#### M-06: Invalidar pool de conectores Odoo por inactividad
**Problema:** `_conector_pool` en `dependencies.py` no tiene TTL — conectores muertos permanecen en cache.  
**Acción:** Agregar timestamp de último uso y limpiar entradas > 30 min de inactividad.

#### M-07: CORS configurable por entorno
**Problema:** `allow_origins` hardcodeado a `localhost:3000` en `main_api.py`.  
**Acción:** Leer `ALLOWED_ORIGINS` del `.env` como lista separada por comas.

```python
# app/api/main_api.py
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, ...)
```

#### M-08: Rate limiting por usuario
**Problema:** No existe protección contra consultas masivas o abuso del endpoint `/chat`.  
**Acción:** Implementar `slowapi` con límite por `sub` (usuario_id del JWT), ej. 60 req/min.

---

### 🟡 MEDIO — Arquitectura

#### M-09: Agregar `sub_rol` y `area_id` al JWT
**Problema:** El JWT actual solo incluye `rol` (3 valores) — no hay forma de distinguir sub-roles.  
**Acción:** Añadir claims `sub_rol` y `area_id` al `access_token` en `jwt_utils.py`.

```python
# jwt_utils.py — crear_access_token()
payload = {
    "sub": usuario_id,
    "email": email,
    "rol": rol,
    "sub_rol": sub_rol,       # ← NUEVO: "direccion"|"gerencia"|"jefatura"|...
    "area_id": area_id,       # ← NUEVO: ID de área/tienda del usuario
    "empresa_id": empresa_id,
    ...
}
```

#### M-10: Migración de BD para sub-roles y áreas
**Problema:** La tabla `usuarios` usa `SAEnum("admin","agente","usuario")` — no soporta sub-roles.  
**Acción:** Agregar columnas `sub_rol` (String) y `area_id` (String, FK a nueva tabla `areas`) sin romper el enum actual (backward compatible).

#### M-11: Rutas frontend por sub-rol
**Problema:** El layout de Next.js solo redirige por rol principal (`admin`, `agente`, `usuario`).  
**Acción:** Leer `sub_rol` del JWT decodificado y redirigir a rutas específicas:
- `direccion/` → agente con sub_rol "direccion"
- `gerencia/` → agente con sub_rol "gerencia"
- `jefatura/` → usuario con sub_rol "jefatura"
- etc.

#### M-12: Logs de auditoría por acción de datos
**Problema:** `SesionLog` registra consultas pero no qué datos específicos se consultaron.  
**Acción:** Agregar campo `datos_accedidos` (JSON) en `SesionLog` con tipo de entidad y filtros aplicados.

---

### 🟢 MENOR — Calidad

#### M-13: Tests de integración para endpoints protegidos
**Problema:** Los tests actuales no cubren autenticación JWT ni permisos por rol.  
**Acción:** Agregar fixtures de tokens por rol en `tests/conftest.py` y tests para cada combinación rol/endpoint.

#### M-14: Documentación OpenAPI completa
**Problema:** Varios endpoints carecen de `response_model` y descripciones.  
**Acción:** Completar `summary`, `description` y `response_model` en todos los routers.

#### M-15: Health check con estado de Odoo y Ollama
**Problema:** `GET /salud` no verifica la conectividad real a Odoo u Ollama.  
**Acción:** Agregar checks opcionales al endpoint de salud con timeout de 2 s.

---

## 4. Caso de Uso: Sistema de Roles Granular

### Descripción del Negocio

La organización tiene una jerarquía con **distintos niveles de acceso a la información**. El sistema debe garantizar que:

- Un **Auxiliar** no puede ver datos operacionales, solo consultar manuales.
- Una **Tienda** solo puede ver datos de su propia tienda.
- Una **Coordinación/Jefatura** ve su área entera pero no otras.
- Una **Gerencia/Dirección** ve datos globales pero no puede modificar configuración del sistema.
- El **Admin** tiene acceso total.

### Actores

```
ANDROMEDA SaaS
│
├── Admin                          → Acceso total
│
├── Agente
│   ├── Dirección                  → Datos globales + manuales
│   └── Gerencia                   → Datos globales + manuales
│
└── Usuario
    ├── Jefatura                   → Datos de su área + manuales
    ├── Coordinación               → Datos de su área + manuales
    ├── Tienda                     → Datos de su tienda + manuales
    └── Auxiliar                   → Solo manuales
```

### Flujo Principal: Login y Redirección por Sub-rol

```
Usuario abre /login
    │
    ▼
Ingresa email + password
    │
    ▼
POST /auth/login
    │
    ├── Backend valida credenciales
    ├── Lee sub_rol y area_id de la BD
    └── Emite JWT con claims: {rol, sub_rol, area_id, empresa_id}
    │
    ▼
Frontend decodifica JWT
    │
    ├── rol = "admin"      → Redirige a /admin
    ├── rol = "agente"
    │   ├── sub_rol = "direccion"  → Redirige a /direccion
    │   └── sub_rol = "gerencia"  → Redirige a /gerencia
    └── rol = "usuario"
        ├── sub_rol = "jefatura"    → Redirige a /jefatura
        ├── sub_rol = "coordinacion"→ Redirige a /coordinacion
        ├── sub_rol = "tienda"      → Redirige a /tienda
        └── sub_rol = "auxiliar"    → Redirige a /auxiliar
```

### Flujo: Consulta en el Chat con Filtrado por Área

```
Usuario (sub_rol=tienda, area_id=TDA-042) escribe:
"¿Cuánto vendí esta semana?"
    │
    ▼
Frontend: POST /chat  {mensaje, historial}
+ Header: Authorization: Bearer <JWT>
    │
    ▼
Backend extrae del JWT: {sub_rol="tienda", area_id="TDA-042"}
    │
    ▼
Pipeline de chat agrega filtro automático:
  dominio_odoo = [('warehouse_id.code', '=', 'TDA-042'), ...]
    │
    ▼
EjecutorVentas ejecuta con filtro de tienda
    │
    ▼
Respuesta: ventas SOLO de TDA-042
```

### Flujo: Acceso a Manuales

```
Usuario (sub_rol=auxiliar) navega a /auxiliar/manuales
    │
    ▼
Frontend verifica sub_rol = "auxiliar" → muestra solo sección Manuales
    │
    ▼
GET /manuales/imagenes/{filename}
+ Header: Authorization: Bearer <JWT>
    │
    ▼
Backend verifica: cualquier sub_rol puede acceder a manuales → OK
    │
    ▼
Retorna imagen del manual
```

### Flujo: Intento de Acceso No Autorizado

```
Usuario (sub_rol=auxiliar) intenta acceder a /admin
    │
    ▼
Frontend: sub_rol ≠ "admin" → redirige a /auxiliar (sin llamar al backend)
    │
    ▼  (si llama directo a la API)
GET /admin/dashboard
+ Header: Authorization: Bearer <JWT sub_rol=auxiliar>
    │
    ▼
Backend: payload["rol"] = "usuario" ≠ "admin"
    │
    ▼
HTTP 403 Forbidden: "Solo administradores"
```

---

## 5. Diseño de la Nueva Jerarquía de Roles

### 5.1 Tabla de Roles

| Rol Principal | Sub-rol | `rol` en BD | `sub_rol` en BD | Descripción |
|---|---|---|---|---|
| Administrador | — | `admin` | `null` | Acceso total al sistema |
| Agente | Dirección | `agente` | `direccion` | Visión global; reportes estratégicos |
| Agente | Gerencia | `agente` | `gerencia` | Visión global; reportes operacionales |
| Usuario | Jefatura | `usuario` | `jefatura` | Datos de su área + manuales |
| Usuario | Coordinación | `usuario` | `coordinacion` | Datos de su área + manuales |
| Usuario | Tienda | `usuario` | `tienda` | Datos de su tienda + manuales |
| Usuario | Auxiliar | `usuario` | `auxiliar` | Solo manuales |

### 5.2 Cambios en la Base de Datos

```sql
-- Agregar columna sub_rol a usuarios (backward compatible, nullable)
ALTER TABLE usuarios ADD COLUMN sub_rol VARCHAR(50) NULL;

-- Agregar columna area_id (NULL para admin/global)
ALTER TABLE usuarios ADD COLUMN area_id VARCHAR(36) NULL;

-- Nueva tabla de áreas organizacionales
CREATE TABLE areas (
    id        VARCHAR(36) PRIMARY KEY,
    codigo    VARCHAR(50) UNIQUE NOT NULL,   -- ej: "TDA-042", "GERENCIA-NORTE"
    nombre    VARCHAR(255) NOT NULL,
    tipo      VARCHAR(50) NOT NULL,          -- "tienda" | "area" | "gerencia" | "direccion"
    empresa_id VARCHAR(36) REFERENCES empresas(id),
    activa    BOOLEAN NOT NULL DEFAULT TRUE
);
```

### 5.3 Cambios en el JWT

```python
# jwt_utils.py — Payload ampliado
{
    "sub": "uuid-usuario",
    "email": "usuario@empresa.com",
    "rol": "usuario",              # admin | agente | usuario
    "sub_rol": "tienda",           # direccion | gerencia | jefatura | coordinacion | tienda | auxiliar
    "area_id": "TDA-042",          # Código del área/tienda (null si es global)
    "empresa_id": "uuid-empresa",
    "tipo": "access",
    "exp": 1746000000
}
```

### 5.4 Cambios en el Schema Pydantic

```python
# schemas.py — UsuarioCrearRequest ampliado
class UsuarioCrearRequest(BaseModel):
    nombre: str
    email: str
    password: str
    empresa_id: Optional[str]
    rol: str = "usuario"           # admin | agente | usuario
    sub_rol: Optional[str] = None  # direccion | gerencia | jefatura | coordinacion | tienda | auxiliar
    area_id: Optional[str] = None  # ID del área (requerido si sub_rol in [jefatura, coordinacion, tienda])

    @field_validator("sub_rol")
    @classmethod
    def validar_sub_rol(cls, v):
        if v is None:
            return v
        validos = {"direccion", "gerencia", "jefatura", "coordinacion", "tienda", "auxiliar"}
        if v not in validos:
            raise ValueError(f"sub_rol debe ser uno de: {validos}")
        return v
```

---

## 6. Cambios Requeridos por Capa

### 6.1 Backend

#### `models/db_saas.py`
```python
# AGREGAR columnas al modelo Usuario
sub_rol = Column(String(50), nullable=True)   # sin enum para flexibilidad
area_id = Column(String(36), nullable=True)   # referencia al área

# AGREGAR modelo Area
class Area(Base):
    __tablename__ = "areas"
    id         = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    codigo     = Column(String(50), unique=True, nullable=False)
    nombre     = Column(String(255), nullable=False)
    tipo       = Column(String(50), nullable=False)  # tienda | area | gerencia | direccion
    empresa_id = Column(String(36), ForeignKey("empresas.id"), nullable=False)
    activa     = Column(Boolean, nullable=False, default=True)
```

#### `app/api/auth/jwt_utils.py`
```python
# MODIFICAR crear_access_token para incluir sub_rol y area_id
def crear_access_token(usuario_id, email, rol, empresa_id,
                        sub_rol=None, area_id=None) -> str:
    payload = {
        "sub": usuario_id, "email": email, "rol": rol,
        "sub_rol": sub_rol, "area_id": area_id,
        "empresa_id": empresa_id, "tipo": "access", "exp": expire,
    }
```

#### `app/api/routers/chat.py`
```python
# AGREGAR: autenticación + filtro de área
def _get_contexto_usuario(credentials=Depends(_bearer)) -> dict:
    """Retorna {usuario_id, sub_rol, area_id, empresa_id} desde el JWT."""
    payload = decodificar_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(401, "Token inválido")
    return payload

@router.post("")
async def procesar_chat(request, bot=Depends(get_bot),
                        ctx=Depends(_get_contexto_usuario)):
    # Filtrar por área si el sub_rol lo requiere
    filtro_area = None
    if ctx["sub_rol"] in ("tienda", "jefatura", "coordinacion"):
        filtro_area = ctx["area_id"]
    # Pasar filtro_area a los ejecutores
```

#### `app/api/dependencies.py`
```python
# NUEVA dependencia compartida para extraer usuario del token
def get_usuario_autenticado(credentials=Depends(_bearer)) -> dict:
    """Dependencia reutilizable: cualquier usuario autenticado."""
    token = credentials.credentials if credentials else None
    if not token:
        raise HTTPException(401, "No autenticado")
    payload = decodificar_access_token(token)
    if not payload:
        raise HTTPException(401, "Token inválido o expirado")
    return payload  # {sub, email, rol, sub_rol, area_id, empresa_id}
```

#### Nuevos middlewares de autorización
```python
# NUEVAS funciones helper en dependencies.py
def solo_puede_ver_manuales(ctx: dict) -> bool:
    return ctx.get("sub_rol") == "auxiliar"

def puede_ver_datos(ctx: dict) -> bool:
    return ctx.get("sub_rol") not in ("auxiliar",)

def es_global(ctx: dict) -> bool:
    """Dirección, Gerencia y Admin ven todos los datos."""
    return ctx.get("rol") == "admin" or ctx.get("sub_rol") in ("direccion", "gerencia")
```

---

### 6.2 Frontend

#### Nuevas rutas en `frontend/src/app/(app)/`
```
(app)/
├── admin/           → rol=admin
├── direccion/       → rol=agente, sub_rol=direccion
│   ├── chat/
│   ├── reportes/
│   └── metricas/
├── gerencia/        → rol=agente, sub_rol=gerencia
│   ├── chat/
│   ├── reportes/
│   └── metricas/
├── jefatura/        → rol=usuario, sub_rol=jefatura
│   ├── chat/
│   └── manuales/
├── coordinacion/    → rol=usuario, sub_rol=coordinacion
│   ├── chat/
│   └── manuales/
├── tienda/          → rol=usuario, sub_rol=tienda
│   ├── chat/
│   └── manuales/
└── auxiliar/        → rol=usuario, sub_rol=auxiliar
    └── manuales/    (SOLO manuales)
```

#### `frontend/src/lib/auth.ts` — Leer sub_rol del JWT
```typescript
// AGREGAR: decodificar JWT para leer sub_rol sin librería extra
export function getSubRol(): string | null {
  const token = getAccessToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.sub_rol ?? null;
  } catch { return null; }
}

export function getAreaId(): string | null {
  const token = getAccessToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.area_id ?? null;
  } catch { return null; }
}
```

#### `frontend/src/components/NavBar.tsx` — Links por sub_rol
```typescript
// AMPLIAR links por sub_rol
const LINKS_DIRECCION: NavLink[] = [
  { href: "/direccion/chat",     label: "Chat",     icon: IcoChat     },
  { href: "/direccion/reportes", label: "Reportes", icon: IcoMetricas },
  { href: "/direccion/metricas", label: "Métricas", icon: IcoMetricas },
];
const LINKS_GERENCIA: NavLink[] = [
  { href: "/gerencia/chat",     label: "Chat",     icon: IcoChat     },
  { href: "/gerencia/reportes", label: "Reportes", icon: IcoMetricas },
];
const LINKS_JEFATURA: NavLink[] = [
  { href: "/jefatura/chat",     label: "Chat",      icon: IcoChat   },
  { href: "/jefatura/manuales", label: "Manuales",  icon: IcoConfig },
];
const LINKS_COORDINACION = LINKS_JEFATURA.map(l =>
  ({ ...l, href: l.href.replace("jefatura", "coordinacion") })
);
const LINKS_TIENDA = LINKS_JEFATURA.map(l =>
  ({ ...l, href: l.href.replace("jefatura", "tienda") })
);
const LINKS_AUXILIAR: NavLink[] = [
  { href: "/auxiliar/manuales", label: "Manuales", icon: IcoConfig },
];
```

---

### 6.3 Infraestructura

#### `.env.example` — Variables nuevas
```env
# Sub-roles activos (solo documentación)
# Valores válidos de sub_rol: direccion | gerencia | jefatura | coordinacion | tienda | auxiliar

# CORS en producción
ALLOWED_ORIGINS=https://mi-dominio.com,https://app.mi-dominio.com

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
```

---

## 7. Matriz de Permisos Completa

| Recurso / Acción | Admin | Dirección | Gerencia | Jefatura | Coordinación | Tienda | Auxiliar |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Dashboard global** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Chat — datos globales** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Chat — datos de área** | ✅ | ✅ | ✅ | ✅ (su área) | ✅ (su área) | ❌ | ❌ |
| **Chat — datos de tienda** | ✅ | ✅ | ✅ | ✅ (su área) | ✅ (su área) | ✅ (su tienda) | ❌ |
| **Manuales** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Métricas globales** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Métricas de área** | ✅ | ✅ | ✅ | ✅ (su área) | ❌ | ❌ | ❌ |
| **Reportes globales** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Gestión de usuarios** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Gestión de empresas** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Configuración del sistema** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Crear usuarios** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 8. Hoja de Ruta de Implementación

### Sprint 1 — Seguridad Base ✅ COMPLETADO

> Implementado en sesión de trabajo. 0 errores de linter/TS. **695/695 tests pasan.**

- [x] **M-01** Proteger `POST /chat` con JWT — `app/api/routers/chat.py`
- [x] **M-02** Proteger `GET/POST /configuracion` — `app/api/routers/configuracion.py` (5 rutas, solo admin)
- [x] **M-03** Proteger `GET /manuales/imagenes` — `app/api/routers/manuales.py` (cualquier usuario autenticado)
- [x] **M-04** Mover refresh_token a httpOnly cookie — `app/api/routers/auth.py` (login + refresh rotado + logout limpia cookie)
- [x] **M-07** CORS configurable por entorno — `app/api/main_api.py` via `ALLOWED_ORIGINS` env var
- [x] **Extra** Dependencias auth centralizadas — `app/api/dependencies.py` (`get_usuario_autenticado`, `get_solo_admin`, `get_agente_o_admin`)
- [x] **Extra** `TokenResponse` sin `refresh_token` en body — `app/api/schemas.py`
- [x] **Extra** Frontend elimina refresh de localStorage — `frontend/src/lib/auth.ts`
- [x] **Extra** Frontend envía cookie con `credentials:'include'` — `frontend/src/lib/api.ts`
- [x] **Extra** `getSubRol()` / `getAreaId()` en frontend — `frontend/src/lib/auth.ts` (preparado Sprint 2)

**Variables de entorno nuevas Sprint 1:**
| Variable | Default | Descripción |
|---|---|---|
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Origins CORS permitidos (coma-separados) |
| `COOKIE_SECURE` | `false` | Poner `true` en producción con HTTPS |

**Tests (suite completa — 30 abril 2026):**
| Suite | Tests | Estado |
|---|---|---|
| `test_actions` | 19 | ✅ 19/19 |
| `test_analysis` | 17 | ✅ 17/17 |
| `test_api` | 40 | ✅ 40/40 |
| `test_auth` | 38 | ✅ 38/38 |
| `test_calidad_respuesta` | 3 | ✅ 3/3 |
| `test_cerebro_nlp` | 26 | ✅ 26/26 |
| `test_conector_odoo` | 24 | ✅ 24/24 |
| `test_config` | 21 | ✅ 21/21 |
| `test_contratos` | 42 | ✅ 42/42 |
| `test_core` | 35 | ✅ 35/35 |
| `test_grafo_conocimiento` | 62 | ✅ 62/62 |
| `test_interfaz_reportes` | 17 | ✅ 17/17 |
| `test_llm` | 42 | ✅ 42/42 |
| `test_memory` | 18 | ✅ 18/18 |
| `test_multi_agente` | 88 | ✅ 88/88 |
| `test_prediction` | 29 | ✅ 29/29 |
| `test_saas` | 100 | ✅ 100/100 |
| `test_utils` | 75 | ✅ 75/75 |
| **TOTAL** | **695** | **✅ 695/695 (0 fallos)** |

**Fixes aplicados a los tests para adaptar a Sprint 1:**
- `tests/test_api.py` — `client` fixture inyecta `get_usuario_autenticado` mock para `TestChatEndpoint`
- `tests/test_auth.py` — `TestRefresh` usa cookies (no body), `test_login_retorna_tokens` verifica cookie, `test_me_con_refresh_token_401` crea refresh_token directamente, `test_refresh_sin_cuerpo_422` → `test_refresh_sin_token_401`
- `tests/test_saas.py` — fixture sobreescribe `get_solo_admin`, `_solo_admin` (admin.py) y `get_usuario_autenticado`
- **Limpieza raíz**: `test_intenciones.py` y `test_routing.py` movidos a `scripts/` (scripts manuales, ya cubiertos por `test_utils.py`); archivos `.txt` de salida eliminados

### Sprint 2 — Modelo de Datos ✅ COMPLETADO

> Implementado en sesión de trabajo. **738/738 tests pasan.** (+43 tests nuevos Sprint 2)

- [x] **M-09** `sub_rol` y `area_id` en JWT — `app/api/auth/jwt_utils.py` (`crear_access_token` extendido con parámetros opcionales; claims omitidos si son `None`)
- [x] **M-10** Migración de BD — `models/db_saas.py`:
  - Nueva tabla `areas` con campos: `id`, `empresa_id`, `nombre`, `codigo`, `tipo`, `activa`, `creado_en`
  - Unicidad `(empresa_id, codigo)` via `UniqueConstraint`
  - Columnas `sub_rol` (String nullable) y `area_id` (FK nullable) en `usuarios`
  - `SUB_ROLES_VALIDOS` como constante exportada: `{admin_global, director, gerente, jefe_area, vendedor, almacenero, contador, rrhh, visor}`
- [x] Actualizar schemas — `app/api/schemas.py`:
  - `UsuarioActual` — agrega `sub_rol` y `area_id` opcionales
  - `UsuarioCrearRequest` — agrega `sub_rol` (con validador contra `SUB_ROLES_VALIDOS`) y `area_id`
  - `UsuarioRespuesta` — agrega `sub_rol` y `area_id`
  - `UsuarioActualizar` — agrega `sub_rol` y `area_id`
  - `AreaCrear` — nuevo schema con validación de `tipo` (tienda|almacen|oficina|planta)
  - `AreaRespuesta` — nuevo schema de respuesta de áreas
- [x] Endpoint login/refresh pasan `sub_rol`/`area_id` al JWT — `app/api/routers/auth.py`
- [x] `GET /auth/me` devuelve `sub_rol` y `area_id` en la respuesta
- [x] `POST /auth/usuarios` acepta y persiste `sub_rol` y `area_id`
- [x] CRUD `/admin/usuarios` incluye `sub_rol`/`area_id` en respuestas y creación/actualización
- [x] CRUD `/admin/areas` — `app/api/routers/areas.py` (nuevo router):
  - `GET /admin/areas` — listar con filtros por empresa y estado
  - `POST /admin/areas` — crear área (admin only)
  - `GET /admin/areas/{id}` — obtener por ID
  - `PUT /admin/areas/{id}` — actualizar
  - `DELETE /admin/areas/{id}` — soft delete (desactivar)
- [x] Compatibilidad retroactiva — usuarios sin `sub_rol`/`area_id` siguen funcionando

**Archivos modificados Sprint 2:**
| Archivo | Cambio |
|---|---|
| `models/db_saas.py` | Nueva clase `Area`, cols `sub_rol`/`area_id` en `Usuario`, `SUB_ROLES_VALIDOS`, `to_dict()` extendido |
| `app/api/auth/jwt_utils.py` | `crear_access_token` + parámetros `sub_rol`, `area_id` opcionales |
| `app/api/schemas.py` | `UsuarioActual`, `UsuarioCrearRequest`, `UsuarioRespuesta`, `UsuarioActualizar` + nuevos `AreaCrear`, `AreaRespuesta` |
| `app/api/routers/auth.py` | login + refresh pasan `sub_rol`/`area_id`; `crear_usuario` persiste nuevos campos |
| `app/api/routers/admin.py` | `_usuario_a_respuesta` + CRUD con `sub_rol`/`area_id` |
| `app/api/routers/areas.py` | Nuevo — CRUD completo de áreas |
| `app/api/main_api.py` | Registra `areas.router` |
| `tests/test_sprint2.py` | Nuevo — 43 tests en 10 clases |
| `tests/test_auth.py` | Amplía `TestJwtUtils` con claims Sprint 2 |

**Tests Sprint 2 (suite completa — completada):**
| Suite | Tests | Estado |
|---|---|---|
| `test_sprint2::TestAreaModel` | 4 | ✅ 4/4 |
| `test_sprint2::TestUsuarioConSubRol` | 5 | ✅ 5/5 |
| `test_sprint2::TestJwtConSubRol` | 5 | ✅ 5/5 |
| `test_sprint2::TestLoginConSubRol` | 3 | ✅ 3/3 |
| `test_sprint2::TestMeConSubRol` | 2 | ✅ 2/2 |
| `test_sprint2::TestCrearUsuarioConSubRol` | 3 | ✅ 3/3 |
| `test_sprint2::TestAreaEndpoints` | 10 | ✅ 10/10 |
| `test_sprint2::TestAdminUsuariosSubRol` | 3 | ✅ 3/3 |
| `test_sprint2::TestCompatibilidadLegacy` | 3 | ✅ 3/3 |
| `test_sprint2::TestSubRolesValidos` | 3 | ✅ 3/3 |
| `test_auth` (actualizados) | +2 (sub_rol JWT claims) | ✅ |
| **TOTAL SPRINT 2** | **738** | **✅ 738/738 (0 fallos)** |

### Sprint 3 — Lógica de Filtrado ✅ COMPLETADO

> Implementado en sesión de trabajo. Bug de ContextVar corregido. **792/792 tests pasan.** (+54 tests nuevos Sprint 3)

- [x] **M-05** Filtrado de datos por área/tienda en ejecutores — `models/conector_odoo.py`:
  - ContextVar `_ctx_usuario_filtro` para propagación thread-safe del contexto de usuario
  - Constantes `_SUB_ROLES_SIN_FILTRO`, `_SUB_ROLES_FILTRO_TIENDA`, `_SUB_ROLES_FILTRO_AREA`
  - Mapa `_FILTROS_ODOO_POR_MODELO` con campos Odoo por modelo (10 modelos cubiertos)
  - Método estático `_aplicar_filtro_area(filtro, modelo, contexto)` — único punto de cambio
  - Integrado en `buscar()` y `buscar_leer()` — sin tocar los ejecutores
- [x] Propagación del contexto al thread executor — `app/api/routers/chat.py`:
  - `_resolver_area_desde_bd(area_id)` — resuelve `(codigo, tipo)` desde la BD de forma tolerante a fallos
  - `_ctx_usuario_filtro.set()` → `contextvars.copy_context()` → `_ctx_copy.run(lambda: bot.procesar_mensaje(...))`
  - `reset()` en bloque `finally` para limpieza garantizada
  - Bug corregido: `set()` debe llamarse ANTES de `copy_context()` para que el snapshot incluya el nuevo valor
- [x] Tests de integración — `tests/test_sprint3.py` (54 tests en 6 clases)

**Archivos modificados Sprint 3:**
| Archivo | Cambio |
|---|---|
| `models/conector_odoo.py` | ContextVar, constantes, mapa de modelos, `_aplicar_filtro_area()`, integración en `buscar()` y `buscar_leer()` |
| `app/api/routers/chat.py` | Import `contextvars`, `_resolver_area_desde_bd()`, bloque `set`→`copy`→`run`, `reset()` en `finally` |
| `tests/test_sprint3.py` | Nuevo — 54 tests en 6 clases |

**Tests Sprint 3:**
| Clase | Tests | Estado |
|---|---|---|
| `TestAplicarFiltroArea` | 25 | ✅ 25/25 |
| `TestConectorOdooContextVar` | 6 | ✅ 6/6 |
| `TestResolverAreaDesdeBd` | 5 | ✅ 5/5 |
| `TestChatIntegracionFiltrado` | 5 | ✅ 5/5 |
| `TestConstantesFiltrado` | 9 | ✅ 9/9 |
| `TestCompatibilidadLegacySprint3` | 4 | ✅ 4/4 |
| **TOTAL SPRINT 3** | **54** | **✅ 54/54 (0 fallos)** |

**Suite completa tras Sprint 3:** 792/792 tests ✅

### Sprint 4 — Frontend ✅ COMPLETADO

> Implementado en sesión de trabajo. 0 errores TypeScript. **829 tests total (792 Python + 37 Jest).**

- [x] Nuevas rutas por sub_rol — `frontend/src/app/(app)/`:
  - `/director/chat` — `SubRolLayout` + `ChatView` (accentColor `#667eea`)
  - `/gerente/chat` — `SubRolLayout` + `ChatView` (accentColor `#764ba2`)
  - `/jefe-area/chat` — `SubRolLayout` + `ChatView` (accentColor `#f59e0b`)
  - `/vendedor/chat` — `SubRolLayout` + `ChatView` (accentColor `#10b981`)
  - `/almacenero/chat` — `SubRolLayout` + `ChatView` (accentColor `#3b82f6`)
  - `/contador/chat` — `SubRolLayout` + `ChatView` (accentColor `#8b5cf6`)
  - `/rrhh/chat` — `SubRolLayout` + `ChatView` (accentColor `#ec4899`)
  - `/visor` — `SubRolLayout` + página de acceso limitado (sin datos)
- [x] Componente `ChatView` — `frontend/src/components/ChatView.tsx` (compartido, evita duplicar lógica en 7 rutas; acepta `sessionPrefix` y `accentColor`)
- [x] Componente `SubRolLayout` — `frontend/src/components/SubRolLayout.tsx` (guard genérico; acepta `allowed: string[]`; redirige al dashboard propio si el sub_rol no coincide)
- [x] `getRedirectPath(rol, subRol)` + `SUB_ROL_ROUTES` — `frontend/src/lib/auth.ts` (lógica de redirección centralizada; sub_rol tiene prioridad sobre rol)
- [x] `NavBar.tsx` actualizado: `LINKS_SUB_ROL` por sub_rol, `SUB_ROL_LABEL` como etiqueta visual, `getSubRol()` en `useEffect`
- [x] `login/page.tsx` actualizado: usa `getRedirectPath(me.rol, getSubRol())` en lugar de if/else
- [x] Jest + ts-jest configurado — `frontend/jest.config.ts`, script `test` en `package.json`
- [x] Tests unitarios — `frontend/src/__tests__/auth.test.ts` (37 tests en 6 suites)

**Archivos creados/modificados Sprint 4:**
| Archivo | Tipo | Cambio |
|---|---|---|
| `frontend/src/lib/auth.ts` | modificado | `getRedirectPath()`, `SUB_ROL_ROUTES` |
| `frontend/src/components/ChatView.tsx` | nuevo | Chat reutilizable con `sessionPrefix` y `accentColor` |
| `frontend/src/components/SubRolLayout.tsx` | nuevo | Guard genérico de sub_rol |
| `frontend/src/app/(app)/director/layout.tsx` | nuevo | Guard para `director` |
| `frontend/src/app/(app)/director/chat/page.tsx` | nuevo | ChatView con prefix `director` |
| `frontend/src/app/(app)/gerente/layout.tsx` | nuevo | Guard para `gerente` |
| `frontend/src/app/(app)/gerente/chat/page.tsx` | nuevo | ChatView con prefix `gerente` |
| `frontend/src/app/(app)/jefe-area/layout.tsx` | nuevo | Guard para `jefe_area` |
| `frontend/src/app/(app)/jefe-area/chat/page.tsx` | nuevo | ChatView con prefix `jefe_area` |
| `frontend/src/app/(app)/vendedor/layout.tsx` | nuevo | Guard para `vendedor` |
| `frontend/src/app/(app)/vendedor/chat/page.tsx` | nuevo | ChatView con prefix `vendedor` |
| `frontend/src/app/(app)/almacenero/layout.tsx` | nuevo | Guard para `almacenero` |
| `frontend/src/app/(app)/almacenero/chat/page.tsx` | nuevo | ChatView con prefix `almacenero` |
| `frontend/src/app/(app)/contador/layout.tsx` | nuevo | Guard para `contador` |
| `frontend/src/app/(app)/contador/chat/page.tsx` | nuevo | ChatView con prefix `contador` |
| `frontend/src/app/(app)/rrhh/layout.tsx` | nuevo | Guard para `rrhh` |
| `frontend/src/app/(app)/rrhh/chat/page.tsx` | nuevo | ChatView con prefix `rrhh` |
| `frontend/src/app/(app)/visor/layout.tsx` | nuevo | Guard para `visor` |
| `frontend/src/app/(app)/visor/page.tsx` | nuevo | Página acceso limitado |
| `frontend/src/components/NavBar.tsx` | modificado | `LINKS_SUB_ROL`, `SUB_ROL_LABEL`, `getSubRol()` |
| `frontend/src/app/login/page.tsx` | modificado | `getRedirectPath()` post-login |
| `frontend/jest.config.ts` | nuevo | Configuración Jest + ts-jest |
| `frontend/package.json` | modificado | Scripts `test` y `test:coverage` |
| `frontend/src/__tests__/auth.test.ts` | nuevo | 37 tests unitarios |

**Tests Sprint 4:**
| Suite | Tests | Estado |
|---|---|---|
| `getRedirectPath` | 14 | ✅ 14/14 |
| `SUB_ROL_ROUTES` | 9 | ✅ 9/9 |
| `decodeTokenPayload` | 3 | ✅ 3/3 |
| `getSubRol` | 3 | ✅ 3/3 |
| `getAreaId` | 3 | ✅ 3/3 |
| `clearTokens` | 1 | ✅ 1/1 |
| **TOTAL SPRINT 4 (Jest)** | **37** | **✅ 37/37 (0 fallos)** |
| **Python (sin regresiones)** | **792** | **✅ 792/792** |
| **TOTAL ACUMULADO** | **829** | **✅ 829/829** |

### Sprint 5 — Mejoras Adicionales (1 semana)
- [ ] **M-06** TTL para pool de conectores Odoo
- [ ] **M-08** Rate limiting con `slowapi`
- [ ] **M-12** Logs de auditoría por datos accedidos
- [ ] **M-14** Documentación OpenAPI completa
- [ ] **M-15** Health check con Odoo y Ollama

---

*Documento generado por revisión automática del proyecto ANDROMEDA — Versión 1.0*  
*Sprint 1 completado — todos los checks verificados sin errores de linter/TypeScript.*  
*Sprint 2 completado — 738/738 tests. tabla `areas`, cols `sub_rol`/`area_id`, JWT ampliado, CRUD REST.*  
*Sprint 3 completado — 792/792 tests. Filtrado por área con ContextVar, `_aplicar_filtro_area()`, `_resolver_area_desde_bd()`.*  
*Sprint 4 completado — 829 tests (792 Python + 37 Jest). Frontend por sub_rol: 8 rutas, `ChatView`, `SubRolLayout`, `getRedirectPath()`, NavBar y login actualizados.*
