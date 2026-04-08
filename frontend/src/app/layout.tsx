import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ANDROMEDA",
  description: "AI ERP Assistant — Panel de control",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-[--andromeda-bg]">{children}</body>
    </html>
  );
}
