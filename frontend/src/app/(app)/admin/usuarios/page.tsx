"use client";

import { useEffect, useState, FormEvent } from "react";
import {
  getUsuarios, crearUsuario, actualizarUsuario, eliminarUsuario,
  getEmpresas, ApiError, UsuarioSaaS, UsuarioCreate, EmpresaSaaS,
} from "@/lib/api";

const ROL_LABELS: Record<string, string> = { admin: "Admin", agente: "Agente", usuario: "Usuario" };
const ROL_COLORS: Record<string, string> = {
  admin:   "rgba(246,79,89,0.35)",
  agente:  "rgba(102,126,234,0.35)",
  usuario: "rgba(118,75,162,0.35)",
};
const ROL_BORDER: Record<string, string> = {
  admin:   "rgba(246,79,89,0.55)",
  agente:  "rgba(102,126,234,0.55)",
  usuario: "rgba(118,75,162,0.55)",
};

// ── Componentes auxiliares ────────────────────────────────────────────────────

function Modal({ title, onClose, children }: {
  title: string; onClose: () => void; children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4"
         style={{ background: "rgba(0,0,0,0.65)", backdropFilter: "blur(4px)" }}>
      <div className="glass-strong rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b"
             style={{ borderColor: "rgba(255,255,255,0.08)" }}>
          <h3 className="font-bold text-white">{title}</h3>
          <button onClick={onClose}
                  className="w-7 h-7 rounded-lg flex items-center justify-center"
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

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-semibold tracking-wider uppercase"
             style={{ color: "rgba(255,255,255,0.5)" }}>{label}</label>
      {children}
    </div>
  );
}

// ── Formulario usuario ────────────────────────────────────────────────────────

interface FormData {
  nombre: string;
  email: string;
  password: string;
  rol: "admin" | "agente" | "usuario";
  empresa_id: string;
  activo: boolean;
}

function defaultForm(u?: UsuarioSaaS): FormData {
  return {
    nombre:     u?.nombre     ?? "",
    email:      u?.email      ?? "",
    password:   "",
    rol:        u?.rol        ?? "usuario",
    empresa_id: u?.empresa_id ?? "",
    activo:     u?.activo     ?? true,
  };
}

function UsuarioForm({
  inicial, empresas, onSave, onCancel, saving, error,
}: {
  inicial?: UsuarioSaaS;
  empresas: EmpresaSaaS[];
  onSave: (data: FormData) => void;
  onCancel: () => void;
  saving: boolean;
  error: string | null;
}) {
  const [form, setForm] = useState<FormData>(() => defaultForm(inicial));
  function set<K extends keyof FormData>(k: K, v: FormData[K]) { setForm((p) => ({ ...p, [k]: v })); }

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSave(form); }} className="space-y-4">
      {error && (
        <div className="px-3 py-2.5 rounded-lg text-xs"
             style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171" }}>
          {error}
        </div>
      )}

      <Field label="Nombre completo">
        <input className="input-dark w-full text-sm" required value={form.nombre}
               onChange={(e) => set("nombre", e.target.value)} placeholder="Juan Pérez" />
      </Field>

      <Field label="Correo electrónico">
        <input className="input-dark w-full text-sm" type="email" required value={form.email}
               onChange={(e) => set("email", e.target.value)} placeholder="juan@empresa.com" />
      </Field>

      <Field label={inicial ? "Nueva contraseña (dejar vacío para no cambiar)" : "Contraseña"}>
        <input className="input-dark w-full text-sm" type="password"
               required={!inicial} value={form.password}
               onChange={(e) => set("password", e.target.value)} placeholder="••••••••" />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Rol">
          <select className="input-dark w-full text-sm" value={form.rol}
                  onChange={(e) => set("rol", e.target.value as FormData["rol"])}>
            <option value="usuario">Usuario</option>
            <option value="agente">Agente</option>
            <option value="admin">Admin</option>
          </select>
        </Field>

        <Field label="Empresa asignada">
          <select className="input-dark w-full text-sm" value={form.empresa_id}
                  onChange={(e) => set("empresa_id", e.target.value)}>
            <option value="">— Sin empresa —</option>
            {empresas.map((emp) => (
              <option key={emp.id} value={emp.id}>{emp.nombre}</option>
            ))}
          </select>
        </Field>
      </div>

      <Field label="Estado">
        <label className="flex items-center gap-2 mt-1 cursor-pointer">
          <input type="checkbox" className="w-4 h-4 accent-andromeda-500"
                 checked={form.activo} onChange={(e) => set("activo", e.target.checked)} />
          <span className="text-sm text-white">Usuario activo</span>
        </label>
      </Field>

      <div className="flex gap-3 pt-2">
        <button type="button" onClick={onCancel}
                className="flex-1 py-2.5 rounded-xl text-sm font-medium"
                style={{ background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.6)" }}>
          Cancelar
        </button>
        <button type="submit" disabled={saving}
                className="flex-1 py-2.5 rounded-xl text-sm font-bold"
                style={{ background: "linear-gradient(135deg,#667eea,#764ba2)", color: "#fff", opacity: saving ? 0.6 : 1 }}>
          {saving ? "Guardando…" : inicial ? "Guardar cambios" : "Crear usuario"}
        </button>
      </div>
    </form>
  );
}

