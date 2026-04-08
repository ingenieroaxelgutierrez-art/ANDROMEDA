"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import { enviarMensaje, getMe, ApiError, MensajeChat } from "@/lib/api";
import ChatBubble from "@/components/ChatBubble";

export default function ChatPage() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [empresaId, setEmpresaId] = useState<string | null>(null);
  const [mensajes, setMensajes] = useState<MensajeChat[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

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
      const resp = await enviarMensaje(texto, sessionId, empresaId);
      // El servidor retorna el historial completo; lo usamos directamente
      setMensajes(resp.historial);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Error al enviar el mensaje.");
      }
      // Revertir mensaje optimista en caso de error
      setMensajes((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-3xl mx-auto">
      <h2 className="text-xl font-bold text-andromeda-700 mb-4">
        Chat con ANDROMEDA
      </h2>

      {/* Panel de mensajes */}
      <div className="flex-1 overflow-y-auto chat-scroll bg-gray-50 rounded-xl border border-gray-200 p-4">
        {mensajes.length === 0 ? (
          <p className="text-center text-sm text-gray-400 mt-16">
            ¡Hola! Escribe una consulta sobre tu ERP, por ejemplo:
            <br />
            <em>«¿Cuánto se vendió este mes?»</em>
          </p>
        ) : (
          mensajes.map((m, i) => (
            <ChatBubble key={i} role={m.role} content={m.content} />
          ))
        )}
        {loading && (
          <div className="flex justify-start mb-3">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
              <span className="inline-flex gap-1">
                <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:300ms]" />
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Error */}
      {error && (
        <p className="text-sm text-red-600 mt-2 px-1">{error}</p>
      )}

      {/* Input */}
      <form
        onSubmit={handleEnviar}
        className="mt-3 flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading || !empresaId}
          placeholder={
            empresaId ? "Escribe tu consulta aquí…" : "Cargando sesión…"
          }
          className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg
                     focus:outline-none focus:ring-2 focus:ring-andromeda-500
                     disabled:opacity-50 transition"
        />
        <button
          type="submit"
          disabled={loading || !input.trim() || !empresaId}
          className="px-5 py-2.5 bg-andromeda-500 hover:bg-andromeda-600
                     text-white font-semibold rounded-lg transition
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Enviar
        </button>
      </form>
    </div>
  );
}
