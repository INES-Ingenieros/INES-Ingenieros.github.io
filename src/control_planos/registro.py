"""Lectura y escritura del registro de planos (``planos.json``).

El registro es la única fuente de verdad sobre qué revisión está vigente. Es el
mismo fichero que consume la web pública, así que su forma está fijada por lo
que la página sabe leer.

Estructura, por documento y no por hoja (decisión D-06), con el número de
índice y el número de hojas guardados dentro de cada revisión (decisión D-10),
porque el índice de planos se reordena y la pantalla tiene que seguir
coincidiendo con el papel que se está escaneando.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .codigo import Codigo, componer

CORRELATIVO_INICIAL_POR_DEFECTO = 101


class ErrorRegistro(RuntimeError):
    """El registro está incoherente, o la operación pedida lo dejaría así."""


@dataclass
class Registro:
    """El registro de planos, cargado en memoria."""

    ruta: Path
    datos: dict[str, Any] = field(default_factory=dict)
    correlativo_inicial: int = CORRELATIVO_INICIAL_POR_DEFECTO

    # ── Carga y guardado ──────────────────────────────────────────────────

    @classmethod
    def cargar(
        cls,
        ruta: str | Path,
        correlativo_inicial: int = CORRELATIVO_INICIAL_POR_DEFECTO,
    ) -> "Registro":
        """Lee el registro del disco. Si no existe, crea uno vacío en memoria."""
        ruta = Path(ruta)
        if ruta.exists():
            with ruta.open(encoding="utf-8") as f:
                datos = json.load(f)
        else:
            datos = {"actualizado": None, "obras": {}}
        datos.setdefault("obras", {})
        return cls(ruta=ruta, datos=datos, correlativo_inicial=correlativo_inicial)

    def guardar(self, *, respaldo: bool = True) -> None:
        """Escribe el registro al disco, dejando antes una copia de seguridad.

        La escritura es atómica: se escribe en un fichero temporal y se
        reemplaza al final. Así una interrupción no deja el registro a medias,
        que dejaría la web pública sirviendo un JSON roto.
        """
        self.verificar()
        self.datos["actualizado"] = datetime.now(timezone.utc).astimezone().isoformat(
            timespec="seconds"
        )
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        if respaldo and self.ruta.exists():
            shutil.copy2(self.ruta, self.ruta.with_suffix(".json.bak"))
        tmp = self.ruta.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(self.datos, f, ensure_ascii=False, indent=2)
            f.write("\n")
        tmp.replace(self.ruta)

    # ── Consultas ─────────────────────────────────────────────────────────

    @property
    def obras(self) -> dict[str, Any]:
        return self.datos["obras"]

    def documentos(self, obra: str) -> list[dict[str, Any]]:
        return self.obras.get(obra.upper(), {}).get("documentos", [])

    def buscar_documento(self, obra: str, correlativo: int) -> dict[str, Any] | None:
        """Devuelve el documento con ese correlativo, o ``None``."""
        buscado = f"{obra.upper()}-{correlativo:03d}"
        for doc in self.documentos(obra):
            if doc.get("id") == buscado:
                return doc
        return None

    def buscar_por_denominacion(
        self, obra: str, denominacion: str
    ) -> dict[str, Any] | None:
        """Devuelve el documento cuya denominación coincide, o ``None``.

        Sirve para reutilizar el correlativo de un documento ya registrado
        cuando se emite una revisión nueva, en lugar de crear otro documento.
        La comparación ignora mayúsculas y espacios de sobra.
        """
        clave = " ".join((denominacion or "").split()).casefold()
        for doc in self.documentos(obra):
            if " ".join(doc.get("denominacion", "").split()).casefold() == clave:
                return doc
        return None

    def siguiente_correlativo(self, obra: str) -> int:
        """El siguiente correlativo libre de la obra.

        Nunca reutiliza uno ya usado, ni siquiera si el documento se anuló:
        un QR antiguo apuntaría entonces a un documento distinto, que es el
        fallo más grave posible en un sistema de control de revisiones
        (decisión D-08).
        """
        usados = [
            int(doc["id"].rsplit("-", 1)[-1])
            for doc in self.documentos(obra)
            if doc.get("id", "").rsplit("-", 1)[-1].isdigit()
        ]
        return max(usados) + 1 if usados else self.correlativo_inicial

    # ── Alta de obra ──────────────────────────────────────────────────────

    def asegurar_obra(
        self,
        obra: str,
        nombre: str | None = None,
        descripcion: str | None = None,
        expediente: str | None = None,
    ) -> dict[str, Any]:
        """Devuelve la obra, creándola si no existía."""
        obra = obra.upper()
        if obra not in self.obras:
            self.obras[obra] = {
                "nombre": nombre or obra,
                "descripcion": descripcion or "",
                "expediente": expediente or "—",
                "documentos": [],
            }
        else:
            ficha = self.obras[obra]
            if nombre:
                ficha["nombre"] = nombre
            if descripcion:
                ficha["descripcion"] = descripcion
            if expediente:
                ficha["expediente"] = expediente
        return self.obras[obra]

    # ── La operación central ──────────────────────────────────────────────

    def registrar_revision(
        self,
        *,
        obra: str,
        denominacion: str,
        revision: str,
        fecha: str,
        n_indice: str,
        hojas: int,
        titulo: str = "",
        motivo: str = "",
        correlativo: int | None = None,
        permitir_repetida: bool = False,
    ) -> Codigo:
        """Da de alta una revisión y la deja como la vigente.

        Si ya existe un documento con esa denominación en la obra, reutiliza su
        correlativo. Si no, asigna el siguiente libre. Todas las revisiones
        anteriores del documento quedan marcadas como superadas.

        Returns:
            El `Codigo` de la revisión registrada, listo para el QR.

        Args:
            permitir_repetida: deja pasar una revisión que ya existe, sin
                tocarla. Solo se usa en modo prueba, donde el registro no se
                guarda: hace falta para poder volver a sellar una hoja de
                ensayo de una revisión ya emitida.

        Raises:
            ErrorRegistro: si esa revisión ya estaba registrada. No se
                sobrescribe en silencio: el QR de la anterior ya puede estar
                impreso y circulando por la obra.
        """
        obra = obra.upper()
        self.asegurar_obra(obra)

        doc = self.buscar_por_denominacion(obra, denominacion)
        if doc is None:
            if correlativo is None:
                correlativo = self.siguiente_correlativo(obra)
            elif self.buscar_documento(obra, correlativo) is not None:
                raise ErrorRegistro(
                    f"el correlativo {correlativo} ya está usado en la obra {obra}"
                )
            codigo = componer(obra, correlativo, revision)
            doc = {
                "id": codigo.documento,
                "denominacion": denominacion,
                "titulo": titulo,
                "vigente": codigo.revision,
                "revisiones": [],
            }
            self.obras[obra]["documentos"].append(doc)
        else:
            correlativo = int(doc["id"].rsplit("-", 1)[-1])
            codigo = componer(obra, correlativo, revision)
            if titulo:
                doc["titulo"] = titulo

        if not permitir_repetida and any(
            r.get("rev") == codigo.revision for r in doc["revisiones"]
        ):
            raise ErrorRegistro(
                f"la revisión R{codigo.revision} de {codigo.documento} ya está "
                "registrada. Si de verdad hay que rehacerla, hay que retirarla "
                "del registro a mano y a conciencia: su QR puede estar ya "
                "impreso y circulando por la obra."
            )

        for r in doc["revisiones"]:
            r["estado"] = "superado"

        doc["revisiones"].append(
            {
                "rev": codigo.revision,
                "fecha": fecha,
                "n_indice": str(n_indice),
                "hojas": int(hojas),
                "estado": "vigente",
                "motivo": motivo or ("Primera emisión" if not doc["revisiones"] else ""),
            }
        )
        doc["revisiones"].sort(key=lambda r: r["rev"])
        doc["vigente"] = codigo.revision
        return codigo

    # ── Integridad ────────────────────────────────────────────────────────

    def verificar(self) -> None:
        """Comprueba que el registro es coherente antes de escribirlo.

        Raises:
            ErrorRegistro: describiendo el primer problema encontrado.
        """
        for clave, obra in self.obras.items():
            vistos: set[str] = set()
            for doc in obra.get("documentos", []):
                ident = doc.get("id", "?")
                if ident in vistos:
                    raise ErrorRegistro(f"identificador repetido: {ident}")
                vistos.add(ident)
                if not ident.startswith(clave + "-"):
                    raise ErrorRegistro(
                        f"el documento {ident} no pertenece a la obra {clave}"
                    )
                revs = doc.get("revisiones", [])
                if not revs:
                    raise ErrorRegistro(f"{ident} no tiene ninguna revisión")
                numeros = [r.get("rev") for r in revs]
                if len(numeros) != len(set(numeros)):
                    raise ErrorRegistro(f"{ident} tiene revisiones repetidas")
                if doc.get("vigente") not in numeros:
                    raise ErrorRegistro(
                        f"{ident} declara vigente la R{doc.get('vigente')}, "
                        "que no está en su lista de revisiones"
                    )
                vigentes = [r for r in revs if r.get("estado") == "vigente"]
                if len(vigentes) != 1:
                    raise ErrorRegistro(
                        f"{ident} tiene {len(vigentes)} revisiones marcadas como "
                        "vigentes; debe haber exactamente una"
                    )
                if vigentes[0].get("rev") != doc.get("vigente"):
                    raise ErrorRegistro(
                        f"en {ident} la revisión marcada vigente no coincide con "
                        "el campo «vigente»"
                    )
