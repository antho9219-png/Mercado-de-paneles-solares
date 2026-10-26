"""
docs/telegram_data_collection.md
================================
Documentación para la recolección de datos desde canales públicos de Telegram.
"""

# Recolección de datos desde Telegram

## Requisitos

1. Instalar Telethon:
```bash
pip install telethon
```

2. Obtener credenciales de Telegram:
   - Ir a https://my.telegram.org/apps
   - Iniciar sesión con tu número de teléfono
   - Crear una aplicación
   - Obtener `api_id` y `api_hash`

## Configuración

Crear archivo `.env` (NUNCA commitear):
```env
TELEGRAM_API_ID=tu_api_id
TELEGRAM_API_HASH=tu_api_hash
TELEGRAM_PHONE=+53xxxxxxxxx
TELEGRAM_SESSION_NAME=solar_telegram
```

Añadir a `.gitignore` (ya incluido):
```
*.session
*.session-journal
.env
```

## Uso

### 1. Identificar canales públicos
Edita la lista de canales en tu script. Solo usar canales PÚBLICOS.

### 2. Ejecutar extracción
```python
import asyncio
from scraper.telegram_scraper import TelegramScraper
from scraper.telegram_parser import TelegramParser
from scraper.telegram_validator import TelegramValidator
import json

async def main():
    channels = [
        {'username': 'canal_publico_ejemplo'},  # Reemplazar con canales reales
    ]
    
    scraper = TelegramScraper()
    messages = await scraper.scrape_channels(channels, limit_per_channel=100)
    
    parser = TelegramParser()
    parsed = []
    for msg in messages:
        rec = parser.parse_message(msg)
        if rec:
            parsed.append(rec)
    
    validator = TelegramValidator()
    result = validator.validate(parsed)
    
    with open('telegram.json', 'w', encoding='utf-8') as f:
        json.dump(result['records'], f, ensure_ascii=False, indent=2)
    
    print(validator.generate_report(result))

asyncio.run(main())
```

## Restricciones importantes

- **Solo canales públicos** - No acceder a grupos privados
- **Respetar términos de uso** de Telegram
- **Sin datos personales** - Solo información del anuncio
- **Sin inventar datos** - Usar null si falta información
- **Deduplicación** - Por (canal, telegram_message_id)
- **Sin credenciales en repo**

## Esquema de telegram.json

Ver especificación en el prompt. Campos obligatorios según disponibilidad.

## Limitaciones

Si no hay canales públicos verificables con suficientes anuncios, el resultado será menor a 30. **NO se inventarán registros**.
