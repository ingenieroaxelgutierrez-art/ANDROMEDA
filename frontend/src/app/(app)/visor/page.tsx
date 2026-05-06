"use client";

import Image from "next/image";

export default function VisorPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6 text-center">
      <div
        className="w-20 h-20 rounded-2xl overflow-hidden"
        style={{ background: "linear-gradient(135deg,#667eea,#764ba2)", opacity: 0.8 }}
      >
        <Image src="/logo.png" alt="ANDROMEDA" width={80} height={80} className="w-full h-full object-cover" />
      </div>

      <div className="space-y-2 max-w-md">
        <h2 className="text-2xl font-bold text-white">Bienvenido a ANDROMEDA</h2>
        <p className="text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.5)" }}>
          Tu perfil tiene acceso de <strong style={{ color: "rgba(255,255,255,0.75)" }}>Visor</strong>.
          Puedes consultar los manuales y documentación del sistema desde el menú lateral.
        </p>
      </div>

      <div
        className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold"
        style={{
          background: "rgba(102,126,234,0.12)",
          border: "1px solid rgba(102,126,234,0.3)",
          color: "#a5b4fc",
        }}
      >
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Acceso limitado — sin datos operacionales
      </div>
    </div>
  );
}
