# Configuración de Ollama — Límite de consumo de RAM

## Objetivo
Limitar el uso de RAM de Ollama a aproximadamente **2 GB** para garantizar coexistencia con el stack completo (Python backend + Next.js frontend + ChromaDB + SQLite).

## ⚙️ Parámetros Configurados

### En `ollama_integrador.py` y `cerebro_llm.py`

```python
"options": {
    "num_ctx": 2048,        # Context window reducido (1GB RAM aprox)
    "num_predict": 512,     # Máximo tokens de respuesta (ahorra RAM)
    "num_thread": 4,        # Límite de threads CPU
    "num_gpu": 0,           # Solo CPU (mejor control de RAM)
    "num_batch": 128,       # Batch size reducido
    "low_vram": True        # Modo bajo consumo de VRAM
}
```

## 📊 Impacto en Recursos

| Parámetro | Valor Original | Valor Optimizado | Ahorro RAM |
|-----------|---------------|------------------|------------|
| `num_ctx` | 4096 | 2048 | ~1GB |
| `num_predict` | 2048 | 512 | ~500MB |
| `num_batch` | 256 | 128 | ~200MB |
| **Total** | **~3GB** | **~2GB** | **~1GB** |

## 🚀 Modelos Recomendados

Para mantener el límite de 2GB:

1. **llama3.2** (3B parámetros) - ✅ Ideal
2. **phi-3:mini** (3.8B parámetros) - ✅ Recomendado
3. **mistral** (7B parámetros) - ⚠️ Puede exceder límite
4. **llama2** (7B parámetros) - ⚠️ No recomendado con estos límites

## 📝 Comandos de Instalación

```bash
# Instalar Ollama
# Windows: Descargar de https://ollama.ai/download

# Descargar modelo optimizado
ollama pull llama3.2

# O modelo aún más ligero
ollama pull phi-3:mini

# Verificar modelos instalados
ollama list
```

## 🔧 Verificación de Recursos

### En Windows PowerShell:
```powershell
# Monitor de RAM en tiempo real
Get-Process ollama | Select-Object Name, @{Name="RAM(MB)";Expression={$_.WS/1MB}}

# Monitor continuo cada 2 segundos
while($true) {
    Clear-Host
    Get-Process ollama -ErrorAction SilentlyContinue | 
    Select-Object Name, @{Name="RAM(MB)";Expression={[math]::Round($_.WS/1MB,2)}}
    Start-Sleep -Seconds 2
}
```

## ⚡ Optimizaciones Adicionales

### Si aún necesitas reducir más RAM:

1. **Reducir context window:**
   ```python
   "num_ctx": 1024  # En lugar de 2048
   ```

2. **Reducir tokens de predicción:**
   ```python
   "num_predict": 256  # En lugar de 512
   ```

3. **Usar modelo más pequeño:**
   ```bash
   ollama pull tinyllama  # Solo 1.1B parámetros (~600MB RAM)
   ```

## 🎨 Notas de Rendimiento

- **Respuestas más cortas**: Con `num_predict: 512` las respuestas serán concisas pero suficientes.
- **Contexto reducido**: Con `num_ctx: 2048` se mantienen ~6-8 mensajes de historial.
- **Solo CPU**: `num_gpu: 0` hace las respuestas un poco más lentas pero más predecibles en RAM.
- **Tiempo de respuesta**: Esperar 3-10 segundos por respuesta dependiendo del modelo.

## ✅ Validación

El sistema registra en logs cuando Ollama está activo:
```
✅ Ollama conectado. Modelos: llama3.2
🤖 Agente ANDROMEDA inicializado con modelo: llama3.2
```

Si ves esto, la configuración está funcionando correctamente.

## 🔍 Troubleshooting

### Problema: "RAM sigue siendo alta"
**Solución**: 
- Reiniciar Ollama: `ollama serve` (cerrar y reabrir)
- Verificar que solo un modelo esté cargado en memoria

### Problema: "Respuestas muy lentas"
**Solución**:
- Aumentar `num_thread` a 8 si tienes CPU potente
- Considerar habilitar GPU si tienes una (cambiar `num_gpu: 0` a `num_gpu: 1`)

### Problema: "Context too long"
**Solución**:
- El historial se limita automáticamente a 6 mensajes en `cerebro_llm.py`
- Si aún ocurre, reducir `max_historial` en `AgenteAndromeda`

---

**Última actualización**: 4 de marzo de 2026
**Configurado por**: Sistema ANDROMEDA v5.0
