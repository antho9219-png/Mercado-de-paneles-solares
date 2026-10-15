"""
analysis.py
===========
Lógica de análisis de datos, separada del scraping.

Incluye:
    * detección y eliminación de duplicados (por ``ad_id`` o ``url``)
    * detección de registros incompletos
    * filtrado de la categoría "panel solar"
    * estadísticas descriptivas de precios por moneda
    * conteos por ubicación, categoría, etc.

No convierte monedas: cualquier precio se analiza en su moneda original.
"""

from __future__ import annotations

from typing import Iterable, Optional, Union

import pandas as pd

from cleaner import is_incomplete, missing_fields
from config import FIELDS, REQUIRED_FIELDS
from storage import records_to_dataframe


# ---------------------------------------------------------------------------
# Duplicados
# ---------------------------------------------------------------------------
def dedup_key(record: dict) -> Optional[str]:
    """
    Devuelve la clave de deduplicación de un registro.

    Se usa la URL normalizada y, si no existe, el ``ad_id``.
    """
    url = record.get("url")
    if url and str(url).strip():
        return "url:" + str(url).strip().rstrip("/").lower()
    ad_id = record.get("ad_id")
    if ad_id is not None and str(ad_id).strip():
        return "id:" + str(ad_id).strip()
    return None


def find_duplicates(records: Iterable[dict]) -> list[dict]:
    """Devuelve los registros que son duplicados (a partir del segundo)."""
    seen: set[str] = set()
    duplicates: list[dict] = []
    for record in records:
        key = dedup_key(record)
        if key is None:
            continue
        if key in seen:
            duplicates.append(record)
        else:
            seen.add(key)
    return duplicates


def deduplicate(records: Iterable[dict]) -> list[dict]:
    """
    Elimina duplicados conservando la primera aparición.

    Los registros sin ``ad_id`` ni ``url`` se conservan (no se pueden comparar).
    """
    seen: set[str] = set()
    unique: list[dict] = []
    for record in records:
        key = dedup_key(record)
        if key is not None:
            if key in seen:
                continue
            seen.add(key)
        unique.append(record)
    return unique


# ---------------------------------------------------------------------------
# Registros incompletos
# ---------------------------------------------------------------------------
def incomplete_records(
    records: Iterable[dict], required: Iterable[str] = REQUIRED_FIELDS
) -> list[dict]:
    """Devuelve los registros a los que les falta algún campo obligatorio."""
    required = tuple(required)
    return [r for r in records if is_incomplete(r, required)]


def incompleteness_report(
    records: Iterable[dict], required: Iterable[str] = REQUIRED_FIELDS
) -> pd.DataFrame:
    """Genera un resumen de cuántos registros carecen de cada campo."""
    records = list(records)
    total = len(records)
    rows = []
    for field_name in required:
        missing = sum(
            1 for r in records if field_name in missing_fields(r, (field_name,))
        )
        rows.append(
            {
                "campo": field_name,
                "faltantes": missing,
                "porcentaje": round(100 * missing / total, 2) if total else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=["campo", "faltantes", "porcentaje"])


# ---------------------------------------------------------------------------
# Selección de categoría
# ---------------------------------------------------------------------------
def only_panels(frame: pd.DataFrame) -> pd.DataFrame:
    """Devuelve solo los anuncios clasificados como ``panel solar``."""
    if frame.empty or "product_type" not in frame.columns:
        return frame.iloc[0:0]
    return frame[frame["product_type"] == "panel solar"].copy()


# ---------------------------------------------------------------------------
# Estadísticas
# ---------------------------------------------------------------------------
def _as_frame(data: Union[pd.DataFrame, Iterable[dict]]) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data
    return records_to_dataframe(data)


def descriptive_statistics(
    data: Union[pd.DataFrame, Iterable[dict]],
    column: str = "price_value",
) -> pd.DataFrame:
    """
    Estadísticas descriptivas de una columna numérica, agrupadas por moneda.

    Se calculan sobre el precio original: **no** se convierten monedas.
    Devuelve un ``DataFrame`` con índice de moneda.
    """
    frame = _as_frame(data)
    if frame.empty or column not in frame.columns:
        return pd.DataFrame(
            columns=["moneda", "n", "media", "mediana", "min", "max", "p25", "p75", "desv"]
        )

    work = frame.copy()
    work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.dropna(subset=[column])
    if work.empty:
        return pd.DataFrame(
            columns=["moneda", "n", "media", "mediana", "min", "max", "p25", "p75", "desv"]
        )

    if "currency" not in work.columns:
        work["currency"] = None
    work["currency"] = work["currency"].fillna("(sin moneda)")

    grouped = work.groupby("currency")[column]
    stats = grouped.agg(
        n="count",
        media="mean",
        mediana="median",
        min="min",
        max="max",
        p25=lambda s: s.quantile(0.25),
        p75=lambda s: s.quantile(0.75),
        desv="std",
    ).reset_index()
    stats = stats.rename(columns={"currency": "moneda"})
    for col in ("media", "mediana", "p25", "p75", "desv"):
        stats[col] = stats[col].round(2)
    return stats


def count_by(
    data: Union[pd.DataFrame, Iterable[dict]],
    column: str,
    top: Optional[int] = None,
) -> pd.DataFrame:
    """
    Cuenta registros por el valor de ``column``.

    Devuelve un ``DataFrame`` ``[valor, cantidad]`` ordenado de mayor a menor.
    """
    frame = _as_frame(data)
    if frame.empty or column not in frame.columns:
        return pd.DataFrame(columns=[column, "cantidad"])
    counts = frame[column].fillna("(desconocido)").value_counts()
    if top is not None:
        counts = counts.head(top)
    result = counts.reset_index()
    result.columns = [column, "cantidad"]
    return result


def summarize(data: Union[pd.DataFrame, Iterable[dict]]) -> dict:
    """Resumen general del conjunto de datos (para informes por consola)."""
    frame = _as_frame(data)
    total = len(frame)
    panels = len(only_panels(frame)) if not frame.empty else 0
    return {
        "total": total,
        "paneles": panels,
        "otros_equipos": total - panels,
        "con_precio": int(pd.to_numeric(frame.get("price_value"), errors="coerce").notna().sum())
        if not frame.empty and "price_value" in frame.columns
        else 0,
        "con_potencia": int(pd.to_numeric(frame.get("power_w"), errors="coerce").notna().sum())
        if not frame.empty and "power_w" in frame.columns
        else 0,
        "incompletos": len(incomplete_records(frame.to_dict(orient="records"))) if total else 0,
    }
