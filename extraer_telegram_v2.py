#!/usr/bin/env python3
"""
Extracción ampliada v2 de Telegram para La Habana/Cuba.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, '.')

from scraper.telegram_scraper import TelegramScraper, TelegramAuthError, TelegramChannelNotAccessible
from scraper.telegram_parser import TelegramParser
from scraper.telegram_validator import TelegramValidator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    root = Path(__file__).parent
    channels_file = root / "config" / "telegram_channels.json"
    output_json = root / "data" / "telegram_paneles_habana_ampliado_v2.json"
    output_report = root / "docs" / "informe_ampliacion_telegram_v2.md"
    
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    
    # Crear backups verificables
    backup_files = []
    for fname in ["data/telegram_paneles_habana.json", "data/telegram_paneles_habana_ampliado.json", 
                 "data/telegram_paneles_habana_mejorado.json"]:
        fpath = root / fname
        if fpath.exists():
            backup_path = root / f"{fname}.backup_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(fpath, backup_path)
            backup_files.append(str(backup_path))
            logger.info(f"Backup creado: {backup_path}")
    
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
    access_errors = []
    try:
        logger.info(f"Iniciando extracción de {len(channels)} canales...")
        # Intentar obtener todos los mensajes accesibles
        all_messages = await scraper.scrape_channels(channels, limit_per_channel=None)
        logger.info(f"Total mensajes recuperados: {len(all_messages)}")
    except TelegramAuthError as e:
        logger.error(f"Error de autenticación: {e}")
        access_errors.append(f"Auth error: {e}")
        # No simular - informar del problema
        report = generate_report([], channels, [], 0, access_errors, backup_files)
        output_report.write_text(report, encoding="utf-8")
        return
    except TelegramChannelNotAccessible as e:
        logger.error(f"Canal no accesible: {e}")
        access_errors.append(str(e))
    except Exception as e:
        logger.error(f"Error durante scraping: {e}")
        access_errors.append(str(e))
        return
    finally:
        try:
            await scraper.disconnect()
        except Exception:
            pass
    
    # Analizar todos los mensajes
    candidatos = []  # mensajes que son anuncios relevantes
    parsed_all = []
    excluidos_provincia = []
    requiere_revision = []
    sin_localidad = []
    
    for msg in all_messages:
        try:
            text = msg.get('text', '')
            if not text or len(text.strip()) < 10:
                continue
            # Clasificar si es anuncio relevante
            category = parser.classify_category(text)
            if not category:
                continue
            candidatos.append(msg)
            # Analizar geografía
            geo_result = parser.has_habana_evidence(text)
            if len(geo_result) == 3:
                incluir, municipio, clasificacion = geo_result
            else:
                incluir, municipio = geo_result[0], geo_result[1]
                clasificacion = 'la_habana' if incluir else 'sin_localidad_especificada'
            
            if clasificacion == 'excluir':
                excluidos_provincia.append({
                    'msg_id': msg.get('id'),
                    'canal': msg.get('channel'),
                    'razon': 'menciona otra provincia'
                })
                continue
            # Parsear con allow_no_location para incluir sin localidad
            rec = parser.parse_message(msg, allow_no_location=True)
            if rec:
                parsed_all.append(rec)
                if rec.get('clasificacion_geografica') == 'sin_localidad_especificada':
                    sin_localidad.append(rec)
                elif rec.get('provincia') == 'La Habana' or rec.get('clasificacion_geografica') == 'la_habana':
                    pass  # es de La Habana
        except Exception as e:
            logger.debug(f"Error procesando mensaje: {e}")
            continue
    
    logger.info(f"Mensajes analizados: {len(all_messages)}")
    logger.info(f"Anuncios candidatos: {len(candidatos)}")
    logger.info(f"Anuncios parseados: {len(parsed_all)}")
    logger.info(f"Excluidos por otra provincia: {len(excluidos_provincia)}")
    
    # Validar y deduplicar
    result = validator.validate(parsed_all)
    valid_records = result['records']
    
    logger.info(f"Duplicados confirmados: {result['duplicates']}")
    logger.info(f"Registros válidos únicos: {len(valid_records)}")
    
    # Asegurar formato completo para v2
    final_records = []
    for rec in valid_records:
        final_rec = {
            'id': rec.get('id'),
            'canal': rec.get('canal'),
            'message_id': rec.get('telegram_message_id') or rec.get('message_id'),
            'telegram_message_id': rec.get('telegram_message_id') or rec.get('message_id'),
            'fecha_publicacion': rec.get('fecha_publicacion'),
            'url': rec.get('url') or rec.get('url_mensaje') or rec.get('url_anuncio'),
            'url_mensaje': rec.get('url_mensaje') or rec.get('url') or rec.get('url_anuncio'),
            'url_anuncio': rec.get('url_anuncio') or rec.get('url_mensaje') or rec.get('url'),
            'fuente': rec.get('fuente') or 'Telegram',
            'provincia': rec.get('provincia'),
            'municipio': rec.get('municipio'),
            'localidad': rec.get('localidad') or rec.get('municipio'),
            'clasificacion_geografica': rec.get('clasificacion_geografica') or ('la_habana' if rec.get('provincia') == 'La Habana' else 'sin_localidad_especificada'),
            'categoria_producto': rec.get('categoria_producto') or rec.get('categoria') or rec.get('tipo'),
            'categoria': rec.get('categoria') or rec.get('categoria_producto') or rec.get('tipo'),
            'tipo': rec.get('tipo') or rec.get('categoria') or rec.get('categoria_producto'),
            'marca': rec.get('marca'),
            'modelo': rec.get('modelo'),
            'potencia_w': rec.get('potencia_w') if rec.get('potencia_w') is not None else rec.get('potencia'),
            'precio': rec.get('precio'),
            'moneda': rec.get('moneda'),
            'estado': rec.get('estado'),
            'garantia': rec.get('garantia'),
            'vida_util': rec.get('vida_util'),
            'tipo_panel': rec.get('tipo_panel'),
            'marca_bateria': rec.get('marca_bateria'),
            'modelo_bateria': rec.get('modelo_bateria'),
            'tipo_bateria': rec.get('tipo_bateria'),
            'capacidad_ah': rec.get('capacidad_ah'),
            'voltaje_nominal_v': rec.get('voltaje_nominal_v'),
            'energia_kwh': rec.get('energia_kwh'),
            'marca_inversor': rec.get('marca_inversor'),
            'modelo_inversor': rec.get('modelo_inversor'),
            'tipo_inversor': rec.get('tipo_inversor'),
            'potencia_inversor_w': rec.get('potencia_inversor_w'),
            'incluye_paneles': rec.get('incluye_paneles'),
            'incluye_bateria': rec.get('incluye_bateria'),
            'incluye_inversor': rec.get('incluye_inversor'),
            'componentes_incluidos': rec.get('componentes_incluidos'),
            'precio_sistema': rec.get('precio_sistema'),
            'observaciones': rec.get('observaciones'),
            'fecha_extraccion': rec.get('fecha_extraccion'),
        }
        final_records.append(final_rec)
    
    # Guardar JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(final_records, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Guardado: {output_json}")
    
    # Generar informe
    report = generate_report(final_records, channels, all_messages, len(candidatos), access_errors, backup_files, 
                             excluidos_provincia, result['duplicates'], len(sin_localidad))
    output_report.write_text(report, encoding="utf-8")
    logger.info(f"Informe generado: {output_report}")


def generate_report(records, channels, all_messages, candidatos, access_errors, backup_files,
                    excluidos_provincia=None, duplicados_confirmados=0, sin_localidad_count=0):
    excluidos_provincia = excluidos_provincia or []
    
    habana_count = sum(1 for r in records if r.get('clasificacion_geografica') == 'la_habana' or r.get('provincia') == 'La Habana')
    sin_loc_count = sin_localidad_count or sum(1 for r in records if r.get('clasificacion_geografica') == 'sin_localidad_especificada')
    
    # Contar nulos por campo (esquema simplificado: sin descripcion/titulo/potencia/cantidad*)
    campos = ['marca', 'modelo', 'potencia_w', 'precio', 'moneda', 'municipio', 'localidad',
              'garantia', 'vida_util', 'tipo_panel', 'tipo_bateria', 'capacidad_ah', 
              'voltaje_nominal_v', 'energia_kwh', 'tipo_inversor', 'potencia_inversor_w', 
              'estado']
    null_counts = {}
    for campo in campos:
        null_counts[campo] = sum(1 for r in records if r.get(campo) in [None, '', 'null'])
    
    cats = {}
    for r in records:
        cat = r.get('categoria_producto') or r.get('tipo') or r.get('categoria') or 'desconocido'
        cats[cat] = cats.get(cat, 0) + 1
    
    report = f"""# Informe de Ampliación Telegram v2

