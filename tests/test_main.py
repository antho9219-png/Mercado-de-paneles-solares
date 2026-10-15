"""Pruebas del pipeline común expuesto por main.py."""

from main import build_parser, process_raw_records


class TestProcessRawRecords:
    def test_limpia_y_deduplica(self):
        raw = [
            {"ad_id": "1", "title": "Panel solar 550W", "price_raw": "250 USD", "url": "https://x/1"},
            {"ad_id": "1", "title": "Panel solar 550W (dup)", "url": "https://x/1"},
            {"ad_id": "2", "title": "Inversor 5kW", "price_raw": "800 USD", "url": "https://x/2"},
        ]
        result = process_raw_records(raw)
        assert len(result) == 2
        assert result[0]["product_type"] == "panel solar"
        assert result[1]["product_type"] == "inversor solar"

    def test_sella_fecha_recopilacion(self):
        raw = [{"ad_id": "1", "title": "Panel", "url": "https://x/1"}]
        result = process_raw_records(raw)
        assert result[0]["collected_at"]

    def test_respeta_fecha_existente(self):
        raw = [
            {
                "ad_id": "1", "title": "Panel", "url": "https://x/1",
                "collected_at": "2020-01-01T00:00:00+00:00",
            }
        ]
        result = process_raw_records(raw)
        assert result[0]["collected_at"] == "2020-01-01T00:00:00+00:00"


class TestCli:
    def test_subcomandos(self):
        parser = build_parser()
        args = parser.parse_args(["import", "--input", "a.csv"])
        assert args.command == "import"
        assert args.input == ["a.csv"]

    def test_scrape_sin_terminos(self):
        args = build_parser().parse_args(["scrape"])
        assert args.terms is None

    def test_input_repetido_acumula(self):
        args = build_parser().parse_args(
            ["import", "--input", "a.csv", "--input", "b.json"]
        )
        assert args.input == ["a.csv", "b.json"]

    def test_input_multiple_en_un_flag(self):
        args = build_parser().parse_args(["import", "--input", "a.csv", "b.json"])
        assert args.input == ["a.csv", "b.json"]
