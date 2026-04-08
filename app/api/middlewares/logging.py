# ============================================================
# ANDROMEDA — app.api.middlewares.logging
# Middleware HTTP: registra método, path, status y tiempo de cada request.
# ============================================================

import time
import logging
from fastapi import Request
from starlette.responses import Response

_logger = logging.getLogger("andromeda.api.requests")


async def log_requests_middleware(request: Request, call_next) -> Response:
    """
    Middleware que registra cada request HTTP entrante.

    Formato de log:
        METHOD /path → STATUS_CODE (XX.Xms)

    No modifica headers ni body; únicamente observa.
    """
    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    _logger.info(
        "%s %s → %d (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response
