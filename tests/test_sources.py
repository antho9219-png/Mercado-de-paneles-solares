"""Pruebas del catálogo de fuentes y su estado legal (comando ``fuentes``)."""

from config import Config
from main import build_parser, cmd_fuentes
from sources import (
    ad_level_sources,
    get_sources,
    render_sources,
    reusable_sources,
)


def _args(argv):
    return build_parser().parse_args(argv)


def _cfg(tmp_path):
    return Config(
        data_dir=tmp_path / "data",
        out_dir=tmp_path / "out",
        log_dir=tmp_path / "logs",
    )


class TestCatalogo:
    def test_hay_fuentes(self):
        assert len(get_sources()) >= 5

    def test_reutilizables_tienen_licencia(self):
        for fuente in reusable_sources():
            assert "SÍ" in fuente.reutilizacion

    def test_revolico_no_es_reutilizable(self):
        revolico = next(f for f in get_sources() if "Revolico" in f.nombre)
        assert revolico.nivel_anuncio is True
        assert not revolico.reutilizacion.startswith("SÍ")

    def test_fuentes_de_anuncios_declaradas(self):
        nombres = {f.nombre for f in ad_level_sources()}
        assert any("Revolico" in n for n in nombres)

    def test_render_menciona_licencia(self):
        texto = render_sources()
        assert "CC BY 4.0" in texto
        assert "ANUNCIOS" in texto


class TestComandoFuentes:
    def test_devuelve_cero(self, tmp_path, capsys):
        code = cmd_fuentes(_args(["fuentes"]), _cfg(tmp_path))
        assert code == 0
        salida = capsys.readouterr().out
        assert "FUENTES" in salida
        assert "Revolico" in salida
