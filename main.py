"""
main.py
=======
Punto de entrada del programa (interfaz de línea de comandos).

Subcomandos disponibles:
    diagnose   Explica por qué se recopilan (o no) anuncios reales.
    fuentes    Catálogo de fuentes y su estado legal (qué se puede reutilizar).
    opendata   Descarga datos ABIERTOS y reutilizables (contexto, no anuncios).
    scrape     Ejecuta el scraping AUTORIZADO (desactivado por defecto).
    import     Importa anuncios desde CSV/JSON obtenidos legítimamente.
    add        Registra manualmente UN anuncio (alternativa autorizada).
    registrar  Incorpora anuncios reales desde la plantilla CSV (valida y deduplica).
    template   Crea una plantilla CSV (con --anuncios, la de anuncios reales).
    analyze    Muestra estadísticas y calidad de los datos.
    visualize  Genera gráficos PNG (opcional, requiere matplotlib).

Ejemplos:
    python main.py diagnose                 # ¿por qué hay 0 anuncios reales?
    python main.py diagnose --online        # además comprueba robots.txt y el sitio
    python main.py fuentes                  # qué fuentes son reutilizables
    python main.py opendata                 # datos abiertos del Banco Mundial (Cuba)
    python main.py add -i                   # registrar un anuncio manualmente
    python main.py add --precio 250 --moneda USD --potencia "550 W" \
        --municipio Playa --tipo-producto "panel solar" --fuente registro_manual
    python main.py template                 # plantilla CSV para tus propios datos
    python main.py import --input data/examples/ejemplo_paneles_habana.csv
    python main.py analyze
    python main.py visualize
    python main.py scrape                    # requiere variables de autorización

Salidas:
    data/raw/paneles_solares_habana.csv            (datos crudos, en español)
    data/processed/paneles_solares_habana_limpio.csv (datos limpios)
    output/paneles_solares.csv|.json               (esquema interno, en inglés)

Este archivo solo coordina: la lógica vive en los demás módulos.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from analysis import (
    count_by,
    deduplicate,
    descriptive_statistics,
    find_duplicates,
    incompleteness_report,
    summarize,
)
from cleaner import clean_record
from config import Config, configure_logging
from diagnostics import format_report, run_diagnostics
from scraper import (
    RevolicoScraper,
    RobotsDisallowed,
    ScraperNotAuthorized,
    collect_habana_ads,
)
from storage import (
    SPANISH_COLUMNS,
    load_csv,
    load_records,
    save_csv,
    save_csv_spanish,
    save_json,
)

logger = logging.getLogger("main")


# ---------------------------------------------------------------------------
# Pipeline común
# ---------------------------------------------------------------------------
def process_raw_records(raw_records: Iterable[dict]) -> list[dict]:
    """
    Limpia, deduplica y sella registros.

    * Aplica ``clean_record`` (precios, potencias, municipios, textos).
    * Elimina duplicados por ID/URL.
    * Rellena ``collected_at`` con la fecha actual si falta.
    """
    cleaned = [clean_record(r) for r in raw_records]
    unique = deduplicate(cleaned)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for record in unique:
        if not record.get("collected_at"):
            record["collected_at"] = now
    return unique


def stamp_collection(records: list[dict]) -> list[dict]:
    """Añade la fecha de recopilación a los registros que no la tengan."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for record in records:
        if not record.get("collected_at"):
            record["collected_at"] = now
    return records


def save_raw(records: list[dict], config: Config) -> Path:
    """Guarda los datos crudos (columnas en español) en data/raw."""
    path = save_csv_spanish(records, config.raw_csv_path)
    logger.info("Datos crudos guardados en %s", path)
    return path


def save_processed(records: list[dict], config: Config) -> Path:
    """Guarda los datos limpios (columnas en español) en data/processed."""
    path = save_csv_spanish(records, config.processed_csv_path)
    logger.info("Datos procesados guardados en %s", path)
    return path


