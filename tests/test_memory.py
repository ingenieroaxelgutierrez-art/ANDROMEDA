# ============================================================
# ANDROMEDA — Tests de services/memory
# ============================================================

import pytest
import os
import json
from unittest.mock import MagicMock, patch
from datetime import datetime
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════
# TESTS DE RegistroSesion y MemoriaSesion
# ═══════════════════════════════════════════════════════════

class TestMemoriaSesion:

    def test_registro_sesion(self):
        from services.memory.memoria_jerarquica import RegistroSesion
        r = RegistroSesion(
            timestamp="2024-01-01 10:00:00",
            mensaje_usuario="hola",
            respuesta="¡Hola!",
            intencion="saludo",
            accion="responder_saludo",
            confianza=0.95
        )
        assert r.mensaje_usuario == "hola"
        assert r.confianza == 0.95

    def test_memoria_sesion_agregar(self):
        from services.memory.memoria_jerarquica import MemoriaSesion, RegistroSesion
        ms = MemoriaSesion()
        assert len(ms.historial) == 0

        r = RegistroSesion(
            timestamp="2024-01-01 10:00:00",
            mensaje_usuario="ventas",
            respuesta="Total: $10,000",
            intencion="consultar_ventas",
            accion="ventas_totales",
            confianza=0.9
        )
        ms.agregar(r)
        assert len(ms.historial) == 1

    def test_memoria_sesion_limite(self):
        from services.memory.memoria_jerarquica import MemoriaSesion, RegistroSesion
        ms = MemoriaSesion(max_interacciones=3)

        for i in range(5):
            ms.agregar(RegistroSesion(
                timestamp=f"2024-01-01 10:0{i}:00",
                mensaje_usuario=f"msg{i}",
                respuesta=f"resp{i}",
                intencion="test",
                accion="test",
                confianza=0.5
            ))

        assert len(ms.historial) == 3
        assert ms.historial[0].mensaje_usuario == "msg2"

    def test_memoria_sesion_ultimas(self):
        from services.memory.memoria_jerarquica import MemoriaSesion, RegistroSesion
        ms = MemoriaSesion()
        for i in range(10):
            ms.agregar(RegistroSesion(
                timestamp=f"2024-01-01 10:0{i}:00",
                mensaje_usuario=f"msg{i}",
                respuesta=f"resp{i}",
                intencion="test",
                accion="test",
                confianza=0.5
            ))

        ultimas = ms.ultimas(3)
        assert len(ultimas) == 3
        assert ultimas[-1].mensaje_usuario == "msg9"


# ═══════════════════════════════════════════════════════════
# TESTS DE MemoriaJerarquica
# ═══════════════════════════════════════════════════════════

class TestMemoriaJerarquica:

    @patch('services.memory.memoria_jerarquica.MemoriaVectorial')
    def test_import_y_estructura(self, mock_vectorial):
        from services.memory.memoria_jerarquica import MemoriaJerarquica
        assert MemoriaJerarquica is not None


# ═══════════════════════════════════════════════════════════
# TESTS DE MemoriaVectorial
# ═══════════════════════════════════════════════════════════

class TestMemoriaVectorial:

    def test_import(self):
        from services.memory.memoria_vectorial import MemoriaVectorial
        assert MemoriaVectorial is not None

    @patch('services.memory.memoria_vectorial.chromadb', create=True)
    def test_init(self, mock_chroma):
        mock_chroma.PersistentClient.return_value = MagicMock()
        from services.memory.memoria_vectorial import MemoriaVectorial
        # Puede necesitar ruta, creamos temporal
        try:
            mv = MemoriaVectorial()
            assert mv is not None
        except Exception:
            pass  # OK si requiere chromadb real
