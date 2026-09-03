"""Composición y lectura de los códigos identificadores de plano.

El identificador tiene la forma ``OBRA-NNN-Rxx`` (por ejemplo
``SESENA-101-R00``) y es lo único que viaja dentro del QR impreso. Ver
``docs/DECISIONES.md``, decisiones D-07 y D-08.

Regla que gobierna este módulo: en el código va solo lo que no puede cambiar
nunca. La denominación, el número de índice y la fecha NO van aquí; son datos
del registro.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

#: Un código de obra válido: mayúsculas y dígitos, sin eñes ni tildes.
_RE_OBRA = re.compile(r"^[A-Z0-9]{2,12}$")

#: Un identificador completo, tal como aparece en el QR. Con IGNORECASE porque
#: este formato lo teclea también una persona que lo ha oído por teléfono, y
#: escribirá «sesena-101-r00» sin pensar en las mayúsculas.
_RE_CODIGO = re.compile(
    r"^\s*([A-Za-z0-9]{2,12})-(\d{1,6})-R(\d{1,3})\s*$", re.IGNORECASE
)


class CodigoInvalido(ValueError):
    """El texto recibido no es un identificador de plano válido."""


@dataclass(frozen=True)
class Codigo:
    """Un identificador de revisión de plano, ya descompuesto en sus partes."""

    obra: str
    correlativo: int
    revision: str

    @property
    def documento(self) -> str:
        """Identificador del documento, sin la revisión (``SESENA-101``)."""
        return f"{self.obra}-{self.correlativo:03d}"

    def __str__(self) -> str:
        return f"{self.documento}-R{self.revision}"


def normalizar_obra(texto: str) -> str:
    """Convierte un nombre de obra en un código de obra utilizable.

    Quita tildes y eñes, pasa a mayúsculas y elimina lo que no sea letra o
    dígito. ``"Emergencia Seseña"`` se convierte en ``"EMERGENCIASESENA"``, que
    es válido pero demasiado largo: el código de obra conviene elegirlo a mano
    y corto. Esta función sirve para validar y para sugerir, no para decidir.

    Raises:
        CodigoInvalido: si tras la limpieza no queda un código utilizable.
    """
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    limpio = re.sub(r"[^A-Za-z0-9]", "", sin_tildes).upper()
    if not _RE_OBRA.match(limpio):
        raise CodigoInvalido(
            f"«{texto}» no da un código de obra válido "
            f"(se obtuvo «{limpio}»; se esperan de 2 a 12 letras o dígitos)"
        )
    return limpio


def normalizar_revision(rev: str | int) -> str:
    """Devuelve la revisión con dos cifras: ``0`` → ``"00"``, ``"3"`` → ``"03"``."""
    try:
        n = int(str(rev).upper().lstrip("R") or "-1")
    except ValueError as exc:
        raise CodigoInvalido(f"«{rev}» no es un número de revisión") from exc
    if not 0 <= n <= 999:
        raise CodigoInvalido(f"revisión fuera de rango: {rev}")
    return f"{n:02d}"


def componer(obra: str, correlativo: int, revision: str | int) -> Codigo:
    """Construye un `Codigo` validando todas sus partes.

    Raises:
        CodigoInvalido: si la obra, el correlativo o la revisión no son válidos.
    """
    obra = obra.strip().upper()
    if not _RE_OBRA.match(obra):
        raise CodigoInvalido(
            f"código de obra no válido: «{obra}». "
            "Debe tener de 2 a 12 caracteres, solo mayúsculas y dígitos, "
            "sin eñes ni tildes (por ejemplo SESENA)."
        )
    if not isinstance(correlativo, int) or not 1 <= correlativo <= 999999:
        raise CodigoInvalido(f"correlativo no válido: {correlativo!r}")
    return Codigo(obra, correlativo, normalizar_revision(revision))


def partir(texto: str) -> Codigo:
    """Lee un identificador escrito (``"SESENA-101-R00"``) y lo descompone.

    Acepta minúsculas y espacios alrededor, porque este mismo formato lo teclea
    una persona cuando el QR no se puede escanear y se dicta por teléfono.

    Raises:
        CodigoInvalido: si el texto no tiene la forma ``OBRA-NNN-Rxx``.
    """
    m = _RE_CODIGO.match(texto or "")
    if not m:
        raise CodigoInvalido(
            f"«{texto}» no tiene la forma OBRA-NNN-Rxx (por ejemplo SESENA-101-R00)"
        )
    return Codigo(m.group(1).upper(), int(m.group(2)), normalizar_revision(m.group(3)))


def url(base: str, codigo: Codigo | str) -> str:
    """Compone la dirección web de verificación de un código.

    Si `base` está vacía se devuelve una dirección de marcador con el esquema
    ``prueba:``, que no es navegable. Es intencionado: así un QR generado en
    modo prueba no puede llevar a nadie a una página real ni parecer válido.
    """
    codigo = str(codigo)
    if not base:
        return f"prueba:{codigo}"
    return f"{base.rstrip('/')}/?p={codigo}"
