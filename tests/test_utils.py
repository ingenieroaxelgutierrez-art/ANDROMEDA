# ============================================================
# ANDROMEDA — Tests de Utilidades (Validador, Normalizador, Intenciones)
# ============================================================

import re
import pytest
from datetime import datetime

from utils.validador_datos import (
    ValidadorDatos,
    TipoValidacion,
    NivelConfianza,
    ResultadoValidacion,
    MetricasCalidad,
)
from utils.normalizador_prompt import (
    NormalizadorPrompt,
    ResultadoNormalizacion,
)
from utils.intenciones_extendidas import INTENCIONES_EXTENDIDAS


# ═══════════════════════════════════════════════════════════
# TESTS DEL VALIDADOR DE DATOS
# ═══════════════════════════════════════════════════════════

class TestEnumsValidador:

    def test_tipo_validacion_valores(self):
        assert TipoValidacion.REQUERIDO.value == "required"
        assert TipoValidacion.NUMERICO.value == "numeric"
        assert TipoValidacion.POSITIVO.value == "positive"
        assert TipoValidacion.FECHA.value == "date"
        assert TipoValidacion.RANGO.value == "range"

    def test_nivel_confianza_valores(self):
        assert NivelConfianza.ALTA.value == "high"
        assert NivelConfianza.MEDIA.value == "medium"
        assert NivelConfianza.BAJA.value == "low"
        assert NivelConfianza.MUY_BAJA.value == "very_low"


class TestMetricasCalidad:

    def test_defaults(self):
        m = MetricasCalidad()
        assert m.total_registros == 0
        assert m.registros_validos == 0
        assert m.confianza_global == 100.0
        assert m.nivel_confianza == NivelConfianza.ALTA
        assert m.detalles_errores == []


class TestValidadorDatos:

    @pytest.fixture
    def validador(self):
        return ValidadorDatos()

    # --- validar_campo_requerido ---

    def test_campo_requerido_con_valor(self, validador):
        r = validador.validar_campo_requerido("texto", "nombre")
        assert r.valido is True
        assert r.campo == "nombre"

    def test_campo_requerido_none(self, validador):
        r = validador.validar_campo_requerido(None, "nombre")
        assert r.valido is False
        assert r.autocorregido is True
        assert r.valor_corregido is not None

    def test_campo_requerido_vacio(self, validador):
        r = validador.validar_campo_requerido("", "nombre")
        assert r.valido is False
        assert r.autocorregido is True

    def test_campo_requerido_lista_vacia(self, validador):
        r = validador.validar_campo_requerido([], "items")
        assert r.valido is False

    def test_campo_requerido_dict_vacio(self, validador):
        r = validador.validar_campo_requerido({}, "datos")
        assert r.valido is False

    def test_campo_requerido_tipo_amount(self, validador):
        r = validador.validar_campo_requerido(None, "total", tipo_default='amount')
        assert r.valor_corregido == 0.0

    # --- validar_numerico ---

    def test_numerico_valido_int(self, validador):
        r = validador.validar_numerico(42, "cantidad")
        assert r.valido is True

    def test_numerico_valido_float(self, validador):
        r = validador.validar_numerico(3.14, "precio")
        assert r.valido is True

    def test_numerico_string(self, validador):
        r = validador.validar_numerico("1,500", "monto")
        assert r.autocorregido is True
        assert r.valor_corregido == 1500.0

    def test_numerico_none(self, validador):
        r = validador.validar_numerico(None, "cantidad")
        assert r.autocorregido is True
        assert r.valor_corregido == 0.0

    def test_numerico_fuera_rango_minimo(self, validador):
        r = validador.validar_numerico(-10, "stock", minimo=0)
        assert r.valido is False
        assert r.valor_corregido == 0

    def test_numerico_fuera_rango_maximo(self, validador):
        r = validador.validar_numerico(200, "porcentaje", maximo=100)
        assert r.valido is False
        assert r.valor_corregido == 100

    def test_numerico_en_rango(self, validador):
        r = validador.validar_numerico(50, "porcentaje", minimo=0, maximo=100)
        assert r.valido is True

    def test_numerico_no_convertible(self, validador):
        r = validador.validar_numerico("abc", "precio")
        assert r.valido is False
        assert r.valor_corregido == 0.0

    # --- validar_fecha ---

    def test_fecha_formato_correcto(self, validador):
        r = validador.validar_fecha("2026-03-15", "fecha")
        assert r.valido is True

    def test_fecha_none(self, validador):
        r = validador.validar_fecha(None, "fecha")
        assert r.valido is False
        assert r.autocorregido is True
        assert r.valor_corregido is not None

    def test_fecha_vacia(self, validador):
        r = validador.validar_fecha("", "fecha")
        assert r.valido is False
        assert r.autocorregido is True

    def test_fecha_datetime_obj(self, validador):
        r = validador.validar_fecha(datetime(2026, 3, 15), "fecha")
        assert r.valido is True
        assert r.valor_corregido == "2026-03-15"

    def test_fecha_formato_dd_mm_yyyy(self, validador):
        r = validador.validar_fecha("15/03/2026", "fecha")
        assert r.valido is True
        assert r.valor_corregido == "2026-03-15"

    def test_fecha_formato_invalido(self, validador):
        r = validador.validar_fecha("no_es_fecha", "fecha")
        assert r.valido is False

    # --- Instanciación ---

    def test_init_sin_conector(self):
        v = ValidadorDatos()
        assert v.odoo is None
        assert v.errores_sesion == []

    def test_set_conector(self, conector_mock):
        v = ValidadorDatos()
        v.set_conector(conector_mock)
        assert v.odoo is conector_mock


