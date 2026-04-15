# ============================================================
# ANDROMEDA v5.0 - IA PREDICTIVA EMPRESARIAL PARA ODOO
# Advanced Neural Data Resource for Operations, 
# Management & Enterprise Decision Analytics
# ============================================================
# - Predicciones de ventas, inventario, flujo de caja
# - NLP avanzado con comprensión contextual
# - Análisis pasado, presente y futuro
# - Generación de cualquier análisis con lenguaje natural
# ============================================================

import os
import sys
import re
import base64
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd

# Agregar el directorio raíz al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Cargar logo como base64
def cargar_logo_base64():
    """Cargar logo.png y convertirlo a base64 para embeber en HTML."""
    try:
        # Buscar logo en assets o en raíz
        logo_paths = [
            os.path.join(BASE_DIR, 'assets', 'logo.png'),
            os.path.join(BASE_DIR, 'logo.png'),
        ]
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_bytes = f.read()
                    logo_b64 = base64.b64encode(logo_bytes).decode('utf-8')
                    return f"data:image/png;base64,{logo_b64}"
    except Exception as e:
        print(f"No se pudo cargar logo: {e}")
    return None

LOGO_BASE64 = cargar_logo_base64()

# Importar componentes - Nueva estructura
from models.conector_odoo import ConectorOdoo
from views.generador_reportes import GeneradorReportes
from services.analysis.analizador_avanzado import AnalizadorAvanzado
from services.prediction.motor_prediccion import MotorPrediccion
from services.nlp.nlp_avanzado import MotorNLPAvanzado, ConsultaEntendida
from utils.asistente_errores import AsistenteErroresOdoo
from services.nlp.motor_empatico import MotorEmpatico

# Módulos de Business Intelligence Experto
from core.motor_bi_experto import MotorBIExperto
from services.analysis.analizador_anomalias import AnalizadorAnomalias
from services.analysis.kpis_financieros import KPIsFinancieros

# Configuración centralizada
from app.config import Config

# Para el sistema de logging
from app.logging_config import get_logger
logger = get_logger("views.interfaz_v5")

# Formateador de respuestas extraído (ARQ-001)
from services.formatters.formateador_respuestas import FormateadorRespuestas
from services.formatters.formateador_conclusiones import FormateadorConclusiones

# Ejecutores de agentes extraídos (ARQ-002)
from services.agents.ejecutores import EjecutoresAgente

# Ejecutor de acciones y mapeador de consultas extraídos (ARQ-v2-001)
from services.actions.ejecutor_acciones import EjecutorAcciones
from services.actions.mapeador_consultas import MapeadorConsultas


# Sistema de validación de datos
try:
    from utils.validador_datos import ValidadorDatos, ManejadorErrores
    VALIDADOR_DISPONIBLE = True
except ImportError:
    VALIDADOR_DISPONIBLE = False
    print("Validador de datos no disponible")

# Cerebro ANDROMEDA - Sistema de matrices y análisis avanzado
try:
    from core.cerebro_andromeda import (
        CerebroAndromeda, 
        MatrizDatosOdoo, 
        LimpiadorDatos,
        MotorEstadistico,
        GeneradorPrompts,
        TipoReporte,
        TipoAnalisis
    )
    CEREBRO_DISPONIBLE = True
    print("Cerebro ANDROMEDA cargado")
except ImportError as e:
    CEREBRO_DISPONIBLE = False
    print(f"Cerebro ANDROMEDA no disponible: {e}")

# Consultas Especializadas
try:
    from utils.consultas_especializadas import ConsultasEspecializadas
    CONSULTAS_ESP_DISPONIBLE = True
    print("Consultas Especializadas cargadas")
except ImportError as e:
    CONSULTAS_ESP_DISPONIBLE = False
    print(f"Consultas Especializadas no disponibles: {e}")

# Sistema de Predicción Inteligente
try:
    from services.prediction.prediccion_inteligente import (
        SistemaPrediccionInteligente,
        FormateadorPrediccion,
        PrediccionInteligente,
        NivelConfianza,
        TipoTendencia,
        NivelAlerta
    )
    PREDICCION_INTELIGENTE_DISPONIBLE = True
    print("Sistema de Predicción Inteligente cargado")
except ImportError as e:
    PREDICCION_INTELIGENTE_DISPONIBLE = False
    print(f"Predicción Inteligente no disponible: {e}")

# Sistema de Análisis Inteligente (nuevo)
try:
    from services.analysis.analisis_inteligente import (
        AnalizadorInteligente,
        DetectorContexto,
        FormateadorInteligente,
        set_conector_analisis,
        TipoAgrupacion,
        TipoComparativa
    )
    ANALISIS_INTELIGENTE_DISPONIBLE = True
    print("Sistema de Análisis Inteligente cargado")
except Exception as e:
    ANALISIS_INTELIGENTE_DISPONIBLE = False
    FormateadorInteligente = None
    print(f"Análisis Inteligente no disponible: {e}")

# Sistema de Análisis 360° (nuevo)
try:
    from services.analysis.analisis_360 import (
        Analizador360,
        DetectorEntidades,
        Formateador360,
        set_conector_360,
        TipoEntidad,
        Analisis360
    )
    ANALISIS_360_DISPONIBLE = True
    print("Sistema de Análisis 360° cargado")
except ImportError as e:
    ANALISIS_360_DISPONIBLE = False
    print(f"Análisis 360° no disponible: {e}")

# Motor de Machine Learning
try:
    from services.prediction.motor_ml import (
        MotorML,
        motor_ml,
        FormateadorML,
        formateador_ml,
        set_conector_ml,
        PrediccionML,
        SegmentacionML
    )
    MOTOR_ML_DISPONIBLE = True
    print("Motor de Machine Learning cargado")
except ImportError as e:
    MOTOR_ML_DISPONIBLE = False
    print(f"Motor ML no disponible: {e}")

# Motor Neural LSTM (PyTorch)
try:
    from services.prediction.neural_lstm import (
        MotorNeuralLSTM,
        motor_lstm,
        FormateadorLSTM,
        formateador_lstm,
        set_conector_lstm,
        PrediccionLSTM
    )
    MOTOR_LSTM_DISPONIBLE = True
    print("Motor Neural LSTM (PyTorch) cargado")
except ImportError as e:
    MOTOR_LSTM_DISPONIBLE = False
    print(f"Motor LSTM no disponible: {e}")

# Motor de KPIs Empresariales
try:
    from services.analysis.kpis_empresariales import (
        MotorKPIsEmpresariales,
        FormateadorKPIs,
        CategoriaKPI,
        ResultadoKPI
    )
    KPIS_EMPRESARIALES_DISPONIBLE = True
    print("Motor de KPIs Empresariales cargado")
except ImportError as e:
    KPIS_EMPRESARIALES_DISPONIBLE = False
    print(f"KPIs Empresariales no disponible: {e}")

# Base de Conocimiento - Manual de Odoo
try:
    from services.knowledge.procesador_manuales import (
        obtener_procesador,
        buscar_en_manual
    )
    MANUAL_ODOO_DISPONIBLE = True
    print("Base de Conocimiento (Manual Odoo) cargada")
except Exception as e:
    MANUAL_ODOO_DISPONIBLE = False
    print(f"Base de Conocimiento no disponible: {e}")

# Sistema de Auditoría Inteligente
try:
    from services.auditoria_inteligente import (
        AuditoriaInteligente,
        GeneradorReportePDF,
        AlertaAuditoria,
        ResultadoAuditoria,
        PrediccionChurn,
        AlertaReposicion
    )
    AUDITORIA_INTELIGENTE_DISPONIBLE = True
    print("Sistema de Auditoría Inteligente cargado")
except Exception as e:
    AUDITORIA_INTELIGENTE_DISPONIBLE = False
    print(f"Auditoría Inteligente no disponible: {e}")

# Sistema de Auditoría de Calidad de Datos (Triple Validación)
try:
    from services.auditoria_calidad_datos import AuditoriaCalidadDatos
    AUDITORIA_CALIDAD_DISPONIBLE = True
    print("Auditoría de Calidad de Datos cargada")
except ImportError as e:
    AUDITORIA_CALIDAD_DISPONIBLE = False
    print(f"Auditoría Calidad no disponible: {e}")

# Sistema de Reconocimiento de Voz
try:
    import speech_recognition as sr
    VOZ_DISPONIBLE = True
    print("Reconocimiento de Voz cargado")
except ImportError as e:
    VOZ_DISPONIBLE = False
    sr = None
    print(f"Reconocimiento de Voz no disponible: {e}")

# Cerebro LLM Local (Ollama)
try:
    from services.llm.cerebro_llm import (
        AgenteAndromeda,
        ConectorOllama,
        obtener_agente,
        AccionDetectada
    )
    from services.llm.generador_queries import (
        GeneradorQueries,
        obtener_generador_queries
    )
    LLM_DISPONIBLE = True
    print("Cerebro LLM Local cargado")
except ImportError as e:
    LLM_DISPONIBLE = False
    AgenteAndromeda = None
    GeneradorQueries = None
    print(f"Cerebro LLM no disponible: {e}")

# Memoria Vectorial (ChromaDB)
try:
    from services.memory import obtener_memoria, obtener_memoria_jerarquica, CHROMADB_DISPONIBLE
    MEMORIA_DISPONIBLE = CHROMADB_DISPONIBLE
    if MEMORIA_DISPONIBLE:
        print("Memoria Vectorial (ChromaDB) cargada")
except ImportError as e:
    MEMORIA_DISPONIBLE = False
    obtener_memoria_jerarquica = None
    print(f"Memoria Vectorial no disponible: {e}")

# Arquitectura Multi-Agente Ligera
try:
    from services.agents import GestorMultiAgente
    MULTI_AGENTE_DISPONIBLE = True
    print("Arquitectura Multi-Agente cargada")
except ImportError as e:
    MULTI_AGENTE_DISPONIBLE = False
    GestorMultiAgente = None
    print(f"Arquitectura Multi-Agente no disponible: {e}")

# Normalizador de Prompts — corrige typos, abreviaciones, coloquialismos
try:
    from utils.normalizador_prompt import obtener_normalizador
    NORMALIZADOR_DISPONIBLE = True
    print("Normalizador de Prompts cargado")
except ImportError as e:
    NORMALIZADOR_DISPONIBLE = False
    print(f"Normalizador no disponible: {e}")

# Validador de Respuestas — anti-alucinación, limpieza de internos
try:
    from utils.validador_respuestas import obtener_validador
    VALIDADOR_RESPUESTAS_DISPONIBLE = True
    print("Validador de Respuestas cargado")
except ImportError as e:
    VALIDADOR_RESPUESTAS_DISPONIBLE = False
    print(f"Validador de Respuestas no disponible: {e}")

# Generador de PDFs (ReportLab)
try:
    from services.reports import obtener_generador_pdf, REPORTLAB_DISPONIBLE
    PDF_DISPONIBLE = REPORTLAB_DISPONIBLE
    if PDF_DISPONIBLE:
        print("Generador de PDFs (ReportLab) cargado")
except ImportError as e:
    PDF_DISPONIBLE = False
    print(f"Generador de PDFs no disponible: {e}")

# Generador de Gráficas
try:
    from services.reports.generador_graficas import GeneradorGraficas
    GRAFICAS_DISPONIBLE = True
    print("Generador de Gráficas cargado")
except ImportError as e:
    GRAFICAS_DISPONIBLE = False
    GeneradorGraficas = None
    print(f"Generador de Gráficas no disponible: {e}")

# Sistema de Logging Avanzado
try:
    from utils.logging_avanzado import LoggerAvanzado, TipoEvento, NivelCriticidad
    LOGGING_DISPONIBLE = True
    print("Sistema de Logging Avanzado cargado")
except Exception as e:
    LOGGING_DISPONIBLE = False
    LoggerAvanzado = None
    NivelCriticidad = None
    TipoEvento = None
    print(f"Logging Avanzado no disponible: {e}")

# Integrador Ollama para mejora de prompts
try:
    from services.llm.ollama_integrador import OllamaIntegrador
    OLLAMA_INTEGRADOR_DISPONIBLE = True
    print("Integrador Ollama cargado")
except ImportError as e:
    OLLAMA_INTEGRADOR_DISPONIBLE = False
    OllamaIntegrador = None
    print(f"Integrador Ollama no disponible: {e}")

try:
    import gradio as gr
    GRADIO_DISPONIBLE = True
except ImportError:
    GRADIO_DISPONIBLE = False
    print("Gradio no instalado")


# ============================================================
# CSS PROFESIONAL - ESTILO GEMINI/CHATGPT CON FONT AWESOME
# ============================================================

