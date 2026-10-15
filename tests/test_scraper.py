"""Pruebas del scraper (sin red): autorización, robots y manejo de errores."""

import urllib.robotparser

import pytest
import requests

from config import Config
from scraper import (
    HTTPAccessError,
    RevolicoScraper,
    RobotsDisallowed,
    ScraperNotAuthorized,
)


def make_config(**overrides) -> Config:
    cfg = Config()
    cfg.request_delay = 0.0  # sin pausas en las pruebas
    cfg.max_retries = 1
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


class DummyResponse:
    def __init__(self, status_code=200, text="", url="http://test/x", encoding="utf-8"):
        self.status_code = status_code
        self.text = text
        self.url = url
        self.encoding = encoding


class DummySession(requests.Session):
    def __init__(self, responses):
        super().__init__()
        self._responses = list(responses)

    def get(self, url, params=None, timeout=None, **kwargs):
        if not self._responses:
            raise AssertionError("No hay respuestas preparadas en el DummySession")
        return self._responses.pop(0)


class TestAuthorization:
    def test_deshabilitado(self):
        with pytest.raises(ScraperNotAuthorized):
            RevolicoScraper.from_config(make_config())

    def test_falta_confirmacion(self):
        with pytest.raises(ScraperNotAuthorized):
            RevolicoScraper.from_config(
                make_config(scraper_enabled=True, authorization_confirmed=False)
            )

    def test_autorizado(self):
        scraper = RevolicoScraper.from_config(
            make_config(scraper_enabled=True, authorization_confirmed=True)
        )
        assert isinstance(scraper, RevolicoScraper)


class TestRobots:
    def test_robots_descargado(self):
        robots_text = "User-agent: *\nDisallow: /privado\n"
        session = DummySession([DummyResponse(200, robots_text, "http://robots")])
        scraper = RevolicoScraper(make_config(respect_robots=True), session=session)
        assert scraper.is_allowed("https://www.revolico.com/item/x") is True
        assert scraper.is_allowed("https://www.revolico.com/privado") is False

    def test_robots_bloquea_peticion(self):
        scraper = RevolicoScraper(make_config(respect_robots=True), session=DummySession([]))
        parser = urllib.robotparser.RobotFileParser()
        parser.parse(["User-agent: *", "Disallow: /search"])
        scraper._robots = parser
        with pytest.raises(RobotsDisallowed):
            scraper.get_html("https://www.revolico.com/search")

    def test_robots_desactivado(self):
        scraper = RevolicoScraper(make_config(respect_robots=False), session=DummySession([]))
        assert scraper.is_allowed("https://www.revolico.com/cualquier-cosa") is True


class TestGetHtml:
    def test_exito(self):
        session = DummySession([DummyResponse(200, "<html>ok</html>")])
        scraper = RevolicoScraper(make_config(respect_robots=False), session=session)
        assert scraper.get_html("http://test/x") == "<html>ok</html>"

    def test_403_no_se_evade(self):
        session = DummySession([DummyResponse(403, "denied")])
        scraper = RevolicoScraper(make_config(respect_robots=False), session=session)
        with pytest.raises(HTTPAccessError):
            scraper.get_html("http://test/x")

    def test_429_no_se_evade(self):
        session = DummySession([DummyResponse(429, "slow down")])
        scraper = RevolicoScraper(make_config(respect_robots=False), session=session)
        with pytest.raises(HTTPAccessError):
            scraper.get_html("http://test/x")

    def test_reintenta_5xx(self):
        session = DummySession([DummyResponse(500, "boom"), DummyResponse(200, "ok")])
        scraper = RevolicoScraper(
            make_config(respect_robots=False, max_retries=3), session=session
        )
        assert scraper.get_html("http://test/x") == "ok"

    def test_error_de_red(self):
        class TimeoutSession(requests.Session):
            def get(self, *args, **kwargs):
                raise requests.Timeout("timeout simulado")

        scraper = RevolicoScraper(
            make_config(respect_robots=False, max_retries=0), session=TimeoutSession()
        )
        with pytest.raises(HTTPAccessError):
            scraper.get_html("http://test/x")
