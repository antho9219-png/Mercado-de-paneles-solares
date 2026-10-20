"""
revolico_json.py
================
Genera ``revolico.json`` con anuncios reales de Revolico (La Habana, Cuba) ya
registrados legítimamente en el proyecto, usando el esquema de 12 campos
solicitado, con validación previa a la escritura.

Por qué no hace scraping aquí
-----------------------------
Las Condiciones de uso de Revolico (norma 12) prohíben copiar, procesar o
distribuir el texto de anuncios de terceros sin autorización previa y por
escrito. Aunque ``robots.txt`` permite ``/search``, las condiciones son el
límite aplicable. El proyecto lo documenta en ``sources.py`` y
``docs/investigacion_fuentes_anuncios.md``, y por eso el scraper real
(``scraper/``) está **desactivado por defecto** y exige a la vez
``SCRAPER_ENABLED=true`` y ``AUTHORIZATION_CONFIRMED=true``.

Este módulo, por tanto, **no realiza ninguna petición de red**. Produce
``revolico.json`` a partir de los anuncios que ya fueron incorporados por las
vías autorizadas (transcripción manual o registro autorizado). Para conseguir
permiso de la fuente, el proyecto genera un borrador con ``python main.py
solicitud``.

Reglas aplicadas (sin inventar nada)
------------------------------------
* ``fecha_publicacion`` se toma del dato registrado; si Revolico no expone la
  fecha, queda ``null``. **Nunca** se sustituye por la fecha de extracción.
* ``fecha_extraccion`` es la fecha real de recopilación del anuncio.
* Los campos desconocidos quedan en ``null``; no se completan por suposición.
* Se conserva la moneda original del precio.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from config import Config
from storage import load_csv

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PROJECT_ROOT / "revolico.json"

# Esquema solicitado para cada registro de revolico.json.
SCHEMA_FIELDS: tuple[str, ...] = (
    "id",
    "marca",
    "modelo",
    "potencia",
    "precio",
    "municipio",
    "garantia",
    "vida_util",
    "estado",
    "fecha_publicacion",
    "fecha_extraccion",
    "url_anuncio",
)

ESTADOS_VALIDOS = {"nuevo", "usado", "reacondicionado", "no_especificado"}

# Detección conservadora del estado del producto a partir del texto del anuncio.
# Solo se acepta si aparece una palabra inequívoca; en caso contrario,
# "no_especificado". No se infiere nada de la longitud, el precio ni el contexto.
_ESTADO_PATRONES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("reacondicionado", re.compile(r"\b(reacondicionad[oa]s?|refurbish(ed)?)\b", re.I)),
    ("usado", re.compile(r"\b(usad[oa]s?|segunda mano)\b", re.I)),
    ("nuevo", re.compile(r"\b(nuev[oa]s?|sin usar|0 horas)\b", re.I)),
)


def _obtener(ad: dict, *claves: str) -> Any:
    """Devuelve el primer valor no vacío entre las claves indicadas.

    ``load_csv`` devuelve las claves internas en inglés (``ad_id``, ``source``…),
    mientras que el CSV en disco usa nombres en español. Este buscador permite
    trabajar con cualquiera de los dos esquemas.
    """
    for clave in claves:
        valor = ad.get(clave)
        if _limpiar(valor) is not None:
            return valor
    return None


def _limpiar(valor: Any) -> Optional[str]:
    """Devuelve el texto sin espacios o ``None`` si está vacío/no numérico."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto or texto.lower() in {"nan", "none", "null"}:
        return None
    return texto


def _a_numero(valor: Any) -> Optional[float]:
    """Convierte un valor a número; devuelve ``None`` si no es numérico."""
    texto = _limpiar(valor)
    if texto is None:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def _compactar_numero(valor: Optional[float]) -> Optional[float]:
    """Devuelve ``int`` cuando el número es entero (p. ej. 660.0 -> 660)."""
    if valor is None:
        return None
    return int(valor) if float(valor).is_integer() else valor


