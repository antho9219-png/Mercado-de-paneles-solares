"""
diagnostics.py
==============
Diagnóstico del proyecto: comprueba dependencias, configuración, estado de la
recopilación y — si se pide explícitamente — accesibilidad **en línea** al sitio.

Sirve para responder con claridad a la pregunta:
    "¿por qué el programa recopila 0 anuncios reales?"

No recopila datos por sí mismo ni inventa nada. Las comprobaciones en línea son
**opt-in** (``online=True``) y realizan un máximo de 2 peticiones corteses.
"""

from __future__ import annotations

import importlib
import logging
import os
import platform
import shutil
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Optional

from config import Config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Modelo de resultado
# ---------------------------------------------------------------------------
@dataclass
class Check:
    """Resultado de una comprobación concreta."""

    nombre: str
    estado: str  # "OK" | "INFO" | "AVISO" | "ERROR"
    detalle: str


# (módulo importable, paquete pip, ¿es imprescindible?)
_DEPENDENCIAS = (
    ("requests", "requests", True),
    ("bs4", "beautifulsoup4", True),
    ("pandas", "pandas", True),
    ("numpy", "numpy", True),
    ("matplotlib", "matplotlib", False),
    ("seaborn", "seaborn", False),
    ("pytest", "pytest", False),
    ("nbformat", "nbformat", False),
)


def _version(paquete: str) -> str:
    try:
        return metadata.version(paquete)
    except Exception:  # pragma: no cover - defensivo
        return "?"


# ---------------------------------------------------------------------------
# Comprobaciones sin red
# ---------------------------------------------------------------------------
def _find_git() -> Optional[str]:
    """Localiza ``git`` en el PATH o en las ubicaciones típicas de Windows."""
    found = shutil.which("git")
    if found:
        return found
    candidatos = (
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Git\cmd\git.exe"),
    )
    for candidato in candidatos:
        if Path(candidato).exists():
            return candidato
    return None


def _check_entorno() -> list[Check]:
    git = _find_git()
    repo = Path(__file__).resolve().parent / ".git"
    return [
        Check(
            "python",
            "OK",
            f"{platform.python_version()} ({platform.system()} {platform.release()})",
        ),
        Check(
            "git",
            "OK" if git else "INFO",
            f"instalado ({git})" if git else "no encontrado",
        ),
        Check(
            "git:repositorio",
            "OK" if repo.exists() else "INFO",
            "inicializado (.git presente)"
            if repo.exists()
            else "sin repositorio local (ejecuta 'git init -b main')",
        ),
    ]


def _check_dependencias() -> list[Check]:
    checks: list[Check] = []
    for modulo, paquete, requerido in _DEPENDENCIAS:
        try:
            importlib.import_module(modulo)
            checks.append(Check(f"dep:{paquete}", "OK", f"instalado ({_version(paquete)})"))
        except ImportError:
            checks.append(
                Check(
                    f"dep:{paquete}",
                    "ERROR" if requerido else "AVISO",
                    "NO instalado" + ("" if requerido else " (opcional)"),
                )
            )
    return checks


def _check_config(config: Config) -> list[Check]:
    checks = [
        Check("cfg:base_url", "INFO", config.base_url),
        Check("cfg:search_url", "INFO", config.search_url),
        Check("cfg:province", "INFO", config.province),
        Check("cfg:request_delay", "INFO", f"{config.request_delay} s entre peticiones"),
        Check("cfg:max_pages", "INFO", str(config.max_pages)),
        Check("cfg:max_items", "INFO", str(config.max_items)),
        Check("cfg:respect_robots", "INFO", str(config.respect_robots)),
        Check("cfg:search_terms", "INFO", ", ".join(config.search_terms)),
    ]
    return checks


