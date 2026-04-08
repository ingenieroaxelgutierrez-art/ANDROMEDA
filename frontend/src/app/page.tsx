/**
 * Raíz del sitio: redirige a /chat si está logueado, o a /login si no.
 * La decisión se toma en el cliente para evitar flash de contenido incorrecto.
 */
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { estaLogueado } from "@/lib/auth";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace(estaLogueado() ? "/chat" : "/login");
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-pulse text-andromeda-500 text-lg font-semibold">
        Cargando ANDROMEDA…
      </div>
    </div>
  );
}
