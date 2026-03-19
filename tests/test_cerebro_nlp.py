# ============================================================
# ANDROMEDA — Tests del Cerebro NLP
# ============================================================

import pytest
from unittest.mock import patch, MagicMock

from services.nlp.cerebro_nlp import (
    TipoConsulta,
    NivelEspecificidad,
    EntidadSmart,
    IntencionSmart,
    AnalisisSemantico,
    ContextoConversacional,
    CerebroNLP,
)


# ═══════════════════════════════════════════════════════════
# TESTS DE ENUMS
# ═══════════════════════════════════════════════════════════

class TestEnums:

    def test_tipo_consulta_valores(self):
        assert TipoConsulta.CONSULTA_DATOS.value == "consulta"
        assert TipoConsulta.ANALISIS.value == "analisis"
        assert TipoConsulta.COMPARATIVA.value == "comparativa"
        assert TipoConsulta.PREDICCION.value == "prediccion"
        assert TipoConsulta.REPORTE.value == "reporte"
        assert TipoConsulta.AYUDA.value == "ayuda"
        assert TipoConsulta.CONVERSACIONAL.value == "chat"
        assert TipoConsulta.MANUAL.value == "manual"
        assert TipoConsulta.GRAFICA.value == "grafica"

    def test_nivel_especificidad_orden(self):
        assert NivelEspecificidad.VAGA.value < NivelEspecificidad.GENERAL.value
        assert NivelEspecificidad.GENERAL.value < NivelEspecificidad.ESPECIFICA.value
        assert NivelEspecificidad.ESPECIFICA.value < NivelEspecificidad.MUY_ESPECIFICA.value


# ═══════════════════════════════════════════════════════════
# TESTS DE DATACLASSES
# ═══════════════════════════════════════════════════════════

class TestDataclassesNLP:

    def test_entidad_smart(self):
        e = EntidadSmart(
            tipo="fecha", valor="2026-03", valor_original="marzo",
            confianza=0.9, contexto="temporal", es_inferida=False
        )
        assert e.tipo == "fecha"
        assert e.confianza == 0.9
        assert e.es_inferida is False

    def test_entidad_smart_defaults(self):
        e = EntidadSmart(tipo="t", valor="v", valor_original="vo", confianza=0.5)
        assert e.contexto == ""
        assert e.es_inferida is False

    def test_intencion_smart(self):
        i = IntencionSmart(
            nombre="consultar_ventas",
            confianza=0.92,
            tipo_consulta=TipoConsulta.CONSULTA_DATOS,
            especificidad=NivelEspecificidad.ESPECIFICA,
            entidades=[],
            parametros={"modelo": "sale.order"},
            accion_principal="consultar_ventas",
            acciones_secundarias=[],
            necesita_contexto=[],
            razonamiento="Detección por patrón"
        )
        assert i.nombre == "consultar_ventas"
        assert i.tipo_consulta == TipoConsulta.CONSULTA_DATOS

    def test_analisis_semantico(self):
        a = AnalisisSemantico(
            tokens_relevantes=["ventas", "mes"],
            verbos_accion=["mostrar"],
            sustantivos_clave=["ventas"],
            modificadores=["del mes"],
            temporalidad={"periodo": "mes_actual"},
            comparadores=[],
            negaciones=[],
            preguntas=False,
            sentimiento="neutro"
        )
        assert a.tokens_relevantes == ["ventas", "mes"]
        assert a.sentimiento == "neutro"

    def test_contexto_conversacional_defaults(self):
        c = ContextoConversacional()
        assert c.tema_actual is None
        assert c.modelo_actual is None
        assert c.periodo_actual is None
        assert c.entidades_mencionadas == {}
        assert c.historial_intenciones == []
        assert c.ultima_consulta is None
        assert c.preguntas_pendientes == []


# ═══════════════════════════════════════════════════════════
# TESTS DEL CEREBRO NLP
# ═══════════════════════════════════════════════════════════

class TestCerebroNLP:

    @pytest.fixture
    def cerebro(self):
        """CerebroNLP inicializado (spaCy puede o no estar disponible)."""
        return CerebroNLP()

    def test_instanciacion(self, cerebro):
        assert isinstance(cerebro, CerebroNLP)
        assert isinstance(cerebro.contexto, ContextoConversacional)

    def test_tiene_tiendas_conocidas(self, cerebro):
        assert hasattr(cerebro, 'tiendas_conocidas')
        assert isinstance(cerebro.tiendas_conocidas, dict)
        assert 'aeropuerto' in cerebro.tiendas_conocidas

    def test_tiene_respuestas_inteligentes(self, cerebro):
        assert hasattr(cerebro, 'respuestas_inteligentes')
        assert 'chistes' in cerebro.respuestas_inteligentes
        assert 'capacidades_resumen' in cerebro.respuestas_inteligentes
        assert 'despedidas' in cerebro.respuestas_inteligentes

    def test_tiene_conceptos(self, cerebro):
        assert hasattr(cerebro, 'conceptos')
        assert 'ventas' in cerebro.conceptos
        assert 'sinonimos' in cerebro.conceptos['ventas']

    def test_tienda_a_nombre_index(self, cerebro):
        assert hasattr(cerebro, 'tienda_a_nombre')
        assert 'aeropuerto' in cerebro.tienda_a_nombre
        assert cerebro.tienda_a_nombre['aeropuerto'] == 'aeropuerto'

    def test_contexto_inicial_vacio(self, cerebro):
        assert cerebro.contexto.tema_actual is None
        assert len(cerebro.contexto.historial_intenciones) == 0
