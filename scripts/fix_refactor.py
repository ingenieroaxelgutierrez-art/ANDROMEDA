"""
FIX script: Inserts the orphaned code from interfaz_v5.py into ejecutor_acciones.py
and removes it from interfaz_v5.py.

Run: python scripts/fix_refactor.py
"""
import re
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERFAZ = os.path.join(BASE, 'views', 'interfaz_v5.py')
EJECUTOR = os.path.join(BASE, 'services', 'actions', 'ejecutor_acciones.py')

# ---- Read files ----
with open(INTERFAZ, 'r', encoding='utf-8') as f:
    ifz_lines = f.readlines()
with open(EJECUTOR, 'r', encoding='utf-8') as f:
    ej_lines = f.readlines()

print(f"interfaz_v5.py: {len(ifz_lines)} lines")
print(f"ejecutor_acciones.py: {len(ej_lines)} lines")

# ---- Step 1: Find orphaned code in interfaz_v5.py ----
# It starts right after the _mapear_accion_a_consulta_odoo delegation stub
# and ends before the next proper method (_resumen_confiable_desde_dataframe)

# Find end of delegation stubs
delegation_end = None
for i, line in enumerate(ifz_lines):
    if 'return self._mapeador_consultas.mapear(' in line:
        delegation_end = i + 1  # line after the return
        break

if delegation_end is None:
    raise ValueError("Cannot find delegation stubs in interfaz_v5.py")

# Find start of next proper method (not orphaned code)
# Look for `    def _resumen_confiable` or similar — any properly defined method
orphan_end = None
for i in range(delegation_end, len(ifz_lines)):
    line = ifz_lines[i]
    # A proper method at class level (4 spaces indent)
    if re.match(r'^    def _resumen_confiable_desde_dataframe', line):
        orphan_end = i
        break
    if re.match(r'^    def _validar_y_regenerar_respuesta', line):
        orphan_end = i
        break
    if re.match(r'^    def _regenerar_respuesta_confiable', line):
        orphan_end = i
        break

if orphan_end is None:
    # Fallback: find any `    def ` that's not inside orphaned code
    for i in range(delegation_end + 100, len(ifz_lines)):
        if re.match(r'^    def (?!_ejecutar|_mapear)', ifz_lines[i]):
            # Verify this isn't inside the orphan (check indent context)
            orphan_end = i
            break

print(f"Orphaned code: L{delegation_end+1} to L{orphan_end} ({orphan_end - delegation_end} lines)")

# Extract orphaned code
orphan_code = ifz_lines[delegation_end:orphan_end]

# ---- Step 2: Transform self. -> self._bot. in orphaned code ----
def transform_self(lines):
    results = []
    for line in lines:
        # Replace self. with self._bot. BUT not in method defs
        if re.match(r'\s*def ', line):
            results.append(line)
        else:
            # Replace self.xxx with self._bot.xxx
            # But don't double-transform (already has self._bot.)
            transformed = re.sub(r'\bself\.(?!_bot\b)', 'self._bot.', line)
            results.append(transformed)
    return results

orphan_transformed = transform_self(orphan_code)

# ---- Step 3: Find insertion point in ejecutor_acciones.py ----
# Find the broken f-string line: `respuesta = f"""## Ticket Promedio`
# Insert the orphaned code (continuation) right after it
# And BEFORE `def _generar_tendencia`

insert_point = None
for i, line in enumerate(ej_lines):
    if '## Ticket Promedio' in line and 'f"""' in line:
        insert_point = i + 1
        break

if insert_point is None:
    raise ValueError("Cannot find Ticket Promedio f-string in ejecutor_acciones.py")

# Find where _generar_tendencia starts
generar_tendencia_start = None
for i in range(insert_point, len(ej_lines)):
    if '    def _generar_tendencia' in ej_lines[i]:
        generar_tendencia_start = i
        break

print(f"Insert point in ejecutor_acciones.py: after L{insert_point}")
print(f"_generar_tendencia starts at: L{generar_tendencia_start+1}")
print(f"Removing {generar_tendencia_start - insert_point} blank/stale lines between insert and _generar_tendencia")

# Build new ejecutor_acciones.py
new_ej_lines = (
    ej_lines[:insert_point] +           # Everything up to the broken f-string
    orphan_transformed +                  # Orphaned code (rest of _ejecutar_accion + more)
    ['\n'] +                              # Blank separator
    ej_lines[generar_tendencia_start:]    # _generar_tendencia and everything after
)

# ---- Step 4: Remove orphaned code from interfaz_v5.py ----
# Also remove any blank lines between delegation stubs and next method
new_ifz_lines = ifz_lines[:delegation_end] + ['\n'] + ifz_lines[orphan_end:]

# ---- Step 5: Write files ----
with open(EJECUTOR, 'w', encoding='utf-8') as f:
    f.writelines(new_ej_lines)

with open(INTERFAZ, 'w', encoding='utf-8') as f:
    f.writelines(new_ifz_lines)

new_ej_count = len(new_ej_lines)
new_ifz_count = len(new_ifz_lines)
print(f"\nejecutor_acciones.py: {len(ej_lines)} -> {new_ej_count} lines")
print(f"interfaz_v5.py: {len(ifz_lines)} -> {new_ifz_count} lines")
print(f"\n✅ Fix complete!")
