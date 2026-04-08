# ============================================================
# ANDROMEDA — app.api.routers.configuracion
# CRUD de Empresas (Fase 4)
#
# Rutas:
#   GET    /configuracion           — lista empresas activas
#   POST   /configuracion           — crea empresa con credenciales cifradas
#   GET    /configuracion/{id}      — detalle de empresa (credenciales enmascaradas)
#   PUT    /configuracion/{id}      — actualiza empresa (re-cifra password si se pasa)
#   DELETE /configuracion/{id}      — soft-delete (marca activa=False)
#
# Seguridad: las credenciales NUNCA se devuelven en texto plano en GETs.
# ============================================================

import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.api.schemas import EmpresaCrear, EmpresaRespuesta, EmpresaActualizar
from models.db_saas import get_session, Empresa, inicializar_db

router = APIRouter(prefix="/configuracion", tags=["Configuración"])


def _empresa_o_404(session, empresa_id: str) -> Empresa:
    """Helper: devuelve la empresa activa o lanza 404."""
    empresa = (
        session.query(Empresa)
        .filter(Empresa.id == empresa_id, Empresa.activa == True)
        .first()
    )
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return empresa


@router.get("", response_model=List[EmpresaRespuesta], summary="Listar empresas")
def listar_empresas() -> List[EmpresaRespuesta]:
    """
    Lista todas las empresas activas.
    Las credenciales siempre están enmascaradas en la respuesta.
    """
    inicializar_db()
    session = get_session()
    try:
        empresas = session.query(Empresa).filter(Empresa.activa == True).all()
        return [EmpresaRespuesta(**e.to_dict()) for e in empresas]
    finally:
        session.close()


@router.post(
    "",
    response_model=EmpresaRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Crear empresa",
)
def crear_empresa(datos: EmpresaCrear) -> EmpresaRespuesta:
    """
    Crea una nueva empresa con credenciales Odoo/ERP cifradas.

    La contraseña viaja en texto plano en el body (sobre HTTPS en producción)
    y se cifra con Fernet antes de almacenarse. Nunca se persiste en texto plano.
    """
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
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando empresa: {exc}") from exc
    finally:
        session.close()


@router.get("/{empresa_id}", response_model=EmpresaRespuesta, summary="Obtener empresa")
def obtener_empresa(empresa_id: str) -> EmpresaRespuesta:
    """
    Retorna los datos de una empresa.
    Las credenciales siempre están enmascaradas.
    """
    inicializar_db()
    session = get_session()
    try:
        empresa = _empresa_o_404(session, empresa_id)
        return EmpresaRespuesta(**empresa.to_dict())
    finally:
        session.close()


@router.put("/{empresa_id}", response_model=EmpresaRespuesta, summary="Actualizar empresa")
def actualizar_empresa(empresa_id: str, datos: EmpresaActualizar) -> EmpresaRespuesta:
    """
    Actualiza datos de una empresa.
    Si se incluye ``odoo_password``, se re-cifra inmediatamente.
    Los campos no enviados (``None``) no se modifican.
    """
    inicializar_db()
    session = get_session()
    try:
        empresa = _empresa_o_404(session, empresa_id)

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


@router.delete(
    "/{empresa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar empresa",
)
def desactivar_empresa(empresa_id: str) -> None:
    """
    Realiza un soft-delete de la empresa (``activa = False``).
    Los datos y el historial se conservan para auditoría.
    """
    inicializar_db()
    session = get_session()
    try:
        empresa = _empresa_o_404(session, empresa_id)
        empresa.activa = False
        empresa.actualizado_en = datetime.now(timezone.utc)
        session.commit()
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error desactivando empresa: {exc}") from exc
    finally:
        session.close()
