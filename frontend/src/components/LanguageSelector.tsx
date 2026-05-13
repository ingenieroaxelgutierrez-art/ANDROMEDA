"use client";

// ============================================================
// ANDROMEDA — LanguageSelector
// Dropdown para elegir idioma. Se integra en el sidebar NavBar.
// ============================================================

import { useState, useRef, useEffect } from "react";
import { LOCALES, Locale } from "@/lib/i18n";
import { useI18n } from "@/components/I18nProvider";

export default function LanguageSelector() {
  const { locale, setLocale, t } = useI18n();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const current = LOCALES.find((l) => l.value === locale) ?? LOCALES[0];

  // Cierra el dropdown al hacer click fuera
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <div ref={ref} className="relative px-3 pb-2">
      {/* Etiqueta */}
      <p className="px-1 pb-1.5 text-xs font-semibold tracking-widest uppercase"
         style={{ color: "rgba(255,255,255,0.3)" }}>
        {t("nav.language")}
      </p>

      {/* Botón trigger */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 w-full px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
        style={{
          color:      "rgba(255,255,255,0.65)",
          background: "rgba(255,255,255,0.05)",
          border:     "1px solid rgba(255,255,255,0.1)",
        }}
        onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.09)")}
        onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.05)")}
      >
        <span className="text-base leading-none">{current.flag}</span>
        <span>{current.label}</span>
        <svg
          className="w-3.5 h-3.5 ml-auto opacity-50 transition-transform duration-200"
          style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)" }}
          fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Opciones */}
      {open && (
        <div
          className="absolute bottom-full mb-1 left-3 right-3 rounded-xl overflow-hidden z-50 shadow-2xl"
          style={{
            background:    "rgba(15,15,45,0.97)",
            border:        "1px solid rgba(255,255,255,0.12)",
            backdropFilter:"blur(20px)",
          }}
        >
          {LOCALES.map((l) => {
            const isSelected = locale === l.value;
            return (
              <button
                key={l.value}
                onClick={() => { setLocale(l.value as Locale); setOpen(false); }}
                className="flex items-center gap-3 w-full px-4 py-2.5 text-sm font-medium transition-colors duration-150"
                style={{
                  color:      isSelected ? "#fff" : "rgba(255,255,255,0.6)",
                  background: isSelected ? "rgba(102,126,234,0.22)" : "transparent",
                }}
                onMouseEnter={(e) => {
                  if (!isSelected)
                    (e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.06)";
                }}
                onMouseLeave={(e) => {
                  if (!isSelected)
                    (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                }}
              >
                <span className="text-base leading-none">{l.flag}</span>
                <span>{l.label}</span>
                {isSelected && (
                  <svg
                    className="w-3.5 h-3.5 ml-auto"
                    style={{ color: "#667eea" }}
                    fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
