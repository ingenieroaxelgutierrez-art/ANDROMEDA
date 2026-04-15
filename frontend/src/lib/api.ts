/**
 * lib/api.ts — Wrapper tipado sobre fetch para la API ANDROMEDA
 *
 * Características:
 *  - Inyecta automáticamente el Bearer token en cada petición.
 *  - En HTTP 401: intenta renovar el access_token con el refresh_token.
 *  - Si el refresh también falla: limpia tokens y redirige a /login.
 *  - Lanza `ApiError` con el cuerpo de error del servidor.
 */

import {
  getAccessToken,
  getRefreshToken,
  guardarTokens,
  clearTokens,
} from "./auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

// ── Tipos públicos ────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UsuarioActual {
  id: string;
  nombre: string;
  email: string;
  rol: string;
  empresa_id: string;
  activo: boolean;
}

export interface MensajeChat {
  role: "user" | "assistant";
  content: string;
}

/** Respuesta del backend POST /chat — alineada con RespuestaAPI de schemas.py */
export interface RespuestaChat {
  /** Último mensaje del asistente (texto plano o Markdown). */
  respuesta: string;
  /** Historial actualizado incluyendo el mensaje del usuario y la respuesta. */
  historial: MensajeChat[];
  /**
   * HTML con tabla de datos o gráfica Plotly/Matplotlib.
   * Vacío si la consulta no produce datos visualizables.
   */
  tabla_html: string;
  /** Estado interno del pipeline, ej. "✓ ventas [AgentVentas] (95%)". */
  status: string;
  /** ID de sesión generado o ecoado. */
  session_id: string;
  /** ISO 8601 del momento de procesamiento. */
  timestamp: string;
  metricas?: Record<string, unknown>;
}

export interface MetricasAdmin {
  total_consultas: number;
  consultas_ok: number;
  consultas_error: number;
  tasa_error: number;
  duracion_promedio_ms: number;
  empresas_activas: number;
  por_tipo: Record<string, number>;
}

// ── Tipos SaaS Admin ─────────────────────────────────────────────────────────

export interface EmpresaSaaS {
  id: string;
  nombre: string;
  odoo_url: string;
  odoo_db: string;
  odoo_usuario: string;
  version_odoo: number;
  tipo_erp: string;
  activa: boolean;
  plan: "basico" | "profesional" | "enterprise";
  max_usuarios: number;
  usuarios_activos: number;
  fecha_alta: string;
}

export type EmpresaCreate = Omit<EmpresaSaaS, "id" | "usuarios_activos" | "fecha_alta"> & {
  odoo_password: string;
};

export interface UsuarioSaaS {
  id: string;
  nombre: string;
  email: string;
  rol: "admin" | "agente" | "usuario";
  empresa_id: string | null;
  empresa_nombre?: string;
  activo: boolean;
  fecha_alta: string;
}

export interface UsuarioCreate {
  nombre: string;
  email: string;
  password: string;
  rol: "admin" | "agente" | "usuario";
  empresa_id?: string | null;
}

export interface DashboardAdmin {
  empresas_total: number;
  empresas_activas: number;
  usuarios_total: number;
  usuarios_activos: number;
  consultas_hoy: number;
  consultas_mes: number;
  tasa_error: number;
  uptime_pct: number;
}

export interface ConfigSistema {
  llm_provider: string;
  llm_model: string;
  max_tokens: number;
  temperatura: number;
  odoo_timeout_seg: number;
  max_reintentos: number;
  session_ttl_min: number;
  log_level: string;
}

// ── Tipos Agente ──────────────────────────────────────────────────────────────

export interface ConfigEmpresaPropia {
  id: string;
  nombre: string;
  odoo_url: string;
  odoo_db: string;
  odoo_usuario: string;
  version_odoo: number;
  tipo_erp: string;
  activa: boolean;
}

export interface MetricasEmpresa {
  total_consultas: number;
  consultas_ok: number;
  consultas_error: number;
  tasa_error: number;
  duracion_promedio_ms: number;
  por_tipo: Record<string, number>;
  tendencia_7dias: Array<{ dia: string; consultas: number }>;
}

// ── ApiError ─────────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly detail?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ── Internals ─────────────────────────────────────────────────────────────────

async function _parseError(res: Response): Promise<ApiError> {
  let detail: unknown;
  try {
    detail = await res.json();
  } catch {
    detail = await res.text();
  }
  const msg =
    typeof detail === "object" && detail !== null && "detail" in detail
      ? String((detail as Record<string, unknown>).detail)
      : res.statusText;
  return new ApiError(res.status, msg, detail);
}

