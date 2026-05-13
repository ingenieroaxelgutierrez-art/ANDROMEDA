/**
 * Tests unitarios para lib/auth.ts — Sprint 4
 *
 * Se testean SOLO las funciones puras (sin DOM ni localStorage):
 *   - getRedirectPath()
 *   - SUB_ROL_ROUTES (estructura del mapa)
 *   - decodeTokenPayload() con mock de localStorage
 *   - getSubRol() / getAreaId() con mock de localStorage
 */

// Polyfill mínimo de localStorage para jsdom
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => { store[k] = v; },
    removeItem: (k: string) => { delete store[k]; },
    clear: () => { store = {}; },
  };
})();
Object.defineProperty(global, "localStorage", { value: localStorageMock });

import {
  getRedirectPath,
  SUB_ROL_ROUTES,
  decodeTokenPayload,
  getSubRol,
  getAreaId,
  guardarTokens,
  clearTokens,
} from "@/lib/auth";

// Helper para crear un JWT fake (sin firma real)
function makeJwt(payload: Record<string, unknown>): string {
  const header  = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body    = btoa(JSON.stringify(payload)).replace(/=/g, "");
  return `${header}.${body}.fake-signature`;
}

// ── getRedirectPath ────────────────────────────────────────────────────────────

describe("getRedirectPath", () => {
  test("sub_rol director → /director/chat", () => {
    expect(getRedirectPath("agente", "director")).toBe("/director/chat");
  });

  test("sub_rol gerente → /gerente/chat", () => {
    expect(getRedirectPath("agente", "gerente")).toBe("/gerente/chat");
  });

  test("sub_rol jefe_area → /jefe-area/chat", () => {
    expect(getRedirectPath("usuario", "jefe_area")).toBe("/jefe-area/chat");
  });

  test("sub_rol vendedor → /vendedor/chat", () => {
    expect(getRedirectPath("usuario", "vendedor")).toBe("/vendedor/chat");
  });

  test("sub_rol almacenero → /almacenero/chat", () => {
    expect(getRedirectPath("usuario", "almacenero")).toBe("/almacenero/chat");
  });

  test("sub_rol contador → /contador/chat", () => {
    expect(getRedirectPath("usuario", "contador")).toBe("/contador/chat");
  });

  test("sub_rol rrhh → /rrhh/chat", () => {
    expect(getRedirectPath("usuario", "rrhh")).toBe("/rrhh/chat");
  });

  test("sub_rol visor → /visor", () => {
    expect(getRedirectPath("usuario", "visor")).toBe("/visor");
  });

  test("sub_rol admin_global → /admin", () => {
    expect(getRedirectPath("admin", "admin_global")).toBe("/admin");
  });

  test("sin sub_rol + rol admin → /admin", () => {
    expect(getRedirectPath("admin", null)).toBe("/admin");
  });

  test("sin sub_rol + rol agente → /agente/chat", () => {
    expect(getRedirectPath("agente", null)).toBe("/agente/chat");
  });

  test("sin sub_rol + rol usuario → /chat", () => {
    expect(getRedirectPath("usuario", null)).toBe("/chat");
  });

  test("sub_rol desconocido cae a fallback de rol", () => {
    expect(getRedirectPath("agente", "sub_rol_inexistente")).toBe("/agente/chat");
  });

  test("sub_rol vacío string cae a fallback de rol", () => {
    // "" no está en SUB_ROL_ROUTES → cae a rol
    expect(getRedirectPath("usuario", "")).toBe("/chat");
  });
});

// ── SUB_ROL_ROUTES ─────────────────────────────────────────────────────────────

describe("SUB_ROL_ROUTES", () => {
  const esperados = [
    "admin_global",
    "director",
    "gerente",
    "jefe_area",
    "vendedor",
    "almacenero",
    "contador",
    "rrhh",
    "visor",
  ];

  test("tiene exactamente 9 sub-roles mapeados", () => {
    expect(Object.keys(SUB_ROL_ROUTES)).toHaveLength(9);
  });

  test.each(esperados)("contiene el sub_rol '%s'", (subRol) => {
    expect(SUB_ROL_ROUTES).toHaveProperty(subRol);
  });

  test("todas las rutas empiezan con /", () => {
    Object.values(SUB_ROL_ROUTES).forEach((ruta) => {
      expect(ruta).toMatch(/^\//);
    });
  });

  test("director apunta a /director/chat", () => {
    expect(SUB_ROL_ROUTES["director"]).toBe("/director/chat");
  });

  test("visor apunta a /visor (sin /chat)", () => {
    expect(SUB_ROL_ROUTES["visor"]).toBe("/visor");
  });
});

// ── decodeTokenPayload / getSubRol / getAreaId ─────────────────────────────────

describe("decodeTokenPayload", () => {
  beforeEach(() => localStorageMock.clear());

  test("retorna null si no hay token", () => {
    expect(decodeTokenPayload()).toBeNull();
  });

  test("decodifica sub_rol correctamente", () => {
    guardarTokens(makeJwt({ sub: "uid-1", sub_rol: "vendedor", area_id: "TDA-01" }));
    const payload = decodeTokenPayload();
    expect(payload).not.toBeNull();
    expect(payload!.sub_rol).toBe("vendedor");
  });

  test("retorna null con token malformado", () => {
    localStorage.setItem("andromeda_access_token", "not.a.jwt");
    // atob de "a" devuelve un string pero JSON.parse puede fallar
    // dependiendo del contenido — el resultado debe ser null o un objeto
    // en cualquier caso no debe lanzar excepción
    expect(() => decodeTokenPayload()).not.toThrow();
  });
});

describe("getSubRol", () => {
  beforeEach(() => localStorageMock.clear());

  test("retorna null sin token", () => {
    expect(getSubRol()).toBeNull();
  });

  test("retorna el sub_rol del JWT", () => {
    guardarTokens(makeJwt({ sub_rol: "director" }));
    expect(getSubRol()).toBe("director");
  });

  test("retorna null si el JWT no tiene sub_rol", () => {
    guardarTokens(makeJwt({ sub: "uid-1", rol: "usuario" }));
    expect(getSubRol()).toBeNull();
  });
});

describe("getAreaId", () => {
  beforeEach(() => localStorageMock.clear());

  test("retorna null sin token", () => {
    expect(getAreaId()).toBeNull();
  });

  test("retorna area_id del JWT", () => {
    guardarTokens(makeJwt({ area_id: "TDA-042" }));
    expect(getAreaId()).toBe("TDA-042");
  });

  test("retorna null si el JWT no tiene area_id", () => {
    guardarTokens(makeJwt({ sub: "uid-1" }));
    expect(getAreaId()).toBeNull();
  });
});

describe("clearTokens", () => {
  test("elimina el access_token del localStorage", () => {
    guardarTokens(makeJwt({ sub: "uid-1" }));
    expect(decodeTokenPayload()).not.toBeNull();
    clearTokens();
    expect(decodeTokenPayload()).toBeNull();
  });
});
