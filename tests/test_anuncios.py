"""Pruebas del registro de anuncios reales (plantilla + validación + dedup)."""

from pathlib import Path

import pandas as pd
import pytest

from anuncios import (
    COLUMNAS_ANUNCIOS,
    is_verifiable_source,
    merge_anuncios,
    read_rows,
    row_to_record,
    save_template,
)
from config import Config
from main import build_parser, cmd_registrar, cmd_template
from storage import SPANISH_COLUMNS


def _args(argv):
    return build_parser().parse_args(argv)


def _cfg(tmp_path):
    return Config(
        data_dir=tmp_path / "data",
        out_dir=tmp_path / "out",
        log_dir=tmp_path / "logs",
    )


def _escribir_plantilla(tmp_path, filas, nombre="anuncios.csv"):
    path = tmp_path / nombre
    pd.DataFrame(filas, columns=list(COLUMNAS_ANUNCIOS)).to_csv(
        path, index=False, encoding="utf-8-sig"
    )
    return path


class TestColumnas:
    def test_columnas_exactas_y_orden(self):
        assert COLUMNAS_ANUNCIOS == (
            "fecha_consulta",
            "precio",
            "moneda",
            "potencia_w",
            "marca",
            "modelo",
            "vida_util",
            "garantia",
            "municipio",
            "url_fuente",
            "observaciones",
        )


class TestPlantilla:
    def test_save_template_solo_cabecera(self, tmp_path):
        path = save_template(tmp_path / "sub" / "plantilla.csv")
        assert path.exists()
        header = path.read_text(encoding="utf-8-sig").splitlines()
        assert header == [",".join(COLUMNAS_ANUNCIOS)]

    def test_comando_template_anuncios(self, tmp_path, capsys):
        salida = tmp_path / "plantilla_anuncios_reales.csv"
        code = cmd_template(
            _args(["template", "--anuncios", "--output", str(salida)]), _cfg(tmp_path)
        )
        assert code == 0
        assert salida.exists()
        header = salida.read_text(encoding="utf-8-sig").splitlines()[0]
        assert header.split(",") == list(COLUMNAS_ANUNCIOS)
        assert "registrar" in capsys.readouterr().out

    def test_template_sin_flag_sigue_siendo_el_de_entrega(self, tmp_path):
        salida = tmp_path / "plantilla.csv"
        code = cmd_template(_args(["template", "--output", str(salida)]), _cfg(tmp_path))
        assert code == 0
        header = salida.read_text(encoding="utf-8-sig").splitlines()[0]
        assert header.split(",") == list(SPANISH_COLUMNS.values())


