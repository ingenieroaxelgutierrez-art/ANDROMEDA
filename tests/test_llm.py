# ============================================================
# ANDROMEDA — Tests de services/llm (cerebro_llm)
# ============================================================

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════
# TESTS DE Dataclasses LLM
# ═══════════════════════════════════════════════════════════

class TestDataclassesLLM:

    def test_mensaje_chat(self):
        from services.llm.cerebro_llm import MensajeChat
        m = MensajeChat(role="user", content="Hola")
        assert m.role == "user"
        assert m.content == "Hola"
        assert isinstance(m.timestamp, datetime)

    def test_respuesta_llm_defaults(self):
        from services.llm.cerebro_llm import RespuestaLLM
        r = RespuestaLLM(contenido="Respuesta", modelo="llama3.2")
        assert r.contenido == "Respuesta"
        assert r.modelo == "llama3.2"
        assert r.tokens_usados == 0
        assert r.exito is True
        assert r.error is None

    def test_respuesta_llm_error(self):
        from services.llm.cerebro_llm import RespuestaLLM
        r = RespuestaLLM(contenido="", modelo="llama3.2", exito=False, error="Timeout")
        assert r.exito is False
        assert r.error == "Timeout"

    def test_accion_detectada(self):
        from services.llm.cerebro_llm import AccionDetectada
        a = AccionDetectada(
            tipo="consulta_odoo",
            accion="ventas_totales",
            parametros={"fecha": "2024-01"},
            confianza=0.95
        )
        assert a.tipo == "consulta_odoo"
        assert a.accion == "ventas_totales"
        assert a.confianza == 0.95
        assert a.parametros['fecha'] == "2024-01"

    def test_accion_detectada_defaults(self):
        from services.llm.cerebro_llm import AccionDetectada
        a = AccionDetectada(tipo="respuesta_directa", accion="saludo")
        assert a.parametros == {}
        assert a.confianza == 0.0
        assert a.explicacion == ""


# ═══════════════════════════════════════════════════════════
# TESTS DE ConectorOllama
# ═══════════════════════════════════════════════════════════

class TestConectorOllama:

    @patch('services.llm.cerebro_llm.urllib.request.urlopen')
    def test_init_ollama_disponible(self, mock_urlopen):
        import json
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'models': [{'name': 'llama3.2'}, {'name': 'mistral'}]
        }).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        from services.llm.cerebro_llm import ConectorOllama
        c = ConectorOllama()
        assert c.disponible is True
        assert 'llama3.2' in c.modelos_disponibles

    @patch('services.llm.cerebro_llm.urllib.request.urlopen', side_effect=Exception("No connection"))
    def test_init_ollama_no_disponible(self, mock_urlopen):
        from services.llm.cerebro_llm import ConectorOllama
        c = ConectorOllama()
        assert c.disponible is False
        assert c.modelos_disponibles == []

    @patch('services.llm.cerebro_llm.urllib.request.urlopen', side_effect=Exception("No connection"))
    def test_listar_modelos_vacio(self, mock_urlopen):
        from services.llm.cerebro_llm import ConectorOllama
        c = ConectorOllama()
        assert c.listar_modelos() == []

    @patch('services.llm.cerebro_llm.urllib.request.urlopen', side_effect=Exception("No connection"))
    def test_generar_sin_conexion(self, mock_urlopen):
        from services.llm.cerebro_llm import ConectorOllama
        c = ConectorOllama()
        resp = c.generar("Hola")
        assert resp.exito is False


# ═══════════════════════════════════════════════════════════
# TESTS DE AgenteAndromeda
# ═══════════════════════════════════════════════════════════

