# ============================================================
# ANDROMEDA — Tests de Contratos (Fase 2)
# ============================================================
# Verifica que las implementaciones reales satisfacen sus
# respectivos protocolos definidos en core/contratos.py
# ============================================================

import pytest
from unittest.mock import MagicMock
import pandas as pd

from core.contratos import (
    ConectorOdooBase,
    AgenteEspecializadoProtocol,
    MotorPrediccionBase,
    ConectorLLMBase,
)


# ════════════════════════════════════════════════════════════
# CONTRATO 1 — ConectorOdooBase
# ════════════════════════════════════════════════════════════

class TestContratoConectorOdoo:
    """Verifica que ConectorOdoo cumple ConectorOdooBase."""

    def test_conector_satisface_protocolo(self):
        """ConectorOdoo debe isinstance de ConectorOdooBase (runtime_checkable)."""
        from models.conector_odoo import ConectorOdoo, ConfiguracionOdoo
        config = ConfiguracionOdoo(
            url="https://test.odoo.com",
            db="test",
            usuario="bot@test.com",
            password="fake"
        )
        conector = ConectorOdoo(config=config)
        assert isinstance(conector, ConectorOdooBase)

    def test_conector_tiene_atributo_conectado(self):
        from models.conector_odoo import ConectorOdoo, ConfiguracionOdoo
        config = ConfiguracionOdoo(url="x", db="x", usuario="x", password="x")
        conector = ConectorOdoo(config=config)
        assert hasattr(conector, 'conectado')
        assert isinstance(conector.conectado, bool)

    def test_conector_tiene_metodo_conectar(self):
        from models.conector_odoo import ConectorOdoo, ConfiguracionOdoo
        config = ConfiguracionOdoo(url="x", db="x", usuario="x", password="x")
        conector = ConectorOdoo(config=config)
        assert callable(getattr(conector, 'conectar', None))

    def test_conector_tiene_metodo_desconectar(self):
        from models.conector_odoo import ConectorOdoo, ConfiguracionOdoo
        config = ConfiguracionOdoo(url="x", db="x", usuario="x", password="x")
        conector = ConectorOdoo(config=config)
        assert callable(getattr(conector, 'desconectar', None))

    def test_conector_tiene_metodo_buscar(self):
        from models.conector_odoo import ConectorOdoo, ConfiguracionOdoo
        config = ConfiguracionOdoo(url="x", db="x", usuario="x", password="x")
        conector = ConectorOdoo(config=config)
        assert callable(getattr(conector, 'buscar', None))

    def test_conector_tiene_metodo_buscar_leer(self):
        from models.conector_odoo import ConectorOdoo, ConfiguracionOdoo
        config = ConfiguracionOdoo(url="x", db="x", usuario="x", password="x")
        conector = ConectorOdoo(config=config)
        assert callable(getattr(conector, 'buscar_leer', None))

    def test_desconectar_no_lanza_excepcion(self):
        """desconectar() no debe lanzar excepción aunque no haya conexión activa."""
        from models.conector_odoo import ConectorOdoo, ConfiguracionOdoo
        config = ConfiguracionOdoo(url="x", db="x", usuario="x", password="x")
        conector = ConectorOdoo(config=config)
        conector.desconectar()  # No debe lanzar
        assert conector.conectado is False


# ════════════════════════════════════════════════════════════
# CONTRATO 2 — AgenteEspecializadoProtocol
# ════════════════════════════════════════════════════════════

