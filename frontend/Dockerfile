# ============================================================
# ANDROMEDA — Frontend (Next.js 14 + TypeScript)
# Imagen de desarrollo: código montado como volumen (hot reload)
# ============================================================

FROM node:20-alpine

WORKDIR /app

# Instalar dependencias (capa cacheada)
COPY package.json package-lock.json* ./
RUN npm ci

# En desarrollo el código se monta como volumen (no se copia aquí)
# En producción (compose.prod.yml) se hace COPY . .

EXPOSE 3000

# Next.js dev server con hot reload
CMD ["npm", "run", "dev"]
