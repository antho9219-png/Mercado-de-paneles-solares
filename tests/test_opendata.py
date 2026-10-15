"""Pruebas del conector de datos abiertos (Banco Mundial) y del comando ``opendata``."""

import opendata
from config import Config
from main import build_parser, cmd_opendata
from opendata import (
    COLUMNAS_OPENDATA,
    fetch_world_bank_indicator,
    load_opendata_csv,
    save_opendata_csv,
)


def _args(argv):
    return build_parser().parse_args(argv)


def _cfg(tmp_path):
    return Config(
        data_dir=tmp_path / "data",
        out_dir=tmp_path / "out",
        log_dir=tmp_path / "logs",
    )


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return _FakeResponse(self.payload)


def _payload_con_datos():
    return [
        {"page": 1, "pages": 1, "total": 2},
        [
            {
                "indicator": {"id": "EG.ELC.ACCS.ZS", "value": "Access to electricity (% of population)"},
                "country": {"id": "CU", "value": "Cuba"},
                "countryiso3code": "CUB",
                "date": "2024",
                "value": 100,
                "unit": "",
            },
            {
                "indicator": {"id": "EG.ELC.ACCS.ZS", "value": "Access to electricity (% of population)"},
                "country": {"id": "CU", "value": "Cuba"},
                "date": "2025",
                "value": None,  # sin dato -> NO se inventa
                "unit": "",
            },
        ],
    ]


class TestFetch:
    def test_parsea_y_omite_valores_ausentes(self):
        session = _FakeSession(_payload_con_datos())
        registros = fetch_world_bank_indicator("EG.ELC.ACCS.ZS", "CUB", session=session)
        assert len(registros) == 1
        registro = registros[0]
        assert registro["pais"] == "Cuba"
        assert registro["anio"] == "2024"
        assert registro["valor"] == 100
        assert registro["fuente"] == "Banco Mundial - datos abiertos"
        assert registro["licencia"] == "CC BY 4.0"
        assert registro["fecha_recopilacion"]

    def test_payload_vacio(self):
        assert fetch_world_bank_indicator("X", "CUB", session=_FakeSession([{}, []])) == []
        assert fetch_world_bank_indicator("X", "CUB", session=_FakeSession([{"message": "no"}]) ) == []

    def test_llama_a_la_url_correcta(self):
        session = _FakeSession(_payload_con_datos())
        fetch_world_bank_indicator("NY.GDP.PCAP.CD", "CUB", session=session)
        assert "country/CUB/indicator/NY.GDP.PCAP.CD" in session.calls[0]["url"]


class TestCsv:
    def test_roundtrip(self, tmp_path):
        registros = fetch_world_bank_indicator(
            "EG.ELC.ACCS.ZS", "CUB", session=_FakeSession(_payload_con_datos())
        )
        ruta = save_opendata_csv(registros, tmp_path / "abiertos.csv")
        assert ruta.exists()
        cabecera = ruta.read_text(encoding="utf-8-sig").splitlines()[0].split(",")
        assert cabecera == list(COLUMNAS_OPENDATA)
        cargados = load_opendata_csv(ruta)
        assert cargados[0]["fuente"] == "Banco Mundial - datos abiertos"
        assert cargados[0]["fecha_recopilacion"]


class TestComandoOpendata:
    def test_descarga_y_guarda(self, tmp_path, monkeypatch, capsys):
        registros = fetch_world_bank_indicator(
            "EG.ELC.ACCS.ZS", "CUB", session=_FakeSession(_payload_con_datos())
        )
        monkeypatch.setattr(opendata, "fetch_world_bank", lambda *a, **k: list(registros))
        salida = tmp_path / "out" / "abiertos.csv"
        code = cmd_opendata(_args(["opendata", "--output", str(salida)]), _cfg(tmp_path))
        assert code == 0
        assert salida.exists()
        texto = capsys.readouterr().out
        assert "NO son anuncios" in texto

    def test_error_de_red_devuelve_1(self, tmp_path, monkeypatch, capsys):
        def _boom(*_a, **_k):
            raise RuntimeError("sin red")

        monkeypatch.setattr(opendata, "fetch_world_bank", _boom)
        code = cmd_opendata(_args(["opendata"]), _cfg(tmp_path))
        assert code == 1
        assert "Error" in capsys.readouterr().err

    def test_sin_datos_no_crea_archivo(self, tmp_path, monkeypatch):
        monkeypatch.setattr(opendata, "fetch_world_bank", lambda *a, **k: [])
        salida = tmp_path / "vacio.csv"
        code = cmd_opendata(_args(["opendata", "--output", str(salida)]), _cfg(tmp_path))
        assert code == 1
        assert not salida.exists()
