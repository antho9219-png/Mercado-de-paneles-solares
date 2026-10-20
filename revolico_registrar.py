"""
revolico_registrar.py
=====================
Incorpora anuncios **verificados** de Revolico a ``revolico.json`` y evita
duplicados. Es la vía autorizada de **registro manual / plantilla**: la persona
transcribe un anuncio que consultó legítimamente (p. ej. como usuario normal del
sitio) y lo registra aquí.

Respeto a las condiciones de uso de Revolico
--------------------------------------------
* **No hace scraping** ni ninguna petición de red a Revolico.
* Solo registra anuncios que una persona incorpora manualmente de forma
  autorizada. No se copia contenido de terceros de forma masiva ni automatizada.
* No publica información personal del vendedor ni más datos de los necesarios.

Reglas de datos
---------------
* Esquema único de **12 campos** por registro (compartido con ``revolico_json.py``).
* ``url_anuncio`` conserva el enlace a la fuente para verificar la procedencia.
* Se usa ``null`` para todo valor desconocido; **nunca** se inventa.
* ``fecha_extraccion`` es la fecha real en que se registra el anuncio (por
  defecto, hoy). ``fecha_publicacion`` es la fecha original del anuncio; si no
  se conoce, queda ``null`` y **no** se sustituye por la de extracción.
* Se conserva la moneda original del precio.

Uso
---
    python revolico_registrar.py validar                     # valida revolico.json
    python revolico_registrar.py list                        # muestra los registros
    python revolico_registrar.py add --interactive           # modo guiado
    python revolico_registrar.py add --id 57503108 --marca AIKO \
        --potencia 660 --precio 145 --moneda USD --municipio "Plaza de la Revolución" \
        --url-anuncio "https://revolico.com/..."
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

from revolico_json import (
    SCHEMA_FIELDS,
    _a_numero,
    _compactar_numero,
    _fecha_iso,
    _limpiar,
)

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_FILE = PROJECT_ROOT / "revolico.json"

# Esquema único de 12 campos, compartido con revolico_json.py (fuente de verdad).
CAMPOS: tuple[str, ...] = SCHEMA_FIELDS

ESTADOS_VALIDOS = ("nuevo", "usado", "reacondicionado", "no_especificado")

_CAMPO_AYUDA = {
    "id": "Identificador único del anuncio (p. ej. el id de Revolico).",
    "marca": "Fabricante del panel.",
    "modelo": "Modelo específico del panel.",
    "potencia": "Potencia nominal en vatios (W).",
    "precio": "Precio anunciado, con su moneda original.",
    "municipio": "Municipio de La Habana.",
    "garantia": "Duración de la garantía indicada por el vendedor.",
    "vida_util": "Vida útil indicada explícitamente en el anuncio.",
    "estado": "nuevo | usado | reacondicionado | no_especificado",
    "fecha_publicacion": "Fecha original del anuncio (AAAA-MM-DD) o null.",
    "fecha_extraccion": "Fecha en que se registra (AAAA-MM-DD).",
    "url_anuncio": "Enlace al anuncio original para verificar su procedencia.",
}


# ---------------------------------------------------------------------------
# E/S
# ---------------------------------------------------------------------------
def cargar(ruta: Path) -> list[dict]:
    """Lee el JSON; devuelve lista vacía si el archivo está vacío."""
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    texto = ruta.read_text(encoding="utf-8").strip()
    if not texto:
        return []
    datos = json.loads(texto)
    if not isinstance(datos, list):
        raise ValueError(f"{ruta} debe contener una lista JSON de anuncios.")
    return datos


def guardar(records: list[dict], ruta: Path) -> Path:
    """Escribe los registros como JSON válido (UTF-8, sin escapar acentos)."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return ruta


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------
def validar(records: list[dict]) -> list[str]:
    """Devuelve una lista de problemas (vacía si todo es correcto)."""
    problemas: list[str] = []
    ids: set[str] = set()
    firmas: set[tuple] = set()

    for i, rec in enumerate(records, start=1):
        etiqueta = f"registro #{i} (id={rec.get('id')!r})"

        faltantes = [c for c in CAMPOS if c not in rec]
        if faltantes:
            problemas.append(f"{etiqueta}: faltan campos {faltantes}")
            continue

        extra = [c for c in rec if c not in CAMPOS]
        if extra:
            problemas.append(f"{etiqueta}: campos fuera del esquema {extra}")

        # id único
        rid = _limpiar(rec.get("id"))
        if rid:
            if rid in ids:
                problemas.append(f"{etiqueta}: id duplicado")
            ids.add(rid)

        # potencia numérica
        potencia = rec.get("potencia")
        if potencia is not None and not isinstance(potencia, (int, float)):
            problemas.append(f"{etiqueta}: 'potencia' debe ser numérica o null")

        # precio: objeto con valor numérico y moneda texto
        precio = rec.get("precio")
        if not isinstance(precio, dict) or set(precio) != {"valor", "moneda"}:
            problemas.append(
                f"{etiqueta}: 'precio' debe ser un objeto {{'valor', 'moneda'}}"
            )
        else:
            if precio.get("valor") is not None and not isinstance(
                precio["valor"], (int, float)
            ):
                problemas.append(f"{etiqueta}: precio.valor debe ser numérico o null")
            if precio.get("moneda") is not None and not isinstance(
                precio["moneda"], str
            ):
                problemas.append(f"{etiqueta}: precio.moneda debe ser texto o null")

        # estado
        if rec.get("estado") not in ESTADOS_VALIDOS:
            problemas.append(
                f"{etiqueta}: 'estado' inválido {rec.get('estado')!r} "
                f"(use uno de {list(ESTADOS_VALIDOS)})"
            )

        # fechas
        fpub = rec.get("fecha_publicacion")
        if fpub is not None and _fecha_iso(fpub) != fpub:
            problemas.append(
                f"{etiqueta}: 'fecha_publicacion' debe ser AAAA-MM-DD o null"
            )
        fext = rec.get("fecha_extraccion")
        if not fext or _fecha_iso(fext) != fext:
            problemas.append(f"{etiqueta}: 'fecha_extraccion' debe ser AAAA-MM-DD")

        # duplicado exacto (mismo contenido con id desconocido)
        firma = (
            rid,
            _limpiar(rec.get("marca")),
            _limpiar(rec.get("modelo")),
            potencia,
            (precio or {}).get("valor") if isinstance(precio, dict) else None,
            (precio or {}).get("moneda") if isinstance(precio, dict) else None,
            _limpiar(rec.get("municipio")),
        )
        if firma in firmas:
            problemas.append(f"{etiqueta}: registro duplicado (mismo contenido)")
        firmas.add(firma)

    return problemas


