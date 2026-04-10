# ============================================================
# ANDROMEDA — conftest.py — Fixtures compartidos para tests
# ============================================================

import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

# ─── Constantes de prueba ─────────────────────────────────
_PASS_FAKE = "fake-api-key-for-testing"  # noqa: S105
_CLI_A = 'Cliente A'
_CLI_B = 'Cliente B'
_CLI_C = 'Cliente C'
_VEND_1 = 'Vendedor 1'
_VEND_2 = 'Vendedor 2'

# Asegurar path del proyecto
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ─── Mock de dependencias pesadas (evita cuelgues en importación) ─────
# sentence_transformers carga PyTorch internamente durante el import,
# lo que puede congelar el proceso en entornos sin GPU o con inicialización
# lenta de CUDA. Se mockea antes de cualquier import del proyecto para que
# los tests sean rápidos y deterministas.
# NOTA: NO mockear torch directamente — scipy lo usa con issubclass() y
# necesita torch.Tensor como clase real. Solo mocking a nivel de ST.
_mock_st = MagicMock()
_mock_st.SentenceTransformer = MagicMock()
_mock_st.util = MagicMock()
sys.modules.setdefault('sentence_transformers', _mock_st)
# ──────────────────────────────────────────────────────────────────────

import pandas as pd


# ─── Fixtures de Configuración ────────────────────────────

@pytest.fixture
def config_odoo():
    """ConfiguracionOdoo de prueba (NO conecta a servidor real)."""
    from app.config import ConfiguracionOdoo
    return ConfiguracionOdoo(
        url="https://test.odoo.com",
        db="test-db",
        usuario="test@test.com",
        password=_PASS_FAKE
    )


@pytest.fixture
def config_class():
    """Clase Config del proyecto."""
    from app.config import Config
    return Config


# ─── Fixtures de DataFrames de prueba ─────────────────────

@pytest.fixture
def df_ventas():
    """DataFrame simulando ventas de Odoo."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['SO001', 'SO002', 'SO003', 'SO004', 'SO005'],
        'partner_id': [_CLI_A, _CLI_B, _CLI_A, _CLI_C, _CLI_B],
        'amount_total': [1500.0, 2300.0, 800.0, 4500.0, 1200.0],
        'date_order': [
            '2026-03-01', '2026-03-02', '2026-03-03',
            '2026-03-04', '2026-03-05'
        ],
        'state': ['sale', 'sale', 'sale', 'done', 'sale'],
        'user_id': [_VEND_1, _VEND_2, _VEND_1, _VEND_2, _VEND_1],
    })


@pytest.fixture
def df_inventario():
    """DataFrame simulando stock de Odoo."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'product_id': ['Producto A', 'Producto B', 'Producto C'],
        'location_id': ['Almacén 1', 'Almacén 1', 'Almacén 2'],
        'quantity': [100.0, -5.0, 0.0],
        'reserved_quantity': [10.0, 0.0, 0.0],
    })


@pytest.fixture
def df_facturas():
    """DataFrame simulando facturas de Odoo."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['INV/2026/001', 'INV/2026/002', 'INV/2026/003'],
        'partner_id': [_CLI_A, _CLI_B, _CLI_C],
        'amount_total': [1500.0, 2300.0, 800.0],
        'amount_residual': [0.0, 1000.0, 800.0],
        'invoice_date': ['2026-03-01', '2026-03-02', '2026-03-03'],
        'payment_state': ['paid', 'partial', 'not_paid'],
        'move_type': ['out_invoice', 'out_invoice', 'out_invoice'],
    })


@pytest.fixture
def df_vacio():
    """DataFrame vacío."""
    return pd.DataFrame()


@pytest.fixture
def df_crm():
    """DataFrame simulando oportunidades CRM."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Oportunidad A', 'Oportunidad B', 'Oportunidad C'],
        'partner_id': [_CLI_A, _CLI_B, _CLI_C],
        'stage_id': ['Nuevo', 'Propuesta', 'Ganado'],
        'expected_revenue': [10000.0, 25000.0, 5000.0],
        'probability': [30.0, 70.0, 100.0],
        'user_id': [_VEND_1, _VEND_2, _VEND_1],
    })


# ─── Fixtures de Consulta simulada ───────────────────────

@dataclass
class ConsultaFake:
    """Simulación de ConsultaEntendida para tests."""
    intencion_principal: str = "consultar_ventas"
    confianza: float = 0.85
    accion_sugerida: str = "consultar_ventas"
    parametros: Optional[dict] = None
    temporalidad: Optional[dict] = None
    modelo_sugerido: str = "sale.order"
    palabras_clave: Optional[list] = None
    filtros_detectados: Optional[list] = None
    contexto_previo: Optional[dict] = None

    def __post_init__(self):
        if self.parametros is None:
            self.parametros = {}
        if self.temporalidad is None:
            self.temporalidad = {
                'fecha_inicio': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'fecha_fin': datetime.now().strftime('%Y-%m-%d')
            }
        if self.palabras_clave is None:
            self.palabras_clave = []
        if self.filtros_detectados is None:
            self.filtros_detectados = []
        if self.contexto_previo is None:
            self.contexto_previo = {}


@pytest.fixture
def consulta_ventas():
    return ConsultaFake(
        intencion_principal="consultar_ventas",
        accion_sugerida="consultar_ventas",
        confianza=0.9
    )


@pytest.fixture
def consulta_inventario():
    return ConsultaFake(
        intencion_principal="consultar_inventario",
        accion_sugerida="consultar_inventario",
        modelo_sugerido="stock.quant",
        confianza=0.88
    )


@pytest.fixture
def consulta_crm():
    return ConsultaFake(
        intencion_principal="pipeline_etapas",
        accion_sugerida="pipeline_etapas",
        modelo_sugerido="crm.lead",
        confianza=0.87
    )


# ─── Fixture de ConectorOdoo mockeado ─────────────────────

@pytest.fixture
def conector_mock(df_ventas):
    """ConectorOdoo completamente mockeado."""
    mock = MagicMock()
    mock.conectado = True
    mock.buscar.return_value = df_ventas
    mock.buscar_leer.return_value = df_ventas.to_dict('records')
    mock.contar.return_value = 5
    mock.obtener_campos.return_value = {
        'name': {'type': 'char'},
        'amount_total': {'type': 'float'},
        'date_order': {'type': 'datetime'},
    }
    return mock


# ─── Fixture del GestorMultiAgente ────────────────────────

@pytest.fixture
def gestor():
    """GestorMultiAgente instanciado."""
    from services.agents.multi_agente import GestorMultiAgente
    return GestorMultiAgente()
