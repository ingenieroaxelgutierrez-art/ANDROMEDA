"use client";

interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;
  /** HTML extra: tabla de datos o gráfica generada por el backend (tabla_html). */
  tablaHtml?: string;
}

import Image from "next/image";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useI18n } from "@/components/I18nProvider";

// ── Tipos de bloque de contenido ─────────────────────────────────────────────
type ContentPart =
  | { type: "markdown"; text: string }
  | { type: "iframe"; src: string; height: string }
  | { type: "html"; html: string };

/**
 * Separa el contenido en bloques:
 *  - texto Markdown normal
 *  - <iframe src="..."> → gráfica externa
 *  - <andromeda-chart>...</andromeda-chart> → documento Plotly completo (iframe srcDoc)
 *  - <div ...> / <img src="data:..."> / <table> → HTML embebido
 */
function splitContent(raw: string): ContentPart[] {
  const parts: ContentPart[] = [];

  // andromeda-chart se detecta PRIMERO (tiene contenido interno extenso)
  const re = /(<andromeda-chart>[\s\S]*?<\/andromeda-chart>|<iframe[^>]*>[\s\S]*?<\/iframe>|<div[\s\S]*?<\/div>|<img\s+src="data:[^"]+"\s*\/>|<table[\s\S]*?<\/table>)/gi;
  let last = 0;
  let m: RegExpExecArray | null;

  while ((m = re.exec(raw)) !== null) {
    if (m.index > last) {
      const txt = raw.slice(last, m.index);
      if (txt.trim()) parts.push({ type: "markdown", text: txt });
    }

    const block = m[1];

    // andromeda-chart → bloque Plotly completo
    if (/^<andromeda-chart/i.test(block)) {
      parts.push({ type: "html", html: block });
    // iframe con src → renderizar como iframe
    } else if (/^<iframe/i.test(block)) {
      const srcMatch = /src="([^"]+)"/.exec(block);
      const heightMatch = /height="([^"]+)"/.exec(block);
      if (srcMatch) {
        parts.push({ type: "iframe", src: srcMatch[1], height: heightMatch?.[1] ?? "620" });
      } else {
        parts.push({ type: "html", html: block });
      }
    } else {
      // div, img data-uri, table → HTML embebido
      parts.push({ type: "html", html: block });
    }

    last = m.index + m[0].length;
  }

  if (last < raw.length) {
    const txt = raw.slice(last);
    if (txt.trim()) parts.push({ type: "markdown", text: txt });
  }

  return parts;
}
/**
 * Renderiza un bloque HTML con lógica de seguridad:
 *  - Si contiene <andromeda-chart> (Plotly completo) → <iframe srcDoc> (los scripts SÍ ejecutan)
 *  - Si no → dangerouslySetInnerHTML (imágenes base64, tablas simples, sin scripts)
 */
