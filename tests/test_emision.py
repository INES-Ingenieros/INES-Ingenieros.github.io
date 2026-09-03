"""Emisión completa: QR, estampado en el PDF y registro.

Ver decisiones D-05 (se estampa sobre el PDF), D-06 (en todas las hojas) y
D-13 (modo prueba mientras no haya dirección definitiva).
"""

from __future__ import annotations

import dataclasses

import pytest
from pypdf import PdfReader

from control_planos import qr as _qr
from control_planos.emision import Peticion, emitir, nombre_salida
from control_planos.registro import ErrorRegistro, Registro


def _peticion(pdf, **kw):
    base = dict(
        pdf=pdf,
        obra="SESENA",
        denominacion="PLANOS SEÑALIZACIÓN PROVISIONAL",
        revision="00",
        n_indice="01",
        titulo="Planta general zona de obra",
        fecha="2026-09-02",
        nombre_obra="Emergencia Seseña",
        expediente="A/OBR-036768/2026",
    )
    return Peticion(**{**base, **kw})


class TestQR:
    def test_el_numero_de_modulos_crece_con_la_longitud(self):
        corto = _qr.generar("https://x.test/?p=A-101-R00")
        largo = _qr.generar("https://" + "y" * 120 + "/?p=SESENA-101-R00")
        assert largo.lado_modulos > corto.lado_modulos

    def test_calcula_el_lado_del_modulo(self):
        q = _qr.generar("https://x.test/planos/?p=SESENA-101-R00")
        assert q.modulo_mm(18.0) == pytest.approx(18.0 / q.lado_modulos)

    def test_detecta_un_qr_demasiado_denso_para_su_tamano(self):
        """Es un límite físico: por debajo de 0,6 mm los móviles fallan."""
        q = _qr.generar("https://" + "z" * 200 + "/?p=SESENA-101-R00")
        assert not q.legible(18.0, 0.60)
        assert q.lado_recomendado_mm(0.60) > 18.0

    def test_rechaza_niveles_de_correccion_inventados(self):
        with pytest.raises(ValueError, match="nivel de corrección"):
            _qr.generar("hola", nivel="Z")

    def test_rechaza_texto_vacio(self):
        with pytest.raises(ValueError):
            _qr.generar("")


class TestEstampado:
    def test_sella_todas_las_hojas(self, pdf_a3, cfg):
        """Una hoja suelta en obra tiene que seguir siendo verificable (D-06)."""
        em = emitir(_peticion(pdf_a3(hojas=4)), cfg)
        assert em.hojas == 4
        assert len(PdfReader(em.pdf).pages) == 4

    def test_no_toca_el_pdf_original(self, pdf_a3, cfg):
        origen = pdf_a3(hojas=2)
        antes = origen.read_bytes()
        emitir(_peticion(origen), cfg)
        assert origen.read_bytes() == antes

    def test_por_defecto_solo_se_estampa_el_qr(self, pdf_a3, cfg):
        """Con el texto al lado, el sello pasa de un cuadrado de 20 mm a una
        tira de 42 mm que invade el cajetín y el dibujo. Ver D-17."""
        em = emitir(_peticion(pdf_a3(hojas=1)), cfg)
        texto = (PdfReader(em.pdf).pages[0].extract_text() or "").replace("\n", "")
        assert "SESENA-101-R00" not in texto

    def test_el_codigo_legible_se_puede_activar(self, pdf_a3, cfg):
        """Sigue disponible para quien quiera la vía de dictado (D-07)."""
        con_texto = dataclasses.replace(cfg.colocacion, texto_visible=True)
        cfg = dataclasses.replace(cfg, colocacion=con_texto)
        em = emitir(_peticion(pdf_a3(hojas=1)), cfg)
        texto = (PdfReader(em.pdf).pages[0].extract_text() or "").replace("\n", "")
        assert "SESENA-101-R00" in texto

    def test_conserva_el_contenido_original(self, pdf_a3, cfg):
        em = emitir(_peticion(pdf_a3(hojas=1)), cfg)
        assert "Hoja 1 de 1" in (PdfReader(em.pdf).pages[0].extract_text() or "")

    def test_conserva_el_tamano_de_hoja(self, pdf_a3, cfg):
        em = emitir(_peticion(pdf_a3(hojas=1)), cfg)
        caja = PdfReader(em.pdf).pages[0].mediabox
        assert round(float(caja.width) * 25.4 / 72) == 420
        assert round(float(caja.height) * 25.4 / 72) == 297

    def test_avisa_si_el_qr_sale_demasiado_denso(self, pdf_a3, cfg):
        estrecho = dataclasses.replace(cfg.colocacion, lado_qr_mm=6.0)
        cfg = dataclasses.replace(cfg, colocacion=estrecho)
        em = emitir(_peticion(pdf_a3(hojas=1)), cfg)
        assert any("módulo" in a for a in em.avisos)

    def test_falla_con_un_pdf_que_no_existe(self, cfg, tmp_path):
        with pytest.raises(FileNotFoundError):
            emitir(_peticion(tmp_path / "no_existe.pdf"), cfg)


class TestNombreDelFichero:
    def test_anade_el_sufijo_de_revision(self, tmp_path):
        r = nombre_salida(tmp_path / "01_DESVIOS.pdf", "00", tmp_path)
        assert r.name == "01_DESVIOS_R00.pdf"

    def test_no_acumula_sufijos(self, tmp_path):
        """Emitir la R01 de un fichero ya llamado _R00 no da _R00_R01."""
        r = nombre_salida(tmp_path / "01_DESVIOS_R00.pdf", "01", tmp_path)
        assert r.name == "01_DESVIOS_R01.pdf"

    def test_conserva_el_nombre_para_que_la_carpeta_se_ordene_por_indice(self, tmp_path):
        """El correlativo no entra en el nombre del fichero (D-12)."""
        r = nombre_salida(tmp_path / "01_DESVIOS.pdf", "00", tmp_path)
        assert "101" not in r.stem


