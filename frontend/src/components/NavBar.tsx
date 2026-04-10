"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { logout } from "@/lib/api";

const LINKS = [
  {
    href: "/chat",
    label: "Chat",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round"
              d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.77 9.77 0 01-4-.8L3 20l1.2-3.6A7.94 7.94 0 013 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    ),
  },
  {
    href: "/metricas",
    label: "Métricas",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    href: "/configuracion",
    label: "Configuración",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
];

export default function NavBar() {
  const router   = useRouter();
  const pathname = usePathname();

  async function handleLogout() {
    try { await logout(); } finally { router.push("/login"); }
  }

  return (
    <aside
      className="glass-strong fixed left-0 top-0 h-full flex flex-col z-50"
      style={{ width: "var(--sidebar-width, 260px)" }}
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
          <div>
            <h1 className="text-gradient font-black text-lg leading-none tracking-tight">ANDROMEDA</h1>
            <p className="text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.35)" }}>Advanced Neural Data Resource for Operations, Management & Enterprise Decision Analytics</p>
          </div>
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
        <p className="px-3 pb-2 text-xs font-semibold tracking-widest uppercase"
           style={{ color: "rgba(255,255,255,0.3)" }}>Menú</p>

        {LINKS.map(({ href, label, icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200"
              style={{
                background:  active ? "rgba(102,126,234,0.25)" : "transparent",
                color:       active ? "#fff" : "rgba(255,255,255,0.65)",
                border:      active ? "1px solid rgba(102,126,234,0.35)" : "1px solid transparent",
              }}
            >
              <span style={{ color: active ? "#8b9fee" : "rgba(255,255,255,0.45)" }}>{icon}</span>
              {label}
              {active && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full"
                      style={{ background: "#667eea" }} />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer — logout */}
      <div className="px-3 pb-6 border-t pt-4" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
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
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
