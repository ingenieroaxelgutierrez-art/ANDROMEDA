import type { Metadata } from "next";
import "./globals.css";
import I18nProvider from "@/components/I18nProvider";

export const metadata: Metadata = {
  title: "ANDROMEDA - 結",
  description: "Advanced Neural Data Resource for Operations, Management & Enterprise Decision Analytics",
  icons: { icon: "/logo1.png" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className="min-h-screen relative">
        <I18nProvider>{children}</I18nProvider>
      </body>
    </html>
  );
}
