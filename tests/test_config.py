# ============================================================
# ANDROMEDA — Tests de Configuración y Main
# ============================================================

import os
import pytest
from unittest.mock import patch, MagicMock

from app.config import Config, ConfiguracionOdoo


# ═══════════════════════════════════════════════════════════
# TESTS DE Config
# ═══════════════════════════════════════════════════════════

class TestConfig:

    def test_base_dir_existe(self):
        assert os.path.isdir(Config.BASE_DIR)

    def test_data_dir_definido(self):
        assert isinstance(Config.DATA_DIR, str)
        assert 'data' in Config.DATA_DIR

    def test_reports_dir_definido(self):
        assert isinstance(Config.REPORTS_DIR, str)
        assert 'reports' in Config.REPORTS_DIR

    def test_version_no_vacia(self):
        assert isinstance(Config.VERSION, str)
        assert len(Config.VERSION) > 0

    def test_nombre(self):
        assert Config.NOMBRE == "ANDROMEDA"

    def test_nombre_completo(self):
        assert isinstance(Config.NOMBRE_COMPLETO, str)
        assert "ANDROMEDA" in Config.NOMBRE_COMPLETO or "Advanced" in Config.NOMBRE_COMPLETO

    def test_modelo_spacy(self):
        assert Config.MODELO_SPACY == "es_core_news_sm"

    def test_gradio_port(self):
        assert isinstance(Config.GRADIO_SERVER_PORT, int)
        assert Config.GRADIO_SERVER_PORT > 0

    def test_crear_directorios(self, tmp_path):
        """Verifica que crear_directorios no falla (los dirs principales ya existen)."""
        Config.crear_directorios()
        assert os.path.isdir(Config.DATA_DIR)
        assert os.path.isdir(Config.REPORTS_DIR)
        assert os.path.isdir(Config.ASSETS_DIR)


# ═══════════════════════════════════════════════════════════
# TESTS DE ConfiguracionOdoo
# ═══════════════════════════════════════════════════════════

class TestConfiguracionOdoo:

    def test_crear_instancia(self):
        c = ConfiguracionOdoo(
            url="https://test.odoo.com", db="test", 
            usuario="user", password="pass"
        )
        assert c.url == "https://test.odoo.com"
        assert c.db == "test"

    def test_default_retorna_instancia(self):
        c = ConfiguracionOdoo.default()
        assert isinstance(c, ConfiguracionOdoo)
        assert len(c.url) > 0
        assert len(c.db) > 0

    def test_desde_json(self, tmp_path):
        import json
        cfg = tmp_path / "cfg.json"
        cfg.write_text(json.dumps({
            "url": "https://x.com", "db": "d",
            "usuario": "u", "password": "p"
        }), encoding="utf-8")
        c = ConfiguracionOdoo.desde_json(str(cfg))
        assert c.url == "https://x.com"

    def test_desde_json_campos_faltantes(self, tmp_path):
        import json
        cfg = tmp_path / "cfg_parcial.json"
        cfg.write_text(json.dumps({"url": "https://parcial.com"}), encoding="utf-8")
        c = ConfiguracionOdoo.desde_json(str(cfg))
        assert c.url == "https://parcial.com"
        assert c.db == ""


# ═══════════════════════════════════════════════════════════
# TESTS DE MAIN (punto de entrada)
# ═══════════════════════════════════════════════════════════

class TestMain:

    def test_importar_main(self):
        """Verificar que main.py se importa sin errores."""
        import main
        assert hasattr(main, 'iniciar_web')
        assert hasattr(main, 'iniciar_consola')

    def test_iniciar_web_es_callable(self):
        import main
        assert callable(main.iniciar_web)

    def test_iniciar_consola_es_callable(self):
        import main
        assert callable(main.iniciar_consola)
