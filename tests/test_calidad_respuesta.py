# ============================================================
# ANDROMEDA — Tests de Calidad de Respuesta IA
# ============================================================
import pytest
from services.nlp.cerebro_nlp import CerebroNLP

# Golden set: preguntas y respuestas esperadas (simplificado)
GOLDEN_SET = [
    {
        "pregunta": "¿Cuáles fueron las ventas totales del mes pasado?",
        "esperado": ["ventas", "mes", "total"],
    },
    {
        "pregunta": "Dame un resumen de los productos más vendidos en enero",
        "esperado": ["productos", "vendidos", "enero"],
    },
    {
        "pregunta": "¿Cuántos clientes nuevos hubo este año?",
        "esperado": ["clientes", "nuevos", "año"],
    },
]

@pytest.mark.parametrize("caso", GOLDEN_SET)
def test_respuesta_no_vacia_y_relevante(caso):
    nlp = CerebroNLP()
    intencion = nlp.analizar(caso["pregunta"])
    respuesta = nlp.explicar_intencion(intencion)
    # No debe ser vacía
    assert respuesta and respuesta.strip(), f"Respuesta vacía para: {caso['pregunta']}"
    # No debe contener frases de alucinación conocidas
    for frase in ["no tengo información", "no sé", "no puedo responder", "alucinación"]:
        assert frase not in respuesta.lower(), f"Alucinación detectada en: {respuesta}"
    # Debe contener al menos una palabra clave esperada
    assert any(pal in respuesta.lower() for pal in caso["esperado"]), f"Respuesta irrelevante: {respuesta}"

# Test de cobertura de intenciones
@pytest.mark.parametrize("pregunta", [
    "¿Qué es ANDROMEDA?",
    "Cuéntame un chiste",
    "¿Puedes generar un reporte de ventas?",
    "¿Cuál es el inventario actual?",
    "¿Cómo está la tendencia de ventas?",
    "¿Quién es el mejor vendedor del mes?",
    "Analisis de datos de invetario",
])
def test_cobertura_intenciones(pregunta):
    nlp = CerebroNLP()
    intencion = nlp.analizar(pregunta)
    respuesta = nlp.explicar_intencion(intencion)
    assert respuesta and len(respuesta) > 10, f"Respuesta muy corta o vacía para: {pregunta}"
    # No debe ser una respuesta genérica tipo "No sé"
    assert "no sé" not in respuesta.lower(), f"Respuesta genérica para: {pregunta}"
