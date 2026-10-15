"""Pruebas de normalización de municipios de La Habana."""

from municipios import (
    MUNICIPIOS_LA_HABANA,
    es_municipio_habana,
    normalize_municipio,
)


class TestNormalizeMunicipio:
    def test_exacto(self):
        assert normalize_municipio("Centro Habana") == "Centro Habana"

    def test_minusculas_y_acentos(self):
        assert normalize_municipio("diez de octubre") == "Diez de Octubre"
        assert normalize_municipio("SAN MIGUEL DEL PADRON") == "San Miguel del Padrón"

    def test_variantes(self):
        assert normalize_municipio("la habana vieja") == "Habana Vieja"
        assert normalize_municipio("Vedado") == "Plaza de la Revolución"
        assert normalize_municipio("Miramar") == "Playa"
        assert normalize_municipio("Guanabo") == "Habana del Este"

    def test_provincia_no_es_municipio(self):
        assert normalize_municipio("La Habana") is None
        assert normalize_municipio("ciudad de la habana") is None
        assert normalize_municipio("Cuba") is None

    def test_otra_provincia(self):
        assert normalize_municipio("Santa Clara") is None

    def test_vacio(self):
        assert normalize_municipio(None) is None
        assert normalize_municipio("") is None

    def test_coincidencia_laxa(self):
        assert normalize_municipio("reparto Centro Habana, cerca") == "Centro Habana"


class TestCatalogo:
    def test_quince_municipios(self):
        assert len(MUNICIPIOS_LA_HABANA) == 15

    def test_es_municipio(self):
        assert es_municipio_habana("Playa") is True
        assert es_municipio_habana("La Habana") is False
