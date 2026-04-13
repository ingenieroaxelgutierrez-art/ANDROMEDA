/**
 * lib/auth.ts — Gestión de tokens en localStorage
 *
 * Diseño:
 *  - access_token  : corta duración (15 min), Header Authorization
 *  - refresh_token : larga duración (7 días), para renovar el access
 *
 * En producción: mover refresh_token a httpOnly cookie (backend).
 */

const ACCESS_KEY  = "andromeda_access_token";
const REFRESH_KEY = "andromeda_refresh_token";
const ROLE_KEY    = "andromeda_rol";

/** Guarda ambos tokens tras un login o refresh exitoso. */
export function guardarTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
}

/** Retorna el access_token actual o null si no existe. */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

/** Retorna el refresh_token actual o null si no existe. */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

/** Elimina ambos tokens y el rol (logout). */
export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(ROLE_KEY);
}

/** Guarda el rol del usuario autenticado. */
export function guardarRol(rol: string): void {
  localStorage.setItem(ROLE_KEY, rol);
}

/** Retorna el rol almacenado o null. */
export function getRol(): string | null {
  return localStorage.getItem(ROLE_KEY);
}

/** Indica si hay una sesión activa (token presente). */
export function estaLogueado(): boolean {
  return getAccessToken() !== null;
}
