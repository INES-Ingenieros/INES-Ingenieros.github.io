"""Lectura de la configuración de la herramienta.

La configuración vive en ``config/config.yaml``. Ninguna clave ni dato sensible
se guarda ahí: por ahora la herramienta no llama a ningún servicio externo.

La clave que gobierna todo es ``url_base``. Mientras esté vacía la herramienta
funciona en MODO PRUEBA y marca los planos como no válidos, para que un ensayo
no pueda acabar en obra por error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .estampar import Colocacion

#: Raíz del proyecto, dos niveles por encima de este fichero
#: (``src/control_planos/config.py`` → ``src/control_planos`` → ``src`` → raíz).
RAIZ = Path(__file__).resolve().parents[2]

RUTA_POR_DEFECTO = RAIZ / "config" / "config.yaml"


class ErrorConfig(RuntimeError):
    """La configuración no se puede leer o tiene valores imposibles."""


@dataclass
class Config:
    """La configuración ya validada."""

    url_base: str = ""
    correccion_errores: str = "Q"
    correlativo_inicial: int = 101
    modulo_minimo_mm: float = 0.60
    colocacion: Colocacion = field(default_factory=Colocacion)
    ruta_registro: Path = RAIZ / "web" / "planos.json"
    ruta_salida: Path = RAIZ / "salida"

    forzar_prueba: bool = False
    """Marca la emisión como prueba aunque `url_base` esté configurada.

    Hace falta para el ensayo de impresión: el QR tiene que llevar la dirección
    real, porque su longitud es la que determina la densidad del símbolo y por
    tanto si el móvil lo lee. Con `url_base` vacía el QR saldría mucho más
    corto y el ensayo mediría algo que no es.
    """

    @property
    def modo_prueba(self) -> bool:
        """¿No se debe considerar válido lo que salga?

        Cierto si falta la dirección definitiva de la web (cualquier QR
        apuntaría a ninguna parte) o si se ha pedido expresamente una prueba.
        """
        return not self.url_base.strip() or self.forzar_prueba


def cargar(ruta: str | Path | None = None) -> Config:
    """Lee la configuración del disco.

    Args:
        ruta: fichero YAML. Si no se indica, ``config/config.yaml``.

    Raises:
        ErrorConfig: si el fichero no existe, no es YAML válido o tiene
            valores fuera de rango.
    """
    ruta = Path(ruta) if ruta else RUTA_POR_DEFECTO
    if not ruta.exists():
        raise ErrorConfig(
            f"no se encuentra la configuración en {ruta}. "
            "Debería existir config/config.yaml en la raíz del proyecto."
        )
    try:
        with ruta.open(encoding="utf-8") as f:
            crudo = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise ErrorConfig(f"{ruta} no es un YAML válido: {exc}") from exc

    if not isinstance(crudo, dict):
        raise ErrorConfig(f"{ruta} debería contener un diccionario de claves")

    est = crudo.get("estampado") or {}
    if not isinstance(est, dict):
        raise ErrorConfig("la clave «estampado» debería ser un diccionario")

    col = Colocacion(
        lado_qr_mm=float(est.get("lado_qr_mm", 18.0)),
        margen_derecho_mm=float(est.get("margen_derecho_mm", 12.0)),
        margen_inferior_mm=float(est.get("margen_inferior_mm", 26.0)),
        hueco_texto_mm=float(est.get("hueco_texto_mm", 2.5)),
        texto_pt=float(est.get("texto_pt", 7.0)),
        recuadro=bool(est.get("recuadro", True)),
    )
    if col.lado_qr_mm <= 0:
        raise ErrorConfig("«lado_qr_mm» tiene que ser mayor que cero")

    nivel = str(crudo.get("correccion_errores", "Q")).upper()
    if nivel not in {"L", "M", "Q", "H"}:
        raise ErrorConfig(
            f"«correccion_errores» vale {nivel!r}; debe ser L, M, Q o H"
        )

    correlativo = int(crudo.get("correlativo_inicial", 101))
    if correlativo < 1:
        raise ErrorConfig("«correlativo_inicial» tiene que ser 1 o más")

    rutas = crudo.get("rutas") or {}
    return Config(
        url_base=str(crudo.get("url_base") or "").strip(),
        correccion_errores=nivel,
        correlativo_inicial=correlativo,
        modulo_minimo_mm=float(est.get("modulo_minimo_mm", 0.60)),
        colocacion=col,
        ruta_registro=RAIZ / str(rutas.get("registro", "web/planos.json")),
        ruta_salida=RAIZ / str(rutas.get("salida", "salida")),
    )
