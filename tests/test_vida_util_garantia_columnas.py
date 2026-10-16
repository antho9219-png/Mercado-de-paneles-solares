"""Comprueba que 'vida útil' y 'garantía' se guardan en sus columnas correctas.

Protege contra el error de tenerlas intercambiadas, tanto en la limpieza de
datos nuevos (``clean_record``) como al leer/escribir los CSV en español
(``data/raw`` y ``data/processed``).
"""

from pathlib import Path

from cleaner import clean_record, parse_garantia, parse_vida_util
from storage import SPANISH_COLUMNS, load_csv, save_csv_spanish

RAIZ = Path(__file__).resolve().parent.parent
EJEMPLOS = RAIZ / "data" / "examples" / "ejemplo_paneles_habana.csv"


class TestMapeoDeColumnas:
    """El mapeo interno -> español no debe intercambiar las dos columnas."""

    def test_no_estan_intercambiadas(self):
        assert SPANISH_COLUMNS["vida_util"] == "vida_util"
        assert SPANISH_COLUMNS["garantia"] == "garantia"
        assert SPANISH_COLUMNS["vida_util"] != SPANISH_COLUMNS["garantia"]

    def test_ida_y_vuelta_por_csv(self, tmp_path):
        registro = {
            "ad_id": "X1",
            "title": "Panel de prueba",
            "vida_util": "25 años",
            "vida_util_anios": 25.0,
            "garantia": "10 años",
        }
        destino = tmp_path / "prueba.csv"
        save_csv_spanish([registro], destino)

        encabezado = destino.read_text(encoding="utf-8-sig").splitlines()[0]
        assert "vida_util" in encabezado and "garantia" in encabezado

        cargado = load_csv(destino)[0]
        assert cargado["vida_util"] == "25 años"
        # load_csv lee todo como texto; por eso se compara el número como float.
        assert float(cargado["vida_util_anios"]) == 25.0
        assert cargado["garantia"] == "10 años"

    def test_encabezado_vacio_conserva_ambas_columnas(self, tmp_path):
        destino = tmp_path / "vacio.csv"
        save_csv_spanish([], destino)
        columnas = destino.read_text(encoding="utf-8-sig").splitlines()[0].split(",")
        assert "vida_util" in columnas
        assert "vida_util_anios" in columnas
        assert "garantia" in columnas


class TestParserSinConfusion:
    def test_garantia_no_se_lee_como_vida_util(self):
        assert parse_vida_util("garantía de 10 años") == (None, None)

    def test_vida_util_no_se_lee_como_garantia(self):
        assert parse_garantia("vida útil de 25 años") is None

    def test_ambas_en_el_mismo_texto(self):
        texto = "vida útil de 25 años y garantía de 10 años"
        assert parse_vida_util(texto) == ("25 años", 25.0)
        assert parse_garantia(texto) == "10 años"


class TestCleanRecord:
    def test_cada_valor_en_su_columna(self):
        limpio = clean_record(
            {
                "ad_id": "1",
                "title": "Panel solar 550W Jinko",
                "description": "Nuevo, vida útil de 25 años y garantía de 10 años.",
                "province": "La Habana",
                "municipality": "Playa",
            }
        )
        assert limpio["vida_util"] == "25 años"
        assert limpio["vida_util_anios"] == 25.0
        assert limpio["garantia"] == "10 años"

    def test_solo_garantia_no_llena_vida_util(self):
        limpio = clean_record(
            {
                "ad_id": "2",
                "title": "Inversor híbrido Growatt",
                "description": "Inversor con MPPT, garantía de 5 años.",
                "province": "La Habana",
                "municipality": "Playa",
            }
        )
        assert limpio["garantia"] == "5 años"
        assert limpio["vida_util"] is None
        assert limpio["vida_util_anios"] is None

    def test_solo_vida_util_no_llena_garantia(self):
        limpio = clean_record(
            {
                "ad_id": "3",
                "title": "Panel Trina 575W",
                "description": "Módulo monocristalino, vida útil de 30 años.",
                "province": "La Habana",
                "municipality": "Playa",
            }
        )
        assert limpio["vida_util"] == "30 años"
        assert limpio["garantia"] is None

    def test_valor_explicito_no_se_pisa(self):
        # Si el campo ya viene declarado, se respeta su columna.
        limpio = clean_record(
            {
                "ad_id": "4",
                "title": "Panel solar",
                "description": "Sin datos técnicos en el texto.",
                "vida_util": "20 años",
                "garantia": "12 años",
                "province": "La Habana",
                "municipality": "Playa",
            }
        )
        assert limpio["vida_util"] == "20 años"
        assert limpio["garantia"] == "12 años"


class TestEjemplosIncluidos:
    """Cada valor de los ejemplos incluidos cae en su columna correcta."""

    def test_archivo_de_ejemplos_coherente(self):
        registros = load_csv(EJEMPLOS)
        assert registros, "El archivo de ejemplos no debe estar vacío"
        for bruto in registros:
            limpio = clean_record(bruto)
            descripcion = (limpio.get("description") or "").lower()
            if "vida" in descripcion:
                assert limpio["vida_util"] is not None, limpio["ad_id"]
                assert "año" in limpio["vida_util"], limpio["ad_id"]
            if "garant" in descripcion:
                assert limpio["garantia"] is not None, limpio["ad_id"]

    def test_caso_conocido_80001(self):
        registros = load_csv(EJEMPLOS)
        bruto = next(r for r in registros if r["ad_id"] == "80001")
        limpio = clean_record(bruto)
        assert limpio["vida_util"] == "25 años"
        assert limpio["garantia"] == "10 años"
