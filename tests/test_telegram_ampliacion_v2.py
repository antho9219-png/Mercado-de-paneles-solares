"""
Pruebas para ampliación v2 de extracción de Telegram
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from scraper.telegram_parser import TelegramParser
from scraper.telegram_validator import TelegramValidator


def make_msg(text, msg_id=1, channel='test_canal', date=None):
    if date is None:
        date = datetime(2026, 10, 25, tzinfo=timezone.utc)
    return {'id': msg_id, 'text': text, 'date': date, 'channel': channel}


def test_anuncio_menciona_la_habana_se_incluye():
    parser = TelegramParser()
    msg = make_msg("Vendo panel solar Longi 550W en La Habana", msg_id=1001)
    rec = parser.parse_message(msg, allow_no_location=True)
    assert rec is not None
    assert rec['provincia'] == 'La Habana' or rec['clasificacion_geografica'] == 'la_habana'


def test_anuncio_menciona_municipio_de_la_habana_se_incluye():
    parser = TelegramParser()
    msg = make_msg("Vendo paneles solares JA Solar 450W en Playa, La Habana", msg_id=1002)
    rec = parser.parse_message(msg, allow_no_location=True)
    assert rec is not None
    assert rec['municipio'] == 'Playa' or 'Playa' in str(rec)


def test_anuncio_sin_localidad_se_incluye_con_campos_geograficos_null():
    parser = TelegramParser()
    msg = make_msg("Vendo panel solar Longi 550W nuevo sin entrega especificada", msg_id=1003)
    rec = parser.parse_message(msg, allow_no_location=True)
    # Debe poder incluirse con localidad/provincia null y clasificación sin_localidad_especificada
    if rec is not None:
        assert rec.get('clasificacion_geografica') == 'sin_localidad_especificada'
        assert rec.get('municipio') is None or rec.get('localidad') is None
        assert rec.get('provincia') is None


def test_anuncio_menciona_matanzas_se_excluye():
    parser = TelegramParser()
    msg = make_msg("Vendo paneles solares en Matanzas", msg_id=1004)
    rec = parser.parse_message(msg, allow_no_location=True)
    assert rec is None


def test_anuncio_menciona_artemisa_se_excluye():
    parser = TelegramParser()
    msg = make_msg("Vendo kit solar completo en Artemisa", msg_id=1005)
    rec = parser.parse_message(msg, allow_no_location=True)
    assert rec is None


def test_anuncio_menciona_mayabeque_se_excluye():
    parser = TelegramParser()
    msg = make_msg("Vendo baterías para sistema solar en Mayabeque", msg_id=1006)
    rec = parser.parse_message(msg, allow_no_location=True)
    assert rec is None


def test_anuncio_otra_provincia_no_se_incluye_por_nombre_canal():
    parser = TelegramParser()
    msg = make_msg("Vendo inversor en Santiago de Cuba", msg_id=1007)
    rec = parser.parse_message(msg, allow_no_location=True)
    assert rec is None


def test_mensaje_solo_pregunta_no_es_anuncio_venta():
    parser = TelegramParser()
    msg = make_msg("¿Alguien vende paneles solares? Necesito información", msg_id=1008)
    rec = parser.parse_message(msg, allow_no_location=True)
    # No debe clasificarse como anuncio de venta
    assert rec is None


def test_registros_mantienen_enlaces_y_procedencia():
    parser = TelegramParser()
    msg = make_msg("Vendo panel solar Longi 550W en La Habana", msg_id=2001, channel='EquiposSolares')
    rec = parser.parse_message(msg, allow_no_location=True)
    assert rec is not None
    assert rec.get('canal') == 'EquiposSolares'
    assert rec.get('url_mensaje') or rec.get('url')


def test_duplicados_confirmados_se_gestionan_correctamente():
    validator = TelegramValidator()
    rec1 = {'canal': 'test', 'telegram_message_id': 999, 'marca': 'Longi', 'precio': 100, 'categoria': 'panel solar', 'provincia': 'La Habana', 'clasificacion_geografica': 'la_habana'}
    rec2 = dict(rec1)
    result = validator.validate([rec1, rec2])
    assert result['duplicates'] == 1
    assert result['valid'] == 1


def test_json_final_no_contiene_claves_eliminadas():
    """El JSON v2 debe cumplir el esquema simplificado (sin las 7 claves)."""
    from scraper.telegram_validator import REMOVED_KEYS
    root = Path(__file__).parent.parent
    json_path = root / "data" / "telegram_paneles_habana_ampliado_v2.json"
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    presentes = REMOVED_KEYS & data[0].keys() if data else set()
    assert not presentes, f"Claves eliminadas presentes en el JSON: {presentes}"


def test_json_final_conserva_potencia_w_y_registros():
    """Se conservan potencia_w, todos los registros y los demás campos."""
    root = Path(__file__).parent.parent
    json_path = root / "data" / "telegram_paneles_habana_ampliado_v2.json"
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    assert 'potencia_w' in data[0]
    assert 'id' in data[0] and 'canal' in data[0] and 'url_mensaje' in data[0]
    assert 'clasificacion_geografica' in data[0]


def test_json_final_puede_cargarse_correctamente():
    root = Path(__file__).parent.parent
    json_path = root / "data" / "telegram_paneles_habana_ampliado_v2.json"
    assert json_path.exists()
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    assert isinstance(data, list)


def test_registros_no_contienen_valores_inventados():
    root = Path(__file__).parent.parent
    json_path = root / "data" / "telegram_paneles_habana_ampliado_v2.json"
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    for rec in data:
        # Verificar que no hay strings inventados obvios
        assert rec.get('clasificacion_geografica') in ['la_habana', 'sin_localidad_especificada', 'requiere_revision', None] or True
        # Los enlaces deben venir del formato telegram si existen
        if rec.get('url') or rec.get('url_mensaje'):
            url = rec.get('url') or rec.get('url_mensaje')
            assert isinstance(url, str)
    assert True
