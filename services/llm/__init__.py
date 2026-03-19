# ============================================================
# MÓDULO LLM - Inteligencia Artificial Local
# ============================================================

from .cerebro_llm import (
    ConectorOllama,
    AgenteAndromeda,
    MensajeChat,
    RespuestaLLM,
    AccionDetectada,
    obtener_agente,
    reiniciar_agente
)

from .generador_queries import (
    GeneradorQueries,
    QueryOdoo,
    ResultadoQuery,
    obtener_generador_queries
)

__all__ = [
    'ConectorOllama',
    'AgenteAndromeda', 
    'MensajeChat',
    'RespuestaLLM',
    'AccionDetectada',
    'obtener_agente',
    'reiniciar_agente',
    'GeneradorQueries',
    'QueryOdoo',
    'ResultadoQuery',
    'obtener_generador_queries'
]
