"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { logout } from "@/lib/api";
import { getRol, getSubRol } from "@/lib/auth";
import { useI18n } from "@/components/I18nProvider";
import LanguageSelector from "@/components/LanguageSelector";

interface NavLink {
  href: string;
  label: string;
  icon: React.ReactNode;
}

// ── Iconos reutilizables ──────────────────────────────────────────────────────

const IcoChat = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round"
          d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.77 9.77 0 01-4-.8L3 20l1.2-3.6A7.94 7.94 0 013 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);
const IcoMetricas = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);
const IcoConfig = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round"
          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);
const IcoDashboard = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round"
          d="M4 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10-3a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1v-7z" />
  </svg>
);
const IcoEmpresas = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round"
          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
  </svg>
);
const IcoUsuarios = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round"
          d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
  </svg>
);
const IcoPerfil = (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round"
          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

// ── Factories de links (reciben t para etiquetas traducidas) ─────────────────

type TFn = (key: string) => string;

function buildLinksAdmin(t: TFn): NavLink[] {
  return [
    { href: "/admin",               label: t("nav.dashboard"),     icon: IcoDashboard },
    { href: "/admin/chat",          label: t("nav.chat"),          icon: IcoChat      },
    { href: "/admin/empresas",      label: t("nav.companies"),     icon: IcoEmpresas  },
    { href: "/admin/usuarios",      label: t("nav.users"),         icon: IcoUsuarios  },
    { href: "/admin/metricas",      label: t("nav.metrics"),       icon: IcoMetricas  },
    { href: "/admin/configuracion", label: t("nav.configuration"), icon: IcoConfig    },
  ];
}
function buildLinksAgente(t: TFn): NavLink[] {
  return [
    { href: "/agente/chat",          label: t("nav.chat"),      icon: IcoChat     },
    { href: "/agente/metricas",      label: t("nav.metrics"),   icon: IcoMetricas },
    { href: "/agente/configuracion", label: t("nav.myCompany"), icon: IcoConfig   },
  ];
}
function buildLinksUsuario(t: TFn): NavLink[] {
  return [
    { href: "/chat",          label: t("nav.chat"),      icon: IcoChat   },
    { href: "/configuracion", label: t("nav.myProfile"), icon: IcoPerfil },
  ];
}
function buildLinksSubRol(subRol: string, t: TFn): NavLink[] | null {
  const map: Record<string, NavLink[]> = {
    director:    [
      { href: "/director/chat",    label: t("nav.chat"),    icon: IcoChat     },
      { href: "/admin/metricas",   label: t("nav.metrics"), icon: IcoMetricas },
    ],
    gerente:     [
      { href: "/gerente/chat",     label: t("nav.chat"),    icon: IcoChat     },
      { href: "/admin/metricas",   label: t("nav.metrics"), icon: IcoMetricas },
    ],
    jefe:        [{ href: "/jefe/chat",        label: t("nav.chat"), icon: IcoChat }],
    coordinador: [{ href: "/coordinador/chat", label: t("nav.chat"), icon: IcoChat }],
    auxiliar:    [{ href: "/auxiliar/chat",    label: t("nav.chat"), icon: IcoChat }],
    tienda:      [{ href: "/tienda/chat",      label: t("nav.chat"), icon: IcoChat }],
  };
  return map[subRol] ?? null;
}

const SUB_ROL_LABEL: Record<string, string> = {
  admin:       "Admin",
  director:    "Director",
  gerente:     "Gerente",
  jefe:        "Jefe",
  coordinador: "Coordinador",
  auxiliar:    "Auxiliar",
  tienda:      "Tienda",
};

const ROL_LABEL: Record<string, string> = {
  admin:   "Administrador",
  agente:  "Profesional",
  usuario: "Usuario",
};
const ROL_COLOR: Record<string, string> = {
  admin:   "rgba(246,79,89,0.7)",
  agente:  "rgba(102,126,234,0.7)",
  usuario: "rgba(118,75,162,0.7)",
};

// ── Componente ────────────────────────────────────────────────────────────────

export default function NavBar() {
  const router   = useRouter();
  const pathname = usePathname();
  const { t }    = useI18n();
  const [rol, setRol]               = useState<string>("usuario");
  const [subRolState, setSubRolState] = useState<string>("");
  const [displayLabel, setDisplayLabel] = useState<string>("Usuario");
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const r      = getRol()    ?? "usuario";
    const subRol = getSubRol() ?? "";
    setRol(r);
    setSubRolState(subRol);
    // Etiqueta visual: sub_rol tiene prioridad sobre rol principal
    setDisplayLabel(SUB_ROL_LABEL[subRol] ?? ROL_LABEL[r] ?? r);
  }, []);

  // Links reactivos al locale
  const links: NavLink[] = (() => {
    const subLinks = buildLinksSubRol(subRolState, t as TFn);
    if (subLinks) return subLinks;
    if (rol === "admin")   return buildLinksAdmin(t as TFn);
    if (rol === "agente")  return buildLinksAgente(t as TFn);
    return buildLinksUsuario(t as TFn);
  })();

  // Cerrar drawer al cambiar de ruta
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  async function handleLogout() {
    try { await logout(); } finally { router.push("/login"); }
  }

  return (
    <>
      {/* ── Barra superior mobile (hamburger + logo) ── */}
      <div
        className="md:hidden fixed top-0 left-0 right-0 h-14 z-[60] flex items-center gap-3 px-4"
        style={{
          background: "rgba(15,15,40,0.92)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(102,126,234,0.2)",
        }}
      >
        <button
          onClick={() => setMobileOpen(true)}
          className="w-9 h-9 flex items-center justify-center rounded-xl flex-shrink-0"
          style={{ background: "rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.85)" }}
          aria-label="Abrir menú"
        >
          <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
            <line x1="3" y1="6"  x2="21" y2="6"  strokeLinecap="round" />
            <line x1="3" y1="12" x2="21" y2="12" strokeLinecap="round" />
            <line x1="3" y1="18" x2="21" y2="18" strokeLinecap="round" />
          </svg>
        </button>
        <div
          className="w-7 h-7 rounded-lg overflow-hidden flex-shrink-0"
          style={{ background: "linear-gradient(135deg,#667eea,#764ba2,#f64f59)" }}
        >
          <Image src="/logo.png" alt="ANDROMEDA" width={28} height={28} className="w-full h-full object-cover" />
        </div>
        <span className="text-gradient font-black text-base tracking-tight">ANDROMEDA</span>
      </div>

      {/* ── Backdrop overlay (mobile) ── */}
      <div
        className={`md:hidden fixed inset-0 z-[65] bg-black/70 transition-opacity duration-300
          ${mobileOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
        style={{ backdropFilter: mobileOpen ? "blur(4px)" : "none" }}
        onClick={() => setMobileOpen(false)}
        aria-hidden="true"
      />

      {/* ── Sidebar ── */}
      <aside
        className={`glass-strong fixed left-0 top-0 h-full flex flex-col z-[70]
          transition-transform duration-300 ease-in-out
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0`}
        style={{ width: "260px" }}
      >
        {/* Header — logo */}
        <div className="px-6 py-7 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl overflow-hidden flex-shrink-0"
              style={{ background: "linear-gradient(135deg,#667eea,#764ba2,#f64f59)" }}
            >
              <Image src="/logo.png" alt="ANDROMEDA" width={40} height={40} className="w-full h-full object-cover" />
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-gradient font-black text-lg leading-none tracking-tight">ANDROMEDA</h1>
              <span
                className="text-xs mt-1 px-2 py-0.5 rounded-full inline-block font-medium"
                style={{
                  background: "rgba(255,255,255,0.06)",
                  color:  ROL_COLOR[rol] ?? "rgba(255,255,255,0.4)",
                  border: `1px solid ${ROL_COLOR[rol] ?? "rgba(255,255,255,0.1)"}`,
                }}
              >
                {displayLabel}
              </span>
            </div>
            {/* Botón cerrar solo en mobile */}
            <button
              className="md:hidden w-7 h-7 flex items-center justify-center rounded-lg flex-shrink-0"
              style={{ background: "rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.6)" }}
              onClick={() => setMobileOpen(false)}
              aria-label="Cerrar menú"
            >
              <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <line x1="18" y1="6"  x2="6"  y2="18" strokeLinecap="round" />
                <line x1="6"  y1="6"  x2="18" y2="18" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
          <p className="px-3 pb-2 text-xs font-semibold tracking-widest uppercase"
             style={{ color: "rgba(255,255,255,0.3)" }}>{t("nav.menu")}</p>

          {links.map(({ href, label, icon }) => {
            const active = pathname === href || (href.length > 1 && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200"
                style={{
                  background: active ? "rgba(102,126,234,0.25)" : "transparent",
                  color:      active ? "#fff" : "rgba(255,255,255,0.65)",
                  border:     active ? "1px solid rgba(102,126,234,0.35)" : "1px solid transparent",
                }}
              >
                <span style={{ color: active ? "#8b9fee" : "rgba(255,255,255,0.45)" }}>{icon}</span>
                {label}
                {active && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full" style={{ background: "#667eea" }} />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer — language selector + logout */}
        <div className="px-3 pb-6 border-t pt-4" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          <LanguageSelector />
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200"
            style={{ color: "rgba(255,255,255,0.5)" }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = "rgba(246,79,89,0.12)";
              (e.currentTarget as HTMLButtonElement).style.color = "#ff8a94";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = "transparent";
              (e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.5)";
            }}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round"
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            {t("nav.logout")}
          </button>
        </div>
      </aside>
    </>
  );
}


