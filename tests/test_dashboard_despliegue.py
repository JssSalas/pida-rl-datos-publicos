"""Pruebas de humo de los dashboards publicados (Streamlit Community Cloud).

Renderizan las aplicaciones con ``streamlit.testing`` usando los datos versionados
en ``dashboard_data/`` y fallan si aparece cualquier excepción o mensaje de error.
"""

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
V2_DATA = ROOT / "dashboard_data" / "v2"
V1_FILES = [
    "tabla_decision_final_v1.csv",
    "cobertura_por_riesgo_dashboard_v1.csv",
    "alto_riesgo_por_semilla_dashboard_v1.csv",
    "conclusiones_dashboard_v1.csv",
    "configuracion_dashboard_v1.json",
]

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest


def _render(app: Path, monkeypatch, data_dir: Path | None = None):
    if data_dir is not None:
        monkeypatch.setenv("PIDA_DASHBOARD_DATA_DIR", str(data_dir))
    return AppTest.from_file(str(app), default_timeout=120).run()


@pytest.mark.skipif(not (V2_DATA / "manifest.csv").is_file(), reason="Sin datos V2 publicados")
def test_datos_v2_publicados_son_agregados_y_validos():
    from dashboard_streamlit.data_loader import load_integral_report

    report = load_integral_report(V2_DATA)
    assert not (V2_DATA / "detalle.csv").exists(), "No se publican trazas por perfil."
    manifest = pd.read_csv(V2_DATA / "manifest.csv")
    assert "detalle" not in set(manifest["tabla"])
    riesgo = report["metricas_subgrupos"]
    riesgo = riesgo.loc[riesgo["dimension"] == "categoria_riesgo", "subgrupo"]
    assert set(riesgo.astype(str)) == {"bajo", "medio", "alto"}


@pytest.mark.skipif(not (V2_DATA / "manifest.csv").is_file(), reason="Sin datos V2 publicados")
def test_dashboard_v2_renderiza_sin_errores(monkeypatch):
    at = _render(ROOT / "dashboard_streamlit" / "app.py", monkeypatch, V2_DATA)
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]
    assert len(at.header) >= 1


def test_dashboard_v1_renderiza_sin_errores(monkeypatch):
    app = ROOT / "dashboard_streamlit_v1" / "app.py"
    if not app.is_file() or not all((ROOT / "dashboard_data" / f).is_file() for f in V1_FILES):
        pytest.skip("Dashboard v1 no publicado")
    at = _render(app, monkeypatch)
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]