def save_outputs(records: list[dict], config: Config) -> tuple[Path, Path]:
    """Guarda los registros en CSV y JSON (esquema interno) y devuelve las rutas."""
    csv_path = save_csv(records, config.csv_path)
    json_path = save_json(records, config.json_path)
    logger.info("Guardados %d registros en %s y %s", len(records), csv_path, json_path)
    return csv_path, json_path


def load_inputs(paths: list[str]) -> list[dict]:
    """Carga y concatena registros de varios archivos CSV/JSON."""
    records: list[dict] = []
    for raw_path in paths:
        path = Path(raw_path)
        loaded = load_records(path)
        logger.info("Importados %d registros desde %s", len(loaded), path)
        records.extend(loaded)
    return records


# ---------------------------------------------------------------------------
# Subcomandos
# ---------------------------------------------------------------------------
def cmd_diagnose(args: argparse.Namespace, config: Config) -> int:
    """
    Explica con claridad por qué se recopilan (o no) anuncios reales.

    Sin red comprueba entorno, dependencias, configuración, la "puerta" de
    autorización y los datos presentes. Con ``--online`` hace, además, un
    máximo de 2 peticiones corteses para comprobar robots.txt y la estructura
    actual del sitio (sin recopilar ni guardar nada).
    """
    checks = run_diagnostics(config, online=bool(args.online), term=args.term)
    print(format_report(checks, config))
    # Código de salida informativo: 0 si no hay errores, 1 si los hay.
    return 0 if not any(c.estado == "ERROR" for c in checks) else 1


def cmd_template(args: argparse.Namespace, config: Config) -> int:
    """
    Escribe una plantilla CSV para registrar datos aportados por el usuario.

    Con ``--anuncios`` genera la plantilla de **anuncios reales** (11 columnas:
    ``fecha_consulta, precio, moneda, potencia_w, marca, modelo, vida_util,
    garantia, municipio, url_fuente, observaciones``), pensada para transcribir
    anuncios a mano. Sin ese flag genera la plantilla con todas las columnas de
    entrega, para importar con ``python main.py import --input <archivo>``.
    """
    if args.anuncios:
        from anuncios import COLUMNAS_ANUNCIOS, save_template

        path = Path(args.output) if args.output else Path("plantilla_anuncios_reales.csv")
        path = save_template(path)
        print(f"Plantilla de anuncios creada: {path}")
        print(f"Columnas ({len(COLUMNAS_ANUNCIOS)}): {', '.join(COLUMNAS_ANUNCIOS)}")
        print(
            "\nRellena una fila por anuncio real y deja vacío lo que no sepas.\n"
            "Cada fila NECESITA una fuente verificable en 'url_fuente'.\n"
            "Después ejecuta:\n"
            f"    python main.py registrar --input {path}"
        )
        print(
            "\nNota: solo incluye datos que tengas derecho a tratar. No añadas "
            "datos personales de terceros."
        )
        return 0

    from storage import records_to_spanish_dataframe

    columns = list(SPANISH_COLUMNS.values())
    path = Path(args.output) if args.output else Path("plantilla_anuncios.csv")
    path.parent.mkdir(parents=True, exist_ok=True)

    frame = records_to_spanish_dataframe([])  # cabecera vacía con el orden correcto
    frame.to_csv(path, index=False, encoding="utf-8-sig")

    print(f"Plantilla creada: {path}")
    print(f"Columnas ({len(columns)}): {', '.join(columns)}")
    print(
        "\nRellena una fila por anuncio respetando las columnas y luego ejecuta:\n"
        f"    python main.py import --input {path}"
    )
    print(
        "Nota: solo incluye datos que tengas derecho a tratar. No añadas "
        "datos personales de terceros."
    )
    return 0


