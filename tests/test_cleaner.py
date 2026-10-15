"""Pruebas de la limpieza y normalización de campos."""

from cleaner import (
    classify_product,
    clean_record,
    detect_brand,
    extract_currency,
    missing_fields,
    parse_power_watts,
    parse_price,
)


class TestParsePrice:
    def test_coma_miles(self):
        assert parse_price("6,000 USD") == (6000.0, "USD")

    def test_punto_miles(self):
        assert parse_price("2.500 CUP") == (2500.0, "CUP")

    def test_decimal_coma(self):
        assert parse_price("0,45") == (0.45, None)

    def test_decimal_punto(self):
        assert parse_price("0.45") == (0.45, None)

    def test_mixto(self):
        assert parse_price("1,234.56 USD") == (1234.56, "USD")

    def test_numero_directo(self):
        assert parse_price(6000) == (6000.0, None)

    def test_sin_precio(self):
        assert parse_price("precio a convenir") == (None, None)

    def test_none(self):
        assert parse_price(None) == (None, None)


class TestCurrency:
    def test_codigo(self):
        assert extract_currency("100 EUR") == "EUR"

    def test_simbolo_ambiguo(self):
        assert extract_currency("$100") is None

    def test_simbolo_euro(self):
        assert extract_currency("100 €") == "EUR"

    def test_sin_moneda(self):
        assert extract_currency("5000") is None


class TestPower:
    def test_watios(self):
        assert parse_power_watts("Panel 450 W")[0] == 450.0

    def test_kilovatios(self):
        assert parse_power_watts("inversor 12 kW")[0] == 12000.0

    def test_kw_decimal(self):
        assert parse_power_watts("panel de 0.45 kW")[0] == 450.0

    def test_kwh_no_es_potencia(self):
        assert parse_power_watts("batería 15 kWh") == (None, None)

    def test_sin_potencia(self):
        assert parse_power_watts("panel solar usado") == (None, None)


class TestBrandAndProduct:
    def test_marca(self):
        assert detect_brand("Panel Jinko 550W") == "Jinko"

    def test_marca_desconocida(self):
        assert detect_brand("Panel marca Foo") is None

    def test_clasifica_panel(self):
        assert classify_product("Panel solar 550W") == "panel solar"

    def test_clasifica_kit(self):
        assert classify_product("Kit solar de 3 kW") == "kit solar"

    def test_clasifica_inversor(self):
        assert classify_product("Inversor Growatt 5kW") == "inversor solar"

    def test_clasifica_bateria(self):
        assert classify_product("Batería Pylontech") == "bateria solar"

    def test_clasifica_otro(self):
        assert classify_product("Cable rojo") == "otro"

    def test_clasifica_vacio(self):
        assert classify_product(None) == "otro"


class TestCleanRecord:
    def test_deriva_campos(self):
        raw = {
            "ad_id": 123,
            "title": "Panel solar 550W Jinko",
            "description": "Monocristalino 550 W",
            "price_raw": "6,000 USD",
            "province": "La Habana",
            "municipality": "Centro Habana",
            "source": "import",
        }
        result = clean_record(raw)
        assert result["ad_id"] == "123"
        assert result["price_value"] == 6000.0
        assert result["currency"] == "USD"
        assert result["power_w"] == 550.0
        assert result["brand"] == "Jinko"
        assert result["product_type"] == "panel solar"
        assert result["location"] == "Centro Habana, La Habana"

    def test_no_inventa_valores(self):
        raw = {"ad_id": "1", "title": "Panel solar", "url": "http://x"}
        result = clean_record(raw)
        assert result["price_value"] is None
        assert result["currency"] is None
        assert result["power_w"] is None
        assert result["brand"] is None


class TestMissingFields:
    def test_detecta_faltantes(self):
        record = {"ad_id": "1", "title": None, "url": "http://x"}
        assert missing_fields(record) == ["title"]

    def test_registro_completo(self):
        record = {"ad_id": "1", "title": "Panel", "url": "http://x"}
        assert missing_fields(record) == []
