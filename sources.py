"""
sources.py
==========
Catálogo de fuentes y su **estado legal** para decidir qué datos se pueden
reutilizar en el proyecto.

Para cada fuente se indica:
    * ``tipo``            : clasificados / datos abiertos / editorial-comercial
    * ``nivel_anuncio``   : si contiene anuncios a nivel de listado (precio, marca…)
    * ``reutilizacion``   : si se pueden reutilizar sus datos y bajo qué licencia
    * ``automatizacion``  : si el acceso automatizado está permitido
    * ``detalle``         : evidencia (condiciones, robots.txt, licencia)

Es una ficha informativa: no descarga nada por sí sola. El objetivo es dejar por
escrito **por qué** no se recopilan anuncios automáticamente y **qué alternativas**
sí son legítimas.

Aviso: la situación legal puede cambiar; revisa siempre los términos vigentes de
cada sitio antes de reutilizar sus datos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# ADVERTENCIA: referencia orientativa, no asesoría legal.


@dataclass(frozen=True)
class Fuente:
    nombre: str
    url: str
    tipo: str
    nivel_anuncio: bool
    reutilizacion: str
    automatizacion: str
    detalle: str

    @property
    def reutilizable(self) -> bool:
        """¿La licencia permite reutilizar los datos sin pedir permiso?"""
        return self.reutilizacion.startswith("SI")


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------
FUENTES: tuple[Fuente, ...] = (
    Fuente(
        nombre="Revolico",
        url="https://www.revolico.com",
        tipo="clasificados",
        nivel_anuncio=True,
        reutilizacion="NO (requiere autorización previa y por escrito)",
        automatizacion="No permitido reproducir/procesar contenido de terceros",
        detalle=(
            "robots.txt permite /search, PERO las Condiciones de uso prohíben "
            "'copiar, procesar o distribuir el texto y/o las fotos o imágenes de "
            "terceros sin su previa autorización' (norma 12) y usar herramientas de "
            "publicación/renovación masiva sin consentimiento escrito (norma 11). "
            "Condiciones: https://help.revolico.com/es/articles/7263759-condiciones-de-uso "
            "(consultadas el 2026-10-15)."
        ),
    ),
    Fuente(
        nombre="Banco Mundial - Datos abiertos",
        url="https://data.worldbank.org/",
        tipo="datos abiertos",
        nivel_anuncio=False,
        reutilizacion="SÍ - licencia abierta CC BY 4.0",
        automatizacion="Sí (API pública, sin clave)",
        detalle="Estadísticas agregadas por país (electricidad, energía, economía). "
        "No contiene anuncios ni precios de venta de paneles.",
    ),
    Fuente(
        nombre="IRENA - Renewable Energy Statistics",
        url="https://www.irena.org/Data",
        tipo="datos abiertos",
        nivel_anuncio=False,
        reutilizacion="SÍ - licencia abierta CC BY 4.0",
        automatizacion="Sí (API PxWeb pública https://pxweb.irena.org + descarga)",
        detalle="Capacidad y generación renovable por país. No contiene anuncios.",
    ),
    Fuente(
        nombre="Global Solar Atlas (Banco Mundial)",
        url="https://globalsolaratlas.info/",
        tipo="datos abiertos",
        nivel_anuncio=False,
        reutilizacion="SÍ - licencia abierta CC BY 4.0",
        automatizacion="Descarga de conjuntos publicados",
        detalle="Recurso solar y potencial fotovoltaico por ubicación. No contiene anuncios.",
    ),
    Fuente(
        nombre="UN Comtrade",
        url="https://comtrade.un.org/",
        tipo="datos abiertos",
        nivel_anuncio=False,
        reutilizacion="SÍ - datos abiertos de Naciones Unidas",
        automatizacion="Sí (API), pero Cuba no reporta la partida de paneles",
        detalle="Se comprobó que para Cuba no hay filas de importación en las "
        "partidas de células/paneles fotovoltaicos (HS 8541) en los periodos probados.",
    ),
    Fuente(
        nombre="TecnoSolar Cuba (termómetro de precios)",
        url="https://tecnosolarcuba.com/precios-paneles-solares-cuba",
        tipo="editorial-comercial",
        nivel_anuncio=False,
        reutilizacion="No sin permiso (no declara licencia abierta)",
        automatizacion="No recomendado",
        detalle="Sitio comercial cubano que publica MEDIANAS agregadas de 'los "
        "anuncios de venta' publicados, no los anuncios originales. Es una fuente "
        "secundaria con derechos de autor y sin API ni licencia abierta. "
        "Comprobado el 2026-10-15.",
    ),
    Fuente(
        nombre="Prensa/tutoriales (Directorio Cubano, d-cuba, electro-habana…)",
        url="https://www.directoriocubano.info/",
        tipo="editorial-comercial",
        nivel_anuncio=False,
        reutilizacion="No sin permiso (contenido con derechos de autor)",
        automatizacion="No recomendado",
        detalle="Publican rangos de precios en artículos, no listados estructurados; "
        "sirven para citar/contrastar, no para construir un dataset reutilizable.",
    ),
    Fuente(
        nombre="Marketplace de redes sociales (Facebook y similares)",
        url="https://www.facebook.com/marketplace/",
        tipo="clasificados",
        nivel_anuncio=True,
        reutilizacion="No sin permiso; además sin acceso automatizado autorizado",
        automatizacion="No (solo Meta Content Library para investigadores aprobados)",
        detalle="No existe API pública para este uso. La 'Meta Content Library & "
        "API' (que abarca Facebook Marketplace) está restringida a investigadores "
        "aprobados de instituciones acreditadas, no para reutilización comercial, "
        "y sus términos prohíben la recopilación automatizada por terceros.",
    ),
)

# Campos de la tabla-resumen
CAMPOS_RESUMEN = ("nombre", "tipo", "nivel_anuncio", "reutilizacion", "automatizacion")


def get_sources() -> tuple[Fuente, ...]:
    """Devuelve el catálogo de fuentes."""
    return FUENTES


def reusable_sources() -> list[Fuente]:
    """Fuentes cuyos datos se pueden reutilizar legalmente (con atribución)."""
    return [f for f in FUENTES if f.reutilizacion.startswith("SÍ")]


def ad_level_sources() -> list[Fuente]:
    """Fuentes que contienen anuncios a nivel de listado (precio, marca, modelo...)."""
    return [f for f in FUENTES if f.nivel_anuncio]


def render_sources(fuentes: Iterable[Fuente] = FUENTES) -> str:
    """Devuelve una tabla de texto legible con el estado de cada fuente."""
    lineas: list[str] = []
    ancho = max((len(f.nombre) for f in fuentes), default=10)
    for fuente in fuentes:
        marca = "ANUNCIOS" if fuente.nivel_anuncio else "contexto"
        lineas.append(f"* {fuente.nombre.ljust(ancho)}  [{marca}]")
        lineas.append(f"    tipo            : {fuente.tipo}")
        lineas.append(f"    reutilizacion   : {fuente.reutilizacion}")
        lineas.append(f"    automatizacion  : {fuente.automatizacion}")
        lineas.append(f"    url             : {fuente.url}")
        lineas.append(f"    detalle         : {fuente.detalle}")
    return "\n".join(lineas)