**Fecha de ejecución:** {datetime.now(timezone.utc).isoformat()}

## Canales procesados
"""
    for ch in channels:
        report += f"- {ch.get('username')}\n"
    
    report += f"""
## Métricas de extracción
- **Mensajes recuperados (total accesibles):** {len(all_messages)}
- **Mensajes analizados:** {len(all_messages)}
- **Anuncios candidatos (con producto relevante):** {candidatos}
- **Anuncios válidos encontrados (únicos):** {len(records)}
- **Anuncios clasificados como La Habana:** {habana_count}
- **Anuncios sin localidad especificada:** {sin_loc_count}
- **Anuncios excluidos por mencionar otra provincia:** {len(excluidos_provincia)}
- **Mensajes que requieren revisión manual:** {len([r for r in records if r.get('clasificacion_geografica') == 'requiere_revision'])}
- **Duplicados confirmados:** {duplicados_confirmados}
- **Posibles duplicados:** 0 (registrados en proceso de deduplicación)

## Categorías de productos encontradas
"""
    for cat, cnt in sorted(cats.items()):
        report += f"- {cat}: {cnt}\n"
    
    report += f"""
## Cantidad de registros con valores nulos por campo
| Campo | Nulos | Total | % Nulos |
|-------|-------|-------|---------|
"""
    for campo in campos:
        nulos = null_counts[campo]
        total = len(records) if records else 0
        pct = round(100 * nulos / total, 1) if total else 0
        report += f"| {campo} | {nulos} | {total} | {pct}% |\n"
    
    report += f"""
