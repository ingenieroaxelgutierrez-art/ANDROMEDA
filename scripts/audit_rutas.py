"""
Audit: compara acciones en NLP vs handlers en ejecutor_acciones + mapeador V2
"""
import re

# 1) Acciones definidas en NLP
with open('services/nlp/nlp_avanzado.py', encoding='utf-8') as f:
    nlp_txt = f.read()

acciones_nlp = sorted(set(re.findall(r"'accion':\s*'([a-z_]+)'", nlp_txt)))
print(f"=== ACCIONES NLP ({len(acciones_nlp)}) ===")
for a in acciones_nlp:
    print(f"  {a}")

# 2) elif explícitos en ejecutor_acciones.py
with open('services/actions/ejecutor_acciones.py', encoding='utf-8') as f:
    ej_txt = f.read()

elif_actions = set(re.findall(r"accion\s*(?:==|in)\s*[\('\"]([a-z_',\s]+)[\)'\"]", ej_txt))
# Extraer individualmente de tuples e igualdades
elif_flat = set()
for m in re.findall(r"accion\s*(?:==\s*'([a-z_]+)'|in\s*\(([^)]+)\))", ej_txt):
    if m[0]:
        elif_flat.add(m[0])
    if m[1]:
        for part in re.findall(r"'([a-z_]+)'", m[1]):
            elif_flat.add(part)

print(f"\n=== ELIF EXPLÍCITOS EN EJECUTOR ({len(elif_flat)}) ===")
for a in sorted(elif_flat):
    print(f"  {a}")

# 3) Acciones en el mapeador V2
with open('services/actions/mapeador_consultas.py', encoding='utf-8') as f:
    mapeador_txt = f.read()

# Buscar keys del dict 'mapeo' (tienen 'modelo' como primera key)
v2_keys = set(re.findall(r"'([a-z_]+)':\s*\{\s*\n\s*'modelo'", mapeador_txt))
# También elif/if sobre accion en mapeador_consultas
for m in re.findall(r"accion == '([a-z_]+)'", mapeador_txt):
    v2_keys.add(m)
for group in re.findall(r"accion in \(([^)]+)\)", mapeador_txt):
    for part in re.findall(r"'([a-z_]+)'", group):
        v2_keys.add(part)

print(f"\n=== MAPEADOR V2 KEYS ({len(v2_keys)}) ===")
for a in sorted(v2_keys):
    print(f"  {a}")

# 4) Acciones NLP sin handler
cubiertos = elif_flat | v2_keys
sin_handler = [a for a in acciones_nlp if a not in cubiertos]
print(f"\n=== SIN HANDLER ({len(sin_handler)}) ===")
for a in sin_handler:
    print(f"  *** {a}")

print(f"\nResumen: {len(acciones_nlp)} NLP / {len(elif_flat)} elif / {len(v2_keys)} V2-mapeador / {len(sin_handler)} SIN HANDLER")
