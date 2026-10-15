"""
anuncios.py
===========
Registro **manual** de anuncios reales de paneles solares en La Habana.

Es la vía autorizada del proyecto: la persona investiga (por ejemplo, visitando
un sitio de clasificados como usuario normal) y **transcribe** los datos. Este
módulo no accede a la red ni automatiza la extracción.

Contenido:
    * :data:`COLUMNAS_ANUNCIOS` — las columnas de la plantilla de registro.
    * :func:`save_template`     — escribe la plantilla CSV (solo cabecera).
    * :func:`read_rows`         — lee la plantilla rellenada.
    * :func:`is_verifiable_source` — comprueba que hay una fuente verificable.
    * :func:`row_to_record`     — convierte una fila en un registro del esquema.
    * :func:`merge_anuncios`    — incorpora sin duplicar.

Reglas de oro (coherentes con el resto del proyecto):
    * **Nunca se inventa ningún dato**: los campos que no se aporten quedan
      vacíos (``None``).
    * Cada fila debe tener una **fuente verificable** (``url_fuente``): así el
      dato se puede auditar. Las filas sin fuente se rechazan.
    * **No se duplican** anuncios: se comparan por URL (y, si falta, por ID).
    * Los anuncios comerciales se guardan **separados** de los datos abiertos
      energéticos (Banco Mundial, etc.).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Union

import pandas as pd

from analysis import dedup_key
from manual import FUENTE_POR_DEFECTO, build_manual_record

PathLike = Union[str, Path]

# Origen por defecto de los anuncios transcriptos a mano.
FUENTE_ANUNCIOS = FUENTE_POR_DEFECTO  # "registro_manual"

# ---------------------------------------------------------------------------
# Columnas EXACTAS de la plantilla de registro de anuncios (en español).
# Orden pedido por el usuario; se respeta tal cual.
# ---------------------------------------------------------------------------
COLUMNAS_ANUNCIOS: tuple[str, ...] = (
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

# Correspondencia plantilla (español) -> esquema interno (inglés).
MAPA_ANUNCIOS: dict[str, str] = {
    "fecha_consulta": "collected_at",
    "precio": "price_raw",
    "moneda": "currency",
    "potencia_w": "power_w",
    "marca": "brand",
    "modelo": "modelo",
    "vida_util": "vida_util",
    "garantia": "garantia",
    "municipio": "municipality",
    "url_fuente": "url",
    "observaciones": "notes",
}

# Un valor se considera una "fuente verificable" si parece una URL/dominio.
_ESQUEMA_RE = re.compile(r"^(https?|ftp)://", re.IGNORECASE)
_HOST_RE = re.compile(r"^[^\s/:]+\.[^\s/]{2,}$")


def save_template(path: PathLike) -> Path:
    """
    Escribe la plantilla **vacía** (solo cabecera) con las columnas pedidas.

    Devuelve la ruta creada. Es idempotente: sobrescribe el archivo.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=list(COLUMNAS_ANUNCIOS)).to_csv(
        path, index=False, encoding="utf-8-sig"
    )
    return path


def read_rows(path: PathLike) -> list[dict[str, str]]:
    """
    Lee la plantilla rellenada y devuelve una lista de filas (dict en español).

    * Se conservan los valores tal como se escribieron: los campos vacíos
      quedan como ``""`` (nunca se rellenan).
    * Se ignoran las líneas completamente vacías.
    * Las columnas extra desconocidas se ignoran; las columnas que falten se
        tratan como vacías (salvo ``url_fuente``, que es obligatoria).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")

    if "url_fuente" not in frame.columns:
        raise ValueError(
            "El archivo no tiene la columna 'url_fuente'. Usa la plantilla de "
            "anuncios: python main.py template --anuncios"
        )

    filas: list[dict[str, str]] = []
    for row in frame.to_dict(orient="records"):
        fila = {
            columna: (
                str(row[columna]).strip()
                if row.get(columna) is not None
                else ""
            )
            for columna in COLUMNAS_ANUNCIOS
        }
        if not any(fila.values()):
            continue  # fila completamente vacía: no aporta nada
        filas.append(fila)
    return filas


def is_verifiable_source(value: Any) -> bool:
    """
    Indica si el valor parece una **fuente verificable** (URL o dominio).

    Se exige un dominio con punto (p. ej. ``revolico.com`` o
    ``https://www.revolico.com/anuncio/123``). Descarta textos como
    ``"pendiente"``, ``"no lo sé"`` o un correo electrónico.
    """
    text = str(value or "").strip()
    if not text or any(ch.isspace() for ch in text):
        return False
    sin_esquema = _ESQUEMA_RE.sub("", text)
    host = sin_esquema.split("/", 1)[0].split("?", 1)[0]
    if "@" in host:  # es un correo, no una URL
        return False
    return bool(_HOST_RE.match(host))


def row_to_record(row: dict[str, Any], *, source: str = FUENTE_ANUNCIOS) -> dict:
    """
    Convierte una fila de la plantilla en un registro **crudo** del proyecto.

    No deriva nada: solo mapea las columnas en español al esquema interno.
    ``potencia_w`` se pasa como potencia (texto y valor) para que el limpiador
    interprete correctamente valores como ``"550 W"`` o ``550``.
    """
    potencia = row.get("potencia_w")
    return build_manual_record(
        price_raw=row.get("precio"),
        currency=row.get("moneda"),
        power_raw=potencia,
        power_w=potencia,
        brand=row.get("marca"),
        modelo=row.get("modelo"),
        vida_util=row.get("vida_util"),
        garantia=row.get("garantia"),
        municipality=row.get("municipio"),
        url=row.get("url_fuente"),
        collected_at=row.get("fecha_consulta"),
        notes=row.get("observaciones"),
        source=source,
    )


def merge_anuncios(
    existentes: Iterable[dict], nuevos: Iterable[dict]
) -> tuple[list[dict], list[dict]]:
    """
    Incorpora ``nuevos`` a ``existentes`` evitando duplicados.

    Se compara por URL normalizada (y, si falta, por ID), igual que el resto del
    proyecto. Devuelve ``(combinados, duplicados)``: ``duplicados`` son los
    registros nuevos que ya estaban (o que se repiten dentro del propio lote).
    """
    combinados = [dict(r) for r in existentes]
    vistos: set[str] = set()
    for record in combinados:
        key = dedup_key(record)
        if key is not None:
            vistos.add(key)

    duplicados: list[dict] = []
    for record in nuevos:
        key = dedup_key(record)
        if key is not None and key in vistos:
            duplicados.append(record)
            continue
        if key is not None:
            vistos.add(key)
        combinados.append(record)
    return combinados, duplicados

