"""Pruebas del diagnóstico (explica por qué se recopilan 0 anuncios reales)."""

import pytest

from config import Config
from diagnostics import (
    Check,
    explicar_bloqueo,
    format_report,
    run_diagnostics,
)
from storage import SPANISH_COLUMNS

# Ninguna prueba de esta serie debe tocar la red.
pytestmark = pytest.mark.filterwarnings("ignore")


def _nombres(checks):
    return {c.nombre for c in checks}


class TestRunDiagnosticsOffline:
    def test_no_hace_peticiones_red_por_defecto(self, tmp_path):
        checks = run_diagnostics(Config(data_dir=tmp_path), online=False)
        assert not any(c.nombre.startswith("online:") for c in checks)

    def test_incluye_comprobaciones_esenciales(self, tmp_path):
        checks = run_diagnostics(Config(data_dir=tmp_path), online=False)
        nombres = _nombres(checks)
        assert "python" in nombres
        assert "gate:SCRAPER_ENABLED" in nombres
        assert "gate:AUTHORIZATION_CONFIRMED" in nombres
        assert "dep:requests" in nombres
        assert "dep:beautifulsoup4" in nombres
        assert "dep:pandas" in nombres

    def test_dependencias_imprescindibles_ok(self, tmp_path):
        checks = run_diagnostics(Config(data_dir=tmp_path), online=False)
        imprescindibles = [c for c in checks if c.nombre.startswith("dep:")]
        requeridas = {"dep:requests", "dep:beautifulsoup4", "dep:pandas", "dep:numpy"}
        for check in imprescindibles:
            if check.nombre in requeridas:
                assert check.estado == "OK", f"{check.nombre} debe estar instalado"

    def test_puerta_desactivada_por_defecto(self, tmp_path):
        checks = run_diagnostics(Config(data_dir=tmp_path), online=False)
        puerta = {c.nombre: c for c in checks if c.nombre.startswith("gate:")}
        assert puerta["gate:SCRAPER_ENABLED"].estado == "AVISO"
        assert puerta["gate:AUTHORIZATION_CONFIRMED"].estado == "AVISO"

    def test_puerta_activada_si_configurada(self, tmp_path):
        cfg = Config(data_dir=tmp_path, scraper_enabled=True, authorization_confirmed=True)
        checks = run_diagnostics(cfg, online=False)
        puerta = {c.nombre: c for c in checks if c.nombre.startswith("gate:")}
        assert puerta["gate:SCRAPER_ENABLED"].estado == "OK"
        assert puerta["gate:AUTHORIZATION_CONFIRMED"].estado == "OK"

    def test_datos_ausentes_se_reportan(self, tmp_path):
        checks = run_diagnostics(Config(data_dir=tmp_path), online=False)
        datos = {c.nombre: c for c in checks if c.nombre.startswith("datos:")}
        assert datos["datos:procesado"].estado == "AVISO"

    def test_estados_validos(self, tmp_path):
        checks = run_diagnostics(Config(data_dir=tmp_path), online=False)
        assert checks, "debe haber al menos una comprobación"
        assert {c.estado for c in checks} <= {"OK", "INFO", "AVISO", "ERROR"}


class TestExplicarBloqueo:
    def test_bloqueo_por_defecto(self):
        motivo = explicar_bloqueo(Config())
        assert motivo is not None
        assert "SCRAPER_ENABLED" in motivo
        assert "AUTHORIZATION_CONFIRMED" in motivo

    def test_sin_bloqueo_si_autorizado(self):
        cfg = Config(scraper_enabled=True, authorization_confirmed=True)
        assert explicar_bloqueo(cfg) is None

    def test_bloqueo_parcial_si_solo_una_bandera(self):
        cfg = Config(scraper_enabled=True, authorization_confirmed=False)
        motivo = explicar_bloqueo(cfg)
        assert motivo is not None
        assert "AUTHORIZATION_CONFIRMED" in motivo
        assert "SCRAPER_ENABLED" not in motivo


class TestFormatReport:
    def test_incluye_motivo_y_alternativa(self, tmp_path):
        cfg = Config(data_dir=tmp_path)
        report = format_report(run_diagnostics(cfg), cfg)
        assert "POR QUE NO SE RECOPILAN ANUNCIOS REALES" in report
        assert "main.py import" in report
        assert "Resumen:" in report

    def test_indica_que_falta_la_red(self, tmp_path):
        cfg = Config(data_dir=tmp_path)
        report = format_report(run_diagnostics(cfg), cfg)
        assert "--online" in report

    def test_sin_nota_de_red_si_ya_hubo_online(self, tmp_path):
        cfg = Config(data_dir=tmp_path)
        checks = run_diagnostics(cfg) + [Check("online:search", "OK", "ok")]
        report = format_report(checks, cfg)
        assert "Anade --online" not in report

    def test_lista_errores(self, tmp_path):
        cfg = Config(data_dir=tmp_path)
        report = format_report(
            [Check("dep:falta", "ERROR", "NO instalado")], cfg
        )
        assert "Errores que impiden la recopilacion" in report
        assert "dep:falta" in report


class TestComandoPlantilla:
    def test_template_crea_csv_correcto(self, tmp_path, capsys):
        from main import main

        salida = tmp_path / "plantilla.csv"
        code = main(["template", "--output", str(salida)])

        assert code == 0
        assert salida.exists()
        header = salida.read_text(encoding="utf-8-sig").splitlines()[0]
        assert header.split(",") == list(SPANISH_COLUMNS.values())
        out = capsys.readouterr().out
        assert "Plantilla creada" in out

    def test_template_incluye_campos_requeridos(self, tmp_path):
        from main import main

        salida = tmp_path / "p.csv"
        main(["template", "--output", str(salida)])
        header = salida.read_text(encoding="utf-8-sig").splitlines()[0]
        for campo in (
            "precio",
            "vida_util",
            "potencia_w",
            "marca",
            "modelo",
            "garantia",
            "municipio",
            "fecha_publicacion",
        ):
            assert campo in header, f"falta la columna {campo}"


class TestComandoDiagnose:
    def test_diagnose_sin_red_devuelve_0(self, tmp_path, capsys, monkeypatch):
        from main import main

        monkeypatch.chdir(tmp_path)  # evita leer datos reales del proyecto
        code = main(["diagnose"])
        out = capsys.readouterr().out
        assert code == 0
        assert "DIAGNOSTICO DEL PROYECTO" in out
        assert "online:" not in out
