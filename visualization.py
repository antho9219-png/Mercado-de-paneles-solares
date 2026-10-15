"""
visualization.py
================
Módulo **opcional** de gráficos (requiere matplotlib).

Genera imágenes PNG en el directorio de salida:
    * distribución de precios
    * relación potencia / precio
    * cantidad de anuncios por ubicación
    * cantidad de anuncios por categoría (tipo de producto)
    * evolución temporal de los anuncios

Cada gráfico lleva título, etiquetas y unidades.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Union

import pandas as pd

from storage import records_to_dataframe

try:  # matplotlib es opcional
    import matplotlib

    matplotlib.use("Agg")  # backend sin pantalla (funciona en servidores/Linux)
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:  # pragma: no cover - depende del entorno
    HAS_MATPLOTLIB = False


def _require_matplotlib() -> None:
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "matplotlib no está instalado. Instálalo con 'pip install matplotlib' "
            "para generar gráficos."
        )


def _as_frame(data: Union[pd.DataFrame, Iterable[dict]]) -> pd.DataFrame:
    return data if isinstance(data, pd.DataFrame) else records_to_dataframe(data)


def _save(fig, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Gráficos individuales
# ---------------------------------------------------------------------------
def plot_price_distribution(
    data: Union[pd.DataFrame, Iterable[dict]],
    out_path: Path,
    currency: Optional[str] = None,
    bins: int = 20,
) -> Optional[Path]:
    """Histograma de precios (una moneda a la vez; no se convierten divisas)."""
    _require_matplotlib()
    frame = _as_frame(data)
    frame["price_value"] = pd.to_numeric(frame.get("price_value"), errors="coerce")
    frame = frame.dropna(subset=["price_value"])
    if frame.empty:
        return None

    if currency is None and "currency" in frame.columns:
        currency = frame["currency"].dropna().mode()
        currency = currency.iloc[0] if not currency.empty else None
    if currency is not None and "currency" in frame.columns:
        frame = frame[frame["currency"] == currency]
        if frame.empty:
            return None

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(frame["price_value"], bins=bins, color="#1c7ed6", edgecolor="white")
    label = f" ({currency})" if currency else ""
    ax.set_title(f"Distribución de precios{label}")
    ax.set_xlabel(f"Precio{label}")
    ax.set_ylabel("Cantidad de anuncios")
    return _save(fig, out_path)


def plot_price_vs_power(
    data: Union[pd.DataFrame, Iterable[dict]], out_path: Path
) -> Optional[Path]:
    """Diagrama de dispersión potencia (W) vs precio."""
    _require_matplotlib()
    frame = _as_frame(data)
    frame["price_value"] = pd.to_numeric(frame.get("price_value"), errors="coerce")
    frame["power_w"] = pd.to_numeric(frame.get("power_w"), errors="coerce")
    frame = frame.dropna(subset=["price_value", "power_w"])
    if frame.empty:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(frame["power_w"], frame["price_value"], color="#f76707", alpha=0.75)
    ax.set_title("Relación entre potencia y precio")
    ax.set_xlabel("Potencia (W)")
    ax.set_ylabel("Precio (moneda original)")
    return _save(fig, out_path)


def plot_ads_by_location(
    data: Union[pd.DataFrame, Iterable[dict]], out_path: Path, top: int = 10
) -> Optional[Path]:
    """Barras horizontales: cantidad de anuncios por ubicación."""
    _require_matplotlib()
    frame = _as_frame(data)
    if frame.empty or "location" not in frame.columns:
        return None
    counts = frame["location"].fillna("(desconocido)").value_counts().head(top)
    if counts.empty:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    counts[::-1].plot(kind="barh", ax=ax, color="#2f9e44")
    ax.set_title(f"Anuncios por ubicación (top {top})")
    ax.set_xlabel("Cantidad de anuncios")
    ax.set_ylabel("Ubicación")
    return _save(fig, out_path)


def plot_ads_by_category(
    data: Union[pd.DataFrame, Iterable[dict]], out_path: Path
) -> Optional[Path]:
    """Barras: cantidad de anuncios por tipo de producto."""
    _require_matplotlib()
    frame = _as_frame(data)
    if frame.empty or "product_type" not in frame.columns:
        return None
    counts = frame["product_type"].fillna("(desconocido)").value_counts()
    if counts.empty:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    counts[::-1].plot(kind="barh", ax=ax, color="#7048e8")
    ax.set_title("Anuncios por categoría (tipo de producto)")
    ax.set_xlabel("Cantidad de anuncios")
    ax.set_ylabel("Tipo de producto")
    return _save(fig, out_path)


def plot_time_evolution(
    data: Union[pd.DataFrame, Iterable[dict]], out_path: Path
) -> Optional[Path]:
    """Línea temporal: anuncios publicados por mes (si hay fechas suficientes)."""
    _require_matplotlib()
    frame = _as_frame(data)
    if frame.empty or "date_published" not in frame.columns:
        return None
    dates = pd.to_datetime(frame["date_published"], errors="coerce", utc=True)
    dates = dates.dropna()
    if dates.empty or dates.dt.to_period("M").nunique() < 2:
        return None  # no hay suficientes fechas para una evolución

    series = dates.dt.to_period("M").value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(series.index.astype(str), series.values, marker="o", color="#d6336c")
    ax.set_title("Evolución temporal de los anuncios")
    ax.set_xlabel("Mes de publicación")
    ax.set_ylabel("Cantidad de anuncios")
    ax.tick_params(axis="x", rotation=45)
    return _save(fig, out_path)


def generate_all_plots(
    data: Union[pd.DataFrame, Iterable[dict]], out_dir: Path
) -> list[Path]:
    """Genera todos los gráficos posibles y devuelve las rutas creadas."""
    out_dir = Path(out_dir)
    created: list[Path] = []
    jobs = (
        ("precios_distribucion.png", lambda p: plot_price_distribution(data, p)),
        ("potencia_vs_precio.png", lambda p: plot_price_vs_power(data, p)),
        ("anuncios_por_ubicacion.png", lambda p: plot_ads_by_location(data, p)),
        ("anuncios_por_categoria.png", lambda p: plot_ads_by_category(data, p)),
        ("evolucion_temporal.png", lambda p: plot_time_evolution(data, p)),
    )
    for name, job in jobs:
        result = job(out_dir / name)
        if result is not None:
            created.append(result)
    return created
