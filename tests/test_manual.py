"""Pruebas del registro manual de anuncios (alternativa autorizada al scraping)."""

from config import Config, FIELDS
from main import build_parser, cmd_add
from manual import build_manual_record, has_data, prompt_record
from storage import SPANISH_COLUMNS, load_csv

# Campos que el usuario pidió conservar (nombres del esquema de entrega).
CAMPOS_PEDIDOS = (
    "fecha_recopilacion",
    "precio",
    "moneda",
    "potencia_w",
    "marca",
    "modelo",
    "vida_util",
    "garantia",
    "municipio",
    "tipo_producto",
    "fuente",
)

# Los mismos campos en el esquema interno.
CAMPOS_PEDIDOS_INTERNOS = (
    "collected_at",
    "price_raw",
    "currency",
    "power_w",
    "brand",
    "modelo",
    "vida_util",
    "garantia",
    "municipality",
    "product_type",
    "source",
)


def _args(argv):
    return build_parser().parse_args(argv)


def _cfg(tmp_path):
    return Config(
        data_dir=tmp_path / "data",
        out_dir=tmp_path / "out",
        log_dir=tmp_path / "logs",
    )


class TestBuildManualRecord:
    def test_no_inventa_valores(self):
        record = build_manual_record()
        # Todos los "datos del anuncio" quedan vacíos.
        for campo in CAMPOS_PEDIDOS_INTERNOS:
            if campo in ("collected_at", "source"):
                continue
            assert record[campo] is None, campo

    def test_metadatos_por_defecto(self):
        record = build_manual_record()
        assert record["source"] == "registro_manual"
        assert record["collected_at"]  # se sella la fecha de recopilación

    def test_esquema_completo(self):
        record = build_manual_record()
        assert set(FIELDS).issubset(record.keys())

    def test_campos_aportados_se_conservan(self):
        record = build_manual_record(
            title="Panel 550W",
            price_raw="250",
            currency="usd",
            power_raw="550 W",
            brand="Jinko",
            modelo="Tiger",
            product_type="panel solar",
            vida_util="25 años",
            garantia="10 años",
            municipality="Playa",
        )
        assert record["title"] == "Panel 550W"
        assert record["currency"] == "USD"  # normalizada a mayúsculas
        assert record["power_raw"] == "550 W"
        assert record["brand"] == "Jinko"
        assert record["modelo"] == "Tiger"
        assert record["product_type"] == "panel solar"
        assert record["vida_util"] == "25 años"
        assert record["garantia"] == "10 años"
        assert record["municipality"] == "Playa"

    def test_provincia_derivada_de_municipio_habana(self):
        record = build_manual_record(municipality="Playa")
        assert record["province"] == "La Habana"

    def test_provincia_no_inventada_si_municipio_desconocido(self):
        record = build_manual_record(municipality="Ciudad Desconocida")
        assert record["province"] is None

    def test_provincia_explicita_se_respeta(self):
        record = build_manual_record(municipality="Playa", provincia="Artemisa")
        assert record["province"] == "Artemisa"

    def test_ubicacion_original_conserva_texto(self):
        record = build_manual_record(municipality="playa")
        assert record["ubicacion_original"] == "playa"


class TestHasData:
    def test_vacio_no_tiene_datos(self):
        assert has_data(build_manual_record()) is False

    def test_con_algun_dato(self):
        assert has_data(build_manual_record(price_raw="250")) is True

    def test_solo_metadatos_no_cuenta(self):
        assert has_data(build_manual_record(source="x", collected_at="2020-01-01")) is False


class TestPromptRecord:
    def test_modo_interactivo(self):
        respuestas = iter(
            ["Panel 550W", "250 USD", "USD", "550 W", "Jinko", "", "25 años",
             "10 años", "Playa", "panel solar", "registro_manual", "", "", ""]
        )
        record = prompt_record(input_fn=lambda _msg: next(respuestas))
        assert record["title"] == "Panel 550W"
        assert record["brand"] == "Jinko"
        assert record["municipality"] == "Playa"

    def test_eof_no_inventa(self):
        def _raise(_msg):
            raise EOFError

        record = prompt_record(input_fn=_raise)
        assert has_data(record) is False


