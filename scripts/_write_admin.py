"""Script temporal que genera app/api/routers/admin.py con todas las rutas."""
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(BASE, "app", "api", "routers", "admin.py")

CODE = """\
# ============================================================
# ANDROMEDA — app.api.routers.admin
# Generado por scripts/_write_admin.py
# ============================================================

import uuid
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Annotated

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.api.auth.jwt_utils import decodificar_access_token
from app.api.schemas import (
    MetricasSaaS,
    EmpresaRespuesta,
    EmpresaCrear,
    EmpresaActualizar,
    UsuarioRespuesta,
    UsuarioCrearRequest,
    UsuarioActualizar,
    DashboardAdmin,
    ConfigSistema,
)
from services.logging_saas import obtener_metricas

router = APIRouter(prefix="/admin", tags=["Administracion"])
_bearer = HTTPBearer(auto_error=False)

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "data", "config_sistema.json"
)


# ── Dependencia: solo admin ───────────────────────────────────────────────────

def _solo_admin(
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
    if payload.get("rol") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    return payload


# ── Dashboard ──────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardAdmin, summary="Dashboard KPIs")
def dashboard(payload: Annotated[dict, Depends(_solo_admin)]) -> DashboardAdmin:
    from models.db_saas import get_session, Empresa, Usuario, SesionLog, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        empresas_total = session.query(Empresa).count()
        empresas_activas_cnt = session.query(Empresa).filter(Empresa.activa == True).count()
        usuarios_total = session.query(Usuario).count()
        usuarios_activos_cnt = session.query(Usuario).filter(Usuario.activo == True).count()
        hoy = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        hace_30 = datetime.now(timezone.utc) - timedelta(days=30)
        consultas_hoy = session.query(SesionLog).filter(SesionLog.timestamp >= hoy).count()
        consultas_mes = session.query(SesionLog).filter(SesionLog.timestamp >= hace_30).count()
        errores_mes = session.query(SesionLog).filter(
            SesionLog.timestamp >= hace_30, SesionLog.resultado == "error"
        ).count()
        tasa_error = round(errores_mes / consultas_mes * 100, 1) if consultas_mes else 0.0
        return DashboardAdmin(
            empresas_total=empresas_total,
            empresas_activas=empresas_activas_cnt,
            usuarios_total=usuarios_total,
            usuarios_activos=usuarios_activos_cnt,
            consultas_hoy=consultas_hoy,
            consultas_mes=consultas_mes,
            tasa_error=tasa_error,
            uptime_pct=100.0,
        )
    finally:
        session.close()


# ── Metricas ───────────────────────────────────────────────────────────────────

@router.get("/metricas", response_model=MetricasSaaS, summary="Metricas globales SaaS")
def metricas_globales(
    payload: Annotated[dict, Depends(_solo_admin)],
    empresa_id: Optional[str] = Query(default=None),
    dias: int = Query(default=30, ge=1, le=365),
) -> MetricasSaaS:
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    hasta = datetime.now(timezone.utc)
    datos = obtener_metricas(empresa_id=empresa_id, desde=desde, hasta=hasta)
    return MetricasSaaS(**datos)


@router.get("/metricas/{empresa_id}", response_model=MetricasSaaS, summary="Metricas por empresa")
def metricas_empresa_ruta(
    empresa_id: str,
    payload: Annotated[dict, Depends(_solo_admin)],
    dias: int = Query(default=30, ge=1, le=365),
) -> MetricasSaaS:
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    hasta = datetime.now(timezone.utc)
    datos = obtener_metricas(empresa_id=empresa_id, desde=desde, hasta=hasta)
    return MetricasSaaS(**datos)


# ── CRUD Empresas ──────────────────────────────────────────────────────────────

@router.get("/empresas", response_model=List[EmpresaRespuesta], summary="Listar empresas")
def listar_empresas(
    payload: Annotated[dict, Depends(_solo_admin)],
    solo_activas: bool = Query(default=False),
) -> List[EmpresaRespuesta]:
    from models.db_saas import get_session, Empresa, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        q = session.query(Empresa)
        if solo_activas:
            q = q.filter(Empresa.activa == True)
        return [EmpresaRespuesta(**e.to_dict()) for e in q.all()]
    finally:
        session.close()


@router.post("/empresas", response_model=EmpresaRespuesta, status_code=201, summary="Crear empresa")
def crear_empresa_admin(datos: EmpresaCrear, payload: Annotated[dict, Depends(_solo_admin)]) -> EmpresaRespuesta:
    from models.db_saas import get_session, Empresa, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        empresa = Empresa(
            id=str(uuid.uuid4()),
            nombre=datos.nombre,
            odoo_url=datos.odoo_url,
            odoo_db=datos.odoo_db,
            odoo_usuario=datos.odoo_usuario,
            version_odoo=datos.version_odoo,
            tipo_erp=datos.tipo_erp,
            activa=True,
            creado_en=datetime.now(timezone.utc),
            actualizado_en=datetime.now(timezone.utc),
        )
        empresa.set_password(datos.odoo_password)
        session.add(empresa)
        session.commit()
        session.refresh(empresa)
        return EmpresaRespuesta(**empresa.to_dict())
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando empresa: {exc}") from exc
    finally:
        session.close()


@router.put("/empresas/{empresa_id}", response_model=EmpresaRespuesta, summary="Actualizar empresa")
def actualizar_empresa_admin(
    empresa_id: str,
    datos: EmpresaActualizar,
    payload: Annotated[dict, Depends(_solo_admin)],
) -> EmpresaRespuesta:
    from models.db_saas import get_session, Empresa, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        empresa = session.query(Empresa).filter(Empresa.id == empresa_id).first()
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
        raise HTTPException(status_code=500, detail=f"Error actualizando: {exc}") from exc
    finally:
        session.close()


@router.delete("/empresas/{empresa_id}", status_code=204, summary="Soft delete empresa")
def eliminar_empresa_admin(empresa_id: str, payload: Annotated[dict, Depends(_solo_admin)]) -> None:
    from models.db_saas import get_session, Empresa, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        empresa = session.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        empresa.activa = False
        empresa.actualizado_en = datetime.now(timezone.utc)
        session.commit()
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando: {exc}") from exc
    finally:
        session.close()


# ── CRUD Usuarios ──────────────────────────────────────────────────────────────

def _usuario_a_respuesta(u, session) -> UsuarioRespuesta:
    from models.db_saas import Empresa
    empresa_nombre = None
    if u.empresa_id:
        emp = session.query(Empresa).filter(Empresa.id == u.empresa_id).first()
        empresa_nombre = emp.nombre if emp else None
    return UsuarioRespuesta(
        id=u.id,
        nombre=u.nombre,
        email=u.email,
        rol=u.rol,
        empresa_id=u.empresa_id,
        empresa_nombre=empresa_nombre,
        activo=u.activo,
        creado_en=u.creado_en.isoformat() if u.creado_en else None,
    )


@router.get("/usuarios", response_model=List[UsuarioRespuesta], summary="Listar usuarios")
def listar_usuarios(payload: Annotated[dict, Depends(_solo_admin)]) -> List[UsuarioRespuesta]:
    from models.db_saas import get_session, Usuario, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        return [_usuario_a_respuesta(u, session) for u in session.query(Usuario).all()]
    finally:
        session.close()


@router.post("/usuarios", response_model=UsuarioRespuesta, status_code=201, summary="Crear usuario")
def crear_usuario_admin(datos: UsuarioCrearRequest, payload: Annotated[dict, Depends(_solo_admin)]) -> UsuarioRespuesta:
    from models.db_saas import get_session, Usuario, Empresa, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        if datos.empresa_id:
            if not session.query(Empresa).filter(Empresa.id == datos.empresa_id, Empresa.activa == True).first():
                raise HTTPException(status_code=404, detail="Empresa no encontrada")
        if session.query(Usuario).filter(Usuario.email == datos.email).first():
            raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")
        nuevo = Usuario(
            id=str(uuid.uuid4()),
            nombre=datos.nombre,
            email=datos.email,
            empresa_id=datos.empresa_id,
            rol=datos.rol,
            activo=True,
            creado_en=datetime.now(timezone.utc),
        )
        nuevo.set_password(datos.password)
        session.add(nuevo)
        session.commit()
        session.refresh(nuevo)
        return _usuario_a_respuesta(nuevo, session)
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando usuario: {exc}") from exc
    finally:
        session.close()


@router.put("/usuarios/{usuario_id}", response_model=UsuarioRespuesta, summary="Actualizar usuario")
def actualizar_usuario_admin(
    usuario_id: str,
    datos: UsuarioActualizar,
    payload: Annotated[dict, Depends(_solo_admin)],
) -> UsuarioRespuesta:
    from models.db_saas import get_session, Usuario, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        usuario = session.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if datos.nombre is not None:
            usuario.nombre = datos.nombre
        if datos.email is not None:
            if session.query(Usuario).filter(Usuario.email == datos.email, Usuario.id != usuario_id).first():
                raise HTTPException(status_code=409, detail="Email ya en uso")
            usuario.email = datos.email
        if datos.password is not None:
            usuario.set_password(datos.password)
        if datos.rol is not None:
            usuario.rol = datos.rol
        if datos.empresa_id is not None:
            usuario.empresa_id = datos.empresa_id
        if datos.activo is not None:
            usuario.activo = datos.activo
        session.commit()
        session.refresh(usuario)
        return _usuario_a_respuesta(usuario, session)
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando usuario: {exc}") from exc
    finally:
        session.close()


@router.delete("/usuarios/{usuario_id}", status_code=204, summary="Soft delete usuario")
def eliminar_usuario_admin(usuario_id: str, payload: Annotated[dict, Depends(_solo_admin)]) -> None:
    from models.db_saas import get_session, Usuario, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        usuario = session.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        usuario.activo = False
        session.commit()
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando usuario: {exc}") from exc
    finally:
        session.close()


# ── Configuracion Sistema ──────────────────────────────────────────────────────

def _leer_config() -> dict:
    defaults = {
        "llm_provider": "ollama",
        "llm_model": "llama3",
        "max_tokens": 2048,
        "temperatura": 0.3,
        "odoo_timeout_seg": 30,
        "max_reintentos": 3,
        "session_ttl_min": 60,
        "log_level": "INFO",
    }
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                defaults.update(json.load(f))
        except Exception:
            pass
    return defaults


@router.get("/configuracion-sistema", response_model=ConfigSistema, summary="Config del sistema")
def get_config_sistema(payload: Annotated[dict, Depends(_solo_admin)]) -> ConfigSistema:
    return ConfigSistema(**_leer_config())


@router.put("/configuracion-sistema", response_model=ConfigSistema, summary="Actualizar config sistema")
def put_config_sistema(datos: ConfigSistema, payload: Annotated[dict, Depends(_solo_admin)]) -> ConfigSistema:
    os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(datos.model_dump(), f, indent=2, ensure_ascii=False)
    return datos
"""

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(CODE)
print(f"Written {len(CODE)} chars to {TARGET}")