def cmd_add(args: argparse.Namespace, config: Config) -> int:
    """
    Registra **manualmente** un anuncio (vía autorizada, sin scraping).

    Añade el registro al archivo crudo (``data/raw``) y regenera el archivo
    limpio (``data/processed/``). Solo guarda lo que el usuario aporta: no
    inventa ningún dato y etiqueta el origen con ``fuente``.
    """
    from manual import build_manual_record, has_data, prompt_record

    if args.interactive:
        record = prompt_record()
    else:
        record = build_manual_record(
            title=args.titulo,
            description=args.descripcion,
            price_raw=args.precio,
            currency=args.moneda,
            power_raw=args.potencia,
            power_w=args.potencia_w,
            brand=args.marca,
            modelo=args.modelo,
            product_type=args.tipo_producto,
            alcance=args.alcance,
            vida_util=args.vida_util,
            garantia=args.garantia,
            municipality=args.municipio,
            provincia=args.provincia,
            url=args.url,
            date_published=args.fecha_publicacion,
            ad_id=args.id,
            source=args.fuente,
            notes=args.observaciones,
        )

    if not has_data(record):
        print("Error: no indicaste ningún dato del anuncio.", file=sys.stderr)
        print(
            "Ejemplo:\n"
            "  python main.py add --precio 250 --moneda USD --potencia \"550 W\" \\\n"
            "      --marca Jinko --municipio Playa --tipo-producto \"panel solar\"\n"
            "Modo guiado: python main.py add --interactive",
            file=sys.stderr,
        )
        return 2

    existentes = load_csv(config.raw_csv_path) if Path(config.raw_csv_path).exists() else []
    crudos = deduplicate(stamp_collection(list(existentes) + [record]))
    procesados = process_raw_records(crudos)

    raw_path = save_raw(crudos, config)
    processed_path = save_processed(procesados, config)
    csv_path, json_path = save_outputs(procesados, config)

    print("=" * 60)
    print("REGISTRO MANUAL DE ANUNCIO")
    print("=" * 60)
    print(f"  Registro añadido    : {record.get('title') or record.get('price_raw') or '(sin título)'}")
    print(f"  Fuente              : {record.get('source')}")
    print(f"  Crudos (data/raw)   : {len(crudos)} registros -> {raw_path}")
    print(f"  Limpios (processed) : {len(procesados)} registros -> {processed_path}")
    print(f"  CSV/JSON            : {csv_path} | {json_path}")
    print("\n--- Registros por fuente (origen de los datos) ---")
    print(count_by(procesados, "source").to_string(index=False))
    print(
        "\nRecuerda: la fiabilidad del dato es la de su fuente. La columna "
        "'fuente' distingue el registro manual de los datos de ejemplo."
    )
    return 0


