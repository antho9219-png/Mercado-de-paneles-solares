import json
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, '.')
from scraper.telegram_parser import TelegramParser
from scraper.telegram_validator import TelegramValidator

parser = TelegramParser()
validator = TelegramValidator()

# Cargar los 5 registros originales
with open('data/telegram_paneles_habana.json.original_backup', encoding='utf-8') as f:
    original_records = json.load(f)

# Re-parsear cada registro usando el descripcion original como texto
reparsed = []
for rec in original_records:
    msg = {
        'id': rec['telegram_message_id'],
        'channel': rec['canal'],
        'text': rec['descripcion'],
        'date': datetime.fromisoformat(rec['fecha_publicacion']),
    }
    parsed = parser.parse_message(msg)
    if parsed:
        # Mapear a formato final con todos los campos solicitados
        final = {
            'id': rec['id'],
            'marca': parsed.get('marca'),
            'modelo': parsed.get('modelo'),
            'potencia_w': parsed.get('potencia_w'),
            'precio': parsed.get('precio'),
            'moneda': parsed.get('moneda'),
            'municipio': parsed.get('municipio'),
            'provincia': parsed.get('provincia'),
            'tipo': parsed.get('categoria'),
            'estado': parsed.get('estado'),
            'garantia': parsed.get('garantia'),
            'vida_util': parsed.get('vida_util'),
            'tipo_panel': parsed.get('tipo_panel'),
            'fecha_publicacion': parsed.get('fecha_publicacion'),
            'fecha_extraccion': datetime.now(timezone.utc).isoformat(),
            'canal': parsed.get('canal'),
            'telegram_message_id': parsed.get('telegram_message_id'),
            'url_anuncio': parsed.get('url_mensaje'),
            'url': parsed.get('url_mensaje'),
            'fuente': 'Telegram',
            'observaciones': parsed.get('observaciones'),
        }
        reparsed.append(final)

# Validar con el validador (solo para reporte, no filtrar)
result = validator.validate(reparsed)

# Guardar archivo mejorado (SEPARADO del original)
output_path = Path('data/telegram_paneles_habana_mejorado.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(reparsed, f, ensure_ascii=False, indent=2)

print(f'Archivo guardado: {output_path}')
print(f'Registros reprocesados: {len(reparsed)}')
print(f'Validos por validador: {result["valid"]}')
print(f'Duplicados: {result["duplicates"]}')
print(f'Insuficientes: {result["insufficient"]}')
