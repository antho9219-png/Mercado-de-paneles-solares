import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from scraper.telegram_scraper import TelegramScraper
from scraper.telegram_parser import TelegramParser
from scraper.telegram_validator import TelegramValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    root = Path(__file__).parent
    channels_file = root / "config" / "telegram_channels.json"
    output_file = root / "data" / "telegram_paneles_habana.json"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not channels_file.exists():
        logger.error(f"No existe {channels_file}")
        logger.error("Añade canales públicos verificados a config/telegram_channels.json con formato: {'channels': [{'username': '...'}]}")
        return
    
    try:
        data = json.loads(channels_file.read_text(encoding="utf-8"))
        channels = data.get("channels", [])
    except Exception as e:
        logger.error(f"Error leyendo {channels_file}: {e}")
        return
    
    if not channels:
        logger.error("Lista de canales vacía")
        logger.error("NO SE INVENTARÁN CANALES. Debes añadir usernames públicos verificados manualmente.")
        logger.error("Formato: {\"channels\": [{\"username\": \"nombre_canal_publico\"}]}")
        logger.error("Sin @, solo canales públicos verificados para La Habana")
        # Guardar archivo vacío válido
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        logger.info(f"Guardado archivo vacío: {output_file}")
        return
    
    scraper = TelegramScraper()
    parser = TelegramParser()
    validator = TelegramValidator()
    
    all_messages = []
    try:
        all_messages = await scraper.scrape_channels(channels, limit_per_channel=200)
        logger.info(f"Total mensajes obtenidos: {len(all_messages)}")
    except Exception as e:
        logger.error(f"Error durante scraping: {e}")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return
    finally:
        try:
            await scraper.disconnect()
        except Exception:
            pass
    
    parsed = []
    for msg in all_messages:
        try:
            rec = parser.parse_message(msg)
            if rec:
                parsed.append(rec)
        except Exception as e:
            logger.debug(f"Error parseando mensaje: {e}")
            continue
    
    result = validator.validate(parsed)
    
    # Mapear al esquema solicitado
    final_records = []
    for rec in result['records']:
        final_records.append({
            'id': rec.get('id'),
            'marca': rec.get('marca'),
            'modelo': rec.get('modelo'),
            'potencia': rec.get('potencia_w'),
            'precio': rec.get('precio'),
            'moneda': rec.get('moneda'),
            'municipio': rec.get('municipio'),
            'provincia': rec.get('provincia') or 'La Habana',
            'cantidad': rec.get('cantidad_paneles'),
            'tipo': rec.get('categoria'),
            'estado': rec.get('estado'),
            'garantia': rec.get('garantia'),
            'vida_util': rec.get('vida_util'),
            'fecha_publicacion': rec.get('fecha_publicacion'),
            'fecha_extraccion': rec.get('fecha_extraccion'),
            'canal': rec.get('canal'),
            'telegram_message_id': rec.get('telegram_message_id'),
            'url_anuncio': rec.get('url_mensaje'),
            'descripcion': rec.get('descripcion')
        })
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_records, f, ensure_ascii=False, indent=2)
    
    logger.info("=" * 50)
    logger.info(f"Canales consultados: {len(channels)}")
    logger.info(f"Mensajes examinados: {len(all_messages)}")
    logger.info(f"Anuncios parseados (con evidencia Habana): {len(parsed)}")
    logger.info(f"Duplicados descartados: {result['duplicates']}")
    logger.info(f"Insuficientes/invalidos descartados: {result['insufficient']}")
    logger.info(f"Anuncios válidos de La Habana: {len(final_records)}")
    logger.info(f"Guardado en: {output_file}")
    logger.info("=" * 50)
    if len(final_records) < 30:
        logger.info("Menos de 30 registros válidos. No se generaron datos ficticios.")
    
    print("\n" + validator.generate_report(result))
    print(f"RUTA: {output_file}")
    print(f"VALIDOS_LA_HABANA: {len(final_records)}")


if __name__ == "__main__":
    asyncio.run(main())
