# ============================================================
# ANDROMEDA — Tests del Sistema Multi-Agente
# ============================================================

import pytest
import pandas as pd
from unittest.mock import MagicMock

from services.agents.multi_agente import (
    GestorMultiAgente,
    AgenteEspecializadoBase,
    AgentVentas,
    AgentInventarios,
    AgentFinanzas,
    AgentDiagnostico,
    AgentConsultasOdoo,
    AgentCRM,
    AgentCompras,
    AgentPDV,
    AgentPredicciones,
    AgentMatematicas,
    AgentEstadistica,
    AgentRRHH,
    AgentValidadorFinal,
    ResultadoPreEjecucion,
    ResultadoPostEjecucion,
    PasoAgente,
    ResultadoCadena,
)


# ═══════════════════════════════════════════════════════════
# TESTS DE DATACLASSES
# ═══════════════════════════════════════════════════════════

class TestDataclasses:

    def test_resultado_pre_ejecucion_defaults(self):
        r = ResultadoPreEjecucion(permitido=True, consulta=None)
        assert r.permitido is True
        assert r.advertencias == []
        assert r.motivo_bloqueo == ""
        assert r.requiere_confirmacion is False
        assert r.confianza_agente == 0.0

    def test_resultado_post_ejecucion(self):
        r = ResultadoPostEjecucion(respuesta="test", confianza_datos=0.85)
        assert r.respuesta == "test"
        assert r.confianza_datos == 0.85
        assert r.observaciones == []

    def test_paso_agente_defaults(self):
        p = PasoAgente(agente_id="agente_ventas", rol="principal")
        assert p.agente_id == "agente_ventas"
        assert p.rol == "principal"
        assert p.exito is True
        assert p.confianza == 0.0
        assert p.error == ""

    def test_resultado_cadena_defaults(self):
        r = ResultadoCadena(respuesta_final="ok", confianza_consolidada=0.88)
        assert r.respuesta_final == "ok"
        assert r.confianza_consolidada == 0.88
        assert r.agentes_involucrados == []
        assert r.pasos == []


# ═══════════════════════════════════════════════════════════
# TESTS DE AGENTES INDIVIDUALES
# ═══════════════════════════════════════════════════════════

class TestAgenteBase:

    def test_instanciacion(self):
        agente = AgenteEspecializadoBase()
        assert agente.id_agente == "agente_base"
        assert isinstance(agente.acciones_soportadas, set)
        assert isinstance(agente.palabras_clave_prompt, set)

    def test_soporta_accion_false(self):
        agente = AgenteEspecializadoBase()
        assert agente.soporta_accion("accion_inexistente") is False

    def test_score_prompt_sin_keywords(self):
        agente = AgenteEspecializadoBase()
        score = agente.score_prompt("hola mundo")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


class TestAgentVentas:

    def test_id_agente(self):
        agente = AgentVentas()
        assert agente.id_agente == "agente_ventas"

    def test_acciones_soportadas_no_vacia(self):
        agente = AgentVentas()
        assert len(agente.acciones_soportadas) > 0

    def test_soporta_consultar_ventas(self):
        agente = AgentVentas()
        assert agente.soporta_accion("consultar_ventas") is True

    def test_soporta_analisis_ventas(self):
        agente = AgentVentas()
        assert agente.soporta_accion("analisis_ventas") is True

    def test_no_soporta_inventario(self):
        agente = AgentVentas()
        assert agente.soporta_accion("consultar_inventario") is False

    def test_score_prompt_alto_para_ventas(self):
        agente = AgentVentas()
        score = agente.score_prompt("quiero ver las ventas del mes")
        assert score > 0.0

    def test_keywords_contiene_venta(self):
        agente = AgentVentas()
        assert any('venta' in kw for kw in agente.palabras_clave_prompt)

    def test_pre_ejecucion_retorna_resultado(self, consulta_ventas):
        agente = AgentVentas()
        resultado = agente.pre_ejecucion(consulta_ventas, "dame las ventas del mes")
        assert isinstance(resultado, ResultadoPreEjecucion)
        assert resultado.permitido is True

    def test_post_ejecucion_retorna_resultado(self, consulta_ventas, df_ventas):
        agente = AgentVentas()
        resultado = agente.post_ejecucion(consulta_ventas, "Ventas: $10,000", df_ventas)
        assert isinstance(resultado, ResultadoPostEjecucion)
        assert isinstance(resultado.confianza_datos, float)

    def test_enriquecer_respuesta_con_datos(self, consulta_ventas, df_ventas):
        agente = AgentVentas()
        respuesta_original = "Las ventas fueron de $10,300"
        resultado = agente.enriquecer_respuesta(consulta_ventas, respuesta_original, df_ventas)
        assert isinstance(resultado, str)
        assert len(resultado) >= len(respuesta_original)

    def test_enriquecer_respuesta_sin_df(self, consulta_ventas):
        agente = AgentVentas()
        resp = "Las ventas fueron de $10,000"
        resultado = agente.enriquecer_respuesta(consulta_ventas, resp, None)
        assert resultado == resp