# ---------------------------------------------------------------------------
# Construcción de un registro
# ---------------------------------------------------------------------------
def _precio(valor: Any, moneda: Any) -> dict:
    """Construye el objeto precio conservando la moneda original."""
    numero = _compactar_numero(_a_numero(valor))
    mon = _limpiar(moneda)
    return {"valor": numero, "moneda": mon}


def construir_registro(args: argparse.Namespace) -> dict:
    """Crea el registro de 12 campos a partir de los argumentos, sin inventar."""
    fext = _limpiar(getattr(args, "fecha_extraccion", None)) or date.today().isoformat()
    return {
        "id": _limpiar(args.id),
        "marca": _limpiar(args.marca),
        "modelo": _limpiar(args.modelo),
        "potencia": _compactar_numero(_a_numero(args.potencia)),
        "precio": _precio(args.precio, args.moneda),
        "municipio": _limpiar(args.municipio),
        "garantia": _limpiar(args.garantia),
        "vida_util": _limpiar(args.vida_util),
        "estado": (args.estado or "no_especificado").strip().lower(),
        "fecha_publicacion": _fecha_iso(args.fecha_publicacion),
        "fecha_extraccion": _fecha_iso(fext) or date.today().isoformat(),
        "url_anuncio": _limpiar(getattr(args, "url_anuncio", None)),
    }


def es_duplicado(registro: dict, existentes: list[dict]) -> bool:
    """True si el registro ya existe (por id o por contenido idéntico)."""
    rid = _limpiar(registro.get("id"))
    for rec in existentes:
        if rid and _limpiar(rec.get("id")) == rid:
            return True
    # Sin id coincidente: comparar por firma de contenido
    for rec in existentes:
        if all(rec.get(c) == registro.get(c) for c in CAMPOS if c != "fecha_extraccion"):
            return True
    return False


