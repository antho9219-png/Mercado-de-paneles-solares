"""
storage.py
==========
Entrada/salida de datos.

* Exporta resultados a CSV y JSON.
* Importa datos **obtenidos legítimamente** desde CSV o JSON (alternativa al
  scraping), tolerando columnas con nombres en español o en inglés.
* Convierte entre listas de registros y ``pandas.DataFrame``.

No modifica ni inventa datos: solo lee, escribe y normaliza la forma.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Union

import pandas as pd

from cleaner import strip_accents
from config import FIELDS

PathLike = Union[str, Path]

# ---------------------------------------------------------------------------
# Alias de columnas para importar archivos heterogéneos
# ---------------------------------------------------------------------------
_COLUMN_ALIASES: dict[str, str] = {
    # identificador
    "id": "ad_id",
    "ad_id": "ad_id",
    "anuncio_id": "ad_id",
    "id_anuncio": "ad_id",
    # título
    "titulo": "title",
    "title": "title",
    "nombre": "title",
    # descripción
    "descripcion": "description",
    "description": "description",
    # precio
    "precio": "price_raw",
    "price": "price_raw",
    "price_raw": "price_raw",
    # moneda
    "moneda": "currency",
    "currency": "currency",
    "precio_valor": "price_value",
    # potencia
    "potencia": "power_raw",
    "potencia_w": "power_w",
    "power": "power_raw",
    "power_raw": "power_raw",
    # marca y modelo
    "marca": "brand",
    "brand": "brand",
    "modelo": "modelo",
    "model": "modelo",
    # tipo y alcance
    "tipo": "product_type",
    "tipo_producto": "product_type",
    "product_type": "product_type",
    "alcance": "alcance",
    # vida útil y garantía
    "vida_util": "vida_util",
    "vida_util_anios": "vida_util_anios",
    "garantia": "garantia",
    "warranty": "garantia",
    # ubicación
    "ubicacion": "location",
    "location": "location",
    "ubicacion_original": "ubicacion_original",
    "provincia": "province",
    "province": "province",
    "municipio": "municipality",
    "municipality": "municipality",
    # categoría
    "categoria": "category",
    "category": "category",
    # fechas
    "fecha": "date_published",
    "fecha_publicacion": "date_published",
    "date_published": "date_published",
    "fecha_recopilacion": "collected_at",
    "collected_at": "collected_at",
    # enlace
    "url": "url",
    "enlace": "url",
    "link": "url",
    "url_anuncio": "url",
    # origen
    "source": "source",
    "origen": "source",
    "fuente": "source",
}

# Posibles claves que envuelven la lista de registros en un JSON.
_JSON_LIST_KEYS = ("records", "ads", "data", "items", "results", "paneles", "anuncios")

# ---------------------------------------------------------------------------
# Mapa del esquema interno (inglés) al esquema de entrega (español).
# Se usa para los CSV de data/raw y data/processed.
# ---------------------------------------------------------------------------
SPANISH_COLUMNS: dict[str, str] = {
    "ad_id": "id_anuncio",
    "title": "titulo",
    "description": "descripcion",
    "price_raw": "precio",
    "price_value": "precio_valor",
    "currency": "moneda",
    "power_raw": "potencia",
    "power_w": "potencia_w",
    "brand": "marca",
    "modelo": "modelo",
    "product_type": "tipo_producto",
    "alcance": "alcance",
    "vida_util": "vida_util",
    "vida_util_anios": "vida_util_anios",
    "garantia": "garantia",
    "location": "ubicacion",
    "ubicacion_original": "ubicacion_original",
    "province": "provincia",
    "municipality": "municipio",
    "category": "categoria",
    "date_published": "fecha_publicacion",
    "url": "url_anuncio",
    "collected_at": "fecha_recopilacion",
    "source": "fuente",
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _is_missing(value: Any) -> bool:
    """Detecta valores nulos o ``NaN`` sin depender del tipo."""
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):  # pragma: no cover - defensivo
        return False


def _stringify_id(value: Any) -> Any:
    """Convierte IDs numéricos a texto sin el sufijo ``.0``."""
    if _is_missing(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip() or None


def _normalize_record(record: dict, alias: bool = True) -> dict:
    """Aplica alias de columnas y deja solo el esquema canónico."""
    result: dict[str, Any] = {}
    for key, value in record.items():
        canonical = key
        if alias:
            canonical = _COLUMN_ALIASES.get(strip_accents(str(key)).lower().replace(" ", "_"), key)
        if canonical in FIELDS and canonical not in result:
            result[canonical] = None if _is_missing(value) else value

    for field_name in FIELDS:
        result.setdefault(field_name, None)

    result["ad_id"] = _stringify_id(result.get("ad_id"))
    if result.get("currency"):
        result["currency"] = str(result["currency"]).strip().upper()
    return result


def records_to_dataframe(records: Iterable[dict]) -> pd.DataFrame:
    """Construye un ``DataFrame`` con el esquema canónico y orden de columnas."""
    rows = [dict(r) for r in records]
    if not rows:
        return pd.DataFrame(columns=list(FIELDS))
    return pd.DataFrame(rows).reindex(columns=list(FIELDS))


def records_to_spanish_dataframe(records: Iterable[dict]) -> pd.DataFrame:
    """
    Construye un ``DataFrame`` con las **columnas de entrega en español**.

    Respeta el orden de :data:`SPANISH_COLUMNS`, de modo que los archivos de
    ``data/raw`` y ``data/processed`` siempre tengan las mismas columnas.
    """
    frame = records_to_dataframe(records)
    spanish_order = list(SPANISH_COLUMNS.values())
    if frame.empty:
        return pd.DataFrame(columns=spanish_order)
    return frame.rename(columns=SPANISH_COLUMNS)[spanish_order]


# ---------------------------------------------------------------------------
# Guardado
# ---------------------------------------------------------------------------
def save_json(records: Iterable[dict], path: PathLike) -> Path:
    """Guarda una lista de registros en un JSON UTF-8 legible."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [dict(r) for r in records]
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path


