"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import Image from "next/image";
import { enviarMensaje, getMe, ApiError, MensajeChat } from "@/lib/api";
import ChatBubble from "@/components/ChatBubble";

export default function AgenteChatPage() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [empresaId, setEmpresaId]   = useState<string | null>(null);
  const [nombreEmpresa, setNombreEmpresa] = useState<string>("");
  const [mensajes, setMensajes]     = useState<MensajeChat[]>([]);
  const [input, setInput]           = useState("");
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState<string | null>(null);
  const bottomRef                   = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getMe()
      .then((u) => {
        setEmpresaId(u.empresa_id);
        setNombreEmpresa(u.nombre);
      })
      .catch(() => setEmpresaId(null));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes]);

  async function handleEnviar(e: FormEvent) {
    e.preventDefault();
    const texto = input.trim();
    if (!texto || !empresaId) return;

    const msgUsuario: MensajeChat = { role: "user", content: texto };
    setMensajes((prev) => [...prev, msgUsuario]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const resp = await enviarMensaje(texto, sessionId, empresaId);
      setMensajes(resp.historial);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Error al enviar el mensaje.");
      setMensajes((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col max-w-3xl mx-auto" style={{ height: "calc(100vh - 64px)" }}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-9 h-9 rounded-xl overflow-hidden flex-shrink-0"
             style={{ background: "linear-gradient(135deg,#667eea,#764ba2)" }}>
          <Image src="/logo.png" alt="ANDROMEDA" width={36} height={36} className="w-full h-full object-cover" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-white leading-tight">Chat con ANDROMEDA</h2>
          <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium"
                style={{
                  background: empresaId ? "rgba(52,211,153,0.15)" : "rgba(255,255,255,0.08)",
                  color: empresaId ? "#34d399" : "rgba(255,255,255,0.4)",
                  border: empresaId ? "1px solid rgba(52,211,153,0.3)" : "1px solid rgba(255,255,255,0.1)",
                }}>
            <span className="w-1.5 h-1.5 rounded-full"
                  style={{ background: empresaId ? "#34d399" : "rgba(255,255,255,0.3)" }} />
            {empresaId ? (nombreEmpresa ? `Hola, ${nombreEmpresa}` : "Conectado") : "Cargando sesión…"}
          </span>
        </div>
      </div>

      {/* Panel de mensajes */}
      <div className="flex-1 overflow-y-auto chat-scroll rounded-2xl p-4"
           style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
        {mensajes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 py-12">
            <div className="w-16 h-16 rounded-2xl overflow-hidden"
                 style={{ background: "linear-gradient(135deg,#667eea,#764ba2)", opacity: 0.7 }}>
              <Image src="/logo.png" alt="ANDROMEDA" width={64} height={64} className="w-full h-full object-cover" />
            </div>
            <p className="text-center text-sm" style={{ color: "rgba(255,255,255,0.35)" }}>
              ¡Hola! Escribe una consulta sobre tu ERP, por ejemplo:
              <br />
              <em style={{ color: "rgba(255,255,255,0.5)" }}>«¿Cuánto se vendió este mes?»</em>
            </p>
          </div>
        ) : (
          mensajes.map((m, i) => (
            <ChatBubble key={`${m.role}-${i}`} role={m.role} content={m.content} />
          ))
        )}
        {loading && (
          <div className="flex items-end gap-2 mb-3">
            <div className="w-8 h-8 rounded-xl flex-shrink-0 overflow-hidden"
                 style={{ background: "linear-gradient(135deg,#667eea,#764ba2)" }}>
              <Image src="/logo.png" alt="ANDROMEDA" width={32} height={32} className="w-full h-full object-cover" />
            </div>
            <div className="px-4 py-3 rounded-2xl rounded-bl-sm"
                 style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)" }}>
              <span className="inline-flex gap-1">
                <span className="typing-dot" />
                <span className="typing-dot" style={{ animationDelay: "0.15s" }} />
                <span className="typing-dot" style={{ animationDelay: "0.3s" }} />
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && (
        <p className="text-sm mt-2 px-1" style={{ color: "#f87171" }}>{error}</p>
      )}

      {/* Input */}
      <form onSubmit={handleEnviar} className="mt-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading || !empresaId}
          placeholder={empresaId ? "Escribe tu consulta aquí…" : "Cargando sesión…"}
          className="input-dark flex-1"
        />
        <button
          type="submit"
          disabled={loading || !input.trim() || !empresaId}
          className="btn-primary px-5 py-2.5 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
          Enviar
        </button>
      </form>
    </div>
  );
}
