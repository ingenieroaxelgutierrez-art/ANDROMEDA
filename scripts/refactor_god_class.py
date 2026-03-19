"""
Script de refactorización: Extrae _ejecutar_accion, helpers y _mapear_accion_a_consulta_odoo
de interfaz_v5.py a módulos dedicados.

Ejecutar desde la raíz del proyecto:
    python scripts/refactor_god_class.py
"""
import re
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, 'views', 'interfaz_v5.py')

with open(SRC, 'r', encoding='utf-8') as f:
    lines = f.readlines()

total = len(lines)
print(f"Total lines in interfaz_v5.py: {total}")

# ---- Find method boundaries ----
def find_method_range(lines, method_name, start_search=0):
    """Find start line and end line (exclusive) of a top-level method in a class."""
    start = None
    for i in range(start_search, len(lines)):
        if re.match(rf'^    def {re.escape(method_name)}\(', lines[i]):
            start = i
            break
    if start is None:
        raise ValueError(f"Method {method_name} not found")
    
    # Find next method at same indentation level (4 spaces)
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if re.match(r'^    def ', lines[i]):
            end = i
            break
        # Also stop at class-level code that isn't indented 4+
        if re.match(r'^class ', lines[i]) or (re.match(r'^\S', lines[i]) and lines[i].strip()):
            end = i
            break
    
    return start, end

# Find all method ranges that need extraction
methods_to_extract_ejecutor = [
    '_ejecutar_accion',
    '_generar_tendencia',
    '_generar_kpis_por_tienda',
    '_consultar_facturas_filtradas',
    '_generar_reporte',
    '_generar_pdf_profesional',
    '_ejecutar_consulta_dinamica',
    '_contar_chiste',
    '_mostrar_capacidades',
    '_responder_despedida',
    '_responder_agradecimiento',
    '_responder_saludo',
    '_ventas_tienda_especifica',
    '_generar_ayuda_completa',
    '_info_conexion',
    '_ejecutar_consulta_avanzada_v2',
    '_respuesta_accion_no_disponible',
]

methods_to_extract_mapeador = [
    '_mapear_accion_a_consulta_odoo',
]

all_methods = methods_to_extract_ejecutor + methods_to_extract_mapeador

# Find all ranges
ranges = {}
for m in all_methods:
    try:
        s, e = find_method_range(lines, m)
        ranges[m] = (s, e)
        print(f"  {m}: L{s+1}-L{e} ({e-s} lines)")
    except ValueError as ex:
        print(f"  WARNING: {ex}")

# ---- Extract code blocks ----
def extract_methods(lines, method_names, ranges):
    """Extract method code blocks, return as list of strings."""
    blocks = []
    for m in method_names:
        if m in ranges:
            s, e = ranges[m]
            block = lines[s:e]
            blocks.append(''.join(block))
    return blocks

ejecutor_blocks = extract_methods(lines, methods_to_extract_ejecutor, ranges)
mapeador_blocks = extract_methods(lines, methods_to_extract_mapeador, ranges)

# ---- Transform self.xxx to self._bot.xxx ----
def transform_self_refs(code, internal_methods):
    """
    In extracted code, change self.xxx to self._bot.xxx for bot attributes,
    but keep self.xxx for internal methods of the new class.
    """
    # First, replace ALL self. with self._bot.
    result = code.replace('self.', 'self._bot.')
    
    # Then restore self. for internal method calls (methods that are in this class)
    for m in internal_methods:
        result = result.replace(f'self._bot.{m}(', f'self.{m}(')
        result = result.replace(f'self._bot.{m},', f'self.{m},')  # reference as callback
    
    # Fix the method definition lines: def xxx(self._bot.) -> def xxx(self.)
    result = re.sub(r'def (\w+)\(self\._bot\.', r'def \1(self.', result)
    
    # Fix: self._bot._bot should just be self._bot
    result = result.replace('self._bot._bot.', 'self._bot.')
    
    return result

# Internal methods for ejecutor_acciones.py
ejecutor_internal = methods_to_extract_ejecutor.copy()
ejecutor_code_raw = '\n'.join(ejecutor_blocks)
ejecutor_code = transform_self_refs(ejecutor_code_raw, ejecutor_internal)

# Internal methods for mapeador_consultas.py (only self-referencing)
mapeador_code_raw = '\n'.join(mapeador_blocks)
mapeador_code = transform_self_refs(mapeador_code_raw, methods_to_extract_mapeador)

