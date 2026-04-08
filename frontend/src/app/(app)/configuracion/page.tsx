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
        <h2 className="text-xl font-bold text-andromeda-700">
          Configuración de empresas
        </h2>
        <span className="text-xs text-gray-400">
          {empresas.length} empresa{empresas.length !== 1 ? "s" : ""} registrada
          {empresas.length !== 1 ? "s" : ""}
        </span>
      </div>

      {loading && (
        <p className="text-sm text-gray-400 animate-pulse">Cargando…</p>
      )}

      {error && (
        <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && !error && empresas.length === 0 && (
        <div className="text-center py-16 text-gray-400 text-sm">
          No hay empresas configuradas todavía.
          <br />
          Utiliza la API <code className="bg-gray-100 px-1 rounded">/configuracion</code> para agregar una.
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {empresas.map((e) => (
          <div
            key={e.id}
            className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-2"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-800">{e.nombre}</h3>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  e.activa
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-500"
                }`}
              >
                {e.activa ? "Activa" : "Inactiva"}
              </span>
            </div>
            <p className="text-xs text-gray-500 truncate">{e.odoo_url}</p>
            <div className="flex gap-4 text-xs text-gray-400">
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
