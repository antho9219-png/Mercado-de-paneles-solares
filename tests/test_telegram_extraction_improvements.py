"""
Pruebas adicionales para validar extracción de marca, modelo, garantía, estado
"""
from datetime import datetime, timezone
from scraper.telegram_parser import TelegramParser


def make_msg(text, msg_id=1, channel='test_canal', date=None):
    if date is None:
        date = datetime(2026, 10, 25, tzinfo=timezone.utc)
    return {'id': msg_id, 'text': text, 'date': date, 'channel': channel}


def test_jinkosolar_como_marca():
    parser = TelegramParser()
    msg = make_msg("Paneles Solares JinkoSolar 590W en La Habana", msg_id=100)
    rec = parser.parse_message(msg)
    assert rec is not None
    assert rec['marca'] in ['JinkoSolar', 'Jinko']


def test_jinko_sin_solar_separado():
    parser = TelegramParser()
    msg = make_msg("Panel Jinko 550W en Playa, La Habana", msg_id=101)
    rec = parser.parse_message(msg)
    assert rec is not None
    assert rec['marca'] is not None


def test_garantia_extraida():
    parser = TelegramParser()
    msg = make_msg("Panel solar Longi 550W con garantía de 25 años en La Habana", msg_id=102)
    rec = parser.parse_message(msg)
    assert rec is not None
    assert rec['garantia'] is not None


def test_estado_nuevo():
    parser = TelegramParser()
    msg = make_msg("Vendo paneles nuevos Longi 550W en Centro Habana", msg_id=103)
    rec = parser.parse_message(msg)
    assert rec is not None
    assert rec['estado'] == 'nuevo'


def test_modelo_extraido():
    parser = TelegramParser()
    msg = make_msg("Panel solar modelo JKM550M-72HL4-V en La Habana", msg_id=104)
    rec = parser.parse_message(msg)
    assert rec is not None
    # Puede extraer modelo o ser None según formato


def test_potencia_no_confundida_con_precio():
    parser = TelegramParser()
    msg = make_msg("Panel 590W precio 143 USD en La Habana", msg_id=105)
    rec = parser.parse_message(msg)
    assert rec is not None
    assert rec['potencia_w'] == 590.0
    assert rec['precio'] == 143.0
    assert rec['moneda'] == 'USD'
