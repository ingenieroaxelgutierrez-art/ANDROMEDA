# ============================================================
# ANDROMEDA — Tests de services/analysis (kpis_empresariales)
# ============================================================

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════
# TESTS DE Dataclasses y Enums
# ═══════════════════════════════════════════════════════════

class TestEnumsYDataclasses:

    def test_categoria_kpi_valores(self):
        from services.analysis.kpis_empresariales import CategoriaKPI
        assert CategoriaKPI.COMERCIAL is not None
        assert CategoriaKPI.TALENTO is not None
        assert CategoriaKPI.OPERACIONES is not None
        assert CategoriaKPI.TIENDAS is not None
        assert CategoriaKPI.COMPRAS is not None

    def test_tipo_agrupacion_valores(self):
        from services.analysis.kpis_empresariales import TipoAgrupacion
        # Verificar que el enum existe y tiene miembros
        assert len(TipoAgrupacion) > 0

    def test_resultado_kpi_defaults(self):
        from services.analysis.kpis_empresariales import ResultadoKPI, CategoriaKPI
        r = ResultadoKPI(nombre="test", categoria=CategoriaKPI.COMERCIAL, valor=100)
        assert r.nombre == "test"
        assert r.valor == 100
        assert r.unidad == ""
        assert r.tendencia == ""
        assert r.variacion_porcentual == pytest.approx(0.0)
        assert r.detalles == {}
        assert r.datos is None
        assert r.alertas == []
        assert r.recomendaciones == []
        assert r.error is None

    def test_resultado_kpi_con_todos_campos(self):
        from services.analysis.kpis_empresariales import ResultadoKPI, CategoriaKPI
        df = pd.DataFrame({'a': [1, 2]})
        r = ResultadoKPI(
            nombre="ventas",
            categoria=CategoriaKPI.COMERCIAL,
            valor=5000.0,
            unidad="MXN",
            tendencia="↑",
            variacion_porcentual=12.5,
            periodo="2024-01",
            detalles={"canal": "POS"},
            datos=df,
            alertas=["Alerta1"],
            recomendaciones=["Rec1"],
            meta=6000.0,
            cumplimiento=83.3,
            estado="regular"
        )
        assert r.valor == pytest.approx(5000.0)
        assert r.unidad == "MXN"
        assert r.tendencia == "↑"
        assert r.meta == pytest.approx(6000.0)
        assert len(r.alertas) == 1
        assert len(r.datos) == 2

    def test_config_kpi_defaults(self):
        from services.analysis.kpis_empresariales import ConfigKPI
        c = ConfigKPI()
        assert c.fecha_inicio is None
        assert c.fecha_fin is None
        assert c.tiendas == []
        assert c.comparar_periodo_anterior is True
        assert c.incluir_proyecciones is False


# ═══════════════════════════════════════════════════════════
# TESTS DE MotorKPIsEmpresariales
# ═══════════════════════════════════════════════════════════

class TestMotorKPIsEmpresariales:

    def _crear_motor(self, conector=None):
        from services.analysis.kpis_empresariales import MotorKPIsEmpresariales
        return MotorKPIsEmpresariales(conector_odoo=conector)

    def test_init_sin_conector(self):
        motor = self._crear_motor()
        assert motor.conector is None
        assert len(motor.kpis_disponibles) > 20

    def test_init_con_conector(self):
        mock_con = MagicMock()
        motor = self._crear_motor(mock_con)
        assert motor.conector is mock_con

    def test_set_conector(self):
        motor = self._crear_motor()
        mock_con = MagicMock()
        motor.set_conector(mock_con)
        assert motor.conector is mock_con

    def test_listar_kpis_todos(self):
        motor = self._crear_motor()
        resultado = motor.listar_kpis()
        assert isinstance(resultado, dict)
        assert len(resultado) > 0

    def test_listar_kpis_por_categoria(self):
        from services.analysis.kpis_empresariales import CategoriaKPI
        motor = self._crear_motor()
        resultado = motor.listar_kpis(CategoriaKPI.COMERCIAL)
        assert isinstance(resultado, dict)

    def test_ejecutar_kpi_sin_conector(self):
        motor = self._crear_motor()
        resultado = motor.ejecutar_kpi('ventas_mensuales')
        assert resultado.error is not None or resultado.valor is not None

    def test_ejecutar_kpi_ventas_mensuales(self):
        mock_con = MagicMock()
        # Simular datos de ventas
        df_ventas = pd.DataFrame({
            'id': [1, 2, 3],
            'amount_total': [1000.0, 2000.0, 1500.0],
            'date_order': ['2024-01-15', '2024-01-20', '2024-01-25'],
            'state': ['sale', 'sale', 'sale']
        })
        mock_con.buscar.return_value = df_ventas
        motor = self._crear_motor(mock_con)
        resultado = motor.ejecutar_kpi('ventas_mensuales')
        assert resultado is not None
        assert 'ventas' in resultado.nombre.lower() or 'Ventas' in resultado.nombre

    def test_ejecutar_kpi_nombre_invalido(self):
        motor = self._crear_motor()
        resultado = motor.ejecutar_kpi('kpi_inexistente')
        assert resultado.error is not None

    def test_ejecutar_categoria(self):
        from services.analysis.kpis_empresariales import CategoriaKPI
        mock_con = MagicMock()
        mock_con.buscar.return_value = pd.DataFrame()
        motor = self._crear_motor(mock_con)
        resultados = motor.ejecutar_categoria(CategoriaKPI.COMERCIAL)
        assert isinstance(resultados, list)

    def test_generar_dashboard_completo(self):
        mock_con = MagicMock()
        mock_con.buscar.return_value = pd.DataFrame()
        motor = self._crear_motor(mock_con)
        dashboard = motor.generar_dashboard_completo()
        assert isinstance(dashboard, dict)

    def test_emoji_categoria(self):
        from services.analysis.kpis_empresariales import CategoriaKPI
        motor = self._crear_motor()
        emoji = motor._emoji_categoria(CategoriaKPI.COMERCIAL)
        assert isinstance(emoji, str)

    def test_resultado_a_dict(self):
        from services.analysis.kpis_empresariales import ResultadoKPI, CategoriaKPI
        motor = self._crear_motor()
        r = ResultadoKPI(nombre="test", categoria=CategoriaKPI.COMERCIAL, valor=100)
        d = motor._resultado_a_dict(r)
        assert isinstance(d, dict)
        assert 'nombre' in d or 'valor' in d


# ═══════════════════════════════════════════════════════════
# TESTS DE analizador_datos.py
# ═══════════════════════════════════════════════════════════

class TestAnalizadorDatos:

    def test_import(self):
        from services.analysis.analizador_datos import AnalizadorDatos
        assert AnalizadorDatos is not None

    def test_init(self):
        from services.analysis.analizador_datos import AnalizadorDatos
        a = AnalizadorDatos()
        assert a is not None


# ═══════════════════════════════════════════════════════════
# TESTS DE analizador_anomalias.py
# ═══════════════════════════════════════════════════════════

class TestAnalizadorAnomalias:

    def test_import(self):
        from services.analysis.analizador_anomalias import AnalizadorAnomalias
        assert AnalizadorAnomalias is not None

    def test_init(self):
        from services.analysis.analizador_anomalias import AnalizadorAnomalias
        a = AnalizadorAnomalias()
        assert a is not None