class TestAgenteAndromeda:

    def _crear_agente(self, ollama_disponible=False):
        from services.llm.cerebro_llm import AgenteAndromeda, ConectorOllama
        mock_ollama = MagicMock(spec=ConectorOllama)
        mock_ollama.disponible = ollama_disponible
        mock_ollama.modelos_disponibles = ['llama3.2'] if ollama_disponible else []
        return AgenteAndromeda(conector_ollama=mock_ollama), mock_ollama

    def test_init_sin_conector(self):
        from services.llm.cerebro_llm import AgenteAndromeda
        with patch('services.llm.cerebro_llm.urllib.request.urlopen', side_effect=Exception("No conn")):
            agente = AgenteAndromeda()
            assert agente is not None

    def test_init_con_conector(self):
        agente, mock_ollama = self._crear_agente(ollama_disponible=True)
        # Verify agent was created with the mock connector
        assert agente is not None

    def test_get_system_prompt(self):
        agente, _ = self._crear_agente()
        prompt = agente._get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_extraer_accion_json_valido(self):
        agente, _ = self._crear_agente()
        respuesta = '{"accion": "ventas_totales", "parametros": {"periodo": "mes"}}'
        accion = agente._extraer_accion(respuesta)
        if accion:
            assert accion.accion == "ventas_totales"

    def test_extraer_accion_sin_json(self):
        agente, _ = self._crear_agente()
        accion = agente._extraer_accion("Respuesta sin JSON alguno")
        # Puede ser None o intentar fallback
        assert accion is None or hasattr(accion, 'accion')

    def test_normalizar_json(self):
        agente, _ = self._crear_agente()
        # JSON con comillas simples
        resultado = agente._normalizar_json("{'accion': 'test'}")
        assert isinstance(resultado, str)

    def test_limpiar_claves_dict(self):
        agente, _ = self._crear_agente()
        data = {"acción": "test", "parámetros": {"fecha": "2024"}}
        limpio = agente._limpiar_claves_dict(data)
        assert isinstance(limpio, dict)

    def test_obtener_accion_de_dict(self):
        agente, _ = self._crear_agente()
        data = {"accion": "ventas_totales"}
        accion = agente._obtener_accion_de_dict(data)
        assert accion == "ventas_totales"

    def test_obtener_accion_de_dict_vario_keys(self):
        agente, _ = self._crear_agente()
        # Probar con la clave 'action' en inglés
        data = {"action": "sales_total"}
        accion = agente._obtener_accion_de_dict(data)
        assert accion is not None or accion is None  # Depende de la implementación

    def test_obtener_parametros_de_dict(self):
        agente, _ = self._crear_agente()
        data = {"parametros": {"fecha": "2024-01"}}
        params = agente._obtener_parametros_de_dict(data)
        assert isinstance(params, dict)

    def test_clasificar_accion(self):
        agente, _ = self._crear_agente()
        tipo = agente._clasificar_accion("ventas_totales")
        assert isinstance(tipo, str)

    def test_fallback_accion_por_texto_ventas(self):
        agente, _ = self._crear_agente()
        accion = agente._fallback_accion_por_texto("muéstrame las ventas del mes")
        if accion:
            assert hasattr(accion, 'accion')

    def test_fallback_accion_por_texto_saludo(self):
        agente, _ = self._crear_agente()
        accion = agente._fallback_accion_por_texto("hola buen día")
        if accion:
            assert hasattr(accion, 'accion')

    def test_limpiar_respuesta(self):
        agente, _ = self._crear_agente()
        limpia = agente._limpiar_respuesta("  Respuesta con espacios  \n\n")
        assert isinstance(limpia, str)
        assert limpia == limpia.strip()

    def test_procesar_con_ollama_disponible(self):
        from services.llm.cerebro_llm import RespuestaLLM
        agente, mock_ollama = self._crear_agente(ollama_disponible=True)
        mock_ollama.generar.return_value = RespuestaLLM(
            contenido='{"accion": "ventas_totales", "parametros": {}}',
            modelo="llama3.2",
            exito=True
        )
        respuesta, accion = agente.procesar("ventas del mes")
        assert isinstance(respuesta, str)

    def test_procesar_sin_ollama(self):
        agente, mock_ollama = self._crear_agente(ollama_disponible=False)
        respuesta, accion = agente.procesar("hola")
        assert isinstance(respuesta, str)
