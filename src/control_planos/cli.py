"""Interfaz de la herramienta de emisión.

Es solo una puerta de entrada al motor de `control_planos.emision`. Hay dos
formas de usarla y las dos acaban en el mismo sitio:

* **Arrastrando el PDF** sobre el acceso directo «Emitir plano»: la herramienta
  pregunta lo que falta, una cosa a la vez. Pensada para quien no vive en la
  consola. Es un acceso directo y no un ``.bat`` porque en los puestos de INES
  esta prohibido ejecutar ``.bat`` (ver ``docs/DECISIONES.md``, D-16).
* **Con parámetros**, para trabajar rápido o para automatizar:

      python -m control_planos.cli plano.pdf --obra SESENA \
          --denominacion "PLANOS SEÑALIZACIÓN PROVISIONAL" --rev 1 \
          --indice 03 --motivo "Ampliación de la zona de obra"

Si falta algún dato obligatorio, se pregunta. Nunca se inventa.
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
import sys
from datetime import date
from pathlib import Path

from . import config as _config
from .codigo import CodigoInvalido, normalizar_revision
from .emision import Emision, Peticion, emitir
from .registro import ErrorRegistro, Registro

ANCHO = 74


# ── Consola ───────────────────────────────────────────────────────────────
# La consola de Windows usa cp1252 por defecto, que no admite caracteres de
# recuadro ni el símbolo de aviso, y al redirigir la salida a un fichero
# tampoco admite las tildes. Sin esto, la herramienta se cae con
# UnicodeEncodeError antes de hacer nada. No es un detalle estético: es la
# diferencia entre que funcione o no en un puesto corriente de la oficina.

def _preparar_consola() -> bool:
    """Pone la salida en UTF-8 si se puede. Devuelve si admite adornos."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, OSError, ValueError):
            pass  # flujo no reconfigurable (pipe, IDE); seguimos igual
    try:
        "═─·⚠".encode(sys.stdout.encoding or "ascii")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


#: Se rellenan en `main`. Por defecto, los seguros.
_G = {"doble": "=", "simple": "-", "punto": "*", "aviso": "!"}


def _regla(clave: str = "simple") -> None:
    print(_G[clave] * ANCHO)


def _titulo(texto: str) -> None:
    print()
    _regla("doble")
    print(f"  {texto}")
    _regla("doble")


def _preguntar(
    etiqueta: str,
    *,
    ayuda: str = "",
    obligatorio: bool = True,
    defecto: str = "",
) -> str:
    """Pregunta una cosa. Solo una. Repite hasta tener respuesta válida."""
    if ayuda:
        print(f"\n  {ayuda}")
    sufijo = f" [{defecto}]" if defecto else ""
    while True:
        try:
            r = input(f"  {etiqueta}{sufijo}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Cancelado. No se ha modificado nada.\n")
            raise SystemExit(130)
        if not r and defecto:
            return defecto
        if r or not obligatorio:
            return r
        print("    (hace falta un valor)")


def _datos_obra(
    obra: str, registro: Registro, args: argparse.Namespace
) -> dict[str, str]:
    """Los datos de la obra, si es nueva y hacen falta.

    Se piden una sola vez, la primera vez que aparece una obra en el registro.
    Si ya está registrada, devuelve un diccionario vacío y no molesta.

    Los toma de los parámetros si se han dado; si no, pregunta. Nunca los
    inventa: sin nombre, la obra aparecería en la web pública con su código
    interno («SESENA») en lugar de su nombre, y el encargado no la reconocería.
    """
    if obra in registro.obras:
        return {}

    extra = {
        "nombre_obra": args.nombre_obra or "",
        "expediente": args.expediente or "",
        "descripcion_obra": args.descripcion or "",
    }
    if extra["nombre_obra"]:
        return extra

    if not sys.stdin.isatty():
        raise SystemExit(
            f"\n  «{obra}» es una obra nueva y no se ha indicado su nombre.\n"
            "  Añade --nombre-obra \"...\" (y si quieres --expediente y\n"
            "  --descripcion), o ejecútalo sin --obra para que te lo pregunte.\n"
        )

    print(f"\n  «{obra}» es una obra nueva. Necesito sus datos una sola vez.")
    extra["nombre_obra"] = _preguntar("Nombre de la obra")
    if not extra["expediente"]:
        extra["expediente"] = _preguntar("Expediente", obligatorio=False)
    if not extra["descripcion_obra"]:
        extra["descripcion_obra"] = _preguntar(
            "Descripción (una línea)", obligatorio=False
        )
    return extra


