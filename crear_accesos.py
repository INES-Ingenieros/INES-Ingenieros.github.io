"""Crea los dos accesos directos con los que se usa la herramienta.

    py crear_accesos.py

Se ejecuta una sola vez por ordenador, y deja en la carpeta del proyecto:

    Emitir plano.lnk        <- se le arrastra el PDF encima
    Publicar en la web.lnk  <- doble clic

**Por qué accesos directos y no ficheros .bat.** En el Windows corporativo de
INES está prohibido ejecutar `.bat`: incluso uno de dos líneas responde «Acceso
denegado» al abrirlo desde el explorador. Un acceso directo no es un script,
sino un puntero a `python.exe`, que sí está permitido. Y conserva lo que hacía
falta: arrastrar un PDF encima le pasa su ruta como argumento.
Ver ``docs/DECISIONES.md``, decisión D-16.

Los accesos directos apuntan a rutas absolutas de este ordenador, así que **no
se suben al repositorio**: en otro puesto se vuelve a ejecutar este script.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PYTHON = RAIZ / ".venv" / "Scripts" / "python.exe"

ACCESOS = [
    (
        "Emitir plano",
        "-m control_planos.cli --pausar",
        "Arrastra encima el PDF ploteado para meterle el QR de control",
    ),
    (
        "Publicar en la web",
        "-m control_planos.publicar --pausar",
        "Sube a la web las revisiones emitidas, para que los QR respondan en obra",
    ),
]

# PowerShell es la via mas fiable para crear un .lnk en Windows sin anadir
# dependencias al proyecto (pywin32 obligaria a instalar un paquete mas solo
# para esto, y en un puesto sin compilador puede dar problemas).
PLANTILLA = """
$w = New-Object -ComObject WScript.Shell
$l = $w.CreateShortcut('{destino}')
$l.TargetPath = '{python}'
$l.Arguments = '{argumentos}'
$l.WorkingDirectory = '{raiz}'
$l.Description = '{descripcion}'
$l.Save()
"""


def main() -> int:
    if not PYTHON.exists():
        print(f"\n  No se encuentra el entorno virtual: {PYTHON}")
        print("\n  Para crearlo, en una consola en esta carpeta:")
        print("      python -m venv .venv")
        print("      .venv\\Scripts\\python.exe -m pip install -e .\n")
        return 1

    print(f"\n  Creando accesos directos en {RAIZ}\n")
    for nombre, argumentos, descripcion in ACCESOS:
        destino = RAIZ / f"{nombre}.lnk"
        guion = PLANTILLA.format(
            destino=destino, python=PYTHON, argumentos=argumentos,
            raiz=RAIZ, descripcion=descripcion,
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", guion],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if r.returncode != 0 or not destino.exists():
            print(f"    FALLO   {destino.name}")
            if r.stderr.strip():
                print("            " + r.stderr.strip().splitlines()[0])
            return 1
        print(f"    creado  {destino.name}")

    print("\n  Listo. A partir de ahora:")
    print("    1. Arrastra el PDF ploteado sobre «Emitir plano»")
    print("    2. Doble clic en «Publicar en la web»\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