def cmd_registrar(args: argparse.Namespace, config: Config) -> int:
    """
    Incorpora **anuncios reales** desde la plantilla CSV de registro manual.

    Reglas:
        * Cada fila debe tener una **fuente verificable** (``url_fuente``); las
          que no la tengan se **rechazan** (nunca se inventa la fuente).
        * **No se duplican** anuncios: se comparan por URL/ID con los ya
          registrados y con el resto del archivo.
        * Los anuncios se guardan **solo** en ``data/raw`` y ``data/processed``;
          este comando nunca toca los datos abiertos energéticos.
    """
    from anuncios import is_verifiable_source, merge_anuncios, read_rows, row_to_record

    ruta = Path(args.input)
    try:
        filas = read_rows(ruta)
    except FileNotFoundError:
        print(f"Error: no existe el archivo {ruta}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if not filas:
        print(f"La plantilla {ruta} no contiene filas.", file=sys.stderr)
        return 1

    validos: list[dict] = []
    rechazados: list[dict] = []
    for indice, fila in enumerate(filas, start=2):  # la fila 1 es la cabecera
        if is_verifiable_source(fila.get("url_fuente")):
            validos.append(row_to_record(fila, source=args.fuente))
        else:
            rechazados.append(
                {"fila": indice, "url_fuente": fila.get("url_fuente") or ""}
            )

    existentes = (
        load_csv(config.raw_csv_path) if Path(config.raw_csv_path).exists() else []
    )
    crudos, duplicados = merge_anuncios(existentes, stamp_collection(validos))
    procesados = process_raw_records(crudos)

    print("=" * 60)
    print("REGISTRO MANUAL DE ANUNCIOS (desde plantilla)")
    print("=" * 60)
    print(f"  Plantilla             : {ruta}")
    print(f"  Filas leídas          : {len(filas)}")
    print(f"  Con fuente (aceptadas): {len(validos)}")
    print(f"  Sin fuente (rechazadas): {len(rechazados)}")
    print(f"  Duplicadas (ignoradas): {len(duplicados)}")

    if rechazados:
        print("\n--- Filas RECHAZADAS por no tener fuente verificable ---")
        for item in rechazados:
            print(f"  fila {item['fila']}: url_fuente = '{item['url_fuente']}'")
        print(
            "Añade la URL o el dominio donde viste el anuncio y vuelve a "
            "ejecutar 'registrar'."
        )

    if duplicados:
        print("\n--- Filas DUPLICADAS (ya registradas; se ignoran) ---")
        for record in duplicados:
            print(f"  {record.get('url') or record.get('ad_id') or '(sin URL)'}")

    if not validos:
        print(
            "\nNinguna fila tiene fuente verificable: no se registró ningún "
            "anuncio.",
            file=sys.stderr,
        )
        return 3

    raw_path = save_raw(crudos, config)
    processed_path = save_processed(procesados, config)
    csv_path, json_path = save_outputs(procesados, config)

    print(f"\n  Total anuncios : {len(procesados)} -> {processed_path}")
    print(f"  Crudos         : {raw_path}")
    print(f"  CSV/JSON       : {csv_path} | {json_path}")
    print("\n--- Anuncios por fuente (origen de los datos) ---")
    print(count_by(procesados, "source").to_string(index=False))
    print(
        "\nLos anuncios se guardan SOLO en data/raw y data/processed.\n"
        "Los datos abiertos (contexto) viven aparte: "
        f"{Path(config.opendata_csv_path).name}."
    )
    return 0


def cmd_fuentes(args: argparse.Namespace, config: Config) -> int:
    """Muestra el catálogo de fuentes y su estado legal de reutilización."""
    from sources import ad_level_sources, render_sources, reusable_sources

    print("=" * 70)
    print("FUENTES DE DATOS Y SU ESTADO LEGAL")
    print("=" * 70)
    print(render_sources())
    print("-" * 70)
    print(f"Fuentes reutilizables (con licencia abierta): {len(reusable_sources())}")
    print(f"Fuentes a nivel de anuncio (listados):        {len(ad_level_sources())}")
    print(
        "\nNinguna fuente de ANUNCIOS permite reutilizar su contenido sin "
        "autorización previa.\n"
        "  * Datos de anuncios  -> 'python main.py add' (manual) o 'import' (con permiso).\n"
        "  * Datos de contexto  -> 'python main.py opendata' (datos abiertos)."
    )
    return 0


def cmd_opendata(args: argparse.Namespace, config: Config) -> int:
    """
    Descarga datos ABIERTOS y reutilizables (contexto, no anuncios).

    Por defecto usa el API público del Banco Mundial (licencia CC BY 4.0) para
    Cuba y guarda un CSV con la fuente, la URL y la fecha de recopilación.
    """
    from opendata import fetch_world_bank, save_opendata_csv

    pais = args.pais or "CUB"
    destinos = args.indicator or None
    try:
        registros = fetch_world_bank(destinos, pais)
    except Exception as exc:  # red/servidor: se informa sin inventar datos
        print(f"Error al descargar datos abiertos: {exc}", file=sys.stderr)
        print(
            "Comprueba tu conexión a Internet. El Banco Mundial expone una API "
            "pública en https://api.worldbank.org.",
            file=sys.stderr,
        )
        return 1

    if not registros:
        print(
            "No se obtuvieron registros: el país o los indicadores no tienen datos "
            "publicados. No se ha creado ningún archivo.",
            file=sys.stderr,
        )
        return 1

    salida = Path(args.output) if args.output else config.opendata_csv_path
    ruta = save_opendata_csv(registros, salida)

    anios = sorted({str(r["anio"]) for r in registros if r.get("anio")})
    indicadores = sorted({r["indicador_id"] for r in registros})
    print("=" * 60)
    print("DATOS ABIERTOS (contexto, NO son anuncios)")
    print("=" * 60)
    print(f"  Fuente        : {registros[0]['fuente']} (licencia {registros[0]['licencia']})")
    print(f"  Pais          : {registros[0]['pais']} ({pais})")
    print(f"  Indicadores   : {len(indicadores)} -> {', '.join(indicadores)}")
    print(f"  Registros     : {len(registros)} (años {anios[0]}..{anios[-1]})")
    print(f"  Archivo       : {ruta}")
    print(
        "\nAviso: son estadísticas agregadas del país (electricidad, energía, "
        "economía).\nNO contienen anuncios, precios, marcas ni modelos de paneles."
    )
    return 0


def cmd_import(args: argparse.Namespace, config: Config) -> int:
    """Importa datos desde CSV/JSON (vía autorizada, sin scraping)."""
    if not args.input:
        print("Error: indica al menos un archivo con --input.", file=sys.stderr)
        return 2

    raw = stamp_collection(load_inputs(args.input))
    if not raw:
        print("No se encontraron registros en los archivos indicados.", file=sys.stderr)
        return 1

    records = process_raw_records(raw)
    print(f"Registros importados: {len(raw)}  ->  únicos tras limpieza: {len(records)}")
    print_incomplete(records)

    if not args.no_save:
        raw_path = save_raw(raw, config)
        processed_path = save_processed(records, config)
        csv_path, json_path = save_outputs(records, config)
        print(f"Crudos     : {raw_path}")
        print(f"Procesados : {processed_path}")
        print(f"CSV/JSON   : {csv_path} | {json_path}")
    return 0


def cmd_scrape(args: argparse.Namespace, config: Config) -> int:
    """Ejecuta el scraping autorizado (o informa de por qué no puede)."""
    try:
        scraper = RevolicoScraper.from_config(config)
    except ScraperNotAuthorized as exc:
        print("\n[SCRAPING NO HABILITADO]", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        print(
            "\nEsto es intencional por defecto (protege los términos del sitio).\n"
            "Para ver un diagnóstico completo ejecuta:\n"
            "    python main.py diagnose\n"
            "Para importar datos que tengas autorización a usar:\n"
            "    python main.py import --input <archivo.csv|archivo.json>\n",
            file=sys.stderr,
        )
        return 3

    if args.terms:
        config.search_terms = list(args.terms)
    if args.max_items is not None:
        config.max_items = args.max_items

    try:
        result = collect_habana_ads(config, scraper)
    except RobotsDisallowed as exc:
        print(f"\n[robots.txt] {exc}", file=sys.stderr)
        return 4

    print("=" * 60)
    print(f"REGISTRO DE EJECUCIÓN (provincia: {config.province})")
    print("=" * 60)
    for key, value in result.summary().items():
        print(f"  {key:28}: {value}")
    for error in result.errors:
        logger.warning("Incidencia: %s", error)

    if not result.records:
        if result.errors:
            print("\nNo se pudo recopilar ningún anuncio (ver errores).", file=sys.stderr)
            print(
                "Sugiere: python main.py diagnose --online\n"
                "         (comprueba red, robots.txt y estructura actual del sitio)",
                file=sys.stderr,
            )
            return 5
        print("No se encontraron anuncios para los términos indicados.")
        print("Sugerencia: python main.py diagnose --online")
        return 0

    records = process_raw_records(result.records)
    print_incomplete(records)
    raw_path = save_raw(result.records, config)
    processed_path = save_processed(records, config)
    csv_path, json_path = save_outputs(records, config)
    print(f"Crudos     : {raw_path}")
    print(f"Procesados : {processed_path}")
    print(f"CSV/JSON   : {csv_path} | {json_path}")
    return 0


def cmd_analyze(args: argparse.Namespace, config: Config) -> int:
    """Carga datos y muestra estadísticas y calidad."""
    paths = args.input or default_existing_paths(config)
    if not paths:
        print(
            "No hay datos para analizar. Usa --input o ejecuta primero 'import'.",
            file=sys.stderr,
        )
        return 1

    raw = load_inputs(paths)
    records = process_raw_records(raw)

    summary = summarize(records)
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    for key, value in summary.items():
        print(f"  {key:16}: {value}")

    duplicates = find_duplicates([clean_record(r) for r in raw])
    print(f"\nDuplicados detectados (antes de deduplicar): {len(duplicates)}")

    print("\n--- Registros incompletos (campos obligatorios) ---")
    print(incompleteness_report(records).to_string(index=False))

    print("\n--- Estadísticas de precio por moneda (sin conversión) ---")
    print(descriptive_statistics(records).to_string(index=False))

    print("\n--- Anuncios por tipo de producto ---")
    print(count_by(records, "product_type").to_string(index=False))

    print("\n--- Anuncios por alcance (panel vs sistema) ---")
    print(count_by(records, "alcance").to_string(index=False))

    print("\n--- Anuncios por municipio (top 15) ---")
    print(count_by(records, "municipality", top=15).to_string(index=False))

    print("\n--- Anuncios por ubicación (top 10) ---")
    print(count_by(records, "location", top=10).to_string(index=False))
    return 0


def cmd_visualize(args: argparse.Namespace, config: Config) -> int:
    """Genera gráficos a partir de los datos disponibles."""
    try:
        from visualization import generate_all_plots
    except ImportError as exc:  # matplotlib ausente
        print(f"No se pueden generar gráficos: {exc}", file=sys.stderr)
        return 1

    paths = args.input or default_existing_paths(config)
    if not paths:
        print("No hay datos para graficar. Usa --input.", file=sys.stderr)
        return 1

    records = process_raw_records(load_inputs(paths))
    created = generate_all_plots(records, config.out_dir)
    if not created:
        print("No se generó ningún gráfico (faltan datos suficientes).")
        return 0
    for path in created:
        print(f"Gráfico generado: {path}")
    return 0


def print_incomplete(records: list[dict]) -> None:
    """Imprime un breve aviso si hay registros incompletos."""
    report = incompleteness_report(records)
    if not report.empty and report["faltantes"].sum() > 0:
        print("Aviso: hay registros con campos obligatorios vacíos:")
        print(report.to_string(index=False))


def default_existing_paths(config: Config) -> list[str]:
    """Devuelve las rutas de datos existentes, priorizando el CSV procesado."""
    for candidate in (config.processed_csv_path, config.csv_path, config.json_path):
        if Path(candidate).exists():
            return [str(candidate)]
    return []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solar-scraper",
        description="Recopilación y análisis del mercado de paneles solares en La Habana.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_diag = sub.add_parser(
        "diagnose",
        help="Diagnostica por qué se recopilan (o no) anuncios reales.",
    )
    p_diag.add_argument(
        "--online",
        action="store_true",
        help="Comprueba también robots.txt y la estructura actual del sitio (2 peticiones).",
    )
    p_diag.add_argument(
        "--term", default="panel solar", help="Término de búsqueda para la prueba en línea."
    )
    p_diag.set_defaults(func=cmd_diagnose)

    p_fuentes = sub.add_parser(
        "fuentes",
        help="Muestra las fuentes de datos y su estado legal de reutilización.",
    )
    p_fuentes.set_defaults(func=cmd_fuentes)

    p_open = sub.add_parser(
        "opendata",
        help="Descarga datos ABIERTOS y reutilizables (contexto, no anuncios).",
    )
    p_open.add_argument(
        "--indicator",
        action="append",
        default=None,
        help="Indicador del Banco Mundial (repetible). Por defecto, un conjunto para Cuba.",
    )
    p_open.add_argument("--pais", default="CUB", help="Código ISO3 del país (por defecto, CUB).")
    p_open.add_argument(
        "--output",
        default=None,
        help="CSV de salida (por defecto data/raw/opendata_banco_mundial.csv).",
    )
    p_open.set_defaults(func=cmd_opendata)

    p_tpl = sub.add_parser(
        "template",
        help="Crea una plantilla CSV: anuncios reales (--anuncios) o datos a importar.",
    )
    p_tpl.add_argument(
        "--anuncios",
        action="store_true",
        help="Plantilla de anuncios reales (11 columnas) para registrar a mano.",
    )
    p_tpl.add_argument("--output", default=None, help="Ruta del CSV a crear.")
    p_tpl.set_defaults(func=cmd_template)

    p_add = sub.add_parser(
        "add",
        help="Registra manualmente un anuncio (vía autorizada, sin scraping).",
    )
    p_add.add_argument("-i", "--interactive", action="store_true",
                       help="Pregunta los campos uno a uno por consola.")
    p_add.add_argument("--titulo", help="Título del anuncio.")
    p_add.add_argument("--descripcion", help="Descripción (texto del vendedor).")
    p_add.add_argument("--precio", help="Precio anunciado (texto o número).")
    p_add.add_argument("--moneda", help="Moneda del precio (USD, CUP, MLC, EUR).")
    p_add.add_argument("--potencia", help="Potencia tal como se anuncia (p. ej. '550 W').")
    p_add.add_argument(
        "--potencia-w", dest="potencia_w", type=float, default=None,
        help="Potencia en vatios (número).",
    )
    p_add.add_argument("--marca", help="Marca.")
    p_add.add_argument("--modelo", help="Modelo.")
    p_add.add_argument("--vida-util", dest="vida_util", help="Vida útil anunciada.")
    p_add.add_argument("--garantia", help="Garantía anunciada.")
    p_add.add_argument("--municipio", help="Municipio de La Habana.")
    p_add.add_argument("--provincia", default=None, help="Provincia (por defecto, derivada).")
    p_add.add_argument("--tipo-producto", dest="tipo_producto", help="Tipo de producto.")
    p_add.add_argument("--alcance", help="Alcance del precio (panel individual, sistema...).")
    p_add.add_argument("--url", help="URL del anuncio (opcional).")
    p_add.add_argument(
        "--observaciones", help="Observaciones del investigador (opcional)."
    )
    p_add.add_argument(
        "--fecha-publicacion", dest="fecha_publicacion", help="Fecha de publicación (opcional)."
    )
    p_add.add_argument("--id", default=None, help="Identificador propio (opcional).")
    p_add.add_argument(
        "--fuente", default="registro_manual", help="Fuente de los datos (columna 'fuente')."
    )
    p_add.set_defaults(func=cmd_add)

    p_reg = sub.add_parser(
        "registrar",
        help="Incorpora anuncios reales desde la plantilla CSV (valida fuente y duplicados).",
    )
    p_reg.add_argument(
        "--input", required=True, help="CSV con la plantilla de anuncios rellenada."
    )
    p_reg.add_argument(
        "--fuente",
        default="registro_manual",
        help="Fuente de los datos (columna 'fuente').",
    )
    p_reg.set_defaults(func=cmd_registrar)

    p_scrape = sub.add_parser("scrape", help="Scraping autorizado (desactivado por defecto).")
    p_scrape.add_argument("--terms", nargs="*", help="Términos de búsqueda a usar.")
    p_scrape.add_argument(
        "--max-items", type=int, default=None, help="Máximo de anuncios a recopilar."
    )
    p_scrape.set_defaults(func=cmd_scrape)

    p_import = sub.add_parser("import", help="Importa anuncios desde CSV/JSON.")
    p_import.add_argument(
        "--input", nargs="+", action="extend", required=True,
        help="Archivos CSV/JSON (puedes repetir --input o pasar varios).",
    )
    p_import.add_argument("--no-save", action="store_true", help="No exportar resultados.")
    p_import.set_defaults(func=cmd_import)

    p_analyze = sub.add_parser("analyze", help="Estadísticas y calidad de datos.")
    p_analyze.add_argument(
        "--input", nargs="+", action="extend", help="Archivos CSV/JSON a analizar."
    )
    p_analyze.set_defaults(func=cmd_analyze)

    p_viz = sub.add_parser("visualize", help="Genera gráficos PNG (opcional).")
    p_viz.add_argument(
        "--input", nargs="+", action="extend", help="Archivos CSV/JSON a graficar."
    )
    p_viz.set_defaults(func=cmd_visualize)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = Config.from_env()
    configure_logging(config)

    try:
        return int(args.func(args, config))
    except KeyboardInterrupt:  # pragma: no cover
        print("\nInterrumpido por el usuario.", file=sys.stderr)
        return 130
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
