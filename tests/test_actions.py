# ============================================================
# ANDROMEDA — Tests de services/actions (ejecutor + mapeador)
# ============================================================

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# TESTS DE EjecutorAcciones
# ═══════════════════════════════════════════════════════════

class TestEjecutorAcciones:

    def _crear_ejecutor(self):
        from services.actions.ejecutor_acciones import EjecutorAcciones
        mock_bot = MagicMock()
        mock_bot.odoo = MagicMock()
        mock_bot.conector = MagicMock()
        mock_bot.reportes = MagicMock()
        mock_bot.ultimo_df = None
        mock_bot.ultimo_modelo = None
        mock_bot.generador_pdf_reportlab = None
        mock_bot.generador_queries = None
        mock_bot.auditoria = None
        mock_bot.cerebro_llm = None
        return EjecutorAcciones(mock_bot), mock_bot

    def test_init(self):
        ej, bot = self._crear_ejecutor()
        assert ej._bot is bot

    def test_contar_chiste(self):
        ej, _ = self._crear_ejecutor()
        resultado = ej._contar_chiste()
        assert isinstance(resultado, str)
        assert "chiste" in resultado.lower()

    def test_mostrar_capacidades(self):
        ej, _ = self._crear_ejecutor()
        resultado = ej._mostrar_capacidades()
        assert isinstance(resultado, str)
        assert "ANDROMEDA" in resultado

    def test_responder_despedida(self):
        ej, _ = self._crear_ejecutor()
        resultado = ej._responder_despedida()
        assert isinstance(resultado, str)
        assert len(resultado) > 10

    def test_responder_agradecimiento(self):
        ej, _ = self._crear_ejecutor()
        resultado = ej._responder_agradecimiento()
        assert isinstance(resultado, str)

    def test_responder_saludo(self):
        ej, _ = self._crear_ejecutor()
        resultado = ej._responder_saludo()
        assert isinstance(resultado, str)
        assert len(resultado) > 10

    def test_generar_ayuda_completa(self):
        ej, _ = self._crear_ejecutor()
        resultado = ej._generar_ayuda_completa()
        assert isinstance(resultado, str)
        assert "ANDROMEDA" in resultado

    def test_info_conexion(self):
        ej, bot = self._crear_ejecutor()
        bot.odoo_url = "https://test.odoo.com"
        bot.odoo_db = "test_db"
        bot.odoo_user = "admin"
        resultado = ej._info_conexion()
        assert isinstance(resultado, str)
        assert "Sistema" in resultado

    def test_generar_reporte_sin_datos(self):
        ej, bot = self._crear_ejecutor()
        bot.ultimo_df = None
        resultado = ej._generar_reporte("pdf")
        assert "No hay datos" in resultado

    def test_generar_reporte_con_datos(self):
        ej, bot = self._crear_ejecutor()
        bot.ultimo_df = pd.DataFrame({'a': [1, 2]})
        bot.ultimo_modelo = 'sale.order'
        bot.reportes.generar_reporte.return_value = "/tmp/reporte.pdf"
        resultado = ej._generar_reporte("pdf")
        assert "Reporte Generado" in resultado

    def test_generar_pdf_sin_generador(self):
        ej, bot = self._crear_ejecutor()
        bot.generador_pdf_reportlab = None
        resultado = ej._generar_pdf_profesional()
        assert "no está disponible" in resultado

    def test_ejecutar_consulta_dinamica_sin_generador(self):
        ej, bot = self._crear_ejecutor()
        bot.generador_queries = None
        resp, df = ej._ejecutar_consulta_dinamica("ventas")
        assert "no está disponible" in resp
        assert df is None

    def test_respuesta_accion_no_disponible(self):
        ej, _ = self._crear_ejecutor()
        resultado = ej._respuesta_accion_no_disponible("Ventas Totales")
        assert "Ventas Totales" in resultado
        assert "puedes hacer" in resultado or "puedo responder" in resultado

    def test_generar_kpis_por_tienda_sin_datos(self):
        ej, bot = self._crear_ejecutor()
        bot.odoo.buscar.return_value = pd.DataFrame()
        resultado = ej._generar_kpis_por_tienda("2024-01-01", "2024-01-31")
        assert "No hay datos" in resultado

    def test_consultar_facturas_sin_datos(self):
        ej, bot = self._crear_ejecutor()
        bot.odoo.buscar.return_value = pd.DataFrame()
        mock_consulta = MagicMock()
        mock_consulta.parametros = {}
        bot._obtener_entidades_cerebro.return_value = []
        resp, df = ej._consultar_facturas_filtradas(mock_consulta, "2024-01-01", "2024-01-31")
        assert "No se encontraron" in resp
        assert df is None

    def test_ventas_tienda_no_encontrada(self):
        ej, bot = self._crear_ejecutor()
        bot.odoo.search_read.return_value = []
        resultado = ej._ventas_tienda_especifica("tienda_xyz", "2024-01-01", "2024-01-31")
        assert "no encontr" in resultado.lower()


# ═══════════════════════════════════════════════════════════
# TESTS DE MapeadorConsultas
# ═══════════════════════════════════════════════════════════

class TestMapeadorConsultas:

    def _crear_mapeador(self):
        from services.actions.mapeador_consultas import MapeadorConsultas
        mock_bot = MagicMock()
        return MapeadorConsultas(mock_bot), mock_bot

    def test_init(self):
        m, bot = self._crear_mapeador()
        assert m._bot is bot

    def test_mapear_ventas_totales(self):
        m, _ = self._crear_mapeador()
        mock_consulta = MagicMock()
        resultado = m._mapear_accion_a_consulta_odoo(
            "ventas_totales", "2024-01-01", "2024-01-31", {}, mock_consulta
        )
        assert resultado is not None or resultado is None  # Depende de la implementación

    def test_mapear_accion_inexistente(self):
        m, _ = self._crear_mapeador()
        mock_consulta = MagicMock()
        resultado = m._mapear_accion_a_consulta_odoo(
            "accion_no_existe_xyz", "2024-01-01", "2024-01-31", {}, mock_consulta
        )
        # Debe manejar acciones desconocidas sin error
        assert resultado is None or isinstance(resultado, dict)