class TestAgentInventarios:

    def test_id_agente(self):
        assert AgentInventarios().id_agente == "agente_inventario"

    def test_soporta_consultar_inventario(self):
        assert AgentInventarios().soporta_accion("consultar_inventario") is True

    def test_soporta_abc_inventario(self):
        assert AgentInventarios().soporta_accion("abc_inventario") is True

    def test_enriquecer_con_stock_negativo(self, consulta_inventario, df_inventario):
        agente = AgentInventarios()
        resp = "Stock disponible"
        resultado = agente.enriquecer_respuesta(consulta_inventario, resp, df_inventario)
        assert isinstance(resultado, str)


class TestAgentFinanzas:

    def test_id_agente(self):
        assert AgentFinanzas().id_agente == "agente_finanzas"

    def test_soporta_facturacion(self):
        agente = AgentFinanzas()
        assert agente.soporta_accion("consultar_facturas") is True

    def test_enriquecer_con_facturas(self, consulta_ventas, df_facturas):
        agente = AgentFinanzas()
        resultado = agente.enriquecer_respuesta(consulta_ventas, "Facturas pendientes", df_facturas)
        assert isinstance(resultado, str)


class TestAgentCRM:

    def test_id_agente(self):
        assert AgentCRM().id_agente == "agente_crm"

    def test_soporta_pipeline(self):
        assert AgentCRM().soporta_accion("pipeline_etapas") is True

    def test_enriquecer_con_oportunidades(self, consulta_crm, df_crm):
        agente = AgentCRM()
        resultado = agente.enriquecer_respuesta(consulta_crm, "Pipeline CRM", df_crm)
        assert isinstance(resultado, str)


class TestAgentCompras:

    def test_id_agente(self):
        assert AgentCompras().id_agente == "agente_compras"

    def test_soporta_evaluacion_proveedores(self):
        assert AgentCompras().soporta_accion("evaluacion_proveedores") is True


class TestAgentPDV:

    def test_id_agente(self):
        assert AgentPDV().id_agente == "agente_pdv"

    def test_soporta_pos(self):
        assert AgentPDV().soporta_accion("analisis_pos") is True


class TestAgentPredicciones:

    def test_id_agente(self):
        assert AgentPredicciones().id_agente == "agente_predicciones"

    def test_soporta_forecast(self):
        assert AgentPredicciones().soporta_accion("forecast_estacional") is True


class TestAgentMatematicas:

    def test_id_agente(self):
        assert AgentMatematicas().id_agente == "agente_matematicas"


class TestAgentEstadistica:

    def test_id_agente(self):
        assert AgentEstadistica().id_agente == "agente_estadistica"

    def test_soporta_score_salud(self):
        assert AgentEstadistica().soporta_accion("score_salud_negocio") is True


class TestAgentRRHH:

    def test_id_agente(self):
        assert AgentRRHH().id_agente == "agente_rrhh"

    def test_soporta_nomina(self):
        assert AgentRRHH().soporta_accion("nomina") is True


class TestAgentDiagnostico:

    def test_id_agente(self):
        assert AgentDiagnostico().id_agente == "agente_diagnostico"


class TestAgentConsultasOdoo:

    def test_id_agente(self):
        assert AgentConsultasOdoo().id_agente == "agente_odoo"


