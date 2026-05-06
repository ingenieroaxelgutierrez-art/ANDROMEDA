import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ANDROMEDA",
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
      <body className="min-h-screen relative">{children}</body>
    </html>
  );
}
