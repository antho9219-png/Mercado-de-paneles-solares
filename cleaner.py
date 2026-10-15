"""
cleaner.py
==========
Limpieza y normalización de campos.

Reglas de oro:
    * Nunca se inventan valores. Si algo no se puede derivar con seguridad,
      se devuelve ``None``.
    * El texto original se conserva (campos ``*_raw``) para revisión manual.

Contenido:
    * limpieza de texto (espacios, saltos de línea, entidades sueltas)
    * extracción de precio y moneda
    * extracción y normalización de potencia a vatios
    * detección de marca y modelo
    * clasificación del tipo de producto y del "alcance" del precio
    * extracción de vida útil y garantía (sin confundirlas entre sí)
    * normalización de municipios de La Habana
    * detección de registros incompletos
"""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Any, Iterable, Optional

from config import KNOWN_BRANDS, KNOWN_CURRENCIES, PRODUCT_KEYWORDS, REQUIRED_FIELDS
from municipios import normalize_municipio

# ---------------------------------------------------------------------------
# Expresiones regulares reutilizables
# ---------------------------------------------------------------------------
_WS_RE = re.compile(r"\s+")
# Separador de miles correcto: 1.234.567 o 1,234,567
_THOUSANDS_RE = re.compile(r"^\d{1,3}(?:[.,]\d{3})+$")
# Número (con separadores opcionales)
_NUM_RE = re.compile(r"\d[\d.,]*")
# Potencia: número seguido de W, kW o kWh (kWh se ignora por ser energía)
_POWER_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kwh|kw|w)\b", re.IGNORECASE)
# Moneda por símbolo
_CURRENCY_SYMBOLS = {"€": "EUR", "£": "GBP", "$": None, "₩": None}

# --- Vida útil y garantía -------------------------------------------------
_ANIOS = r"(años|anos|year|years|yrs|yr)"
_MESES = r"(meses|mes|month|months)"
_VIDA_PATTERNS = (
    re.compile(
        rf"vida\s*[uú]til[^0-9]{{0,25}}?(\d{{1,3}}(?:[.,]\d+)?)\s*{_ANIOS}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(\d{{1,3}}(?:[.,]\d+)?)\s*{_ANIOS}\s*(?:de\s*)?vida\s*[uú]til",
        re.IGNORECASE,
    ),
)
_GARANTIA_NUM_RE = re.compile(
    rf"garant[ií]a[^0-9]{{0,25}}?(\d{{1,3}}(?:[.,]\d+)?)\s*({_ANIOS}|{_MESES}|d[ií]as|days?)",
    re.IGNORECASE,
)
_GARANTIA_TEXTO_RE = re.compile(
    r"garant[ií]a\s*(?:de\s*)?(por\s*vida|de\s*f[aá]brica|del?\s*fabricante)",
    re.IGNORECASE,
)

# --- Modelo ---------------------------------------------------------------
# Teselas que se descartan al buscar un modelo después de la marca.
_MODEL_STOP = {
    "w", "kw", "kwh", "v", "ah", "mah", "a", "de", "con", "para", "y", "en",
    "el", "la", "los", "las", "un", "una", "panel", "paneles", "placa",
    "placas", "modulo", "modulos", "solar", "solares", "sistema", "kit",
    "nuevo", "nueva", "usado", "usada", "garantia", "original", "monocristalino",
    "policristalino",
}
_POWER_SPEC_RE = re.compile(r"^\d+(?:[.,]\d+)?\s*(w|kw|kwh|v|ah|mah|a)$", re.IGNORECASE)


