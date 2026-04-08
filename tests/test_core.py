# ============================================================
# ANDROMEDA — Tests de Core (bot_principal, cerebro_andromeda)
# ============================================================

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# TESTS DE OdooBotPro
# ═══════════════════════════════════════════════════════════

class TestOdooBotPro:

    @patch('core.bot_principal.GeneradorReportes')
    @patch('core.bot_principal.ConectorOdoo')
    @patch('core.bot_principal.MotorNLP')
    def test_init_crea_componentes(self, mock_nlp, mock_odoo, mock_rep, config_odoo):
        from core.bot_principal import OdooBotPro
        bot = OdooBotPro(config_odoo, modo_verbose=False)
        assert bot.verbose is False
        assert bot.conectado is False
        mock_nlp.assert_called_once()
        mock_odoo.assert_called_once_with(config_odoo)

    @patch('core.bot_principal.GeneradorReportes')
    @patch('core.bot_principal.ConectorOdoo')
    @patch('core.bot_principal.MotorNLP')
    def test_conectar_exitoso(self, mock_nlp, mock_odoo_cls, mock_rep, config_odoo):
        from core.bot_principal import OdooBotPro
        mock_odoo_cls.return_value.conectar.return_value = (True, "Conectado")
        bot = OdooBotPro(config_odoo)
        exito, msg = bot.conectar()
        assert exito is True
        assert bot.conectado is True

    @patch('core.bot_principal.GeneradorReportes')
    @patch('core.bot_principal.ConectorOdoo')
    @patch('core.bot_principal.MotorNLP')
    def test_conectar_fallido(self, mock_nlp, mock_odoo_cls, mock_rep, config_odoo):
        from core.bot_principal import OdooBotPro
        mock_odoo_cls.return_value.conectar.return_value = (False, "Error de red")
        bot = OdooBotPro(config_odoo)
        exito, msg = bot.conectar()
        assert exito is False
        assert bot.conectado is False

    @patch('core.bot_principal.GeneradorReportes')
    @patch('core.bot_principal.ConectorOdoo')
    @patch('core.bot_principal.MotorNLP')
    def test_procesar_guarda_historial(self, mock_nlp, mock_odoo_cls, mock_rep, config_odoo):
        from core.bot_principal import OdooBotPro
        mock_odoo_cls.return_value.conectar.return_value = (True, "ok")

        # Mock NLP para devolver intención de saludo
        mock_intencion = MagicMock()
        mock_intencion.intencion = 'saludo'
        mock_intencion.confianza = 0.95
        mock_intencion.entidades = []
        mock_nlp.return_value.detectar_intencion.return_value = mock_intencion

        bot = OdooBotPro(config_odoo)
        bot.conectado = True
        respuesta = bot.procesar("hola")
        assert len(bot.contexto.historial) >= 1
        assert bot.contexto.historial[0]['tipo'] == 'usuario'

    @patch('core.bot_principal.GeneradorReportes')
    @patch('core.bot_principal.ConectorOdoo')
    @patch('core.bot_principal.MotorNLP')
    def test_procesar_retorna_respuesta_bot(self, mock_nlp, mock_odoo_cls, mock_rep, config_odoo):
        from core.bot_principal import OdooBotPro, RespuestaBot
        mock_odoo_cls.return_value.conectar.return_value = (True, "ok")

        mock_intencion = MagicMock()
        mock_intencion.intencion = 'saludo'
        mock_intencion.confianza = 0.95
        mock_intencion.entidades = []
        mock_nlp.return_value.detectar_intencion.return_value = mock_intencion

        bot = OdooBotPro(config_odoo)
        bot.conectado = True
        respuesta = bot.procesar("hola")
        assert isinstance(respuesta, RespuestaBot)
        assert isinstance(respuesta.mensaje, str)
        assert len(respuesta.mensaje) > 0


