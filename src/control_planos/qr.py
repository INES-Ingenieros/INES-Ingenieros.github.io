"""Generación del código QR y control de su legibilidad física.

Este módulo no dibuja: devuelve la matriz de módulos para que el estampado la
pinte como vectores. Un QR rasterizado a 18 mm pierde definición justo en el
borde de cada módulo, que es donde la cámara decide si lee o no.

La otra responsabilidad de este módulo es avisar cuando el QR va a salir
demasiado denso para el tamaño en el que se va a imprimir. Es un límite físico,
no informático: por debajo de unos 0,6 mm de lado de módulo, los móviles
empiezan a fallar sobre papel impreso, fotocopiado o doblado.
"""

from __future__ import annotations

from dataclasses import dataclass

import qrcode
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)

#: Niveles de corrección de errores, por su letra habitual.
NIVELES = {
    "L": ERROR_CORRECT_L,  # 7 %
    "M": ERROR_CORRECT_M,  # 15 %
    "Q": ERROR_CORRECT_Q,  # 25 % — el adecuado en obra
    "H": ERROR_CORRECT_H,  # 30 %
}

#: Módulos de margen blanco alrededor del símbolo. La norma pide 4; con un
#: recuadro blanco alrededor (que es lo que hace el estampado) 2 son
#: suficientes y el QR aprovecha mejor el espacio disponible.
BORDE_MODULOS = 2


@dataclass(frozen=True)
class QR:
    """Un QR ya calculado, con lo necesario para dibujarlo y para juzgarlo."""

    matriz: list[list[bool]]
    """Matriz cuadrada de módulos, borde incluido. ``True`` es módulo negro."""

    version: int
    """Versión del símbolo (1 a 40). A más versión, más denso."""

    modulos_datos: int
    """Módulos del símbolo sin contar el borde."""

    texto: str
    nivel: str

    @property
    def lado_modulos(self) -> int:
        """Módulos por lado contando el borde blanco."""
        return len(self.matriz)

    def modulo_mm(self, lado_mm: float) -> float:
        """Lado de cada módulo, en mm, si el QR se imprime con ese lado total."""
        return lado_mm / self.lado_modulos

    def legible(self, lado_mm: float, minimo_mm: float) -> bool:
        """¿Sale cada módulo con tamaño suficiente para leerse en papel?"""
        return self.modulo_mm(lado_mm) >= minimo_mm

    def lado_recomendado_mm(self, minimo_mm: float) -> float:
        """Lado total mínimo, en mm, para respetar el umbral de legibilidad."""
        return self.lado_modulos * minimo_mm


def generar(texto: str, nivel: str = "Q") -> QR:
    """Calcula el QR de un texto.

    Args:
        texto: lo que se codifica. Aquí siempre es la dirección de verificación.
        nivel: corrección de errores, ``"L"``, ``"M"``, ``"Q"`` o ``"H"``.

    Raises:
        ValueError: si el nivel no existe o el texto está vacío.
    """
    if not texto:
        raise ValueError("no se puede generar un QR de un texto vacío")
    nivel = nivel.upper()
    if nivel not in NIVELES:
        raise ValueError(
            f"nivel de corrección desconocido: {nivel!r}. "
            f"Los válidos son {', '.join(NIVELES)}."
        )

    qr = qrcode.QRCode(
        error_correction=NIVELES[nivel],
        border=BORDE_MODULOS,
        box_size=1,
    )
    qr.add_data(texto)
    qr.make(fit=True)

    return QR(
        matriz=qr.get_matrix(),
        version=qr.version,
        modulos_datos=qr.modules_count,
        texto=texto,
        nivel=nivel,
    )
