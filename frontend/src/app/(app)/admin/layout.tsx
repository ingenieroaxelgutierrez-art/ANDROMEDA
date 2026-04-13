"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { estaLogueado, getRol } from "@/lib/auth";

export default function AdminLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const router  = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!estaLogueado()) {
      router.replace("/login");
      return;
    }
    const rol = getRol();
    if (rol !== "admin") {
      // Redirigir al área correcta según rol
      router.replace(rol === "agente" ? "/agente/chat" : "/chat");
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <div className="relative flex items-center justify-center min-h-screen z-10">
        <div className="glass-strong rounded-2xl px-8 py-6 flex items-center gap-4">
          <svg className="animate-spin w-6 h-6 text-andromeda-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <span className="text-sm font-medium" style={{ color: "rgba(255,255,255,0.7)" }}>
            Verificando acceso…
          </span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
