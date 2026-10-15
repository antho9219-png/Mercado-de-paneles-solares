"""Pruebas de la solicitud de autorización por escrito (``solicitud``)."""

from config import Config
from main import build_parser, cmd_solicitud
from permisos import contacto_para, render_solicitud, save_solicitud


def _cfg(tmp_path):
    return Config(
        data_dir=tmp_path / "data",
        out_dir=tmp_path / "out",
        log_dir=tmp_path / "logs",
    )


class TestCarta:
    def test_menciona_el_sitio(self):
        assert "revolico.com" in render_solicitud(sitio="revolico.com")

    def test_no_inventa_identidad(self):
        texto = render_solicitud(sitio="revolico.com")
        assert "[COMPLETAR: nombre" in texto
        assert "[COMPLETAR: correo" in texto

    def test_completa_campos_conocidos(self):
        texto = render_solicitud(
            sitio="revolico.com",
            solicitante="Ana Pérez",
            email="ana@ejemplo.org",
            institucion="Estudiante",
        )
        assert "Ana Pérez" in texto
        assert "ana@ejemplo.org" in texto
        assert "Estudiante" in texto
        assert "[COMPLETAR: nombre" not in texto
        assert "[COMPLETAR: correo" not in texto

    def test_pide_autorizacion_por_escrito(self):
        texto = render_solicitud(sitio="revolico.com").lower()
        assert "autorización" in texto
        assert "por escrito" in texto

    def test_promete_respetar_robots(self):
        assert "robots.txt" in render_solicitud(sitio="revolico.com")

    def test_uso_y_alcance_personalizados(self):
        texto = render_solicitud(sitio="x.com", uso="docencia", alcance="solo precios")
        assert "docencia" in texto
        assert "solo precios" in texto

    def test_contacto_conocido_y_desconocido(self):
        assert "help.revolico.com" in contacto_para("revolico.com")
        assert contacto_para("otro-sitio.com").endswith("otro-sitio.com")
        assert contacto_para("") == ""

    def test_save_escribe_archivo(self, tmp_path):
        destino = tmp_path / "sub" / "carta.txt"
        ruta = save_solicitud(destino, sitio="revolico.com", solicitante="Ana")
        assert ruta == destino
        assert "Ana" in destino.read_text(encoding="utf-8")


class TestComandoSolicitud:
    def test_imprime_por_defecto(self, tmp_path, capsys):
        args = build_parser().parse_args(["solicitud", "--solicitante", "Ana"])
        codigo = cmd_solicitud(args, _cfg(tmp_path))
        salida = capsys.readouterr().out
        assert codigo == 0
        assert "Asunto" in salida
        assert "Ana" in salida
        assert "revolico.com" in salida

    def test_escribe_archivo_con_output(self, tmp_path, capsys):
        destino = tmp_path / "solicitud.txt"
        args = build_parser().parse_args(["solicitud", "--output", str(destino)])
        codigo = cmd_solicitud(args, _cfg(tmp_path))
        assert codigo == 0
        assert destino.exists()
        assert "revolico.com" in destino.read_text(encoding="utf-8")
        assert "Solicitud escrita" in capsys.readouterr().out
