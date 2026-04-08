# ============================================================
# ANDROMEDA — Contratos del Sistema (typing.Protocol)
# ============================================================
# Fase 2 — Mantenibilidad y Contratos
#
# Define la "forma" esperada de cada capa del sistema usando
# typing.Protocol (duck typing estructural, sin herencia forzada).
#
# Propósito:
#   - Hacer explícito qué métodos/atributos espera cada integración
#   - Facilitar el reemplazo futuro de Odoo, Ollama o motores de ML
#   - Servir de documentación viva de los contratos entre capas
#
# NOTA: Estas interfaces NO contienen lógica. Solo contratos.
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable

import pandas as pd


# ============================================================
# CONTRATO 1 — Conector ERP (Odoo o cualquier sucesor)
# ============================================================

@runtime_checkable
class ConectorOdooBase(Protocol):
    """
    Contrato para cualquier conector de ERP.

    Implementado actualmente por: `models.conector_odoo.ConectorOdoo`
    Si en el futuro se migra a SAP, ERPNext u otro ERP, solo hay
    que reimplementar este protocolo en un nuevo módulo.
    """

    conectado: bool

    def conectar(self) -> Tuple[bool, str]:
        """
        Establece la conexión con el ERP.

        Returns:
            (éxito: bool, mensaje: str)
        """
        ...

    def desconectar(self) -> None:
        """Cierra la conexión activa."""
        ...

    def buscar(
        self,
        modelo: str,
        filtros: Optional[List] = None,
        campos: Optional[List[str]] = None,
        limite: int = 100,
        orden: Optional[str] = None,
        hash_prompt: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Consulta de solo-lectura que retorna un DataFrame.

        Args:
            modelo:     Nombre del modelo ERP (p. ej. 'sale.order')
            filtros:    Dominio de filtros (lista de tuplas Odoo)
            campos:     Campos a obtener; None = todos los default
            limite:     Máximo de registros
            orden:      Campo de ordenamiento ('date_order desc')
            hash_prompt: Hash SHA-256 del prompt que originó la consulta
            prompt:     Texto del prompt; si se provee, se firma automáticamente
        """
        ...

    def buscar_leer(
        self,
        modelo: str,
        filtros: Optional[List] = None,
        campos: Optional[List[str]] = None,
        limite: int = 100,
        orden: Optional[str] = None,
        hash_prompt: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Consulta de solo-lectura que retorna lista de dicts.
        Equivale al search_read de Odoo RPC.
        """
        ...


# ============================================================
# CONTRATO 2 — Agente Especializado (multi-agente)
# ============================================================

@runtime_checkable
class AgenteEspecializadoProtocol(Protocol):
    """
    Contrato para agentes especializados del sistema multi-agente.

    Implementado por: `AgenteEspecializadoBase` y sus 12 subclases
    en `services.agents.multi_agente`.

    Cada agente representa un dominio de negocio (ventas, inventario,
    finanzas, etc.) y puede pre-validar, ejecutar y enriquecer respuestas.
    """

    id_agente: str
    prompt_base: str

    def score_prompt(self, mensaje: str) -> float:
        """
        Retorna un score 0.0–1.0 que indica cuánto encaja este agente
        con el mensaje del usuario. Usado por el GestorMultiAgente para
        seleccionar el agente más apropiado.
        """
        ...

    def soporta_accion(self, accion: str) -> bool:
        """Indica si este agente soporta la acción dada."""
        ...

    def pre_ejecucion(self, consulta: Any, mensaje: str) -> Any:
        """
        Valida si la consulta puede ejecutarse.
        Retorna ResultadoPreEjecucion con flag `permitido`.
        Puede bloquear consultas fuera del dominio del agente.
        """
        ...

    def ejecutar(
        self,
        consulta: Any,
        mensaje: str,
        ejecutor: Any,
    ) -> Tuple[str, Any]:
        """
        Ejecuta la consulta delegando al ejecutor registrado por la UI.
        Retorna (respuesta: str, df: DataFrame | None).
        """
        ...

    def enriquecer_respuesta(
        self,
        consulta: Any,
        respuesta: str,
        df: Any,
        mensaje: str = "",
    ) -> str:
        """
        Hook post-ejecución para añadir análisis determinista
        sobre los datos reales ya obtenidos. No debe inventar datos.
        """
        ...

    def post_ejecucion(
        self,
        consulta: Any,
        respuesta: str,
        df: Any,
        error: bool = False,
    ) -> Any:
        """
        Validación final de la respuesta generada.
        Retorna ResultadoPostEjecucion con confianza ajustada.
        """
        ...


# ============================================================
# CONTRATO 3 — Motor de Predicción
# ============================================================

@runtime_checkable
class MotorPrediccionBase(Protocol):
    """
    Contrato para cualquier motor de predicción/forecasting.

    Implementado actualmente por:
        - `services.prediction.motor_prediccion.MotorPrediccion`  (series de tiempo)
        - `services.prediction.motor_ml.MotorML`                  (ML clásico)
        - `services.prediction.neural_lstm.MotorNeuralLSTM`        (LSTM/PyTorch)

    Si en el futuro se integra Prophet, XGBoost u otro framework,
    debe cumplir este contrato.
    """

    def set_conector(self, conector: ConectorOdooBase) -> None:
        """Inyecta el conector ERP para acceso a datos históricos."""
        ...

    def predecir_ventas(self, dias_futuro: int = 7) -> Any:
        """
        Predice ventas para los próximos `dias_futuro` días.
        Retorna un objeto Prediccion con: valor_predicho, tendencia,
        confianza, insights y alertas.
        """
        ...

    def predecir_agotamiento(self, producto_id: int = None, top: int = 20) -> Any:
        """
        Estima el nivel de stock futuro y riesgo de agotamiento.
        Retorna un dict con productos en riesgo, días restantes y alertas de reposición.
        """
        ...


# ============================================================
# CONTRATO 4 — Conector LLM
# ============================================================

@runtime_checkable
class ConectorLLMBase(Protocol):
    """
    Contrato para cualquier conector de modelo de lenguaje.

    Implementado actualmente por:
        - `services.llm.cerebro_llm.ConectorOllama`  (Ollama local)
        - `services.llm.ollama_integrador.OllamaIntegrador` (integrador extendido)

    Si en el futuro se integra OpenAI, Anthropic, Gemini u otro LLM,
    debe cumplir este contrato.
    """

    disponible: bool

    def generar(
        self,
        prompt: str,
        modelo: Optional[str] = None,
        temperatura: float = 0.3,
        max_tokens: int = 1024,
    ) -> Any:
        """
        Genera texto a partir de un prompt.

        Args:
            prompt:       Texto de entrada
            modelo:       Nombre del modelo a usar; None = default
            temperatura:  Creatividad (0.0 = determinista, 1.0 = creativo)
            max_tokens:   Límite de tokens en la respuesta

        Returns:
            RespuestaLLM con campos: contenido, exito, error, tokens_usados
        """
        ...

    def esta_disponible(self) -> bool:
        """
        Verifica si el servicio LLM está activo y responde.
        Debe ser rápido (timeout corto) para no bloquear el pipeline.
        """
        ...
