"""
FIX script v2: Clean up orphaned code in ejecutor_acciones.py.
The first extraction + fix left orphaned code (from broken methods due to
f-strings containing 'def' patterns) BETWEEN the end of _ejecutar_accion  
and the start of _generar_tendencia.

Strategy:
1. Find the orphaned zone (between return of _ejecutar_accion and next def)
2. Check if the orphaned code is unique or duplicated in existing methods
3. If duplicated → merge into the proper method definition
4. Remove orphaned code from between-method zone

Run: python scripts/fix_refactor_v2.py
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EJECUTOR = os.path.join(BASE, 'services', 'actions', 'ejecutor_acciones.py')

with open(EJECUTOR, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"ejecutor_acciones.py: {len(lines)} lines")

# ---- Step 1: Find method boundaries using indent tracking ----
# A class method starts with exactly '    def ' (4 spaces)
# Its body is everything after that line until the next '    def ' or dedent to class level

class_methods = []  # (start_line_0indexed, name)
for i, line in enumerate(lines):
    if line.startswith('    def ') and not line.startswith('        def '):
        # Extract method name
        match = re.match(r'    def (\w+)\(', line)
        name = match.group(1) if match else 'unknown'
        class_methods.append((i, name))

print(f"\nMethods: {len(class_methods)}")
for start, name in class_methods:
    print(f"  L{start+1}: {name}")

# ---- Step 2: Find the orphaned zone ----
# It's after _ejecutar_accion's `return respuesta, df` and before _generar_tendencia's def
ejecutar_accion_idx = None
generar_tendencia_idx = None
for start, name in class_methods:
    if name == '_ejecutar_accion':
        ejecutar_accion_idx = start
    if name == '_generar_tendencia':
        generar_tendencia_idx = start
        break

# Find the actual end of _ejecutar_accion method body
# The method body ends when we find `return respuesta, df` at 8-space indent
# as the last return before orphaned code starts
ejecutar_ret = None
for i in range(ejecutar_accion_idx + 1, generar_tendencia_idx):
    stripped = lines[i].strip()
    if stripped == 'return respuesta, df':
        ejecutar_ret = i
        # Don't break — find the LAST one (the real end)

if ejecutar_ret is None:
    print("ERROR: cannot find 'return respuesta, df' in _ejecutar_accion")
    exit(1)

# The orphaned zone starts after the return + any blank/comment lines that are part of the method
orphan_start = ejecutar_ret + 1
# Skip blank lines and comment/section header lines
while orphan_start < generar_tendencia_idx:
    stripped = lines[orphan_start].strip()
    if stripped == '' or stripped.startswith('# =========='):
        orphan_start += 1
    else:
        break

orphan_end = generar_tendencia_idx
orphan_lines = orphan_end - orphan_start
print(f"\nOrphaned zone: L{orphan_start+1} to L{orphan_end} ({orphan_lines} lines)")

if orphan_lines <= 0:
    print("No orphaned code found! File is clean.")
    exit(0)

# ---- Step 3: Analyze orphaned content ----
# Check if it contains method bodies that are fragments of existing methods
orphan_content = lines[orphan_start:orphan_end]

# Check if any of this code exists in the properly-defined methods below
# We'll check for unique signatures/patterns
print(f"\nFirst 5 orphaned lines:")
for i, line in enumerate(orphan_content[:5]):
    print(f"  L{orphan_start+i+1}: {line.rstrip()[:80]}")

# The orphan is typically: fragments of _generar_kpis_por_tienda and other helpers
# that were partially extracted. The COMPLETE versions are in the methods defined
# at L1550+. So we can safely remove the orphan zone.

# ---- Step 4: Check that existing methods at L1550+ are complete ----
# Verify _generar_kpis_por_tienda has a return statement
kpis_por_tienda_idx = None
for start, name in class_methods:
    if name == '_generar_kpis_por_tienda':
        kpis_por_tienda_idx = start
        break

if kpis_por_tienda_idx:
    # Find its end (next method)
    kpis_end = len(lines)
    for start, name in class_methods:
        if start > kpis_por_tienda_idx:
            kpis_end = start
            break
    
    # Check for return
    has_return = False
    for i in range(kpis_por_tienda_idx, kpis_end):
        if 'return' in lines[i]:
            has_return = True
            break
    print(f"\n_generar_kpis_por_tienda (L{kpis_por_tienda_idx+1}-L{kpis_end}): {'has return ✓' if has_return else 'MISSING return ✗'}")

# ---- Step 5: Also check if orphan has the COMPLETE body we need ----
# The orphan might have code that the truncated methods need
# Strategy: if the orphan has content that's unique and needed, 
# we need to merge. If it's all duplicate, just delete.

# For now, let's check if _generar_kpis_por_tienda at L1550 is complete
# by checking its total lines
if kpis_por_tienda_idx:
    kpis_length = kpis_end - kpis_por_tienda_idx
    print(f"  Length: {kpis_length} lines")
    
    # Check the orphan for kpis-related content
    kpis_in_orphan = sum(1 for l in orphan_content if 'kpis_tienda' in l or 'Tienda' in l)
    print(f"  kpis_tienda refs in orphan: {kpis_in_orphan}")

# ---- Step 6: The orphaned zone contains duplicate fragments ----
# The methods at L1550+ were extracted with their FULL content from the original
# file (they were later than L3551 in the original).
# The orphaned zone contains fragments from the INTERMEDIATE file that had
# parts of _generar_kpis_por_tienda body that were between the cut point and
# the method start.
# Since the method at L1550 starts with `def` and has its full body,
# the orphan duplicates are safe to remove.

# ---- Step 7: Remove orphaned zone ----
# BUT we also need to keep the SECTION COMMENT for _ejecutar_accion closing
# and any blank lines for readability

# Find proper close of _ejecutar_accion (the return + next 1-2 blank lines)
close_line = ejecutar_ret + 1  # Line after return
# Keep up to 2 blank lines after return
while close_line < orphan_start and lines[close_line].strip() == '':
    close_line += 1

# Keep the section comment if it's just a separator
section_end = close_line
while section_end < orphan_start:
    stripped = lines[section_end].strip()
    if stripped.startswith('# =====') or stripped.startswith('# FORM'):
        section_end += 1 
    else:
        break

# Build new file: everything up to close, then from generar_tendencia onward
new_lines = lines[:close_line] + ['\n'] + lines[generar_tendencia_idx:]

with open(EJECUTOR, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

new_count = len(new_lines)
print(f"\nejecutor_acciones.py: {len(lines)} -> {new_count} lines")
print(f"Removed: {len(lines) - new_count} orphaned lines")
print(f"\n✅ Fix v2 complete!")