CSS_PRO_V5 = """
/* Reset y base con fondo galaxia */
.gradio-container {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 25%, #0d1b2a 50%, #1a1a3e 75%, #0a0a1a 100%) !important;
    background-size: 400% 400% !important;
    animation: gradientShift 15s ease infinite !important;
    min-height: 100vh;
    position: relative;
    overflow: hidden;
}

/* Animación del gradiente */
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Canvas de estrellas animado */
#starsCanvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
}

/* Estrellas extras con CSS - capas múltiples que se mueven */
.gradio-container::before {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background-image: 
        radial-gradient(2px 2px at 10% 10%, rgba(255,255,255,0.9), transparent),
        radial-gradient(2px 2px at 20% 30%, rgba(255,255,255,0.7), transparent),
        radial-gradient(1px 1px at 30% 60%, rgba(255,255,255,0.8), transparent),
        radial-gradient(2px 2px at 40% 20%, rgba(102,126,234,0.8), transparent),
        radial-gradient(1px 1px at 50% 80%, rgba(255,255,255,0.6), transparent),
        radial-gradient(2px 2px at 60% 40%, rgba(255,255,255,0.7), transparent),
        radial-gradient(1px 1px at 70% 70%, rgba(118,75,162,0.7), transparent),
        radial-gradient(2px 2px at 80% 15%, rgba(255,255,255,0.8), transparent),
        radial-gradient(1px 1px at 90% 50%, rgba(255,255,255,0.6), transparent);
    background-size: 50% 50%;
    animation: starsMove 60s linear infinite;
    pointer-events: none;
    z-index: 0;
    opacity: 0.8;
}

.gradio-container::after {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background-image: 
        radial-gradient(3px 3px at 15% 25%, rgba(102,126,234,0.9), transparent),
        radial-gradient(2px 2px at 25% 75%, rgba(255,255,255,0.6), transparent),
        radial-gradient(3px 3px at 35% 45%, rgba(255,255,255,0.8), transparent),
        radial-gradient(2px 2px at 55% 35%, rgba(118,75,162,0.8), transparent),
        radial-gradient(3px 3px at 65% 85%, rgba(255,255,255,0.7), transparent),
        radial-gradient(2px 2px at 75% 55%, rgba(102,126,234,0.7), transparent),
        radial-gradient(3px 3px at 85% 25%, rgba(255,255,255,0.9), transparent),
        radial-gradient(2px 2px at 95% 65%, rgba(118,75,162,0.6), transparent);
    background-size: 60% 60%;
    animation: starsMove2 80s linear infinite reverse;
    pointer-events: none;
    z-index: 0;
    opacity: 0.6;
}

@keyframes starsMove {
    0% { transform: translate(0, 0) rotate(0deg); }
    25% { transform: translate(-5%, 5%) rotate(90deg); }
    50% { transform: translate(0, 10%) rotate(180deg); }
    75% { transform: translate(5%, 5%) rotate(270deg); }
    100% { transform: translate(0, 0) rotate(360deg); }
}

@keyframes starsMove2 {
    0% { transform: translate(0, 0) rotate(0deg); }
    100% { transform: translate(-10%, -10%) rotate(-360deg); }
}

/* Variables CSS */
:root {
    --sidebar-width: 280px;
    --sidebar-collapsed: 70px;
    --transition-speed: 0.3s;
}

/* Layout principal */
.main-layout {
    display: flex;
    min-height: 100vh;
    position: relative;
    z-index: 1;
}

/* Sidebar izquierdo - Efecto Glass */
.sidebar {
    width: var(--sidebar-width);
    background: rgba(15, 15, 35, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(102, 126, 234, 0.2);
    padding: 0;
    display: flex;
    flex-direction: column;
    position: fixed;
    height: 100vh;
    left: 0;
    top: 0;
    z-index: 1000;
    transition: width var(--transition-speed) ease, transform var(--transition-speed) ease;
    overflow: hidden;
}

/* Columna del sidebar */
.sidebar-col {
    position: fixed !important;
    left: 0 !important;
    top: 0 !important;
    width: var(--sidebar-width) !important;
    height: 100vh !important;
    z-index: 1000 !important;
    pointer-events: auto !important;
    padding: 0 !important;
    margin: 0 !important;
}

.sidebar.collapsed {
    width: var(--sidebar-collapsed);
}

.sidebar.collapsed .sidebar-header h2,
.sidebar.collapsed .new-chat-text,
.sidebar.collapsed .menu-item span:last-child,
.sidebar.collapsed .menu-section-title,
.sidebar.collapsed .user-details {
    opacity: 0;
    visibility: hidden;
    width: 0;
}

.sidebar.collapsed .sidebar-logo {
    justify-content: center;
    padding-left: 0;
}

.sidebar.collapsed .new-chat-btn {
    padding: 12px;
    justify-content: center;
    width: 44px;
    height: 44px;
    margin: 0 auto;
    border-radius: 10px;
}

.sidebar.collapsed .menu-item {
    justify-content: center;
    padding: 14px !important;
    margin: 4px 8px;
    border-radius: 10px;
}

.sidebar.collapsed .menu-item-icon {
    margin-right: 0 !important;
    font-size: 18px;
}

.sidebar.collapsed .user-info {
    justify-content: center;
}

.sidebar.collapsed .logo-container {
    margin: 0 auto;
}

/* Toggle button - Estilo Moderno */
.sidebar-toggle {
    position: fixed;
    left: 265px;
    top: 20px;
    width: 36px;
    height: 36px;
    background: rgba(102, 126, 234, 0.2) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(102, 126, 234, 0.4);
    border-radius: 10px;
    color: #fff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    transition: all 0.3s ease;
}

.sidebar-toggle:hover {
    background: rgba(102, 126, 234, 0.4) !important;
    border-color: rgba(102, 126, 234, 0.6);
    transform: scale(1.05);
}

.sidebar-toggle i {
    font-size: 14px;
    transition: transform 0.3s ease;
}

.sidebar-toggle.collapsed {
    left: 55px;
}

.sidebar-toggle.collapsed i {
    transform: rotate(180deg);
}

.sidebar-header {
    padding: 24px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    position: relative;
}

.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    transition: all var(--transition-speed) ease;
}

/* Logo container - placeholder para imagen personalizada */
.logo-container {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f64f59 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    overflow: hidden;
}

.logo-container img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.logo-container i {
    font-size: 20px;
    color: white;
}

.sidebar-logo h2 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f64f59 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 1.6em;
    font-weight: 800;
    margin: 0;
    white-space: nowrap;
    transition: all var(--transition-speed) ease;
}

.new-chat-btn {
    width: 100%;
    padding: 14px 20px;
    margin-top: 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: all 0.3s ease;
}

.new-chat-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102,126,234,0.4);
}

.sidebar-menu {
    flex: 1;
    padding: 16px 12px;
    overflow-y: auto;
}

.menu-section {
    margin-bottom: 24px;
}

.menu-section-title {
    color: rgba(255,255,255,0.4);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 0 12px;
    margin-bottom: 8px;
    white-space: nowrap;
    transition: all var(--transition-speed) ease;
}

.menu-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 10px;
    color: rgba(255,255,255,0.75);
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 4px;
    position: relative;
    z-index: 10;
    pointer-events: auto !important;
    user-select: none;
}

.menu-item:hover {
    background: rgba(102,126,234,0.15);
    color: white;
}

.menu-item:active {
    background: rgba(102,126,234,0.25);
    transform: scale(0.98);
}

.menu-item.active {
    background: rgba(102,126,234,0.25);
    color: white;
}

.menu-item-icon {
    font-size: 18px;
    width: 24px;
    text-align: center;
}

.sidebar-footer {
    padding: 16px 12px;
    border-top: 1px solid rgba(255,255,255,0.08);
}

.user-info {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-radius: 10px;
    background: rgba(255,255,255,0.03);
    transition: all var(--transition-speed) ease;
}

.user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
}

.user-avatar i {
    color: white;
}

.user-details {
    flex: 1;
    overflow: hidden;
    transition: all var(--transition-speed) ease;
}

.user-name {
    color: white;
    font-size: 13px;
    font-weight: 500;
    white-space: nowrap;
}

.user-status {
    color: #22c55e;
    font-size: 11px;
    display: flex;
    align-items: center;
    gap: 4px;
}

.user-status::before {
    content: '';
    width: 6px;
    height: 6px;
    background: #22c55e;
    border-radius: 50%;
}

/* Contenido principal - DINÁMICO */
.main-content,
.main-content-col {
    flex: 1;
    margin-left: var(--sidebar-width);
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    background: transparent !important;
    transition: margin-left var(--transition-speed) ease;
    position: relative;
    z-index: 1;
}

body.sidebar-collapsed .main-content,
body.sidebar-collapsed .main-content-col,
.main-content.expanded {
    margin-left: var(--sidebar-collapsed);
}

/* Header principal - Efecto Glass */
.top-header {
    padding: 16px 32px;
    border-bottom: 1px solid rgba(102, 126, 234, 0.2);
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(15, 15, 35, 0.7) !important;
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    position: sticky;
    top: 0;
    z-index: 50;
    margin-left: var(--sidebar-width);
    transition: margin-left var(--transition-speed) ease;
}

.header-title {
    display: flex;
    align-items: center;
    gap: 16px;
}

.header-title h1 {
    color: white;
    font-size: 1.3em;
    font-weight: 600;
    margin: 0;
}

.header-badge {
    background: linear-gradient(135deg, #667eea, #764ba2);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    color: white;
}

.header-stats {
    display: flex;
    gap: 24px;
}

.stat-item {
    text-align: center;
}

.stat-value {
    color: white;
    font-size: 1.1em;
    font-weight: 700;
}

.stat-label {
    color: rgba(255,255,255,0.5);
    font-size: 11px;
    text-transform: uppercase;
}

/* Área del chat - Transparente para ver galaxia */
.chat-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    max-width: 900px;
    margin: 0 auto;
    width: 100%;
    padding: 0 24px;
    background: transparent !important;
}

.chat-messages {
    flex: 1;
    padding: 24px 0;
    overflow-y: auto;
    background: transparent !important;
}

/* Contenedores Gradio - Transparentes */
.gradio-container,
.gradio-container > div,
.contain > div,
#component-0 {
    background: transparent !important;
}

/* Estilos del Chatbot */
.chat-messages .message {
    background: rgba(255,255,255,0.05) !important;
    border-radius: 16px !important;
    margin: 8px 0 !important;
    backdrop-filter: blur(10px) !important;
}

/* Input Group - Simple y funcional */
.input-group {
    background: rgba(45, 45, 65, 0.8) !important;
    border-radius: 24px !important;
    padding: 8px 16px !important;
    border: 1px solid rgba(102, 126, 234, 0.3) !important;
    backdrop-filter: blur(10px) !important;
    max-width: 800px !important;
    margin: 0 auto !important;
}

.input-group .gradio-row {
    gap: 12px !important;
    align-items: center !important;
}

/* Textbox dentro del input-group */
.input-group textarea,
.input-group input[type="text"] {
    background: transparent !important;
    border: none !important;
    color: #fff !important;
    font-size: 15px !important;
    padding: 12px 0 !important;
}

.input-group textarea:focus,
.input-group input:focus {
    outline: none !important;
    box-shadow: none !important;
}

.input-group textarea::placeholder {
    color: rgba(255,255,255,0.5) !important;
}

/* Botón Enviar */
.input-group button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 20px !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
}

.input-group button:hover {
    transform: scale(1.02) !important;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4) !important;
}

/* Focus state */
.input-group:focus-within {
    border-color: rgba(102, 126, 234, 0.6) !important;
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.2) !important;
}

/* Panel de acciones rápidas */
.quick-actions-panel {
    position: absolute;
    bottom: 100%;
    left: 0;
    background: #1a1a2e;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 12px;
    margin-bottom: 12px;
    min-width: 320px;
    max-height: 400px;
    overflow-y: auto;
    box-shadow: 0 -10px 40px rgba(0,0,0,0.5);
}

.quick-actions-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
}

.quick-action-item {
    padding: 12px 16px;
    background: rgba(102,126,234,0.08);
    border-radius: 10px;
    color: rgba(255,255,255,0.85);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 10px;
}

.quick-action-item:hover {
    background: rgba(102,126,234,0.2);
    color: white;
}

.quick-action-icon {
    font-size: 16px;
}

/* Mensajes del chat */
.message {
    padding: 16px 0;
    display: flex;
    gap: 16px;
}

.message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
}

.message-avatar.user {
    background: linear-gradient(135deg, #667eea, #764ba2);
}

.message-avatar.assistant {
    background: linear-gradient(135deg, #1a1a2e, #302b63);
    border: 1px solid rgba(102,126,234,0.3);
}

.message-content {
    flex: 1;
    color: rgba(255,255,255,0.9);
    line-height: 1.6;
}

/* Tablas de datos */
.data-table-container {
    margin-top: 16px;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.1);
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}

.data-table th {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 14px 16px;
    text-align: left;
    font-weight: 600;
}

.data-table td {
    padding: 12px 16px;
    color: #c9d1d9;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.data-table tr:nth-child(even) {
    background: rgba(255,255,255,0.02);
}

.data-table tr:hover {
    background: rgba(102,126,234,0.08);
}

/* Panel de configuración en sidebar */
.config-panel {
    padding: 16px;
    background: rgba(102,126,234,0.05);
    border-radius: 12px;
    margin: 8px 12px;
}

.config-title {
    color: rgba(255,255,255,0.6);
    font-size: 12px;
    margin-bottom: 12px;
}

.config-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
    color: rgba(255,255,255,0.8);
    font-size: 13px;
}

/* Animaciones */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.message {
    animation: fadeInUp 0.3s ease;
}

/* Responsive */
@media (max-width: 1024px) {
    .sidebar {
        width: 80px;
    }
    .sidebar-logo h2,
    .menu-item span,
    .menu-section-title,
    .user-details,
    .new-chat-btn span {
        display: none;
    }
    .main-content {
        margin-left: 80px;
    }
}
"""


# ============================================================
# CLASE PRINCIPAL v5.0
# ============================================================

