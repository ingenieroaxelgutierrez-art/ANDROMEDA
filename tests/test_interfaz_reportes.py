# ============================================================
# ANDROMEDA — Tests de Interfaz y Reportes
# ============================================================

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════════════════
# TESTS DE OdooAIProV5
# ═══════════════════════════════════════════════════════════

class TestOdooAIProV5:
    """Tests de la interfaz principal — componentes aislados."""

    @pytest.fixture
    def bot(self):
        """OdooAIProV5 con todas las dependencias mockeadas."""
        mock_conector_cls = MagicMock()
        mock_conector_cls.return_value.conectar.return_value = (True, "Mock OK")

        with patch.multiple(
            'views.interfaz_v5',
            ConectorOdoo=mock_conector_cls,
            CerebroNLP=MagicMock,
            MotorNLPAvanzado=MagicMock,
            MotorEmpatico=MagicMock,
            CerebroAndromeda=MagicMock,
            GeneradorGraficas=MagicMock,
            AnalizadorAvanzado=MagicMock,
            MotorPrediccion=MagicMock,
            MotorBIExperto=MagicMock,
            AnalizadorAnomalias=MagicMock,
            KPIsFinancieros=MagicMock,
            GestorMultiAgente=MagicMock,
            AsistenteErroresOdoo=MagicMock,
            create=True,
        ):
            from views.interfaz_v5 import OdooAIProV5
            return OdooAIProV5()

    def test_instanciacion(self, bot):
        assert bot is not None

    def test_max_input_length_definido(self, bot):
        assert hasattr(bot, 'MAX_INPUT_LENGTH')
        assert bot.MAX_INPUT_LENGTH == 2000

    def test_max_requests_per_minute_definido(self, bot):
        assert hasattr(bot, 'MAX_REQUESTS_PER_MINUTE')
        assert bot.MAX_REQUESTS_PER_MINUTE == 30

    def test_procesar_mensaje_vacio(self, bot):
        historial, _, status = bot.procesar_mensaje("", [])
        assert status == "✓ Listo"

    def test_procesar_mensaje_solo_espacios(self, bot):
        historial, _, status = bot.procesar_mensaje("   ", [])
        assert status == "✓ Listo"

    def test_procesar_mensaje_trunca_input_largo(self, bot):
        """Input mayor a MAX_INPUT_LENGTH debe truncarse."""
        msg_largo = "a" * 5000
        # El mensaje se trunca internamente; no debe dar error
        bot.motor_empatico.procesar_mensaje.return_value = ("Hola", "saludo")
        historial, _, _ = bot.procesar_mensaje(msg_largo, [])
        # Debe haber procesado sin error
        assert len(historial) > 0

    def test_rate_limiting(self, bot):
        """Después de MAX_REQUESTS_PER_MINUTE, debe rechazar."""
        bot.motor_empatico.procesar_mensaje.return_value = ("Hola", "saludo")
        bot._request_timestamps = []
        
        # Simular que ya se alcanzó el límite
        ahora = datetime.now()
        bot._request_timestamps = [ahora - timedelta(seconds=i) for i in range(30)]
        
        historial, _, status = bot.procesar_mensaje("test", [])
        assert "Rate limit" in status or "Demasiadas" in historial[-1].get('content', '')


# ═══════════════════════════════════════════════════════════
# TESTS DE GeneradorGraficas
# ═══════════════════════════════════════════════════════════

class TestGeneradorGraficas:

    def test_init(self):
        from services.reports.generador_graficas import GeneradorGraficas
        gen = GeneradorGraficas()
        assert gen is not None

    def test_detectar_tipo_grafica_ventas(self, df_ventas):
        from services.reports.generador_graficas import GeneradorGraficas
        gen = GeneradorGraficas()
        tipo = gen.detectar_tipo_grafica(df_ventas, contexto="ventas por mes")
        assert isinstance(tipo, str)
        assert len(tipo) > 0

    def test_detectar_tipo_grafica_df_vacio(self, df_vacio):
        from services.reports.generador_graficas import GeneradorGraficas
        gen = GeneradorGraficas()
        tipo = gen.detectar_tipo_grafica(df_vacio, contexto="test")
        assert isinstance(tipo, str)


# ═══════════════════════════════════════════════════════════
# TESTS DE GeneradorPDF
# ═══════════════════════════════════════════════════════════

class TestGeneradorPDF:

    def test_init_sin_config(self):
        from services.reports.generador_pdf import GeneradorPDF
        gen = GeneradorPDF()
        assert gen is not None

    def test_init_con_config(self):
        from services.reports.generador_pdf import GeneradorPDF, ConfiguracionReporte
        config = ConfiguracionReporte()
        gen = GeneradorPDF(config)
        assert gen is not None
