"""
scraper/collector.py
====================
Orquestación de alto nivel del scraping: recorre los términos de búsqueda,
parsea las páginas, filtra por provincia (La Habana), evita duplicados y
lleva un **registro de ejecución** (cuántos se encontraron, procesaron y
descartaron).

Separa la coordinación (este módulo) del acceso HTTP
(``revolico_scraper.py``) y del parseo (``parser.py``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from config import Config
from municipios import normalizar_texto
from parser import ParseError, parse_item_page, parse_search_page
from scraper.revolico_scraper import (
    HTTPAccessError,
    RevolicoScraper,
    RobotsDisallowed,
    ScraperError,
)

logger = logging.getLogger(__name__)


@dataclass
class CollectResult:
    """Resultado de una ejecución de recopilación (con métricas)."""

    records: list[dict] = field(default_factory=list)
    pages_fetched: int = 0
    found: int = 0
    kept: int = 0
    discarded_province: int = 0
    discarded_duplicates: int = 0
    details_fetched: int = 0
    errors: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        """Resumen legible para consola/logs."""
        return {
            "paginas_descargadas": self.pages_fetched,
            "anuncios_encontrados": self.found,
            "anuncios_conservados": len(self.records),
            "descartados_por_provincia": self.discarded_province,
            "descartados_por_duplicado": self.discarded_duplicates,
            "fichas_de_detalle": self.details_fetched,
            "errores": len(self.errors),
        }


def _matches_province(value: Optional[str], target: Optional[str]) -> bool:
    """Compara una provincia de forma tolerante (acentos, mayúsculas, prefijos)."""
    if not target:
        return True
    if not value:
        return False
    a = normalizar_texto(value)
    b = normalizar_texto(target)
    return a == b or b in a or a in b


def collect_habana_ads(
    config: Config, scraper: Optional[RevolicoScraper] = None
) -> CollectResult:
    """
    Recopila anuncios de la provincia objetivo (por defecto, La Habana).

    * Respeta ``max_items`` (máximo de anuncios por ejecución).
    * Filtra por provincia usando el campo ``province`` resuelto del anuncio.
    * Evita duplicados por URL/ID.
    * Registra los errores por página sin abortar toda la ejecución.
    * Lanza :class:`RobotsDisallowed` si robots.txt prohíbe el acceso.
    """
    scraper = scraper or RevolicoScraper.from_config(config)
    result = CollectResult()
    seen: set[str] = set()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    terms = list(config.search_terms or [])
    stop = False
    for term in terms:
        for page in range(1, config.max_pages + 1):
            if len(result.records) >= config.max_items:
                stop = True
                break
            try:
                _url, html = scraper.search_page(term, page)
            except RobotsDisallowed:
                raise
            except (HTTPAccessError, ScraperError) as exc:
                message = f"{term!r} pág {page}: {exc}"
                logger.warning("Error al buscar: %s", message)
                result.errors.append(message)
                break  # con este término no se insiste

            result.pages_fetched += 1
            try:
                page_records = parse_search_page(html)
            except ParseError as exc:
                message = f"{term!r} pág {page}: {exc}"
                logger.warning("No se pudo parsear la búsqueda: %s", message)
                result.errors.append(message)
                continue

            if not page_records:
                logger.info("Sin resultados para %r en la página %d", term, page)
                break

            for record in page_records:
                result.found += 1
                if not _matches_province(record.get("province"), config.province):
                    result.discarded_province += 1
                    continue
                key = record.get("url") or (
                    f"id:{record.get('ad_id')}" if record.get("ad_id") else None
                )
                if key is not None and key in seen:
                    result.discarded_duplicates += 1
                    continue
                if key is not None:
                    seen.add(key)
                if not record.get("collected_at"):
                    record["collected_at"] = now
                result.records.append(record)
                if len(result.records) >= config.max_items:
                    break
        if stop:
            break

    result.kept = len(result.records)

    if config.fetch_details and result.records:
        _enrich_with_details(scraper, result, config.max_details)

    return result


def _enrich_with_details(
    scraper: RevolicoScraper, result: CollectResult, budget: int
) -> None:
    """Completa registros con la descripción de su página de detalle."""
    remaining = budget
    for record in result.records:
        url = record.get("url")
        if remaining > 0 and url and not record.get("description"):
            try:
                html = scraper.fetch_detail(url)
                detail = parse_item_page(html)
                for key, value in detail.items():
                    if value not in (None, "") and not record.get(key):
                        record[key] = value
                remaining -= 1
                result.details_fetched += 1
            except RobotsDisallowed:
                raise
            except (ScraperError, ParseError) as exc:
                message = f"detalle {url}: {exc}"
                logger.warning("No se pudo completar: %s", message)
                result.errors.append(message)
