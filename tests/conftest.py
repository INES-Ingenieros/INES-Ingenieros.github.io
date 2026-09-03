"""Utilidades comunes de los tests.

Ningún test toca el registro real ni la carpeta de salida del proyecto: todo
ocurre en directorios temporales que pytest limpia al terminar.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfgen import canvas

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from control_planos.config import Config  # noqa: E402
from control_planos.estampar import Colocacion  # noqa: E402


@pytest.fixture
def pdf_a3(tmp_path: Path):
    """Genera un PDF A3 apaisado de varias hojas, como los de Civil 3D."""

    def _crear(hojas: int = 4, nombre: str = "01_PRUEBA.pdf") -> Path:
        ruta = tmp_path / nombre
        c = canvas.Canvas(str(ruta), pagesize=landscape(A3))
        for i in range(hojas):
            c.setFont("Helvetica", 24)
            c.drawString(60, 500, f"Hoja {i + 1} de {hojas}")
            c.showPage()
        c.save()
        return ruta

    return _crear


@pytest.fixture
def cfg(tmp_path: Path) -> Config:
    """Configuración apuntando a un registro y una salida temporales.

    Con `url_base` puesta: la mayoría de los tests comprueban el
    comportamiento de emisión real. El modo prueba se comprueba aparte.
    """
    return Config(
        url_base="https://ejemplo.test/planos",
        correccion_errores="Q",
        correlativo_inicial=101,
        modulo_minimo_mm=0.60,
        colocacion=Colocacion(),
        ruta_registro=tmp_path / "registro" / "planos.json",
        ruta_salida=tmp_path / "salida",
    )
