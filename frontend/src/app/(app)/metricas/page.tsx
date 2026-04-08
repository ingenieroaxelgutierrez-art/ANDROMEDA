"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { getMetricas, ApiError, MetricasAdmin } from "@/lib/api";
import MetricsCard from "@/components/MetricsCard";

export default function MetricasPage() {
  const [metricas, setMetricas] = useState<MetricasAdmin | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMetricas()
      .then(setMetricas)
      .catch((err) => {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Error al cargar métricas.");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  // Preparar datos para el gráfico de tipos de consulta
  const porTipoData = metricas
    ? Object.entries(metricas.por_tipo).map(([tipo, count]) => ({
        tipo,
        consultas: count,
      }))
    : [];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-andromeda-700">
        Métricas del sistema
      </h2>

      {loading && (
        <p className="text-sm text-gray-400 animate-pulse">Cargando métricas…</p>
      )}

      {error && (
        <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {metricas && (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricsCard
              label="Total consultas"
              value={metricas.total_consultas.toLocaleString()}
            />
            <MetricsCard
              label="Consultas exitosas"
              value={metricas.consultas_ok.toLocaleString()}
              colorClass="text-green-600"
            />
            <MetricsCard
              label="Tasa de error"
              value={`${metricas.tasa_error.toFixed(1)}%`}
              colorClass={
                metricas.tasa_error > 10 ? "text-red-600" : "text-andromeda-700"
              }
            />
            <MetricsCard
              label="Duración promedio"
              value={`${Math.round(metricas.duracion_promedio_ms)} ms`}
              colorClass="text-andromeda-700"
            />
          </div>

          {/* Gráfico de consultas por tipo */}
          {porTipoData.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h3 className="text-sm font-semibold text-gray-600 mb-4">
                Consultas por tipo
              </h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={porTipoData}
                  margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="tipo"
                    tick={{ fontSize: 11, fill: "#6b7280" }}
                  />
                  <YAxis tick={{ fontSize: 11, fill: "#6b7280" }} />
                  <Tooltip
                    contentStyle={{
                      fontSize: 12,
                      borderRadius: 8,
                      border: "1px solid #e5e7eb",
                    }}
                  />
                  <Bar dataKey="consultas" fill="#3b5bdb" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Empresas activas */}
          <div className="text-sm text-gray-500">
            Empresas activas: <strong>{metricas.empresas_activas}</strong>
          </div>
        </>
      )}
    </div>
  );
}
