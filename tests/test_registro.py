"""El registro de revisiones. Ver decisiones D-06, D-08 y D-10."""

from __future__ import annotations

import json

import pytest

from control_planos.registro import ErrorRegistro, Registro


@pytest.fixture
def reg(tmp_path):
    return Registro.cargar(tmp_path / "planos.json", correlativo_inicial=101)


def _alta(reg, **kw):
    base = dict(
        obra="SESENA",
        denominacion="PLANOS SEÑALIZACIÓN PROVISIONAL",
        revision="00",
        fecha="2026-09-02",
        n_indice="01",
        hojas=4,
    )
    return reg.registrar_revision(**{**base, **kw})


class TestCorrelativo:
    def test_arranca_en_101(self, reg):
        """No en 001, para que no se confunda con el «Nº» del cajetín (D-08)."""
        assert str(_alta(reg)) == "SESENA-101-R00"

    def test_avanza_con_cada_documento_nuevo(self, reg):
        _alta(reg, denominacion="UNO")
        _alta(reg, denominacion="DOS")
        assert reg.buscar_por_denominacion("SESENA", "DOS")["id"] == "SESENA-102"

    def test_se_reutiliza_al_revisar_el_mismo_documento(self, reg):
        c0 = _alta(reg)
        c1 = _alta(reg, revision="01")
        assert c0.documento == c1.documento == "SESENA-101"

    def test_no_reutiliza_un_numero_ya_usado(self, reg):
        """Un QR antiguo apuntaría a otro documento. Es el fallo más grave."""
        _alta(reg, denominacion="UNO")
        with pytest.raises(ErrorRegistro, match="ya está usado"):
            _alta(reg, denominacion="OTRA", correlativo=101)

    def test_es_independiente_por_obra(self, reg):
        _alta(reg, obra="SESENA")
        c = _alta(reg, obra="JARAMA")
        assert c.documento == "JARAMA-101"

    def test_la_denominacion_se_compara_sin_importar_mayusculas_ni_espacios(self, reg):
        _alta(reg, denominacion="PLANTAS  DE ESTRUCTURA")
        c = _alta(reg, denominacion="plantas de estructura", revision="01")
        assert c.documento == "SESENA-101"


class TestVigencia:
    def test_la_primera_revision_queda_vigente(self, reg):
        _alta(reg)
        doc = reg.buscar_documento("SESENA", 101)
        assert doc["vigente"] == "00"
        assert doc["revisiones"][0]["estado"] == "vigente"

    def test_una_revision_nueva_supera_a_la_anterior(self, reg):
        _alta(reg)
        _alta(reg, revision="01", n_indice="03", hojas=5, motivo="Se amplía la zona")
        doc = reg.buscar_documento("SESENA", 101)
        assert doc["vigente"] == "01"
        estados = {r["rev"]: r["estado"] for r in doc["revisiones"]}
        assert estados == {"00": "superado", "01": "vigente"}

    def test_solo_hay_una_vigente_por_documento(self, reg):
        for r in ("00", "01", "02"):
            _alta(reg, revision=r)
        doc = reg.buscar_documento("SESENA", 101)
        assert sum(1 for x in doc["revisiones"] if x["estado"] == "vigente") == 1

    def test_no_se_puede_repetir_una_revision(self, reg):
        """Su QR puede estar ya impreso y circulando por la obra."""
        _alta(reg)
        with pytest.raises(ErrorRegistro, match="ya está registrada"):
            _alta(reg, revision="00")


class TestDatosPorRevision:
    def test_el_numero_de_indice_se_guarda_en_cada_revision(self, reg):
        """Así la pantalla nunca contradice al papel que se escanea (D-10)."""
        _alta(reg, revision="00", n_indice="01")
        _alta(reg, revision="01", n_indice="03")
        revs = {r["rev"]: r["n_indice"] for r in
                reg.buscar_documento("SESENA", 101)["revisiones"]}
        assert revs == {"00": "01", "01": "03"}

    def test_las_hojas_tambien_van_por_revision(self, reg):
        _alta(reg, revision="00", hojas=4)
        _alta(reg, revision="01", hojas=5)
        revs = {r["rev"]: r["hojas"] for r in
                reg.buscar_documento("SESENA", 101)["revisiones"]}
        assert revs == {"00": 4, "01": 5}

    def test_la_primera_emision_lleva_motivo_por_defecto(self, reg):
        _alta(reg)
        assert reg.buscar_documento("SESENA", 101)["revisiones"][0]["motivo"] == (
            "Primera emisión"
        )


class TestPersistencia:
    def test_guarda_y_recarga(self, tmp_path):
        ruta = tmp_path / "planos.json"
        r1 = Registro.cargar(ruta)
        _alta(r1)
        r1.guardar()
        r2 = Registro.cargar(ruta)
        assert r2.buscar_documento("SESENA", 101)["vigente"] == "00"

    def test_escribe_json_valido_y_con_acentos_legibles(self, tmp_path):
        ruta = tmp_path / "planos.json"
        r = Registro.cargar(ruta)
        _alta(r)
        r.guardar()
        texto = ruta.read_text(encoding="utf-8")
        assert "SEÑALIZACIÓN" in texto        # sin escapar a Ñ
        assert json.loads(texto)["obras"]["SESENA"]

    def test_deja_copia_de_seguridad(self, tmp_path):
        ruta = tmp_path / "planos.json"
        r = Registro.cargar(ruta)
        _alta(r)
        r.guardar()
        _alta(r, revision="01")
        r.guardar()
        assert ruta.with_suffix(".json.bak").exists()

    def test_anota_la_fecha_de_actualizacion(self, tmp_path):
        r = Registro.cargar(tmp_path / "planos.json")
        _alta(r)
        r.guardar()
        assert r.datos["actualizado"].startswith("20")


class TestIntegridad:
    def test_detecta_un_vigente_que_no_existe(self, reg):
        _alta(reg)
        reg.buscar_documento("SESENA", 101)["vigente"] = "09"
        with pytest.raises(ErrorRegistro, match="declara vigente"):
            reg.verificar()

    def test_detecta_dos_vigentes(self, reg):
        _alta(reg)
        _alta(reg, revision="01")
        reg.buscar_documento("SESENA", 101)["revisiones"][0]["estado"] = "vigente"
        with pytest.raises(ErrorRegistro, match="marcadas como"):
            reg.verificar()

    def test_detecta_un_documento_en_la_obra_equivocada(self, reg):
        _alta(reg)
        reg.buscar_documento("SESENA", 101)["id"] = "JARAMA-101"
        with pytest.raises(ErrorRegistro, match="no pertenece"):
            reg.verificar()

    def test_no_guarda_un_registro_incoherente(self, tmp_path):
        """La web pública consume este fichero: no puede quedar roto."""
        ruta = tmp_path / "planos.json"
        r = Registro.cargar(ruta)
        _alta(r)
        r.buscar_documento("SESENA", 101)["revisiones"] = []
        with pytest.raises(ErrorRegistro):
            r.guardar()
        assert not ruta.exists()