def save_csv(records: Iterable[dict], path: PathLike) -> Path:
    """
    Guarda una lista de registros en CSV UTF-8.

    Se usa ``utf-8-sig`` para que Excel abra bien los acentos; el separador es
    la coma estándar y funciona igual en Linux.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = records_to_dataframe(records)
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def save_csv_spanish(records: Iterable[dict], path: PathLike) -> Path:
    """
    Guarda una lista de registros en CSV UTF-8 con **columnas en español**.

    Es el formato de entrega del proyecto (data/raw y data/processed).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = records_to_spanish_dataframe(records)
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def save_records(records: Iterable[dict], csv_path: PathLike, json_path: PathLike) -> tuple[Path, Path]:
    """Guarda en CSV y JSON a la vez. Devuelve ``(csv, json)``."""
    records = [dict(r) for r in records]
    return save_csv(records, csv_path), save_json(records, json_path)


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------
def load_csv(path: PathLike) -> list[dict]:
    """Carga registros desde un CSV, aplicando alias de columnas."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    return [_normalize_record(row) for row in frame.to_dict(orient="records")]


def load_json(path: PathLike) -> list[dict]:
    """
    Carga registros desde JSON.

    Admite:
        * una lista de objetos;
        * un objeto con una lista bajo claves como ``records``/``ads``/``paneles``;
        * un único objeto-registro (se envuelve en una lista).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(payload, list):
        raw_records = payload
    elif isinstance(payload, dict):
        raw_records = None
        for key in _JSON_LIST_KEYS:
            if isinstance(payload.get(key), list):
                raw_records = payload[key]
                break
        if raw_records is None:
            # ¿Es un único registro?
            if any(k in payload for k in ("title", "titulo", "ad_id", "id")):
                raw_records = [payload]
            else:
                raise ValueError(
                    "El JSON no contiene una lista de anuncios reconocible"
                )
    else:
        raise ValueError("Estructura JSON no soportada")

    return [_normalize_record(r) for r in raw_records if isinstance(r, dict)]


def load_records(path: PathLike) -> list[dict]:
    """Carga registros detectando el formato por la extensión del archivo."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv(path)
    if suffix == ".json":
        return load_json(path)
    raise ValueError(f"Formato no soportado: {suffix!r} (usa .csv o .json)")
