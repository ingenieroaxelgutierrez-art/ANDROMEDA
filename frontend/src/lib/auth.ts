/**
 * lib/auth.ts — Gestión de tokens del lado cliente
 *
 * Diseño de seguridad (Sprint 1):
 *  - access_token  : localStorage (corta duración, 15 min)
 *  - refresh_token : httpOnly cookie manejada por el backend
 *    El navegador la envía automáticamente en POST /auth/refresh
 *    con credentials:'include'. JS nunca puede leerla → XSS mitigado.
 */

const ACCESS_KEY    = "andromeda_access_token";
const ROLE_KEY      = "andromeda_rol";
// Cookie name usada por el proxy de imágenes (Next.js API route).
// No httpOnly → el servidor Next.js la lee; SameSite=Strict → no se envía cross-site.
const IMG_COOKIE    = "andromeda_at";

/** Guarda el access_token tras un login o refresh exitoso. */
export function guardarTokens(accessToken: string): void {
  localStorage.setItem(ACCESS_KEY, accessToken);
  // Cookie accesible para el proxy de imágenes server-side (Next.js route handler).
  // max-age=900 = 15 min (misma vida que el JWT de acceso).
  document.cookie = `${IMG_COOKIE}=${accessToken}; path=/; SameSite=Strict; max-age=900`;
}

/** Retorna el access_token actual o null si no existe. */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

/** Elimina el access_token y el rol (logout). La cookie la limpia el backend. */
export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(ROLE_KEY);
  document.cookie = `${IMG_COOKIE}=; path=/; max-age=0`;
}

/** Guarda el rol del usuario autenticado. */
export function guardarRol(rol: string): void {
  localStorage.setItem(ROLE_KEY, rol);
}

/** Retorna el rol almacenado o null. */
export function getRol(): string | null {
  return localStorage.getItem(ROLE_KEY);
}

/** Indica si hay una sesión activa (access_token presente). */
export function estaLogueado(): boolean {
  return getAccessToken() !== null;
}

/**
 * Decodifica el payload del access_token sin verificar firma
 * (la firma se verifica en el servidor en cada request).
 * Uso: leer claims client-side (rol, empresa_id, exp) para UI.
 */
export function decodeTokenPayload(): Record<string, unknown> | null {
  const token = getAccessToken();
  if (!token) return null;
  try {
    const b64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(b64));
  } catch {
    return null;
  }
}

/** Retorna el sub_rol del token o null. */
export function getSubRol(): string | null {
  return (decodeTokenPayload()?.sub_rol as string) ?? null;
}

/** Retorna el area_id del token o null. */
export function getAreaId(): string | null {
  return (decodeTokenPayload()?.area_id as string) ?? null;
}

/**
 * Mapa canónico sub_rol → ruta de dashboard.
 * Centralizar aquí evita duplicar la lógica en login, layout y NavBar.
 */
export const SUB_ROL_ROUTES: Record<string, string> = {
  admin:       "/admin",
  director:    "/director/chat",
  gerente:     "/gerente/chat",
  jefe:        "/jefe/chat",
  coordinador: "/coordinador/chat",
  auxiliar:    "/auxiliar/chat",
  tienda:      "/tienda/chat",
};

/**
 * Devuelve la ruta de destino tras el login.
 * Prioridad: sub_rol > rol principal > fallback genérico.
 */
export function getRedirectPath(rol: string, subRol: string | null): string {
  if (subRol && SUB_ROL_ROUTES[subRol]) return SUB_ROL_ROUTES[subRol];
  if (rol === "admin") return "/admin";
  if (rol === "agente") return "/agente/chat";
  return "/chat";
}
