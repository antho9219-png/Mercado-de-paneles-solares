"""
permisos.py
===========
Redacta una **solicitud de autorización por escrito** para pedir permiso y
reutilizar los datos (anuncios) de un sitio de clasificados.

Contexto
--------
El proyecto **no** automatiza la recopilación de anuncios porque las condiciones
de uso de los sitios de clasificados exigen autorización previa y por escrito
(p. ej. Revolico). Pedir esa autorización es la vía legítima para conseguir
anuncios reales a nivel de listado.

Este módulo es *offline*: **no** descarga, envía ni publica nada. Solo redacta un
borrador para que la persona lo revise, lo complete y lo envíe.

Reglas (coherentes con el resto del proyecto)
---------------------------------------------
* **No se inventa nada:** los campos no aportados quedan como ``[COMPLETAR: …]``.
* Se deja constancia del sitio, el uso previsto, el alcance y la fecha.
* La carta pide el consentimiento y ofrece atenerse a condiciones razonables
  (citar la fuente, respetar robots.txt y los límites de velocidad, etc.).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]

# Contacto orientativo por sitio (puede cambiar; revísalo antes de enviar).
# No se asume ninguna dirección de correo: se enlaza el centro de ayuda.
CONTACTOS: dict[str, str] = {
    "revolico.com": "https://help.revolico.com/",
    "tecnosolarcuba.com": "https://tecnosolarcuba.com/",
}

USO_POR_DEFECTO = "análisis del mercado de paneles solares en La Habana (Cuba)"
AMBITO_POR_DEFECTO = "municipios de La Habana, Cuba"
ALCANCE_POR_DEFECTO = (
    "reutilizar los campos de texto de los anuncios (precio, descripción, marca, "
    "modelo y ubicación) para un único análisis con fines académicos"
)


def _completar(valor: str | None, etiqueta: str) -> str:
    """Devuelve el valor o, si está vacío, un hueco ``[COMPLETAR: …]``."""
    texto = (valor or "").strip()
    return texto if texto else f"[COMPLETAR: {etiqueta}]"


def contacto_para(sitio: str) -> str:
    """Devuelve un enlace de contacto orientativo para ``sitio`` (o vacío)."""
    clave = (sitio or "").strip().lower()
    if not clave:
        return ""
    return CONTACTOS.get(clave, f"https://{clave}")


def render_solicitud(
    *,
    sitio: str = "revolico.com",
    solicitante: str | None = None,
    email: str | None = None,
    institucion: str | None = None,
    uso: str | None = None,
    alcance: str | None = None,
    ambito: str | None = None,
    fecha: date | None = None,
) -> str:
    """
    Devuelve el borrador de la carta (texto). No envía nada.

    Los campos no aportados quedan como ``[COMPLETAR: …]`` para **no inventar**
    datos de contacto ni de identidad.
    """
    sitio_limpio = (sitio or "el sitio").strip()
    valores = {
        "sitio": sitio_limpio,
        "uso": (uso or "").strip() or USO_POR_DEFECTO,
        "alcance": (alcance or "").strip() or ALCANCE_POR_DEFECTO,
        "ambito": _completar(ambito or AMBITO_POR_DEFECTO, "ámbito"),
        "solicitante": _completar(solicitante, "nombre y apellidos del solicitante"),
        "email": _completar(email, "correo de contacto"),
        "institucion": _completar(institucion, "institución o perfil (estudiante, ONG…)"),
        "fecha": (fecha or date.today()).isoformat(),
        "contacto": contacto_para(sitio) or f"[COMPLETAR: contacto de {sitio_limpio}]",
    }
    return _PLANTILLA.format(**valores)


def save_solicitud(path: PathLike, **kwargs) -> Path:
    """
    Escribe el borrador de la carta en ``path`` y devuelve la ruta.

    Acepta los mismos argumentos que :func:`render_solicitud`.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_solicitud(**kwargs), encoding="utf-8")
    return path


_PLANTILLA = """\
Asunto: Solicitud de autorización para reutilizar datos de anuncios

Estimado equipo de {sitio}:

Me dirijo a ustedes para pedir **autorización por escrito** para reutilizar
parte de la información publicada en sus anuncios.

  * Uso previsto: {uso}
  * Alcance de lo solicitado: {alcance}
  * Ámbito geográfico: {ambito}
  * Persona solicitante: {solicitante}
  * Institución/perfil: {institucion}
  * Correo de contacto: {email}
  * Fecha de la solicitud: {fecha}
  * Contacto de referencia: {contacto}

Me comprometo a:

  1. citar {sitio} como fuente y enlazar la página original de cada anuncio;
  2. no redistribuir textos ni fotografías de terceros más de lo imprescindible;
  3. respetar robots.txt, los límites de velocidad (rate limits) y no eludir
     ninguna medida de protección;
  4. eliminar los datos si ustedes lo solicitan.

Si lo consideran necesario, puedo aceptar condiciones adicionales o un permiso
limitado a determinadas categorías.

Quedo a la espera de su respuesta y agradezco de antemano su atención.

Saludos cordiales,
{solicitante}
"""