class TestComandoAdd:
    def test_sin_datos_devuelve_error(self, tmp_path):
        code = cmd_add(_args(["add"]), _cfg(tmp_path))
        assert code == 2

    def test_add_crea_raw_y_processed(self, tmp_path):
        cfg = _cfg(tmp_path)
        code = cmd_add(
            _args(
                [
                    "add",
                    "--precio", "250",
                    "--moneda", "USD",
                    "--potencia", "550 W",
                    "--marca", "Jinko",
                    "--modelo", "Tiger",
                    "--vida-util", "25 años",
                    "--garantia", "10 años",
                    "--municipio", "Playa",
                    "--tipo-producto", "panel solar",
                    "--fuente", "registro_manual",
                ]
            ),
            cfg,
        )
        assert code == 0
        assert cfg.raw_csv_path.exists()
        assert cfg.processed_csv_path.exists()

    def test_campos_pedidos_en_procesado(self, tmp_path):
        cfg = _cfg(tmp_path)
        cmd_add(
            _args(
                [
                    "add",
                    "--precio", "250",
                    "--moneda", "USD",
                    "--potencia", "550 W",
                    "--marca", "Jinko",
                    "--modelo", "Tiger",
                    "--vida-util", "25 años",
                    "--garantia", "10 años",
                    "--municipio", "Playa",
                    "--tipo-producto", "panel solar",
                    "--fuente", "registro_manual",
                ]
            ),
            cfg,
        )
        registro = load_csv(cfg.processed_csv_path)[0]
        assert float(registro["price_value"]) == 250.0
        assert registro["currency"] == "USD"
        assert float(registro["power_w"]) == 550.0
        assert registro["brand"] == "Jinko"
        assert registro["modelo"] == "Tiger"
        assert registro["vida_util"] == "25 años"
        assert registro["garantia"] == "10 años"
        assert registro["municipality"] == "Playa"
        assert registro["product_type"] == "panel solar"
        assert registro["source"] == "registro_manual"
        assert registro["collected_at"]

    def test_encabezado_tiene_campos_pedidos(self, tmp_path):
        cfg = _cfg(tmp_path)
        cmd_add(_args(["add", "--precio", "250"]), cfg)
        header = cfg.processed_csv_path.read_text(encoding="utf-8-sig").splitlines()[0]
        for campo in CAMPOS_PEDIDOS:
            assert campo in header.split(","), f"falta {campo}"

    def test_dos_registros_se_acumulan(self, tmp_path):
        cfg = _cfg(tmp_path)
        cmd_add(_args(["add", "--precio", "250"]), cfg)
        cmd_add(_args(["add", "--precio", "300"]), cfg)
        registros = load_csv(cfg.processed_csv_path)
        assert len(registros) == 2

    def test_municipio_se_normaliza(self, tmp_path):
        cfg = _cfg(tmp_path)
        cmd_add(_args(["add", "--municipio", "playa"]), cfg)
        registros = load_csv(cfg.processed_csv_path)
        assert registros[0]["municipality"] == "Playa"

    def test_deduplica_por_url(self, tmp_path):
        cfg = _cfg(tmp_path)
        cmd_add(_args(["add", "--precio", "250", "--url", "https://ejemplo/a"]), cfg)
        cmd_add(_args(["add", "--precio", "999", "--url", "https://ejemplo/a"]), cfg)
        assert len(load_csv(cfg.processed_csv_path)) == 1

    def test_no_mezcla_con_datos_de_ejemplo(self, tmp_path):
        cfg = _cfg(tmp_path)
        cmd_add(_args(["add", "--precio", "250"]), cfg)
        registros = load_csv(cfg.processed_csv_path)
        assert all(r["source"] == "registro_manual" for r in registros)
