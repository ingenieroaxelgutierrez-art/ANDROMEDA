"use client";

import { useEffect, useState, FormEvent } from "react";
import {
  getEmpresas, crearEmpresa, actualizarEmpresa, eliminarEmpresa,
  ApiError, EmpresaSaaS, EmpresaCreate,
} from "@/lib/api";

const PLAN_LABELS: Record<string, string> = {
  basico:       "Básico",
  profesional:  "Profesional",
  enterprise:   "Enterprise",
};
const PLAN_COLORS: Record<string, string> = {
  basico:      "rgba(100,116,139,0.4)",
  profesional: "rgba(102,126,234,0.35)",
  enterprise:  "rgba(246,79,89,0.35)",
};
const PLAN_BORDER: Record<string, string> = {
  basico:      "rgba(100,116,139,0.5)",
  profesional: "rgba(102,126,234,0.5)",
  enterprise:  "rgba(246,79,89,0.5)",
};

const VERSIONES_ODOO = [12, 13, 14, 15, 16, 17];

// ── Modal contenedor ──────────────────────────────────────────────────────────

function Modal({ title, onClose, children }: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4"
         style={{ background: "rgba(0,0,0,0.65)", backdropFilter: "blur(4px)" }}>
      <div className="glass-strong rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b"
             style={{ borderColor: "rgba(255,255,255,0.08)" }}>
          <h3 className="font-bold text-white">{title}</h3>
          <button onClick={onClose}
                  className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors"
                  style={{ color: "rgba(255,255,255,0.4)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.08)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  );
}

// ── Fila de campo de formulario ───────────────────────────────────────────────

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-semibold tracking-wider uppercase"
             style={{ color: "rgba(255,255,255,0.5)" }}>{label}</label>
      {children}
    </div>
  );
}

// ── Formulario empresa ────────────────────────────────────────────────────────

interface FormData {
  nombre: string;
  odoo_url: string;
  odoo_db: string;
  odoo_usuario: string;
  odoo_password: string;
  version_odoo: number;
  tipo_erp: string;
  activa: boolean;
  plan: "basico" | "profesional" | "enterprise";
  max_usuarios: number;
}

function defaultForm(empresa?: EmpresaSaaS): FormData {
  return {
    nombre:        empresa?.nombre       ?? "",
    odoo_url:      empresa?.odoo_url     ?? "",
    odoo_db:       empresa?.odoo_db      ?? "",
    odoo_usuario:  empresa?.odoo_usuario ?? "",
    odoo_password: "",
    version_odoo:  empresa?.version_odoo ?? 17,
    tipo_erp:      empresa?.tipo_erp     ?? "odoo",
    activa:        empresa?.activa       ?? true,
    plan:          empresa?.plan         ?? "basico",
    max_usuarios:  empresa?.max_usuarios ?? 5,
  };
}

