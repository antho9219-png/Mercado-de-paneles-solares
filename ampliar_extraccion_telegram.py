"""
Script de ampliación de la extracción de Telegram.
Obtiene mensajes históricos de los canales configurados, los parsea con el
parser mejorado (incluyendo baterías e inversores) y guarda en un archivo
separado sin sobrescribir los originales.
"""
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, '.')
from scraper.telegram_scraper import TelegramScraper
from scraper.telegram_parser import TelegramParser
from scraper.telegram_validator import TelegramValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    root = Path(__file__).parent
    channels_file = root / "config" / "telegram_channels.json"
    output_file = root / "data" / "telegram_paneles_habana_ampliado.json"

    if not channels_file.exists():
        logger.error(f"No existe {channels_file}")
        return

    try:
        data = json.loads(channels_file.read_text(encoding="utf-8"))
        channels = data.get("channels", [])
    except Exception as e:
        logger.error(f"Error leyendo {channels_file}: {e}")
        return

    if not channels:
        logger.error("Lista de canales vacía")
        return

    scraper = TelegramScraper()
    parser = TelegramParser()
    validator = TelegramValidator()

    all_messages = []
    try:
        all_messages = await scraper.scrape_channels(channels, limit_per_channel=None)
        logger.info(f"Total mensajes obtenidos: {len(all_messages)}")
    except Exception as e:
        logger.error(f"Error durante scraping: {e}")
        return
    finally:
        try:
            await scraper.disconnect()
        except Exception:
            pass

    # Parsear todos los mensajes con el parser mejorado
    parsed = []
    for msg in all_messages:
        try:
            rec = parser.parse_message(msg)
            if rec:
                parsed.append(rec)
        except Exception as e:
            logger.debug(f"Error parseando mensaje: {e}")
            continue

    logger.info(f"Anuncios parseados (con evidencia Habana): {len(parsed)}")

    # Validar y deduplicar
    result = validator.validate(parsed)
    logger.info(f"Duplicados descartados: {result['duplicates']}")
    logger.info(f"Insuficientes descartados: {result['insufficient']}")
    logger.info(f"Registros válidos: {result['valid']}")

    # Mapear al esquema de salida ampliado
    final_records = []
    for rec in result['records']:
        final_records.append({
            'id': rec.get('id'),
            'marca': rec.get('marca'),
            'modelo': rec.get('modelo'),
            'potencia_w': rec.get('potencia_w'),
            'precio': rec.get('precio'),
            'moneda': rec.get('moneda'),
            'municipio': rec.get('municipio'),
            'provincia': rec.get('provincia') or 'La Habana',
            'tipo': rec.get('categoria'),
            'estado': rec.get('estado'),
            'garantia': rec.get('garantia'),
            'vida_util': rec.get('vida_util'),
            'tipo_panel': rec.get('tipo_panel'),
            'tipo_bateria': rec.get('tipo_bateria'),
            'capacidad_ah': rec.get('capacidad_ah'),
            'voltaje_nominal_v': rec.get('voltaje_nominal_v'),
            'energia_kwh': rec.get('energia_kwh'),
            'tipo_inversor': rec.get('tipo_inversor'),
            'potencia_inversor_w': rec.get('potencia_inversor_w'),
            'fecha_publicacion': rec.get('fecha_publicacion'),
            'fecha_extraccion': rec.get('fecha_extraccion'),
            'canal': rec.get('canal'),
            'telegram_message_id': rec.get('telegram_message_id'),
            'url_anuncio': rec.get('url_mensaje'),
            'url': rec.get('url_mensaje'),
            'fuente': 'Telegram',
            'observaciones': rec.get('observaciones'),
        })

    # Guardar archivo ampliado (SEPARADO del original)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_records, f, ensure_ascii=False, indent=2)

    logger.info(f"Guardado en: {output_file}")
    logger.info(f"Total registros: {len(final_records)}")

    # Reporte por categoría
    cats = {}
    for r in final_records:
        cat = r.get('tipo', 'desconocido')
        cats[cat] = cats.get(cat, 0) + 1
    logger.info(f"Distribución por categoría: {cats}")

    # Contar nulos por campo
    campos = ['marca', 'modelo', 'potencia_w', 'precio', 'moneda', 'municipio',
              'garantia', 'vida_util', 'tipo_panel', 'tipo_bateria',
              'capacidad_ah', 'voltaje_nominal_v', 'energia_kwh',
              'tipo_inversor', 'potencia_inversor_w', 'estado']
    print("\n=== VALORES NULOS POR CAMPO ===")
    for campo in campos:
        nulos = sum(1 for r in final_records if r.get(campo) in [None, '', 'null'])
        pct = round(100 * nulos / len(final_records), 1) if final_records else 0
        print(f"  {campo}: {nulos}/{len(final_records)} ({pct}%)")

    print("\n=== REGISTROS ===")
    for r in final_records:
        print(f"  ID {r['telegram_message_id']} | {r['canal']} | {r['tipo']} | Marca: {r['marca']} | Precio: {r['precio']} {r['moneda']} | Potencia: {r['potencia_w']}")


if __name__ == "__main__":
    asyncio.run(main())
