# ============================================================
# ANDROMEDA - Models Module
# Conexión a Odoo y definiciones de modelos
# ============================================================

from .conector_odoo import ConectorOdoo
from .modelos_odoo import MODELOS_ODOO, ModeloOdoo, CampoOdoo

__all__ = ['ConectorOdoo', 'MODELOS_ODOO', 'ModeloOdoo', 'CampoOdoo']