# ═══════════════════════════════════════════════════════════
# TESTS DEL NORMALIZADOR DE PROMPTS
# ═══════════════════════════════════════════════════════════

class TestNormalizadorPrompt:

    @pytest.fixture
    def norm(self):
        return NormalizadorPrompt()

    def test_instanciacion(self, norm):
        assert isinstance(norm, NormalizadorPrompt)

    def test_normalizar_retorna_resultado(self, norm):
        r = norm.normalizar("hola mundo")
        assert isinstance(r, ResultadoNormalizacion)
        assert r.texto_original == "hola mundo"
        assert isinstance(r.texto_normalizado, str)
        assert isinstance(r.correcciones, list)
        assert isinstance(r.confianza_interpretacion, float)

    # --- Corrección de typos ---

    def test_corrige_venats(self, norm):
        r = norm.normalizar("dame las venats del mes")
        assert "ventas" in r.texto_normalizado

    def test_corrige_inbentario(self, norm):
        r = norm.normalizar("consulta el inbentario")
        assert "inventario" in r.texto_normalizado

    def test_corrige_factruas(self, norm):
        r = norm.normalizar("factruas pendientes")
        assert "facturas" in r.texto_normalizado

    def test_corrige_clietes(self, norm):
        r = norm.normalizar("mis clietes principales")
        assert "clientes" in r.texto_normalizado

    def test_corrige_prodcutos(self, norm):
        r = norm.normalizar("top prodcutos vendidos")
        assert "productos" in r.texto_normalizado

    def test_corrige_analsis(self, norm):
        r = norm.normalizar("analsis de tendencia")
        assert "analisis" in r.texto_normalizado

    # --- Expansión de abreviaciones ---

    def test_expande_inv(self, norm):
        r = norm.normalizar("consultar inv")
        assert "inventario" in r.texto_normalizado

    def test_expande_fac(self, norm):
        r = norm.normalizar("ver fac pendientes")
        assert "facturas" in r.texto_normalizado

    def test_expande_rrhh(self, norm):
        r = norm.normalizar("analisis de rrhh")
        assert "recursos humanos" in r.texto_normalizado

    def test_expande_pdv(self, norm):
        r = norm.normalizar("ventas del pdv")
        assert "punto de venta" in r.texto_normalizado

    # --- Coloquialismos ---

    def test_traduce_plata(self, norm):
        r = norm.normalizar("cuanta plata tenemos")
        assert "dinero" in r.texto_normalizado

    def test_traduce_lana(self, norm):
        r = norm.normalizar("cuanta lana hay")
        assert "dinero" in r.texto_normalizado

    # --- Limpieza ---

    def test_limpia_espacios_multiples(self, norm):
        r = norm.normalizar("ventas   del    mes")
        assert "  " not in r.texto_normalizado

    def test_limpia_puntuacion_excesiva(self, norm):
        r = norm.normalizar("ventas del mes???")
        assert "???" not in r.texto_normalizado

    def test_output_lowercase(self, norm):
        r = norm.normalizar("VENTAS DEL MES")
        assert r.texto_normalizado == r.texto_normalizado.lower()

    # --- Confianza ---

    def test_confianza_alta_sin_correcciones(self, norm):
        r = norm.normalizar("ventas del mes")
        assert r.confianza_interpretacion >= 0.9

    def test_confianza_disminuye_con_correcciones(self, norm):
        r = norm.normalizar("venats del mes inbentario factruas")
        assert r.confianza_interpretacion < 1.0

    # --- Fragmentos clave ---

    def test_fragmentos_clave(self, norm):
        r = norm.normalizar("dame las ventas del mes por tienda")
        assert isinstance(r.fragmentos_clave, list)


