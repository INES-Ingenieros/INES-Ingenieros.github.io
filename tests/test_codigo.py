"""Composición y lectura de identificadores. Ver decisiones D-07 y D-08."""

from __future__ import annotations

import pytest

from control_planos.codigo import (
    CodigoInvalido,
    componer,
    normalizar_obra,
    normalizar_revision,
    partir,
    url,
)


class TestComponer:
    def test_forma_del_codigo(self):
        c = componer("SESENA", 101, 0)
        assert str(c) == "SESENA-101-R00"
        assert c.documento == "SESENA-101"
        assert c.revision == "00"

    def test_correlativo_a_tres_cifras(self):
        assert str(componer("X1", 7, 0)) == "X1-007-R00"
        assert str(componer("X1", 1234, 0)) == "X1-1234-R00"

    @pytest.mark.parametrize("obra", ["", "s", "SESEÑA", "ses ena", "sesena-01", "A" * 13])
    def test_rechaza_obras_no_validas(self, obra):
        with pytest.raises(CodigoInvalido):
            componer(obra, 101, 0)

    def test_acepta_obra_en_minusculas_y_la_normaliza(self):
        assert componer("sesena", 101, 0).obra == "SESENA"


class TestRevision:
    @pytest.mark.parametrize(
        "entrada,esperado",
        [(0, "00"), ("0", "00"), ("3", "03"), ("R7", "07"), ("r12", "12"), (12, "12")],
    )
    def test_normaliza_a_dos_cifras(self, entrada, esperado):
        assert normalizar_revision(entrada) == esperado

    @pytest.mark.parametrize("mala", ["", "abc", "-1", "1000"])
    def test_rechaza_revisiones_imposibles(self, mala):
        with pytest.raises(CodigoInvalido):
            normalizar_revision(mala)


class TestPartir:
    def test_lee_el_codigo_del_qr(self):
        c = partir("SESENA-101-R00")
        assert (c.obra, c.correlativo, c.revision) == ("SESENA", 101, "00")

    def test_tolera_lo_que_teclea_una_persona(self):
        """Este formato lo escribe alguien que lo ha oído por teléfono."""
        for texto in ["  sesena-101-r00 ", "SESENA-101-R0", "Sesena-101-R00"]:
            assert partir(texto).documento == "SESENA-101"

    @pytest.mark.parametrize(
        "mal", ["", "SESENA", "SESENA-101", "SESENA-101-00", "8f3a7c2e-1234"]
    )
    def test_rechaza_lo_que_no_es_un_codigo(self, mal):
        with pytest.raises(CodigoInvalido):
            partir(mal)

    def test_ida_y_vuelta(self):
        original = componer("SESENA", 101, 5)
        assert partir(str(original)) == original


class TestUrl:
    def test_compone_la_direccion(self):
        c = componer("SESENA", 101, 0)
        assert url("https://x.test/planos", c) == "https://x.test/planos/?p=SESENA-101-R00"

    def test_ignora_la_barra_final_de_la_base(self):
        c = componer("SESENA", 101, 0)
        assert url("https://x.test/planos/", c) == url("https://x.test/planos", c)

    def test_sin_base_devuelve_una_direccion_no_navegable(self):
        """En modo prueba el QR no debe poder llevar a ninguna página real."""
        d = url("", componer("SESENA", 101, 0))
        assert d.startswith("prueba:")
        assert "http" not in d


class TestNormalizarObra:
    def test_quita_tildes_y_enes(self):
        assert normalizar_obra("Seseña") == "SESENA"
        assert normalizar_obra("Alcázar") == "ALCAZAR"

    def test_rechaza_lo_que_queda_vacio(self):
        with pytest.raises(CodigoInvalido):
            normalizar_obra("---")
