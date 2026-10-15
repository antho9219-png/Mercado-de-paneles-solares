"""
main.py
=======
Punto de entrada del programa (interfaz de línea de comandos).

Subcomandos disponibles:
    diagnose   Explica por qué se recopilan (o no) anuncios reales.
    scrape     Ejecuta el scraping AUTORIZADO (desactivado por defecto).
    import     Importa anuncios desde CSV/JSON obtenidos legítimamente.
    template   Crea una plantilla CSV para aportar datos propios autorizados.
    analyze    Muestra estadísticas y calidad de los datos.
    visualize  Genera gráficos PNG (opcional, requiere matplotlib).

Ejemplos:
    python main.py diagnose                 # ¿por qué hay 0 anuncios reales?
    python main.py diagnose --online        # además comprueba robots.txt y el sitio
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
    Escribe una plantilla CSV con las columnas de entrega (en español).

    Sirve para que el usuario aporte sus propios datos autorizados
    (por ejemplo, exportados a mano de una fuente con permiso) e importarlos
    con ``python main.py import --input <archivo>``.
    """
    from storage import records_to_spanish_dataframe

    columns = list(SPANISH_COLUMNS.values())
    path = Path(args.output)
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

    p_tpl = sub.add_parser(
        "template",
        help="Crea una plantilla CSV (columnas en español) para importar tus datos.",
    )
    p_tpl.add_argument(
        "--output", default="plantilla_anuncios.csv", help="Ruta del CSV a crear."
    )
    p_tpl.set_defaults(func=cmd_template)

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
