"""
municipios.py
=============
Normalización de los **municipios de La Habana**.

Objetivo: convertir variantes de escritura ("la habana vieja", "HABANA VIEJA",
"Habana Vieja") en una única etiqueta canónica, para poder agrupar y comparar
anuncios sin que la ortografía rompa los conteos.

Reglas de oro:
    * Nunca se inventa un municipio. Si el texto no coincide con ninguno de los
      15 municipios de La Habana con suficiente confianza, se devuelve ``None``
      (desconocido).
    * La provincia "La Habana" **no** es un municipio: no se asigna ningún
      municipio solo porque el anuncio diga "La Habana". Esa decisión se deja
      al criterio del analista (documentada como limitación).

Fuente de la lista: división político-administrativa vigente de La Habana
(15 municipios).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

# ---------------------------------------------------------------------------
# Lista canónica de municipios de La Habana
# ---------------------------------------------------------------------------
MUNICIPIOS_LA_HABANA: tuple[str, ...] = (
    "Arroyo Naranjo",
    "Boyeros",
    "Centro Habana",
    "Cerro",
    "Cotorro",
    "Diez de Octubre",
    "Guanabacoa",
    "Habana del Este",
    "La Lisa",
    "Marianao",
    "Playa",
    "Plaza de la Revolución",
    "Regla",
    "San Miguel del Padrón",
    "Habana Vieja",
)

# Nombres alternativos observados en anuncios -> etiqueta canónica.
# Las claves ya deben estar normalizadas (sin acentos, minúsculas, sin signos).
_VARIANTES: dict[str, str] = {
    # Arroyo Naranjo
    "arroyo naranjo": "Arroyo Naranjo",
    "arroyo": "Arroyo Naranjo",
    # Boyeros
    "boyeros": "Boyeros",
    "boyero": "Boyeros",
    "santiago de las vegas": "Boyeros",
    "wajay": "Boyeros",
    # Centro Habana
    "centro habana": "Centro Habana",
    "centro": "Centro Habana",
    # Cerro
    "cerro": "Cerro",
    # Cotorro
    "cotorro": "Cotorro",
    # Diez de Octubre
    "diez de octubre": "Diez de Octubre",
    "10 de octubre": "Diez de Octubre",
    "diez octubre": "Diez de Octubre",
    # Guanabacoa
    "guanabacoa": "Guanabacoa",
    # Habana del Este
    "habana del este": "Habana del Este",
    "la habana del este": "Habana del Este",
    "habana este": "Habana del Este",
    "este habana": "Habana del Este",
    "cojimar": "Habana del Este",
    "guanabo": "Habana del Este",
    # La Lisa
    "la lisa": "La Lisa",
    "lisa": "La Lisa",
    # Marianao
    "marianao": "Marianao",
    # Playa
    "playa": "Playa",
    "miramar": "Playa",
    "la playa": "Playa",
    # Plaza de la Revolución
    "plaza de la revolucion": "Plaza de la Revolución",
    "plaza de la revolucion ": "Plaza de la Revolución",
    "plaza": "Plaza de la Revolución",
    "plaza revolucion": "Plaza de la Revolución",
    "vedado": "Plaza de la Revolución",
    # Regla
    "regla": "Regla",
    # San Miguel del Padrón
    "san miguel del padron": "San Miguel del Padrón",
    "san miguel": "San Miguel del Padrón",
    "san miguel del padron ": "San Miguel del Padrón",
    # Habana Vieja
    "habana vieja": "Habana Vieja",
    "la habana vieja": "Habana Vieja",
    "vieja": "Habana Vieja",
    "casco historico": "Habana Vieja",
}

# Palabras que indican provincia (no municipio) y que por tanto NO deben
# confundirse con un municipio.
_PROVINCIA_PALABRAS = {
    "la habana",
    "habana",
    "ciudad de la habana",
    "provincia la habana",
    "provincia de la habana",
    "cuba",
}


def normalizar_texto(text: Optional[str]) -> str:
    """Minúsculas, sin acentos y sin signos de puntuación sobrantes."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", str(text))
    sin_acentos = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    sin_acentos = sin_acentos.lower()
    sin_acentos = re.sub(r"[.,;:_/\-]+", " ", sin_acentos)
    sin_acentos = re.sub(r"\s+", " ", sin_acentos).strip()
    return sin_acentos


def normalize_municipio(text: Optional[str]) -> Optional[str]:
    """
    Devuelve el municipio canónico de La Habana o ``None`` si no se identifica.

    Ejemplos:
        "Habana Vieja"        -> "Habana Vieja"
        "la habana vieja"     -> "Habana Vieja"
        "DIEZ DE OCTUBRE"     -> "Diez de Octubre"
        "La Habana"           -> None  (es la provincia, no un municipio)
        "Santa Clara"         -> None  (no es municipio de La Habana)
    """
    key = normalizar_texto(text)
    if not key:
        return None
    if key in _PROVINCIA_PALABRAS:
        return None
    if key in _VARIANTES:
        return _VARIANTES[key]

    # Coincidencia laxa: el municipio canónico aparece contenido en el texto
    # (p. ej. "reparto Centro Habana").
    for etiqueta in MUNICIPIOS_LA_HABANA:
        if normalizar_texto(etiqueta) in key:
            return etiqueta
    return None


def es_municipio_habana(text: Optional[str]) -> bool:
    """Indica si ``text`` corresponde a un municipio de La Habana."""
    return normalize_municipio(text) is not None
