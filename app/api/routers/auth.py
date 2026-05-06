# ============================================================
# ANDROMEDA — app.api.routers.auth
# Autenticación JWT (Fase 5 + Sprint 1 Seguridad)
#
# Rutas:
#   POST /auth/login     — autentica usuario, emite access + refresh token
#   POST /auth/refresh   — renueva access_token con refresh_token (cookie)
#   GET  /auth/me        — perfil del usuario autenticado
#   POST /auth/usuarios  — crea usuario (solo admin)
#   POST /auth/logout    — limpia cookie httpOnly + logout stateless
#
# Diseño:
#   - access_token  : 15 min en body Authorization
#   - refresh_token : 7 días en httpOnly cookie (Path=/auth) — NO en body
#   - HS256 firmado con SECRET_KEY
#   - COOKIE_SECURE=true en producción (HTTPS)
# ============================================================

import os
import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.api.auth.jwt_utils import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    crear_access_token,
    crear_refresh_token,
    decodificar_refresh_token,
    decodificar_access_token,
)
from app.api.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UsuarioActual,
    UsuarioCrearRequest,
    PerfilActualizar,
)

_COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
_COOKIE_MAX_AGE: int = REFRESH_TOKEN_EXPIRE_DAYS * 86400  # segundos

router = APIRouter(prefix="/auth", tags=["Autenticación"])

_bearer = HTTPBearer(auto_error=False)


# ── Helpers privados ──────────────────────────────────────────────────────────

def _usuario_por_email(email: str):
    from models.db_saas import get_session, Usuario, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        return (
            session.query(Usuario)
            .filter(Usuario.email == email, Usuario.activo == True)
            .first()
        )
    finally:
        session.close()


def _usuario_por_id(usuario_id: str):
    from models.db_saas import get_session, Usuario, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        return (
            session.query(Usuario)
            .filter(Usuario.id == usuario_id, Usuario.activo == True)
            .first()
        )
    finally:
        session.close()


def _get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """Dependencia interna: extrae y valida el JWT del header Authorization."""
    token = credentials.credentials if credentials else None
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado — se requiere Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decodificar_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# ── Endpoints públicos ────────────────────────────────────────────────────────