# ═══════════════════════════════════════════════════════════
# TESTS DE INTENCIONES EXTENDIDAS
# ═══════════════════════════════════════════════════════════

class TestIntencionesExtendidas:

    def test_es_diccionario(self):
        assert isinstance(INTENCIONES_EXTENDIDAS, dict)

    def test_no_esta_vacio(self):
        assert len(INTENCIONES_EXTENDIDAS) > 0

    def test_estructura_correcta(self):
        for nombre, config in INTENCIONES_EXTENDIDAS.items():
            assert 'patrones' in config, f"'{nombre}' falta 'patrones'"
            assert 'prioridad' in config, f"'{nombre}' falta 'prioridad'"
            assert 'accion' in config, f"'{nombre}' falta 'accion'"
            assert isinstance(config['patrones'], list), f"'{nombre}' patrones no es lista"
            assert isinstance(config['prioridad'], int), f"'{nombre}' prioridad no es int"

    def test_patrones_son_regex_validos(self):
        for nombre, config in INTENCIONES_EXTENDIDAS.items():
            for patron in config['patrones']:
                try:
                    re.compile(patron)
                except re.error as e:
                    pytest.fail(f"Regex inválido en '{nombre}': {patron} → {e}")

    def test_analisis_ventas_presente(self):
        assert 'analisis_ventas' in INTENCIONES_EXTENDIDAS

    def test_top_productos_presente(self):
        assert 'top_productos' in INTENCIONES_EXTENDIDAS

    def test_top_clientes_presente(self):
        assert 'top_clientes' in INTENCIONES_EXTENDIDAS

    def test_tendencia_presente(self):
        assert 'tendencia' in INTENCIONES_EXTENDIDAS

    def test_patron_analisis_ventas_match(self):
        config = INTENCIONES_EXTENDIDAS['analisis_ventas']
        texto = "análisis de ventas"
        match = any(re.search(p, texto) for p in config['patrones'])
        assert match, f"Ningún patrón de 'analisis_ventas' matchea '{texto}'"

    def test_patron_top_productos_match(self):
        config = INTENCIONES_EXTENDIDAS['top_productos']
        texto = "top 10 productos más vendidos"
        match = any(re.search(p, texto) for p in config['patrones'])
        assert match, f"Ningún patrón de 'top_productos' matchea '{texto}'"
