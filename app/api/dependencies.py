# ============================================================
# ANDROMEDA — app.api.dependencies
# Inyección de dependencias FastAPI.
#
# Dependencias disponibles:
#   get_bot()                 — Singleton global del bot
#   get_db()                  — Sesión SQLAlchemy (generador, se cierra sola)
#   get_conector_empresa()    — ConectorOdoo configurado por empresa_id
#   get_usuario_autenticado() — Cualquier usuario con JWT válido (Sprint 1)
#   get_solo_admin()          — Restringe a rol=admin (Sprint 1)
#   get_agente_o_admin()      — Agente o admin (Sprint 1)
# ============================================================

import threading
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

_bot_lock: threading.Lock = threading.Lock()
_bot: Optional[object] = None

# Pool de conectores Odoo por empresa_id (thread-safe)
_conector_pool: dict = {}
_pool_lock: threading.Lock = threading.Lock()


def get_bot() -> object:
    """
    Retorna la instancia singleton del bot ANDROMEDA.

    Patrón double-checked locking:
    - Primera llamada: instancia OdooAIProV5 (proceso pesado, una sola vez).
    - Llamadas siguientes: devuelve la instancia cacheada en O(1).

    En tests, sobreescribir vía:
        app.dependency_overrides[get_bot] = lambda: mock_bot
    """
    global _bot
    if _bot is None:
        with _bot_lock:
            if _bot is None:
                # Importación diferida: evita carga de PyTorch/spaCy al importar el módulo API.
                from views.interfaz_v5 import OdooAIProV5  # noqa: PLC0415
                _bot = OdooAIProV5()
    return _bot


def get_db() -> Generator[Session, None, None]:
    """
    Generador FastAPI para inyectar sesiones de BD SaaS.

    Uso en endpoints:
        def mi_endpoint(db: Session = Depends(get_db)):
            ...

    La sesión se crea antes del endpoint y se cierra (con commit o rollback)
    automáticamente al finalizar, incluso si hay excepción.
    """
    from models.db_saas import get_session, inicializar_db
    inicializar_db()
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_conector_empresa(empresa_id: str) -> object:
    """
    Retorna un ConectorOdoo configurado para la empresa indicada.

    Pool thread-safe con lazy instantiation por empresa_id.
    Las credenciales se cargan descifradas desde la BD SaaS.
    Si la empresa no existe o las credenciales son inválidas, retorna
    el conector con la configuración de entorno (default).

    Uso en endpoints que soportan multi-empresa:
        conector = get_conector_empresa(request.empresa_id)
    """
    if empresa_id in _conector_pool:
        return _conector_pool[empresa_id]

    with _pool_lock:
        if empresa_id in _conector_pool:
            return _conector_pool[empresa_id]

        try:
            from models.db_saas import get_session, Empresa, inicializar_db
            from models.conector_odoo import ConectorOdoo, ConfiguracionOdoo

            inicializar_db()
            session = get_session()
            try:
                empresa = session.query(Empresa).filter(
                    Empresa.id == empresa_id, Empresa.activa == True
                ).first()
                if empresa:
                    config = ConfiguracionOdoo(
                        url=empresa.odoo_url,
                        db=empresa.odoo_db,
                        usuario=empresa.odoo_usuario,
                        password=empresa.get_password(),
                    )
                    conector = ConectorOdoo(config=config, usuario=empresa_id)
                else:
                    conector = ConectorOdoo()
            finally:
                session.close()
        except Exception:
            from models.conector_odoo import ConectorOdoo
            conector = ConectorOdoo()

        _conector_pool[empresa_id] = conector
        return conector


# ── Dependencias de autenticación compartidas ─────────────────────────────────
# Fuente única de verdad: todos los routers importan desde aquí.
# Evita la duplicación de _solo_admin / _get_token_payload en cada router.

_bearer = HTTPBearer(auto_error=False)


def get_usuario_autenticado(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """
    Dependencia compartida — cualquier usuario con JWT válido.

    Extrae y valida el Bearer token del header Authorization.
    Retorna el payload completo del JWT (sub, email, rol, empresa_id, …).

    Uso:
        @router.get("/ruta")
        def mi_endpoint(ctx: dict = Depends(get_usuario_autenticado)):
            empresa_id = ctx["empresa_id"]
    """
    from app.api.auth.jwt_utils import decodificar_access_token

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


def get_solo_admin(
    payload: dict = Depends(get_usuario_autenticado),
) -> dict:
    """
    Dependencia — rol=admin exclusivamente.

    Construida sobre get_usuario_autenticado: primero valida el token,
    luego verifica el rol. HTTP 403 si el rol no es admin.
    """
    if payload.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a administradores",
        )
    return payload


def get_agente_o_admin(
    payload: dict = Depends(get_usuario_autenticado),
) -> dict:
    """
    Dependencia — rol=agente o rol=admin.

    Permite el acceso a agentes (Dirección/Gerencia) y admins.
    Roles de usuario (jefatura, tienda, etc.) reciben HTTP 403.
    """
    if payload.get("rol") not in ("admin", "agente"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a agentes y administradores",
        )
    return payload


def invalidar_pool_empresa(empresa_id: str) -> None:
    """
    Elimina la entrada del pool para forzar re-inicialización.
    Llamar cuando las credenciales de una empresa se actualicen.
    """
    with _pool_lock:
        _conector_pool.pop(empresa_id, None)


# ── Autenticación JWT (Fase 5) ───────────────────────────────────────────────

from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = None,
) -> dict:
    """
    Dependencia FastAPI: valida el Bearer token y retorna los claims del usuario.

    Uso en endpoints protegidos:
        @router.get("/recurso")
        def recurso(usuario=Depends(get_current_user)):
            ...

    Retorna dict con claves: sub, email, rol, empresa_id.
    Lanza HTTP 401 si el token falta, es inválido o ha expirado.
    """
    from app.api.auth.jwt_utils import decodificar_access_token

    token: Optional[str] = None
    if credentials:
        token = credentials.credentials

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


def require_rol(*roles: str):
    """
    Factoría de dependencias para guardar de roles.

    Uso:
        @router.delete("/recurso")
        def borrar(usuario=Depends(require_rol("admin"))):
            ...

    Lanza HTTP 403 si el usuario no tiene el rol requerido.
    """
    def _check(usuario: dict = Depends(get_current_user)) -> dict:
        if usuario.get("rol") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acción restringida — roles requeridos: {list(roles)}",
            )
        return usuario
    return _check

