"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { logout } from "@/lib/api";

const LINKS = [
  { href: "/chat", label: "Chat" },
  { href: "/configuracion", label: "Configuración" },
  { href: "/metricas", label: "Métricas" },
];

export default function NavBar() {
  const router = useRouter();
  const pathname = usePathname();

  async function handleLogout() {
    try {
      await logout();
    } finally {
      router.push("/login");
    }
  }

  return (
    <nav className="bg-andromeda-700 text-white shadow-md">
      <div className="container mx-auto px-4 max-w-6xl flex items-center justify-between h-14">
        {/* Logo */}
        <span className="font-bold text-lg tracking-tight">ANDROMEDA</span>

        {/* Links */}
        <ul className="flex items-center gap-6 text-sm font-medium">
          {LINKS.map(({ href, label }) => (
            <li key={href}>
              <Link
                href={href}
                className={`hover:text-andromeda-100 transition ${
                  pathname === href ? "border-b-2 border-white pb-0.5" : ""
                }`}
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="text-sm hover:text-andromeda-100 transition"
        >
          Cerrar sesión
        </button>
      </div>
    </nav>
  );
}
