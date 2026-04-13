# ============================================================
# ANDROMEDA — app.api.routers.agente
# Rutas para el rol agente (profesional)
#
# GET /agente/empresa         — datos de la empresa propia
# PUT /agente/empresa         — actualizar empresa propia (URL, DB, credenciales)
# GET /agente/metricas        — metricas de la empresa propia
# ============================================================

from datetime import datetime, timezone, timedelta
from typing import Optional, Annotated

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.api.auth.jwt_utils import decodificar_access_token
from app.api.schemas import EmpresaRespuesta, EmpresaActualizar, MetricasSaaS
from services.logging_saas import obtener_metricas

router = APIRouter(prefix="/agente", tags=["Agente"])
_bearer = HTTPBearer(auto_error=False)


# ── Dependencia: agente o admin ───────────────────────────────────────────────

def _req_agente(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    token = credentials.credentials if credentials else None
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decodificar_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("rol") not in ("admin", "agente"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol agente o admin",
        )
    return payload


# ── Empresa propia ────────────────────────────────────────────────────────────

@router.get("/empresa", response_model=EmpresaRespuesta, summary="Datos de la empresa propia")
def get_empresa_propia(payload: Annotated[dict, Depends(_req_agente)]) -> EmpresaRespuesta:
    empresa_id = payload.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="Sin empresa asignada")
    from models.db_saas import get_session, Empresa, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        empresa = session.query(Empresa).filter(Empresa.id == empresa_id, Empresa.activa == True).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        return EmpresaRespuesta(**empresa.to_dict())
    finally:
        session.close()


@router.put("/empresa", response_model=EmpresaRespuesta, summary="Actualizar empresa propia")
def put_empresa_propia(
    datos: EmpresaActualizar,
    payload: Annotated[dict, Depends(_req_agente)],
) -> EmpresaRespuesta:
    empresa_id = payload.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=400, detail="Sin empresa asignada")
    from models.db_saas import get_session, Empresa, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        empresa = session.query(Empresa).filter(Empresa.id == empresa_id, Empresa.activa == True).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        if datos.nombre is not None:
            empresa.nombre = datos.nombre
        if datos.odoo_url is not None:
            empresa.odoo_url = datos.odoo_url
        if datos.odoo_db is not None:
            empresa.odoo_db = datos.odoo_db
        if datos.odoo_usuario is not None:
            empresa.odoo_usuario = datos.odoo_usuario
        if datos.odoo_password is not None:
            empresa.set_password(datos.odoo_password)
        if datos.version_odoo is not None:
            empresa.version_odoo = datos.version_odoo
        if datos.tipo_erp is not None:
            empresa.tipo_erp = datos.tipo_erp
        empresa.actualizado_en = datetime.now(timezone.utc)
        session.commit()
        session.refresh(empresa)
        return EmpresaRespuesta(**empresa.to_dict())
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando empresa: {exc}") from exc
    finally:
        session.close()


# ── Metricas de la empresa ────────────────────────────────────────────────────

@router.get("/metricas", response_model=MetricasSaaS, summary="Metricas de la empresa propia")
def get_metricas_empresa(
    payload: Annotated[dict, Depends(_req_agente)],
    dias: int = Query(default=30, ge=1, le=365),
) -> MetricasSaaS:
    empresa_id = payload.get("empresa_id")
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    hasta = datetime.now(timezone.utc)
    datos = obtener_metricas(empresa_id=empresa_id, desde=desde, hasta=hasta)
    return MetricasSaaS(**datos)
