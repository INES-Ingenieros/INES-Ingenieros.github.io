"""Control de planos de obra con QR.

Herramienta de emisión de planos: estampa un código QR sobre el PDF ploteado y
mantiene el registro de qué revisión está vigente, para que en obra se pueda
comprobar con el móvil si un plano impreso está al día.

INES Ingenieros Consultores. Requiere Python 3.11 o superior.

El diseño y sus motivos están en ``docs/DECISIONES.md``. El uso, en
``docs/GUIA_USUARIO.md``.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