class TestAgentValidadorFinal:

    def test_id_agente(self):
        assert AgentValidadorFinal().id_agente == "agente_validador_final"

    def test_post_ejecucion_respuesta_vacia(self, consulta_ventas):
        agente = AgentValidadorFinal()
        resultado = agente.post_ejecucion(consulta_ventas, "", None, error=False)
        assert isinstance(resultado, ResultadoPostEjecucion)
        assert resultado.confianza_datos < 0.8

    def test_post_ejecucion_respuesta_normal(self, consulta_ventas, df_ventas):
        agente = AgentValidadorFinal()
        resultado = agente.post_ejecucion(
            consulta_ventas,
            "Las ventas del mes fueron de $10,300 con 5 órdenes registradas.",
            df_ventas
        )
        assert isinstance(resultado, ResultadoPostEjecucion)


# ═══════════════════════════════════════════════════════════
# TESTS DEL GESTOR MULTI-AGENTE
# ═══════════════════════════════════════════════════════════

class TestGestorMultiAgente:

    def test_instanciacion(self, gestor):
        assert isinstance(gestor, GestorMultiAgente)
        assert len(gestor.agentes) >= 12

    def test_todos_los_agentes_registrados(self, gestor):
        ids_esperados = {
            'agente_ventas', 'agente_inventario', 'agente_finanzas',
            'agente_diagnostico', 'agente_odoo', 'agente_crm',
            'agente_compras', 'agente_pdv', 'agente_predicciones',
            'agente_matematicas', 'agente_estadistica', 'agente_rrhh',
            'agente_validador_final',
        }
        for aid in ids_esperados:
            assert aid in gestor.agentes, f"Agente {aid} no registrado"

    def test_resolver_agente_ventas(self, gestor):
        agente_id, confianza, prompt = gestor.resolver_agente(
            "consultar_ventas", "dame las ventas del mes"
        )
        assert agente_id == "agente_ventas"
        assert confianza > 0.0
        assert isinstance(prompt, str)

    def test_resolver_agente_inventario(self, gestor):
        agente_id, confianza, prompt = gestor.resolver_agente(
            "consultar_inventario", "stock disponible"
        )
        assert agente_id == "agente_inventario"

    def test_resolver_agente_finanzas(self, gestor):
        agente_id, _, _ = gestor.resolver_agente(
            "consultar_facturas", "facturas pendientes"
        )
        assert agente_id == "agente_finanzas"

    def test_resolver_agente_crm(self, gestor):
        agente_id, _, _ = gestor.resolver_agente(
            "pipeline_etapas", "pipeline de oportunidades"
        )
        assert agente_id == "agente_crm"

    def test_resolver_agente_compras(self, gestor):
        agente_id, _, _ = gestor.resolver_agente(
            "evaluacion_proveedores", "evaluar proveedores"
        )
        assert agente_id == "agente_compras"

    def test_resolver_agente_pdv(self, gestor):
        agente_id, _, _ = gestor.resolver_agente(
            "analisis_pos", "ventas del punto de venta"
        )
        assert agente_id == "agente_pdv"

    def test_resolver_agente_rrhh(self, gestor):
        agente_id, _, _ = gestor.resolver_agente(
            "nomina_analytics", "analisis de nómina"
        )
        assert agente_id == "agente_rrhh"

    def test_resolver_agente_confianza_rango(self, gestor):
        _, confianza, _ = gestor.resolver_agente("consultar_ventas", "ventas")
        assert 0.0 <= confianza <= 1.0

    def test_pre_ejecutar(self, gestor, consulta_ventas):
        resultado = gestor.pre_ejecutar("agente_ventas", consulta_ventas, "ventas del mes")
        assert isinstance(resultado, ResultadoPreEjecucion)
        assert resultado.permitido is True

    def test_post_ejecutar(self, gestor, consulta_ventas, df_ventas):
        resultado = gestor.post_ejecutar(
            "agente_ventas", consulta_ventas,
            "Las ventas del mes fueron $10,300", df_ventas
        )
        assert isinstance(resultado, ResultadoPostEjecucion)
        assert isinstance(resultado.respuesta, str)
        assert 0.0 <= resultado.confianza_datos <= 1.0

    def test_post_ejecutar_con_error(self, gestor, consulta_ventas):
        resultado = gestor.post_ejecutar(
            "agente_ventas", consulta_ventas,
            "Error al procesar", None, error=True
        )
        assert isinstance(resultado, ResultadoPostEjecucion)

    def test_prompt_base(self, gestor):
        prompt = gestor.prompt_base("agente_ventas")
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestGestorRegistroEjecutores:

    def test_registrar_ejecutor(self, gestor):
        mock_fn = MagicMock(return_value=("resultado", None))
        gestor.registrar_ejecutor("agente_ventas", mock_fn)
        assert "agente_ventas" in gestor.ejecutores_por_agente

    def test_registrar_ejecutor_default(self, gestor):
        mock_fn = MagicMock(return_value=("fallback", None))
        gestor.registrar_ejecutor_default(mock_fn)
        assert gestor.ejecutor_default is not None

    def test_ejecutar_accion_usa_executor_registrado(self, gestor, consulta_ventas):
        mock_fn = MagicMock(return_value=("resp mock", pd.DataFrame()))
        gestor.registrar_ejecutor("agente_ventas", mock_fn)
        resp, df = gestor.ejecutar_accion("agente_ventas", consulta_ventas, "ventas")
        mock_fn.assert_called_once()
        assert resp == "resp mock"

    def test_ejecutar_accion_usa_default_si_no_hay_registro(self, gestor, consulta_ventas):
        mock_default = MagicMock(return_value=("default resp", None))
        gestor.registrar_ejecutor_default(mock_default)
        resp, df = gestor.ejecutar_accion("agente_inexistente", consulta_ventas, "test")
        mock_default.assert_called_once()