function EmpresaForm({
  inicial, onSave, onCancel, saving, error,
}: {
  inicial?: EmpresaSaaS;
  onSave: (data: FormData) => void;
  onCancel: () => void;
  saving: boolean;
  error: string | null;
}) {
  const [form, setForm] = useState<FormData>(() => defaultForm(inicial));

  function set<K extends keyof FormData>(key: K, val: FormData[K]) {
    setForm((prev) => ({ ...prev, [key]: val }));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSave(form);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="px-3 py-2.5 rounded-lg text-xs"
             style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171" }}>
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Field label="Nombre empresa">
          <input className="input-dark w-full text-sm" required value={form.nombre}
                 onChange={(e) => set("nombre", e.target.value)} placeholder="Acme Corp" />
        </Field>
        <Field label="Plan">
          <select className="input-dark w-full text-sm" value={form.plan}
                  onChange={(e) => set("plan", e.target.value as FormData["plan"])}>
            <option value="basico">Básico</option>
            <option value="profesional">Profesional</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </Field>
      </div>

      <Field label="URL Odoo">
        <input className="input-dark w-full text-sm" type="url" required value={form.odoo_url}
               onChange={(e) => set("odoo_url", e.target.value)} placeholder="https://miempresa.odoo.com" />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Base de datos">
          <input className="input-dark w-full text-sm" required value={form.odoo_db}
                 onChange={(e) => set("odoo_db", e.target.value)} placeholder="mi_db" />
        </Field>
        <Field label="Versión Odoo">
          <select className="input-dark w-full text-sm" value={form.version_odoo}
                  onChange={(e) => set("version_odoo", Number(e.target.value))}>
            {VERSIONES_ODOO.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Usuario Odoo">
          <input className="input-dark w-full text-sm" required value={form.odoo_usuario}
                 onChange={(e) => set("odoo_usuario", e.target.value)} placeholder="admin" />
        </Field>
        <Field label={inicial ? "Nueva contraseña (opcional)" : "Contraseña Odoo"}>
          <input className="input-dark w-full text-sm" type="password"
                 required={!inicial} value={form.odoo_password}
                 onChange={(e) => set("odoo_password", e.target.value)} placeholder="••••••••" />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Máx. usuarios">
          <input className="input-dark w-full text-sm" type="number" min={1} max={500}
                 value={form.max_usuarios} onChange={(e) => set("max_usuarios", Number(e.target.value))} />
        </Field>
        <Field label="Estado">
          <label className="flex items-center gap-2 mt-1 cursor-pointer">
            <input type="checkbox" className="w-4 h-4 accent-andromeda-500"
                   checked={form.activa} onChange={(e) => set("activa", e.target.checked)} />
            <span className="text-sm text-white">Empresa activa</span>
          </label>
        </Field>
      </div>

      <div className="flex gap-3 pt-2">
        <button type="button" onClick={onCancel}
                className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors"
                style={{ background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.6)" }}>
          Cancelar
        </button>
        <button type="submit" disabled={saving}
                className="flex-1 py-2.5 rounded-xl text-sm font-bold transition-opacity"
                style={{ background: "linear-gradient(135deg,#667eea,#764ba2)", color: "#fff", opacity: saving ? 0.6 : 1 }}>
          {saving ? "Guardando…" : inicial ? "Guardar cambios" : "Crear empresa"}
        </button>
      </div>
    </form>
  );
}

// ── Página principal ──────────────────────────────────────────────────────────

export default function EmpresasPage() {
  const [empresas, setEmpresas]   = useState<EmpresaSaaS[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);
  const [modal, setModal]         = useState<"crear" | EmpresaSaaS | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<EmpresaSaaS | null>(null);
  const [saving, setSaving]       = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function cargar() {
    setLoading(true);
    try {
      setEmpresas(await getEmpresas());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Error al cargar empresas.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { cargar(); }, []);

  async function handleSave(data: FormData, editando?: EmpresaSaaS) {
    setSaving(true);
    setFormError(null);
    try {
      if (editando) {
        const updated = await actualizarEmpresa(editando.id, data as Partial<EmpresaSaaS>);
        setEmpresas((prev) => prev.map((e) => e.id === updated.id ? updated : e));
      } else {
        const nueva = await crearEmpresa(data as EmpresaCreate);
        setEmpresas((prev) => [...prev, nueva]);
      }
      setModal(null);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Error al guardar.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(empresa: EmpresaSaaS) {
    setSaving(true);
    try {
      await eliminarEmpresa(empresa.id);
      setEmpresas((prev) => prev.filter((e) => e.id !== empresa.id));
      setConfirmDelete(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Error al eliminar.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActiva(empresa: EmpresaSaaS) {
    try {
      const updated = await actualizarEmpresa(empresa.id, { activa: !empresa.activa });
      setEmpresas((prev) => prev.map((e) => e.id === updated.id ? updated : e));
    } catch { /* silencioso */ }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-black text-white tracking-tight">Empresas</h2>
          <p className="mt-1 text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
            {empresas.length} empresa{empresas.length !== 1 ? "s" : ""} registrada{empresas.length !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          onClick={() => { setFormError(null); setModal("crear"); }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-opacity"
          style={{ background: "linear-gradient(135deg,#667eea,#764ba2)", color: "#fff" }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Nueva empresa
        </button>
      </div>

      {loading && <p className="text-sm animate-pulse" style={{ color: "rgba(255,255,255,0.4)" }}>Cargando…</p>}
      {error && (
        <div className="px-4 py-3 rounded-lg text-sm"
             style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171" }}>
          {error}
        </div>
      )}

      {/* Tabla */}
      {!loading && empresas.length > 0 && (
        <div className="rounded-xl overflow-hidden"
             style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
          {/* Encabezados */}
          <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 px-5 py-3 text-xs font-semibold uppercase tracking-wider"
               style={{ borderBottom: "1px solid rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.35)" }}>
            <span>Empresa</span>
            <span className="text-center">Plan</span>
            <span className="text-center">Usuarios</span>
            <span className="text-center">Estado</span>
            <span className="text-right">Acciones</span>
          </div>

          {empresas.map((emp) => (
            <div key={emp.id}
                 className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 items-center px-5 py-4"
                 style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
              {/* Nombre + URL */}
              <div>
                <p className="text-sm font-semibold text-white">{emp.nombre}</p>
                <p className="text-xs mt-0.5 truncate max-w-[220px]"
                   style={{ color: "rgba(255,255,255,0.4)" }}>{emp.odoo_url}</p>
              </div>

              {/* Plan */}
              <span className="text-xs font-medium px-2.5 py-1 rounded-full"
                    style={{
                      background: PLAN_COLORS[emp.plan] ?? "rgba(100,116,139,0.4)",
                      border: `1px solid ${PLAN_BORDER[emp.plan] ?? "rgba(100,116,139,0.5)"}`,
                      color: "#fff",
                    }}>
                {PLAN_LABELS[emp.plan] ?? emp.plan}
              </span>

              {/* Usuarios */}
              <span className="text-sm text-white text-center font-medium">
                {emp.usuarios_activos}<span style={{ color: "rgba(255,255,255,0.3)" }}>/{emp.max_usuarios}</span>
              </span>

              {/* Estado toggle */}
              <button
                onClick={() => toggleActiva(emp)}
                className="text-xs font-medium px-2.5 py-1 rounded-full transition-colors"
                style={{
                  background: emp.activa ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.12)",
                  border:     emp.activa ? "1px solid rgba(16,185,129,0.4)" : "1px solid rgba(239,68,68,0.3)",
                  color:      emp.activa ? "#34d399" : "#f87171",
                }}
              >
                {emp.activa ? "Activa" : "Inactiva"}
              </button>

              {/* Acciones */}
              <div className="flex items-center gap-2 justify-end">
                <button
                  onClick={() => { setFormError(null); setModal(emp); }}
                  title="Editar"
                  className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
                  style={{ color: "rgba(255,255,255,0.4)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(102,126,234,0.2)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round"
                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  onClick={() => setConfirmDelete(emp)}
                  title="Eliminar"
                  className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
                  style={{ color: "rgba(255,255,255,0.4)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(239,68,68,0.15)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && empresas.length === 0 && !error && (
        <div className="text-center py-16 rounded-xl"
             style={{ background: "rgba(255,255,255,0.02)", border: "1px dashed rgba(255,255,255,0.1)" }}>
          <p className="text-sm" style={{ color: "rgba(255,255,255,0.35)" }}>Sin empresas registradas aún.</p>
          <button onClick={() => setModal("crear")} className="mt-3 text-sm text-andromeda-400 hover:underline">
            Crear la primera empresa
          </button>
        </div>
      )}

      {/* Modal crear/editar */}
      {modal && modal !== "crear" && (
        <Modal title={`Editar — ${modal.nombre}`} onClose={() => setModal(null)}>
          <EmpresaForm
            inicial={modal}
            onSave={(data) => handleSave(data, modal)}
            onCancel={() => setModal(null)}
            saving={saving}
            error={formError}
          />
        </Modal>
      )}
      {modal === "crear" && (
        <Modal title="Nueva empresa" onClose={() => setModal(null)}>
          <EmpresaForm
            onSave={(data) => handleSave(data)}
            onCancel={() => setModal(null)}
            saving={saving}
            error={formError}
          />
        </Modal>
      )}

      {/* Confirmación eliminar */}
      {confirmDelete && (
        <Modal title="Eliminar empresa" onClose={() => setConfirmDelete(null)}>
          <div className="space-y-4">
            <p className="text-sm" style={{ color: "rgba(255,255,255,0.65)" }}>
              ¿Estás seguro de que deseas eliminar{" "}
              <span className="font-semibold text-white">{confirmDelete.nombre}</span>? Esta acción no se puede deshacer.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setConfirmDelete(null)}
                      className="flex-1 py-2.5 rounded-xl text-sm font-medium"
                      style={{ background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.6)" }}>
                Cancelar
              </button>
              <button onClick={() => handleDelete(confirmDelete)} disabled={saving}
                      className="flex-1 py-2.5 rounded-xl text-sm font-bold"
                      style={{ background: "rgba(239,68,68,0.8)", color: "#fff", opacity: saving ? 0.6 : 1 }}>
                {saving ? "Eliminando…" : "Eliminar"}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