@router.post("/login", summary="Iniciar sesión")
def login(datos: LoginRequest, response: Response) -> TokenResponse:
    """
    Autentica usuario con email + contraseña.

    - ``access_token`` (body): 15 min con claims usuario/rol/empresa.
    - ``refresh_token`` (httpOnly cookie): 7 días, Path=/auth.
      Al ser httpOnly, JavaScript no puede leerlo — protección XSS.
    - Verificación timing-safe con bcrypt (passlib).
    - HTTP 401 genérico — no revela si el email existe.
    """
    usuario = _usuario_por_email(datos.email)
    _no_autorizado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not usuario or not usuario.check_password(datos.password):
        raise _no_autorizado

    refresh_token = crear_refresh_token(usuario_id=usuario.id)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=_COOKIE_SECURE,
        max_age=_COOKIE_MAX_AGE,
        path="/auth",
    )

    return TokenResponse(
        access_token=crear_access_token(
            usuario_id=usuario.id,
            email=usuario.email,
            rol=usuario.rol,
            empresa_id=usuario.empresa_id,
            sub_rol=usuario.sub_rol,
            area_id=usuario.area_id,
        ),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", summary="Renovar access token")
def refresh(request: Request, response: Response, datos: RefreshRequest = None) -> TokenResponse:
    """
    Renueva el ``access_token`` usando el ``refresh_token``.

    Lee el token desde la cookie httpOnly ``refresh_token`` (path=/auth).
    Si no está en cookie, acepta el campo del body por compatibilidad.
    Verifica que el usuario siga activo en BD antes de emitir el nuevo token.
    Emite una nueva cookie con el refresh_token rotado.
    """
    # Cookie httpOnly es la fuente autoritativa; body es fallback de compatibilidad
    token = request.cookies.get("refresh_token")
    if not token and datos and datos.refresh_token:
        token = datos.refresh_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario_id = decodificar_refresh_token(token)
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    usuario = _usuario_por_id(usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Rotar el refresh_token (emitir uno nuevo) para limitar la ventana de abuso
    nuevo_refresh = crear_refresh_token(usuario_id=usuario.id)
    response.set_cookie(
        key="refresh_token",
        value=nuevo_refresh,
        httponly=True,
        samesite="lax",
        secure=_COOKIE_SECURE,
        max_age=_COOKIE_MAX_AGE,
        path="/auth",
    )

    return TokenResponse(
        access_token=crear_access_token(
            usuario_id=usuario.id,
            email=usuario.email,
            rol=usuario.rol,
            empresa_id=usuario.empresa_id,
            sub_rol=usuario.sub_rol,
            area_id=usuario.area_id,
        ),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Cerrar sesión")
def logout(response: Response) -> None:
    """
    Logout: elimina la cookie httpOnly refresh_token del navegador.
    El cliente también debe descartar el access_token del lado cliente.
    """
    response.delete_cookie(key="refresh_token", path="/auth")
    return None


# ── Endpoints protegidos ──────────────────────────────────────────────────────

@router.get("/me", summary="Perfil del usuario autenticado")
def me(payload: Annotated[dict, Depends(_get_token_payload)]) -> UsuarioActual:
    """Retorna el perfil del usuario desde el JWT. Requiere Bearer token."""
    usuario = _usuario_por_id(payload["sub"])
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return UsuarioActual(**usuario.to_dict())


@router.post(
    "/usuarios",
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario (solo admin)",
    responses={
        404: {"description": "Empresa no encontrada"},
        409: {"description": "Ya existe un usuario con ese email"},
    },
)
def crear_usuario(
    datos: UsuarioCrearRequest,
    payload: Annotated[dict, Depends(_get_token_payload)],
) -> UsuarioActual:
    """Crea un nuevo usuario. Solo rol ``admin`` puede invocar este endpoint."""
    if payload.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear usuarios",
        )

    from models.db_saas import get_session, Usuario, Empresa, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        empresa = session.query(Empresa).filter(
            Empresa.id == datos.empresa_id, Empresa.activa == True
        ).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")

        if session.query(Usuario).filter(Usuario.email == datos.email).first():
            raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")

        nuevo = Usuario(
            id=str(uuid.uuid4()),
            nombre=datos.nombre,
            email=datos.email,
            empresa_id=datos.empresa_id,
            rol=datos.rol,
            sub_rol=datos.sub_rol,
            area_id=datos.area_id,
            activo=True,
            creado_en=datetime.now(timezone.utc),
        )
        nuevo.set_password(datos.password)
        session.add(nuevo)
        session.commit()
        session.refresh(nuevo)
        return UsuarioActual(**nuevo.to_dict())
    finally:
        session.close()


@router.put("/perfil", summary="Actualizar perfil propio")
def actualizar_perfil(
    datos: PerfilActualizar,
    payload: Annotated[dict, Depends(_get_token_payload)],
) -> UsuarioActual:
    """Permite al usuario autenticado cambiar su nombre, email o contraseña."""
    from models.db_saas import get_session, Usuario, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        usuario = session.query(Usuario).filter(
            Usuario.id == payload["sub"], Usuario.activo == True
        ).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if datos.nombre is not None:
            usuario.nombre = datos.nombre

        if datos.email is not None:
            if session.query(Usuario).filter(
                Usuario.email == datos.email, Usuario.id != usuario.id
            ).first():
                raise HTTPException(status_code=409, detail="Email ya en uso")
            usuario.email = datos.email

        if datos.password_nuevo is not None:
            if not datos.password_actual or not usuario.check_password(datos.password_actual):
                raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
            usuario.set_password(datos.password_nuevo)

        session.commit()
        session.refresh(usuario)
        return UsuarioActual(**usuario.to_dict())
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando perfil: {exc}") from exc
    finally:
        session.close()
