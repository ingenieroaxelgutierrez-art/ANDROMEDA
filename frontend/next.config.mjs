/** @type {import('next').NextConfig} */
const nextConfig = {
  // Genera un bundle standalone para el Dockerfile de producción.
  // Incluye solo los archivos necesarios para ejecutar el servidor.
  output: "standalone",

  // Expone la URL de la API como variable de entorno pública.
  // En Docker se sobreescribe con NEXT_PUBLIC_API_URL=http://backend:8000
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000",
  },
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/manuales/imagenes/**",
      },
      {
        protocol: "http",
        hostname: "127.0.0.1",
        port: "8000",
        pathname: "/manuales/imagenes/**",
      },
      {
        protocol: "http",
        hostname: "backend",
        port: "8000",
        pathname: "/manuales/imagenes/**",
      },
    ],
  },
};

export default nextConfig;