# ═══════════════════════════════════════════════════════════
# TESTS DE CADENA MULTI-AGENTE
# ═══════════════════════════════════════════════════════════

class TestCadenaMultiAgente:

    def test_es_cadena_con_tendencia(self, gestor):
        resultado = gestor.es_cadena(
            "ventas por marca y su tendencia",
            "analisis_ventas",
            "agente_ventas"
        )
        assert isinstance(resultado, bool)

    def test_planificar_cadena_retorna_pasos(self, gestor):
        pasos = gestor.planificar_cadena(
            "ventas por marca y su tendencia",
            "analisis_ventas",
            "agente_ventas"
        )
        assert isinstance(pasos, list)
        if len(pasos) > 0:
            assert isinstance(pasos[0], PasoAgente)
            assert pasos[0].rol == "principal"

    def test_cadena_principal_siempre_primero(self, gestor):
        pasos = gestor.planificar_cadena(
            "análisis completo de ventas con predicción",
            "analisis_ventas",
            "agente_ventas"
        )
        if pasos:
            assert pasos[0].agente_id == "agente_ventas"
            assert pasos[0].rol == "principal"

    def test_pre_ejecutar_cadena(self, gestor, consulta_ventas):
        pasos = [
            PasoAgente(agente_id="agente_ventas", rol="principal"),
            PasoAgente(agente_id="agente_estadistica", rol="enriquecimiento"),
        ]
        resultado = gestor.pre_ejecutar_cadena(pasos, consulta_ventas, "ventas")
        assert isinstance(resultado, list)
        assert len(resultado) == 2
        for paso in resultado:
            assert paso.resultado_pre is not None

    def test_post_ejecutar_cadena(self, gestor, consulta_ventas, df_ventas):
        pasos = [
            PasoAgente(agente_id="agente_ventas", rol="principal"),
            PasoAgente(agente_id="agente_estadistica", rol="enriquecimiento"),
        ]
        resultado = gestor.post_ejecutar_cadena(
            pasos, consulta_ventas, "Ventas: $10,300", df_ventas
        )
        assert isinstance(resultado, ResultadoCadena)
        assert isinstance(resultado.respuesta_final, str)
        assert 0.0 <= resultado.confianza_consolidada <= 1.0

    def test_resumen_cadena(self, gestor):
        resultado = ResultadoCadena(
            respuesta_final="Resultado consolidado",
            confianza_consolidada=0.88,
            agentes_involucrados=["agente_ventas", "agente_estadistica"],
            pasos=[
                PasoAgente(agente_id="agente_ventas", rol="principal", confianza=0.92, exito=True),
                PasoAgente(agente_id="agente_estadistica", rol="enriquecimiento", confianza=0.85, exito=True),
            ]
        )
        resumen = gestor.resumen_cadena(resultado)
        assert isinstance(resumen, str)
        assert "agente_ventas" in resumen or "ventas" in resumen.lower()

    def test_obtener_prompts_cadena(self, gestor):
        pasos = [
            PasoAgente(agente_id="agente_ventas", rol="principal"),
            PasoAgente(agente_id="agente_estadistica", rol="enriquecimiento"),
        ]
        prompt = gestor.obtener_prompts_cadena(pasos)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_ejecutar_cadena_completa(self, gestor, consulta_ventas, df_ventas):
        pasos = [
            PasoAgente(agente_id="agente_ventas", rol="principal"),
            PasoAgente(agente_id="agente_estadistica", rol="enriquecimiento"),
        ]
        mock_exec = MagicMock(return_value=("resp estadistica", df_ventas))
        gestor.registrar_ejecutor("agente_estadistica", mock_exec)
        gestor.registrar_ejecutor_default(MagicMock(return_value=("default", None)))

        resultado = gestor.ejecutar_cadena_completa(
            pasos, consulta_ventas, "ventas",
            respuesta_principal="Ventas: $10,300",
            df_principal=df_ventas
        )
        assert isinstance(resultado, ResultadoCadena)
        assert isinstance(resultado.respuesta_final, str)
        assert 0.0 <= resultado.confianza_consolidada <= 1.0


