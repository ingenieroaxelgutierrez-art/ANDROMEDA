"use client";

import { useEffect, useState, FormEvent } from "react";
import { getMe, actualizarPerfil, ApiError, UsuarioActual } from "@/lib/api";

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

const ROL_LABELS: Record<string, string> = { admin: "Administrador", agente: "Profesional", usuario: "Usuario" };

export default function ConfiguracionPage() {
  const [me, setMe]           = useState<UsuarioActual | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Campos editables
  const [nombre, setNombre]           = useState("");
  const [email, setEmail]             = useState("");
  const [passwordActual, setPasswordActual] = useState("");
  const [passwordNueva, setPasswordNueva]   = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");

  useEffect(() => {
    getMe()
      .then((u) => {
        setMe(u);
        setNombre(u.nombre);
        setEmail(u.email);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar perfil."))
      .finally(() => setLoading(false));
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (passwordNueva && passwordNueva !== passwordConfirm) {
      setError("Las contraseñas nuevas no coinciden.");
      return;
    }
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      const payload: Parameters<typeof actualizarPerfil>[0] = {};
      if (nombre !== me?.nombre)   payload.nombre = nombre;
      if (email !== me?.email)     payload.email  = email;
      if (passwordNueva) {
        payload.password_actual = passwordActual;
        payload.password_nueva  = passwordNueva;
      }
      const updated = await actualizarPerfil(payload);
      setMe(updated);
      setPasswordActual("");
      setPasswordNueva("");
      setPasswordConfirm("");
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Error al guardar.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">Mi perfil</h2>
        <p className="mt-1 text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
          Datos personales y seguridad de tu cuenta
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
          Perfil actualizado correctamente.
        </div>
      )}

      {me && (
        <>
          {/* Avatar / resumen */}
          <div className="rounded-xl p-5 flex items-center gap-4"
               style={{ background: "rgba(102,126,234,0.1)", border: "1px solid rgba(102,126,234,0.2)" }}>
            <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 text-lg font-black text-white"
                 style={{ background: "linear-gradient(135deg,#667eea,#764ba2)" }}>
              {me.nombre.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-bold text-white">{me.nombre}</p>
              <p className="text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.5)" }}>{me.email}</p>
            </div>
            <span className="ml-auto text-xs px-2.5 py-1 rounded-full font-medium"
                  style={{ background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.6)", border: "1px solid rgba(255,255,255,0.12)" }}>
              {ROL_LABELS[me.rol] ?? me.rol}
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <section className="rounded-xl p-6 space-y-4"
                     style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <h3 className="text-sm font-bold text-white">Información personal</h3>

              <Field label="Nombre completo">
                <input className="input-dark w-full text-sm" value={nombre}
                       onChange={(e) => setNombre(e.target.value)} required placeholder="Tu nombre" />
              </Field>

              <Field label="Correo electrónico">
                <input className="input-dark w-full text-sm" type="email" value={email}
                       onChange={(e) => setEmail(e.target.value)} required placeholder="tu@email.com" />
              </Field>
            </section>

            <section className="rounded-xl p-6 space-y-4"
                     style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <h3 className="text-sm font-bold text-white">Cambiar contraseña</h3>
              <p className="text-xs" style={{ color: "rgba(255,255,255,0.35)" }}>
                Déjalo en blanco si no deseas cambiar tu contraseña.
              </p>

              <Field label="Contraseña actual">
                <input className="input-dark w-full text-sm" type="password" value={passwordActual}
                       onChange={(e) => setPasswordActual(e.target.value)} placeholder="••••••••" />
              </Field>

              <div className="grid grid-cols-2 gap-4">
                <Field label="Nueva contraseña">
                  <input className="input-dark w-full text-sm" type="password" value={passwordNueva}
                         onChange={(e) => setPasswordNueva(e.target.value)} placeholder="••••••••" />
                </Field>
                <Field label="Confirmar contraseña">
                  <input className="input-dark w-full text-sm" type="password" value={passwordConfirm}
                         onChange={(e) => setPasswordConfirm(e.target.value)} placeholder="••••••••" />
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
              {saving ? "Guardando…" : "Guardar cambios"}
            </button>
          </form>
        </>
      )}
    </div>
  );
}


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