def _check_puerta(config: Config) -> list[Check]:
    """Estado de la autorización que habilita el scraping."""
    checks: list[Check] = []
    if config.scraper_enabled:
        checks.append(Check("gate:SCRAPER_ENABLED", "OK", "activado"))
    else:
        checks.append(
            Check(
                "gate:SCRAPER_ENABLED",
                "AVISO",
                "desactivado (define SCRAPER_ENABLED=true para activarlo)",
            )
        )
    if config.authorization_confirmed:
        checks.append(Check("gate:AUTHORIZATION_CONFIRMED", "OK", "confirmado"))
    else:
        checks.append(
            Check(
                "gate:AUTHORIZATION_CONFIRMED",
                "AVISO",
                "sin confirmar (define AUTHORIZATION_CONFIRMED=true solo con autorización)",
            )
        )
    return checks


def _check_directorios(config: Config) -> list[Check]:
    return [
        Check(f"dir:{ruta.name}", "OK" if Path(ruta).exists() else "AVISO",
              str(ruta))
        for ruta in (config.data_dir, config.raw_dir, config.processed_dir,
                     config.out_dir, config.log_dir)
    ]


def _check_datos(config: Config) -> list[Check]:
    """¿Qué hay en el CSV procesado? ¿Son datos reales o de ejemplo?"""
    path = Path(config.processed_csv_path)
    if not path.exists():
        return [
            Check(
                "datos:procesado",
                "AVISO",
                f"no existe {path} (ejecuta 'python main.py import --input <archivo>')",
            )
        ]
    try:
        import pandas as pd

        frame = pd.read_csv(path, dtype=str)
    except Exception as exc:  # pragma: no cover - defensivo
        return [Check("datos:procesado", "ERROR", f"no se pudo leer {path}: {exc}")]

    checks = [Check("datos:procesado", "OK", f"{len(frame)} registros en {path}")]
    if "fuente" in frame.columns:
        fuentes = frame["fuente"].fillna("(desconocido)").value_counts().to_dict()
        solo_ejemplo = all(str(f).lower() == "ejemplo" for f in fuentes)
        reales = sum(v for f, v in fuentes.items() if str(f).lower() != "ejemplo")
        checks.append(
            Check(
                "datos:fuente",
                "AVISO" if solo_ejemplo else "OK",
                ", ".join(f"{k}={v}" for k, v in fuentes.items()),
            )
        )
        checks.append(
            Check(
                "datos:reales",
                "OK" if reales else "AVISO",
                f"{reales} registros con fuente distinta de 'ejemplo'",
            )
        )
        if not reales:
            checks.append(
                Check(
                    "datos:aviso",
                    "AVISO",
                    "TODOS los registros son de EJEMPLO (sintéticos), no anuncios reales: "
                    "usa 'python main.py add' o 'python main.py import'",
                )
            )
    return checks


