"""
Pruebas del parser de Telegram (sin red).
"""
import pytest
from scraper.telegram_parser import TelegramParser
from scraper.telegram_validator import TelegramValidator


def test_classify_panel_solar():
    parser = TelegramParser()
    text = "Vendo panel solar Longi 450W nuevo en Playa"
    assert parser.classify_category(text) == 'panel solar'


def test_classify_bateria_separado():
    parser = TelegramParser()
    text = "Vendo batería LiFePO4 100Ah"
    assert parser.classify_category(text) == 'batería'


def test_classify_inversor_separado():
    parser = TelegramParser()
    text = "Vendo inversor Growatt 5kW"
    assert parser.classify_category(text) == 'inversor'


def test_extract_brand():
    parser = TelegramParser()
    assert parser.extract_brand("Panel Longi 550W") == "Longi"
    assert parser.extract_brand("JA Solar 450W") == "JA Solar"


def test_extract_power():
    parser = TelegramParser()
    assert parser.extract_power("Panel 550W") == 550.0
    assert parser.extract_power("450 w") == 450.0


def test_extract_price():
    parser = TelegramParser()
    price, curr = parser.extract_price("Vendo a 180 USD")
    assert price == 180.0
    assert curr == "USD"


def test_deduplication():
    validator = TelegramValidator()
    rec1 = {'canal': 'test', 'telegram_message_id': 123, 'marca': 'Longi', 'descripcion': 'x', 'precio': 100, 'categoria': 'panel solar', 'provincia': 'La Habana'}
    rec2 = {'canal': 'test', 'telegram_message_id': 123, 'marca': 'Longi', 'descripcion': 'x', 'precio': 100, 'categoria': 'panel solar', 'provincia': 'La Habana'}
    
    validator2 = TelegramValidator()
    result = validator2.validate([rec1, rec2])
    assert result['duplicates'] == 1
    assert result['valid'] == 1


def test_no_inventar_datos():
    parser = TelegramParser()
    msg = {'id': 1, 'text': 'Solo texto sin datos', 'date': None, 'channel': 'test'}
    rec = parser.parse_message(msg)
    # Puede ser None si no se puede clasificar
    if rec:
        assert rec['marca'] is None or isinstance(rec['marca'], str)
        assert rec['precio'] is None or isinstance(rec['precio'], (int, float))
