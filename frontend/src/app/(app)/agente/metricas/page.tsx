"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { getMetricasEmpresa, ApiError, MetricasEmpresa } from "@/lib/api";
import MetricsCard from "@/components/MetricsCard";
import { useI18n } from "@/components/I18nProvider";

export default function AgenteMetricasPage() {
  const { t } = useI18n();
  const [metricas, setMetricas] = useState<MetricasEmpresa | null>(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);

  function cargar() {
    setLoading(true);
    getMetricasEmpresa()
      .then(setMetricas)
      .catch((err) => setError(err instanceof ApiError ? err.message : t("admin.metricsError")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { cargar(); }, []);

  const porTipoData = metricas
    ? Object.entries(metricas.por_tipo).map(([tipo, consultas]) => ({ tipo, consultas }))
    : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-black text-white tracking-tight">{t("agente.metricsTitle")}</h2>
          <p className="mt-1 text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
            {t("agenteExt.metricsSub")}
          </p>
        </div>
        <button onClick={cargar}
                className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium"
                style={{ background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.6)", border: "1px solid rgba(255,255,255,0.1)" }}>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {t("admin.refresh")}
        </button>
      </div>

      {loading && <p className="text-sm animate-pulse" style={{ color: "rgba(255,255,255,0.4)" }}>{t("common.loadingMetrics")}</p>}
      {error && (
        <div className="px-4 py-3 rounded-lg text-sm"
             style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171" }}>
          {error}
        </div>
      )}

      {metricas && (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricsCard label={t("agenteExt.totalConsultas")} value={metricas.total_consultas.toLocaleString()} />
            <MetricsCard label={t("agenteExt.exitosas")}       value={metricas.consultas_ok.toLocaleString()} colorClass="text-emerald-400" />
            <MetricsCard label={t("agenteExt.conError")}       value={metricas.consultas_error.toLocaleString()} colorClass="text-rose-400" />
            <MetricsCard
              label={t("admin.avgResponse")}
              value={`${metricas.duracion_promedio_ms.toFixed(0)} ms`}
              colorClass="text-sky-400"
            />
          </div>

          {/* Tendencia 7 días */}
          {metricas.tendencia_7dias && metricas.tendencia_7dias.length > 0 && (
            <div className="rounded-xl p-6"
                 style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <h3 className="text-sm font-semibold mb-5" style={{ color: "rgba(255,255,255,0.6)" }}>
                {t("agenteExt.trend7days")}
              </h3>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={metricas.tendencia_7dias} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="dia" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
                  <YAxis tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      background: "rgba(15,15,40,0.95)",
                      border: "1px solid rgba(102,126,234,0.3)",
                      borderRadius: 10,
                      color: "#fff",
                    }}
                  />
                  <Line type="monotone" dataKey="consultas" stroke="#667eea" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Por tipo */}
          {porTipoData.length > 0 && (
            <div className="rounded-xl p-6"
                 style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <h3 className="text-sm font-semibold mb-5" style={{ color: "rgba(255,255,255,0.6)" }}>
                {t("admin.queriesByType")}
              </h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={porTipoData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="tipo" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
                  <YAxis tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      background: "rgba(15,15,40,0.95)",
                      border: "1px solid rgba(102,126,234,0.3)",
                      borderRadius: 10,
                      color: "#fff",
                    }}
                  />
                  <Bar dataKey="consultas" fill="#764ba2" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
}
