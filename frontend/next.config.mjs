/** @type {import('next').NextConfig} */
const nextConfig = {
  // Expone la URL de la API como variable de entorno pública.
  // Sobreescribir con NEXT_PUBLIC_API_URL en .env.local en producción.
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000",
  },
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "127.0.0.1",
        port: "8000",
        pathname: "/manuales/imagenes/**",
      },
    ],
  },
};

export default nextConfig;
