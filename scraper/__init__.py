"""
scraper
=======
Paquete de recopilación de anuncios de Revolico.

Expone:
    * :class:`RevolicoScraper` y sus excepciones (acceso HTTP cortés).
    * :func:`collect_habana_ads` y :class:`CollectResult` (orquestación).
"""

from scraper.collector import CollectResult, collect_habana_ads
from scraper.revolico_scraper import (
    HTTPAccessError,
    RevolicoScraper,
    RobotsDisallowed,
    ScraperError,
    ScraperNotAuthorized,
)

__all__ = [
    "RevolicoScraper",
    "ScraperError",
    "ScraperNotAuthorized",
    "RobotsDisallowed",
    "HTTPAccessError",
    "CollectResult",
    "collect_habana_ads",
]
