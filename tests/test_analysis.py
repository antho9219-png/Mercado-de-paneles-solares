"""Pruebas de análisis: duplicados, incompletos y estadísticas."""

from analysis import (
    count_by,
    deduplicate,
    descriptive_statistics,
    find_duplicates,
    incompleteness_report,
    only_panels,
    summarize,
)
from storage import records_to_dataframe


def _records():
    return [
        {
            "ad_id": "1", "title": "Panel solar 550W", "price_raw": "250 USD",
            "price_value": 250.0, "currency": "USD", "power_w": 550.0,
            "product_type": "panel solar", "location": "Centro Habana, La Habana",
            "url": "https://x/1",
        },
        {
            "ad_id": "1", "title": "Panel solar 550W (dup)", "price_raw": "250 USD",
            "price_value": 250.0, "currency": "USD", "power_w": 550.0,
            "product_type": "panel solar", "location": "Centro Habana, La Habana",
            "url": "https://x/1",
        },
        {
            "ad_id": "2", "title": "Inversor 5kW", "price_raw": "800 USD",
            "price_value": 800.0, "currency": "USD", "power_w": 5000.0,
            "product_type": "inversor solar", "location": "Playa, La Habana",
            "url": "https://x/2",
        },
        {
            "ad_id": "3", "title": "Panel solar 450W", "price_raw": "15000 CUP",
            "price_value": 15000.0, "currency": "CUP", "power_w": 450.0,
            "product_type": "panel solar", "location": "Santa Clara, Villa Clara",
            "url": "https://x/3",
        },
        {
            "ad_id": "4", "title": "Panel sin url", "price_raw": "200 USD",
            "price_value": 200.0, "currency": "USD", "power_w": None,
            "product_type": "panel solar", "location": None, "url": None,
        },
    ]


class TestDeduplication:
    def test_deduplica_por_url(self):
        unique = deduplicate(_records())
        assert len(unique) == 4

    def test_encuentra_duplicados(self):
        assert len(find_duplicates(_records())) == 1

    def test_conserva_primera_aparicion(self):
        unique = deduplicate(_records())
        assert unique[0]["title"] == "Panel solar 550W"

    def test_sin_clave_no_se_elimina(self):
        records = [{"ad_id": None, "url": None}, {"ad_id": None, "url": None}]
        assert len(deduplicate(records)) == 2


class TestIncomplete:
    def test_detecta_el_incompleto(self):
        report = incompleteness_report(_records())
        faltantes = dict(zip(report["campo"], report["faltantes"]))
        assert faltantes["url"] == 1
        assert faltantes["ad_id"] == 0

    def test_porcentaje(self):
        report = incompleteness_report(_records())
        row = report[report["campo"] == "url"].iloc[0]
        assert row["porcentaje"] == 20.0


class TestStatistics:
    def test_agrupa_por_moneda(self):
        stats = descriptive_statistics(_records())
        monedas = set(stats["moneda"])
        assert monedas == {"USD", "CUP"}

    def test_cuenta_usd(self):
        stats = descriptive_statistics(_records())
        usd = stats[stats["moneda"] == "USD"].iloc[0]
        assert usd["n"] == 4
        assert usd["min"] == 200.0
        assert usd["max"] == 800.0

    def test_sin_conversion(self):
        # CUP y USD se mantienen separados
        stats = descriptive_statistics(_records())
        assert len(stats) == 2


class TestCounts:
    def test_conteo_por_tipo(self):
        counts = count_by(_records(), "product_type")
        valores = dict(zip(counts["product_type"], counts["cantidad"]))
        assert valores["panel solar"] == 4
        assert valores["inversor solar"] == 1

    def test_top(self):
        counts = count_by(_records(), "location", top=1)
        assert len(counts) == 1

    def test_columna_inexistente(self):
        counts = count_by(_records(), "no_existe")
        assert counts.empty


class TestPanels:
    def test_solo_paneles(self):
        frame = records_to_dataframe(_records())
        panels = only_panels(frame)
        assert len(panels) == 4
        assert set(panels["product_type"]) == {"panel solar"}


class TestSummarize:
    def test_resumen(self):
        summary = summarize(_records())
        assert summary["total"] == 5
        assert summary["paneles"] == 4
        assert summary["otros_equipos"] == 1
        assert summary["incompletos"] == 1
