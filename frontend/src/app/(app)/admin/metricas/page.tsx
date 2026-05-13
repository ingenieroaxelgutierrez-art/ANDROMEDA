"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { getMetricas, ApiError, MetricasAdmin } from "@/lib/api";
import MetricsCard from "@/components/MetricsCard";
import { useI18n } from "@/components/I18nProvider";

export default function AdminMetricasPage() {
  const { t } = useI18n();
  const [metricas, setMetricas] = useState<MetricasAdmin | null>(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);

  function cargar() {
    setLoading(true);
    getMetricas()
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
          <h2 className="text-2xl font-black text-white tracking-tight">{t("admin.metricsTitle")}</h2>
          <p className="mt-1 text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
            {t("admin.metricsSub")}
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

      {loading && <p className="text-sm animate-pulse" style={{ color: "rgba(255,255,255,0.4)" }}>{t("common.loading")}</p>}
      {error && (
        <div className="px-4 py-3 rounded-lg text-sm"
             style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171" }}>
          {error}
        </div>
      )}

      {metricas && (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <MetricsCard label={t("admin.queriesLabel")}         value={metricas.total_consultas.toLocaleString()} />
            <MetricsCard label={t("admin.successRate")}           value={metricas.consultas_ok.toLocaleString()}    colorClass="text-emerald-400" />
            <MetricsCard label={t("common.error")}               value={metricas.consultas_error.toLocaleString()} colorClass="text-rose-400" />
            <MetricsCard
              label={t("admin.errorRate")}
              value={`${(metricas.tasa_error).toFixed(2)}%`}
              colorClass={metricas.tasa_error > 0.05 ? "text-rose-400" : "text-emerald-400"}
            />
            <MetricsCard
              label={t("admin.avgDuration")}
              value={`${metricas.duracion_promedio_ms.toFixed(0)} ms`}
              colorClass="text-sky-400"
            />
            <MetricsCard
              label={t("admin.activeCompaniesCard")}
              value={metricas.empresas_activas.toLocaleString()}
              colorClass="text-andromeda-400"
            />
          </div>

          {/* Gráfico por tipo */}
          {porTipoData.length > 0 && (
            <div className="rounded-xl p-6"
                 style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <h3 className="text-sm font-semibold mb-5" style={{ color: "rgba(255,255,255,0.6)" }}>
                Consultas por tipo
              </h3>
              <ResponsiveContainer width="100%" height={220}>
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
                  <Bar dataKey="consultas" fill="#667eea" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Detalle por tipo (tabla) */}
          <div className="rounded-xl overflow-hidden"
               style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            <div className="px-5 py-3 text-xs font-semibold uppercase tracking-wider"
                 style={{ borderBottom: "1px solid rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.35)" }}>
              Detalle por tipo de consulta
            </div>
            {porTipoData.map(({ tipo, consultas }, i) => {
              const total = porTipoData.reduce((a, b) => a + b.consultas, 0);
              const pct   = total > 0 ? (consultas / total) * 100 : 0;
              return (
                <div key={tipo}
                     className="flex items-center gap-4 px-5 py-3"
                     style={{ borderTop: i > 0 ? "1px solid rgba(255,255,255,0.05)" : undefined }}>
                  <p className="text-sm w-36 font-medium" style={{ color: "rgba(255,255,255,0.7)" }}>{tipo}</p>
                  <div className="flex-1 h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.08)" }}>
                    <div className="h-full rounded-full" style={{ width: `${pct}%`, background: "#667eea" }} />
                  </div>
                  <p className="text-sm font-bold text-white w-12 text-right">{consultas}</p>
                  <p className="text-xs w-10 text-right" style={{ color: "rgba(255,255,255,0.35)" }}>
                    {pct.toFixed(1)}%
                  </p>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
