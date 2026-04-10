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
      <h2 className="text-xl font-bold text-white">
        Métricas del sistema
      </h2>

      {loading && (
        <p className="text-sm animate-pulse" style={{ color: "rgba(255,255,255,0.4)" }}>
          Cargando métricas…
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
              colorClass="text-emerald-400"
            />
            <MetricsCard
              label="Tasa de error"
              value={`${metricas.tasa_error.toFixed(1)}%`}
              colorClass={metricas.tasa_error > 10 ? "text-red-400" : "text-andromeda-400"}
            />
            <MetricsCard
              label="Duración promedio"
              value={`${Math.round(metricas.duracion_promedio_ms)} ms`}
              colorClass="text-andromeda-400"
            />
          </div>

          {/* Gráfico de consultas por tipo */}
          {porTipoData.length > 0 && (
            <div
              className="rounded-xl p-6"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <h3
                className="text-sm font-semibold mb-4"
                style={{ color: "rgba(255,255,255,0.6)" }}
              >
                Consultas por tipo
              </h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={porTipoData}
                  margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis
                    dataKey="tipo"
                    tick={{ fontSize: 11, fill: "rgba(255,255,255,0.4)" }}
                    axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "rgba(255,255,255,0.4)" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      fontSize: 12,
                      borderRadius: 8,
                      background: "rgba(15,15,35,0.95)",
                      border: "1px solid rgba(102,126,234,0.3)",
                      color: "#fff",
                    }}
                    cursor={{ fill: "rgba(255,255,255,0.04)" }}
                  />
                  <Bar dataKey="consultas" fill="#667eea" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Empresas activas */}
          <div className="text-sm" style={{ color: "rgba(255,255,255,0.4)" }}>
            Empresas activas:{" "}
            <strong className="text-white">{metricas.empresas_activas}</strong>
          </div>
        </>
      )}
    </div>
  );
}
