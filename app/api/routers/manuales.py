# ============================================================
# ANDROMEDA — app.api.routers.manuales
# GET /manuales/imagenes/{filename} — Sirve imágenes del manual
# ============================================================

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/manuales", tags=["manuales"])

_IMAGENES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "manuales" / "imagenes"

_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg+xml": "image/svg+xml",
}


@router.get("/imagenes/{filename}", summary="Obtener imagen del manual")
def get_imagen(filename: str) -> FileResponse:
    """Sirve una imagen del manual almacenada en data/manuales/imagenes/."""
    # Sanitizar: no permitir traversal de directorios
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    ruta = _IMAGENES_DIR / safe_name
    if not ruta.exists() or not ruta.is_file():
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    extension = "".join(Path(safe_name).suffixes).lower()
    media_type = _MIME.get(extension, "image/png")

    return FileResponse(str(ruta), media_type=media_type)