# ---- Detect needed imports from the extracted code ----
# Check what's used in the code
ejecutor_imports = set()
if 'datetime' in ejecutor_code:
    ejecutor_imports.add('from datetime import datetime, timedelta')
if 'pd.' in ejecutor_code or 'pd.DataFrame' in ejecutor_code:
    ejecutor_imports.add('import pandas as pd')
if 'Tuple' in ejecutor_code or 'List' in ejecutor_code or 'Dict' in ejecutor_code:
    ejecutor_imports.add('from typing import List, Tuple, Dict, Any, Optional')
if 're.' in ejecutor_code or 're.compile' in ejecutor_code:
    ejecutor_imports.add('import re')
if 'os.' in ejecutor_code:
    ejecutor_imports.add('import os')
if 'json.' in ejecutor_code:
    ejecutor_imports.add('import json')
if 'NivelCriticidad' in ejecutor_code:
    ejecutor_imports.add('# NivelCriticidad es importado dinámicamente por el bot')
if 'ContextoConsulta' in ejecutor_code or 'TipoAgrupacion' in ejecutor_code:
    ejecutor_imports.add('# ContextoConsulta/TipoAgrupacion importados desde services/analysis')

# Also check for get_logger
ejecutor_imports.add('from app.logging_config import get_logger')

# ---- Create ejecutor_acciones.py ----
ejecutor_header = '''# ============================================================
# ANDROMEDA - Ejecutor de Acciones
# ============================================================
# Módulo extraído de interfaz_v5.py (ARQ-v2-001)
# Centraliza _ejecutar_accion y todos sus helpers:
#   - _generar_tendencia, _generar_kpis_por_tienda
#   - _consultar_facturas_filtradas, _generar_reporte
#   - _generar_pdf_profesional, _ejecutar_consulta_dinamica
#   - _contar_chiste, _mostrar_capacidades, _responder_*
#   - _ventas_tienda_especifica, _generar_ayuda_completa
#   - _info_conexion, _ejecutar_consulta_avanzada_v2
#   - _mapear_accion_a_consulta_odoo, _respuesta_accion_no_disponible
# ============================================================

'''

ejecutor_import_block = '\n'.join(sorted(ejecutor_imports)) + '\n\n'
ejecutor_import_block += 'logger = get_logger("services.actions.ejecutor_acciones")\n\n\n'

ejecutor_class = '''class EjecutorAcciones:
    """Ejecuta acciones del sistema según la consulta entendida.
    
    Extraído de OdooAIProV5._ejecutar_accion (ARQ-v2-001).
    Recibe referencia al bot para acceder a todos los servicios.
    """

    def __init__(self, bot):
        self._bot = bot

    def ejecutar(self, consulta, mensaje: str = ""):
        """Punto de entrada principal — delega a _ejecutar_accion."""
        return self._ejecutar_accion(consulta, mensaje)

'''

# Convert extracted methods to be inside the class (they already have 4-space indent)
ejecutor_file = ejecutor_header + ejecutor_import_block + ejecutor_class + ejecutor_code + '\n'

# ---- Create mapeador_consultas.py ----
mapeador_header = '''# ============================================================
# ANDROMEDA - Mapeador de Consultas Odoo
# ============================================================
# Módulo extraído de interfaz_v5.py (ARQ-v2-001)
# Mapea acciones v2 a consultas directas Odoo.
# ============================================================

from app.logging_config import get_logger

logger = get_logger("services.actions.mapeador_consultas")


class MapeadorConsultas:
    """Mapea acciones a consultas directas de Odoo.
    
    Extraído de OdooAIProV5._mapear_accion_a_consulta_odoo (ARQ-v2-001).
    """

    def __init__(self, bot):
        self._bot = bot

    def mapear(self, accion: str, fecha_ini: str, fecha_fin: str, params: dict, consulta) -> dict:
        """Punto de entrada principal — delega a _mapear_accion_a_consulta_odoo."""
        return self._mapear_accion_a_consulta_odoo(accion, fecha_ini, fecha_fin, params, consulta)

'''

mapeador_file = mapeador_header + mapeador_code + '\n'

# ---- Create __init__.py for services/actions/ ----
init_content = '''# services/actions/ — Módulos de ejecución de acciones (ARQ-v2-001)
from .ejecutor_acciones import EjecutorAcciones
from .mapeador_consultas import MapeadorConsultas

__all__ = ['EjecutorAcciones', 'MapeadorConsultas']
'''

# ---- Modify interfaz_v5.py ----
# Remove extracted method blocks and replace with delegation methods

