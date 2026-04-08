# ANDROMEDA - Seguridad: Firma de Prompts (SHA-256)
# Autor: KAIROS-SYNERGY
# Descripción: Función simple para firmar prompts con SHA-256, sin dependencias externas.

import hashlib

def firmar_prompt(texto: str) -> str:
    """
    Genera el hash SHA-256 de un prompt normalizado.
    Args:
        texto: Prompt a firmar (str)
    Returns:
        str: Hash SHA-256 en hexadecimal
    """
    if not isinstance(texto, str):
        raise TypeError("El prompt debe ser un string")
    prompt_normalizado = texto.strip().replace('\r\n', '\n').replace('\r', '\n')
    return hashlib.sha256(prompt_normalizado.encode('utf-8')).hexdigest()

# Ejemplo de uso (eliminar en producción)
if __name__ == "__main__":
    ejemplo = "¿Cuáles son las ventas de hoy?"
    print(f"Prompt: {ejemplo}")
    print(f"Hash: {firmar_prompt(ejemplo)}")
