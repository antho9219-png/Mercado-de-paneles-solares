"""
opendata.py
===========
Recopilación de **datos abiertos reutilizables** (no anuncios).

Solo usa fuentes con licencia que permite la reutilización (por defecto, la API
pública del Banco Mundial, cuyos datos se publican con licencia abierta
CC BY 4.0). Guarda siempre la **fuente**, la **URL** y la **fecha de recopilación**
de cada registro.

Importante:
    * Estos datos son **contexto** para el estudio del mercado solar en Cuba
      (electrificación, cuota renovable, economía). **No son anuncios** y no
      contienen precio, marca ni modelo de paneles.
    * No se scrapea ningún clasificado ni se reproduce contenido de terceros.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional, Union

import requests

PathLike = Union[str, Path]

# ---------------------------------------------------------------------------
# Fuente: Banco Mundial (datos abiertos, CC BY 4.0)
# ---------------------------------------------------------------------------
BANCO_MUNDIAL_API = "https://api.worldbank.org/v2"
PAIS_POR_DEFECTO = "CUB"
BANCO_MUNDIAL_NOMBRE = "Banco Mundial - datos abiertos"
BANCO_MUNDIAL_LICENCIA = "CC BY 4.0"

# (id del indicador, descripción en español)
INDICADORES_BANCO_MUNDIAL: tuple[tuple[str, str], ...] = (
    ("EG.ELC.ACCS.ZS", "Acceso a la electricidad (% de la poblacion)"),
    ("EG.ELC.RNEW.ZS", "Electricidad renovable (% del total)"),
    ("EG.FEC.RNEW.ZS", "Consumo de energia renovable (% del total)"),
    ("EG.USE.PCAP.KG.OE", "Uso de energia per capita (kg equivalente de petroleo)"),
    ("NY.GDP.PCAP.CD", "PIB per capita (USD corrientes)"),
)

# Columnas del CSV de datos abiertos (procedencia incluida).
COLUMNAS_OPENDATA: tuple[str, ...] = (
    "indicador_id",
    "indicador",
    "pais",
    "anio",
    "valor",
    "unidad",
    "fuente",
    "fuente_url",
    "licencia",
    "fecha_recopilacion",
)

_DESCRIPCION_POR_ID = {i: d for i, d in INDICADORES_BANCO_MUNDIAL}


def _ahora_iso() -> str:
    """Fecha/hora actual en ISO 8601 (UTC)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_world_bank_indicator(
    indicator_id: str,
    country: str = PAIS_POR_DEFECTO,
    *,
    session: Any = None,
    timeout: float = 30.0,
    per_page: int = 100,
    description: Optional[str] = None,
) -> list[dict]:
    """
    Descarga un indicador del Banco Mundial para un país.

    Devuelve una lista de registros (uno por año con valor disponible). Solo se
    incluyen los años con valor: **no se rellenan huecos**.
    Lanza ``requests.RequestException`` si falla la red o el servidor.
    """
    session = session if session is not None else requests
    url = f"{BANCO_MUNDIAL_API}/country/{country}/indicator/{indicator_id}"
    params = {"format": "json", "per_page": per_page}

    respuesta = session.get(url, params=params, timeout=timeout)
    respuesta.raise_for_status()
    payload = respuesta.json()

    if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
        return []

    nombre = description or _DESCRIPCION_POR_ID.get(indicator_id, indicator_id)
    fecha = _ahora_iso()
    registros: list[dict] = []
    for fila in payload[1]:
        valor = fila.get("value")
        if valor is None:  # nunca se inventan valores
            continue
        registros.append(
            {
                "indicador_id": fila.get("indicator", {}).get("id", indicator_id),
                "indicador": nombre,
                "pais": fila.get("country", {}).get("value", country),
                "anio": fila.get("date"),
                "valor": valor,
                "unidad": fila.get("unit", "") or "",
                "fuente": BANCO_MUNDIAL_NOMBRE,
                "fuente_url": url,
                "licencia": BANCO_MUNDIAL_LICENCIA,
                "fecha_recopilacion": fecha,
            }
        )
    return registros


def fetch_world_bank(
    indicator_ids: Optional[Iterable[str]] = None,
    country: str = PAIS_POR_DEFECTO,
    *,
    session: Any = None,
    timeout: float = 30.0,
) -> list[dict]:
    """Descarga varios indicadores (por defecto, los de :data:`INDICADORES_BANCO_MUNDIAL`)."""
    ids = list(indicator_ids) if indicator_ids else [i for i, _ in INDICADORES_BANCO_MUNDIAL]
    registros: list[dict] = []
    for indicator_id in ids:
        registros.extend(
            fetch_world_bank_indicator(
                indicator_id, country, session=session, timeout=timeout
            )
        )
    return registros


def save_opendata_csv(records: Iterable[dict], path: PathLike) -> Path:
    """Guarda los registros en CSV (utf-8-sig) con el orden de columnas fijo."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    registros = [dict(r) for r in records]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(COLUMNAS_OPENDATA), extrasaction="ignore")
        writer.writeheader()
        for registro in registros:
            writer.writerow({col: registro.get(col) for col in COLUMNAS_OPENDATA})
    return path


def load_opendata_csv(path: PathLike) -> list[dict]:
    """Carga un CSV de datos abiertos previamente guardado."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return [dict(fila) for fila in csv.DictReader(fh)]