def strip_accents(text: str) -> str:
    """Devuelve el texto sin acentos (solo para comparar palabras clave)."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def clean_text(value: Any) -> Optional[str]:
    """
    Normaliza un texto: convierte a str, recorta y colapsa espacios.

    Devuelve ``None`` para valores vacíos o que no aportan información.
    """
    if value is None:
        return None
    text = str(value).replace("\xa0", " ")
    text = _WS_RE.sub(" ", text).strip()
    return text or None


def clean_multiline(value: Any) -> Optional[str]:
    """Como :func:`clean_text` pero conserva los saltos de línea útiles."""
    if value is None:
        return None
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text or None


# ---------------------------------------------------------------------------
# Precio y moneda
# ---------------------------------------------------------------------------
def extract_currency(text: Any) -> Optional[str]:
    """
    Detecta la moneda a partir del texto.

    Prioriza códigos explícitos (USD, CUP, MLC, EUR). El símbolo ``$`` es
    ambiguo, por lo que NO se asume que sea USD.
    """
    if text is None:
        return None
    raw = str(text)
    upper = raw.upper()
    for code in KNOWN_CURRENCIES:
        if re.search(rf"\b{code}\b", upper):
            return code
    for symbol, code in _CURRENCY_SYMBOLS.items():
        if symbol in raw and code is not None:
            return code
    return None


def _number_to_float(number_text: str) -> Optional[float]:
    """Convierte un número con separadores a ``float`` con heurística."""
    num = number_text.strip()
    if not num:
        return None
    has_dot = "." in num
    has_comma = "," in num

    if has_dot and has_comma:
        # El último separador es el decimal.
        if num.rfind(".") > num.rfind(","):
            thousand, decimal = ",", "."
        else:
            thousand, decimal = ".", ","
        num = num.replace(thousand, "").replace(decimal, ".")
    elif has_comma:
        if _THOUSANDS_RE.match(num):
            num = num.replace(",", "")
        else:
            num = num.replace(",", ".")
    elif has_dot:
        if _THOUSANDS_RE.match(num):
            num = num.replace(".", "")
        # en otro caso se deja como decimal ("0.45")

    try:
        return float(num)
    except ValueError:
        return None


def parse_price(text: Any) -> tuple[Optional[float], Optional[str]]:
    """
    Extrae (valor, moneda) de un texto o número de precio.

    Ejemplos:
        "6,000 USD"  -> (6000.0, "USD")
        "2.500 CUP"  -> (2500.0, "CUP")
        "0,45"       -> (0.45, None)
        "sin precio" -> (None, None)
    """
    if text is None:
        return None, None

    currency = extract_currency(text)

    # Si ya es un número, no hay que interpretar separadores.
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        return float(text), currency

    raw = str(text)
    match = _NUM_RE.search(raw)
    if not match:
        return None, currency
    return _number_to_float(match.group(0)), currency


# ---------------------------------------------------------------------------
# Potencia
# ---------------------------------------------------------------------------
def parse_power_watts(text: Any) -> tuple[Optional[float], Optional[str]]:
    """
    Extrae la primera potencia del texto y la normaliza a vatios.

    Ignora ``kWh`` (energía, no potencia). Devuelve ``(vatios, texto_original)``.
    Ejemplos:
        "Panel 450 W"      -> (450.0, "450 W")
        "inversor 12 kW"   -> (12000.0, "12 kW")
        "batería 15 kWh"   -> (None, None)
    """
    if text is None:
        return None, None
    raw = str(text)
    for value_text, unit in _POWER_RE.findall(raw):
        unit_lower = unit.lower()
        if unit_lower == "kwh":
            continue  # energía, no potencia
        value = _number_to_float(value_text)
        if value is None:
            continue
        watts = value * 1000.0 if unit_lower == "kw" else value
        return watts, f"{value_text} {unit}"
    return None, None


# ---------------------------------------------------------------------------
# Vida útil y garantía (¡no confundir una con otra!)
# ---------------------------------------------------------------------------
def parse_vida_util(text: Any) -> tuple[Optional[str], Optional[float]]:
    """
    Extrae la **vida útil** declarada del panel.

    Devuelve ``(texto_con_unidades, anios)``. Solo busca cerca de la expresión
    "vida útil", de modo que no confunde la vida útil con la garantía.

    Ejemplos:
        "vida útil de 25 años"        -> ("25 años", 25.0)
        "25 años de vida útil"        -> ("25 años", 25.0)
        "garantía de 10 años"         -> (None, None)   # es garantía, no vida útil
    """
    if text is None:
        return None, None
    raw = str(text)
    for pattern in _VIDA_PATTERNS:
        match = pattern.search(raw)
        if not match:
            continue
        number = _number_to_float(match.group(1))
        if number is None:
            continue
        years = number  # "años"/"year(s)"; no se convierten otras unidades
        return f"{match.group(1)} {match.group(2)}", years
    return None, None


def parse_garantia(text: Any) -> Optional[str]:
    """
    Extrae la **garantía** anunciada (texto, conservando unidades).

    Ejemplos:
        "garantía de 5 años"     -> "5 años"
        "garantía: 12 meses"     -> "12 meses"
        "garantía por vida"      -> "por vida"
    """
    if text is None:
        return None
    raw = str(text)
    match = _GARANTIA_NUM_RE.search(raw)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    match = _GARANTIA_TEXTO_RE.search(raw)
    if match:
        return match.group(1)
    return None


# ---------------------------------------------------------------------------
# Marca y modelo
# ---------------------------------------------------------------------------
def detect_brand(text: Any) -> Optional[str]:
    """Detecta una marca conocida dentro del texto (sin inventar valores)."""
    if text is None:
        return None
    haystack = strip_accents(str(text)).lower()
    for brand in KNOWN_BRANDS:
        needle = strip_accents(brand).lower()
        if re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack):
            return brand
    return None


def detect_model(text: Any, brand: Optional[str] = None) -> Optional[str]:
    """
    Intenta identificar el **modelo** del producto.

    Es conservador: solo devuelve un modelo si, justo después de la marca,
    aparece una tesela con dígitos que *no* sea una especificación de potencia
    o voltaje (p. ej. ``PV18-5K``). En caso contrario devuelve ``None``.

    Ejemplos:
        "Inversor Growatt SPF5000ES" -> "SPF5000ES"
        "Panel Jinko 550W"           -> None   (550W es potencia, no modelo)
    """
    if not text:
        return None
    if brand is None:
        brand = detect_brand(text)
    if not brand:
        return None

    tokens = [t for t in re.split(r"[\s,;:()\[\]{}/]+", str(text)) if t]
    low = [strip_accents(t).lower() for t in tokens]
    bseq = [strip_accents(b).lower() for b in brand.split()]

    idx = -1
    for i in range(len(low) - len(bseq) + 1):
        if low[i : i + len(bseq)] == bseq:
            idx = i

    if idx < 0:
        return None

    model_tokens: list[str] = []
    for token in tokens[idx + len(bseq) : idx + len(bseq) + 4]:
        plain = strip_accents(token).lower()
        if plain in _MODEL_STOP:
            break
        if _POWER_SPEC_RE.match(token) or re.fullmatch(r"\d+", token):
            # Es una especificación (potencia/voltaje) o una cantidad, no un modelo.
            break
        model_tokens.append(token)
        if len(model_tokens) >= 3:
            break

    if not any(re.search(r"\d", t) for t in model_tokens):
        return None
    return " ".join(model_tokens)


# ---------------------------------------------------------------------------
# Tipo de producto y alcance del precio
# ---------------------------------------------------------------------------
def classify_product(text: Any) -> str:
    """
    Clasifica el producto en una categoría normalizada.

    Distingue entre paneles y otros equipos para no mezclar categorías.
    Devuelve ``"otro"`` cuando no hay coincidencias.
    """
    haystack = strip_accents(str(text or "")).lower()
    if not haystack:
        return "otro"
    for label, keywords in PRODUCT_KEYWORDS.items():
        for keyword in keywords:
            if strip_accents(keyword).lower() in haystack:
                return label
    return "otro"


def detect_alcance(text: Any, product_type: Optional[str] = None) -> str:
    """
    Indica a qué corresponde el precio anunciado.

    Valores posibles:
        * ``"panel individual"``
        * ``"varios paneles"``
        * ``"sistema completo"`` (kits / instalaciones completas)
        * ``"no determinado"``

    Sirve para **no comparar** precios de un panel con precios de un sistema.
    """
    t = strip_accents(str(text or "")).lower()
    if not t:
        return "no determinado"
    if product_type is None:
        product_type = classify_product(t)
    if product_type == "kit solar":
        return "sistema completo"
    if re.search(r"\b(kit|sistema|instalacion)\b", t) and re.search(
        r"panel|placa|modulo|solar|fotovoltaic", t
    ):
        return "sistema completo"

    multiple = re.search(
        r"\b(\d{1,3})\s*(paneles|panel|placas|placa|modulos|modulo)\b", t
    )
    if multiple and int(multiple.group(1)) > 1:
        return "varios paneles"
    if re.search(r"\b(par|juego|set|lote)\s*de\s*\d+\s*(paneles|placas|modulos)", t):
        return "varios paneles"
    if product_type == "panel solar":
        return "panel individual"
    return "no determinado"


# ---------------------------------------------------------------------------
# Ubicación
# ---------------------------------------------------------------------------
def normalize_location(*parts: Any) -> Optional[str]:
    """
    Une provincia/municipio en una ubicación legible.

    No altera el texto más allá de espacios y capitalización ligera; los campos
    originales se conservan por separado.
    """
    cleaned = [clean_text(p) for p in parts if clean_text(p)]
    if not cleaned:
        return None
    return ", ".join(cleaned)


# ---------------------------------------------------------------------------
# Registros incompletos
# ---------------------------------------------------------------------------
def _is_blank(value: Any) -> bool:
    """Detecta valores vacíos, ``None`` o ``NaN`` (sin depender de pandas)."""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, float):
        try:
            return math.isnan(value)
        except (TypeError, ValueError):  # pragma: no cover - defensivo
            return False
    return False


def missing_fields(
    record: dict, required: Iterable[str] = REQUIRED_FIELDS
) -> list[str]:
    """Devuelve la lista de campos obligatorios que faltan o están vacíos."""
    missing = []
    for field_name in required:
        if _is_blank(record.get(field_name)):
            missing.append(field_name)
    return missing


def is_incomplete(record: dict, required: Iterable[str] = REQUIRED_FIELDS) -> bool:
    """Indica si el registro está incompleto según los campos obligatorios."""
    return bool(missing_fields(record, required))


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def clean_record(record: dict) -> dict:
    """
    Aplica la limpieza completa a un registro y devuelve un diccionario nuevo.

    Deriva ``price_value``, ``currency``, ``power_w``, ``brand``, ``modelo``,
    ``product_type``, ``alcance``, ``vida_util``, ``garantia`` y ``location``
    a partir de los campos disponibles, **sin** modificar los textos originales.
    """
    result = dict(record)

    # --- Textos básicos ---
    result["title"] = clean_text(record.get("title"))
    result["description"] = clean_multiline(record.get("description"))
    declared_province = clean_text(record.get("province"))
    declared_municipality = clean_text(record.get("municipality"))
    result["province"] = declared_province
    result["category"] = clean_text(record.get("category"))
    result["url"] = clean_text(record.get("url"))
    if record.get("ad_id") is not None:
        result["ad_id"] = str(record["ad_id"]).strip() or None

    # --- Ubicación: se conserva el texto original y se normaliza el municipio ---
    result["ubicacion_original"] = (
        clean_text(record.get("ubicacion_original"))
        or clean_text(record.get("location"))
        or normalize_location(declared_municipality, declared_province)
    )
    municipio = normalize_municipio(declared_municipality)
    result["municipality"] = municipio  # None si no se identifica con seguridad
    result["location"] = normalize_location(municipio, declared_province) or normalize_location(
        declared_municipality, declared_province
    )

    # --- Precio ---
    price_value, currency = parse_price(record.get("price_raw"))
    if price_value is None and isinstance(record.get("price_value"), (int, float)):
        price_value = float(record["price_value"])
    result["price_value"] = price_value
    existing_currency = clean_text(record.get("currency"))
    result["currency"] = existing_currency.upper() if existing_currency else currency

    # --- Potencia: buscar en texto original y, si falta, en el título ---
    power_text = " ".join(
        str(x) for x in (record.get("power_raw"), record.get("title"),
                         record.get("description")) if x
    )
    watts, power_raw = parse_power_watts(power_text)
    if record.get("power_w") is not None:
        try:
            watts = float(record["power_w"])
        except (TypeError, ValueError):
            pass
    result["power_w"] = watts
    result["power_raw"] = clean_text(record.get("power_raw")) or power_raw

    # --- Texto combinado para derivar marca/modelo/tipo/vida útil/garantía ---
    search_text = " ".join(
        str(x)
        for x in (record.get("title"), record.get("description"), record.get("notes"))
        if x
    )
    result["brand"] = clean_text(record.get("brand")) or detect_brand(search_text)
    result["modelo"] = clean_text(record.get("modelo")) or detect_model(
        search_text, result["brand"]
    )
    result["product_type"] = clean_text(record.get("product_type")) or classify_product(
        search_text
    )
    result["alcance"] = clean_text(record.get("alcance")) or detect_alcance(
        search_text, result["product_type"]
    )

    vida_util, vida_util_anios = parse_vida_util(search_text)
    result["vida_util"] = clean_text(record.get("vida_util")) or vida_util
    if record.get("vida_util_anios") is not None:
        try:
            vida_util_anios = float(record["vida_util_anios"])
        except (TypeError, ValueError):
            pass
    result["vida_util_anios"] = vida_util_anios
    result["garantia"] = clean_text(record.get("garantia")) or parse_garantia(search_text)

    # --- Fechas y meta ---
    result["date_published"] = clean_text(record.get("date_published"))
    result["collected_at"] = clean_text(record.get("collected_at"))
    result["source"] = clean_text(record.get("source")) or "import"
    # Observaciones del investigador: se conservan tal cual (sin derivar nada).
    result["notes"] = clean_multiline(record.get("notes"))
    return result