def _elegir_obra(registro: Registro, args: argparse.Namespace) -> tuple[str, dict[str, str]]:
    """Pregunta la obra, ofreciendo las que ya están registradas."""
    conocidas = sorted(registro.obras)
    if conocidas:
        print("\n  Obras ya registradas:")
        for clave in conocidas:
            n = len(registro.documentos(clave))
            print(f"    {_G['punto']} {clave:12} {registro.obras[clave].get('nombre','')} "
                  f"({n} documento{'s' if n != 1 else ''})")
    obra = _preguntar(
        "Código de obra",
        ayuda="Código corto, en mayúsculas y sin eñes ni tildes (p. ej. SESENA).",
    ).upper()
    return obra, _datos_obra(obra, registro, args)


def _completar(args: argparse.Namespace, registro: Registro) -> Peticion:
    """Rellena lo que falte preguntando, de uno en uno."""
    pdf = Path(args.pdf) if args.pdf else Path(_preguntar("Ruta del PDF ploteado"))
    pdf = Path(str(pdf).strip('"').strip("'"))
    if not pdf.exists():
        raise SystemExit(f"\n  No existe el fichero: {pdf}\n")

    if args.obra:
        obra = args.obra.upper()
        extra = _datos_obra(obra, registro, args)
    else:
        obra, extra = _elegir_obra(registro, args)

    denominacion = args.denominacion
    if not denominacion:
        docs = registro.documentos(obra)
        if docs:
            print("\n  Documentos ya registrados en esta obra:")
            for d in docs:
                print(f"    {_G['punto']} {d['id']:14} R{d['vigente']}  {d['denominacion']}")
            print("\n  Si escribes una denominación que ya existe, se emitirá una")
            print("  revisión nueva de ese documento y conservará su correlativo.")
        denominacion = _preguntar(
            "Denominación del documento",
            ayuda="Tal como figura en el cajetín, en «DESIGNACIÓN DEL PLANO».",
        )

    doc = registro.buscar_por_denominacion(obra, denominacion)
    if doc:
        siguiente = normalizar_revision(int(doc["vigente"]) + 1)
        print(f"\n  Ese documento ya existe: {doc['id']}, vigente la R{doc['vigente']}.")
    else:
        siguiente = "00"
        print(f"\n  Documento nuevo. Se le asignará el correlativo "
              f"{registro.siguiente_correlativo(obra)}.")

    revision = args.rev if args.rev is not None else _preguntar(
        "Revisión", defecto=siguiente
    )
    titulo = args.titulo or _preguntar(
        "Título del plano",
        ayuda="La línea de detalle bajo la denominación. Puede quedar vacío.",
        obligatorio=False,
    )
    indice = args.indice or _preguntar(
        "Nº de índice",
        ayuda="El «Nº» que lleva el cajetín de ESTE papel. Se guarda con esta "
              "revisión, así que puede cambiar en las siguientes.",
    )
    motivo = args.motivo
    if motivo is None:
        motivo = "" if not doc else _preguntar(
            "Motivo del cambio",
            ayuda="Lo verá el encargado en obra al escanear. Sé concreto.",
            obligatorio=False,
        )

    return Peticion(
        pdf=pdf,
        obra=obra,
        denominacion=denominacion,
        revision=str(revision),
        n_indice=indice,
        titulo=titulo,
        motivo=motivo,
        fecha=args.fecha or date.today().isoformat(),
        **extra,
    )


def _informar(em: Emision) -> None:
    _titulo("EMITIDO" if not em.modo_prueba else "GENERADO EN MODO PRUEBA")
    print(f"  Código          {em.codigo}")
    print(f"  Documento       {em.codigo.documento}")
    print(f"  Hojas selladas  {em.hojas}")
    print(f"  PDF             {em.pdf}")
    print(f"  Dirección QR    {em.url}")
    print(f"  QR              versión {em.version_qr}, "
          f"módulo de {em.lado_modulo_mm:.2f} mm")
    if em.avisos:
        print()
        _regla()
        for a in em.avisos:
            print(f"  {_G['aviso']}  " + a.replace("\n", "\n     "))
        _regla()
    print()


