"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { estaLogueado } from "@/lib/auth";
import NavBar from "@/components/NavBar";

export default function AppLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const router   = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (estaLogueado()) {
      setReady(true);
    } else {
      router.replace("/login");
    }
  }, [pathname, router]);

  if (!ready) {
    return (
      <div className="relative flex items-center justify-center min-h-screen z-10">
        <div className="glass-strong rounded-2xl px-8 py-6 flex items-center gap-4">
          <svg className="animate-spin w-6 h-6 text-andromeda-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <span className="text-sm font-medium" style={{ color: "rgba(255,255,255,0.7)" }}>
            Verificando sesión…
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen z-10">
      {/* Sidebar: fijo en desktop, drawer en mobile */}
      <NavBar />

      {/* Contenido principal */}
      <main
        className="flex-1 overflow-y-auto md:ml-[260px] pt-14 md:pt-0"
        style={{ minHeight: "100vh" }}
      >
        <div className="max-w-5xl mx-auto px-4 md:px-8 py-4 md:py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