# Collect all line ranges to remove (sorted)
all_ranges = []
for m in all_methods:
    if m in ranges:
        all_ranges.append(ranges[m])

# Sort by start line
all_ranges.sort(key=lambda x: x[0])

# Also remove the comment line "# FORMATEADORES" if it's between _ejecutar_accion and _generar_tendencia
# Check for section comment
if '_ejecutar_accion' in ranges and '_generar_tendencia' in ranges:
    ea_end = ranges['_ejecutar_accion'][1]
    gt_start = ranges['_generar_tendencia'][0]
    # Include any blank/comment lines between them
    for i in range(ea_end, gt_start):
        stripped = lines[i].strip()
        if stripped == '' or stripped.startswith('#') or stripped.startswith('# ='):
            pass  # These will be between ranges and included in the gap
        else:
            break

# Merge overlapping/adjacent ranges
merged = []
for s, e in all_ranges:
    if merged and s <= merged[-1][1]:
        merged[-1] = (merged[-1][0], max(merged[-1][1], e))
    else:
        merged.append((s, e))

# Also extend first range backwards to include any section comments
if merged:
    first_s = merged[0][0]
    # Check lines before first extracted method for section comments
    while first_s > 0 and (lines[first_s - 1].strip() == '' or 
                            lines[first_s - 1].strip().startswith('# =') or
                            lines[first_s - 1].strip().startswith('# FORMATEADORES')):
        first_s -= 1
    # Don't go before _ejecutar_accion though
    if '_ejecutar_accion' in ranges:
        first_s = max(first_s, ranges['_ejecutar_accion'][0])
    merged[0] = (first_s, merged[0][1])

print(f"\nMerged ranges to remove:")
total_removed = 0
for s, e in merged:
    print(f"  L{s+1}-L{e} ({e-s} lines)")
    total_removed += e - s
print(f"  Total: {total_removed} lines to remove")

# Build delegation methods to insert
delegation = '''
    # ============================================================
    # ACCIONES — Delegadas a EjecutorAcciones (ARQ-v2-001)
    # ============================================================

    def _ejecutar_accion(self, consulta, mensaje: str = ""):
        """Delega a EjecutorAcciones.ejecutar() — ver services/actions/ejecutor_acciones.py"""
        return self._ejecutor_acciones.ejecutar(consulta, mensaje)

    def _mapear_accion_a_consulta_odoo(self, accion: str, fecha_ini: str, fecha_fin: str, params: dict, consulta) -> dict:
        """Delega a MapeadorConsultas.mapear() — ver services/actions/mapeador_consultas.py"""
        return self._mapeador_consultas.mapear(accion, fecha_ini, fecha_fin, params, consulta)

'''

# Build new file content
new_lines = []
skip_until = -1
delegation_inserted = False

for i, line in enumerate(lines):
    if i < skip_until:
        continue
    
    # Check if this line is in a range to remove
    in_range = False
    for s, e in merged:
        if s <= i < e:
            in_range = True
            skip_until = e
            if not delegation_inserted:
                new_lines.append(delegation)
                delegation_inserted = True
            break
    
    if not in_range:
        new_lines.append(line)

new_content = ''.join(new_lines)

# ---- Write output files ----
# Create services/actions/ directory
actions_dir = os.path.join(BASE, 'services', 'actions')
os.makedirs(actions_dir, exist_ok=True)

# Write ejecutor_acciones.py
ejecutor_path = os.path.join(actions_dir, 'ejecutor_acciones.py')
with open(ejecutor_path, 'w', encoding='utf-8') as f:
    f.write(ejecutor_file)
print(f"\nCreated: {ejecutor_path}")
print(f"  Lines: {ejecutor_file.count(chr(10))}")

# Write mapeador_consultas.py
mapeador_path = os.path.join(actions_dir, 'mapeador_consultas.py')
with open(mapeador_path, 'w', encoding='utf-8') as f:
    f.write(mapeador_file)
print(f"Created: {mapeador_path}")
print(f"  Lines: {mapeador_file.count(chr(10))}")

# Write __init__.py
init_path = os.path.join(actions_dir, '__init__.py')
with open(init_path, 'w', encoding='utf-8') as f:
    f.write(init_content)
print(f"Created: {init_path}")

# Write modified interfaz_v5.py
with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)
print(f"\nModified: {SRC}")
print(f"  Original: {total} lines")
print(f"  New: {new_content.count(chr(10))} lines")
print(f"  Removed: ~{total_removed} lines")
print(f"\n✅ Refactoring complete!")
