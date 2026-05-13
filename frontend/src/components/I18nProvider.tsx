"use client";

// ============================================================
// ANDROMEDA — I18nProvider
// Context React que provee locale + función t() a toda la app.
// Persiste la elección en localStorage.
// ============================================================

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { Locale, LOCALE_STORAGE_KEY, t as _t, TranslationKey } from "@/lib/i18n";

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey) => string;
}

const I18nContext = createContext<I18nContextValue>({
  locale: "es",
  setLocale: () => {},
  t: (key) => key,
});

export function useI18n(): I18nContextValue {
  return useContext(I18nContext);
}

export default function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("es");

  useEffect(() => {
    const stored = localStorage.getItem(LOCALE_STORAGE_KEY) as Locale | null;
    if (stored && ["es", "en", "ja"].includes(stored)) {
      setLocaleState(stored);
    }
  }, []);

  useEffect(() => {
    // Actualiza el atributo lang del html para accesibilidad y SEO
    document.documentElement.lang = locale;
  }, [locale]);

  function setLocale(newLocale: Locale) {
    setLocaleState(newLocale);
    localStorage.setItem(LOCALE_STORAGE_KEY, newLocale);
  }

  return (
    <I18nContext.Provider value={{ locale, setLocale, t: (key) => _t(locale, key) }}>
      {children}
    </I18nContext.Provider>
  );
}