# ── Punto de entrada ──────────────────────────────────────────────────────

def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="control-planos",
        description="Estampa el QR de control sobre un plano ploteado y "
                    "actualiza el registro de revisiones.",
    )
    p.add_argument("pdf", nargs="?", help="PDF ploteado. Si falta, se pregunta.")
    p.add_argument("--obra", help="Código corto de obra (p. ej. SESENA)")
    p.add_argument("--nombre-obra", dest="nombre_obra",
                   help="Nombre de la obra. Solo se usa la primera vez que "
                        "aparece; es lo que se ve en la web pública")
    p.add_argument("--expediente", help="Expediente del cliente. Solo la primera vez")
    p.add_argument("--descripcion", help="Descripción de la obra, una línea. "
                                         "Solo la primera vez")
    p.add_argument("--denominacion", help="Denominación del documento")
    p.add_argument("--titulo", help="Título del plano")
    p.add_argument("--rev", help="Número de revisión (0, 1, 2...)")
    p.add_argument("--indice", help="Nº de índice del cajetín de este papel")
    p.add_argument("--motivo", help="Motivo del cambio, visible en obra")
    p.add_argument("--fecha", help="Fecha de emisión AAAA-MM-DD (por defecto, hoy)")
    p.add_argument("--config", help="Ruta alternativa del config.yaml")
    p.add_argument(
        "--resellar", action="store_true",
        help="Vuelve a generar el PDF sellado de una revision YA registrada, "
             "sin duplicarla y sin tocar el registro. Para cuando el fichero "
             "sellado se ha perdido o hace falta otra copia.",
    )
    p.add_argument(
        "--prueba", action="store_true",
        help="Sella como PRUEBA y no toca el registro, aunque la dirección de "
             "la web esté configurada. Es lo que hay que usar para el ensayo "
             "de impresión: el QR lleva la dirección real, que es la que "
             "determina si se puede leer en papel.",
    )
    p.add_argument("-v", "--verbose", action="store_true", help="Traza detallada")
    p.add_argument(
        "--pausar", action="store_true",
        help="Espera a que se pulse Intro antes de cerrar. Lo usan los accesos "
             "directos del escritorio: al lanzarse desde el explorador, la "
             "ventana se cerraria de golpe y no se leeria el resultado.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    if _preparar_consola():
        _G.update(doble="═", simple="─", punto="·",
                  aviso="⚠")
    args = construir_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="  %(levelname)s  %(message)s",
    )

    try:
        cfg = _config.cargar(args.config)
    except _config.ErrorConfig as exc:
        print(f"\n  Error de configuración: {exc}\n", file=sys.stderr)
        return 2

    if args.prueba:
        cfg = dataclasses.replace(cfg, forzar_prueba=True)
    if args.resellar:
        cfg = dataclasses.replace(cfg, resellar=True)

    _titulo("CONTROL DE PLANOS - EMISION")
    if cfg.modo_prueba:
        if args.prueba:
            print("  MODO PRUEBA pedido con --prueba. El QR llevará la dirección")
            print("  real, para que el ensayo de impresión mida la densidad de")
            print("  verdad, pero el plano irá sellado como PRUEBA y el registro")
            print("  no se tocará.")
        else:
            print("  MODO PRUEBA: falta «url_base» en config/config.yaml.")
            print("  Los planos se sellarán como PRUEBA y el registro no se tocará.")

    registro = Registro.cargar(cfg.ruta_registro, cfg.correlativo_inicial)

    try:
        peticion = _completar(args, registro)
        em = emitir(peticion, cfg)
    except (CodigoInvalido, ErrorRegistro, ValueError, FileNotFoundError) as exc:
        print(f"\n  No se ha emitido nada.\n  {exc}\n", file=sys.stderr)
        return 1

    _informar(em)
    return 0


def _con_pausa(argv: list[str] | None = None) -> int:
    """`main` envuelto en una espera final, para lanzarlo desde el explorador."""
    try:
        codigo = main(argv)
    except SystemExit as exc:
        codigo = int(exc.code or 0)
    if "--pausar" in (sys.argv[1:] if argv is None else argv):
        print()
        try:
            input("  Pulsa Intro para cerrar esta ventana. ")
        except (EOFError, KeyboardInterrupt):
            pass
    return codigo


if __name__ == "__main__":
    raise SystemExit(_con_pausa())
