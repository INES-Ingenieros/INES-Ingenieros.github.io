"""El test más importante de la suite: el recorrido físico completo.

Genera un plano, lo sella, lo rasteriza como si se imprimiera, **lee el QR de
vuelta** y comprueba que la dirección que sale es la que tenía que ser.

Es el único test que verifica lo que de verdad importa: que lo que acabe en el
papel se pueda leer. Todos los demás comprueban lógica; este comprueba óptica.

Necesita `opencv-python-headless`, que es solo de desarrollo y no forma parte de
la herramienta. Si no está instalado, el test se salta.
"""

from __future__ import annotations

import dataclasses

import pytest

from control_planos.emision import Peticion, emitir

cv2 = pytest.importorskip("cv2", reason="opencv-python-headless no instalado")
np = pytest.importorskip("numpy")
pdfium = pytest.importorskip("pypdfium2")


def _leer_qr_del_pdf(ruta, col, pagina: int = 0) -> str:
    """Rasteriza la página y lee el QR de la zona donde se estampó.

    Se recorta la zona del sello antes de decodificar: en un A3 completo el QR
    es una parte tan pequeña que el detector no lo encuentra.
    """
    doc = pdfium.PdfDocument(str(ruta))
    pg = doc[pagina]
    ancho_mm = float(pg.get_mediabox()[2] - pg.get_mediabox()[0]) * 25.4 / 72
    img = pg.render(scale=600 / 72).to_pil().convert("L")
    W, H = img.size
    pxmm = W / ancho_mm
    holgura = 4.0
    x1 = ancho_mm - col.margen_derecho_mm + holgura
    x0 = x1 - col.lado_qr_mm - 2 * holgura
    y0 = col.margen_inferior_mm - holgura
    y1 = y0 + col.lado_qr_mm + 2 * holgura
    rec = img.crop((int(x0 * pxmm), int(H - y1 * pxmm),
                    int(x1 * pxmm), int(H - y0 * pxmm)))
    r = cv2.QRCodeDetector().detectAndDecode(np.array(rec))
    return next((x for x in r if isinstance(x, str) and x), "")


class TestIdaYVuelta:
    def test_el_qr_estampado_se_puede_leer_y_dice_lo_que_debe(self, pdf_a3, cfg):
        cfg = dataclasses.replace(cfg, url_base="HTTPS://EJEMPLO.TEST")
        em = emitir(
            Peticion(
                pdf=pdf_a3(hojas=2), obra="SESENA",
                denominacion="PLANOS SEÑALIZACIÓN PROVISIONAL",
                revision="00", n_indice="01", nombre_obra="Emergencia Seseña",
            ),
            cfg,
        )
        leido = _leer_qr_del_pdf(em.pdf, cfg.colocacion)
        assert leido, "el QR estampado no se ha podido leer del PDF rasterizado"
        assert leido == "HTTPS://EJEMPLO.TEST/?p=SESENA-101-R00"

    def test_se_puede_leer_en_todas_las_hojas(self, pdf_a3, cfg):
        """En obra las hojas se separan; una hoja suelta debe seguir valiendo."""
        cfg = dataclasses.replace(cfg, url_base="HTTPS://EJEMPLO.TEST")
        em = emitir(
            Peticion(
                pdf=pdf_a3(hojas=3), obra="SESENA", denominacion="PLANTAS",
                revision="00", n_indice="01", nombre_obra="Emergencia Seseña",
            ),
            cfg,
        )
        for i in range(3):
            leido = _leer_qr_del_pdf(em.pdf, cfg.colocacion, pagina=i)
            assert leido == "HTTPS://EJEMPLO.TEST/?p=SESENA-101-R00", f"hoja {i + 1}"