// ── Página principal ──────────────────────────────────────────────────────────

export default function UsuariosPage() {
  const [usuarios, setUsuarios]   = useState<UsuarioSaaS[]>([]);
  const [empresas, setEmpresas]   = useState<EmpresaSaaS[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);
  const [modal, setModal]         = useState<"crear" | UsuarioSaaS | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<UsuarioSaaS | null>(null);
  const [saving, setSaving]       = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [filtroRol, setFiltroRol] = useState<string>("todos");
  const [busqueda, setBusqueda]   = useState("");

  useEffect(() => {
    Promise.all([getUsuarios(), getEmpresas()])
      .then(([u, e]) => { setUsuarios(u); setEmpresas(e); })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar datos."))
      .finally(() => setLoading(false));
  }, []);

  async function handleSave(data: FormData, editando?: UsuarioSaaS) {
    setSaving(true);
    setFormError(null);
    try {
      if (editando) {
        const payload: Partial<UsuarioSaaS> & { password?: string } = {
          nombre:     data.nombre,
          email:      data.email,
          rol:        data.rol,
          empresa_id: data.empresa_id || null,
          activo:     data.activo,
        };
        if (data.password) payload.password = data.password;
        const updated = await actualizarUsuario(editando.id, payload);
        setUsuarios((prev) => prev.map((u) => u.id === updated.id ? updated : u));
      } else {
        const payload: UsuarioCreate = {
          nombre:     data.nombre,
          email:      data.email,
          password:   data.password,
          rol:        data.rol,
          empresa_id: data.empresa_id || null,
        };
        const nuevo = await crearUsuario(payload);
        setUsuarios((prev) => [...prev, nuevo]);
      }
      setModal(null);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Error al guardar.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(usuario: UsuarioSaaS) {
    setSaving(true);
    try {
      await eliminarUsuario(usuario.id);
      setUsuarios((prev) => prev.filter((u) => u.id !== usuario.id));
      setConfirmDelete(null);
    } catch { /* silencioso */ } finally { setSaving(false); }
  }

  async function toggleActivo(usuario: UsuarioSaaS) {
    try {
      const updated = await actualizarUsuario(usuario.id, { activo: !usuario.activo });
      setUsuarios((prev) => prev.map((u) => u.id === updated.id ? updated : u));
    } catch { /* silencioso */ }
  }

  const filtrados = usuarios.filter((u) => {
    const matchRol = filtroRol === "todos" || u.rol === filtroRol;
    const q = busqueda.toLowerCase();
    const matchBusqueda = !q || u.nombre.toLowerCase().includes(q) || u.email.toLowerCase().includes(q);
    return matchRol && matchBusqueda;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-black text-white tracking-tight">Usuarios</h2>
          <p className="mt-1 text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
            {usuarios.length} usuario{usuarios.length !== 1 ? "s" : ""} registrado{usuarios.length !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          onClick={() => { setFormError(null); setModal("crear"); }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold"
          style={{ background: "linear-gradient(135deg,#667eea,#764ba2)", color: "#fff" }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Nuevo usuario
        </button>
      </div>

      {/* Filtros */}
      <div className="flex gap-3 items-center">
        <input
          className="input-dark text-sm flex-1 max-w-xs"
          placeholder="Buscar por nombre o email…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
        />
        {(["todos", "admin", "agente", "usuario"] as const).map((r) => (
          <button key={r}
                  onClick={() => setFiltroRol(r)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                  style={{
                    background: filtroRol === r ? "rgba(102,126,234,0.25)" : "rgba(255,255,255,0.05)",
                    color: filtroRol === r ? "#fff" : "rgba(255,255,255,0.5)",
                    border: filtroRol === r ? "1px solid rgba(102,126,234,0.4)" : "1px solid rgba(255,255,255,0.08)",
                  }}>
            {r === "todos" ? "Todos" : ROL_LABELS[r]}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm animate-pulse" style={{ color: "rgba(255,255,255,0.4)" }}>Cargando…</p>}
      {error   && (
        <div className="px-4 py-3 rounded-lg text-sm"
             style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171" }}>
          {error}
        </div>
      )}

      {/* Tabla */}
      {!loading && filtrados.length > 0 && (
        <div className="rounded-xl overflow-hidden"
             style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
          <div className="grid grid-cols-[1fr_auto_1fr_auto_auto] gap-4 px-5 py-3 text-xs font-semibold uppercase tracking-wider"
               style={{ borderBottom: "1px solid rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.35)" }}>
            <span>Usuario</span>
            <span className="text-center">Rol</span>
            <span>Empresa</span>
            <span className="text-center">Estado</span>
            <span className="text-right">Acciones</span>
          </div>

          {filtrados.map((u) => (
            <div key={u.id}
                 className="grid grid-cols-[1fr_auto_1fr_auto_auto] gap-4 items-center px-5 py-3.5"
                 style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
              <div>
                <p className="text-sm font-semibold text-white">{u.nombre}</p>
                <p className="text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.4)" }}>{u.email}</p>
              </div>

              <span className="text-xs font-medium px-2.5 py-1 rounded-full"
                    style={{
                      background: ROL_COLORS[u.rol] ?? "rgba(100,116,139,0.4)",
                      border: `1px solid ${ROL_BORDER[u.rol] ?? "rgba(100,116,139,0.5)"}`,
                      color: "#fff",
                    }}>
                {ROL_LABELS[u.rol] ?? u.rol}
              </span>

              <p className="text-sm truncate" style={{ color: u.empresa_nombre ? "rgba(255,255,255,0.65)" : "rgba(255,255,255,0.25)" }}>
                {u.empresa_nombre ?? "— Sin empresa —"}
              </p>

              <button onClick={() => toggleActivo(u)}
                      className="text-xs font-medium px-2.5 py-1 rounded-full transition-colors"
                      style={{
                        background: u.activo ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.12)",
                        border:     u.activo ? "1px solid rgba(16,185,129,0.4)" : "1px solid rgba(239,68,68,0.3)",
                        color:      u.activo ? "#34d399" : "#f87171",
                      }}>
                {u.activo ? "Activo" : "Inactivo"}
              </button>

              <div className="flex items-center gap-2 justify-end">
                <button onClick={() => { setFormError(null); setModal(u); }}
                        className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{ color: "rgba(255,255,255,0.4)" }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(102,126,234,0.2)")}
                        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round"
                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button onClick={() => setConfirmDelete(u)}
                        className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{ color: "rgba(255,255,255,0.4)" }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(239,68,68,0.15)")}
                        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
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

      {!loading && filtrados.length === 0 && !error && (
        <div className="text-center py-16 rounded-xl"
             style={{ background: "rgba(255,255,255,0.02)", border: "1px dashed rgba(255,255,255,0.1)" }}>
          <p className="text-sm" style={{ color: "rgba(255,255,255,0.35)" }}>
            {busqueda || filtroRol !== "todos" ? "Sin resultados para los filtros aplicados." : "Sin usuarios registrados aún."}
          </p>
        </div>
      )}

      {/* Modal crear/editar */}
      {modal && modal !== "crear" && (
        <Modal title={`Editar — ${modal.nombre}`} onClose={() => setModal(null)}>
          <UsuarioForm inicial={modal} empresas={empresas}
                       onSave={(d) => handleSave(d, modal)}
                       onCancel={() => setModal(null)}
                       saving={saving} error={formError} />
        </Modal>
      )}
      {modal === "crear" && (
        <Modal title="Nuevo usuario" onClose={() => setModal(null)}>
          <UsuarioForm empresas={empresas}
                       onSave={(d) => handleSave(d)}
                       onCancel={() => setModal(null)}
                       saving={saving} error={formError} />
        </Modal>
      )}

      {/* Confirmar eliminar */}
      {confirmDelete && (
        <Modal title="Eliminar usuario" onClose={() => setConfirmDelete(null)}>
          <div className="space-y-4">
            <p className="text-sm" style={{ color: "rgba(255,255,255,0.65)" }}>
              ¿Eliminar a <span className="font-semibold text-white">{confirmDelete.nombre}</span>? Esta acción no se puede deshacer.
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