class OdooAIProV5:
    """ANDROMEDA  - Advanced Neural Data Resource for Operations, Management & Enterprise Decision Analytics."""
    
    VERSION = "1.0.0"
    NOMBRE = "ANDROMEDA"
    
    # Historial de sesión persistente: {sesion_id: [mensajes]}
    # Permite recuperar la conversación si el usuario cambia de ruta y regresa
    _sesiones_historial: dict = {}
    MAX_SESIONES = 500          # máximo de sesiones en memoria
    MAX_HISTORIAL_SESION = 200  # máximo de mensajes por sesión

    def __init__(self):
        print(f"\n{'='*60}")
        print(f"Iniciando {self.NOMBRE} v{self.VERSION}")
        print(f"{'='*60}\n")
        
        # Componentes base
        self.odoo = ConectorOdoo()
        self.reportes = GeneradorReportes()
        self.analizador = AnalizadorAvanzado()
        self.predictor = MotorPrediccion()
        self.nlp = MotorNLPAvanzado()
        self.asistente_errores = AsistenteErroresOdoo()
        self.motor_empatico = MotorEmpatico()
        self.fmt = FormateadorRespuestas()
        self._conclusiones = FormateadorConclusiones()
        
        # Ejecutor de acciones extraído (ARQ-v2-001)
        self._ejecutor_acciones = EjecutorAcciones(self)
        self._mapeador_consultas = MapeadorConsultas(self)
        
        # Módulos de Business Intelligence Experto
        self.motor_bi = MotorBIExperto()
        self.analizador_anomalias = AnalizadorAnomalias()
        self.kpis = KPIsFinancieros()
        
        # Cerebro ANDROMEDA - Sistema de matrices inteligentes
        if CEREBRO_DISPONIBLE:
            self.cerebro = CerebroAndromeda()
            self.limpiador = LimpiadorDatos()
            self.matriz = MatrizDatosOdoo()
            print("Cerebro ANDROMEDA activado")
        else:
            self.cerebro = None
            self.limpiador = None
            self.matriz = None
        
        # Consultas Especializadas
        if CONSULTAS_ESP_DISPONIBLE:
            self.consultas_esp = ConsultasEspecializadas()
            print("Consultas Especializadas activadas")
        else:
            self.consultas_esp = None
        
        # Sistema de Predicción Inteligente
        if PREDICCION_INTELIGENTE_DISPONIBLE:
            self.prediccion_inteligente = SistemaPrediccionInteligente()
            self.formateador_prediccion = FormateadorPrediccion()
            print("Predicción Inteligente activada")
        else:
            self.prediccion_inteligente = None
            self.formateador_prediccion = None
        
        # Sistema de Análisis Inteligente
        if ANALISIS_INTELIGENTE_DISPONIBLE:
            self.analizador_inteligente = AnalizadorInteligente()
            self.detector_contexto = DetectorContexto()
            print("Análisis Inteligente activado")
        else:
            self.analizador_inteligente = None
            self.detector_contexto = None
        
        # Sistema de Análisis 360°
        if ANALISIS_360_DISPONIBLE:
            self.analizador_360 = Analizador360()
            self.formateador_360 = Formateador360()
            print("Análisis 360° activado")
        else:
            self.analizador_360 = None
            self.formateador_360 = None
        
        # Motor de Machine Learning
        if MOTOR_ML_DISPONIBLE:
            self.motor_ml = motor_ml
            self.formateador_ml = formateador_ml
            print("Motor ML activado")
        else:
            self.motor_ml = None
            self.formateador_ml = None
        
        # Motor Neural LSTM (PyTorch)
        if MOTOR_LSTM_DISPONIBLE:
            self.motor_lstm = motor_lstm
            self.formateador_lstm = formateador_lstm
            print("Motor Neural LSTM (PyTorch) activado")
        else:
            self.motor_lstm = None
            self.formateador_lstm = None
        
        # Motor de KPIs Empresariales
        if KPIS_EMPRESARIALES_DISPONIBLE:
            self.motor_kpis = MotorKPIsEmpresariales()
            self.formateador_kpis = FormateadorKPIs()
            print("Motor de KPIs Empresariales activado")
        else:
            self.motor_kpis = None
            self.formateador_kpis = None
        
        # Sistema de Auditoría Inteligente
        if AUDITORIA_INTELIGENTE_DISPONIBLE:
            self.auditoria = AuditoriaInteligente()
            self.generador_pdf = GeneradorReportePDF()
            print("Auditoría Inteligente activada")
        else:
            self.auditoria = None
            self.generador_pdf = None
        
        # Auditoría de Calidad de Datos (Triple Validación)
        if AUDITORIA_CALIDAD_DISPONIBLE:
            self.auditoria_calidad = AuditoriaCalidadDatos()
            print("Auditoría de Calidad de Datos activada")
        else:
            self.auditoria_calidad = None
        
        # Cerebro LLM Local (Ollama) - DESACTIVADO por rendimiento
        # El sistema NLP tradicional es suficiente y más rápido
        self.agente_llm = None
        self.llm_activo = False
        print("Usando sistema NLP tradicional (LLM desactivado para mejor rendimiento)")
        
        # Memoria Vectorial (ChromaDB)
        if MEMORIA_DISPONIBLE:
            try:
                self.memoria = obtener_memoria()
                print("Memoria Vectorial activada")
            except Exception as e:
                self.memoria = None
                print(f"Error inicializando memoria: {e}")
        else:
            self.memoria = None

        # Memoria Jerárquica (sesión + contextual + preferencias + semántica)
        try:
            if obtener_memoria_jerarquica:
                self.memoria_jerarquica = obtener_memoria_jerarquica(self.memoria)
                print("Memoria Jerárquica activada")
            else:
                self.memoria_jerarquica = None
        except Exception as e:
            self.memoria_jerarquica = None
            print(f"Error inicializando Memoria Jerárquica: {e}")
        
        # Generador de PDFs (ReportLab)
        if PDF_DISPONIBLE:
            try:
                self.generador_pdf_reportlab = obtener_generador_pdf()
                print("Generador de PDFs activado")
            except Exception as e:
                self.generador_pdf_reportlab = None
                print(f"Error inicializando PDFs: {e}")
        else:
            self.generador_pdf_reportlab = None
        
        # Generador de Gráficas
        if GRAFICAS_DISPONIBLE:
            try:
                # Modo 'web' para gráficas interactivas en chat web
                # Sistema detecta automáticamente si usar Plotly (interactivo) o Matplotlib (fallback)
                self.generador_graficas = GeneradorGraficas(modo='web')
                print("Generador de Gráficas activado - Modo WEB (Plotly interactivo)")
            except Exception as e:
                self.generador_graficas = None
                print(f"Error inicializando Gráficas: {e}")
        else:
            self.generador_graficas = None
        
        # Sistema de Logging Avanzado
        if LOGGING_DISPONIBLE:
            try:
                from utils.logging_avanzado import obtener_logger as _obtener_logger
                self.logger = _obtener_logger()
                print("Sistema de Logging Avanzado activado")
            except Exception as e:
                self.logger = None
                print(f"Error inicializando Logging: {e}")
        else:
            self.logger = None
        
        # Integrador Ollama para mejora de prompts
        if OLLAMA_INTEGRADOR_DISPONIBLE:
            try:
                self.ollama_integrador = OllamaIntegrador()
                self.ollama_activo = self.ollama_integrador.conectado
                if self.ollama_activo:
                    print("Integrador Ollama activado y conectado")
                else:
                    print("Integrador Ollama disponible pero no conectado")
            except Exception as e:
                self.ollama_integrador = None
                self.ollama_activo = False
                print(f"Error inicializando Ollama: {e}")
        else:
            self.ollama_integrador = None
            self.ollama_activo = False
        
        # Generador de Queries Dinámicos
        if LLM_DISPONIBLE and GeneradorQueries:
            try:
                self.generador_queries = obtener_generador_queries()
                print("Generador de Queries Dinámicos activado")
            except Exception as e:
                self.generador_queries = None
                print(f"Error inicializando queries: {e}")
        else:
            self.generador_queries = None
        
        # Conectar
        exito, msg = self.odoo.conectar()
        self.conectado = exito
        print(f"Conexión: {msg}")
        
        # Configurar moneda dinámica desde Odoo
        if exito:
            try:
                company_ids = self.odoo.odoo.env['res.company'].search([], limit=1)
                if company_ids:
                    company = self.odoo.odoo.env['res.company'].read(company_ids, ['currency_id'])[0]
                    currency_id = company['currency_id'][0] if company.get('currency_id') else None
                    if currency_id:
                        currency = self.odoo.odoo.env['res.currency'].read([currency_id], ['symbol'])[0]
                        simbolo = currency.get('symbol', '$')
                        FormateadorRespuestas.configurar_moneda(simbolo)
                        print(f"Moneda configurada: {simbolo}")
            except Exception as e:
                print(f"Moneda por defecto ($): {e}")
        
        # Configurar motores
        self.analizador.set_conector(self.odoo)
        self.predictor.set_conector(self.odoo)
        
        # Configurar módulos BI
        self.motor_bi.set_conector(self.odoo)
        self.analizador_anomalias.set_conector(self.odoo)
        self.kpis.set_conector(self.odoo)
        
        # Configurar Cerebro ANDROMEDA
        if self.cerebro:
            self.cerebro.set_conector(self.odoo)
        
        # Configurar Consultas Especializadas
        if self.consultas_esp:
            self.consultas_esp.set_conector(self.odoo)
        
        # Configurar Sistema de Predicción Inteligente
        if self.prediccion_inteligente:
            self.prediccion_inteligente.set_conector(self.odoo)
        
        # Configurar Sistema de Análisis Inteligente
        if self.analizador_inteligente:
            self.analizador_inteligente.set_conector(self.odoo)
        
        # Configurar Sistema de Análisis 360°
        if self.analizador_360:
            self.analizador_360.set_conector(self.odoo)
        
        # Configurar Motor ML
        if self.motor_ml:
            self.motor_ml.set_conector(self.odoo)
        
        # Configurar Motor LSTM
        if self.motor_lstm:
            self.motor_lstm.set_conector(self.odoo)
        
        # Configurar Motor KPIs Empresariales
        if self.motor_kpis:
            self.motor_kpis.set_conector(self.odoo)
        
        # Configurar Auditoría Inteligente
        if self.auditoria:
            self.auditoria.set_conector(self.odoo)
        
        # Configurar Auditoría de Calidad de Datos
        if self.auditoria_calidad:
            self.auditoria_calidad.set_conector(self.odoo)
        
        # Configurar Generador de Queries Dinámicos
        if self.generador_queries:
            self.generador_queries.set_conector(self.odoo)
            if self.agente_llm:
                self.generador_queries.set_agente_llm(self.agente_llm)
        
        # Estado y memoria de contexto
        self.ultimo_df = None
        self.ultimo_modelo = None
        self.ultimo_resultado = None  # Última respuesta generada
        self.ultima_accion = None     # Última acción ejecutada
        self.ultimos_datos = None     # Últimos datos en bruto para PDF
        self.contexto_conversacion = []
        self.confirmacion_critica_pendiente = None

        # Router explícito de intenciones (configurable)
        self.intent_confidence_threshold = self._leer_umbral_confianza()
        self.acciones_criticas = {
            'consulta_dinamica',
            'generar_excel',
            'generar_pdf',
            'generar_pdf_profesional',
            'generar_reporte_auditoria',
        }

        # Multi-agente ligero (ventas, inventario, finanzas, diagnóstico)
        if MULTI_AGENTE_DISPONIBLE and GestorMultiAgente:
            try:
                self.gestor_agentes = GestorMultiAgente()
                self._ejecutores = EjecutoresAgente(self)
                self.gestor_agentes.registrar_ejecutor_default(self._ejecutar_accion)
                # Registrar ejecutores desde módulo dedicado (ARQ-002)
                self.gestor_agentes.registrar_ejecutor('agente_ventas', self._ejecutores._ejecutor_ventas)
                self.gestor_agentes.registrar_ejecutor('agente_inventario', self._ejecutores._ejecutor_inventario)
                self.gestor_agentes.registrar_ejecutor('agente_finanzas', self._ejecutores._ejecutor_finanzas)
                self.gestor_agentes.registrar_ejecutor('agente_crm', self._ejecutores._ejecutor_crm)
                self.gestor_agentes.registrar_ejecutor('agente_compras', self._ejecutores._ejecutor_compras)
                self.gestor_agentes.registrar_ejecutor('agente_pdv', self._ejecutores._ejecutor_pdv)
                self.gestor_agentes.registrar_ejecutor('agente_rrhh', self._ejecutores._ejecutor_rrhh)
                self.gestor_agentes.registrar_ejecutor('agente_predicciones', self._ejecutores._ejecutor_predicciones)
                self.gestor_agentes.registrar_ejecutor('agente_diagnostico', self._ejecutores._ejecutor_diagnostico)
                self.gestor_agentes.registrar_ejecutor('agente_odoo', self._ejecutores._ejecutor_odoo)
                self.gestor_agentes.registrar_ejecutor('agente_estadistica', self._ejecutores._ejecutor_estadistica)
                self.gestor_agentes.registrar_ejecutor('agente_matematicas', self._ejecutores._ejecutor_matematicas)
                print("Gestor Multi-Agente activado")
            except Exception as e:
                self.gestor_agentes = None
                print(f"Error inicializando Gestor Multi-Agente: {e}")
        else:
            self.gestor_agentes = None
        
        print(f"\n{self.NOMBRE} v{self.VERSION} - LISTO")
        print(f"{'='*60}\n")

    def _leer_umbral_confianza(self) -> float:
        """Lee y normaliza el umbral de confianza para el router de intenciones."""
        valor = os.getenv('ANDROMEDA_INTENT_CONFIDENCE_THRESHOLD', '0.58')
        try:
            umbral = float(valor)
        except Exception:
            umbral = 0.58
        return max(0.0, min(1.0, umbral))

    def _ejecutar_desde_gestor_agentes(self, consulta: ConsultaEntendida, mensaje: str, agente_id: str = '') -> Tuple[str, pd.DataFrame]:
        """Ejecuta una acción a través del gestor multi-agente cuando está disponible."""
        if self.gestor_agentes and agente_id:
            try:
                result = self.gestor_agentes.ejecutar_accion(agente_id, consulta, mensaje)
                # Guard defensivo: verificar que el resultado sea una tupla válida de 2 elementos
                if isinstance(result, tuple) and len(result) == 2:
                    return result
                if result is not None:
                    logger.warning(
                        f"Agente '{agente_id}' retornó tipo inesperado: {type(result).__name__} — usando ejecutor directo"
                    )
            except Exception as e:
                logger.warning(f"Error en agente '{agente_id}': {e} — usando ejecutor directo")
        return self._ejecutar_accion(consulta, mensaje)
    
    def _es_solicitud_mutacion_bd(self, mensaje: str) -> bool:
        """Detecta solicitudes de escritura/modificación en BD no permitidas."""
        msg = mensaje.lower()
        # Verbos de mutación (español + inglés + SQL)
        patron_mutacion = re.compile(
            r'\b(crear|crea|generar|genera|nuevo|nueva|actualizar|actualiza|'
            r'modificar|modifica|editar|edita|cambiar|cambia|'
            r'eliminar|elimina|borrar|borra|insertar|inserta|'
            r'escribir|guardar|guardame|hazme|hacerme|'
            r'create|delete|remove|update|write|insert|'
            r'drop|truncate|alter|exec|execute)\b',
            re.IGNORECASE
        )
        # Objetos de negocio
        patron_objeto = re.compile(
            r'\b(registro|base\s*de\s*datos|bd|factura|pedido|producto|'
            r'cliente|usuario|asiento|movimiento|orden|inventario|'
            r'tabla|table|proveedor|empleado|contacto|partner)\b',
            re.IGNORECASE
        )
        # Comandos SQL directos siempre bloqueados
        patron_sql = re.compile(
            r'\b(drop\s+table|truncate|alter\s+table|delete\s+from|'
            r'insert\s+into|update\s+\w+\s+set)\b',
            re.IGNORECASE
        )
        if patron_sql.search(msg):
            return True
        return bool(patron_mutacion.search(msg) and patron_objeto.search(msg))

    def _detectar_agente_especializado(self, accion: str, mensaje: str = '') -> str:
        """Asigna el agente especializado — delega al GestorMultiAgente si disponible."""
        if self.gestor_agentes:
            try:
                agente_id, _, _ = self.gestor_agentes.resolver_agente(
                    accion=accion, mensaje=mensaje
                )
                return agente_id
            except Exception:
                pass

        # Fallback: mapeo estático
        acciones_diagnostico = {
            'diagnosticar_error', 'auditoria_nocturna', 'semaforo_salud', 'detectar_pagos_fantasma',
            'analizar_churn', 'reposicion_jit', 'stock_lento', 'clientes_olvidados',
            'diferencias_centavos', 'generar_reporte_auditoria', 'detectar_anomalias', 'analisis_riesgos',
            'auditoria_calidad_datos'
        }

        if accion in acciones_diagnostico:
            return 'agente_diagnostico'

        if 'inventario' in accion or accion in {
            'productos_sin_stock', 'rotacion_inventario', 'valoracion_inventario',
            'predecir_agotamiento', 'kpi_rotacion_inventario', 'kpi_faltantes'
        }:
            return 'agente_inventario'

        if 'factura' in accion or accion in {
            'cuentas_por_cobrar', 'cuentas_por_pagar', 'cxc_analisis', 'cxp_analisis',
            'score_morosos', 'flujo_caja', 'salud_negocio', 'kpi_ticket_promedio'
        }:
            return 'agente_finanzas'

        if 'ventas' in accion or accion in {
            'top_productos', 'top_clientes', 'comparar_periodos', 'ventas_vendedor', 'tendencia'
        }:
            return 'agente_ventas'

        return 'agente_general'

    def _requiere_confirmacion_critica(self, accion: str, mensaje: str) -> bool:
        """Define si una consulta debe pedirse con confirmación explícita."""
        if accion in self.acciones_criticas:
            return True
        return 'query dinamica' in mensaje.lower() or 'consulta dinamica' in mensaje.lower()

    def _es_respuesta_afirmativa(self, mensaje: str) -> bool:
        texto = mensaje.strip().lower()
        afirmaciones = {'si', 'sí', 'ok', 'dale', 'confirmo', 'confirmar', 'ejecuta', 'adelante', 'continuar'}
        return texto in afirmaciones or texto.startswith('si ') or texto.startswith('sí ')

    def _es_respuesta_negativa(self, mensaje: str) -> bool:
        texto = mensaje.strip().lower()
        negativas = {'no', 'cancelar', 'cancela', 'detener', 'alto', 'parar'}
        return texto in negativas or texto.startswith('no ')

    def _resolver_confirmacion_critica(self, mensaje: str, historial: List[Dict], tiempo_inicio=None) -> Optional[Tuple[List[Dict], str, str]]:
        """Resuelve una confirmación pendiente para ejecutar una consulta crítica."""
        if not self.confirmacion_critica_pendiente:
            return None

        pendiente = self.confirmacion_critica_pendiente

        if self._es_respuesta_negativa(mensaje):
            self.confirmacion_critica_pendiente = None
            respuesta = "Consulta crítica cancelada. ANDROMEDA se mantiene en modo solo lectura y sin ejecutar esa operación."
            historial.append({"role": "assistant", "content": respuesta})
            return historial, "", "⚠️ Consulta crítica cancelada"

        if not self._es_respuesta_afirmativa(mensaje):
            respuesta = (
                "Tengo una consulta crítica pendiente. Responde **sí** para ejecutar o **no** para cancelar.\n\n"
                f"Acción pendiente: **{pendiente.get('accion', 'consulta')}**"
            )
            historial.append({"role": "assistant", "content": respuesta})
            return historial, "", "⚠️ Esperando confirmación"

        consulta = pendiente['consulta']
        mensaje_original = pendiente['mensaje_original']
        self.confirmacion_critica_pendiente = None

        try:
            respuesta, df = self._ejecutar_desde_gestor_agentes(
                consulta,
                mensaje_original,
                pendiente.get('agente', '')
            )
            if self.gestor_agentes:
                try:
                    post = self.gestor_agentes.post_ejecutar(
                        agente_id=pendiente.get('agente', 'agente_general'),
                        consulta=consulta,
                        respuesta=respuesta,
                        df=df,
                        error=False
                    )
                    respuesta = post.respuesta
                except Exception:
                    pass
        except Exception as e:
            respuesta = f"Error al ejecutar la consulta crítica confirmada: {str(e)}"
            df = None
            if self.gestor_agentes:
                try:
                    post_error = self.gestor_agentes.post_ejecutar(
                        agente_id=pendiente.get('agente', 'agente_general'),
                        consulta=consulta,
                        respuesta=respuesta,
                        df=None,
                        error=True
                    )
                    respuesta = post_error.respuesta
                except Exception:
                    pass

        historial.append({"role": "assistant", "content": respuesta})
        tabla_html = ""
        if df is not None and not df.empty:
            self.ultimo_df = df
            tabla_html = self._df_a_html(df.head(30))

        if self.logger:
            self.logger.registrar_prompt(
                prompt_original=f"[CONFIRMADO] {mensaje_original}",
                respuesta=respuesta[:500] if respuesta else "",
                sesion_id=str(id(self)),
                intencion=consulta.intencion_principal,
                confianza=float(pendiente.get('confianza', consulta.confianza)),
                usuario=None
            )

        if self.logger and tiempo_inicio:
            duracion_s = (datetime.now() - tiempo_inicio).total_seconds()
            self.logger.registrar_rendimiento(
                modulo="InterfazAndromeda._resolver_confirmacion_critica",
                operacion=consulta.accion_sugerida,
                tiempo_ms=duracion_s * 1000,
                exitosa=True
            )
        return historial, tabla_html, f"✓ {consulta.accion_sugerida} (confirmada)"

    def _generar_fallback_estructurado(self, consulta: ConsultaEntendida) -> str:
        """Genera fallback inteligente cuando la confianza es baja."""
        sugerencias = []
        if consulta.subintenciones:
            sugerencias.extend(consulta.subintenciones[:3])

        # Intentar entender qué quiso decir el usuario usando fragmentos clave
        interpretacion = ""
        if NORMALIZADOR_DISPONIBLE:
            try:
                norm = obtener_normalizador()
                resultado = norm.normalizar(consulta.contexto)
                if resultado.fragmentos_clave:
                    # Sugerir intenciones basadas en fragmentos detectados
                    for frag in resultado.fragmentos_clave[:3]:
                        sugerencias.append(frag)
                if resultado.correcciones:
                    interpretacion = f"\n\n*Interpreté:* \"{resultado.texto_normalizado}\""
            except Exception:
                pass

        if not sugerencias:
            sugerencias = [
                "ventas de hoy",
                "inventario actual",
                "top 10 productos",
                "tendencia de ventas por marca"
            ]

        sugerencias_md = "\n".join([f"- {s}" for s in sugerencias])
        return (
            "No pude determinar con suficiente certeza qué información necesitas.\n\n"
            f"**Confianza:** {consulta.confianza:.0%} | **Umbral mínimo:** {self.intent_confidence_threshold:.0%}"
            f"{interpretacion}\n\n"
            "Intenta con alguna de estas opciones o reformula con más detalle:\n"
            f"{sugerencias_md}"
        )

    def _registrar_ruteo_intencion(self, mensaje: str, consulta: ConsultaEntendida, agente: str, estado: str, motivo: str = ""):
        """Registra la decisión del router: intención, confianza y agente de destino."""
        if not self.logger:
            return
        try:
            self.logger.registrar_evento(
                tipo=TipoEvento.INTERACCION,
                mensaje=f"IntentRouter: {estado}",
                modulo="InterfazAndromeda.IntentRouter",
                contexto={
                    'mensaje': mensaje[:180],
                    'intencion': consulta.intencion_principal,
                    'accion': consulta.accion_sugerida,
                    'confianza': round(float(consulta.confianza), 4),
                    'umbral': round(float(self.intent_confidence_threshold), 4),
                    'agente': agente,
                    'motivo': motivo
                }
            )
        except Exception:
            pass
    
    def _obtener_entidades_cerebro(self, consulta) -> list:
        """
        Extrae las entidades del cerebro de una consulta.
        Las entidades pueden estar en un dict (de nlp_avanzado) o lista (de cerebro_nlp).
        """
        if not hasattr(consulta, 'entidades') or not consulta.entidades:
            return []
        
        if isinstance(consulta.entidades, dict):
            return consulta.entidades.get('_cerebro', [])
        elif isinstance(consulta.entidades, list):
            return consulta.entidades
        return []
    
    # Límite de longitud para protección contra DoS
    MAX_INPUT_LENGTH = 2000
    # Rate limiting: máximo de requests por minuto por sesión
    MAX_REQUESTS_PER_MINUTE = 30

    def procesar_mensaje(self, mensaje: str, historial: List[Dict]) -> Tuple[List[Dict], str, str]:
        """Procesa un mensaje con NLP avanzado, LLM y predicciones."""
        if not mensaje.strip():
            return historial, "", "✓ Listo"
        
        # ── VALIDACIÓN DE ENTRADA ──
        # Limitar longitud del input (protección DoS)
        if len(mensaje) > self.MAX_INPUT_LENGTH:
            mensaje = mensaje[:self.MAX_INPUT_LENGTH]
        
        # Rate limiting básico
        ahora = datetime.now()
        if not hasattr(self, '_request_timestamps'):
            self._request_timestamps = []
        # Limpiar timestamps mayores a 60 segundos
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if (ahora - ts).total_seconds() < 60
        ]
        if len(self._request_timestamps) >= self.MAX_REQUESTS_PER_MINUTE:
            historial.append({"role": "assistant", "content": "⚠️ Demasiadas consultas por minuto. Por favor espera un momento antes de continuar."})
            return historial, "", "⚠️ Rate limit"
        self._request_timestamps.append(ahora)
        
        # ── PRE-NORMALIZACIÓN GLOBAL DEL PROMPT ──
        # Se aplica ANTES de cualquier otro procesamiento para que
        # tanto el motor empático, LLM y NLP reciban texto limpio
        if NORMALIZADOR_DISPONIBLE:
            try:
                norm = obtener_normalizador()
                resultado_norm = norm.normalizar(mensaje)
                # Solo reemplazar si hubo correcciones reales
                if resultado_norm.correcciones:
                    mensaje = resultado_norm.texto_normalizado
            except Exception:
                pass

        # Registrar inicio del procesamiento
        tiempo_inicio = datetime.now() if self.logger else None

        # Recuperar memoria semántica relevante (sin alterar intención, solo contexto cognitivo)
        recuerdos_semanticos = []
        if self.memoria_jerarquica:
            try:
                recuerdos_semanticos = self.memoria_jerarquica.buscar_semantico(mensaje, limite=2)
            except Exception:
                recuerdos_semanticos = []
        
        historial.append({"role": "user", "content": mensaje})
        
        # 1. Respuestas empáticas rápidas
        resp_empatica, tipo_emp = self.motor_empatico.procesar_mensaje(mensaje)
        if tipo_emp in ['saludo', 'despedida']:
            historial.append({"role": "assistant", "content": resp_empatica})

            if self.memoria_jerarquica:
                self.memoria_jerarquica.registrar_interaccion(
                    mensaje_usuario=mensaje,
                    respuesta=resp_empatica,
                    intencion=tipo_emp,
                    accion='respuesta_empatica',
                    confianza=1.0,
                    parametros={},
                    modelo_erp=self.ultimo_modelo,
                    metadata_extra={'recuerdos_semanticos': len(recuerdos_semanticos)}
                )
            
            # Registrar evento
            if self.logger:
                self.logger.registrar_evento(
                    tipo=TipoEvento.INTERACCION,
                    mensaje=f"Saludo/Despedida: {tipo_emp}",
                    modulo="InterfazAndromeda.procesar_mensaje",
                    contexto={'mensaje': mensaje, 'respuesta': resp_empatica}
                )
            
            return historial, "", f"✓ {tipo_emp}"

        # 1b. Pre-interceptar solicitud de gráfica contextual pura.
        # Solo activa si el mensaje ES SOLO sobre gráfica (no contiene solicitud de datos nuevos)
        # para evitar que "ventas por tienda con gráfica" se intercepte aquí.
        _palabras_datos = {
            'ventas', 'venta', 'inventario', 'stock', 'factura', 'cliente', 'compra',
            'producto', 'tienda', 'pos', 'pedido', 'cobrar', 'pagar', 'predicci',
            'predice', 'analiza', 'análisis', 'reporte', 'informe', 'kpi', 'financiero',
        }
        _msg_lower = mensaje.lower()
        _tiene_datos = any(p in _msg_lower for p in _palabras_datos)
        if self._quiere_grafica(mensaje) and not _tiene_datos and self.ultimo_df is not None:
            grafica_html = self._generar_html_grafica(None, mensaje)
            if grafica_html:
                respuesta_grafica = (
                    "📊 **Visualización generada** a partir de los últimos datos consultados:\n\n"
                    + grafica_html
                )
                historial.append({"role": "assistant", "content": respuesta_grafica})
                return historial, self._df_a_html(self.ultimo_df.head(30)), "✓ grafica_contextual"
        
        # 2. Si LLM está activo, usar el agente inteligente
        if self.llm_activo and self.agente_llm:
            return self._procesar_con_llm(mensaje, historial, resp_empatica, tipo_emp, tiempo_inicio, recuerdos_semanticos)
        
        # 3. Fallback: Usar sistema NLP tradicional
        return self._procesar_tradicional(mensaje, historial, resp_empatica, tipo_emp, tiempo_inicio, recuerdos_semanticos)
    
    def _procesar_con_llm(self, mensaje: str, historial: List[Dict], resp_empatica: str, tipo_emp: str, tiempo_inicio=None, recuerdos_semanticos: List[str] = None) -> Tuple[List[Dict], str, str]:
        """Procesa mensaje usando el cerebro LLM."""
        try:
            # Enriquecer mensaje con contexto de memoria si hay recuerdos relevantes
            mensaje_enriquecido = mensaje
            bloques_contexto = []
            if recuerdos_semanticos:
                contexto_mem = "\n".join(f"- {r}" for r in recuerdos_semanticos[:3])
                bloques_contexto.append(f"Conversaciones previas:\n{contexto_mem}")
            # Contexto relacional del grafo de conocimiento
            try:
                if hasattr(self, 'memoria_jerarquica') and self.memoria_jerarquica:
                    ctx_grafo = self.memoria_jerarquica.obtener_contexto_grafo(mensaje)
                    if ctx_grafo:
                        bloques_contexto.append(f"Relaciones conocidas:\n{ctx_grafo}")
            except Exception:
                pass
            if bloques_contexto:
                mensaje_enriquecido = f"{mensaje}\n\n[Contexto:\n" + "\n".join(bloques_contexto) + "]"

            # Obtener respuesta del agente
            respuesta_llm, accion = self.agente_llm.procesar(mensaje_enriquecido)
            
            df = None
            respuesta_final = respuesta_llm
            
            # Si detectó una acción, ejecutarla
            if accion and accion.accion:
                # Crear una consulta simulada para el sistema tradicional
                from services.nlp.nlp_avanzado import ConsultaEntendida
                consulta = ConsultaEntendida(
                    intencion_principal=accion.accion,
                    confianza=accion.confianza,
                    entidades=[],
                    parametros=accion.parametros,
                    temporalidad=self._extraer_temporalidad_simple(mensaje),
                    modificadores=[],
                    contexto=mensaje,
                    accion_sugerida=accion.accion,
                    respuesta_tipo=accion.tipo,
                    subintenciones=[]
                )
                
                try:
                    # Ejecutar la acción con el sistema unificado
                    agente_llm = self._detectar_agente_especializado(accion.accion, mensaje)

                    respuesta_accion, df = self._ejecutar_desde_gestor_agentes(consulta, mensaje, agente_llm)

                    # Validación de respuesta por agente especializado
                    if self.gestor_agentes:
                        try:
                            post_llm = self.gestor_agentes.post_ejecutar(
                                agente_id=agente_llm,
                                consulta=consulta,
                                respuesta=respuesta_accion,
                                df=df,
                                error=False
                            )
                            respuesta_accion = post_llm.respuesta
                        except Exception:
                            pass
                    
                    # Combinar respuesta del LLM con datos
                    if respuesta_accion and not respuesta_accion.startswith("🤔"):
                        respuesta_final = respuesta_accion
                    else:
                        # Si la acción falló, usar respuesta del LLM
                        respuesta_final = respuesta_llm

                    respuesta_final, _, _, _ = self._validar_y_regenerar_respuesta(
                        respuesta=respuesta_final,
                        consulta=consulta,
                        mensaje=mensaje,
                        df=df,
                        confianza_operativa=float(getattr(accion, 'confianza', 0.7) or 0.7),
                    )
                        
                except Exception as e:
                    print(f"Error ejecutando acción LLM: {e}")
                    # Usar respuesta del LLM si falla la acción
                    respuesta_final = respuesta_llm
            
            # Estructura conversacional: Reconocimiento → Datos → Insight → Cierre
            if accion and accion.accion:
                respuesta_final = self._conclusiones.aplicar(
                    respuesta=respuesta_final,
                    accion=accion.accion,
                    intencion=accion.accion,
                    es_cadena=False,
                )

            # Agregar empatía si corresponde
            if resp_empatica and tipo_emp == 'emocional':
                respuesta_final = resp_empatica + "\n\n" + respuesta_final
            
            historial.append({"role": "assistant", "content": respuesta_final})
            
            # Generar tabla HTML / gráfica
            tabla_html = ""
            if df is not None and not df.empty:
                self.ultimo_df = df
                tabla_html = self._df_a_html(df.head(30))
            accion_str = (accion.accion if accion and hasattr(accion, 'accion') else '') or ''
            if self._quiere_grafica(mensaje, accion_str):
                grafica_html = self._generar_html_grafica(df, mensaje)
                if grafica_html:
                    # Insertar gráfica al final del mensaje del chat (chatbot acepta HTML)
                    if historial and historial[-1].get('role') == 'assistant':
                        historial[-1]['content'] += '\n\n' + grafica_html
                    if tabla_html:  # tabla sigue en el panel
                        tabla_html = grafica_html + "<hr/>" + tabla_html
                    else:
                        tabla_html = grafica_html

            # Guardar en memoria jerárquica (incluye semántica vectorial)
            if self.memoria_jerarquica:
                try:
                    memoria_params = accion.parametros if (accion and getattr(accion, 'parametros', None)) else {}
                    self.memoria_jerarquica.registrar_interaccion(
                        mensaje_usuario=mensaje,
                        respuesta=respuesta_final[:900],
                        intencion=accion.accion if accion else 'chat',
                        accion=accion.accion if accion else 'chat',
                        confianza=float(accion.confianza) if accion and getattr(accion, 'confianza', None) is not None else 0.7,
                        parametros=memoria_params,
                        modelo_erp=self.ultimo_modelo,
                        metadata_extra={'modo': 'llm', '_df': df}
                    )
                except Exception as e:
                    print(f"Error guardando memoria jerárquica: {e}")
            elif self.memoria:
                try:
                    self.memoria.guardar_conversacion(
                        mensaje_usuario=mensaje,
                        respuesta_andromeda=respuesta_final[:500],
                        intencion=accion.accion if accion else 'chat',
                        accion_ejecutada=accion.accion if accion else None
                    )
                except Exception as e:
                    print(f"Error guardando en memoria: {e}")
            
            status = f"✓ LLM ({accion.accion if accion else 'chat'})"
            return historial, tabla_html, status
            
        except Exception as e:
            import traceback
            print(f"Error con LLM, usando sistema tradicional: {e}")
            print(f"   Debug: Tipo error={type(e).__name__}, Mensaje={str(e)[:100]}")
            print(f"   Traceback: {traceback.format_exc()[:500]}")
            return self._procesar_tradicional(mensaje, historial, resp_empatica, tipo_emp, tiempo_inicio)
    
    def _extraer_temporalidad_simple(self, mensaje: str) -> Dict:
        """Extrae temporalidad básica del mensaje."""
        from datetime import datetime, timedelta
        import re
        hoy = datetime.now()
        
        mensaje_lower = mensaje.lower()
        
        # Primero buscar rangos de años "2025 y 2026"
        patron_rango = re.compile(r'(\d{4})\s*(?:y|a|al|hasta)\s*(\d{4})')
        match_rango = patron_rango.search(mensaje_lower)
        if match_rango:
            anio_inicio = int(match_rango.group(1))
            anio_fin = int(match_rango.group(2))
            if anio_fin < anio_inicio:
                anio_inicio, anio_fin = anio_fin, anio_inicio
            return {'fecha_inicio': f"{anio_inicio}-01-01", 'fecha_fin': f"{anio_fin}-12-31"}
        
        # Buscar año específico "año 2025", "todo 2025", "2025"
        patron_anio = re.compile(r'(?:todo\s+)?(?:el\s+)?(?:a[ñn]o\s+)?(\d{4})')
        match_anio = patron_anio.search(mensaje_lower)
        if match_anio:
            anio = int(match_anio.group(1))
            if 2000 <= anio <= 2100:
                return {'fecha_inicio': f"{anio}-01-01", 'fecha_fin': f"{anio}-12-31"}
        
        # Patrones de meses
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        for nombre_mes, num_mes in meses.items():
            if nombre_mes in mensaje_lower:
                # Buscar año asociado
                match_anio_mes = re.search(r'(\d{4})', mensaje_lower)
                anio = int(match_anio_mes.group(1)) if match_anio_mes else hoy.year
                primer_dia = datetime(anio, num_mes, 1)
                if num_mes == 12:
                    ultimo_dia = datetime(anio + 1, 1, 1) - timedelta(days=1)
                else:
                    ultimo_dia = datetime(anio, num_mes + 1, 1) - timedelta(days=1)
                return {'fecha_inicio': primer_dia.strftime('%Y-%m-%d'), 'fecha_fin': ultimo_dia.strftime('%Y-%m-%d')}
        
        if 'hoy' in mensaje_lower:
            return {'fecha_inicio': hoy.strftime('%Y-%m-%d'), 'fecha_fin': hoy.strftime('%Y-%m-%d')}
        elif 'ayer' in mensaje_lower:
            ayer = hoy - timedelta(days=1)
            return {'fecha_inicio': ayer.strftime('%Y-%m-%d'), 'fecha_fin': ayer.strftime('%Y-%m-%d')}
        elif 'semana' in mensaje_lower:
            inicio = hoy - timedelta(days=7)
            return {'fecha_inicio': inicio.strftime('%Y-%m-%d'), 'fecha_fin': hoy.strftime('%Y-%m-%d')}
        elif 'mes' in mensaje_lower:
            inicio = hoy.replace(day=1)
            return {'fecha_inicio': inicio.strftime('%Y-%m-%d'), 'fecha_fin': hoy.strftime('%Y-%m-%d')}
        else:
            # Default: último año (más útil que solo hoy)
            inicio = hoy - timedelta(days=365)
            return {'fecha_inicio': inicio.strftime('%Y-%m-%d'), 'fecha_fin': hoy.strftime('%Y-%m-%d')}
    
    def _procesar_tradicional(self, mensaje: str, historial: List[Dict], resp_empatica: str, tipo_emp: str, tiempo_inicio=None, recuerdos_semanticos: List[str] = None) -> Tuple[List[Dict], str, str]:
        """Procesa mensaje usando el sistema NLP tradicional."""
        # 0. Resolver confirmación pendiente de consultas críticas
        resultado_confirmacion = self._resolver_confirmacion_critica(mensaje, historial, tiempo_inicio)
        if resultado_confirmacion:
            return resultado_confirmacion

        # 0.1. Guardrail: modo solo lectura (sin mutaciones de BD)
        if self._es_solicitud_mutacion_bd(mensaje):
            respuesta = (
                "Por seguridad, ANDROMEDA está en modo **solo lectura**.\n\n"
                "Puedo ayudarte a **consultar, analizar y buscar datos**, pero no puedo crear, modificar o eliminar registros en la base de datos."
            )
            historial.append({"role": "assistant", "content": respuesta})
            if self.logger:
                self.logger.registrar_evento(
                    tipo=TipoEvento.INTERACCION,
                    mensaje="Solicitud bloqueada por política solo lectura",
                    modulo="InterfazAndromeda._procesar_tradicional",
                    contexto={'mensaje': mensaje[:200]}
                )
            return historial, "", "🔒 Solo lectura"

        # Detectar si es error/problema
        if self._es_consulta_error(mensaje):
            diagnostico = self.asistente_errores.diagnosticar(mensaje)
            respuesta = self.asistente_errores.formatear_diagnostico(diagnostico)
            historial.append({"role": "assistant", "content": respuesta})
            
            # Registrar evento de diagnóstico
            if self.logger:
                self.logger.registrar_evento(
                    tipo=TipoEvento.DIAGNOSTICO,
                    mensaje="Diagnóstico de error",
                    modulo="InterfazAndromeda._procesar_tradicional",
                    contexto={'mensaje': mensaje, 'diagnostico': str(diagnostico)[:200]}
                )
            
            return historial, "", "✓ Diagnóstico"
        
        # ── NORMALIZACIÓN DEL PROMPT ──
        # Corrige typos, expande abreviaciones, traduce coloquialismos
        mensaje_original = mensaje
        correcciones_prompt = []
        if NORMALIZADOR_DISPONIBLE:
            try:
                norm = obtener_normalizador()
                resultado_norm = norm.normalizar(mensaje)
                if resultado_norm.texto_normalizado != mensaje.lower().strip():
                    mensaje = resultado_norm.texto_normalizado
                    correcciones_prompt = resultado_norm.correcciones
                    if correcciones_prompt and self.logger:
                        self.logger.registrar_evento(
                            tipo=TipoEvento.INTERACCION,
                            mensaje="Prompt normalizado",
                            modulo="InterfazAndromeda._procesar_tradicional",
                            contexto={
                                'original': mensaje_original[:100],
                                'normalizado': mensaje[:100],
                                'correcciones': correcciones_prompt[:5]
                            }
                        )
            except Exception:
                pass

        # Procesar con NLP avanzado — única fuente de clasificación de intención.
        # La confianza proviene de similitud coseno real (MotorEmbeddings), no de un LLM.
        # Ollama/LLM entra DESPUÉS, solo para generación de texto (ver ejecutor_acciones.py).
        consulta = self.nlp.entender(mensaje)

        # Aplicar memoria contextual (modelo/filtros activos) antes de rutear
        if self.memoria_jerarquica:
            try:
                consulta = self.memoria_jerarquica.aplicar_contexto_a_consulta(consulta)
            except Exception:
                pass

        # 4. Intent Router unificado
        agente_especializado = self._detectar_agente_especializado(consulta.accion_sugerida, mensaje)
        confianza_agente = 0.7
        fuente_agente = 'router_unificado'
        advertencias_agente = []

        if self.gestor_agentes:
            try:
                agente_especializado, confianza_agente, fuente_agente = self.gestor_agentes.resolver_agente(
                    accion=consulta.accion_sugerida,
                    mensaje=mensaje
                )
                precheck = self.gestor_agentes.pre_ejecutar(agente_especializado, consulta, mensaje)
                consulta = precheck.consulta
                advertencias_agente = precheck.advertencias or []

                if not precheck.permitido:
                    respuesta = (
                        "La consulta fue detenida por reglas del agente especializado para evitar alucinaciones.\n\n"
                        f"**Agente:** {agente_especializado}\n"
                        f"**Motivo:** {precheck.motivo_bloqueo}"
                    )
                    df = None
                    self._registrar_ruteo_intencion(
                        mensaje=mensaje,
                        consulta=consulta,
                        agente=agente_especializado,
                        estado='bloqueado_por_reglas',
                        motivo='validacion_previa_agente'
                    )
                    historial.append({"role": "assistant", "content": respuesta})
                    return historial, "", "⛔ Bloqueado por reglas"
            except Exception as e:
                advertencias_agente.append(f'error_gestor_agente:{str(e)[:80]}')

        confianza_operativa = max(0.0, min(1.0, (consulta.confianza * 0.8) + (confianza_agente * 0.2)))

        if confianza_operativa < self.intent_confidence_threshold:
            respuesta = self._generar_fallback_estructurado(consulta)
            df = None
            self._registrar_ruteo_intencion(
                mensaje=mensaje,
                consulta=consulta,
                agente=agente_especializado,
                estado='fallback_baja_confianza',
                motivo=f'conf_operativa_bajo_umbral:{fuente_agente}'
            )

        elif self._requiere_confirmacion_critica(consulta.accion_sugerida, mensaje):
            self.confirmacion_critica_pendiente = {
                'consulta': consulta,
                'mensaje_original': mensaje,
                'accion': consulta.accion_sugerida,
                'agente': agente_especializado,
                'confianza': confianza_operativa,
                'timestamp': datetime.now().isoformat()
            }
            respuesta = (
                "Esta es una **consulta crítica** y requiere confirmación antes de ejecutarla.\n\n"
                f"- Intención: **{consulta.intencion_principal}**\n"
                f"- Acción: **{consulta.accion_sugerida}**\n"
                f"- Confianza operativa: **{confianza_operativa:.0%}**\n"
                f"- Agente: **{agente_especializado}**\n"
                f"- Fuente de selección: **{fuente_agente}**\n\n"
                "Responde **sí** para continuar o **no** para cancelar."
            )
            df = None
            self._registrar_ruteo_intencion(
                mensaje=mensaje,
                consulta=consulta,
                agente=agente_especializado,
                estado='esperando_confirmacion',
                motivo='consulta_critica'
            )

        else:
            self._registrar_ruteo_intencion(
                mensaje=mensaje,
                consulta=consulta,
                agente=agente_especializado,
                estado='ruteado',
                motivo=f'ejecucion_normal:{fuente_agente}'
            )
        
        # Registrar prompt procesado (después de obtener respuesta)
        # Se hará al final de _procesar_tradicional para tener la respuesta completa
        
        # Ejecutar acción con manejo de errores
        hubo_error_ejecucion = False
        cadena_info = None  # Resumen de cadena multi-agente si aplica
        if confianza_operativa >= self.intent_confidence_threshold and not self._requiere_confirmacion_critica(consulta.accion_sugerida, mensaje):
            try:
                # ── Detectar si requiere cadena multi-agente ──
                es_cadena = False
                pasos_cadena = []
                if self.gestor_agentes:
                    try:
                        es_cadena = self.gestor_agentes.es_cadena(
                            mensaje, consulta.accion_sugerida, agente_especializado
                        )
                        if es_cadena:
                            pasos_cadena = self.gestor_agentes.planificar_cadena(
                                mensaje, consulta.accion_sugerida, agente_especializado
                            )
                            # Pre-ejecución cadena: cada agente enriquece la consulta
                            pasos_cadena = self.gestor_agentes.pre_ejecutar_cadena(
                                pasos_cadena, consulta, mensaje
                            )
                    except Exception:
                        es_cadena = False

                respuesta, df = self._ejecutar_desde_gestor_agentes(
                    consulta,
                    mensaje,
                    agente_especializado
                )

                # ── Validación post-ejecución ──
                if self.gestor_agentes:
                    try:
                        if es_cadena and pasos_cadena:
                            # Cadena multi-agente: cada agente EJECUTA su paso y valida
                            resultado_cadena = self.gestor_agentes.ejecutar_cadena_completa(
                                pasos=pasos_cadena,
                                consulta=consulta,
                                mensaje=mensaje,
                                respuesta_principal=respuesta,
                                df_principal=df
                            )
                            respuesta = resultado_cadena.respuesta_final
                            confianza_operativa = max(0.0, min(1.0,
                                (confianza_operativa * 0.4) + (resultado_cadena.confianza_consolidada * 0.6)
                            ))
                            cadena_info = self.gestor_agentes.resumen_cadena(resultado_cadena)
                        else:
                            # Agente único
                            post = self.gestor_agentes.post_ejecutar(
                                agente_id=agente_especializado,
                                consulta=consulta,
                                respuesta=respuesta,
                                df=df,
                                error=False
                            )
                            respuesta = post.respuesta
                            confianza_operativa = max(0.0, min(1.0,
                                (confianza_operativa * 0.7) + (post.confianza_datos * 0.3)
                            ))
                    except Exception:
                        pass
                
                # Registrar operación exitosa
                if self.logger and tiempo_inicio:
                    duracion_s = (datetime.now() - tiempo_inicio).total_seconds()
                    self.logger.registrar_rendimiento(
                        modulo="InterfazAndromeda._procesar_tradicional",
                        operacion=consulta.accion_sugerida,
                        tiempo_ms=duracion_s * 1000,
                        exitosa=True
                    )
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error en consulta: {e}")
                print(f"   Acción: {consulta.accion_sugerida}")
                print(f"   Mensaje: {mensaje[:100]}")
                hubo_error_ejecucion = True
                
                # Registrar error
                if self.logger and NivelCriticidad:
                    try:
                        self.logger.registrar_error(
                            excepcion=e,
                            modulo="InterfazAndromeda._procesar_tradicional",
                            criticidad=NivelCriticidad.ALTO if "database" in str(e).lower() else NivelCriticidad.MEDIA,
                            contexto={
                                'accion': consulta.accion_sugerida,
                                'mensaje': mensaje[:200],
                                'tipo_error': type(e).__name__
                            }
                        )
                    except Exception:
                        logger.error(f"ERROR en InterfazAndromeda._procesar_tradicional: {type(e).__name__} - {e}")
                
                respuesta = f"**Error al procesar tu consulta**\n\n{str(e)}\n\nIntenta reformular tu pregunta o verifica la conexión con Odoo."
                df = None

                if self.gestor_agentes:
                    try:
                        post_error = self.gestor_agentes.post_ejecutar(
                            agente_id=agente_especializado,
                            consulta=consulta,
                            respuesta=respuesta,
                            df=None,
                            error=True
                        )
                        respuesta = post_error.respuesta
                        confianza_operativa = min(confianza_operativa, post_error.confianza_datos)
                    except Exception:
                        pass
        
        # Estructura conversacional: Reconocimiento → Datos → Insight → Cierre
        if not hubo_error_ejecucion:
            respuesta = self._conclusiones.aplicar(
                respuesta=respuesta,
                accion=consulta.accion_sugerida,
                intencion=consulta.intencion_principal,
                es_cadena=bool(cadena_info),
            )

        # Agregar empatía si corresponde
        if resp_empatica and tipo_emp == 'emocional':
            respuesta = resp_empatica + "\n\n" + respuesta
        
        # Agregar resumen de cadena multi-agente si aplica
        if cadena_info:
            respuesta = respuesta + "\n\n---\n" + cadena_info

        respuesta, confianza_operativa, problemas_validacion, intentos_validacion = self._validar_y_regenerar_respuesta(
            respuesta=respuesta,
            consulta=consulta,
            mensaje=mensaje,
            df=df,
            confianza_operativa=confianza_operativa,
        )
        if problemas_validacion and self.logger:
            self.logger.registrar_evento(
                tipo=TipoEvento.INTERACCION,
                mensaje=f"Respuesta validada con reintentos: {intentos_validacion}",
                modulo="InterfazAndromeda.ValidadorRespuestas",
                contexto={
                    'problemas': problemas_validacion[:5],
                    'confianza_final': round(confianza_operativa, 2),
                    'accion': consulta.accion_sugerida,
                }
            )
        
        # Anexar advertencias del agente al usuario (si son relevantes)
        if advertencias_agente:
            notas = self._traducir_advertencias(advertencias_agente)
            if notas:
                respuesta = respuesta + "\n\n> **Nota:** " + " | ".join(notas)
        
        historial.append({"role": "assistant", "content": respuesta})
        
        # Generar tabla HTML / gráfica
        tabla_html = ""
        if df is not None and not df.empty:
            self.ultimo_df = df
            tabla_html = self._df_a_html(df.head(30))
        accion_trad = getattr(consulta, 'accion_sugerida', '') or ''
        if self._quiere_grafica(mensaje, accion_trad):
            grafica_html = self._generar_html_grafica(df, mensaje)
            if grafica_html:
                # Insertar gráfica al final del mensaje del chat
                if historial and historial[-1].get('role') == 'assistant':
                    historial[-1]['content'] += '\n\n' + grafica_html
                tabla_html = grafica_html + ("<hr/>" + tabla_html if tabla_html else "")

        # Registrar prompt después de procesar
        if self.logger:
            self.logger.registrar_prompt(
                prompt_original=mensaje,
                respuesta=respuesta[:500] if respuesta else "",
                sesion_id=str(id(self)),
                intencion=consulta.intencion_principal,
                confianza=confianza_operativa,
                usuario=None
            )

        # Registrar memoria jerárquica (sesión/contexto/preferencias/semántica)
        if self.memoria_jerarquica:
            try:
                memoria_params = dict(consulta.parametros or {})
                if isinstance(consulta.temporalidad, dict):
                    if consulta.temporalidad.get('fecha_inicio'):
                        memoria_params['fecha_inicio'] = consulta.temporalidad.get('fecha_inicio')
                    if consulta.temporalidad.get('fecha_fin'):
                        memoria_params['fecha_fin'] = consulta.temporalidad.get('fecha_fin')

                self.memoria_jerarquica.registrar_interaccion(
                    mensaje_usuario=mensaje,
                    respuesta=respuesta[:900] if respuesta else "",
                    intencion=consulta.intencion_principal,
                    accion=consulta.accion_sugerida,
                    confianza=confianza_operativa,
                    parametros=memoria_params,
                    modelo_erp=self.ultimo_modelo,
                    metadata_extra={
                        'modo': 'tradicional',
                        'status': 'ok',
                        'agente': agente_especializado,
                        'advertencias_agente': ';'.join(advertencias_agente)[:200],
                        '_df': df,  # Para extracción de entidades en el grafo
                    }
                )
            except Exception as e:
                print(f"Error en memoria jerárquica: {e}")
        
        # Status con info de confianza
        if confianza_operativa < self.intent_confidence_threshold:
            status = f"⚠️ fallback ({confianza_operativa:.0%})"
        elif self._requiere_confirmacion_critica(consulta.accion_sugerida, mensaje):
            status = f"⚠️ confirmación requerida ({confianza_operativa:.0%})"
        else:
            chain_marker = " 🔗" if cadena_info else ""
            status = f"✓ {consulta.accion_sugerida} [{agente_especializado}]{chain_marker} ({confianza_operativa:.0%})"
        
        return historial, tabla_html, status
    

    # ============================================================
    # TRADUCCIÓN DE ADVERTENCIAS INTERNAS → TEXTO USUARIO
    # ============================================================

    _MAPA_ADVERTENCIAS = {
        'temporalidad_default_30_dias': 'Se usaron los últimos 30 días como periodo por defecto.',
        'margen_requiere_campo_costo_verificar_disponibilidad': 'El cálculo de margen requiere campo de costo; si no está configurado, el resultado puede ser parcial.',
        'comparativa_sin_periodos_explicitos_usar_mes_anterior': 'No se especificaron periodos, se comparó con el mes anterior.',
        'limite_ajustado_200': 'Se limitaron los resultados a 200 registros para estabilidad.',
        'stock_negativo_puede_indicar_movimientos_pendientes': 'Se detectó stock negativo; puede haber movimientos pendientes de procesar.',
        'abc_requiere_datos_costo_y_movimiento_verificar': 'El análisis ABC requiere datos de costo y movimiento; verificar que estén completos.',
        'merma_verificar_tipo_movimiento_scrap_adjustment': 'Análisis de merma basado en movimientos tipo scrap/adjustment.',
        'rango_financiero_default_30_dias': 'Se usaron los últimos 30 días como periodo financiero por defecto.',
        'cxc_debe_filtrar_solo_facturas_posted_open': 'CxC filtrada solo para facturas en estado publicado/abierto.',
        'conciliacion_requiere_cruce_pagos_y_facturas': 'La conciliación requiere cruce de pagos y facturas; verificar datos completos.',
        'ratio_requiere_balance_completo_verificar_datos': 'Las ratios financieras requieren balance completo; verificar datos.',
    }

    def _traducir_advertencias(self, advertencias: list) -> list:
        """Convierte advertencias internas a texto entendible para el usuario."""
        notas = []
        for adv in advertencias:
            if adv.startswith('error_gestor_agente:'):
                continue  # Los errores internos no se muestran al usuario
            texto = self._MAPA_ADVERTENCIAS.get(adv)
            if texto:
                notas.append(texto)
        return notas

    # ============================================================
    # ACCIONES — Delegadas a EjecutorAcciones (ARQ-v2-001)
    # ============================================================

    def _ejecutar_accion(self, consulta, mensaje: str = ""):
        """Delega a EjecutorAcciones.ejecutar() — ver services/actions/ejecutor_acciones.py"""
        return self._ejecutor_acciones.ejecutar(consulta, mensaje)

    def _generar_ayuda_completa(self) -> str:
        """Delega a EjecutorAcciones — mantiene compatibilidad post-refactor ARQ-v2-001."""
        return self._ejecutor_acciones._generar_ayuda_completa()

    def _mapear_accion_a_consulta_odoo(self, accion: str, fecha_ini: str, fecha_fin: str, params: dict, consulta) -> dict:
        """Delega a MapeadorConsultas.mapear() — ver services/actions/mapeador_consultas.py"""
        return self._mapeador_consultas.mapear(accion, fecha_ini, fecha_fin, params, consulta)

    def _resumen_confiable_desde_dataframe(self, consulta: ConsultaEntendida, df) -> str:
        """Genera un informe ejecutivo desde el DataFrame — formato Junta Directiva / CDO."""
        import pandas as _pd
        from datetime import datetime as _dt

        accion_raw = getattr(consulta, 'accion_sugerida', '') or getattr(consulta, 'intencion_principal', 'consulta')
        accion_legible = accion_raw.replace('_', ' ').title()
        n = len(df)

        # ── 1. Limpiar campos many2one [id, 'Name'] ───────────────────────────
        df = df.copy()
        for col in df.columns:
            try:
                df[col] = df[col].apply(
                    lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) == 2 else x
                )
            except Exception:
                pass

        # ── 2. Excluir columnas técnicas ──────────────────────────────────────
        _excluir = {'id', 'write_uid', 'create_uid', 'message_follower_ids',
                    'activity_ids', 'message_ids', 'currency_id', 'company_id'}
        df = df[[c for c in df.columns if c not in _excluir and not str(c).endswith('_uid')]]
        if df.empty:
            return f"## 📊 {accion_legible}\n\n> Sin datos disponibles para presentar."

        # ── 3. Detectar columna de entidad/categoría ──────────────────────────
        _prio_cat = ['partner_id', 'product_id', 'config_id', 'team_id', 'categ_id',
                     'warehouse_id', 'journal_id', 'department_id', 'user_id',
                     'Tienda', 'Cliente', 'Producto', 'Vendedor', 'name', 'x_name']
        col_cat = None
        for p in _prio_cat:
            if p in df.columns:
                col_cat = p
                break
        if col_cat is None:
            obj_cols = [c for c in df.columns if df[c].dtype == object]
            if obj_cols:
                col_cat = obj_cols[0]

        # ── 4. Detectar columna monetaria principal ───────────────────────────
        _prio_mon = ['amount_total', 'amount_untaxed', 'price_subtotal', 'price_total',
                     'lst_price', 'standard_price', 'wage', 'debit', 'balance',
                     'Ventas Total', 'Ventas_Total', 'total', 'subtotal', 'monto']
        col_mon = None
        try:
            num_cols = df.select_dtypes(include=['number']).columns.tolist()
        except Exception:
            num_cols = []
        for p in _prio_mon:
            if p in num_cols:
                col_mon = p
                break
        if col_mon is None and num_cols:
            col_mon = num_cols[0]

        es_monetaria = col_mon and (
            any(k in str(col_mon).lower() for k in ('amount', 'price', 'total', 'cost', 'wage', 'ventas', 'monto', 'balance', 'debit'))
        )

        # ── 5. Encabezado ejecutivo ───────────────────────────────────────────
        lineas = [f"## 📊 {accion_legible}", ""]
        lineas.append(f"> **{n:,}** registros analizados &nbsp;|&nbsp; {_dt.now().strftime('%d/%m/%Y %H:%M')}")
        lineas.append("")

        # ── 6. Si hay categoría + monto → tabla de ranking ────────────────────
        if col_cat and col_mon and n > 1:
            total_global = df[col_mon].sum()
            try:
                ranking = (
                    df.groupby(col_cat, as_index=False)[col_mon]
                    .sum()
                    .sort_values(col_mon, ascending=False)
                    .head(10)
                    .reset_index(drop=True)
                )
                label_cat = str(col_cat).replace('_id', '').replace('_', ' ').title()
                label_mon = str(col_mon).replace('_', ' ').title()
                lineas.append(f"### Ranking por {label_cat}")
                lineas.append("")
                lineas.append(f"| # | {label_cat} | {label_mon} | % del Total |")
                lineas.append(f"|---|{'---'*max(1,len(label_cat)//3)}|{'-'*10}|------------|")
                for i, row in ranking.iterrows():
                    val = row[col_mon]
                    pct = (val / total_global * 100) if total_global > 0 else 0
                    fmt_val = f"${val:,.2f}" if es_monetaria else f"{val:,.1f}"
                    cat_name = str(row[col_cat])[:40]
                    lineas.append(f"| {i+1} | {cat_name} | **{fmt_val}** | {pct:.1f}% |")
                lineas.append("")

                # Insights automáticos
                if len(ranking) >= 2:
                    lider = ranking.iloc[0]
                    ultimo = ranking.iloc[-1]
                    pct_lider = (lider[col_mon] / total_global * 100) if total_global > 0 else 0
                    lineas.append("### Hallazgos Clave")
                    lineas.append("")
                    fmt_l = f"${lider[col_mon]:,.2f}" if es_monetaria else f"{lider[col_mon]:,.1f}"
                    fmt_u = f"${ultimo[col_mon]:,.2f}" if es_monetaria else f"{ultimo[col_mon]:,.1f}"
                    lineas.append(f"- **Líder:** {str(lider[col_cat])[:40]} concentra el **{pct_lider:.0f}%** del total ({fmt_l}).")
                    brecha_pct = ((lider[col_mon] - ultimo[col_mon]) / lider[col_mon] * 100) if lider[col_mon] > 0 else 0
                    lineas.append(f"- **Brecha líder/último:** {brecha_pct:.0f}% — de {fmt_l} a {fmt_u}.")
                    top3_pct = (ranking.head(3)[col_mon].sum() / total_global * 100) if total_global > 0 else 0
                    if top3_pct > 70:
                        lineas.append(f"- **Alta concentración:** el Top 3 acumula el {top3_pct:.0f}% del total. Riesgo de dependencia.")
                    fmt_tot = f"${total_global:,.2f}" if es_monetaria else f"{total_global:,.1f}"
                    lineas.append(f"- **Total consolidado:** {fmt_tot} en {n} registros.")
                    lineas.append("")
            except Exception:
                pass  # fallback a tabla simple si groupby falla

        elif col_mon and num_cols:
            # Solo numéricos — resumen ejecutivo de KPIs
            lineas.append("### Resumen Ejecutivo")
            lineas.append("")
            lineas.append("| Indicador | Valor |")
            lineas.append("|-----------|-------|")
            for col in num_cols[:5]:
                serie = df[col].dropna()
                if serie.empty:
                    continue
                label = str(col).replace('_', ' ').title()
                es_mon_col = any(k in col.lower() for k in ('amount', 'price', 'total', 'cost', 'wage', 'ventas', 'monto'))
                total = serie.sum()
                fmt = f"${total:,.2f}" if es_mon_col else f"{total:,.0f}"
                lineas.append(f"| {label} | **{fmt}** |")
            lineas.append("")

        else:
            # Solo texto — mostrar primeras filas
            lineas.append("### Datos")
            lineas.append("")
            try:
                lineas.append(df.head(15).to_markdown(index=False))
            except Exception:
                for _, row in df.head(10).iterrows():
                    lineas.append("- " + " | ".join(f"**{k}:** {v}" for k, v in row.items() if _pd.notna(v)))
            lineas.append("")

        lineas.append(f"_Análisis ejecutivo generado por **ANDROMEDA** · Datos verificados en tiempo real · {_dt.now().strftime('%d/%m/%Y %H:%M')}_")
        return "\n".join(lineas)

    def _regenerar_respuesta_confiable(self, consulta: ConsultaEntendida, mensaje: str, respuesta_actual: str, df, problemas: List[str], intento: int) -> str:
        """Reintenta generar una respuesta más confiable priorizando datos reales."""
        accion_legible = (getattr(consulta, 'accion_sugerida', '') or getattr(consulta, 'intencion_principal', 'consulta')).replace('_', ' ').title()

        if df is not None and hasattr(df, 'empty') and not df.empty:
            if hasattr(self, 'cerebro_llm') and self.cerebro_llm:
                try:
                    contexto_datos = df.head(15).to_string(index=False)
                    prompt = (
                        f"Reformula la respuesta para la consulta '{mensaje}'.\n"
                        f"Acción: {accion_legible}.\n"
                        f"Problemas detectados: {', '.join(problemas) or 'baja confiabilidad'}.\n"
                        f"Datos verificables:\n{contexto_datos}\n\n"
                        "Instrucciones estrictas:\n"
                        "- Usa solo hechos visibles en los datos\n"
                        "- Si algo no se puede concluir, dilo explícitamente\n"
                        "- No inventes métricas ni causas\n"
                        "- Entrega una respuesta breve, concreta y trazable\n"
                        f"- Este es el intento {intento} de corrección"
                    )
                    regenerada = self.cerebro_llm.generar(prompt, temperatura=0.1, max_tokens=380)
                    contenido = getattr(regenerada, 'contenido', '') if regenerada else ''
                    if contenido and contenido.strip():
                        return contenido.strip()
                except Exception:
                    pass

            return self._resumen_confiable_desde_dataframe(consulta, df)

        return self._ejecutor_acciones._respuesta_accion_no_disponible(accion_legible)

    def _validar_y_regenerar_respuesta(self, respuesta: str, consulta: ConsultaEntendida, mensaje: str, df, confianza_operativa: float) -> Tuple[str, float, List[str], int]:
        """Valida y, si hace falta, reintenta generar una respuesta más confiable."""
        if not respuesta or not VALIDADOR_RESPUESTAS_DISPONIBLE:
            return respuesta, confianza_operativa, [], 0

        try:
            validador = obtener_validador()
        except Exception:
            return respuesta, confianza_operativa, [], 0

        respuesta_actual = respuesta
        confianza_actual = confianza_operativa
        problemas_ultimo_intento: List[str] = []
        max_intentos = 3

        for intento in range(1, max_intentos + 1):
            resultado_val = validador.validar(
                respuesta=respuesta_actual,
                consulta_original=mensaje,
                accion=consulta.accion_sugerida,
                tipo_respuesta=consulta.respuesta_tipo,
                df=df,
                confianza_previa=confianza_actual,
            )
            respuesta_actual = resultado_val.respuesta_validada
            confianza_actual = resultado_val.confianza_respuesta
            problemas_ultimo_intento = resultado_val.problemas or []

            requiere_reintento = (
                resultado_val.accion_correctiva == 'rechazada'
                or confianza_actual < 0.45
            )
            if not requiere_reintento or intento == max_intentos:
                return respuesta_actual, confianza_actual, problemas_ultimo_intento, intento

            nueva_respuesta = self._regenerar_respuesta_confiable(
                consulta=consulta,
                mensaje=mensaje,
                respuesta_actual=respuesta_actual,
                df=df,
                problemas=problemas_ultimo_intento,
                intento=intento + 1,
            )
            if not nueva_respuesta or nueva_respuesta.strip() == respuesta_actual.strip():
                return respuesta_actual, confianza_actual, problemas_ultimo_intento, intento
            respuesta_actual = nueva_respuesta

        return respuesta_actual, confianza_actual, problemas_ultimo_intento, max_intentos

    def _respuesta_inteligente(self, consulta: ConsultaEntendida) -> str:
        return f"""Entendí que quieres información sobre **{consulta.intencion_principal.replace('_', ' ')}** 
(confianza: {consulta.confianza:.0%})

**Prueba con:**
• "Analiza las ventas del mes"
• "Predice las ventas para 7 días"
• "Score de salud del negocio"
• "Top 10 clientes"
• "Cuentas por cobrar"
• "Qué puedes hacer"

 _Habla naturalmente, entiendo contexto._"""
    
    def _es_consulta_error(self, mensaje: str) -> bool:
        return any(x in mensaje.lower() for x in ['error', 'falla', 'no funciona', 'traceback'])
    
    # Columnas que representan valores monetarios (para formateo con $)
    _COLUMNAS_MONETARIAS = {
        'amount_total', 'amount_untaxed', 'amount_tax', 'amount_due',
        'amount_residual', 'amount_paid', 'price_subtotal', 'price_total',
        'price_unit', 'total', 'subtotal', 'balance', 'debit', 'credit',
        'wage', 'standard_price', 'lst_price', 'list_price', 'cost',
        'margin', 'profit', 'revenue', 'amount', 'monto', 'saldo',
        'precio', 'costo', 'ingreso', 'egreso', 'valor', 'sum',
        'price_reduce', 'price_reduce_taxinc', 'amount_residual_signed',
    }

    # ── Palabras clave que indican solicitud de gráfica ──────────────────────
    _PALABRAS_GRAFICA = {
        'grafica', 'gráfica', 'grafico', 'gráfico', 'grafic', 'graficame',
        'graficar', 'visualiza', 'visualizar', 'chart', 'plot', 'dibuja',
        'muestra.*grafica', 'genera.*grafica', 'crea.*grafica',
    }

    def _quiere_grafica(self, mensaje: str, accion: str = "") -> bool:
        """Detecta si el usuario solicitó una gráfica."""
        msg = mensaje.lower()
        return (
            any(p in msg for p in self._PALABRAS_GRAFICA)
            or str(accion).startswith('graficar')
        )

    def _generar_html_grafica(self, df, mensaje: str) -> str:
        """Genera HTML de gráfica. Si df está vacío usa self.ultimo_df."""
        if not self.generador_graficas:
            return ""

        # ── Caso especial: predicción de ventas ───────────────────────────────
        # El ejecutor almacena el objeto PrediccionInteligente completo en
        # self.ultima_prediccion para poder graficar histórico + proyección.
        ultima_pred = getattr(self, 'ultima_prediccion', None)
        if ultima_pred is not None and getattr(ultima_pred, 'datos_proyectados', None):
            try:
                resultado_pred = self.generador_graficas.grafica_prediccion(
                    datos_historicos=getattr(ultima_pred, 'datos_historicos', [])[-30:],
                    datos_proyectados=ultima_pred.datos_proyectados,
                    titulo=getattr(ultima_pred, 'titulo', 'Predicción de Ventas'),
                    contexto=mensaje,
                )
                self.ultima_prediccion = None  # consumir: no reutilizar en siguiente llamada
                if resultado_pred:
                    if resultado_pred.strip().startswith('<'):
                        return resultado_pred
                    return f'<img src="{resultado_pred}" style="max-width:100%;border-radius:8px;margin-top:8px" />'
            except Exception as e_pred:
                print(f"Error generando gráfica predicción: {e_pred}")
                self.ultima_prediccion = None
        # ── Flujo normal ───────────────────────────────────────────────────────
        df_usar = df
        if df_usar is None or (hasattr(df_usar, 'empty') and df_usar.empty):
            if self.ultimo_df is not None and hasattr(self.ultimo_df, 'empty') and not self.ultimo_df.empty:
                df_usar = self.ultimo_df
            else:
                return ""
        try:
            resultado = self.generador_graficas.generar_grafica_auto(
                df=df_usar,
                contexto=mensaje,
            )
            if not resultado:
                return ""
            # Plotly → HTML div; Matplotlib → data:image/png;base64,...
            if resultado.strip().startswith('<'):
                return resultado
            return f'<img src="{resultado}" style="max-width:100%;border-radius:8px;margin-top:8px" />'
        except Exception as e:
            print(f"Error generando gráfica: {e}")
            return ""

    def _es_columna_monetaria(self, nombre_col: str) -> bool:
        """Detecta si una columna contiene valores monetarios por su nombre."""
        nombre = nombre_col.lower().strip()
        if nombre in self._COLUMNAS_MONETARIAS:
            return True
        for patron in ('amount', 'price', 'total', 'cost', 'wage', 'monto', 'precio', 'saldo'):
            if patron in nombre:
                return True
        return False

    def _df_a_html(self, df) -> str:
        if df.empty:
            return ""
        
        df_c = df.copy()
        for col in df_c.columns:
            df_c[col] = df_c[col].apply(lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else x)
        
        # Detectar columnas monetarias una sola vez
        cols_monetarias = {col for col in df_c.columns if self._es_columna_monetaria(str(col))}
        
        # Nombres legibles para columnas comunes de Odoo
        nombres_legibles = {
            'amount_total': 'Total', 'amount_untaxed': 'Subtotal',
            'amount_tax': 'Impuestos', 'amount_residual': 'Saldo Pendiente',
            'price_subtotal': 'Subtotal', 'price_unit': 'Precio Unit.',
            'product_uom_qty': 'Cantidad', 'qty_available': 'Disponible',
            'qty_on_hand': 'En Mano', 'virtual_available': 'Virtual',
            'name': 'Nombre', 'display_name': 'Nombre',
            'partner_id': 'Cliente/Proveedor', 'date_order': 'Fecha Orden',
            'invoice_date': 'Fecha Factura', 'state': 'Estado',
            'quantity': 'Cantidad', 'create_date': 'Fecha Creación',
        }
        
        html = """<div style="overflow-x:auto;border-radius:16px;border:1px solid #30363d;margin:10px 0;">
<table style="width:100%;border-collapse:collapse;font-size:13px;background:#0d1117;">
<thead><tr style="background:linear-gradient(135deg,#667eea,#764ba2);">"""
        
        for col in df_c.columns:
            nombre = nombres_legibles.get(str(col), str(col).replace('_', ' ').title())
            html += f'<th style="padding:14px;color:white;text-align:left;font-weight:600;">{nombre}</th>'
        html += "</tr></thead><tbody>"
        
        for i, row in df_c.iterrows():
            bg = "#161b22" if i % 2 == 0 else "#0d1117"
            html += f'<tr style="background:{bg};">'
            for col_name, val in zip(df_c.columns, row):
                if isinstance(val, float):
                    if pd.isna(val):
                        val = "—"
                    elif col_name in cols_monetarias:
                        val = f"{self.fmt._m}{val:,.2f}"
                    else:
                        val = f"{val:,.2f}" if val != int(val) else f"{int(val):,}"
                elif isinstance(val, (int,)):
                    val = f"{val:,}"
                html += f'<td style="padding:12px;color:#c9d1d9;border-bottom:1px solid #21262d;">{val}</td>'
            html += "</tr>"
        
        html += "</tbody></table></div>"
        return html
    
    # ============================================================
    # FORMATEADORES DE AUDITORÍA INTELIGENTE
    # ============================================================
    
    def crear_interfaz(self) -> gr.Blocks:
        """Crea la interfaz profesional estilo Gemini/ChatGPT."""
        
        # Obtener logo base64 (para HTML) y ruta (para avatar_images)
        logo_src = LOGO_BASE64 if LOGO_BASE64 else ""
        logo_img = f'<img src="{logo_src}" alt="Logo">' if logo_src else '<i class="fas fa-rocket" style="font-size:24px;color:white;"></i>'
        logo_img_header = f'<img src="{logo_src}" alt="Logo" style="height: 40px; width: auto;">' if logo_src else ''
        
        # Ruta del archivo logo para avatar_images (Gradio 6.x no soporta base64 directamente)
        import os
        # Buscar logo en varias ubicaciones posibles
        base_dir = os.path.dirname(os.path.dirname(__file__))  # Raíz del proyecto
        posibles_logos = [
            os.path.join(base_dir, "assets", "logo.png"),
            os.path.join(base_dir, "logo.png"),
            os.path.join(os.path.dirname(__file__), "logo.png")
        ]
        logo_file = None
        for path in posibles_logos:
            if os.path.exists(path):
                logo_file = path
                break
        
        with gr.Blocks(title=f"{self.NOMBRE} v{self.VERSION}", theme=gr.themes.Base()) as app:
            
            # Estado para el panel de acciones
            _panel_abierto = gr.State(False)
            
            # ============== LAYOUT PRINCIPAL ==============
            with gr.Row(elem_classes=["main-layout"]):
                
                # ============== SIDEBAR IZQUIERDO ==============
                with gr.Column(scale=0, min_width=280, elem_classes=["sidebar-col"]):
                    gr.HTML(f"""
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
                    
                    <!-- Canvas de estrellas animadas -->
                    <canvas id="starsCanvas"></canvas>
                    <script>
                    (function() {{
                        var canvas = document.getElementById('starsCanvas');
                        if (!canvas) return;
                        var ctx = canvas.getContext('2d');
                        var stars = [];
                        var numStars = 150;
                        
                        function resize() {{
                            canvas.width = window.innerWidth;
                            canvas.height = window.innerHeight;
                        }}
                        resize();
                        window.addEventListener('resize', resize);
                        
                        for (var i = 0; i < numStars; i++) {{
                            stars.push({{
                                x: Math.random() * canvas.width,
                                y: Math.random() * canvas.height,
                                size: Math.random() * 2 + 0.5,
                                speedX: (Math.random() - 0.5) * 0.3,
                                speedY: (Math.random() - 0.5) * 0.3,
                                brightness: Math.random() * 0.5 + 0.5,
                                twinkleSpeed: Math.random() * 0.02 + 0.01,
                                color: Math.random() > 0.8 ? 'rgba(102,126,234,' : (Math.random() > 0.9 ? 'rgba(118,75,162,' : 'rgba(255,255,255,')
                            }});
                        }}
                        
                        function animate() {{
                            ctx.clearRect(0, 0, canvas.width, canvas.height);
                            
                            stars.forEach(function(star) {{
                                star.x += star.speedX;
                                star.y += star.speedY;
                                star.brightness += star.twinkleSpeed;
                                if (star.brightness > 1 || star.brightness < 0.3) star.twinkleSpeed *= -1;
                                
                                if (star.x < 0) star.x = canvas.width;
                                if (star.x > canvas.width) star.x = 0;
                                if (star.y < 0) star.y = canvas.height;
                                if (star.y > canvas.height) star.y = 0;
                                
                                ctx.beginPath();
                                ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
                                ctx.fillStyle = star.color + star.brightness + ')';
                                ctx.fill();
                            }});
                            
                            requestAnimationFrame(animate);
                        }}
                        animate();
                    }})();
                    </script>
                    
                    <!-- Botón Toggle Fijo con JavaScript inline -->
                    <button class="sidebar-toggle" id="sidebarToggleBtn" title="Colapsar menú" onclick="
                        (function() {{
                            var sidebar = document.getElementById('sidebar');
                            var btn = document.getElementById('sidebarToggleBtn');
                            if (!sidebar) return;
                            
                            var isCollapsed = sidebar.classList.toggle('collapsed');
                            if (btn) btn.classList.toggle('collapsed', isCollapsed);
                            
                            var margin = isCollapsed ? '70px' : '280px';
                            document.querySelectorAll('.main-content-col').forEach(function(el) {{ el.style.marginLeft = margin; }});
                            document.querySelectorAll('.top-header').forEach(function(el) {{ el.style.marginLeft = margin; }});
                            
                            try {{ localStorage.setItem('sidebarState', isCollapsed ? 'collapsed' : 'expanded'); }} catch(e) {{}}
                        }})()
                    ">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    
                    <div class="sidebar" id="sidebar">
                        <div class="sidebar-header">
                            <div class="sidebar-logo">
                                <div class="logo-container">
                                    {logo_img}
                                </div>
                                <h2>{self.NOMBRE}</h2>
                            </div>
                            <button class="new-chat-btn" onclick="location.reload()">
                                <i class="fas fa-plus"></i>
                                <span class="new-chat-text">Nueva Conversación</span>
                            </button>
                        </div>
                        
                        <div class="sidebar-menu">
                            <div>¿Qué Puedes hacer?</div>
                            <div class="menu-section">
                                <div class="menu-section-title">Análisis</div>
                                <div class="menu-item-static">
                                    <i class="fas fa-comments menu-item-icon"></i>
                                    <span>Chat IA</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-chart-pie menu-item-icon"></i>
                                    <span>Dashboard</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-chart-line menu-item-icon"></i>
                                    <span>Reportes</span>
                                </div>
                            </div>
                            <div class="menu-section">
                                <div class="menu-section-title">Predicciones</div>
                                <div class="menu-item-static">
                                    <i class="fas fa-crystal-ball menu-item-icon"></i>
                                    <span>Ventas Futuras</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-box-open menu-item-icon"></i>
                                    <span>Stock Crítico</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-money-bill-wave menu-item-icon"></i>
                                    <span>Flujo de Caja</span>
                                </div>
                            </div>
                            <div class="menu-section">
                                <div class="menu-section-title">Business Intelligence</div>
                                <div class="menu-item-static">
                                    <i class="fas fa-brain menu-item-icon"></i>
                                    <span>KPIs Ejecutivos</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-search-dollar menu-item-icon"></i>
                                    <span>Auditoría</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-exclamation-triangle menu-item-icon"></i>
                                    <span>Anomalías</span>
                                </div>
                            </div>
                            <div class="menu-section">
                                <div class="menu-section-title"> Auditoría Inteligente</div>
                                <div class="menu-item-static">
                                    <i class="fas fa-moon menu-item-icon"></i>
                                    <span>Auditoría Nocturna</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-traffic-light menu-item-icon"></i>
                                    <span>Semáforo Salud</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-user-slash menu-item-icon"></i>
                                    <span>Churn Clientes</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-boxes menu-item-icon"></i>
                                    <span>Reposición JIT</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-ghost menu-item-icon"></i>
                                    <span>Pagos Fantasma</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-search menu-item-icon"></i>
                                    <span>Calidad de Datos</span>
                                </div>
                            </div>
                            <div class="menu-section">
                                <div class="menu-section-title">Configuración</div>
                                <div class="menu-item">
                                    <i class="fas fa-cog menu-item-icon"></i>
                                    <span>Ajustes</span>
                                </div>
                                <div class="menu-item">
                                    <i class="fas fa-plug menu-item-icon"></i>
                                    <span>Conexión Odoo</span>
                                </div>
                                <div class="menu-item-static">
                                    <i class="fas fa-question-circle menu-item-icon"></i>
                                    <span>Ayuda</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="sidebar-footer">
                            <div class="user-info">
                                <div class="user-avatar">
                                    <i class="fas fa-user"></i>
                                </div>
                                <div class="user-details">
                                    <div class="user-name">{(self.odoo.config.usuario or 'usuario').split('@')[0]}</div>
                                    <div class="user-status">Conectado</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """)
                
                # ============== CONTENIDO PRINCIPAL ==============
                with gr.Column(scale=4, elem_classes=["main-content-col"]):
                    
                    # Header superior FIJO
                    gr.HTML(f"""
                    <div class="top-header" style="
                        position: sticky;
                        top: 0;
                        z-index: 1000;
                        padding: 16px 32px;
                        border-bottom: 1px solid rgba(102, 126, 234, 0.2);
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        background: rgba(15, 15, 35, 0.95);
                        backdrop-filter: blur(20px);
                        -webkit-backdrop-filter: blur(20px);
                        margin-left: 280px;
                        transition: margin-left 0.3s ease;
                    ">
                        <div class="header-title" style="display: flex; align-items: center; gap: 16px;">
                            {logo_img_header}
                            <h1 style="color: white; font-size: 1.5em; font-weight: 700; margin: 0;
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f64f59 100%);
                                -webkit-background-clip: text;
                                -webkit-text-fill-color: transparent;
                                background-clip: text;">
                                {self.NOMBRE}
                            </h1>
                        </div>
                        <div class="header-stats" style="display: flex; gap: 32px; align-items: center;">
                            <div class="stat-item" style="text-align: center;">
                                <div class="stat-value" style="color: #22c55e; font-size: 1.1em; font-weight: 700; display: flex; align-items: center; gap: 6px;">
                                    <span style="width: 8px; height: 8px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite;"></span>
                                    Online
                                </div>
                                <div class="stat-label" style="color: rgba(255,255,255,0.5); font-size: 11px;">ESTADO</div>
                            </div>
                            <div class="stat-item" style="text-align: center;">
                                <div class="stat-value" id="reloj-andromeda" style="color: white; font-size: 1.1em; font-weight: 700;">{datetime.now().strftime('%H:%M:%S')}</div>
                                <div class="stat-label" style="color: rgba(255,255,255,0.5); font-size: 11px;">HORA</div>
                            </div>
                        </div>
                    </div>
                    <style>
                        @keyframes pulse {{
                            0%, 100% {{ opacity: 1; }}
                            50% {{ opacity: 0.5; }}
                        }}
                    </style>
                    <script>
                        // Reloj en tiempo real para ANDROMEDA
                        function actualizarReloj() {{
                            const reloj = document.getElementById('reloj-andromeda');
                            if (reloj) {{
                                const ahora = new Date();
                                const horas = String(ahora.getHours()).padStart(2, '0');
                                const minutos = String(ahora.getMinutes()).padStart(2, '0');
                                const segundos = String(ahora.getSeconds()).padStart(2, '0');
                                reloj.textContent = horas + ':' + minutos + ':' + segundos;
                            }}
                        }}
                        setInterval(actualizarReloj, 1000);
                        actualizarReloj();
                    </script>
                    """)
                    
                    # Área del chat centrada
                    with gr.Column(elem_classes=["chat-area"]):
                        
                        # Chat con logo como avatar
                        chatbot = gr.Chatbot(
                            height=450,
                            show_label=False,
                            avatar_images=(None, logo_file),
                            elem_classes=["chat-messages"],
                            sanitize_html=False  # Permitir HTML de Plotly
                        )
                        
                        # Tabla de datos (se abre automáticamente cuando hay contenido)
                        with gr.Accordion("Datos y Resultados", open=True):
                            tabla = gr.HTML()
                        
                        # ============== INPUT ESTILO GEMINI PROFESIONAL ==============
                        gr.HTML("""
                        <style>
                            /* Contenedor principal del input */
                            .gemini-input-wrapper {
                                position: sticky;
                                bottom: 0;
                                z-index: 500;
                                padding: 20px 0;
                                background: linear-gradient(to top, rgba(13, 13, 25, 1) 0%, rgba(13, 13, 25, 0.95) 60%, transparent 100%);
                            }
                            .gemini-input-container {
                                background: linear-gradient(145deg, rgba(35, 35, 60, 0.98), rgba(25, 25, 45, 0.99)) !important;
                                border: 1px solid rgba(102, 126, 234, 0.25) !important;
                                border-radius: 26px !important;
                                padding: 6px 8px !important;
                                display: flex !important;
                                align-items: center !important;
                                gap: 6px !important;
                                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 
                                            0 2px 8px rgba(102, 126, 234, 0.1),
                                            inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
                                backdrop-filter: blur(20px) !important;
                                max-width: 100% !important;
                                margin: 0 auto !important;
                            }
                            .gemini-input-container:focus-within {
                                border-color: rgba(102, 126, 234, 0.5) !important;
                                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 
                                            0 0 20px rgba(102, 126, 234, 0.15),
                                            inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
                            }
                            .gemini-btn {
                                width: 44px !important;
                                height: 44px !important;
                                min-width: 44px !important;
                                max-width: 44px !important;
                                border-radius: 50% !important;
                                padding: 0 !important;
                                margin: 0 !important;
                                display: flex !important;
                                align-items: center !important;
                                justify-content: center !important;
                                font-size: 18px !important;
                                border: none !important;
                                cursor: pointer !important;
                                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
                                flex-shrink: 0 !important;
                            }
                            .gemini-btn-plus {
                                background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15)) !important;
                                color: #a5b4fc !important;
                                border: 1px solid rgba(102, 126, 234, 0.2) !important;
                            }
                            .gemini-btn-plus:hover {
                                background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3)) !important;
                                transform: scale(1.08) rotate(90deg);
                                color: #c4b5fd !important;
                            }
                            .gemini-btn-mic {
                                background: rgba(255, 255, 255, 0.03) !important;
                                color: rgba(255, 255, 255, 0.5) !important;
                                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                            }
                            .gemini-btn-mic:hover {
                                color: #f87171 !important;
                                background: rgba(248, 113, 113, 0.12) !important;
                                border-color: rgba(248, 113, 113, 0.3) !important;
                                transform: scale(1.08);
                            }
                            .gemini-btn-send {
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f64f59 100%) !important;
                                color: white !important;
                                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.35) !important;
                                border: none !important;
                            }
                            .gemini-btn-send:hover {
                                transform: scale(1.1);
                                box-shadow: 0 6px 25px rgba(102, 126, 234, 0.5) !important;
                            }
                            .gemini-btn-send:active {
                                transform: scale(0.95);
                            }
                            .gemini-textbox {
                                flex: 1 !important;
                                min-width: 0 !important;
                            }
                            .gemini-textbox textarea {
                                background: transparent !important;
                                border: none !important;
                                color: #f1f5f9 !important;
                                font-size: 15px !important;
                                font-weight: 400 !important;
                                line-height: 1.5 !important;
                                resize: none !important;
                                padding: 12px 8px !important;
                            }
                            .gemini-textbox textarea::placeholder {
                                color: rgba(255, 255, 255, 0.35) !important;
                                font-style: italic !important;
                            }
                            .gemini-textbox textarea:focus {
                                outline: none !important;
                                box-shadow: none !important;
                            }
                            /* Ocultar bordes de gradio group */
                            .gemini-input-container > .gradio-row {
                                gap: 8px !important;
                            }
                        </style>
                        """)
                        
                        with gr.Group(elem_classes=["gemini-input-container"]):
                            with gr.Row(equal_height=True):
                                btn_plus = gr.Button("＋", elem_classes=["gemini-btn", "gemini-btn-plus"], scale=0, min_width=40)
                                msg = gr.Textbox(
                                    placeholder="Pregúntame lo que necesites...",
                                    show_label=False,
                                    lines=1,
                                    max_lines=4,
                                    scale=6,
                                    container=False,
                                    elem_classes=["gemini-textbox"]
                                )
                                btn_mic = gr.Button("🎤", elem_classes=["gemini-btn", "gemini-btn-mic"], scale=0, min_width=40)
                                btn = gr.Button("➤", elem_classes=["gemini-btn", "gemini-btn-send"], scale=0, min_width=40)
                        
                        # ============== ENTRADA POR VOZ (oculto por defecto) ==============
                        with gr.Accordion("Entrada por Voz", open=True, visible=False) as panel_voz:
                            gr.HTML("""
                            <div style="text-align:center;padding:10px;">
                                <p style="color:#8b949e;margin:0 0 12px;font-size:13px;">
                                    <b>Graba tu mensaje de voz</b> - Se convertirá automáticamente a texto
                                </p>
                            </div>
                            """)
                            with gr.Row():
                                audio_input = gr.Audio(
                                    sources=["microphone"],
                                    type="filepath",
                                    label="🎤 Grabar mensaje",
                                    show_label=True,
                                    scale=4
                                )
                                btn_voz = gr.Button("Procesar Voz", variant="secondary", scale=1)
                            voz_status = gr.Textbox(
                                label="Estado",
                                value="Esperando grabación...",
                                interactive=False,
                                lines=1
                            )
                        
                        # ============== PANEL DE ACCIONES RÁPIDAS (oculto por defecto) ==============
                        with gr.Accordion("Acciones Rápidas", open=True, visible=False) as panel_acciones:
                            gr.HTML("<p style='color:#8b949e;margin:0 0 12px;font-size:13px;'>Predicciones</p>")
                            with gr.Row():
                                p1 = gr.Button("Predecir Ventas", size="sm")
                                p2 = gr.Button("Stock Crítico", size="sm")
                                p3 = gr.Button("Flujo Caja", size="sm")
                                p4 = gr.Button("Salud Negocio", size="sm")
                                p5 = gr.Button("Estacionalidad", size="sm")
                            
                            gr.HTML("<p style='color:#8b949e;margin:16px 0 12px;font-size:13px;'><b>Business Intelligence Experto</b></p>")
                            with gr.Row():
                                bi1 = gr.Button("Dashboard KPIs", size="sm", variant="primary")
                                bi2 = gr.Button("Reporte BI", size="sm", variant="primary")
                                bi3 = gr.Button("Auditoría Fraude", size="sm", variant="primary")
                            with gr.Row():
                                bi4 = gr.Button("Anomalías", size="sm", variant="primary")
                                bi5 = gr.Button("Análisis Riesgos", size="sm", variant="primary")
                            
                            gr.HTML("<p style='color:#f59e0b;margin:16px 0 12px;font-size:13px;'>🚨 <b>Auditoría Inteligente</b></p>")
                            with gr.Row():
                                aud1 = gr.Button("Auditoría Nocturna", size="sm", variant="secondary")
                                aud2 = gr.Button("Semáforo Salud", size="sm", variant="secondary")
                                aud3 = gr.Button("Pagos Fantasma", size="sm", variant="secondary")
                            with gr.Row():
                                aud4 = gr.Button("Churn Clientes", size="sm", variant="secondary")
                                aud5 = gr.Button("Reposición JIT", size="sm", variant="secondary")
                                aud6 = gr.Button("Stock Lento", size="sm", variant="secondary")
                            with gr.Row():
                                aud7 = gr.Button("Clientes Olvidados", size="sm", variant="secondary")
                                aud8 = gr.Button("Diferencias ¢", size="sm", variant="secondary")
                                aud9 = gr.Button("Diagnóstico Error", size="sm", variant="secondary")
                            with gr.Row():
                                aud10 = gr.Button("🔍 Calidad de Datos", size="sm", variant="primary")
                            
                            gr.HTML("<p style='color:#8b949e;margin:16px 0 12px;font-size:13px;'><b>Análisis</b></p>")
                            with gr.Row():
                                a1 = gr.Button("Ventas", size="sm")
                                a2 = gr.Button("POS", size="sm")
                                a3 = gr.Button("CXC", size="sm")
                                a4 = gr.Button("CXP", size="sm")
                                a5 = gr.Button("Inventario", size="sm")
                            
                            with gr.Row():
                                a6 = gr.Button("Compras", size="sm")
                                a7 = gr.Button("RH", size="sm")
                                a8 = gr.Button("Contratos", size="sm")
                                a9 = gr.Button("CRM", size="sm")
                                a10 = gr.Button("Comparar", size="sm")
                            
                            gr.HTML("<p style='color:#8b949e;margin:16px 0 12px;font-size:13px;'><b>Reportes</b></p>")
                            with gr.Row():
                                r1 = gr.Button("Excel", size="sm")
                                r2 = gr.Button("PDF", size="sm")
                                r3 = gr.Button("Top Productos", size="sm")
                                r4 = gr.Button("Top Clientes", size="sm")
                                r5 = gr.Button("Ayuda", size="sm")
            
            # Status bar (oculto pero funcional)
            status = gr.Textbox(value="✓ Listo", show_label=False, visible=False)
            
            # ============== ESTADO DE SESIÓN PERSISTENTE ==============
            sesion_id = gr.State(None)

            # ============== EVENTOS ==============
            def _guardar_sesion(sid: str, historial: list) -> None:
                """Persiste el historial en la store de la clase."""
                if not sid:
                    return
                cls = type(self)
                # Evitar crecer indefinidamente
                if len(historial) > cls.MAX_HISTORIAL_SESION:
                    historial = historial[-cls.MAX_HISTORIAL_SESION:]
                cls._sesiones_historial[sid] = historial
                # Purgar sesiones más antiguas si se supera el límite
                if len(cls._sesiones_historial) > cls.MAX_SESIONES:
                    eliminadas = len(cls._sesiones_historial) - cls.MAX_SESIONES
                    for k in list(cls._sesiones_historial.keys())[:eliminadas]:
                        del cls._sesiones_historial[k]

            def _cargar_sesion(sid):
                """Genera o recupera un session_id y restaura el historial."""
                import uuid
                if not sid:
                    sid = str(uuid.uuid4())
                historial = type(self)._sesiones_historial.get(sid, [])
                return historial, sid

            def enviar(m, h, sid):
                import uuid
                if not sid:
                    sid = str(uuid.uuid4())
                # Si el historial llegó vacío pero teníamos sesión guardada, restaurar
                if not h:
                    h = type(self)._sesiones_historial.get(sid, [])
                h_new, t, s = self.procesar_mensaje(m, h)
                _guardar_sesion(sid, h_new)
                return h_new, t, s, "", sid

            def sugerir(txt, h, sid):
                return enviar(txt, h, sid)

            # Restaurar historial al cargar la página
            app.load(_cargar_sesion, inputs=[sesion_id], outputs=[chatbot, sesion_id])

            # Eventos principales
            btn.click(enviar, [msg, chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            msg.submit(enviar, [msg, chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            
            # Estados para controlar visibilidad de paneles
            estado_acciones = gr.State(False)
            estado_voz = gr.State(False)
            
            # Toggle para panel de acciones rápidas (btn_plus)
            def toggle_acciones(visible):
                nuevo_estado = not visible
                return gr.update(visible=nuevo_estado), nuevo_estado
            
            btn_plus.click(toggle_acciones, inputs=[estado_acciones], outputs=[panel_acciones, estado_acciones])
            
            # Toggle para panel de voz (btn_mic)
            def toggle_voz(visible):
                nuevo_estado = not visible
                return gr.update(visible=nuevo_estado), nuevo_estado
            
            btn_mic.click(toggle_voz, inputs=[estado_voz], outputs=[panel_voz, estado_voz])
            
            # Predicciones
            p1.click(lambda h, sid: sugerir("Predice las ventas para los próximos 7 días", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            p2.click(lambda h, sid: sugerir("¿Qué productos se van a agotar?", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            p3.click(lambda h, sid: sugerir("Predice el flujo de caja para 30 días", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            p4.click(lambda h, sid: sugerir("Score de salud del negocio", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            p5.click(lambda h, sid: sugerir("Analiza patrones de estacionalidad", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            
            # Business Intelligence Experto
            bi1.click(lambda h, sid: sugerir("Dashboard de KPIs ejecutivo", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            bi2.click(lambda h, sid: sugerir("Reporte de Business Intelligence completo", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            bi3.click(lambda h, sid: sugerir("Auditoría de fraude y riesgos financieros", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            bi4.click(lambda h, sid: sugerir("Detectar anomalías financieras", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            bi5.click(lambda h, sid: sugerir("Análisis de riesgos empresariales", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            
            # Auditoría Inteligente
            aud1.click(lambda h, sid: sugerir("Ejecutar auditoría nocturna completa de la base de datos", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            aud2.click(lambda h, sid: sugerir("Mostrar semáforo de salud operativa", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            aud3.click(lambda h, sid: sugerir("Detectar pagos fantasma y movimientos sospechosos", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            aud4.click(lambda h, sid: sugerir("Analizar riesgo de churn de clientes", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            aud5.click(lambda h, sid: sugerir("Calcular reposición de inventario justo a tiempo", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            aud6.click(lambda h, sid: sugerir("Analizar productos con stock lento o muerto", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            aud7.click(lambda h, sid: sugerir("Identificar clientes olvidados que dejaron de comprar", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            aud8.click(lambda h, sid: sugerir("Detectar diferencias de centavos y residuales en facturas", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            aud9.click(lambda h, sid: sugerir("Diagnosticar error de Odoo", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            aud10.click(lambda h, sid: sugerir("Ejecutar auditoría de calidad de datos con triple validación", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            
            # Análisis
            a1.click(lambda h, sid: sugerir("Análisis de ventas del mes", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            a2.click(lambda h, sid: sugerir("Análisis del POS de hoy", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            a3.click(lambda h, sid: sugerir("Cuentas por cobrar", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            a4.click(lambda h, sid: sugerir("Cuentas por pagar", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            a5.click(lambda h, sid: sugerir("Análisis de inventario", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            a6.click(lambda h, sid: sugerir("Análisis de compras y top proveedores", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            a7.click(lambda h, sid: sugerir("Empleados por departamento", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            a8.click(lambda h, sid: sugerir("Contratos por vencer", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            a9.click(lambda h, sid: sugerir("Análisis del CRM", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            a10.click(lambda h, sid: sugerir("Compara ventas de hoy vs ayer", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            
            # Reportes
            r1.click(lambda h, sid: sugerir("Generar Excel", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            r2.click(lambda h, sid: sugerir("Generar PDF", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            r3.click(lambda h, sid: sugerir("Top 10 productos más vendidos del mes", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            r4.click(lambda h, sid: sugerir("Top 10 mejores clientes", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            r5.click(lambda h, sid: sugerir("Qué puedes hacer", h, sid), [chatbot, sesion_id], [chatbot, tabla, status, msg, sesion_id])
            
            # ============== PROCESAMIENTO DE VOZ ==============
            def procesar_audio(audio_path, historial, sid):
                """Convierte audio a texto y lo procesa como mensaje."""
                import uuid
                if not sid:
                    sid = str(uuid.uuid4())
                if audio_path is None:
                    return historial, "", "No hay audio grabado", "", sid
                
                if not VOZ_DISPONIBLE:
                    return historial, "", "Reconocimiento de voz no disponible. Instala: pip install SpeechRecognition", "", sid
                
                try:
                    recognizer = sr.Recognizer()
                    
                    # Cargar el archivo de audio
                    with sr.AudioFile(audio_path) as source:
                        audio_data = recognizer.record(source)
                    
                    # Reconocer el texto (usando Google Speech Recognition gratuito)
                    texto = recognizer.recognize_google(audio_data, language="es-ES")
                    
                    if texto:
                        # Procesar el mensaje como si fuera texto
                        h_new, t, _ = self.procesar_mensaje(texto, historial)
                        _guardar_sesion(sid, h_new)
                        return h_new, t, f"Reconocido: \"{texto}\"", texto, sid
                    else:
                        return historial, "", "No se pudo reconocer el audio", "", sid
                        
                except sr.UnknownValueError:
                    return historial, "", "No se pudo entender el audio. Intenta hablar más claro.", "", sid
                except sr.RequestError as e:
                    return historial, "", f"Error de conexión con el servicio de voz: {e}", "", sid
                except Exception as e:
                    return historial, "", f"Error procesando audio: {str(e)}", "", sid
            
            # Evento del botón de voz
            btn_voz.click(
                procesar_audio, 
                [audio_input, chatbot, sesion_id], 
                [chatbot, tabla, voz_status, msg, sesion_id]
            )
        
        return app


def main():
    """Punto de entrada principal."""
    if not GRADIO_DISPONIBLE:
        print("Instala Gradio: pip install gradio")
        return
    
    bot = OdooAIProV5()
    app = bot.crear_interfaz()
    
    # Obtener ruta absoluta para servir archivos estáticos
    import os
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    
    app.launch(
        server_name=Config.GRADIO_SERVER_NAME,
        server_port=Config.GRADIO_SERVER_PORT,
        share=Config.GRADIO_SHARE,
        inbrowser=True,
        css=CSS_PRO_V5,
        allowed_paths=[os.path.join(ruta_base, 'static')]
    )


if __name__ == "__main__":
    main()
