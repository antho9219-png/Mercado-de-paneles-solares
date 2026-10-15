"""Pruebas de configuración por variables de entorno."""

from config import DEFAULT_SEARCH_TERMS, Config

_ENV_VARS = [
    "BASE_URL", "SEARCH_PATH", "USER_AGENT", "REQUEST_DELAY", "REQUEST_TIMEOUT",
    "MAX_RETRIES", "MAX_PAGES", "PAGE_LENGTH", "FETCH_DETAILS", "MAX_DETAILS",
    "MAX_ITEMS", "PROVINCE", "RESPECT_ROBOTS", "SCRAPER_ENABLED",
    "AUTHORIZATION_CONFIRMED", "DATA_DIR", "OUT_DIR", "LOG_DIR", "RAW_SUBDIR",
    "PROCESSED_SUBDIR", "RAW_CSV_NAME", "PROCESSED_CSV_NAME", "CSV_NAME",
    "JSON_NAME", "LOG_LEVEL", "SEARCH_TERMS",
]


def _clear_env(monkeypatch):
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)


class TestDefaults:
    def test_scraper_desactivado(self, monkeypatch):
        _clear_env(monkeypatch)
        cfg = Config.from_env()
        assert cfg.scraper_enabled is False
        assert cfg.authorization_confirmed is False
        assert cfg.is_scraper_authorized() is False

    def test_valores_seguros(self, monkeypatch):
        _clear_env(monkeypatch)
        cfg = Config.from_env()
        assert cfg.respect_robots is True
        assert cfg.request_delay > 0
        assert cfg.search_terms == list(DEFAULT_SEARCH_TERMS)

    def test_urls(self, monkeypatch):
        _clear_env(monkeypatch)
        cfg = Config.from_env()
        assert cfg.search_url == "https://www.revolico.com/search"


class TestOverrides:
    def test_autorizacion(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("SCRAPER_ENABLED", "true")
        monkeypatch.setenv("AUTHORIZATION_CONFIRMED", "1")
        cfg = Config.from_env()
        assert cfg.is_scraper_authorized() is True

    def test_numeros(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("REQUEST_DELAY", "0.5")
        monkeypatch.setenv("MAX_PAGES", "7")
        cfg = Config.from_env()
        assert cfg.request_delay == 0.5
        assert cfg.max_pages == 7

    def test_terminos(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("SEARCH_TERMS", "panel solar, kit solar")
        cfg = Config.from_env()
        assert cfg.search_terms == ["panel solar", "kit solar"]

    def test_valor_invalido_usa_default(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("MAX_PAGES", "no-numero")
        cfg = Config.from_env()
        assert cfg.max_pages == 3


class TestRutasHabana:
    def test_rutas_por_defecto(self, monkeypatch):
        _clear_env(monkeypatch)
        cfg = Config.from_env()
        assert cfg.province == "La Habana"
        assert cfg.raw_csv_path.name == "paneles_solares_habana.csv"
        assert cfg.processed_csv_path.name == "paneles_solares_habana_limpio.csv"
        assert cfg.raw_csv_path.parent.name == "raw"
        assert cfg.processed_csv_path.parent.name == "processed"

    def test_max_items_env(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("MAX_ITEMS", "15")
        monkeypatch.setenv("PROVINCE", "Matanzas")
        cfg = Config.from_env()
        assert cfg.max_items == 15
        assert cfg.province == "Matanzas"


class TestDirectories:
    def test_ensure_directories(self, tmp_path):
        cfg = Config(
            data_dir=tmp_path / "d",
            out_dir=tmp_path / "o",
            log_dir=tmp_path / "l",
        )
        cfg.ensure_directories()
        assert cfg.data_dir.is_dir()
        assert cfg.out_dir.is_dir()
        assert cfg.log_dir.is_dir()