def _fecha_iso(valor: Any) -> Optional[str]:
    """Normaliza una fecha a ``AAAA-MM-DD`` o ``None`` si es desconocida."""
    texto = _limpiar(valor)
    if texto is None:
        return None
    # Formato completo ISO 8601 (p. ej. 2026-10-16T21:22:47+00:00)
    try:
        return datetime.fromisoformat(texto.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass
    # Ya en formato AAAA-MM-DD
    try:
        return date.fromisoformat(texto).isoformat()
    except ValueError:
        return None


def detectar_estado(*textos: Any) -> str:
    """Clasifica el estado del producto de forma conservadora."""
    bloqueado = " ".join(t for t in (_limpiar(x) for x in textos) if t)
    if not bloqueado:
        return "no_especificado"
    for estado, patron in _ESTADO_PATRONES:
        if patron.search(bloqueado):
            return estado
    return "no_especificado"


def mapear_anuncio(ad: dict) -> dict:
    """
    Convierte un anuncio registrado (columnas en español) al esquema de 12
    campos de ``revolico.json``, sin inventar valores.
    """
    precio_valor = _compactar_numero(_a_numero(_obtener(ad, "price_value", "precio_valor")))
    moneda = _limpiar(_obtener(ad, "currency", "moneda"))
    potencia = _compactar_numero(_a_numero(_obtener(ad, "power_w", "potencia_w")))
    fecha_recop = _fecha_iso(_obtener(ad, "collected_at", "fecha_recopilacion"))

    return {
        "id": _limpiar(_obtener(ad, "ad_id", "id_anuncio")),
        "marca": _limpiar(_obtener(ad, "brand", "marca")),
        "modelo": _limpiar(_obtener(ad, "modelo")),
        "potencia": potencia,
        "precio": {
            "valor": precio_valor,
            "moneda": moneda,
        },
        "municipio": _limpiar(_obtener(ad, "municipality", "municipio")),
        "garantia": _limpiar(_obtener(ad, "garantia")),
        "vida_util": _limpiar(_obtener(ad, "vida_util")),
        "estado": detectar_estado(
            _obtener(ad, "description", "descripcion"),
            _obtener(ad, "title", "titulo"),
        ),
        # La fecha de publicación solo procede del dato registrado; si la fuente
        # no la expone, queda null. Nunca se usa la fecha de extracción.
        "fecha_publicacion": _fecha_iso(
            _obtener(ad, "date_published", "fecha_publicacion")
        ),
        "fecha_extraccion": fecha_recop,
        "url_anuncio": _limpiar(_obtener(ad, "url", "url_anuncio")),
    }


def es_anuncio_de_panel(ad: dict) -> bool:
    """Filtra publicaciones que no correspondan a paneles solares."""
    tipo = (_limpiar(_obtener(ad, "product_type", "tipo_producto")) or "").lower()
    titulo = (_limpiar(_obtener(ad, "title", "titulo")) or "").lower()
    return "panel" in tipo or "panel" in titulo or "fotovoltaic" in titulo


def cargar_anuncios_reales(config: Config, fuente: str = "revolico") -> list[dict]:
    """
    Carga los anuncios registrados por la fuente indicada desde el CSV
    procesado (datos reales, no ejemplos).
    """
    ruta = config.processed_csv_path
    if not ruta.exists():
        ruta = config.raw_csv_path
    if not ruta.exists():
        return []

    registros = load_csv(ruta)
    seleccionados = []
    for ad in registros:
        origen = (_limpiar(_obtener(ad, "source", "fuente")) or "").lower()
        if fuente and fuente not in origen:
            continue
        if not es_anuncio_de_panel(ad):
            continue
        seleccionados.append(ad)
    return seleccionados


def deduplicar(records: Iterable[dict]) -> list[dict]:
    """Elimina duplicados usando el identificador y la URL, en ese orden."""
    vistos_ids: set[str] = set()
    vistos_urls: set[str] = set()
    unicos: list[dict] = []
    for rec in records:
        rid = rec.get("id")
        url = rec.get("url_anuncio")
        if rid and rid in vistos_ids:
            continue
        if url and url in vistos_urls:
            continue
        if rid:
            vistos_ids.add(rid)
        if url:
            vistos_urls.add(url)
        unicos.append(rec)
    return unicos


def validar(records: list[dict]) -> list[str]:
    """Valida la estructura y los tipos antes de escribir el JSON."""
    problemas: list[str] = []
    ids_vistos: set[str] = set()
    urls_vistas: set[str] = set()

    for i, rec in enumerate(records, start=1):
        etiqueta = f"registro #{i} (id={rec.get('id')!r})"

        faltantes = [c for c in SCHEMA_FIELDS if c not in rec]
        if faltantes:
            problemas.append(f"{etiqueta}: faltan campos {faltantes}")
            continue

        extra = [c for c in rec if c not in SCHEMA_FIELDS]
        if extra:
            problemas.append(f"{etiqueta}: campos fuera del esquema {extra}")

        rid = rec.get("id")
        if not rid or not isinstance(rid, str):
            problemas.append(f"{etiqueta}: 'id' debe ser una cadena no vacía")
        elif rid in ids_vistos:
            problemas.append(f"{etiqueta}: id duplicado")
        else:
            ids_vistos.add(rid)

        potencia = rec.get("potencia")
        if potencia is not None and not isinstance(potencia, (int, float)):
            problemas.append(f"{etiqueta}: 'potencia' debe ser numérica o null")

        precio = rec.get("precio")
        if not isinstance(precio, dict):
            problemas.append(f"{etiqueta}: 'precio' debe ser un objeto")
        else:
            valor = precio.get("valor")
            if valor is not None and not isinstance(valor, (int, float)):
                problemas.append(f"{etiqueta}: precio.valor debe ser numérico o null")
            moneda = precio.get("moneda")
            if moneda is not None and not isinstance(moneda, str):
                problemas.append(f"{etiqueta}: precio.moneda debe ser texto o null")

        if rec.get("estado") not in ESTADOS_VALIDOS:
            problemas.append(
                f"{etiqueta}: 'estado' inválido {rec.get('estado')!r} "
                f"(debe ser uno de {sorted(ESTADOS_VALIDOS)})"
            )

        fpub = rec.get("fecha_publicacion")
        if fpub is not None:
            if not isinstance(fpub, str) or _fecha_iso(fpub) != fpub:
                problemas.append(
                    f"{etiqueta}: 'fecha_publicacion' debe ser AAAA-MM-DD o null"
                )

        fext = rec.get("fecha_extraccion")
        if not fext or _fecha_iso(fext) != fext:
            problemas.append(
                f"{etiqueta}: 'fecha_extraccion' debe ser AAAA-MM-DD válida"
            )
        elif fpub and fpub > fext:
            problemas.append(
                f"{etiqueta}: 'fecha_publicacion' ({fpub}) es posterior a "
                f"'fecha_extraccion' ({fext})"
            )

        url = rec.get("url_anuncio")
        if not url or not isinstance(url, str) or not url.startswith("http"):
            problemas.append(f"{etiqueta}: 'url_anuncio' debe ser una URL válida")
        elif url in urls_vistas:
            problemas.append(f"{etiqueta}: url duplicada")
        else:
            urls_vistas.add(url)

    return problemas


def construir_records(config: Config, fuente: str) -> list[dict]:
    """Carga, mapea y deduplica los anuncios reales de la fuente indicada."""
    anuncios = cargar_anuncios_reales(config, fuente=fuente)
    records = [mapear_anuncio(ad) for ad in anuncios]
    return deduplicar(records)


def generar(
    output: Path = DEFAULT_OUTPUT,
    fuente: str = "revolico",
    config: Optional[Config] = None,
) -> tuple[Path, list[dict], list[str]]:
    """Construye, valida y escribe ``revolico.json``. Devuelve (ruta, datos, problemas)."""
    config = config or Config.from_env()
    records = construir_records(config, fuente=fuente)
    problemas = validar(records)

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    return output, records, problemas


def _informe(records: list[dict]) -> None:
    total = len(records)
    con_fecha = sum(1 for r in records if r["fecha_publicacion"])
    sin_fecha = total - con_fecha
    print(f"Anuncios encontrados : {total}")
    print(f"Anuncios guardados   : {total}")
    print(f"Con fecha publicacion: {con_fecha}")
    print(f"Fecha publicacion nula: {sin_fecha}")
    for r in records:
        estado = r["fecha_publicacion"] or "null"
        print(
            f"  - id={r['id']} {r['marca'] or '?'} "
            f"{r['potencia'] or '?'}W "
            f"{(r['precio']['valor'] if r['precio']['valor'] is not None else '?')} "
            f"{r['precio']['moneda'] or ''} "
            f"[{r['municipio'] or '?'}] f.publicacion={estado}"
        )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera revolico.json con anuncios reales ya registrados "
        "(sin scraping).",
    )
    parser.add_argument(
        "--output", default=str(DEFAULT_OUTPUT), help="Ruta de salida del JSON."
    )
    parser.add_argument(
        "--fuente", default="revolico", help="Filtrar por la columna 'fuente'."
    )
    args = parser.parse_args(argv)

    ruta, records, problemas = generar(
        output=Path(args.output), fuente=args.fuente
    )

    print(f"Archivo escrito: {ruta}")
    _informe(records)

    if problemas:
        print("\nPROBLEMAS DE VALIDACION:", file=sys.stderr)
        for p in problemas:
            print(f"  - {p}", file=sys.stderr)
        return 3
    print("Validacion: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
