"""Pruebas del colector (sin red): filtro por provincia, duplicados y límite."""

import json

from config import Config
from scraper import collect_habana_ads


def _html(state: dict) -> str:
    blob = json.dumps({"props": {"pageProps": {"__APOLLO_STATE__": state}}})
    return (
        '<html><head><script id="__NEXT_DATA__" type="application/json">'
        f"{blob}</script></head></html>"
    )


def _state(ads: list[dict]) -> dict:
    state = {
        "ProvinceType:1": {"__typename": "ProvinceType", "id": "1", "name": "La Habana"},
        "ProvinceType:2": {"__typename": "ProvinceType", "id": "2", "name": "Villa Clara"},
        "MunicipalityType:39": {"__typename": "MunicipalityType", "id": "39", "name": "Playa"},
        "ROOT_QUERY": {
            'adsPerPage({"contains":"panel solar","page":1})': {
                "edges": [{"node": {"__ref": f"AdType:{a['id']}"}} for a in ads]
            }
        },
    }
    for ad in ads:
        state[f"AdType:{ad['id']}"] = ad
    return state


def _ad(ad_id, province_id="1"):
    return {
        "__typename": "AdType",
        "id": str(ad_id),
        "title": f"Panel solar {ad_id}",
        "price": 200,
        "currency": "USD",
        "permalink": f"/item/panel-solar-{ad_id}",
        "updatedOnToOrder": "2026-01-15T10:00:00.000Z",
        "provinceId": province_id,
        "municipalityId": "39",
    }


class FakeScraper:
    """Scraper falso: devuelve HTML preparado, sin tocar la red."""

    def __init__(self, pages: dict):
        self.pages = pages
        self.calls = []

    def search_page(self, term, page=1):
        self.calls.append((term, page))
        html = self.pages.get((term, page))
        if html is None:
            return "http://fake/search", _html({"ROOT_QUERY": {}})
        return "http://fake/search", html

    def fetch_detail(self, url):  # pragma: no cover - no debe usarse aquí
        raise AssertionError("fetch_detail no debería llamarse en estas pruebas")


def make_config(**overrides) -> Config:
    cfg = Config()
    cfg.search_terms = ["panel solar"]
    cfg.max_pages = 1
    cfg.fetch_details = False
    cfg.province = "La Habana"
    cfg.max_items = 50
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


class TestFiltroProvincia:
    def test_solo_la_habana(self):
        pages = {("panel solar", 1): _html(_state([_ad(1, "1"), _ad(2, "2")]))}
        cfg = make_config()
        result = collect_habana_ads(cfg, FakeScraper(pages))
        assert [r["ad_id"] for r in result.records] == ["1"]
        assert result.discarded_province == 1
        assert result.found == 2

    def test_registros_tienen_fecha(self):
        pages = {("panel solar", 1): _html(_state([_ad(1)]))}
        result = collect_habana_ads(make_config(), FakeScraper(pages))
        assert result.records[0]["collected_at"]


class TestDuplicados:
    def test_evita_repetidos_por_url(self):
        ad = _ad(1)
        pages = {("panel solar", 1): _html(_state([ad, dict(ad)]))}
        result = collect_habana_ads(make_config(), FakeScraper(pages))
        assert len(result.records) == 1
        assert result.discarded_duplicates == 1


class TestLimite:
    def test_max_items(self):
        ads = [_ad(i) for i in range(1, 6)]
        pages = {("panel solar", 1): _html(_state(ads))}
        result = collect_habana_ads(make_config(max_items=2), FakeScraper(pages))
        assert len(result.records) == 2


class TestResumen:
    def test_resumen(self):
        pages = {("panel solar", 1): _html(_state([_ad(1)]))}
        result = collect_habana_ads(make_config(), FakeScraper(pages))
        resumen = result.summary()
        assert resumen["anuncios_encontrados"] == 1
        assert resumen["anuncios_conservados"] == 1
