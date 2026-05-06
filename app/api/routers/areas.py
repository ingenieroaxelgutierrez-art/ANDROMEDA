# ============================================================
# ANDROMEDA — app.api.routers.areas
# Sprint 2 — Modelo de Datos: Gestión de Áreas
#
# Rutas:
#   GET  /admin/areas               — listar áreas (con filtros)
#   POST /admin/areas               — crear área
#   GET  /admin/areas/{area_id}     — obtener área por ID
#   PUT  /admin/areas/{area_id}     — actualizar área
#   DELETE /admin/areas/{area_id}   — desactivar área (soft delete)
#
# Seguridad: solo admin (Depends(_solo_admin) de admin.py).
# ============================================================

import uuid
from datetime import datetime, timezone
from typing import Annotated, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, status

from app.api.routers.admin import _solo_admin
from app.api.schemas import AreaCrear, AreaRespuesta

router = APIRouter(prefix="/admin/areas", tags=["Áreas"])


# ── CRUD de Áreas ─────────────────────────────────────────────────────────────

@router.get("", summary="Listar áreas")
def listar_areas(
    empresa_id: Optional[str] = Query(default=None, description="Filtrar por empresa"),
    activa: Optional[bool] = Query(default=None, description="Filtrar por estado activa/inactiva"),
    _: Annotated[dict, Depends(_solo_admin)] = None,
) -> List[AreaRespuesta]:
    """Retorna todas las áreas. Admite filtros por empresa y estado."""
    from models.db_saas import get_session, Area, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        q = session.query(Area)
        if empresa_id:
            q = q.filter(Area.empresa_id == empresa_id)
        if activa is not None:
            q = q.filter(Area.activa == activa)
        areas = q.order_by(Area.nombre).all()
        return [AreaRespuesta(**a.to_dict()) for a in areas]
    finally:
        session.close()


@router.post("", status_code=status.HTTP_201_CREATED, summary="Crear área")
def crear_area(
    datos: AreaCrear,
    _: Annotated[dict, Depends(_solo_admin)] = None,
) -> AreaRespuesta:
    """Crea un área nueva para una empresa. Solo admin."""
    from models.db_saas import get_session, Area, Empresa, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        empresa = session.query(Empresa).filter(
            Empresa.id == datos.empresa_id, Empresa.activa == True
        ).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")

        # Validar unicidad de codigo dentro de la empresa
        if datos.codigo:
            existe = session.query(Area).filter(
                Area.empresa_id == datos.empresa_id,
                Area.codigo == datos.codigo,
            ).first()
            if existe:
                raise HTTPException(
                    status_code=409,
                    detail=f"Ya existe un área con código '{datos.codigo}' en esa empresa",
                )

        area = Area(
            id=str(uuid.uuid4()),
            empresa_id=datos.empresa_id,
            nombre=datos.nombre,
            codigo=datos.codigo,
            tipo=datos.tipo,
            activa=datos.activa,
            creado_en=datetime.now(timezone.utc),
        )
        session.add(area)
        session.commit()
        session.refresh(area)
        return AreaRespuesta(**area.to_dict())
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando área: {exc}") from exc
    finally:
        session.close()


@router.get("/{area_id}", summary="Obtener área por ID")
def obtener_area(
    area_id: str,
    _: Annotated[dict, Depends(_solo_admin)] = None,
) -> AreaRespuesta:
    """Retorna un área por su ID."""
    from models.db_saas import get_session, Area, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        area = session.query(Area).filter(Area.id == area_id).first()
        if not area:
            raise HTTPException(status_code=404, detail="Área no encontrada")
        return AreaRespuesta(**area.to_dict())
    finally:
        session.close()


@router.put("/{area_id}", summary="Actualizar área")
def actualizar_area(
    area_id: str,
    datos: AreaCrear,
    _: Annotated[dict, Depends(_solo_admin)] = None,
) -> AreaRespuesta:
    """Actualiza todos los campos de un área existente."""
    from models.db_saas import get_session, Area, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        area = session.query(Area).filter(Area.id == area_id).first()
        if not area:
            raise HTTPException(status_code=404, detail="Área no encontrada")

        # Validar unicidad del código si cambió
        if datos.codigo and datos.codigo != area.codigo:
            existe = session.query(Area).filter(
                Area.empresa_id == datos.empresa_id,
                Area.codigo == datos.codigo,
                Area.id != area_id,
            ).first()
            if existe:
                raise HTTPException(
                    status_code=409,
                    detail=f"Ya existe un área con código '{datos.codigo}' en esa empresa",
                )

        area.nombre = datos.nombre
        area.codigo = datos.codigo
        area.tipo = datos.tipo
        area.activa = datos.activa
        session.commit()
        session.refresh(area)
        return AreaRespuesta(**area.to_dict())
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando área: {exc}") from exc
    finally:
        session.close()


@router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desactivar área")
def desactivar_area(
    area_id: str,
    _: Annotated[dict, Depends(_solo_admin)] = None,
) -> None:
    """Desactiva (soft delete) un área. Los usuarios asignados quedan sin área."""
    from models.db_saas import get_session, Area, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        area = session.query(Area).filter(Area.id == area_id).first()
        if not area:
            raise HTTPException(status_code=404, detail="Área no encontrada")
        if not area.activa:
            raise HTTPException(status_code=409, detail="El área ya está inactiva")
        area.activa = False
        session.commit()
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error desactivando área: {exc}") from exc
    finally:
        session.close()
