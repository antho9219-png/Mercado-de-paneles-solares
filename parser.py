"""
parser.py
=========
Extracción y normalización *estructural* de los datos de un anuncio.

Revolico es una aplicación Next.js: cada página incluye un bloque
``<script id="__NEXT_DATA__">`` con un JSON (estado Apollo) que contiene los
datos del anuncio de forma estructurada. Es una fuente mucho más estable que
el HTML, por lo que se parsea ese JSON en lugar de "raspar" etiquetas.

Este módulo NO limpia precios ni potencias (eso es responsabilidad de
``cleaner.py``); solo extrae estructura y resuelve referencias.

Flujo:
    HTML  ->  extract_next_data()  ->  estado Apollo  ->  registros "crudos"
"""

from __future__ import annotations

import json
from typing import Any, Optional

from bs4 import BeautifulSoup

from cleaner import normalize_location

# URL base del sitio (configurable desde config.Config; aquí es solo el respaldo).
REVOLICO_BASE_URL = "https://www.revolico.com"


class ParseError(Exception):
    """Error al interpretar el contenido de una página."""


# ---------------------------------------------------------------------------
# Acceso al estado Apollo
# ---------------------------------------------------------------------------
def extract_next_data(html: str) -> dict:
    """
    Devuelve el dict de ``__NEXT_DATA__`` contenido en el HTML.

    Lanza :class:`ParseError` si no existe o no es JSON válido.
    """
    if not html or not isinstance(html, str):
        raise ParseError("HTML vacío o no textual")

    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script is None:
        raise ParseError("No se encontró el bloque __NEXT_DATA__")

    payload = script.string or script.get_text()
    if not payload:
        raise ParseError("El bloque __NEXT_DATA__ está vacío")

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensivo
        raise ParseError(f"__NEXT_DATA__ no es JSON válido: {exc}") from exc


def get_apollo_state(next_data: dict) -> dict:
    """Extrae ``props.pageProps.__APOLLO_STATE__`` del ``__NEXT_DATA__``."""
    try:
        return next_data["props"]["pageProps"]["__APOLLO_STATE__"]
    except (KeyError, TypeError) as exc:
        raise ParseError("No se encontró __APOLLO_STATE__ en la página") from exc


def resolve_ref(state: dict, ref: Any) -> Optional[dict]:
    """
    Resuelve una referencia Apollo del tipo ``{"__ref": "ProvinceType:1"}``.

    Si ``ref`` ya es un diccionario normal, se devuelve tal cual.
    """
    if isinstance(ref, dict):
        if "__ref" in ref:
            return state.get(ref["__ref"])
        return ref
    if isinstance(ref, str):
        return state.get(ref)
    return None


def _to_iso(moment: Any) -> Optional[str]:
    """Normaliza una marca temporal de la web a ISO 8601 legible."""
    if moment is None:
        return None
    text = str(moment).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return text


# ---------------------------------------------------------------------------
# Construcción de un registro "crudo"
# ---------------------------------------------------------------------------
def _resolve_place(state: dict, node: dict) -> tuple[Optional[str], Optional[str]]:
    """
    Devuelve ``(provincia, municipio)`` resolviendo referencias o IDs.

    Admite los dos formatos observados:
        * lista:   ``provinceId`` / ``municipalityId`` (p. ej. ``"1"``)
        * detalle: ``province`` / ``municipality`` como ``{"__ref": ...}``
    Las claves del estado siguen el patrón ``ProvinceType:<id>`` y
    ``MunicipalityType:<id>``.
    """

    def lookup(kind: str, ref: Any) -> Optional[dict]:
        if isinstance(ref, dict):
            return resolve_ref(state, ref)
        if ref is None:
            return None
        return state.get(f"{kind}:{ref}") or state.get(str(ref))

    province = municipality = None

    prov = lookup("ProvinceType", node.get("province")) or lookup(
        "ProvinceType", node.get("provinceId")
    )
    if prov:
        province = prov.get("name") or prov.get("title")

    muni = lookup("MunicipalityType", node.get("municipality")) or lookup(
        "MunicipalityType", node.get("municipalityId")
    )
    if muni:
        municipality = muni.get("name") or muni.get("title")

    return province, municipality


