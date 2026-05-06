# ============================================================
# ANDROMEDA — app.api.auth.jwt_utils
# Utilidades JWT — Fase 5
#
# Tokens:
#   access_token  — corta duración (15 min), lleva Claims del usuario
#   refresh_token — larga duración (7 días), solo lleva sub + tipo
#
# Firma: HS256 con SECRET_KEY del .env
# Librería: python-jose[cryptography]
# ============================================================

from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt

# ── Configuración ────────────────────────────────────────────────────────────

_SECRET_KEY: str = os.getenv("SECRET_KEY", "andromeda-default-key-change-in-production")
_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

_TOKEN_TYPE_ACCESS = "access"
_TOKEN_TYPE_REFRESH = "refresh"


# ── Creación de tokens ────────────────────────────────────────────────────────

def crear_access_token(
    usuario_id: str,
    email: str,
    rol: str,
    empresa_id: str,
    sub_rol: Optional[str] = None,
    area_id: Optional[str] = None,
) -> str:
    """
    Genera un JWT de acceso de corta duración (15 min por defecto).

    Claims incluidos:
        sub         — usuario_id (sujeto estándar JWT)
        email       — email del usuario
        rol         — admin | agente | usuario
        empresa_id  — empresa a la que pertenece el usuario
        sub_rol     — perfil operativo dentro del rol (Sprint 2, opcional)
        area_id     — área a la que pertenece (Sprint 2, opcional)
        tipo        — "access"
        exp         — tiempo de expiración (UNIX timestamp)
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": usuario_id,
        "email": email,
        "rol": rol,
        "empresa_id": empresa_id,
        "tipo": _TOKEN_TYPE_ACCESS,
        "exp": expire,
    }
    # Incluir claims opcionales solo cuando tienen valor (evita contaminación del JWT)
    if sub_rol is not None:
        payload["sub_rol"] = sub_rol
    if area_id is not None:
        payload["area_id"] = area_id
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def crear_refresh_token(usuario_id: str) -> str:
    """
    Genera un JWT de refresco de larga duración (7 días por defecto).

    Solo incluye el claim mínimo necesario para identificar al usuario.
    El backend valida que el usuario siga activo antes de emitir un nuevo access_token.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload: Dict[str, Any] = {
        "sub": usuario_id,
        "tipo": _TOKEN_TYPE_REFRESH,
        "exp": expire,
    }
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


# ── Decodificación y validación ───────────────────────────────────────────────

def decodificar_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica y valida un access_token.

    Returns:
        Dict con los claims si el token es válido y no ha expirado.
        None si el token es inválido, expirado o no es de tipo "access".
    """
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        if payload.get("tipo") != _TOKEN_TYPE_ACCESS:
            return None
        return payload
    except JWTError:
        return None


def decodificar_refresh_token(token: str) -> Optional[str]:
    """
    Decodifica y valida un refresh_token.

    Returns:
        usuario_id (str) si el token es válido.
        None si el token es inválido, expirado o no es de tipo "refresh".
    """
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        if payload.get("tipo") != _TOKEN_TYPE_REFRESH:
            return None
        return payload.get("sub")
    except JWTError:
        return None
