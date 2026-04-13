"use client";

import { useEffect, useState, FormEvent } from "react";
import { getConfigSistema, actualizarConfigSistema, ApiError, ConfigSistema } from "@/lib/api";

const LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"];
const LLM_PROVIDERS = ["ollama", "openai", "anthropic", "groq", "azure"];

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-semibold tracking-wider uppercase"
             style={{ color: "rgba(255,255,255,0.5)" }}>{label}</label>
      {children}
      {hint && <p className="text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>{hint}</p>}
    </div>
  );
}

export default function AdminConfiguracionPage() {
  const [config, setConfig]     = useState<ConfigSistema | null>(null);
  const [form, setForm]         = useState<ConfigSistema | null>(null);
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [success, setSuccess]   = useState(false);

  useEffect(() => {
    getConfigSistema()
      .then((c) => { setConfig(c); setForm(c); })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar configuración."))
      .finally(() => setLoading(false));
  }, []);

  function set<K extends keyof ConfigSistema>(k: K, v: ConfigSistema[K]) {
    setForm((prev) => prev ? { ...prev, [k]: v } : prev);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      const updated = await actualizarConfigSistema(form);
      setConfig(updated);
      setForm(updated);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Error al guardar configuración.");
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    if (config) setForm({ ...config });
  }

  const changed = JSON.stringify(form) !== JSON.stringify(config);

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">Configuración del sistema</h2>
        <p className="mt-1 text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
          Parámetros globales del motor de IA y la plataforma
        </p>
      </div>

      {loading && <p className="text-sm animate-pulse" style={{ color: "rgba(255,255,255,0.4)" }}>Cargando…</p>}
      {error && (
        <div className="px-4 py-3 rounded-lg text-sm"
             style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171" }}>
          {error}
        </div>
      )}
      {success && (
        <div className="px-4 py-3 rounded-lg text-sm"
             style={{ background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.3)", color: "#34d399" }}>
          Configuración guardada correctamente.
        </div>
      )}

      {form && (
        <form onSubmit={handleSubmit} className="space-y-7">

          {/* Sección LLM */}
          <section className="rounded-xl p-6 space-y-4"
                   style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            <h3 className="text-sm font-bold text-white">Motor LLM</h3>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Proveedor">
                <select className="input-dark w-full text-sm" value={form.llm_provider}
                        onChange={(e) => set("llm_provider", e.target.value)}>
                  {LLM_PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </Field>
              <Field label="Modelo">
                <input className="input-dark w-full text-sm" value={form.llm_model}
                       onChange={(e) => set("llm_model", e.target.value)}
                       placeholder="llama3.2:3b" />
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Máx. tokens" hint="Tokens máximos por respuesta">
                <input className="input-dark w-full text-sm" type="number" min={64} max={32000}
                       value={form.max_tokens} onChange={(e) => set("max_tokens", Number(e.target.value))} />
              </Field>
              <Field label="Temperatura" hint="0 = determinista · 1 = creativo">
                <input className="input-dark w-full text-sm" type="number" min={0} max={2} step={0.05}
                       value={form.temperatura} onChange={(e) => set("temperatura", Number(e.target.value))} />
              </Field>
            </div>
          </section>

          {/* Sección Odoo */}
          <section className="rounded-xl p-6 space-y-4"
                   style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            <h3 className="text-sm font-bold text-white">Conexión Odoo</h3>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Timeout (segundos)" hint="Tiempo espera por petición">
                <input className="input-dark w-full text-sm" type="number" min={5} max={120}
                       value={form.odoo_timeout_seg}
                       onChange={(e) => set("odoo_timeout_seg", Number(e.target.value))} />
              </Field>
              <Field label="Máx. reintentos">
                <input className="input-dark w-full text-sm" type="number" min={0} max={5}
                       value={form.max_reintentos}
                       onChange={(e) => set("max_reintentos", Number(e.target.value))} />
              </Field>
            </div>
          </section>

          {/* Sección Sesiones y Logs */}
          <section className="rounded-xl p-6 space-y-4"
                   style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            <h3 className="text-sm font-bold text-white">Sesiones y auditoría</h3>

            <div className="grid grid-cols-2 gap-4">
              <Field label="TTL sesión (minutos)" hint="Tiempo de vida de cada sesión de chat">
                <input className="input-dark w-full text-sm" type="number" min={5} max={1440}
                       value={form.session_ttl_min}
                       onChange={(e) => set("session_ttl_min", Number(e.target.value))} />
              </Field>
              <Field label="Nivel de log">
                <select className="input-dark w-full text-sm" value={form.log_level}
                        onChange={(e) => set("log_level", e.target.value)}>
                  {LOG_LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
                </select>
              </Field>
            </div>
          </section>

          {/* Botones */}
          <div className="flex gap-3">
            <button type="button" onClick={handleReset} disabled={!changed}
                    className="px-5 py-2.5 rounded-xl text-sm font-medium transition-opacity"
                    style={{
                      background: "rgba(255,255,255,0.06)",
                      color: "rgba(255,255,255,0.6)",
                      opacity: !changed ? 0.4 : 1,
                    }}>
              Descartar cambios
            </button>
            <button type="submit" disabled={saving || !changed}
                    className="px-6 py-2.5 rounded-xl text-sm font-bold transition-opacity"
                    style={{
                      background: "linear-gradient(135deg,#667eea,#764ba2)",
                      color: "#fff",
                      opacity: (saving || !changed) ? 0.6 : 1,
                    }}>
              {saving ? "Guardando…" : "Guardar configuración"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
