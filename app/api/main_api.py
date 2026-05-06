# ============================================================
# ANDROMEDA — app.api.main_api
# Punto de entrada de la API REST (FastAPI).
#
# Ejecutar en desarrollo:
#   uvicorn app.api.main_api:app --host 127.0.0.1 --port 8000 --reload
#
# Ejecutar en producción:
#   uvicorn app.api.main_api:app --host 0.0.0.0 --port 8000 --workers 4
# ============================================================

import os
import sys

# Garantizar que la raíz del proyecto esté en sys.path,
# independientemente del directorio de trabajo al invocar uvicorn.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Config
from app.api.routers import auth, chat, reportes, salud, configuracion, admin, manuales, agente, areas
from app.api.middlewares.logging import log_requests_middleware


# ── Lifespan: reemplaza el deprecado @app.on_event("startup") ───────────────
@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    from models.db_saas import inicializar_db
    from services.logging_saas import rotar_logs_antiguos
    inicializar_db()
    rotar_logs_antiguos()   # limpia logs >30 días al arrancar
    yield


# ── Instancia principal ──────────────────────────────────────────────────────
app = FastAPI(
    title=Config.NOMBRE,
    description=Config.NOMBRE_COMPLETO,
    version=Config.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middlewares ──────────────────────────────────────────────────────────────
# CORS: orígenes permitidos desde ALLOWED_ORIGINS (separados por coma).
# En desarrollo se usa el default localhost:3000.
# En producción: ALLOWED_ORIGINS=https://mi-dominio.com,https://app.mi-dominio.com
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Se registra antes que los routers para capturar todos los requests.
app.middleware("http")(log_requests_middleware)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)            # POST /auth/login  POST /auth/refresh  GET /auth/me  PUT /auth/perfil
app.include_router(salud.router)           # GET /health  GET /status
app.include_router(chat.router)            # POST /chat
app.include_router(reportes.router)        # GET /reportes  POST /reportes/generar
app.include_router(configuracion.router)   # GET|POST|PUT|DELETE /configuracion
app.include_router(admin.router)           # GET /admin/dashboard  /empresas  /usuarios  /metricas  /configuracion-sistema
app.include_router(agente.router)          # GET|PUT /agente/empresa  GET /agente/metricas
app.include_router(manuales.router)        # GET /manuales/imagenes/{filename}
app.include_router(areas.router)           # GET|POST|PUT|DELETE /admin/areas  (Sprint 2)

