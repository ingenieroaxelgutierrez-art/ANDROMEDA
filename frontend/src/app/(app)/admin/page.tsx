"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getDashboard, getMetricas, ApiError, DashboardAdmin, MetricasAdmin } from "@/lib/api";
import MetricsCard from "@/components/MetricsCard";

export default function AdminDashboardPage() {
  const [dash, setDash]       = useState<DashboardAdmin | null>(null);
  const [metricas, setMetricas] = useState<MetricasAdmin | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getDashboard().catch(() => null),
      getMetricas().catch(() => null),
    ]).then(([d, m]) => {
      setDash(d);
      setMetricas(m);
    }).catch((err) => {
      setError(err instanceof ApiError ? err.message : "Error al cargar dashboard.");
    }).finally(() => setLoading(false));
  }, []);

  const cards = [
    {
      label: "Empresas totales",
      value: dash?.empresas_total ?? "—",
      sub: `${dash?.empresas_activas ?? 0} activas`,
      color: "text-andromeda-400",
    },
    {
      label: "Usuarios registrados",
      value: dash?.usuarios_total ?? "—",
      sub: `${dash?.usuarios_activos ?? 0} activos hoy`,
      color: "text-emerald-400",
    },
    {
      label: "Consultas hoy",
      value: dash?.consultas_hoy ?? metricas?.total_consultas ?? "—",
      sub: `${dash?.consultas_mes ?? 0} este mes`,
      color: "text-sky-400",
    },
    {
      label: "Tasa de error",
      value: dash ? `${(dash.tasa_error * 100).toFixed(1)}%` : (metricas ? `${(metricas.tasa_error * 100).toFixed(1)}%` : "—"),
      sub: "Últimas 24 h",
      color: "text-rose-400",
    },
    {
      label: "Uptime sistema",
      value: dash ? `${dash.uptime_pct.toFixed(1)}%` : "—",
      sub: "Últimos 30 días",
      color: "text-violet-400",
    },
    {
      label: "Resp. promedio",
      value: metricas ? `${metricas.duracion_promedio_ms.toFixed(0)} ms` : "—",
      sub: "Tiempo de respuesta",
      color: "text-amber-400",
    },
  ];

  const accesos = [
    { href: "/admin/empresas",      label: "Gestionar empresas",    desc: "Alta, edición y configuración Odoo",   color: "#667eea" },
    { href: "/admin/usuarios",      label: "Gestionar usuarios",    desc: "Roles, permisos y accesos",            color: "#764ba2" },
    { href: "/admin/metricas",      label: "Ver métricas",          desc: "Consultas, errores y rendimiento",     color: "#10b981" },
    { href: "/admin/configuracion", label: "Configuración sistema",  desc: "LLM, modelos y parámetros globales",  color: "#f64f59" },
  ];

  return (
    <div className="space-y-8">
      {/* Encabezado */}
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">Panel de administración</h2>
        <p className="mt-1 text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
          Vista global de toda la plataforma ANDROMEDA SaaS
        </p>
      </div>

      {loading && (
        <p className="text-sm animate-pulse" style={{ color: "rgba(255,255,255,0.4)" }}>Cargando dashboard…</p>
      )}
      {error && (
        <div className="px-4 py-3 rounded-lg text-sm"
             style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171" }}>
          {error}
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {cards.map((c) => (
          <MetricsCard key={c.label} label={c.label} value={c.value} subtext={c.sub} colorClass={c.color} />
        ))}
      </div>

      {/* Accesos rápidos */}
      <div>
        <h3 className="text-sm font-semibold mb-4 uppercase tracking-widest"
            style={{ color: "rgba(255,255,255,0.35)" }}>Acceso rápido</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {accesos.map(({ href, label, desc, color }) => (
            <Link
              key={href}
              href={href}
              className="flex items-start gap-4 p-5 rounded-xl transition-all duration-200 group"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLAnchorElement).style.background = "rgba(255,255,255,0.07)";
                (e.currentTarget as HTMLAnchorElement).style.borderColor = `${color}55`;
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLAnchorElement).style.background = "rgba(255,255,255,0.04)";
                (e.currentTarget as HTMLAnchorElement).style.borderColor = "rgba(255,255,255,0.08)";
              }}
            >
              <span
                className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
                style={{ background: color }}
              />
              <div>
                <p className="text-sm font-semibold text-white">{label}</p>
                <p className="text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.4)" }}>{desc}</p>
              </div>
              <svg className="w-4 h-4 ml-auto mt-0.5 opacity-0 group-hover:opacity-60 transition-opacity"
                   fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          ))}
        </div>
      </div>

      {/* Consultas por tipo */}
      {metricas && Object.keys(metricas.por_tipo).length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-4 uppercase tracking-widest"
              style={{ color: "rgba(255,255,255,0.35)" }}>Consultas por tipo</h3>
          <div className="rounded-xl overflow-hidden"
               style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            {Object.entries(metricas.por_tipo).map(([tipo, count], i) => {
              const total = Object.values(metricas.por_tipo).reduce((a, b) => a + b, 0);
              const pct   = total > 0 ? (count / total) * 100 : 0;
              return (
                <div key={tipo}
                     className="flex items-center gap-4 px-5 py-3"
                     style={{ borderTop: i > 0 ? "1px solid rgba(255,255,255,0.05)" : undefined }}>
                  <p className="text-xs w-32 font-medium" style={{ color: "rgba(255,255,255,0.6)" }}>{tipo}</p>
                  <div className="flex-1 h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.08)" }}>
                    <div className="h-full rounded-full" style={{ width: `${pct}%`, background: "#667eea" }} />
                  </div>
                  <p className="text-xs font-bold text-white w-8 text-right">{count}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