def _resolve_category(state: dict, node: dict) -> Optional[str]:
    """Devuelve el título de la categoría/subcategoría del anuncio."""
    subcategory = resolve_ref(state, node.get("subcategory"))
    if subcategory and (subcategory.get("title") or subcategory.get("name")):
        return subcategory.get("title") or subcategory.get("name")
    return None


def parse_ad_node(node: dict, state: dict) -> dict:
    """
    Convierte un nodo Apollo ``AdType`` en un registro "crudo" del esquema.

    No completa valores: los campos no disponibles quedan en ``None``.
    """
    price = node.get("price")
    parsed = {
        "ad_id": str(node["id"]) if node.get("id") is not None else None,
        "title": node.get("title"),
        "description": node.get("description") or node.get("shortDescription"),
        "price_raw": price if price is not None else None,
        "price_value": None,
        "currency": node.get("currency"),
        "power_raw": None,
        "power_w": None,
        "brand": None,
        "modelo": None,
        "product_type": None,
        "alcance": None,
        "vida_util": None,
        "vida_util_anios": None,
        "garantia": None,
        "province": None,
        "municipality": None,
        "location": None,
        "ubicacion_original": None,
        "category": None,
        "date_published": _to_iso(
            node.get("updatedOnByUser") or node.get("updatedOnToOrder")
        ),
        "url": None,
        "collected_at": None,
        "source": "revolico",
    }

    permalink = node.get("permalink")
    if permalink:
        parsed["url"] = f"{REVOLICO_BASE_URL}{permalink}"

    province, municipality = _resolve_place(state, node)
    parsed["province"] = province
    parsed["municipality"] = municipality
    parsed["location"] = normalize_location(municipality, province)
    # La ubicación original (tal como la declara el anuncio) se conserva aparte.
    parsed["ubicacion_original"] = parsed["location"]
    parsed["category"] = _resolve_category(state, node)
    return parsed


# ---------------------------------------------------------------------------
# Búsqueda
# ---------------------------------------------------------------------------
def _search_edges(state: dict) -> list[dict]:
    """Localiza los nodos de resultados de búsqueda dentro del estado Apollo."""
    root = state.get("ROOT_QUERY", {})
    for key, value in root.items():
        if key.startswith("adsPerPage") and isinstance(value, dict):
            return [edge.get("node") for edge in value.get("edges", [])]
    return []


def parse_search_page(html: str) -> list[dict]:
    """
    Extrae todos los anuncios de una página de búsqueda.

    Devuelve una lista de registros "crudos". La lista viene sin descripción
    completa (Revolico no la incluye en el listado).
    """
    next_data = extract_next_data(html)
    state = get_apollo_state(next_data)

    records: list[dict] = []
    for node_ref in _search_edges(state):
        node = resolve_ref(state, node_ref)
        if isinstance(node, dict) and node.get("id") is not None:
            records.append(parse_ad_node(node, state))
    return records


# ---------------------------------------------------------------------------
# Detalle
# ---------------------------------------------------------------------------
def parse_item_page(html: str) -> dict:
    """
    Extrae un único anuncio desde su página de detalle (con descripción).
    """
    next_data = extract_next_data(html)
    state = get_apollo_state(next_data)

    root = state.get("ROOT_QUERY", {})
    node = None
    for key, value in root.items():
        if key.startswith("ad("):
            node = resolve_ref(state, value)
            break

    if node is None:
        # Respaldo: buscar cualquier AdType con descripción.
        for key, value in state.items():
            if key.startswith("AdType:") and isinstance(value, dict):
                node = value
                break

    if not isinstance(node, dict) or node.get("id") is None:
        raise ParseError("No se encontró el anuncio en la página de detalle")

    return parse_ad_node(node, state)


def detail_url(base_url: str, permalink_or_url: str) -> Optional[str]:
    """Construye una URL absoluta de detalle a partir de un permalink."""
    if not permalink_or_url:
        return None
    if permalink_or_url.startswith("http"):
        return permalink_or_url
    return f"{base_url.rstrip('/')}/{permalink_or_url.lstrip('/')}"
