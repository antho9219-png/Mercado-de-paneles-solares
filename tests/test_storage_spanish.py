"""Pruebas de exportación en español (data/raw y data/processed)."""

from storage import (
    SPANISH_COLUMNS,
    load_csv,
    records_to_spanish_dataframe,
    save_csv_spanish,
)


def _sample():
    return [
        {
            "ad_id": "1",
            "title": "Panel solar 550W",
            "description": "Nuevo",
            "price_raw": "250 USD",
            "price_value": 250.0,
            "currency": "USD",
            "power_raw": "550 W",
            "power_w": 550.0,
            "brand": "Jinko",
            "modelo": None,
            "product_type": "panel solar",
            "alcance": "panel individual",
            "vida_util": "25 años",
            "vida_util_anios": 25.0,
            "garantia": "10 años",
            "location": "Playa, La Habana",
            "ubicacion_original": "Playa, La Habana",
            "province": "La Habana",
            "municipality": "Playa",
            "category": "Energía",
            "date_published": "2026-01-15T10:00:00+00:00",
            "url": "https://x/1",
            "collected_at": "2026-03-01T00:00:00+00:00",
            "source": "import",
        }
    ]


class TestSpanishColumns:
    def test_encabezado_espanol(self, tmp_path):
        path = tmp_path / "proc.csv"
        save_csv_spanish(_sample(), path)
        header = path.read_text(encoding="utf-8-sig").splitlines()[0]
        assert header.split(",") == list(SPANISH_COLUMNS.values())
        assert "titulo" in header and "municipio" in header and "precio" in header

    def test_roundtrip(self, tmp_path):
        path = tmp_path / "proc.csv"
        save_csv_spanish(_sample(), path)
        loaded = load_csv(path)
        assert loaded[0]["ad_id"] == "1"
        assert loaded[0]["title"] == "Panel solar 550W"
        assert loaded[0]["municipality"] == "Playa"
        assert loaded[0]["garantia"] == "10 años"

    def test_dataframe_vacio(self):
        frame = records_to_spanish_dataframe([])
        assert list(frame.columns) == list(SPANISH_COLUMNS.values())
        assert frame.empty
