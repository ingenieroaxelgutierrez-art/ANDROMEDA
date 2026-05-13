import re, os
os.chdir(r'c:\Users\procesos\Documents\ANDROMEDA')

# Load all handler sets
with open('services/actions/ejecutor_acciones.py', encoding='utf-8') as f:
    ej_txt = f.read()

with open('services/actions/mapeador_consultas.py', encoding='utf-8') as f:
    map_txt = f.read()

with open('services/agents/ejecutores.py', encoding='utf-8') as f:
    ejec_txt = f.read()

# Handlers in ejecutor_acciones.py (elif accion == 'x' or elif accion in ('a','b'))
elif_flat = set()
for m in re.findall(r"accion\s*(?:==\s*'([a-z_]+)'|in\s*\(([^)]+)\))", ej_txt):
    if m[0]: elif_flat.add(m[0])
    if m[1]:
        for part in re.findall(r"'([a-z_]+)'", m[1]): elif_flat.add(part)

# Keys in mapeador_consultas.py (dict keys with 'modelo':)
map_keys = set(re.findall(r"'([a-z_]+)':\s*\{\s*\n\s*'modelo'", map_txt))

# Handlers in ejecutores.py (accion == 'x')
ejec_flat = set()
for m in re.findall(r"accion\s*(?:==\s*'([a-z_]+)'|in\s*\(([^)]+)\))", ejec_txt):
    if m[0]: ejec_flat.add(m[0])
    if m[1]:
        for part in re.findall(r"'([a-z_]+)'", m[1]): ejec_flat.add(part)

all_covered = elif_flat | map_keys | ejec_flat

# acciones_soportadas per agent
with open('services/agents/multi_agente.py', encoding='utf-8') as f:
    ma_txt = f.read()

# Find class names and their acciones_soportadas
class_blocks = re.findall(r'class (Agent\w+)[^{]+?acciones_soportadas\s*=\s*\{([^}]+)\}', ma_txt, re.DOTALL)
print(f'\n=== COBERTURA POR AGENTE ===')
total_sin = 0
for cls, block in class_blocks:
    acciones = set(re.findall(r"'([a-z_]+)'", block))
    sin_handler = [a for a in sorted(acciones) if a not in all_covered]
    cubiertos = [a for a in sorted(acciones) if a in all_covered]
    print(f'\n{cls} ({len(acciones)} acciones):')
    print(f'  Cubiertas ({len(cubiertos)}): {cubiertos}')
    if sin_handler:
        print(f'  SIN HANDLER ({len(sin_handler)}): {sin_handler}')
    total_sin += len(sin_handler)

print(f'\nTOTAL SIN HANDLER: {total_sin}')
print(f'TOTAL COVERED (elif + mapeador + ejec): {len(all_covered)}')
