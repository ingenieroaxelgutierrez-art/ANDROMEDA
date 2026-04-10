"use client";

import { useEffect, useState } from "react";
import { getConfiguracion, ApiError } from "@/lib/api";

interface Empresa {
  id: string;
  nombre: string;
  odoo_url: string;
  odoo_db: string;
  odoo_usuario: string;
  version_odoo: number;
  tipo_erp: string;
  activa: boolean;
}

export default function ConfiguracionPage() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getConfiguracion()
      .then((data) => setEmpresas(data as Empresa[]))
      .catch((err) => {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Error al cargar la configuración.");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">
          Configuración de empresas
        </h2>
        <span
          className="text-xs px-3 py-1 rounded-full"
          style={{
            background: "rgba(255,255,255,0.06)",
            color: "rgba(255,255,255,0.4)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          {empresas.length} empresa{empresas.length === 1 ? "" : "s"} registrada
          {empresas.length === 1 ? "" : "s"}
        </span>
      </div>

      {loading && (
        <p className="text-sm animate-pulse" style={{ color: "rgba(255,255,255,0.4)" }}>
          Cargando…
        </p>
      )}

      {error && (
        <div
          className="px-4 py-3 rounded-lg text-sm"
          style={{
            background: "rgba(239,68,68,0.12)",
            border: "1px solid rgba(239,68,68,0.3)",
            color: "#f87171",
          }}
        >
          {error}
        </div>
      )}

      {!loading && !error && empresas.length === 0 && (
        <div
          className="text-center py-16 text-sm"
          style={{ color: "rgba(255,255,255,0.35)" }}
        >
          No hay empresas configuradas todavía.
          <br />
          Utiliza la API{" "}
          <code
            className="px-1.5 py-0.5 rounded text-xs"
            style={{
              background: "rgba(102,126,234,0.18)",
              color: "#a5b4fc",
              border: "1px solid rgba(102,126,234,0.25)",
            }}
          >
            /configuracion
          </code>{" "}
          para agregar una.
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {empresas.map((e) => (
          <div
            key={e.id}
            className="rounded-xl p-5 space-y-2"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)",
              backdropFilter: "blur(12px)",
            }}
          >
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-white">{e.nombre}</h3>
              <span
                className="text-xs px-2 py-0.5 rounded-full font-medium"
                style={
                  e.activa
                    ? {
                        background: "rgba(52,211,153,0.15)",
                        color: "#34d399",
                        border: "1px solid rgba(52,211,153,0.3)",
                      }
                    : {
                        background: "rgba(255,255,255,0.06)",
                        color: "rgba(255,255,255,0.35)",
                        border: "1px solid rgba(255,255,255,0.08)",
                      }
                }
              >
                {e.activa ? "Activa" : "Inactiva"}
              </span>
            </div>
            <p
              className="text-xs truncate"
              style={{ color: "rgba(255,255,255,0.4)" }}
            >
              {e.odoo_url}
            </p>
            <div
              className="flex gap-4 text-xs"
              style={{ color: "rgba(255,255,255,0.3)" }}
            >
              <span>BD: {e.odoo_db}</span>
              <span>Odoo v{e.version_odoo}</span>
              <span>{e.tipo_erp.toUpperCase()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