class TestContratoAgenteEspecializado:
    """Verifica que AgenteEspecializadoBase y sus subclases satisfacen el protocolo."""

    AGENTES = [
        'AgentVentas', 'AgentInventarios', 'AgentFinanzas', 'AgentDiagnostico',
        'AgentConsultasOdoo', 'AgentCRM', 'AgentCompras', 'AgentPDV',
        'AgentPredicciones', 'AgentMatematicas', 'AgentEstadistica', 'AgentRRHH',
    ]

    @pytest.mark.parametrize("nombre_clase", AGENTES)
    def test_agente_satisface_protocolo(self, nombre_clase):
        """Cada agente especializado debe implementar AgenteEspecializadoProtocol."""
        import services.agents.multi_agente as ma
        cls = getattr(ma, nombre_clase)
        agente = cls()
        assert isinstance(agente, AgenteEspecializadoProtocol), (
            f"{nombre_clase} no satisface AgenteEspecializadoProtocol"
        )

    @pytest.mark.parametrize("nombre_clase", AGENTES)
    def test_agente_tiene_id_agente(self, nombre_clase):
        import services.agents.multi_agente as ma
        cls = getattr(ma, nombre_clase)
        agente = cls()
        assert hasattr(agente, 'id_agente')
        assert isinstance(agente.id_agente, str)
        assert len(agente.id_agente) > 0

    @pytest.mark.parametrize("nombre_clase", AGENTES)
    def test_agente_tiene_prompt_base(self, nombre_clase):
        import services.agents.multi_agente as ma
        cls = getattr(ma, nombre_clase)
        agente = cls()
        assert hasattr(agente, 'prompt_base')
        assert isinstance(agente.prompt_base, str)
        assert len(agente.prompt_base) > 10

    @pytest.mark.parametrize("nombre_clase", AGENTES)
    def test_agente_score_prompt_retorna_float(self, nombre_clase):
        import services.agents.multi_agente as ma
        cls = getattr(ma, nombre_clase)
        agente = cls()
        score = agente.score_prompt("ventas del mes")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    @pytest.mark.parametrize("nombre_clase", AGENTES)
    def test_agente_score_prompt_mensaje_vacio(self, nombre_clase):
        """score_prompt con mensaje vacío nunca debe lanzar excepción."""
        import services.agents.multi_agente as ma
        cls = getattr(ma, nombre_clase)
        agente = cls()
        score = agente.score_prompt("")
        assert score == 0.0

    def test_ids_agentes_son_unicos(self):
        """No puede haber dos agentes con el mismo id_agente."""
        import services.agents.multi_agente as ma
        ids = []
        for nombre in self.AGENTES:
            cls = getattr(ma, nombre)
            ids.append(cls().id_agente)
        assert len(ids) == len(set(ids)), f"IDs duplicados encontrados: {ids}"


# ════════════════════════════════════════════════════════════
# CONTRATO 3 — MotorPrediccionBase
# ════════════════════════════════════════════════════════════

class TestContratoMotorPrediccion:
    """Verifica que MotorPrediccion satisface MotorPrediccionBase."""

    def test_motor_prediccion_satisface_protocolo(self):
        from services.prediction.motor_prediccion import MotorPrediccion
        motor = MotorPrediccion()
        assert isinstance(motor, MotorPrediccionBase)

    def test_motor_tiene_set_conector(self):
        from services.prediction.motor_prediccion import MotorPrediccion
        motor = MotorPrediccion()
        assert callable(getattr(motor, 'set_conector', None))

    def test_motor_tiene_predecir_ventas(self):
        from services.prediction.motor_prediccion import MotorPrediccion
        motor = MotorPrediccion()
        assert callable(getattr(motor, 'predecir_ventas', None))

    def test_motor_tiene_predecir_agotamiento(self):
        from services.prediction.motor_prediccion import MotorPrediccion
        motor = MotorPrediccion()
        assert callable(getattr(motor, 'predecir_agotamiento', None))

    def test_set_conector_acepta_mock(self):
        """set_conector debe aceptar cualquier objeto sin lanzar excepción."""
        from services.prediction.motor_prediccion import MotorPrediccion
        motor = MotorPrediccion()
        mock_conector = MagicMock()
        motor.set_conector(mock_conector)  # No debe lanzar
        assert motor.conector is mock_conector


# ════════════════════════════════════════════════════════════
# CONTRATO 4 — ConectorLLMBase
# ════════════════════════════════════════════════════════════

class TestContratoConectorLLM:
    """Verifica que ConectorOllama satisface ConectorLLMBase."""

    def test_conector_ollama_satisface_protocolo(self):
        from services.llm.cerebro_llm import ConectorOllama
        conector = ConectorOllama()
        assert isinstance(conector, ConectorLLMBase)

    def test_conector_llm_tiene_atributo_disponible(self):
        from services.llm.cerebro_llm import ConectorOllama
        conector = ConectorOllama()
        assert hasattr(conector, 'disponible')
        assert isinstance(conector.disponible, bool)

    def test_conector_llm_tiene_metodo_generar(self):
        from services.llm.cerebro_llm import ConectorOllama
        conector = ConectorOllama()
        assert callable(getattr(conector, 'generar', None))

    def test_conector_llm_tiene_metodo_esta_disponible(self):
        from services.llm.cerebro_llm import ConectorOllama
        conector = ConectorOllama()
        assert callable(getattr(conector, 'esta_disponible', None))

    def test_esta_disponible_retorna_bool(self):
        """esta_disponible() siempre debe retornar bool, incluso sin Ollama activo."""
        from services.llm.cerebro_llm import ConectorOllama
        conector = ConectorOllama()
        resultado = conector.esta_disponible()
        assert isinstance(resultado, bool)