class TestRegistroTrasEmitir:
    def test_deja_el_registro_escrito(self, pdf_a3, cfg):
        emitir(_peticion(pdf_a3(hojas=3)), cfg)
        reg = Registro.cargar(cfg.ruta_registro)
        doc = reg.buscar_documento("SESENA", 101)
        assert doc["vigente"] == "00"
        assert doc["revisiones"][0]["hojas"] == 3

    def test_las_hojas_se_cuentan_solas(self, pdf_a3, cfg):
        """No se pregunta un dato que está en el propio PDF."""
        emitir(_peticion(pdf_a3(hojas=7)), cfg)
        reg = Registro.cargar(cfg.ruta_registro)
        assert reg.buscar_documento("SESENA", 101)["revisiones"][0]["hojas"] == 7

    def test_da_de_alta_la_obra_la_primera_vez(self, pdf_a3, cfg):
        emitir(_peticion(pdf_a3(hojas=1)), cfg)
        reg = Registro.cargar(cfg.ruta_registro)
        assert reg.obras["SESENA"]["expediente"] == "A/OBR-036768/2026"

    def test_una_segunda_revision_supera_a_la_primera(self, pdf_a3, cfg):
        emitir(_peticion(pdf_a3(hojas=4)), cfg)
        em = emitir(
            _peticion(pdf_a3(hojas=5, nombre="01_PRUEBA_R00.pdf"),
                      revision="01", n_indice="03", motivo="Se amplía la zona"),
            cfg,
        )
        assert str(em.codigo) == "SESENA-101-R01"
        reg = Registro.cargar(cfg.ruta_registro)
        doc = reg.buscar_documento("SESENA", 101)
        assert {r["rev"]: r["estado"] for r in doc["revisiones"]} == {
            "00": "superado", "01": "vigente",
        }

    def test_repetir_una_revision_no_deja_rastro(self, pdf_a3, cfg):
        """Ni en el registro ni en la carpeta de salida."""
        emitir(_peticion(pdf_a3(hojas=1)), cfg)
        antes = cfg.ruta_registro.read_text(encoding="utf-8")
        with pytest.raises(ErrorRegistro):
            emitir(_peticion(pdf_a3(hojas=1, nombre="otro.pdf")), cfg)
        assert cfg.ruta_registro.read_text(encoding="utf-8") == antes


class TestModoPrueba:
    @pytest.fixture
    def cfg_prueba(self, cfg):
        return dataclasses.replace(cfg, url_base="")

    def test_avisa_de_que_es_una_prueba(self, pdf_a3, cfg_prueba):
        em = emitir(_peticion(pdf_a3(hojas=1)), cfg_prueba)
        assert em.modo_prueba
        assert any("MODO PRUEBA" in a for a in em.avisos)

    def test_estampa_la_marca_en_el_papel(self, pdf_a3, cfg_prueba):
        """Un plano de ensayo no puede confundirse con uno válido."""
        em = emitir(_peticion(pdf_a3(hojas=1)), cfg_prueba)
        texto = (PdfReader(em.pdf).pages[0].extract_text() or "").replace("\n", "")
        assert "PRUEBA" in texto

    def test_no_toca_el_registro(self, pdf_a3, cfg_prueba):
        emitir(_peticion(pdf_a3(hojas=1)), cfg_prueba)
        assert not cfg_prueba.ruta_registro.exists()

    def test_el_qr_no_apunta_a_ninguna_pagina_real(self, pdf_a3, cfg_prueba):
        em = emitir(_peticion(pdf_a3(hojas=1)), cfg_prueba)
        assert em.url.startswith("prueba:")

    def test_forzar_prueba_conserva_la_direccion_real(self, pdf_a3, cfg):
        """El ensayo de impresión necesita la dirección real: su longitud es la
        que determina la densidad del QR y si el móvil puede leerlo."""
        cfg = dataclasses.replace(cfg, forzar_prueba=True)
        em = emitir(_peticion(pdf_a3(hojas=1)), cfg)
        assert em.modo_prueba
        assert em.url.startswith("https://")          # dirección real, no «prueba:»
        assert not cfg.ruta_registro.exists()         # pero el registro intacto
        texto = (PdfReader(em.pdf).pages[0].extract_text() or "").replace("\n", "")
        assert "PRUEBA" in texto                      # y el papel marcado


class TestDatosDeLaObra:
    """Una obra nueva no puede quedar registrada sin nombre: en la web pública
    aparecería su código interno («SESENA») y el encargado no la reconocería."""

    def test_el_nombre_de_la_obra_llega_al_registro(self, pdf_a3, cfg):
        emitir(_peticion(pdf_a3(hojas=1)), cfg)
        reg = Registro.cargar(cfg.ruta_registro)
        assert reg.obras["SESENA"]["nombre"] == "Emergencia Seseña"

    def test_sin_nombre_se_registra_el_codigo_y_hay_que_evitarlo(self, pdf_a3, cfg):
        """Comportamiento del motor cuando no se le dan datos de obra.
        La interfaz debe impedir llegar aquí; ver `_datos_obra` en cli.py."""
        p = _peticion(pdf_a3(hojas=1))
        p.nombre_obra = ""
        emitir(p, cfg)
        reg = Registro.cargar(cfg.ruta_registro)
        assert reg.obras["SESENA"]["nombre"] == "SESENA"
