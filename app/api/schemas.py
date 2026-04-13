# ============================================================
# ANDROMEDA — app.api.schemas
# Modelos Pydantic para validación de I/O de la API REST.
# Ningún modelo de negocio del bot depende de este archivo.
# ============================================================

from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, List, Optional


# ── Solicitud / Respuesta del chat ──────────────────────────────────────────

class MensajeRequest(BaseModel):
    """Cuerpo de la solicitud POST /chat."""

    mensaje: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Mensaje del usuario en lenguaje natural.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="ID de sesión para trazabilidad. Se genera automáticamente si no se provee.",
    )
    empresa_id: Optional[str] = Field(
        default=None,
        description="ID de empresa (reservado para multi-empresa, Fase 4).",
    )
    historial: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description=(
            "Historial previo de conversación en formato "
            "[{\"role\": \"user\"|\"assistant\", \"content\": \"...\"}]. "
            "El servidor no mantiene estado: el cliente es responsable de enviarlo."
        ),
    )


class RespuestaAPI(BaseModel):
    """Cuerpo de la respuesta de POST /chat."""

    respuesta: str = Field(description="Último mensaje del asistente.")
    tabla_html: str = Field(description="Tabla HTML de datos (vacía si no aplica).")
    status: str = Field(description="Estado interno del pipeline (e.g. '✓ ventas [AgentVentas] (95%)').")
    session_id: str = Field(description="ID de sesión (eco del enviado o uno generado).")
    historial: List[Dict[str, Any]] = Field(description="Historial actualizado de la conversación.")
    timestamp: str = Field(description="ISO 8601 del momento de procesamiento.")


# ── Reportes ─────────────────────────────────────────────────────────────────

class TipoReporte(BaseModel):
    """Descriptor de un tipo de reporte disponible."""

    id: str = Field(description="Clave única del reporte (p.ej. 'ventas').")
    nombre: str = Field(description="Nombre legible.")
    descripcion: str = Field(description="Descripción breve del contenido.")


class ListaReportes(BaseModel):
    """Respuesta de GET /reportes."""

    tipos: List[TipoReporte]
    total: int


class GenerarReporteRequest(BaseModel):
    """Cuerpo de la solicitud POST /reportes/generar."""

    tipo: str = Field(..., description="ID del tipo de reporte a generar.")
    parametros: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Parámetros opcionales: periodo, empresa_id, etc.",
    )


class ReporteGenerado(BaseModel):
    """Respuesta de POST /reportes/generar."""

    tipo: str
    archivo: Optional[str] = Field(default=None, description="Ruta al archivo generado, si aplica.")
    mensaje: str
    timestamp: str


# ── Empresa (Fase 4 — Multi-empresa) ─────────────────────────────────────────

class EmpresaCrear(BaseModel):
    """Cuerpo de POST /configuracion — crea una nueva empresa."""

    nombre: str = Field(..., min_length=1, max_length=255, description="Nombre de la empresa.")
    odoo_url: str = Field(..., min_length=1, max_length=512, description="URL del servidor Odoo/ERP.")
    odoo_db: str = Field(..., min_length=1, max_length=255, description="Nombre de la base de datos Odoo.")
    odoo_usuario: str = Field(..., min_length=1, max_length=255, description="Usuario de acceso al ERP.")
    odoo_password: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Contraseña del ERP. Se cifra con Fernet antes de persistir.",
    )
    version_odoo: int = Field(
        default=17,
        ge=14,
        le=25,
        description="Versión mayor de Odoo (e.g. 17). Rango soportado: 14–19+.",
    )
    tipo_erp: str = Field(
        default="odoo",
        description="Tipo de ERP: 'odoo' | 'sap' | 'netsuite' | 'holded'.",
    )

    @field_validator("tipo_erp")
    @classmethod
    def validar_tipo_erp(cls, v: str) -> str:
        tipos_validos = {"odoo", "sap", "netsuite", "holded"}
        if v not in tipos_validos:
            raise ValueError(f"tipo_erp debe ser uno de: {tipos_validos}")
        return v


class EmpresaActualizar(BaseModel):
    """Cuerpo de PUT /configuracion/{id} — todos los campos son opcionales."""

    nombre: Optional[str] = Field(default=None, max_length=255)
    odoo_url: Optional[str] = Field(default=None, max_length=512)
    odoo_db: Optional[str] = Field(default=None, max_length=255)
    odoo_usuario: Optional[str] = Field(default=None, max_length=255)
    odoo_password: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Si se provee, la contraseña se re-cifra.",
    )
    version_odoo: Optional[int] = Field(default=None, ge=14, le=25)
    tipo_erp: Optional[str] = Field(default=None)