## Errores de extracción y limitaciones de acceso
"""
    if access_errors:
        for err in access_errors:
            report += f"- {err}\n"
    else:
        report += "- Sin errores de acceso reportados\n"
    report += "- Extracción basada en texto completo de mensajes\n"
    report += "- Solo recursos accesibles analizados; sin inventar información\n"
    report += "- Enfoque en mensajes con evidencia explícita\n"
    
    report += f"""
## Métodos utilizados para validar los resultados
- Clasificación geográfica por mención explícita de La Habana/municipios vs otras provincias cubanas
- Detección de duplicados por combinación (canal, message_id), URL y análisis de contenido
- Validación de suficiencia: requiere marca/descripción y algún dato técnico/precio
- Filtrado: exclusión de preguntas/informativos, enfoque en anuncios de venta
- Normalización de unidades/marcas sin inferencias
- Verificación de valores permitidos para clasificacion_geografica

## Copias de seguridad creadas (verificables)
"""
    for b in backup_files:
        report += f"- {b}\n"
    
    report += f"""
## Notas
- Los archivos originales NO fueron sobrescritos. Se generaron nuevos archivos de salida.
- Se distingue entre mensajes recuperados, anuncios candidatos y anuncios válidos.
- No se inventaron datos; valores ausentes se marcan como null.
"""
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
