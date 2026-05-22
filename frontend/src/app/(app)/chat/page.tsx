"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import Image from "next/image";
import { enviarMensaje, getMe, ApiError, MensajeChat } from "@/lib/api";
import ChatBubble from "@/components/ChatBubble";
import { useI18n } from "@/components/I18nProvider";

const SESSION_KEY = "andromeda_chat_session_id";
const HISTORY_KEY = "andromeda_chat_history";

export default function ChatPage() {
  const { t, locale } = useI18n();
  const [sessionId] = useState<string>(() => {
    if (typeof window === "undefined") return crypto.randomUUID();
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (stored) return stored;
    const id = crypto.randomUUID();
    sessionStorage.setItem(SESSION_KEY, id);
    return id;
  });
  const [empresaId, setEmpresaId] = useState<string | null>(null);
  const [mensajes, setMensajes] = useState<MensajeChat[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const raw = sessionStorage.getItem(HISTORY_KEY);
      return raw ? (JSON.parse(raw) as MensajeChat[]) : [];
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Persistir historial en sessionStorage cuando cambia
  useEffect(() => {
    if (typeof window !== "undefined") {
      sessionStorage.setItem(HISTORY_KEY, JSON.stringify(mensajes));
    }
  }, [mensajes]);

  // Cargar empresa_id del usuario al montar
  useEffect(() => {
    getMe()
      .then((u) => setEmpresaId(u.empresa_id))
      .catch(() => setEmpresaId(null));
  }, []);

  // Auto-scroll al último mensaje
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes]);

  async function handleEnviar(e: FormEvent) {
    e.preventDefault();
    const texto = input.trim();
    if (!texto || !empresaId) return;

    // Optimistic UI: agregar mensaje del usuario inmediatamente
    const msgUsuario: MensajeChat = { role: "user", content: texto };
    setMensajes((prev) => [...prev, msgUsuario]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const resp = await enviarMensaje(texto, sessionId, mensajes, empresaId ?? undefined, locale);
      // El servidor retorna el historial completo; lo usamos directamente
      setMensajes(resp.historial);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(t("chat.errorSend"));
      }
      // Revertir mensaje optimista en caso de error
      setMensajes((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col max-w-3xl mx-auto chat-container">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div
          className="w-9 h-9 rounded-xl overflow-hidden flex-shrink-0"
          style={{ background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" }}
        >
          <Image src="/logo.png" alt="ANDROMEDA" width={36} height={36} className="w-full h-full object-cover" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-white leading-tight">{t("chat.title")}</h2>
          <span
            className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium"
            style={{
              background: empresaId ? "rgba(52,211,153,0.15)" : "rgba(255,255,255,0.08)",
              color: empresaId ? "#34d399" : "rgba(255,255,255,0.4)",
              border: empresaId ? "1px solid rgba(52,211,153,0.3)" : "1px solid rgba(255,255,255,0.1)",
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: empresaId ? "#34d399" : "rgba(255,255,255,0.3)" }}
            />
            {empresaId ? t("chat.connected") : t("chat.connecting")}
          </span>
        </div>
      </div>

      {/* Panel de mensajes */}
      <div
        className="flex-1 overflow-y-auto chat-scroll rounded-2xl p-4"
        style={{
          background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.07)",
        }}
      >
        {mensajes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 py-12">
            <div
              className="w-16 h-16 rounded-2xl overflow-hidden"
              style={{ background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", opacity: 0.7 }}
            >
              <Image src="/logo.png" alt="ANDROMEDA" width={64} height={64} className="w-full h-full object-cover" />
            </div>
            <p className="text-center text-sm" style={{ color: "rgba(255,255,255,0.35)" }}>
              {t("chat.emptyHint")}
              <br />
              <em style={{ color: "rgba(255,255,255,0.5)" }}>{t("chat.emptyExample")}</em>
            </p>
          </div>
        ) : (
          mensajes.map((m, i) => (
            <ChatBubble key={`${m.role}-${i}`} role={m.role} content={m.content} />
          ))
        )}
        {loading && (
          <div className="flex items-end gap-2 mb-3">
            <div
              className="w-8 h-8 rounded-xl flex-shrink-0 overflow-hidden"
              style={{ background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" }}
            >
              <Image src="/logo.png" alt="ANDROMEDA" width={32} height={32} className="w-full h-full object-cover" />
            </div>
            <div
              className="px-4 py-3 rounded-2xl rounded-bl-sm"
              style={{
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            >
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

      {/* Error */}
      {error && (
        <p
          className="text-sm mt-2 px-1"
          style={{ color: "#f87171" }}
        >
          {error}
        </p>
      )}

      {/* Input */}
      <form onSubmit={handleEnviar} className="mt-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading || !empresaId}
          placeholder={empresaId ? t("chat.placeholder") : t("chat.connecting")}
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
          {t("chat.send")}
        </button>
      </form>
    </div>
  );
}