class TestRespuestaBot:

    def test_defaults(self):
        from core.bot_principal import RespuestaBot
        r = RespuestaBot(mensaje="test")
        assert r.mensaje == "test"
        assert r.tipo == "texto"
        assert r.datos is None
        assert r.archivo is None
        assert r.sugerencias == []
        assert r.confianza == 1.0

    def test_con_datos(self, df_ventas):
        from core.bot_principal import RespuestaBot
        r = RespuestaBot(
            mensaje="Ventas encontradas",
            tipo="tabla",
            datos=df_ventas,
            confianza=0.9
        )
        assert r.tipo == "tabla"
        assert len(r.datos) == 5
        assert r.confianza == 0.9


class TestContextoConversacion:

    def test_defaults(self):
        from core.bot_principal import ContextoConversacion
        ctx = ContextoConversacion()
        assert ctx.ultimo_modelo is None
        assert ctx.ultima_consulta is None
        assert ctx.ultimos_datos is None
        assert ctx.filtros_activos == {}
        assert ctx.historial == []


# ═══════════════════════════════════════════════════════════
# TESTS DE CerebroAndromeda
# ═══════════════════════════════════════════════════════════

class TestCerebroAndromeda:

    def test_init_sin_conector(self):
        from core.cerebro_andromeda import CerebroAndromeda
        cerebro = CerebroAndromeda()
        assert cerebro is not None

    def test_init_con_conector(self, conector_mock):
        from core.cerebro_andromeda import CerebroAndromeda
        cerebro = CerebroAndromeda(conector_odoo=conector_mock)
        assert cerebro is not None

    def test_set_conector(self, conector_mock):
        from core.cerebro_andromeda import CerebroAndromeda
        cerebro = CerebroAndromeda()
        cerebro.set_conector(conector_mock)


class TestLimpiadorDatos:

    def test_limpiar_dataframe_vacio(self, df_vacio):
        from core.cerebro_andromeda import LimpiadorDatos
        limpiador = LimpiadorDatos()
        df_limpio, confianza, stats = limpiador.limpiar_dataframe(df_vacio)
        assert isinstance(df_limpio, pd.DataFrame)
        assert isinstance(confianza, float)
        assert isinstance(stats, dict)

    def test_limpiar_dataframe_con_datos(self, df_ventas):
        from core.cerebro_andromeda import LimpiadorDatos
        limpiador = LimpiadorDatos()
        df_limpio, confianza, stats = limpiador.limpiar_dataframe(df_ventas, modelo='sale.order')
        assert len(df_limpio) > 0
        assert 0 <= confianza <= 1.0
        assert 'registros_procesados' in stats

    def test_validar_numerico_normal(self):
        from core.cerebro_andromeda import LimpiadorDatos
        limpiador = LimpiadorDatos()
        assert limpiador.validar_numerico(42.5) == 42.5

    def test_validar_numerico_none(self):
        from core.cerebro_andromeda import LimpiadorDatos
        limpiador = LimpiadorDatos()
        assert limpiador.validar_numerico(None, default=0.0) == 0.0

    def test_validar_numerico_string(self):
        from core.cerebro_andromeda import LimpiadorDatos
        limpiador = LimpiadorDatos()
        assert limpiador.validar_numerico("not_a_number", default=-1.0) == -1.0

    def test_validar_fecha_valida(self):
        from core.cerebro_andromeda import LimpiadorDatos
        limpiador = LimpiadorDatos()
        r = limpiador.validar_fecha("2026-03-13")
        assert r == "2026-03-13"

    def test_validar_fecha_none(self):
        from core.cerebro_andromeda import LimpiadorDatos
        limpiador = LimpiadorDatos()
        assert limpiador.validar_fecha(None) is None

    def test_validar_fecha_invalida(self):
        from core.cerebro_andromeda import LimpiadorDatos
        limpiador = LimpiadorDatos()
        assert limpiador.validar_fecha("no-es-fecha") is None


class TestMotorEstadistico:

    def test_existe(self):
        from core.cerebro_andromeda import MotorEstadistico
        assert MotorEstadistico is not None
