"""Publicación del registro en la web.

Segundo y último paso de la emisión. Hasta que esto se ejecuta, el plano ya
lleva el QR impreso pero la web no sabe que esa revisión existe: al escanearlo
en obra saldría «CÓDIGO NO VÁLIDO».

Está escrito en Python y no como un `.bat` porque **en el Windows corporativo de
INES está prohibido ejecutar ficheros `.bat`**: un `.bat` de dos líneas da
«Acceso denegado». Ver ``docs/DECISIONES.md``, decisión D-16.

Si el envío falla, se dice expresamente que los QR todavía no funcionan. Un
fallo silencioso aquí es peligroso: el papel ya está en la caseta.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .config import RAIZ

ANCHO = 74


def _git(*args: str, capturar: bool = True) -> subprocess.CompletedProcess:
    """Ejecuta git en la raíz del proyecto."""
    return subprocess.run(
        ["git", *args],
        cwd=RAIZ,
        capture_output=capturar,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _hay_git() -> bool:
    try:
        return _git("--version").returncode == 0
    except (FileNotFoundError, OSError):
        return False


def _regla(car: str = "=") -> None:
    print(car * ANCHO)


def _resumen_cambios(registro: str) -> list[str]:
    """Las líneas añadidas al registro, para que se vea qué se va a publicar."""
    d = _git("diff", "HEAD", "--", registro)
    interesantes = ('"id"', '"rev"', '"denominacion"', '"estado"', '"motivo"')
    return [
        l[1:].strip().rstrip(",")
        for l in d.stdout.splitlines()
        if l.startswith("+") and not l.startswith("+++")
        and any(c in l for c in interesantes)
    ]


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    pausar = "--pausar" in argv

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, OSError, ValueError):
        pass

    codigo = _publicar()

    if pausar:
        print()
        try:
            input("  Pulsa Intro para cerrar esta ventana. ")
        except (EOFError, KeyboardInterrupt):
            pass
    return codigo


def _publicar() -> int:
    print()
    _regla()
    print("  PUBLICAR EN LA WEB")
    _regla()
    print()

    if not _hay_git():
        print("  No se encuentra git en este ordenador, así que no se puede")
        print("  publicar. Avisa para resolverlo.")
        return 2

    registro = "planos.json"
    if not (RAIZ / registro).exists():
        print(f"  No existe {registro}. No hay nada que publicar.")
        return 1

    pendiente = _git("status", "--porcelain", "--", registro).stdout.strip()
    sin_enviar = _git("log", "--oneline", "@{u}..HEAD").stdout.strip()

    if not pendiente and not sin_enviar:
        print("  No hay revisiones nuevas por publicar.")
        print()
        print("  El registro no ha cambiado desde la última publicación. Si acabas")
        print("  de emitir un plano y sigue saliendo esto, comprueba que la emisión")
        print("  terminó sin errores.")
        return 0

    if pendiente:
        cambios = _resumen_cambios(registro)
        if cambios:
            print("  Se van a publicar estos datos del registro:")
            print()
            for l in cambios[:24]:
                print("    " + l)
            if len(cambios) > 24:
                print(f"    ... y {len(cambios) - 24} líneas más")
            print()
    if sin_enviar:
        n = len(sin_enviar.splitlines())
        print(f"  Hay además {n} publicación(es) anterior(es) sin enviar a internet.")
        print()

    try:
        r = input("  ¿Publicar ahora? (S/N): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n\n  Cancelado. No se ha subido nada.")
        return 130
    if r not in ("s", "si", "sí"):
        print("\n  Cancelado. No se ha subido nada.")
        return 0

    print()
    if pendiente:
        print("  Registrando el cambio...")
        if _git("add", registro).returncode != 0:
            print("  No se ha podido preparar el cambio. Nada subido.")
            return 1
        c = _git("commit", "-m", "Registro de planos actualizado")
        if c.returncode != 0:
            print("  No se ha podido registrar el cambio. Nada subido.")
            print("  " + (c.stderr or c.stdout).strip()[:400])
            return 1

    print("  Subiendo a internet...")
    p = _git("push", capturar=True)
    if p.returncode != 0:
        print()
        _regla("!")
        print("  ATENCIÓN: el envío ha fallado.")
        _regla("!")
        print()
        print("  El cambio está guardado en este ordenador pero NO en la web, así")
        print("  que los QR de los planos recién emitidos TODAVÍA NO FUNCIONAN en")
        print("  obra. Vuelve a ejecutar esto cuando tengas conexión.")
        print()
        detalle = (p.stderr or p.stdout).strip()
        if detalle:
            print("  Lo que dice git:")
            for l in detalle.splitlines()[:8]:
                print("    " + l)
        return 1

    print()
    _regla()
    print("  PUBLICADO")
    _regla()
    print()
    print("  La web tarda entre uno y dos minutos en actualizarse. Después, los")
    print("  QR de los planos emitidos ya responden en obra.")
    print()
    print("  https://ines-ingenieros.github.io")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
