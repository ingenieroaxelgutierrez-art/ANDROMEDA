/**
 * GET /api/manuales/imagenes/[filename]
 *
 * Proxy server-side que reenvía la petición al backend con el Bearer token
 * leído desde la cookie `andromeda_at` (SameSite=Strict, no httpOnly).
 *
 * Necesario porque el endpoint del backend requiere autenticación y los
 * elementos <img> del navegador no pueden añadir cabeceras Authorization.
 */

import { NextRequest, NextResponse } from "next/server";

// Server-side: usar la URL interna Docker si está definida.
// En dev local sin Docker cae al valor público o al fallback.
const BACKEND =
  process.env.BACKEND_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

// Tipos MIME admitidos para imágenes del manual.
const MIME_ALLOWED = new Set([
  "image/png",
  "image/jpeg",
  "image/gif",
  "image/webp",
  "image/svg+xml",
]);

export async function GET(
  request: NextRequest,
  { params }: { params: { filename: string } }
): Promise<NextResponse> {
  // Leer token desde cookie (misma origin → cookie enviada automáticamente).
  const token = request.cookies.get("andromeda_at")?.value;

  if (!token) {
    return NextResponse.json({ error: "No autenticado" }, { status: 401 });
  }

  // Sanitizar filename: no permitir traversal (solo el nombre base).
  const filename = params.filename.replace(/[/\\]/g, "");
  if (!filename || filename !== params.filename) {
    return NextResponse.json({ error: "Nombre inválido" }, { status: 400 });
  }

  let backendRes: Response;
  try {
    backendRes = await fetch(
      `${BACKEND}/manuales/imagenes/${encodeURIComponent(filename)}`,
      {
        headers: { Authorization: `Bearer ${token}` },
        // No redirigir automáticamente por seguridad.
        redirect: "manual",
      }
    );
  } catch {
    return NextResponse.json(
      { error: "Error conectando al backend" },
      { status: 502 }
    );
  }

  if (!backendRes.ok) {
    return NextResponse.json(
      { error: "Imagen no encontrada" },
      { status: backendRes.status }
    );
  }

  const contentType = backendRes.headers.get("content-type") ?? "image/png";

  // Solo devolver contenido si es realmente una imagen.
  if (!MIME_ALLOWED.has(contentType.split(";")[0].trim())) {
    return NextResponse.json({ error: "Tipo no permitido" }, { status: 415 });
  }

  const buffer = await backendRes.arrayBuffer();

  return new NextResponse(buffer, {
    status: 200,
    headers: {
      "Content-Type": contentType,
      // Caché pública moderada: las imágenes del manual no cambian frecuentemente.
      "Cache-Control": "public, max-age=300, stale-while-revalidate=60",
    },
  });
}