class TestReadRows:
    def test_lee_valores_y_omite_filas_vacias(self, tmp_path):
        path = _escribir_plantilla(
            tmp_path,
            [
                {
                    "fecha_consulta": "2026-03-01",
                    "precio": "250",
                    "moneda": "USD",
                    "potencia_w": "550",
                    "marca": "Jinko",
                    "modelo": "",
                    "vida_util": "",
                    "garantia": "10 años",
                    "municipio": "Playa",
                    "url_fuente": "https://revolico.com/anuncio/1",
                    "observaciones": "Panel solar nuevo",
                },
                {c: "" for c in COLUMNAS_ANUNCIOS},  # fila vacía: se ignora
            ],
        )
        filas = read_rows(path)
        assert len(filas) == 1
        assert filas[0]["marca"] == "Jinko"
        assert filas[0]["modelo"] == ""

    def test_falta_columna_url_fuente(self, tmp_path):
        path = tmp_path / "sin_url.csv"
        pd.DataFrame({"precio": ["250"]}).to_csv(path, index=False, encoding="utf-8-sig")
        with pytest.raises(ValueError):
            read_rows(path)

    def test_archivo_inexistente(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_rows(tmp_path / "no_existe.csv")


class TestFuenteVerificable:
    @pytest.mark.parametrize(
        "valor",
        [
            "https://www.revolico.com/anuncio/123",
            "http://revolico.com/x",
            "revolico.com",
            "www.revolico.com/anuncio/1",
        ],
    )
    def test_acepta_urls(self, valor):
        assert is_verifiable_source(valor) is True

    @pytest.mark.parametrize(
        "valor",
        ["", None, "   ", "pendiente", "no lo sé", "sin fuente", "ejemplo/a", "a@b.com"],
    )
    def test_rechaza_no_urls(self, valor):
        assert is_verifiable_source(valor) is False


class TestRowToRecord:
    def test_mapea_y_no_inventa(self):
        record = row_to_record(
            {
                "fecha_consulta": "2026-03-01",
                "precio": "250",
                "moneda": "usd",
                "potencia_w": "550 W",
                "marca": "Jinko",
                "municipio": "Playa",
                "url_fuente": "https://revolico.com/a/1",
                "observaciones": "panel nuevo",
            }
        )
        assert record["collected_at"] == "2026-03-01"
        assert record["price_raw"] == "250"
        assert record["currency"] == "USD"
        assert record["brand"] == "Jinko"
        assert record["municipality"] == "Playa"
        assert record["province"] == "La Habana"
        assert record["url"] == "https://revolico.com/a/1"
        assert record["notes"] == "panel nuevo"
        assert record["source"] == "registro_manual"
        # Campos no aportados: vacíos (no se inventan).
        assert record["modelo"] is None
        assert record["vida_util"] is None
        assert record["garantia"] is None

    def test_observaciones_se_usan_para_clasificar(self):
        from cleaner import clean_record

        record = row_to_record(
            {"observaciones": "Vendo panel solar 550W", "url_fuente": "revolico.com/x"}
        )
        limpio = clean_record(record)
        assert limpio["product_type"] == "panel solar"
        assert limpio["notes"] == "Vendo panel solar 550W"


class TestMerge:
    def test_deduplica_por_url(self):
        existentes = [{"url": "https://a.com/1", "price_raw": "100"}]
        nuevos = [
            {"url": "https://a.com/1", "price_raw": "999"},  # duplicado
            {"url": "https://a.com/2", "price_raw": "200"},
        ]
        combinados, duplicados = merge_anuncios(existentes, nuevos)
        assert len(combinados) == 2
        assert len(duplicados) == 1
        assert duplicados[0]["price_raw"] == "999"

    def test_duplicados_dentro_del_propio_archivo(self):
        nuevos = [
            {"url": "https://a.com/1"},
            {"url": "https://a.com/1/", "price_raw": "200"},  # misma URL normalizada
        ]
        combinados, duplicados = merge_anuncios([], nuevos)
        assert len(combinados) == 1
        assert len(duplicados) == 1


class TestComandoRegistrar:
    def test_sin_fuente_no_registra(self, tmp_path):
        cfg = _cfg(tmp_path)
        path = _escribir_plantilla(
            tmp_path, [{"precio": "250", "marca": "Jinko", "url_fuente": ""}]
        )
        code = cmd_registrar(_args(["registrar", "--input", str(path)]), cfg)
        assert code == 3
        assert not cfg.raw_csv_path.exists()

    def test_registra_con_fuente(self, tmp_path):
        cfg = _cfg(tmp_path)
        path = _escribir_plantilla(
            tmp_path,
            [
                {
                    "precio": "250",
                    "moneda": "USD",
                    "potencia_w": "550 W",
                    "marca": "Jinko",
                    "municipio": "Playa",
                    "url_fuente": "https://revolico.com/a/1",
                    "observaciones": "panel solar nuevo",
                }
            ],
        )
        code = cmd_registrar(_args(["registrar", "--input", str(path)]), cfg)
        assert code == 0
        assert cfg.raw_csv_path.exists()
        assert cfg.processed_csv_path.exists()

        from storage import load_csv

        registro = load_csv(cfg.processed_csv_path)[0]
        assert registro["source"] == "registro_manual"
        assert registro["brand"] == "Jinko"
        assert float(registro["power_w"]) == 550.0
        assert registro["notes"] == "panel solar nuevo"
        assert registro["url"] == "https://revolico.com/a/1"

    def test_columnas_observaciones_en_entrega(self, tmp_path):
        cfg = _cfg(tmp_path)
        path = _escribir_plantilla(
            tmp_path, [{"url_fuente": "revolico.com/a/1", "observaciones": "nota"}]
        )
        cmd_registrar(_args(["registrar", "--input", str(path)]), cfg)
        header = cfg.processed_csv_path.read_text(encoding="utf-8-sig").splitlines()[0]
        assert "observaciones" in header.split(",")

    def test_no_duplica_entre_ejecuciones(self, tmp_path, capsys):
        cfg = _cfg(tmp_path)
        path = _escribir_plantilla(
            tmp_path, [{"precio": "250", "url_fuente": "https://revolico.com/a/1"}]
        )
        assert cmd_registrar(_args(["registrar", "--input", str(path)]), cfg) == 0
        assert cmd_registrar(_args(["registrar", "--input", str(path)]), cfg) == 0

        from storage import load_csv

        assert len(load_csv(cfg.processed_csv_path)) == 1

    def test_no_toca_los_datos_abiertos(self, tmp_path):
        cfg = _cfg(tmp_path)
        cfg.opendata_csv_path.parent.mkdir(parents=True, exist_ok=True)
        cfg.opendata_csv_path.write_text("contenido-abierto", encoding="utf-8")
        path = _escribir_plantilla(
            tmp_path, [{"url_fuente": "https://revolico.com/a/1"}]
        )
        cmd_registrar(_args(["registrar", "--input", str(path)]), cfg)
        assert cfg.opendata_csv_path.read_text(encoding="utf-8") == "contenido-abierto"
        assert cfg.opendata_csv_path != cfg.raw_csv_path

    def test_mezcla_rechazadas_y_duplicadas(self, tmp_path, capsys):
        cfg = _cfg(tmp_path)
        path = _escribir_plantilla(
            tmp_path,
            [
                {"url_fuente": "revolico.com/a/1"},
                {"url_fuente": "revolico.com/a/1"},  # duplicada en el archivo
                {"url_fuente": "no lo sé"},          # rechazada
            ],
        )
        code = cmd_registrar(_args(["registrar", "--input", str(path)]), cfg)
        assert code == 0
        salida = capsys.readouterr().out
        assert "RECHAZADAS" in salida
        assert "DUPLICADAS" in salida
