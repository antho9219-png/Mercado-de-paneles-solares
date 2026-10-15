"""
config.py
=========
Configuración general del proyecto de análisis del mercado de paneles solares
en La Habana.

La configuración se puede ajustar mediante variables de entorno, de modo que el
mismo código funcione en Linux, macOS y Windows sin cambios.

Uso:
    from config import Config
    cfg = Config.from_env()
    print(cfg.raw_csv_path)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# Rutas base (siempre relativas al directorio del proyecto)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Esquema canónico de un anuncio.
# Es el orden de columnas que se usará en CSV/JSON "internos". Mantener este
# orden evita sorpresas al comparar archivos entre ejecuciones.
#
# Las columnas de entrega (data/raw y data/processed) usan nombres en español
# y se generan con el mapa ``storage.SPANISH_COLUMNS``.
# ---------------------------------------------------------------------------
FIELDS: tuple[str, ...] = (
    "ad_id",             # ID del anuncio
    "title",             # Título
    "description",       # Descripción
    "price_raw",         # Precio tal como aparece en el anuncio
    "price_value",       # Precio numérico (derivado)
    "currency",          # Moneda del precio
    "power_raw",         # Potencia tal como aparece
    "power_w",           # Potencia normalizada a vatios (derivado)
    "brand",             # Marca (derivada del texto, sin inventar)
    "modelo",            # Modelo identificado (o nulo)
    "product_type",      # Tipo de producto normalizado
    "alcance",           # Alcance del precio: panel / varios / sistema
    "vida_util",         # Vida útil declarada (con unidades originales)
    "vida_util_anios",   # Vida útil normalizada a años (derivado)
    "garantia",          # Garantía anunciada (texto)
    "location",          # Ubicación normalizada (municipio, provincia)
    "ubicacion_original",# Ubicación tal como aparecía en el anuncio
    "province",          # Provincia
    "municipality",      # Municipio normalizado (La Habana) o nulo
    "category",          # Categoría del sitio
    "date_published",    # Fecha de publicación (ISO 8601)
    "url",               # URL del anuncio
    "collected_at",      # Fecha de recopilación (ISO 8601, UTC)
    "source",            # Origen: "revolico", "import" o "ejemplo"
)

# Campos que se consideran indispensables para que un registro sea "completo".
# Se usan para detectar registros incompletos (no se inventan valores).
REQUIRED_FIELDS: tuple[str, ...] = ("ad_id", "title", "url")

# Términos de búsqueda por defecto relacionados con energía solar.
DEFAULT_SEARCH_TERMS: tuple[str, ...] = (
    "panel solar",
    "paneles solares",
    "sistema fotovoltaico",
    "kit solar",
    "inversor solar",
    "batería solar",
)

# Provincia objetivo por defecto (el proyecto se centra en La Habana).
DEFAULT_PROVINCE = "La Habana"

# Palabras clave que clasifican el tipo de producto. El orden importa:
# el primer grupo que coincida define el tipo.
PRODUCT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "kit solar": (
        "kit solar", "kit fotovoltaico", "sistema solar", "sistema fotovoltaico",
        "instalacion solar", "instalación solar",
    ),
    "panel solar": (
        "panel solar", "paneles solares", "panel fotovoltaico", "modulo solar",
        "módulo solar", "placa solar", "placa fotovoltaica",
    ),
    "inversor solar": (
        "inversor", "inverter", "inversor hibrido", "inversor híbrido",
    ),
    "bateria solar": (
        "bateria", "batería", "baterias", "baterías", "acumulador", "pylontech",
        "bateria de litio", "batería de litio",
    ),
    "controlador": (
        "controlador", "regulador", "mppt", "pwm",
    ),
    "estructura": (
        "estructura", "soporte", "riel", "montaje",
    ),
}

# Marcas conocidas de equipos solares (para derivar `brand` sin inventar datos).
KNOWN_BRANDS: tuple[str, ...] = (
    "Canadian Solar", "JA Solar", "Jinko", "Longi", "Trina", "Risen",
    "Growatt", "Victron", "Sungrow", "Deye", "MUST", "Epever", "Renogy",
    "Felicity", "Pylontech", "BYD", "Huawei", "Fronius", "SMA", "Goodwe",
    "Solis", "Talesun", "Sunpower", "REC", "Qcells", "Astronergy",
    "Luminous", "Microtek", "EPEver", "LiFePO4",
)

# Monedas reconocidas en el contexto cubano.
KNOWN_CURRENCIES: tuple[str, ...] = ("USD", "CUP", "MLC", "EUR")


def _env_str(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on", "si", "sí"}


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    try:
        return float(value) if value not in (None, "") else default
    except ValueError:
        return default


@dataclass
class Config:
    """Contenedor de configuración de la aplicación."""

    # --- Sitio ---
    base_url: str = "https://www.revolico.com"
    search_path: str = "/search"

    # --- Cortesía / límites (NO sobrecargar el sitio) ---
    user_agent: str = "SolarMarketResearchBot/1.0 (+contacto: estudiante@ejemplo.com)"
    request_delay: float = 3.0          # segundos entre peticiones
    request_timeout: float = 20.0       # segundos de espera por respuesta
    max_retries: int = 3                # reintentos ante errores temporales
    max_pages: int = 3                  # páginas de búsqueda por término
    page_length: int = 50               # anuncios por página de búsqueda
    fetch_details: bool = True          # visitar la ficha para completar datos
    max_details: int = 20               # límite de fichas por ejecución
    max_items: int = 50                 # máximo de anuncios por ejecución (global)
    respect_robots: bool = True         # comprobar robots.txt antes de pedir

    # --- Filtro geográfico ---
    province: str = DEFAULT_PROVINCE    # provincia objetivo ("La Habana")

    # --- Autorización (obligatoria para activar el scraper) ---
    scraper_enabled: bool = False
    authorization_confirmed: bool = False

    # --- Entrada / salida ---
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")
    out_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "output")
    log_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "logs")
    raw_subdir: str = "raw"
    processed_subdir: str = "processed"
    raw_csv_name: str = "paneles_solares_habana.csv"
    processed_csv_name: str = "paneles_solares_habana_limpio.csv"
    csv_name: str = "paneles_solares.csv"
    json_name: str = "paneles_solares.json"

    # --- Registro ---
    log_level: str = "INFO"

    # --- Búsqueda ---
    search_terms: List[str] = field(default_factory=lambda: list(DEFAULT_SEARCH_TERMS))

    @classmethod
    def from_env(cls) -> "Config":
        """Crea la configuración leyendo variables de entorno."""
        terms = os.environ.get("SEARCH_TERMS")
        search_terms = (
            [t.strip() for t in terms.split(",") if t.strip()]
            if terms
            else list(DEFAULT_SEARCH_TERMS)
        )
        return cls(
            base_url=_env_str("BASE_URL", "https://www.revolico.com").rstrip("/"),
            search_path=_env_str("SEARCH_PATH", "/search"),
            user_agent=_env_str(
                "USER_AGENT",
                "SolarMarketResearchBot/1.0 (+contacto: estudiante@ejemplo.com)",
            ),
            request_delay=_env_float("REQUEST_DELAY", 3.0),
            request_timeout=_env_float("REQUEST_TIMEOUT", 20.0),
            max_retries=_env_int("MAX_RETRIES", 3),
            max_pages=_env_int("MAX_PAGES", 3),
            page_length=_env_int("PAGE_LENGTH", 50),
            fetch_details=_env_bool("FETCH_DETAILS", True),
            max_details=_env_int("MAX_DETAILS", 20),
            max_items=_env_int("MAX_ITEMS", 50),
            respect_robots=_env_bool("RESPECT_ROBOTS", True),
            province=_env_str("PROVINCE", DEFAULT_PROVINCE),
            scraper_enabled=_env_bool("SCRAPER_ENABLED", False),
            authorization_confirmed=_env_bool("AUTHORIZATION_CONFIRMED", False),
            data_dir=Path(_env_str("DATA_DIR", str(PROJECT_ROOT / "data"))),
            out_dir=Path(_env_str("OUT_DIR", str(PROJECT_ROOT / "output"))),
            log_dir=Path(_env_str("LOG_DIR", str(PROJECT_ROOT / "logs"))),
            raw_subdir=_env_str("RAW_SUBDIR", "raw"),
            processed_subdir=_env_str("PROCESSED_SUBDIR", "processed"),
            raw_csv_name=_env_str("RAW_CSV_NAME", "paneles_solares_habana.csv"),
            processed_csv_name=_env_str(
                "PROCESSED_CSV_NAME", "paneles_solares_habana_limpio.csv"
            ),
            csv_name=_env_str("CSV_NAME", "paneles_solares.csv"),
            json_name=_env_str("JSON_NAME", "paneles_solares.json"),
            log_level=_env_str("LOG_LEVEL", "INFO").upper(),
            search_terms=search_terms,
        )

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    @property
    def search_url(self) -> str:
        """URL base de búsqueda."""
        return f"{self.base_url}{self.search_path}"

    @property
    def raw_dir(self) -> Path:
        """Directorio de datos crudos (data/raw)."""
        return Path(self.data_dir) / self.raw_subdir

    @property
    def processed_dir(self) -> Path:
        """Directorio de datos procesados (data/processed)."""
        return Path(self.data_dir) / self.processed_subdir

    @property
    def raw_csv_path(self) -> Path:
        """Ruta del CSV crudo: data/raw/paneles_solares_habana.csv."""
        return self.raw_dir / self.raw_csv_name

    @property
    def processed_csv_path(self) -> Path:
        """Ruta del CSV procesado: data/processed/*_limpio.csv."""
        return self.processed_dir / self.processed_csv_name

    def ensure_directories(self) -> None:
        """Crea los directorios de datos/salida/logs si no existen."""
        for directory in (
            self.data_dir,
            self.raw_dir,
            self.processed_dir,
            self.out_dir,
            self.log_dir,
        ):
            Path(directory).mkdir(parents=True, exist_ok=True)

    @property
    def csv_path(self) -> Path:
        return Path(self.out_dir) / self.csv_name

    @property
    def json_path(self) -> Path:
        return Path(self.out_dir) / self.json_name

    def is_scraper_authorized(self) -> bool:
        """Indica si el scraper está habilitado Y con autorización confirmada."""
        return bool(self.scraper_enabled and self.authorization_confirmed)


def configure_logging(config: Config) -> None:
    """
    Configura el registro (logging) a consola y a archivo.

    Se escribe en ``logs/solar_scraper.log`` además de la consola.
    """
    import logging

    config.ensure_directories()
    level = getattr(logging, str(config.log_level).upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)
    # Evita duplicar manejadores si se llama más de una vez.
    if root.handlers:
        root.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    log_file = Path(config.log_dir) / "solar_scraper.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    logging.getLogger(__name__).info("Registro iniciado en %s", log_file)