# ---------------------------------------------------------------------------
# Comprobaciones en línea (opt-in)
# ---------------------------------------------------------------------------
def _check_online(config: Config, term: str) -> list[Check]:
    from parser import ParseError, parse_search_page
    from scraper.revolico_scraper import (
        HTTPAccessError,
        RevolicoScraper,
        RobotsDisallowed,
        ScraperError,
    )

    checks: list[Check] = []
    # Se construye el cliente directamente (sin la puerta de autorización) porque
    # solo se comprueba accesibilidad; no se recopilan datos.
    scraper = RevolicoScraper(config)

    # 1) robots.txt
    try:
        parser = scraper._robots_parser()  # noqa: SLF001 (uso deliberado)
        allowed = parser.can_fetch(config.user_agent, config.search_url)
        checks.append(
            Check(
                "online:robots.txt",
                "OK",
                f"descargado; /search {'PERMITIDO' if allowed else 'BLOQUEADO'} para nuestro user-agent",
            )
        )
    except Exception as exc:  # pragma: no cover - depende de red
        checks.append(Check("online:robots.txt", "ERROR", f"no se pudo leer: {exc}"))
        return checks

    if not allowed:
        checks.append(
            Check("online:search", "ERROR", "robots.txt prohíbe /search; no se continúa")
        )
        return checks

    # 2) Una única petición de búsqueda para comprobar estructura y respuesta.
    try:
        html = scraper.get_html(config.search_url, params={"q": term, "page": 1})
    except RobotsDisallowed as exc:
        checks.append(Check("online:search", "ERROR", f"robots.txt: {exc}"))
        return checks
    except HTTPAccessError as exc:
        checks.append(Check("online:search", "ERROR", f"error HTTP: {exc}"))
        return checks
    except ScraperError as exc:
        checks.append(Check("online:search", "ERROR", f"error del scraper: {exc}"))
        return checks

    checks.append(Check("online:search", "OK", f"respuesta recibida ({len(html)} caracteres)"))

    # 3) ¿El parser encuentra anuncios en la respuesta?
    try:
        records = parse_search_page(html)
    except ParseError as exc:
        checks.append(
            Check(
                "online:parse",
                "ERROR",
                f"la estructura de la página cambió o no es la esperada: {exc}",
            )
        )
        return checks

    if not records:
        checks.append(
            Check(
                "online:parse",
                "AVISO",
                "no se encontraron anuncios (posible cambio de estructura o sin resultados)",
            )
        )
        return checks

    provincias = {}
    for record in records:
        provincias[record.get("province") or "(desconocida)"] = (
            provincias.get(record.get("province") or "(desconocida)", 0) + 1
        )
    detalle = ", ".join(f"{k}={v}" for k, v in provincias.items())
    checks.append(
        Check("online:parse", "OK", f"{len(records)} anuncios parseados; provincias: {detalle}")
    )
    return checks


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------
def explicar_bloqueo(config: Config) -> Optional[str]:
    """Devuelve el motivo por el que el scraping no está habilitado, o ``None``."""
    motivos = []
    if not config.scraper_enabled:
        motivos.append("el scraper está DESACTIVADO (SCRAPER_ENABLED no es 'true')")
    if not config.authorization_confirmed:
        motivos.append(
            "la autorización NO está confirmada (AUTHORIZATION_CONFIRMED no es 'true')"
        )
    if not motivos:
        return None
    return "No se recopilan anuncios porque " + " y ".join(motivos) + "."


def run_diagnostics(config: Config, online: bool = False, term: str = "panel solar") -> list[Check]:
    """Ejecuta todas las comprobaciones y devuelve la lista de resultados."""
    checks: list[Check] = []
    checks.extend(_check_entorno())
    checks.extend(_check_dependencias())
    checks.extend(_check_config(config))
    checks.extend(_check_puerta(config))
    checks.extend(_check_directorios(config))
    checks.extend(_check_datos(config))
    if online:
        checks.extend(_check_online(config, term))
    return checks


def format_report(checks: list[Check], config: Config) -> str:
    """Da formato legible al informe de diagnóstico."""
    lineas = ["=" * 68, "DIAGNOSTICO DEL PROYECTO - MERCADO SOLAR LA HABANA", "=" * 68]
    ancho = max((len(c.nombre) for c in checks), default=10)
    for check in checks:
        lineas.append(f"  [{check.estado:5}] {check.nombre:<{ancho}}  {check.detalle}")

    errores = [c for c in checks if c.estado == "ERROR"]
    avisos = [c for c in checks if c.estado == "AVISO"]

    lineas.append("-" * 68)
    lineas.append(f"Resumen: {len(checks)} comprobaciones | {len(errores)} errores | {len(avisos)} avisos")

    motivo = explicar_bloqueo(config)
    lineas.append("")
    if motivo:
        lineas.append("POR QUE NO SE RECOPILAN ANUNCIOS AUTOMATICAMENTE:")
        lineas.append(f"  {motivo}")
        lineas.append("  Alternativas autorizadas para conseguir datos:")
        lineas.append("    * Registro manual: python main.py add --interactive")
        lineas.append("    * Importar CSV/JSON propio: python main.py import --input <archivo>")
        lineas.append("    * Plantilla de campos: python main.py template")
    else:
        lineas.append(
            "El scraping esta AUTORIZADO. Ejecuta: python main.py scrape --max-items 30"
        )

    if errores:
        lineas.append("")
        lineas.append("Errores que impiden la recopilacion:")
        for check in errores:
            lineas.append(f"  - {check.nombre}: {check.detalle}")

    if not any(c.nombre.startswith("online:") for c in checks):
        lineas.append("")
        lineas.append(
            "Nota: las comprobaciones de red no se ejecutaron. "
            "Anade --online para comprobar robots.txt y la estructura del sitio."
        )
    return "\n".join(lineas)
