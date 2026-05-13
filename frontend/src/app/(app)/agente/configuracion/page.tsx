"use client";

import { useEffect, useState, FormEvent } from "react";
import { getEmpresaPropia, actualizarEmpresaPropia, ApiError, ConfigEmpresaPropia } from "@/lib/api";
import { useI18n } from "@/components/I18nProvider";

const VERSIONES_ODOO = [12, 13, 14, 15, 16, 17];

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

export default function AgenteConfiguracionPage() {
  const { t } = useI18n();
  const [empresa, setEmpresa]   = useState<ConfigEmpresaPropia | null>(null);
  const [form, setForm]         = useState<ConfigEmpresaPropia & { odoo_password: string } | null>(null);
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [success, setSuccess]   = useState(false);

  useEffect(() => {
    getEmpresaPropia()
      .then((e) => {
        setEmpresa(e);
        setForm({ ...e, odoo_password: "" });
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : t("agenteExt.errorLoadConfig")))
      .finally(() => setLoading(false));
  }, []);

  type FormFields = ConfigEmpresaPropia & { odoo_password: string };
  function set<K extends keyof FormFields>(k: K, v: FormFields[K]) {
    setForm((prev) => prev ? { ...prev, [k]: v } : prev);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      const payload: Partial<ConfigEmpresaPropia> & { odoo_password?: string } = {
        odoo_url:     form.odoo_url,
        odoo_db:      form.odoo_db,
        odoo_usuario: form.odoo_usuario,
        version_odoo: form.version_odoo,
        tipo_erp:     form.tipo_erp,
      };
      if (form.odoo_password) payload.odoo_password = form.odoo_password;
      const updated = await actualizarEmpresaPropia(payload);
      setEmpresa(updated);
      setForm({ ...updated, odoo_password: "" });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("agenteExt.errorSave"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">{t("agente.configTitle")}</h2>
        <p className="mt-1 text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
          {t("agenteExt.configSub")}
        </p>
      </div>

      {loading && <p className="text-sm animate-pulse" style={{ color: "rgba(255,255,255,0.4)" }}>{t("common.loading")}</p>}
      {error && (
        <div className="px-4 py-3 rounded-lg text-sm"
             style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171" }}>
          {error}
        </div>
      )}
      {success && (
        <div className="px-4 py-3 rounded-lg text-sm"
             style={{ background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.3)", color: "#34d399" }}>
          {t("agenteExt.configSaved")}
        </div>
      )}

      {/* Info empresa (solo lectura) */}
      {empresa && (
        <div className="rounded-xl p-5 flex items-center gap-4"
             style={{ background: "rgba(102,126,234,0.1)", border: "1px solid rgba(102,126,234,0.2)" }}>
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
               style={{ background: "rgba(102,126,234,0.2)" }}>
            <svg className="w-5 h-5" style={{ color: "#667eea" }} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round"
                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <div>
            <p className="font-bold text-white">{empresa.nombre}</p>
            <p className="text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.5)" }}>
              {empresa.activa ? t("agenteExt.companyActive") : t("agenteExt.companyInactive")} · Odoo {empresa.version_odoo}
            </p>
          </div>
          <span className="ml-auto text-xs px-2.5 py-1 rounded-full font-medium"
                style={{
                  background: empresa.activa ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.12)",
                  border:     empresa.activa ? "1px solid rgba(16,185,129,0.4)" : "1px solid rgba(239,68,68,0.3)",
                  color:      empresa.activa ? "#34d399" : "#f87171",
                }}>
            {empresa.activa ? t("common.statusActiveF") : t("common.statusInactiveF")}
          </span>
        </div>
      )}

      {form && (
        <form onSubmit={handleSubmit} className="space-y-5">
          <section className="rounded-xl p-6 space-y-4"
                   style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            <h3 className="text-sm font-bold text-white">{t("agenteExt.sectionOdoo")}</h3>

            <Field label={t("agente.odooUrl")}>
              <input className="input-dark w-full text-sm" type="url" value={form.odoo_url}
                     onChange={(e) => set("odoo_url", e.target.value)}
                     placeholder="https://miempresa.odoo.com" />
            </Field>

            <div className="grid grid-cols-2 gap-4">
              <Field label={t("agente.odooDb")}>
                <input className="input-dark w-full text-sm" value={form.odoo_db}
                       onChange={(e) => set("odoo_db", e.target.value)} placeholder="mi_db" />
              </Field>
              <Field label={t("agenteExt.fieldVersion")}>
                <select className="input-dark w-full text-sm" value={form.version_odoo}
                        onChange={(e) => set("version_odoo", Number(e.target.value))}>
                  {VERSIONES_ODOO.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Field label={t("agente.odooUser")}>
                <input className="input-dark w-full text-sm" value={form.odoo_usuario}
                       onChange={(e) => set("odoo_usuario", e.target.value)} placeholder="admin" />
              </Field>
              <Field label={t("agenteExt.fieldPwLabel")} hint={t("agenteExt.fieldPwHint")}>
                <input className="input-dark w-full text-sm" type="password" value={form.odoo_password}
                       onChange={(e) => set("odoo_password", e.target.value)} placeholder="••••••••" />
              </Field>
            </div>
          </section>

          <button type="submit" disabled={saving}
                  className="px-6 py-2.5 rounded-xl text-sm font-bold transition-opacity"
                  style={{
                    background: "linear-gradient(135deg,#667eea,#764ba2)",
                    color: "#fff",
                    opacity: saving ? 0.6 : 1,
                  }}>
            {saving ? t("common.saving") : t("agenteExt.saveChanges")}
          </button>
        </form>
      )}
    </div>
  );
}
