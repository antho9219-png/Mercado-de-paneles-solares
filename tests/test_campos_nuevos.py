"""Pruebas de los campos nuevos: vida útil, garantía, modelo y alcance."""

from cleaner import (
    clean_record,
    detect_alcance,
    detect_model,
    parse_garantia,
    parse_vida_util,
)


class TestVidaUtil:
    def test_forma_directa(self):
        assert parse_vida_util("vida útil de 25 años") == ("25 años", 25.0)

    def test_forma_inversa(self):
        assert parse_vida_util("25 años de vida util") == ("25 años", 25.0)

    def test_no_confunde_con_garantia(self):
        # "garantía" sin "vida útil" no debe producir vida útil.
        assert parse_vida_util("garantía de 10 años") == (None, None)

    def test_sin_dato(self):
        assert parse_vida_util("panel solar 550W") == (None, None)


class TestGarantia:
    def test_anios(self):
        assert parse_garantia("garantía de 5 años") == "5 años"

    def test_meses(self):
        assert parse_garantia("garantía: 12 meses") == "12 meses"

    def test_por_vida(self):
        assert parse_garantia("garantía por vida") == "por vida"

    def test_sin_garantia(self):
        assert parse_garantia("panel solar, vida útil de 25 años") is None


class TestModelo:
    def test_modelo_con_digitos(self):
        assert detect_model("Inversor Growatt SPF5000ES") == "SPF5000ES"

    def test_modelo_con_guion(self):
        assert detect_model("Kit MUST PV18-5K") == "PV18-5K"

    def test_potencia_no_es_modelo(self):
        assert detect_model("Panel Jinko 550W") is None

    def test_sin_marca(self):
        assert detect_model("Panel solar 550W") is None


class TestAlcance:
    def test_kit(self):
        assert detect_alcance("Kit solar de 3 kW", "kit solar") == "sistema completo"

    def test_varios_paneles(self):
        assert detect_alcance("Juego de 4 paneles solares", "panel solar") == "varios paneles"

    def test_panel_individual(self):
        assert detect_alcance("Panel solar 550W", "panel solar") == "panel individual"

    def test_no_determinado(self):
        assert detect_alcance("Cable rojo", "otro") == "no determinado"


class TestCleanRecordMunicipio:
    def test_normaliza_municipio(self):
        result = clean_record(
            {"ad_id": "1", "title": "Panel solar", "province": "La Habana",
             "municipality": "la habana vieja"}
        )
        assert result["municipality"] == "Habana Vieja"
        assert result["ubicacion_original"] == "la habana vieja, La Habana"

    def test_provincia_no_asigna_municipio(self):
        result = clean_record(
            {"ad_id": "1", "title": "Panel solar", "province": "La Habana",
             "municipality": "La Habana"}
        )
        assert result["municipality"] is None

    def test_deriva_campos_tecnicos(self):
        result = clean_record(
            {
                "ad_id": "1",
                "title": "Panel solar 550W Jinko",
                "description": "Nuevo, vida útil de 25 años y garantía de 10 años.",
                "province": "La Habana",
                "municipality": "Playa",
            }
        )
        assert result["vida_util"] == "25 años"
        assert result["vida_util_anios"] == 25.0
        assert result["garantia"] == "10 años"
        assert result["alcance"] == "panel individual"
        assert result["municipality"] == "Playa"