# ---------------------------------------------------------------------------
# Modo interactivo
# ---------------------------------------------------------------------------
def _leer_interactivo() -> dict:
    """Pregunta campo por campo; vacío -> null."""
    print("Registro interactivo (deje vacío para dejar en null):")
    valores: dict[str, Optional[str]] = {}
    for campo in CAMPOS:
        if campo == "fecha_extraccion":
            por_defecto = date.today().isoformat()
            respuesta = input(f"  {campo} [{por_defecto}]: ").strip()
            valores[campo] = respuesta or por_defecto
        elif campo == "estado":
            print(f"  opciones de estado: {', '.join(ESTADOS_VALIDOS)}")
            respuesta = input(f"  {campo} [no_especificado]: ").strip()
            valores[campo] = respuesta or "no_especificado"
        else:
            valores[campo] = input(f"  {campo}: ").strip() or None

    class _Args:  # contenedor simple
        pass

    args = _Args()
    args.id = valores["id"]
    args.marca = valores["marca"]
    args.modelo = valores["modelo"]
    args.potencia = valores["potencia"]
    args.precio = valores["precio"]
    args.moneda = None
    args.municipio = valores["municipio"]
    args.garantia = valores["garantia"]
    args.vida_util = valores["vida_util"]
    args.estado = valores["estado"]
    args.fecha_publicacion = valores["fecha_publicacion"]
    args.fecha_extraccion = valores["fecha_extraccion"]
    args.url_anuncio = valores["url_anuncio"]
    return construir_registro(args)


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------
def cmd_add(args: argparse.Namespace) -> int:
    ruta = Path(args.archivo)
    existentes = cargar(ruta)

    registro = _leer_interactivo() if args.interactive else construir_registro(args)

    # Validar el candidato por separado antes de mezclarlo
    problemas = validar([registro])
    if problemas:
        print("El registro no es válido:", file=sys.stderr)
        for p in problemas:
            print(f"  - {p}", file=sys.stderr)
        return 3

    if es_duplicado(registro, existentes):
        print(
            f"Duplicado detectado (id={registro['id']!r}): no se añade. "
            "Use --forzar para añadirlo de todos modos.",
            file=sys.stderr,
        )
        return 2

    existentes.append(registro)
    guardar(existentes, ruta)
    print(f"Añadido. Total de anuncios en {ruta}: {len(existentes)}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    ruta = Path(args.archivo)
    records = cargar(ruta)
    if not records:
        print(f"{ruta}: sin anuncios registrados todavía (0).")
        return 0
    print(f"{ruta}: {len(records)} anuncio(s)")
    for r in records:
        precio = r.get("precio") or {}
        print(
            f"  - id={r.get('id')} {r.get('marca') or '?'} "
            f"{r.get('potencia') or '?'}W "
            f"{precio.get('valor') if precio.get('valor') is not None else '?'} "
            f"{precio.get('moneda') or ''} [{r.get('municipio') or '?'}] "
            f"estado={r.get('estado')} f.pub={r.get('fecha_publicacion')}"
        )
    return 0


def cmd_validar(args: argparse.Namespace) -> int:
    ruta = Path(args.archivo)
    try:
        records = cargar(ruta)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"JSON inválido: {exc}", file=sys.stderr)
        return 1
    problemas = validar(records)
    print(f"{ruta}: {len(records)} registro(s)")
    if problemas:
        print("PROBLEMAS:", file=sys.stderr)
        for p in problemas:
            print(f"  - {p}", file=sys.stderr)
        return 3
    print("Validación: OK")
    return 0


def _add_campos_add(p: argparse.ArgumentParser) -> None:
    p.add_argument("--archivo", default=str(DEFAULT_FILE), help="Ruta del JSON.")
    p.add_argument("-i", "--interactive", action="store_true",
                   help="Pregunta los campos uno a uno.")
    p.add_argument("--id", help="Identificador único del anuncio.")
    p.add_argument("--marca", help="Fabricante.")
    p.add_argument("--modelo", help="Modelo.")
    p.add_argument("--potencia", help="Potencia en vatios (W).")
    p.add_argument("--precio", help="Valor numérico del precio.")
    p.add_argument("--moneda", help="Moneda original (USD, CUP, MLC, EUR).")
    p.add_argument("--municipio", help="Municipio de La Habana.")
    p.add_argument("--garantia", help="Garantía anunciada.")
    p.add_argument("--vida-util", dest="vida_util", help="Vida útil anunciada.")
    p.add_argument("--estado", help="nuevo|usado|reacondicionado|no_especificado")
    p.add_argument("--fecha-publicacion", dest="fecha_publicacion",
                   help="Fecha original (AAAA-MM-DD); si se omite, null.")
    p.add_argument("--fecha-extraccion", dest="fecha_extraccion",
                   help="Fecha de registro (AAAA-MM-DD); por defecto, hoy.")
    p.add_argument("--url-anuncio", dest="url_anuncio",
                   help="Enlace al anuncio original para verificar la procedencia.")
    p.add_argument("--forzar", action="store_true",
                   help="Añade aunque detecte duplicado.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Registra anuncios verificados de Revolico en revolico.json "
        "(sin scraping, evitando duplicados).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Añade un anuncio verificado.")
    _add_campos_add(p_add)
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="Muestra los anuncios registrados.")
    p_list.add_argument("--archivo", default=str(DEFAULT_FILE))
    p_list.set_defaults(func=cmd_list)

    p_val = sub.add_parser("validar", help="Valida el JSON y su esquema.")
    p_val.add_argument("--archivo", default=str(DEFAULT_FILE))
    p_val.set_defaults(func=cmd_validar)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "add" and args.forzar:
        # --forzar omite la comprobación de duplicados
        global es_duplicado  # noqa: PLW0603
        es_duplicado = lambda *a, **k: False  # type: ignore[assignment]

    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
