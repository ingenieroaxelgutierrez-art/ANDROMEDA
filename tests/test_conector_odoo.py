# ============================================================
# ANDROMEDA — Tests del Conector Odoo
# ============================================================

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, PropertyMock

from models.conector_odoo import ConectorOdoo, ConfiguracionOdoo


# ═══════════════════════════════════════════════════════════
# TESTS DE ConfiguracionOdoo
# ═══════════════════════════════════════════════════════════

class TestConfiguracionOdoo:

    def test_crear_config(self, config_odoo):
        assert config_odoo.url == "https://test.odoo.com"
        assert config_odoo.db == "test-db"
        assert config_odoo.usuario == "test@test.com"

    def test_default(self):
        config = ConfiguracionOdoo.default()
        assert isinstance(config.url, str)
        assert isinstance(config.db, str)
        assert len(config.url) > 0
        assert len(config.db) > 0

    def test_desde_json(self, tmp_path):
        import json
        cfg_file = tmp_path / "odoo_config.json"
        cfg_file.write_text(json.dumps({
            "url": "https://json.odoo.com",
            "db": "json-db",
            "usuario": "json@test.com",
            "password": "json-pass"
        }), encoding="utf-8")

        config = ConfiguracionOdoo.desde_json(str(cfg_file))
        assert config.url == "https://json.odoo.com"
        assert config.db == "json-db"


# ═══════════════════════════════════════════════════════════
# TESTS DEL CONECTOR ODOO
# ═══════════════════════════════════════════════════════════

class TestConectorOdoo:

    def test_init_sin_config(self):
        """Debe instanciar con config default si no se pasa ninguna."""
        conector = ConectorOdoo()
        assert conector.config is not None
        assert conector.conectado is False

    def test_init_con_config(self, config_odoo):
        conector = ConectorOdoo(config_odoo)
        assert conector.config.url == "https://test.odoo.com"
        assert conector.conectado is False

    def test_modelos_principales(self, config_odoo):
        conector = ConectorOdoo(config_odoo)
        modelos = conector.modelos_principales
        assert 'ventas' in modelos
        assert 'productos' in modelos
        assert 'stock' in modelos
        assert 'clientes' in modelos
        assert 'facturas' in modelos
        assert modelos['ventas']['modelo'] == 'sale.order'

    def test_desconectar(self, config_odoo):
        conector = ConectorOdoo(config_odoo)
        conector.desconectar()
        assert conector.conectado is False
        assert conector.odoo is None

    @patch('models.conector_odoo.odoorpc.ODOO')
    def test_conectar_exitoso(self, mock_odoo_class, config_odoo):
        mock_instance = MagicMock()
        mock_odoo_class.return_value = mock_instance

        conector = ConectorOdoo(config_odoo)
        exito, msg = conector.conectar()

        assert exito is True
        assert conector.conectado is True
        assert "Conectado" in msg

    @patch('models.conector_odoo.odoorpc.ODOO')
    def test_conectar_falla(self, mock_odoo_class, config_odoo):
        mock_odoo_class.side_effect = Exception("Connection refused")

        conector = ConectorOdoo(config_odoo)
        exito, msg = conector.conectar()

        assert exito is False
        assert conector.conectado is False
        assert "Error" in msg

    def test_contar_sin_conexion_retorna_cero(self, config_odoo):
        """Sin conexión real, contar debe manejar el error."""
        conector = ConectorOdoo(config_odoo)
        conector.conectado = False
        # Patch _verificar_conexion para que no intente conectar real
        with patch.object(conector, '_verificar_conexion', return_value=False):
            resultado = conector.contar('sale.order')
            assert resultado == 0

    def test_buscar_sin_conexion_retorna_df_vacio(self, config_odoo):
        """Sin conexión, buscar devuelve DataFrame vacío."""
        conector = ConectorOdoo(config_odoo)
        with patch.object(conector, '_verificar_conexion', return_value=False):
            resultado = conector.buscar('sale.order')
            assert isinstance(resultado, pd.DataFrame)

    def test_conector_mock_fixture(self, conector_mock, df_ventas):
        """Verifica que el fixture conector_mock funciona correctamente."""
        assert conector_mock.conectado is True
        resultado = conector_mock.buscar('sale.order')
        assert isinstance(resultado, pd.DataFrame)
        assert len(resultado) == len(df_ventas)
        assert conector_mock.contar('sale.order') == 5
