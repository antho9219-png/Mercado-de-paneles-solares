"""Pruebas del parser de páginas Next.js (__NEXT_DATA__)."""

import json

import pytest

from parser import (
    ParseError,
    detail_url,
    extract_next_data,
    parse_item_page,
    parse_search_page,
)


def _html_with_next_data(payload: dict) -> str:
    """Construye un HTML mínimo con un bloque __NEXT_DATA__."""
    blob = json.dumps(payload)
    return (
        "<html><head>"
        f'<script id="__NEXT_DATA__" type="application/json">{blob}</script>'
        "</head><body></body></html>"
    )


SEARCH_STATE = {
    "ProvinceType:1": {"__typename": "ProvinceType", "id": "1", "name": "La Habana"},
    "MunicipalityType:39": {"__typename": "MunicipalityType", "id": "39", "name": "Diez de Octubre"},
    "AdType:111": {
        "__typename": "AdType",
        "id": "111",
        "title": "Panel solar 550W",
        "price": 250,
        "currency": "USD",
        "permalink": "/item/panel-solar-550w-111",
        "updatedOnToOrder": "2026-01-15T10:00:00.000Z",
        "provinceId": "1",
        "municipalityId": "39",
    },
    "ROOT_QUERY": {
        'adsPerPage({"contains":"panel solar","page":1})': {
            "edges": [{"node": {"__ref": "AdType:111"}}]
        }
    },
}

ITEM_STATE = {
    "ProvinceType:1": {"__typename": "ProvinceType", "id": "1", "name": "La Habana"},
    "MunicipalityType:39": {"__typename": "MunicipalityType", "id": "39", "name": "Diez de Octubre"},
    "CategoryType:1703": {"__typename": "CategoryType", "id": "1703", "title": "Plantas y Estaciones de Energía"},
    "AdType:222": {
        "__typename": "AdType",
        "id": "222",
        "title": "Kit solar 3kW",
        "description": "Kit solar completo de 3 kW",
        "price": 3500,
        "currency": "USD",
        "permalink": "/item/kit-solar-3kw-222",
        "updatedOnByUser": "2026-03-01T08:00:00.000Z",
        "province": {"__ref": "ProvinceType:1"},
        "municipality": {"__ref": "MunicipalityType:39"},
        "subcategory": {"__ref": "CategoryType:1703"},
    },
    "ROOT_QUERY": {"ad({\"id\":\"222\"})": {"__ref": "AdType:222"}},
}


class TestExtractNextData:
    def test_extrae_json(self):
        html = _html_with_next_data({"props": {"pageProps": {"a": 1}}})
        assert extract_next_data(html)["props"]["pageProps"]["a"] == 1

    def test_sin_next_data(self):
        with pytest.raises(ParseError):
            extract_next_data("<html><body>sin datos</body></html>")

    def test_html_vacio(self):
        with pytest.raises(ParseError):
            extract_next_data("")


class TestParseSearch:
    def test_extrae_anuncio(self):
        html = _html_with_next_data(
            {"props": {"pageProps": {"__APOLLO_STATE__": SEARCH_STATE}}}
        )
        records = parse_search_page(html)
        assert len(records) == 1
        record = records[0]
        assert record["ad_id"] == "111"
        assert record["title"] == "Panel solar 550W"
        assert record["price_raw"] == 250
        assert record["currency"] == "USD"
        assert record["province"] == "La Habana"
        assert record["municipality"] == "Diez de Octubre"
        assert record["url"].endswith("/item/panel-solar-550w-111")
        assert record["date_published"].endswith("+00:00")


class TestParseItem:
    def test_extrae_detalle(self):
        html = _html_with_next_data(
            {"props": {"pageProps": {"__APOLLO_STATE__": ITEM_STATE}}}
        )
        record = parse_item_page(html)
        assert record["ad_id"] == "222"
        assert record["description"] == "Kit solar completo de 3 kW"
        assert record["category"] == "Plantas y Estaciones de Energía"
        assert record["province"] == "La Habana"

    def test_detalle_sin_anuncio(self):
        state = {"ROOT_QUERY": {}}
        html = _html_with_next_data(
            {"props": {"pageProps": {"__APOLLO_STATE__": state}}}
        )
        with pytest.raises(ParseError):
            parse_item_page(html)


class TestDetailUrl:
    def test_relativo(self):
        assert detail_url("https://x.com", "/item/a-1") == "https://x.com/item/a-1"

    def test_absoluto(self):
        assert detail_url("https://x.com", "https://y.com/z") == "https://y.com/z"

    def test_vacio(self):
        assert detail_url("https://x.com", "") is None
