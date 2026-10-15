"""
manual.py
=========
Registro manual de anuncios: alternativa **autorizada** al scraping.

Sirve para incorporar datos que el investigador observa y transcribe de forma
legítima (por ejemplo, visitando el sitio como usuario normal y anotando los
campos), sin automatizar la extracción ni redistribuir contenido de terceros.

Reglas (coherentes con el resto del proyecto):
    * **No se inventa ningún valor.** Los campos no aportados quedan vacíos
      (``None``); el limpiador (``cleaner.py``) intentará derivarlos del texto.
    * ``source`` etiqueta el origen de los datos (por defecto
      ``"registro_manual"``), de modo que siempre se pueda distinguir lo que es
      dato real de lo que es ejemplo o importación.
    * ``collected_at`` se sella con la fecha/hora actual (es metadato, no un
      dato del anuncio).

Este módulo no accede a la red: solo construye registros.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Optional

from cleaner import clean_multiline, clean_text
from config import FIELDS
from municipios import normalize_municipio

FUENTE_POR_DEFECTO = "registro_manual"

# Campos que se piden en el modo interactivo.
# (clave del esquema interno, etiqueta para el usuario)
CAMPOS_INTERACTIVOS: tuple[tuple[str, str], ...] = (
    ("title", "Título del anuncio"),
    ("price_raw", "Precio anunciado (p. ej. '250 USD' o '250')"),
    ("currency", "Moneda (USD, CUP, MLC, EUR)"),
    ("power_raw", "Potencia (p. ej. '550 W' o '12 kW')"),
    ("brand", "Marca"),
    ("modelo", "Modelo"),
    ("vida_util", "Vida útil anunciada (p. ej. '25 años')"),
    ("garantia", "Garantía (p. ej. '10 años')"),
    ("municipality", "Municipio de La Habana (p. ej. 'Playa')"),
    ("product_type", "Tipo de producto (p. ej. 'panel solar')"),
    ("source", f"Fuente de los datos [{FUENTE_POR_DEFECTO}]"),
    ("url", "URL del anuncio (opcional)"),
    ("date_published", "Fecha de publicación (opcional)"),
    ("description", "Descripción (opcional)"),
)

# Campos que se consideran "dato del anuncio" (excluyen metadatos).
# ``notes`` son observaciones del investigador, no un dato del anuncio.
_CAMPOS_DATO = tuple(
    f for f in FIELDS if f not in {"collected_at", "source", "notes"}
)


def _now_iso() -> str:
    """Fecha/hora actual en ISO 8601 (UTC)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_float(value: Any) -> Optional[float]:
    """Convierte a ``float`` sin inventar: si no es numérico, devuelve ``None``."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_manual_record(
    *,
    title: Any = None,
    description: Any = None,
    price_raw: Any = None,
    currency: Any = None,
    power_raw: Any = None,
    power_w: Any = None,
    brand: Any = None,
    modelo: Any = None,
    product_type: Any = None,
    alcance: Any = None,
    vida_util: Any = None,
    garantia: Any = None,
    municipality: Any = None,
    provincia: Any = None,
    url: Any = None,
    date_published: Any = None,
    ad_id: Any = None,
    source: Any = FUENTE_POR_DEFECTO,
    collected_at: Any = None,
    notes: Any = None,
) -> dict:
    """
    Construye un registro **crudo** (esquema interno) a partir de datos aportados.

    No rellena campos ausentes ni deriva valores: eso corresponde a
    ``cleaner.clean_record`` en la fase de procesamiento. Devuelve un
    diccionario con todas las claves de :data:`config.FIELDS`.
    """
    municipio_texto = clean_text(municipality)
    municipio_norm = normalize_municipio(municipality)
    provincia_texto = clean_text(provincia)
    # Derivación segura: los 15 municipios normalizados pertenecen a La Habana.
    if provincia_texto is None and municipio_norm is not None:
        provincia_texto = "La Habana"

    moneda = (clean_text(currency) or "").upper() or None

    record: dict[str, Any] = {field: None for field in FIELDS}
    record.update(
        {
            "ad_id": clean_text(ad_id),
            "title": clean_text(title),
            "description": clean_multiline(description),
            "price_raw": clean_text(price_raw),
            "currency": moneda,
            "power_raw": clean_text(power_raw),
            "power_w": _to_float(power_w),
            "brand": clean_text(brand),
            "modelo": clean_text(modelo),
            "product_type": clean_text(product_type),
            "alcance": clean_text(alcance),
            "vida_util": clean_text(vida_util),
            "garantia": clean_text(garantia),
            "province": provincia_texto,
            "municipality": clean_text(municipality),
            # Se conserva la ubicación tal como la aportó el usuario.
            "ubicacion_original": clean_text(municipality),
            "url": clean_text(url),
            "date_published": clean_text(date_published),
            "collected_at": clean_text(collected_at) or _now_iso(),
            "source": clean_text(source) or FUENTE_POR_DEFECTO,
            # Observaciones del investigador: texto libre, nunca se inventa.
            "notes": clean_multiline(notes),
        }
    )
    return record


def has_data(record: dict) -> bool:
    """Indica si el registro aporta algún dato del anuncio (no solo metadatos)."""
    return any(record.get(field) not in (None, "") for field in _CAMPOS_DATO)


def prompt_record(input_fn: Callable[[str], str] = input) -> dict:
    """
    Pide los campos por consola (modo interactivo) y devuelve un registro crudo.

    Deja en blanco lo que el usuario no sepa: nunca inventa valores.
    """
    valores: dict[str, Any] = {}
    for clave, etiqueta in CAMPOS_INTERACTIVOS:
        try:
            respuesta = input_fn(f"{etiqueta}: ")
        except EOFError:  # entrada agotada: se detiene sin inventar nada
            break
        if respuesta is not None and str(respuesta).strip():
            valores[clave] = str(respuesta).strip()
    return build_manual_record(**valores)