/** Renueva el access_token usando el refresh_token almacenado. */
async function _renovarToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  const res = await fetch(`${BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    clearTokens();
    return false;
  }

  const data: TokenResponse = await res.json();
  guardarTokens(data.access_token, data.refresh_token);
  return true;
}

/** fetch interno con retry automático en 401. */
async function _fetch(
  path: string,
  options: RequestInit = {},
  retried = false
): Promise<Response> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401 && !retried) {
    const renovado = await _renovarToken();
    if (renovado) {
      return _fetch(path, options, true);
    }
    // Redirigir a login en el navegador
    if (globalThis.window !== undefined) {
      globalThis.window.location.href = "/login";
    }
  }

  return res;
}

// ── API pública ───────────────────────────────────────────────────────────────

/** POST /auth/login */
export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** POST /auth/logout */
export async function logout(): Promise<void> {
  await _fetch("/auth/logout", { method: "POST" });
  clearTokens();
}

/** GET /auth/me */
export async function getMe(): Promise<UsuarioActual> {
  const res = await _fetch("/auth/me");
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** POST /chat */
export async function enviarMensaje(
  mensaje: string,
  sessionId: string,
  historialPrevio: MensajeChat[] = [],
  empresaId?: string
): Promise<RespuestaChat> {
  const res = await _fetch("/chat", {
    method: "POST",
    body: JSON.stringify({
      mensaje,
      session_id: sessionId,
      historial: historialPrevio,
      empresa_id: empresaId,
    }),
  });
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** GET /admin/metricas */
export async function getMetricas(
  empresaId?: string
): Promise<MetricasAdmin> {
  const query = empresaId ? `?empresa_id=${encodeURIComponent(empresaId)}` : "";
  const res = await _fetch(`/admin/metricas${query}`);
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** GET /configuracion */
export async function getConfiguracion(): Promise<unknown[]> {
  const res = await _fetch("/configuracion");
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

// ── Admin — Dashboard ─────────────────────────────────────────────────────────

/** GET /admin/dashboard */
export async function getDashboard(): Promise<DashboardAdmin> {
  const res = await _fetch("/admin/dashboard");
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

// ── Admin — Empresas ──────────────────────────────────────────────────────────

/** GET /admin/empresas */
export async function getEmpresas(): Promise<EmpresaSaaS[]> {
  const res = await _fetch("/admin/empresas");
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** POST /admin/empresas */
export async function crearEmpresa(data: EmpresaCreate): Promise<EmpresaSaaS> {
  const res = await _fetch("/admin/empresas", {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** PUT /admin/empresas/{id} */
export async function actualizarEmpresa(
  id: string,
  data: Partial<EmpresaSaaS>
): Promise<EmpresaSaaS> {
  const res = await _fetch(`/admin/empresas/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** DELETE /admin/empresas/{id} */
export async function eliminarEmpresa(id: string): Promise<void> {
  const res = await _fetch(`/admin/empresas/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw await _parseError(res);
}

// ── Admin — Usuarios ──────────────────────────────────────────────────────────

/** GET /admin/usuarios */
export async function getUsuarios(): Promise<UsuarioSaaS[]> {
  const res = await _fetch("/admin/usuarios");
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** POST /admin/usuarios */
export async function crearUsuario(data: UsuarioCreate): Promise<UsuarioSaaS> {
  const res = await _fetch("/admin/usuarios", {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** PUT /admin/usuarios/{id} */
export async function actualizarUsuario(
  id: string,
  data: Partial<UsuarioSaaS> & { password?: string }
): Promise<UsuarioSaaS> {
  const res = await _fetch(`/admin/usuarios/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** DELETE /admin/usuarios/{id} */
export async function eliminarUsuario(id: string): Promise<void> {
  const res = await _fetch(`/admin/usuarios/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw await _parseError(res);
}

/** GET /admin/configuracion-sistema */
export async function getConfigSistema(): Promise<ConfigSistema> {
  const res = await _fetch("/admin/configuracion-sistema");
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** PUT /admin/configuracion-sistema */
export async function actualizarConfigSistema(
  data: Partial<ConfigSistema>
): Promise<ConfigSistema> {
  const res = await _fetch("/admin/configuracion-sistema", {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

// ── Agente — Empresa propia ───────────────────────────────────────────────────

/** GET /agente/empresa */
export async function getEmpresaPropia(): Promise<ConfigEmpresaPropia> {
  const res = await _fetch("/agente/empresa");
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** PUT /agente/empresa */
export async function actualizarEmpresaPropia(
  data: Partial<ConfigEmpresaPropia> & { odoo_password?: string }
): Promise<ConfigEmpresaPropia> {
  const res = await _fetch("/agente/empresa", {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** GET /agente/metricas */
export async function getMetricasEmpresa(): Promise<MetricasEmpresa> {
  const res = await _fetch("/agente/metricas");
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

// ── Usuario — Perfil ──────────────────────────────────────────────────────────

/** PUT /auth/perfil */
export async function actualizarPerfil(data: {
  nombre?: string;
  email?: string;
  password_actual?: string;
  password_nueva?: string;
}): Promise<UsuarioActual> {
  const res = await _fetch("/auth/perfil", {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await _parseError(res);
  return res.json();
}