# ═══════════════════════════════════════════════════════════
# TESTS DE COBERTURA CRUZADA (todos los agentes)
# ═══════════════════════════════════════════════════════════

class TestCoberturaTodosAgentes:
    """Verifica que TODOS los agentes tienen estructura correcta."""

    AGENTES = [
        AgentVentas, AgentInventarios, AgentFinanzas, AgentDiagnostico,
        AgentConsultasOdoo, AgentCRM, AgentCompras, AgentPDV,
        AgentPredicciones, AgentMatematicas, AgentEstadistica, AgentRRHH,
        AgentValidadorFinal,
    ]

    # Agentes que NO tienen acciones propias (son agentes de validación/meta)
    AGENTES_SIN_ACCIONES = {AgentValidadorFinal}

    @pytest.mark.parametrize("AgentClass", AGENTES)
    def test_hereda_de_base(self, AgentClass):
        assert issubclass(AgentClass, AgenteEspecializadoBase)

    @pytest.mark.parametrize("AgentClass", AGENTES)
    def test_tiene_id_agente(self, AgentClass):
        agente = AgentClass()
        assert isinstance(agente.id_agente, str)
        assert agente.id_agente != "agente_base"

    @pytest.mark.parametrize("AgentClass", AGENTES)
    def test_tiene_prompt_base(self, AgentClass):
        agente = AgentClass()
        assert isinstance(agente.prompt_base, str)
        assert len(agente.prompt_base) > 10

    @pytest.mark.parametrize("AgentClass", AGENTES)
    def test_tiene_acciones_soportadas(self, AgentClass):
        agente = AgentClass()
        assert isinstance(agente.acciones_soportadas, set)
        if AgentClass not in self.AGENTES_SIN_ACCIONES:
            assert len(agente.acciones_soportadas) > 0

    @pytest.mark.parametrize("AgentClass", AGENTES)
    def test_tiene_keywords(self, AgentClass):
        agente = AgentClass()
        assert isinstance(agente.palabras_clave_prompt, set)

    @pytest.mark.parametrize("AgentClass", AGENTES)
    def test_pre_ejecucion_no_falla(self, AgentClass, consulta_ventas):
        agente = AgentClass()
        resultado = agente.pre_ejecucion(consulta_ventas, "test")
        assert isinstance(resultado, ResultadoPreEjecucion)

    @pytest.mark.parametrize("AgentClass", AGENTES)
    def test_post_ejecucion_no_falla(self, AgentClass, consulta_ventas):
        agente = AgentClass()
        resultado = agente.post_ejecucion(consulta_ventas, "respuesta test", None)
        assert isinstance(resultado, ResultadoPostEjecucion)

    @pytest.mark.parametrize("AgentClass", AGENTES)
    def test_score_prompt_retorna_float(self, AgentClass):
        agente = AgentClass()
        score = agente.score_prompt("analisis de ventas inventario")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