class EmpresaRespuesta(BaseModel):
    """Respuesta de GET/POST/PUT /configuracion — credenciales siempre enmascaradas."""

    id: str
    nombre: str
    odoo_url: str
    odoo_db: str
    odoo_usuario: str
    version_odoo: int
    tipo_erp: str
    activa: bool
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None


# ── Métricas SaaS (Fase 4) ───────────────────────────────────────────────────

class PeriodoMetricas(BaseModel):
    desde: str
    hasta: str


class MetricasSaaS(BaseModel):
    """Respuesta de GET /admin/metricas — agregados de comportamiento por empresa."""

    empresa_id: Optional[str] = None
    periodo: Optional[PeriodoMetricas] = None
    total_consultas: int = 0
    consultas_ok: int = 0
    consultas_error: int = 0
    tasa_error: float = 0.0
    duracion_promedio_ms: int = 0
    por_tipo: Dict[str, int] = Field(default_factory=dict)
    por_dia: Dict[str, int] = Field(default_factory=dict)
    empresas_activas: Optional[List[str]] = None


# ── Auth (Fase 5 — JWT) ────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Cuerpo de POST /auth/login."""

    email: str = Field(..., min_length=1, max_length=255, description="Email del usuario.")
    password: str = Field(..., min_length=1, max_length=512, description="Contraseña en texto plano (sobre HTTPS).")


class TokenResponse(BaseModel):
    """Respuesta de POST /auth/login y POST /auth/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Segundos hasta que expira el access_token.")


class RefreshRequest(BaseModel):
    """Cuerpo de POST /auth/refresh."""

    refresh_token: str = Field(..., description="Refresh token emitido en el login.")


class UsuarioActual(BaseModel):
    """Respuesta de GET /auth/me — perfil del usuario autenticado."""

    id: str
    nombre: str
    email: str
    rol: str
    empresa_id: Optional[str] = None
    activo: bool


class UsuarioCrearRequest(BaseModel):
    """Cuerpo de POST /auth/usuarios — crear usuario (solo admin)."""

    nombre: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=512)
    empresa_id: Optional[str] = Field(default=None, description="ID de la empresa a la que pertenece. Requerido salvo para admin global.")
    rol: str = Field(default="agente", description="admin | agente | usuario")

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, v: str) -> str:
        roles_validos = {"admin", "agente", "usuario"}
        if v not in roles_validos:
            raise ValueError(f"rol debe ser uno de: {roles_validos}")
        return v


# ── Dashboard Admin ──────────────────────────────────────────────────────────

class DashboardAdmin(BaseModel):
    """Respuesta de GET /admin/dashboard."""
    empresas_total: int = 0
    empresas_activas: int = 0
    usuarios_total: int = 0
    usuarios_activos: int = 0
    consultas_hoy: int = 0
    consultas_mes: int = 0
    tasa_error: float = 0.0
    uptime_pct: float = 100.0


# ── CRUD Usuarios (admin) ────────────────────────────────────────────────────

class UsuarioRespuesta(BaseModel):
    """Respuesta de GET/POST/PUT /admin/usuarios."""
    id: str
    nombre: str
    email: str
    rol: str
    empresa_id: Optional[str] = None
    empresa_nombre: Optional[str] = None
    activo: bool
    creado_en: Optional[str] = None


class UsuarioActualizar(BaseModel):
    """Cuerpo de PUT /admin/usuarios/{id}."""
    nombre: Optional[str] = Field(default=None, max_length=255)
    email: Optional[str] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8, max_length=512)
    rol: Optional[str] = Field(default=None)
    empresa_id: Optional[str] = Field(default=None)
    activo: Optional[bool] = Field(default=None)


class PerfilActualizar(BaseModel):
    """Cuerpo de PUT /auth/perfil."""
    nombre: Optional[str] = Field(default=None, max_length=255)
    email: Optional[str] = Field(default=None, max_length=255)
    password_actual: Optional[str] = Field(default=None, max_length=512)
    password_nuevo: Optional[str] = Field(default=None, min_length=8, max_length=512)


# ── Configuración Sistema ────────────────────────────────────────────────────

class ConfigSistema(BaseModel):
    """Configuración global del sistema (GET/PUT /admin/configuracion-sistema)."""
    llm_provider: str = "ollama"
    llm_model: str = "llama3"
    max_tokens: int = 2048
    temperatura: float = 0.3
    odoo_timeout_seg: int = 30
    max_reintentos: int = 3
    session_ttl_min: int = 60
    log_level: str = "INFO"
