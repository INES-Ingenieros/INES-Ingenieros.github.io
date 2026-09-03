"""El motor de emisión: los ocho pasos que convierten un PDF ploteado en un
plano emitido y verificable.

Este módulo es **la pieza central y la única que hay que reutilizar**. No sabe
nada de cómo se le ha pedido el trabajo: da igual que se lo pida una persona
por consola, un delineante arrastrando un fichero, o algún día un disparador
de SharePoint. Todos los caminos acaban llamando a `emitir`.

Los ocho pasos:

1. Lee el PDF ploteado y cuenta sus hojas.
2. Recibe obra, documento, revisión y motivo.
3. Asigna el correlativo, o reutiliza el del documento si ya existía.
4. Compone el código y la dirección de verificación.
5. Genera el QR.
6. Lo estampa en todas las hojas, con el código legible al lado.
7. Actualiza el registro: la anterior pasa a superada, la nueva a vigente.
8. Guarda el PDF sellado.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from pypdf import PdfReader

from . import estampar as _estampar
from . import qr as _qr
from .codigo import Codigo, url as componer_url
from .config import Config
from .registro import Registro

log = logging.getLogger(__name__)

#: Sufijo de revisión al final del nombre de fichero, para no acumularlos
#: (``plano_R00.pdf`` emitido como R01 debe dar ``plano_R01.pdf``).
_RE_SUFIJO_REV = re.compile(r"[_\- ]*R\d{1,3}$", re.IGNORECASE)


@dataclass
class Peticion:
    """Todo lo que hace falta para emitir una revisión."""

    pdf: Path
    obra: str
    denominacion: str
    revision: str
    n_indice: str
    titulo: str = ""
    motivo: str = ""
    fecha: str = field(default_factory=lambda: date.today().isoformat())

    # Solo se usan la primera vez que aparece una obra en el registro.
    nombre_obra: str = ""
    descripcion_obra: str = ""
    expediente: str = ""


@dataclass
class Emision:
    """El resultado de una emisión."""

    codigo: Codigo
    url: str
    pdf: Path
    hojas: int
    modo_prueba: bool
    lado_modulo_mm: float
    version_qr: int
    avisos: list[str]


def nombre_salida(pdf: Path, revision: str, destino: Path) -> Path:
    """Compone el nombre del PDF sellado.

    Conserva el nombre original y solo ajusta el sufijo de revisión, para que
    la carpeta siga ordenándose por número de índice y no por correlativo
    (decisión D-12).
    """
    base = _RE_SUFIJO_REV.sub("", pdf.stem)
    return destino / f"{base}_R{revision}{pdf.suffix or '.pdf'}"


def emitir(peticion: Peticion, cfg: Config) -> Emision:
    """Ejecuta los ocho pasos y devuelve el resultado.

    El registro se escribe en disco **solo si el estampado ha ido bien**. Si el
    PDF falla, el registro queda intacto: nunca debe haber una revisión anotada
    como vigente sin un PDF sellado que la respalde.

    Raises:
        FileNotFoundError: si el PDF no existe.
        ValueError: si el PDF está cifrado o vacío.
        ErrorRegistro: si esa revisión ya estaba registrada.
    """
    pdf = Path(peticion.pdf)

    # 1 · Las hojas se cuentan, no se preguntan.
    lector = PdfReader(pdf)
    if lector.is_encrypted:
        raise ValueError(
            f"{pdf.name} está cifrado. Hay que volver a plotearlo sin protección."
        )
    hojas = len(lector.pages)
    if not hojas:
        raise ValueError(f"{pdf.name} no tiene ninguna página")

    # 2 y 3 · Registro en memoria. Aquí se decide el correlativo.
    registro = Registro.cargar(cfg.ruta_registro, cfg.correlativo_inicial)
    registro.asegurar_obra(
        peticion.obra,
        nombre=peticion.nombre_obra or None,
        descripcion=peticion.descripcion_obra or None,
        expediente=peticion.expediente or None,
    )
    codigo = registro.registrar_revision(
        obra=peticion.obra,
        denominacion=peticion.denominacion,
        titulo=peticion.titulo,
        revision=peticion.revision,
        fecha=peticion.fecha,
        n_indice=peticion.n_indice,
        hojas=hojas,
        motivo=peticion.motivo,
        # En modo prueba el registro no se guarda, asi que no hay razon para
        # impedir re-sellar una revision ya emitida: es justo lo que hace falta
        # para reimprimir una hoja de ensayo.
        permitir_repetida=cfg.modo_prueba,
    )

    # 4 y 5 · Dirección y QR.
    url = componer_url(cfg.url_base, codigo)
    q = _qr.generar(url, cfg.correccion_errores)

    # 6 y 8 · Estampado.
    destino = nombre_salida(pdf, codigo.revision, cfg.ruta_salida)
    res = _estampar.estampar(
        pdf,
        destino,
        q=q,
        codigo=str(codigo),
        colocacion=cfg.colocacion,
        modo_prueba=cfg.modo_prueba,
        modulo_minimo_mm=cfg.modulo_minimo_mm,
    )

    # 7 · El registro se persiste al final, cuando ya hay PDF sellado.
    if not cfg.modo_prueba:
        registro.guardar()
    else:
        log.warning(
            "MODO PRUEBA: no se ha tocado el registro. Configura «url_base» en "
            "config/config.yaml para emitir de verdad."
        )

    avisos = list(res.avisos)
    if cfg.modo_prueba:
        avisos.insert(
            0,
            "MODO PRUEBA. El plano lleva estampado «PRUEBA — NO VÁLIDO» y el "
            "registro no se ha modificado. Este PDF NO puede ir a obra."
            + (
                " El QR lleva la dirección real, para que el ensayo de "
                "impresión mida la densidad de verdad, pero esa dirección "
                "todavía no está publicada."
                if cfg.forzar_prueba
                else " Falta «url_base», así que el QR no apunta a ninguna parte."
            ),
        )

    return Emision(
        codigo=codigo,
        url=url,
        pdf=res.ruta,
        hojas=hojas,
        modo_prueba=cfg.modo_prueba,
        lado_modulo_mm=res.lado_modulo_mm,
        version_qr=res.version_qr,
        avisos=avisos,
    )
