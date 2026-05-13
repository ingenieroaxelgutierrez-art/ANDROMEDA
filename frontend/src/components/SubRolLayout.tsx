"use client";

/**
 * SubRolLayout — guard de protección de ruta por sub_rol.
 *
 * Uso:
 *   <SubRolLayout allowed={["director", "gerente"]}>
 *     {children}
 *   </SubRolLayout>
 *
 * Flujo:
 *  1. Si no hay sesión → /login
 *  2. Si el sub_rol no está en `allowed` → `redirectTo` (por defecto la
 *     ruta canónica del sub_rol actual o /chat)
 *  3. Si OK → renderiza children
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { estaLogueado, getSubRol, getRedirectPath, getRol } from "@/lib/auth";
import { useI18n } from "@/components/I18nProvider";

interface SubRolLayoutProps {
  /** Sub-roles permitidos para esta ruta */
  allowed: string[];
  /** Ruta de redirección si el sub_rol no está autorizado (default: dashboard del usuario) */
  redirectTo?: string;
  children: React.ReactNode;
}

export default function SubRolLayout({ allowed, redirectTo, children }: SubRolLayoutProps) {
  const router  = useRouter();
  const { t }   = useI18n();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!estaLogueado()) {
      router.replace("/login");
      return;
    }
    const subRol = getSubRol();
    const rol    = getRol() ?? "usuario";

    if (!subRol || !allowed.includes(subRol)) {
      // Redirigir al dashboard propio del usuario en lugar de bloquear con 403
      router.replace(redirectTo ?? getRedirectPath(rol, subRol));
      return;
    }
    setReady(true);
  }, [router, allowed, redirectTo]);

  if (!ready) {
    return (
      <div className="relative flex items-center justify-center min-h-screen z-10">
        <div className="glass-strong rounded-2xl px-8 py-6 flex items-center gap-4">
          <svg className="animate-spin w-6 h-6 text-andromeda-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-sm font-medium" style={{ color: "rgba(255,255,255,0.7)" }}>
            {t("common.verifyingAccess")}
          </span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
