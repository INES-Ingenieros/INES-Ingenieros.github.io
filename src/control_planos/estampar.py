"""Estampado del QR y del código legible sobre el PDF ya ploteado.

Se trabaja sobre el PDF, no sobre el DWG (decisión D-05): la herramienta no
sabe ni le importa con qué programa se generó el plano.

El QR se dibuja como **vectores**, no como imagen. A 20 mm de lado cada módulo
mide medio milímetro, y una imagen rasterizada pierde definición justo en el
borde de cada módulo, que es donde la cámara del móvil decide si lee o no.

Junto al QR va siempre el código en texto legible. No es decorativo: es la vía
de contraste cuando el QR está roto, mojado o mal fotocopiado, y cuando no hay
cobertura (decisión D-07).
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .qr import QR

log = logging.getLogger(__name__)

FUENTE = "Helvetica-Bold"
"""Tipografía del código legible.

Se usa una de las 14 tipografías estándar del formato PDF a propósito: no hay
que incrustar ningún fichero, el PDF no engorda y se ve igual en cualquier
visor y en cualquier plóter. Montserrat quedaría más de INES, pero a 7 pt sobre
un código alfanumérico la diferencia no se aprecia y el coste sí.
"""


@dataclass
class Colocacion:
    """Dónde y cómo se estampa. En milímetros, desde el borde de la hoja."""

    lado_qr_mm: float = 20.0
    margen_derecho_mm: float = 24.0
    margen_inferior_mm: float = 23.0
    hueco_texto_mm: float = 2.5
    texto_pt: float = 7.0
    recuadro: bool = True


@dataclass
class Resultado:
    """Lo que ha pasado al estampar."""

    ruta: Path
    paginas: int
    lado_modulo_mm: float
    version_qr: int
    avisos: list[str]


def _dibujar_qr(c: canvas.Canvas, q: QR, x: float, y: float, lado: float) -> None:
    """Pinta la matriz del QR como rectángulos vectoriales.

    Los módulos negros contiguos de una misma fila se pintan como un único
    rectángulo. Reduce mucho el número de objetos del PDF sin cambiar el
    resultado impreso.
    """
    n = q.lado_modulos
    paso = lado / n
    c.setFillColorRGB(0, 0, 0)
    for i, fila in enumerate(q.matriz):
        # La fila 0 de la matriz es la de arriba; en PDF la Y crece hacia arriba.
        fy = y + lado - (i + 1) * paso
        inicio: int | None = None
        for j, negro in enumerate(list(fila) + [False]):
            if negro and inicio is None:
                inicio = j
            elif not negro and inicio is not None:
                c.rect(
                    x + inicio * paso, fy, (j - inicio) * paso, paso,
                    stroke=0, fill=1,
                )
                inicio = None


def _capa(
    ancho: float,
    alto: float,
    q: QR,
    codigo: str,
    col: Colocacion,
    modo_prueba: bool,
) -> bytes:
    """Genera un PDF de una página, del tamaño de la hoja, con solo el sello."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(ancho, alto))

    lado = col.lado_qr_mm * mm
    x_qr = ancho - col.margen_derecho_mm * mm - lado
    y_qr = col.margen_inferior_mm * mm

    lineas = [codigo] if not modo_prueba else ["PRUEBA — NO VÁLIDO", codigo]
    anchos = [stringWidth(t, FUENTE, col.texto_pt) for t in lineas]
    ancho_texto = max(anchos) if anchos else 0.0
    x_texto_der = x_qr - col.hueco_texto_mm * mm

    if col.recuadro:
        # Fondo blanco bajo el sello, para que se lea aunque caiga sobre una
        # zona dibujada del plano. Con un hilo fino gris para que se distinga
        # del papel y no parezca un hueco del dibujo.
        holgura = 1.0 * mm
        x0 = x_texto_der - ancho_texto - holgura
        c.setFillColorRGB(1, 1, 1)
        c.setStrokeColorRGB(0.72, 0.72, 0.72)
        c.setLineWidth(0.3)
        c.rect(x0, y_qr - holgura, (x_qr + lado + holgura) - x0,
               lado + 2 * holgura, stroke=1, fill=1)

    _dibujar_qr(c, q, x_qr, y_qr, lado)

    # Texto a la izquierda del QR, alineado a la derecha y centrado en vertical.
    interlinea = col.texto_pt * 1.25
    alto_texto = interlinea * len(lineas)
    y_linea = y_qr + (lado + alto_texto) / 2 - interlinea + col.texto_pt * 0.25
    c.setFont(FUENTE, col.texto_pt)
    for i, texto in enumerate(lineas):
        if modo_prueba and i == 0:
            c.setFillColorRGB(0.82, 0.14, 0.16)   # rojo, inconfundible
        else:
            c.setFillColorRGB(0.06, 0.07, 0.15)   # navy de INES
        c.drawRightString(x_texto_der, y_linea - i * interlinea, texto)

    c.showPage()
    c.save()
    return buf.getvalue()


