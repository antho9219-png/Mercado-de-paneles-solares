"""
Pruebas del parser y validador de Telegram con filtros geográficos (sin red).
"""
from datetime import datetime, timezone
from scraper.telegram_parser import TelegramParser
from scraper.telegram_validator import TelegramValidator


def make_msg(text, msg_id=1, channel='test_canal', date=None):
    if date is None:
        date = datetime(2026, 10, 25, tzinfo=timezone.utc)
    return {'id': msg_id, 'text': text, 'date': date, 'channel': channel}


def test_habana_municipio_aceptado():
    parser = TelegramParser()
    msg = make_msg("Vendo paneles solares Longi 550W en Playa, La Habana", msg_id=10)
    rec = parser.parse_message(msg)
    assert rec is not None
    assert rec['provincia'] == 'La Habana'
    assert rec['municipio'] == 'Playa'
    assert rec['categoria'] == 'panel solar'


def test_habana_solo_la_habana_aceptado():
    parser = TelegramParser()
    msg = make_msg("Vendo panel solar JA Solar 450W, La Habana", msg_id=11)
    rec = parser.parse_message(msg)
    assert rec is not None
    assert rec['provincia'] == 'La Habana'


def test_otra_provincia_excluido():
    parser = TelegramParser()
    msg = make_msg("Vendo paneles solares en Santiago de Cuba", msg_id=12)
    rec = parser.parse_message(msg)
    assert rec is None


def test_ubicacion_desconocida_excluido():
    parser = TelegramParser()
    msg = make_msg("Vendo panel solar Longi 550W nuevo", msg_id=13)
    rec = parser.parse_message(msg)
    assert rec is None


def test_bateria_sin_panel_excluido():
    parser = TelegramParser()
    msg = make_msg("Vendo batería LiFePO4 100Ah en La Habana", msg_id=14)
    rec = parser.parse_message(msg)
    assert rec is None


def test_inversor_sin_panel_excluido():
    parser = TelegramParser()
    msg = make_msg("Vendo inversor Growatt 5kW en Playa, La Habana", msg_id=15)
    rec = parser.parse_message(msg)
    assert rec is None


def test_kit_solar_con_habana_aceptado():
    parser = TelegramParser()
    msg = make_msg("Kit solar completo 3kW en Centro Habana", msg_id=16)
    rec = parser.parse_message(msg)
    assert rec is not None
    assert rec['categoria'] == 'kit solar'
    assert rec['provincia'] == 'La Habana'


def test_deduplicacion_por_canal_y_message_id():
    validator = TelegramValidator()
    rec1 = {
        'canal': 'test_canal', 'telegram_message_id': 100,
        'marca': 'Longi', 'descripcion': 'Panel en La Habana', 'precio': 200,
        'categoria': 'panel solar', 'provincia': 'La Habana'
    }
    rec2 = dict(rec1)
    result = validator.validate([rec1, rec2])
    assert result['duplicates'] == 1
    assert result['valid'] == 1


def test_datos_incompletos_rechazados():
    validator = TelegramValidator()
    rec = {
        'canal': 'test_canal', 'telegram_message_id': 200,
        'marca': None, 'descripcion': None, 'precio': None, 'potencia_w': None, 'cantidad_paneles': None,
        'categoria': 'panel solar', 'provincia': 'La Habana'
    }
    result = validator.validate([rec])
    assert result['valid'] == 0


def test_provincia_diferente_rechazado_por_validador():
    validator = TelegramValidator()
    rec = {
        'canal': 'test_canal', 'telegram_message_id': 300,
        'marca': 'Longi', 'descripcion': 'Panel', 'precio': 150,
        'categoria': 'panel solar', 'provincia': 'Matanzas'
    }
    result = validator.validate([rec])
    assert result['valid'] == 0