function renderHtmlPart(html: string, key: number, chartLabel: string): React.ReactElement {
  const plotlyMatch = /^<andromeda-chart>([\s\S]*)<\/andromeda-chart>$/i.exec(html.trim());
  if (plotlyMatch) {
    return (
      <div
        key={key}
        className="my-3 rounded-xl overflow-hidden andromeda-chart"
        style={{ border: "1px solid rgba(102,126,234,0.3)", boxShadow: "0 4px 20px rgba(0,0,0,0.4)" }}
      >
        <iframe
          srcDoc={plotlyMatch[1]}
          style={{ width: "100%", height: "500px", border: "none", display: "block", borderRadius: "inherit" }}
          title={`${chartLabel} ${key}`}
          sandbox="allow-scripts"
        />
      </div>
    );
  }
  // HTML sin scripts: tablas, imágenes base64
  return (
    <div
      key={key}
      className="my-3 rounded-xl overflow-x-auto andromeda-chart"
      style={{ border: "1px solid rgba(102,126,234,0.3)", padding: "8px", background: "rgba(0,0,0,0.25)" }}
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function ChatBubble({ role, content, tablaHtml }: Readonly<ChatBubbleProps>) {
  const { t } = useI18n();
  const chartLabel = t("common.chart");
  const isUser = role === "user";
  const parts = isUser ? null : splitContent(content);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      {/* Avatar asistente */}
      {!isUser && (
        <div
          className="w-8 h-8 rounded-xl flex-shrink-0 overflow-hidden mr-3 mt-0.5"
          style={{ background: "linear-gradient(135deg,#667eea,#764ba2)" }}
        >
          <Image src="/logo.png" alt="ANDROMEDA" width={32} height={32} className="w-full h-full object-cover" />
        </div>
      )}

      <div
        className={`rounded-2xl text-sm leading-relaxed ${isUser ? "px-4 py-3 max-w-[78%]" : "w-full max-w-[92%] px-4 py-3"}`}
        style={
          isUser
            ? {
                background: "linear-gradient(135deg,#667eea,#764ba2)",
                color: "#fff",
                borderBottomRightRadius: "4px",
                boxShadow: "0 4px 20px rgba(102,126,234,0.35)",
                whiteSpace: "pre-wrap",
              }
            : {
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.10)",
                color: "#e2e8f0",
                borderBottomLeftRadius: "4px",
                backdropFilter: "blur(12px)",
              }
        }
      >
        {isUser ? (
          content
        ) : (
          <>
            {parts!.map((part, i) =>
              part.type === "iframe" ? (
                <div
                  key={i}
                  className="my-3 rounded-xl overflow-hidden"
                  style={{ border: "1px solid rgba(102,126,234,0.3)", boxShadow: "0 4px 20px rgba(0,0,0,0.4)" }}
                >
                  <iframe
                    src={part.src}
                    width="100%"
                    height={`${part.height}px`}
                    frameBorder="0"
                  title={`${chartLabel} ${i}`}
                    style={{ display: "block", borderRadius: "inherit" }}
                  />
                </div>
              ) : part.type === "html" ? (
                /* HTML embebido: gráfica Plotly (andromeda-chart → iframe) o Matplotlib base64 */
                renderHtmlPart(part.html, i, chartLabel)
              ) : (
                <ReactMarkdown
                key={i}
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => <h1 className="text-lg font-bold mt-3 mb-1 text-white">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-base font-bold mt-3 mb-1 text-white">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1 text-purple-300">{children}</h3>,
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
                  em: ({ children }) => <em className="italic text-purple-200">{children}</em>,
                  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-0.5 pl-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-0.5 pl-1">{children}</ol>,
                  li: ({ children }) => <li className="text-slate-200">{children}</li>,
                  code: ({ inline, children }: { inline?: boolean; children?: React.ReactNode }) =>
                    inline ? (
                      <code className="px-1.5 py-0.5 rounded text-xs font-mono" style={{ background: "rgba(102,126,234,0.25)", color: "#a78bfa" }}>
                        {children}
                      </code>
                    ) : (
                      <code className="block w-full px-3 py-2 rounded-lg text-xs font-mono overflow-x-auto" style={{ background: "rgba(0,0,0,0.35)", color: "#86efac" }}>
                        {children}
                      </code>
                    ),
                  pre: ({ children }) => (
                    <pre className="my-2 rounded-lg overflow-x-auto" style={{ background: "rgba(0,0,0,0.35)" }}>
                      {children}
                    </pre>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 pl-3 my-2 italic text-slate-300" style={{ borderColor: "#667eea" }}>
                      {children}
                    </blockquote>
                  ),
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-2">
                      <table className="w-full text-xs border-collapse">{children}</table>
                    </div>
                  ),
                  thead: ({ children }) => <thead style={{ background: "rgba(102,126,234,0.2)" }}>{children}</thead>,
                  th: ({ children }) => (
                    <th className="px-3 py-1.5 text-left font-semibold text-purple-300" style={{ border: "1px solid rgba(255,255,255,0.1)" }}>
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="px-3 py-1.5 text-slate-300" style={{ border: "1px solid rgba(255,255,255,0.08)" }}>
                      {children}
                    </td>
                  ),
                  tr: ({ children }) => <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>{children}</tr>,
                  hr: () => <hr className="my-3 opacity-20" />,
                  img: ({ src, alt }) => {
                    // Redirigir imágenes del manual al proxy Next.js (que añade el Bearer token).
                    // El backend genera URLs absolutas como http://localhost:8000/manuales/imagenes/x.png
                    const proxied = src?.includes("/manuales/imagenes/")
                      ? `/api/manuales/imagenes/${src.split("/manuales/imagenes/")[1]}`
                      : src;
                    return (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={proxied}
                        alt={alt ?? ""}
                        className="max-w-full rounded-lg my-2"
                        style={{ maxHeight: "320px", objectFit: "contain" }}
                      />
                    );
                  },
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer" className="underline text-purple-400 hover:text-purple-300">
                      {children}
                    </a>
                  ),
                }}
              >
                {part.text}
              </ReactMarkdown>
            )
          )}
            {/* Panel de tabla/gráfica extra proveniente de tabla_html del backend */}
            {tablaHtml && renderHtmlPart(tablaHtml, -1, t("common.additionalChart"))}
          </>
        )}
      </div>

      {/* Avatar usuario */}
      {isUser && (
        <div
          className="w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center ml-3 mt-0.5"
          style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.12)" }}
        >
          <svg className="w-4 h-4" style={{ color: "rgba(255,255,255,0.6)" }} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      )}
    </div>
  );
}