def estampar(
    pdf_entrada: str | Path,
    pdf_salida: str | Path,
    *,
    q: QR,
    codigo: str,
    colocacion: Colocacion | None = None,
    modo_prueba: bool = False,
    modulo_minimo_mm: float = 0.60,
) -> Resultado:
    """Estampa el QR y el código en **todas** las hojas del PDF.

    En todas y no solo en la primera: en obra las hojas se separan del conjunto,
    y una hoja suelta tiene que seguir siendo verificable (decisión D-06).

    Args:
        pdf_entrada: el PDF tal como salió de AutoCAD o Civil 3D.
        pdf_salida: dónde se escribe el PDF sellado. No se toca el original.
        q: el QR ya calculado.
        codigo: el identificador en texto, que se imprime junto al QR.
        colocacion: medidas del sello. Si no se pasa, se usan las de por defecto.
        modo_prueba: si es cierto, añade «PRUEBA — NO VÁLIDO» en rojo.
        modulo_minimo_mm: umbral por debajo del cual se avisa de que el QR
            puede no leerse en papel.

    Returns:
        Un `Resultado` con la ruta, el número de hojas y los avisos.

    Raises:
        FileNotFoundError: si el PDF de entrada no existe.
        ValueError: si el PDF está cifrado o no tiene páginas.
    """
    pdf_entrada, pdf_salida = Path(pdf_entrada), Path(pdf_salida)
    col = colocacion or Colocacion()
    avisos: list[str] = []

    if not pdf_entrada.exists():
        raise FileNotFoundError(f"no existe el PDF de entrada: {pdf_entrada}")

    lector = PdfReader(pdf_entrada)
    if lector.is_encrypted:
        raise ValueError(
            f"{pdf_entrada.name} está cifrado y no se puede sellar. "
            "Hay que volver a plotearlo sin protección."
        )
    if not lector.pages:
        raise ValueError(f"{pdf_entrada.name} no tiene ninguna página")

    lado_modulo = q.modulo_mm(col.lado_qr_mm)
    if lado_modulo < modulo_minimo_mm:
        avisos.append(
            f"el lado de cada módulo del QR sale de {lado_modulo:.2f} mm, por "
            f"debajo del mínimo recomendado de {modulo_minimo_mm:.2f} mm. "
            f"Para respetarlo, el QR tendría que medir "
            f"{q.lado_recomendado_mm(modulo_minimo_mm):.0f} mm de lado en vez de "
            f"{col.lado_qr_mm:.0f} mm, o habría que acortar la dirección web. "
            "Conviene imprimir una hoja y comprobar que un móvil lo lee."
        )

    # Se clona el documento en el escritor ANTES de superponer nada. Fusionar
    # sobre páginas que aún cuelgan del lector está obsoleto en pypdf y es poco
    # fiable: el contenido superpuesto puede perderse al escribir.
    escritor = PdfWriter(clone_from=str(pdf_entrada))
    tamanos: set[tuple[int, int]] = set()

    for pagina in escritor.pages:
        caja = pagina.mediabox
        ancho, alto = float(caja.width), float(caja.height)
        giro = int(pagina.get("/Rotate", 0) or 0) % 360
        tamanos.add((round(ancho / mm), round(alto / mm)))

        if giro:
            # La capa se dibuja en el sistema de coordenadas de la página, que
            # es anterior al giro de visualización. Se compensa dibujando sobre
            # el tamaño visual y girando la capa al superponerla.
            avisos.append(
                f"una hoja tiene giro de visualización de {giro}°. La posición "
                "del sello se ha compensado, pero conviene revisar esa hoja a "
                "ojo: no se ha podido validar contra un plano real girado."
            )
            visual = (alto, ancho) if giro in (90, 270) else (ancho, alto)
            capa_pdf = _capa(visual[0], visual[1], q, codigo, col, modo_prueba)
            capa = PdfReader(io.BytesIO(capa_pdf)).pages[0]
            capa.add_transformation(_giro(giro, ancho, alto))
        else:
            capa_pdf = _capa(ancho, alto, q, codigo, col, modo_prueba)
            capa = PdfReader(io.BytesIO(capa_pdf)).pages[0]

        pagina.merge_page(capa, over=True)

    if len(tamanos) > 1:
        avisos.append(
            "el PDF mezcla hojas de distinto tamaño "
            f"({', '.join(f'{a}x{b} mm' for a, b in sorted(tamanos))}). "
            "El sello se coloca respecto al borde de cada hoja, así que debería "
            "quedar bien, pero conviene mirarlo."
        )

    pdf_salida.parent.mkdir(parents=True, exist_ok=True)
    with pdf_salida.open("wb") as f:
        escritor.write(f)

    log.info("sellado %s → %s (%d hojas)", pdf_entrada.name, pdf_salida.name,
             len(lector.pages))

    return Resultado(
        ruta=pdf_salida,
        paginas=len(lector.pages),
        lado_modulo_mm=lado_modulo,
        version_qr=q.version,
        avisos=avisos,
    )


def _giro(grados: int, ancho: float, alto: float):
    """Transformación que compensa el giro de visualización de una página."""
    from pypdf import Transformation

    if grados == 90:
        return Transformation().rotate(90).translate(ancho, 0)
    if grados == 180:
        return Transformation().rotate(180).translate(ancho, alto)
    if grados == 270:
        return Transformation().rotate(270).translate(0, alto)
    return Transformation()
