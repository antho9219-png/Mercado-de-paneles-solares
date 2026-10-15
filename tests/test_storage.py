"""Pruebas de almacenamiento: exportación e importación CSV/JSON."""

import json

import pytest

from config import FIELDS
from storage import load_csv, load_json, load_records, save_csv, save_json


def _sample():
    return [
        {
            "ad_id": "1", "title": "Panel solar 550W", "description": "Nuevo",
            "price_raw": "250 USD", "price_value": 250.0, "currency": "USD",
            "power_raw": "550 W", "power_w": 550.0, "brand": "Jinko",
            "product_type": "panel solar", "location": "La Habana",
            "province": "La Habana", "municipality": "Centro Habana",
            "category": "Energía", "date_published": "2026-01-15T10:00:00+00:00",
            "url": "https://x/1", "collected_at": "2026-03-01T00:00:00+00:00",
            "source": "import",
        }
    ]


class TestRoundtrip:
    def test_csv(self, tmp_path):
        path = tmp_path / "out.csv"
        save_csv(_sample(), path)
        loaded = load_csv(path)
        assert len(loaded) == 1
        assert loaded[0]["ad_id"] == "1"
        assert loaded[0]["price_value"] == "250.0" or float(loaded[0]["price_value"]) == 250.0

    def test_json(self, tmp_path):
        path = tmp_path / "out.json"
        save_json(_sample(), path)
        loaded = load_json(path)
        assert len(loaded) == 1
        assert loaded[0]["title"] == "Panel solar 550W"
        assert loaded[0]["currency"] == "USD"

    def test_columnas_canonicas(self, tmp_path):
        path = tmp_path / "out.csv"
        save_csv(_sample(), path)
        header = path.read_text(encoding="utf-8-sig").splitlines()[0]
        assert header == ",".join(FIELDS)


class TestLoadJson:
    def test_lista_simple(self, tmp_path):
        path = tmp_path / "list.json"
        path.write_text(json.dumps([{"id": 7, "titulo": "Panel"}]), encoding="utf-8")
        loaded = load_json(path)
        assert loaded[0]["ad_id"] == "7"
        assert loaded[0]["title"] == "Panel"

    def test_clave_envolvente(self, tmp_path):
        path = tmp_path / "wrap.json"
        path.write_text(json.dumps({"records": [{"id": 8}]}), encoding="utf-8")
        loaded = load_json(path)
        assert loaded[0]["ad_id"] == "8"

    def test_alias_espanol(self, tmp_path):
        path = tmp_path / "es.json"
        payload = {"paneles": [{"id": 9, "titulo": "Panel", "precio": "100 USD", "marca": "Jinko"}]}
        path.write_text(json.dumps(payload), encoding="utf-8")
        loaded = load_json(path)
        assert loaded[0]["title"] == "Panel"
        assert loaded[0]["price_raw"] == "100 USD"
        assert loaded[0]["brand"] == "Jinko"

    def test_estructura_no_soportada(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"foo": "bar"}), encoding="utf-8")
        with pytest.raises(ValueError):
            load_json(path)


class TestDispatch:
    def test_formato_no_soportado(self, tmp_path):
        path = tmp_path / "data.txt"
        path.write_text("hola", encoding="utf-8")
        with pytest.raises(ValueError):
            load_records(path)

    def test_archivo_inexistente(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_records(tmp_path / "no.csv")
