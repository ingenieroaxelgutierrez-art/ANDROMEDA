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

export interface RespuestaChat {
  respuesta: string;
  historial: MensajeChat[];
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
  empresaId: string
): Promise<RespuestaChat> {
  const res = await _fetch("/chat", {
    method: "POST",
    body: JSON.stringify({
      mensaje,
      session_id: sessionId,
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
