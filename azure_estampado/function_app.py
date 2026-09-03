"""Servicio de estampado de QR sobre PDF, para Azure Functions.

Es la única pieza del sistema que Power Automate no puede hacer por sí mismo.
Y es deliberadamente tonta:

    recibe un PDF y un código  ->  devuelve el mismo PDF con el QR estampado

**Lo que este servicio NO hace, y conviene tenerlo claro antes de aprobarlo:**

* No guarda nada. El PDF se procesa en memoria y se devuelve. No hay base de
  datos, ni almacenamiento, ni registro del contenido.
* No accede a SharePoint, ni a Microsoft Graph, ni al tenant de INES. No tiene
  ni pide ningún permiso sobre nada.
* No hace ninguna llamada saliente. No consulta internet.
* No conoce ninguna credencial. La única clave que existe es la propia clave de
  función de Azure, que la guarda Power Automate para poder llamarlo.
* No sabe de qué obra es el plano, ni quién lo ha subido.

Toda la lógica de negocio —qué revisión es, qué correlativo le toca, si ya
estaba emitida, cuándo se publica— vive en Power Automate y en el registro. Aquí
solo se dibuja un cuadrado negro en una esquina.

Modelo de programación v2 de Azure Functions, runtime de Python.
"""

from __future__ import annotations

import io
import logging
import tempfile
from pathlib import Path

import azure.functions as func

from control_planos.estampar import Colocacion, estampar
from control_planos.qr import generar

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

#: Tope de tamaño del PDF de entrada. Los planos con ortofoto rondan los 50 MB;
#: se deja margen pero se acota, para que un fichero equivocado no agote la
#: memoria de la función.
MAX_BYTES = 120 * 1024 * 1024


@app.route(route="estampar", methods=["POST"])
def estampar_pdf(req: func.HttpRequest) -> func.HttpResponse:
    """Estampa el QR en todas las hojas de un PDF.

    Entrada:
        Cuerpo: el PDF en binario (``Content-Type: application/pdf``).
            Se envía en crudo y no en base64 a propósito: base64 engorda el
            contenido un 33 %, y con planos de 50 MB eso importa.
        Parámetros (en la cadena de consulta o en cabeceras):
            ``codigo``  obligatorio, p. ej. ``SESENA-103-R00``
            ``url``     obligatorio, la dirección que codifica el QR
            ``prueba``  opcional, ``1`` para estampar «PRUEBA — NO VÁLIDO»
            ``lado_qr_mm``, ``margen_derecho_mm``, ``margen_inferior_mm``
                        opcionales, para no tener que redesplegar si cambia
                        el cajetín de un cliente

    Salida:
        El PDF sellado en binario. Las medidas del QR van en cabeceras
        ``X-QR-*`` para que Power Automate pueda registrarlas o avisar.
    """
    def dato(nombre: str, defecto: str | None = None) -> str | None:
        return req.params.get(nombre) or req.headers.get(nombre) or defecto

    codigo = dato("codigo")
    url = dato("url")
    if not codigo or not url:
        return func.HttpResponse(
            "Faltan «codigo» o «url».", status_code=400, mimetype="text/plain"
        )

    cuerpo = req.get_body()
    if not cuerpo:
        return func.HttpResponse(
            "El cuerpo de la peticion esta vacio: falta el PDF.",
            status_code=400, mimetype="text/plain",
        )
    if len(cuerpo) > MAX_BYTES:
        return func.HttpResponse(
            f"El PDF pesa {len(cuerpo) / 1024 / 1024:.0f} MB y el tope es "
            f"{MAX_BYTES / 1024 / 1024:.0f} MB.",
            status_code=413, mimetype="text/plain",
        )

    try:
        col = Colocacion(
            lado_qr_mm=float(dato("lado_qr_mm", "20") or 20),
            margen_derecho_mm=float(dato("margen_derecho_mm", "22.7") or 22.7),
            margen_inferior_mm=float(dato("margen_inferior_mm", "22.8") or 22.8),
        )
    except ValueError:
        return func.HttpResponse(
            "Alguna medida no es un numero.", status_code=400, mimetype="text/plain"
        )

    logging.info("estampando %s (%.1f MB)", codigo, len(cuerpo) / 1024 / 1024)

    # Se trabaja en un directorio temporal que el sistema borra al salir. No
    # queda copia del plano en ninguna parte.
    with tempfile.TemporaryDirectory() as tmp:
        entrada = Path(tmp) / "entrada.pdf"
        salida = Path(tmp) / "salida.pdf"
        entrada.write_bytes(cuerpo)
        try:
            q = generar(url, "Q")
            res = estampar(
                entrada, salida,
                q=q, codigo=codigo, colocacion=col,
                modo_prueba=dato("prueba") in ("1", "true", "True"),
            )
            sellado = salida.read_bytes()
        except ValueError as exc:
            # PDF cifrado, vacio o ilegible: es culpa de la entrada, no nuestra.
            logging.warning("PDF rechazado (%s): %s", codigo, exc)
            return func.HttpResponse(str(exc), status_code=422, mimetype="text/plain")
        except Exception:
            logging.exception("fallo al estampar %s", codigo)
            return func.HttpResponse(
                "Error interno al estampar el PDF.",
                status_code=500, mimetype="text/plain",
            )

    return func.HttpResponse(
        sellado,
        status_code=200,
        mimetype="application/pdf",
        headers={
            "X-QR-Hojas": str(res.paginas),
            "X-QR-Modulo-Mm": f"{res.lado_modulo_mm:.3f}",
            "X-QR-Version": str(res.version_qr),
            "X-QR-Avisos": " | ".join(res.avisos)[:900],
        },
    )


@app.route(route="salud", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def salud(req: func.HttpRequest) -> func.HttpResponse:
    """Comprobación de que el servicio está vivo. No procesa nada."""
    from control_planos import __version__

    return func.HttpResponse(
        f"control-planos {__version__} · servicio de estampado operativo\n",
        mimetype="text/plain",
    )
