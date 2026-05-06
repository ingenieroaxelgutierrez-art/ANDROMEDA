"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { login, getMe, ApiError } from "@/lib/api";
import { guardarTokens, guardarRol, getSubRol, getRedirectPath } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const tokens = await login(email.trim(), password);
      guardarTokens(tokens.access_token);
      const me = await getMe();
      guardarRol(me.rol);
      // sub_rol viene en el JWT — ya fue guardado por guardarTokens()
      const subRol = getSubRol();
      router.push(getRedirectPath(me.rol, subRol));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Error de conexión. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative flex items-center justify-center min-h-screen z-10">
      {/* Tarjeta glass */}
      <div className="glass-strong rounded-2xl p-10 w-full max-w-md shadow-2xl space-y-8">

        {/* Marca */}
        <div className="text-center space-y-2">
          {/* Orbe logo */}
          <div className="mx-auto w-16 h-16 rounded-2xl overflow-hidden"
               style={{ background: "linear-gradient(135deg,#667eea,#764ba2,#f64f59)" }}>
            <Image src="/logo.png" alt="ANDROMEDA" width={64} height={64} className="w-full h-full object-cover" />
          </div>
          <h1 className="text-3xl font-black text-gradient tracking-tight">ANDROMEDA</h1>
          <p className="text-sm" style={{ color: "rgba(255,255,255,0.45)" }}>
            Advanced Neural Data Resource for Operations, Management, and Enterprise Assistance
          </p>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-1.5">
            <label htmlFor="email" className="block text-xs font-semibold tracking-wider"
                   style={{ color: "rgba(255,255,255,0.5)" }}>
              CORREO ELECTRÓNICO
            </label>
            <input
              id="email" type="email" autoComplete="email" required
              value={email} onChange={(e) => setEmail(e.target.value)}
              className="input-dark"
              placeholder="usuario@empresa.com"
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="password" className="block text-xs font-semibold tracking-wider"
                   style={{ color: "rgba(255,255,255,0.5)" }}>
              CONTRASEÑA
            </label>
            <input
              id="password" type="password" autoComplete="current-password" required
              value={password} onChange={(e) => setPassword(e.target.value)}
              className="input-dark"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="px-4 py-3 rounded-xl text-sm"
                 style={{ background: "rgba(246,79,89,0.12)", border: "1px solid rgba(246,79,89,0.3)", color: "#ff8a94" }}>
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full py-3">
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Iniciando sesión…
              </span>
            ) : "Iniciar sesión"}
          </button>
        </form>

        <p className="text-center text-xs" style={{ color: "rgba(255,255,255,0.2)" }}>
          ANDROMEDA {new Date().getFullYear()} · Acceso restringido
        </p>
      </div>
    </main>
  );
}
