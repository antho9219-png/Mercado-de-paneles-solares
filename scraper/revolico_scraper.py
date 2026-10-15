"""
scraper/revolico_scraper.py
===========================
Adaptador de acceso al sitio (obtención autorizada de HTML).

Principios de diseño (importante):
    * El scraper está **desactivado por defecto**. Solo funciona si el usuario
      activa ``SCRAPER_ENABLED=true`` Y confirma ``AUTHORIZATION_CONFIRMED=true``,
      dando fe de que cuenta con autorización / base legítima para el acceso.
    * Se respeta ``robots.txt`` (``urllib.robotparser``).
    * Hay pausas configurables entre peticiones y reintentos con espera
      (evita sobrecargar el sitio).
    * **No** se evade CAPTCHA, autenticación, bloqueos ni límites. Ante un
      ``401``/``403``/``429`` el proceso se detiene e informa.
    * **No** se recopilan datos personales: solo datos del anuncio.

Este módulo NO limpia datos: devuelve registros "crudos" que luego procesa
``cleaner.py``.
"""

from __future__ import annotations

import logging
import time
import urllib.robotparser
from typing import Optional

import requests

from config import Config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Excepciones específicas (permiten un manejo de errores claro)
# ---------------------------------------------------------------------------
class ScraperError(Exception):
    """Error genérico del scraper."""


class ScraperNotAuthorized(ScraperError):
    """El scraper no está habilitado o no se confirmó la autorización."""


class RobotsDisallowed(ScraperError):
    """robots.txt no permite acceder a la URL solicitada."""


class HTTPAccessError(ScraperError):
    """Respuesta HTTP inesperada (incluye 401/403/429)."""


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------
class RevolicoScraper:
    """Cliente HTTP cortés para el sitio, con comprobación de robots.txt."""

    def __init__(self, config: Config, session: Optional[requests.Session] = None):
        self.config = config
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": config.user_agent,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "es-CU,es;q=0.9,en;q=0.5",
            }
        )
        self._robots: Optional[urllib.robotparser.RobotFileParser] = None
        self._last_request_time = 0.0

    # -- Construcción controlada -------------------------------------------
    @classmethod
    def from_config(cls, config: Config) -> "RevolicoScraper":
        """
        Crea el scraper validando que exista autorización.

        Lanza :class:`ScraperNotAuthorized` si no está habilitado/confirmado.
        """
        if not config.scraper_enabled:
            raise ScraperNotAuthorized(
                "El scraper está desactivado. Actívalo con SCRAPER_ENABLED=true "
                "solo si tienes autorización para el acceso automatizado."
            )
        if not config.authorization_confirmed:
            raise ScraperNotAuthorized(
                "Falta confirmar la autorización. Define AUTHORIZATION_CONFIRMED=true "
                "únicamente si cuentas con autorización o base legítima."
            )
        return cls(config)

    # -- Control de ritmo ---------------------------------------------------
    def _wait_turn(self) -> None:
        """Garantiza una pausa mínima entre peticiones."""
        elapsed = time.monotonic() - self._last_request_time
        remaining = self.config.request_delay - elapsed
        if remaining > 0:
            logger.debug("Pausa de cortesía: %.2fs", remaining)
            time.sleep(remaining)
        self._last_request_time = time.monotonic()

    # -- robots.txt ---------------------------------------------------------
    def _robots_parser(self) -> urllib.robotparser.RobotFileParser:
        """Descarga y analiza ``robots.txt`` una sola vez."""
        if self._robots is not None:
            return self._robots

        robots_url = f"{self.config.base_url}/robots.txt"
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        try:
            response = self.session.get(robots_url, timeout=self.config.request_timeout)
            if response.status_code == 200:
                parser.parse(response.text.splitlines())
                logger.info("robots.txt cargado desde %s", robots_url)
            elif response.status_code == 404:
                parser.parse([])  # sin robots.txt -> permitido
                logger.info("No hay robots.txt (404); se asume permitido")
            else:
                # Ante la duda, se es conservador y se bloquea.
                parser.parse(["User-agent: *", "Disallow: /"])
                logger.warning(
                    "robots.txt devolvió %s; se bloquea por precaución",
                    response.status_code,
                )
        except requests.RequestException as exc:
            parser.parse(["User-agent: *", "Disallow: /"])
            logger.warning("No se pudo leer robots.txt (%s); se bloquea por precaución", exc)
        self._robots = parser
        return parser

    def is_allowed(self, url: str) -> bool:
        """Indica si ``robots.txt`` permite acceder a ``url``."""
        if not self.config.respect_robots:
            logger.warning("RESPECT_ROBOTS=false: se omite la comprobación de robots.txt")
            return True
        parser = self._robots_parser()
        return parser.can_fetch(self.config.user_agent, url)

    def _check_allowed(self, url: str) -> None:
        if not self.is_allowed(url):
            raise RobotsDisallowed(
                f"robots.txt no permite acceder a {url}. No se continuará."
            )

    # -- Peticiones HTTP ----------------------------------------------------
    def get_html(self, url: str, params: Optional[dict] = None) -> str:
        """
        Descarga el HTML de ``url`` con manejo de errores, pausas y reintentos.

        No intenta eludir ninguna protección: ante 401/403/429 se detiene.
        """
        self._check_allowed(url)

        attempt = 0
        while True:
            attempt += 1
            self._wait_turn()
            try:
                response = self.session.get(
                    url, params=params, timeout=self.config.request_timeout
                )
            except requests.RequestException as exc:
                if attempt > self.config.max_retries:
                    raise HTTPAccessError(
                        f"Fallo de red tras {attempt - 1} reintentos: {exc}"
                    ) from exc
                backoff = self.config.request_delay * attempt
                logger.warning("Error de red (%s). Reintento en %.1fs", exc, backoff)
                time.sleep(backoff)
                continue

            status = response.status_code
            if status == 200:
                if not response.encoding:
                    response.encoding = "utf-8"
                return response.text

            # Nunca se evade un bloqueo ni un límite.
            if status in (401, 403):
                raise HTTPAccessError(
                    f"Acceso denegado (HTTP {status}) en {response.url}. "
                    "No se intentará eludir la restricción."
                )
            if status == 429:
                raise HTTPAccessError(
                    f"Límite de solicitudes alcanzado (HTTP 429) en {response.url}. "
                    "No se intentará eludir el límite; ejecuta más tarde."
                )
            if status == 404:
                raise HTTPAccessError(f"Recurso no encontrado (HTTP 404): {response.url}")
            if 500 <= status < 600:
                if attempt > self.config.max_retries:
                    raise HTTPAccessError(
                        f"Error del servidor (HTTP {status}) tras reintentos: {response.url}"
                    )
                backoff = self.config.request_delay * attempt
                logger.warning("HTTP %s en %s. Reintento en %.1fs", status, response.url, backoff)
                time.sleep(backoff)
                continue

            raise HTTPAccessError(
                f"Respuesta HTTP inesperada ({status}) en {response.url}"
            )

    # -- Búsqueda y detalle -------------------------------------------------
    def search_page(self, term: str, page: int = 1) -> tuple[str, str]:
        """Devuelve ``(url, html)`` de una página de búsqueda."""
        url = self.config.search_url
        params = {"q": term, "page": page}
        logger.info("Buscando %r (página %s)", term, page)
        return url, self.get_html(url, params=params)

    def fetch_detail(self, url: str) -> str:
        """Descarga el HTML de un anuncio."""
        logger.info("Descargando detalle: %s", url)
        return self.get_html(url)
