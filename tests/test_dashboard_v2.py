"""Pruebas de carga, esquema y acuerdos metodológicos del dashboard V2."""

from pathlib import Path

import pandas as pd
import pytest

from dashboard_streamlit.data_loader import (
    DashboardDataError, filter_algorithms, load_integral_report, report_fingerprint,
)


def _write_report(directory: Path, risk_categories=("bajo", "medio", "alto")):
    tables = {
        "episodios": pd.DataFrame({
            "algoritmo": ["Reglas", "PPO"], "semilla": [42, 42],
            "recompensa_acumulada": [1.0, 2.0], "recursos_usados": [3, 4],
        }),
        "resumen_algoritmos": pd.DataFrame({
            "algoritmo": ["Reglas", "PPO"], "recompensa_acumulada_mean": [1.0, 2.0],
        }),
        "clasificaciones_propuestas": pd.DataFrame({
            "algoritmo": ["Reglas"] * 4, "tipo_clasificacion": ["propuesta"] * 4,
            "accion": [0, 1, 2, 3], "accion_nombre": ["Nula", "Mensaje", "Llamada", "Teleorientación"],
            "n": [1, 1, 1, 1], "porcentaje": [25.0] * 4,
        }),
        "clasificaciones_ejecutadas": pd.DataFrame({
            "algoritmo": ["Reglas"] * 4, "tipo_clasificacion": ["ejecutada"] * 4,
            "accion": [0, 1, 2, 3], "accion_nombre": ["Nula", "Mensaje", "Llamada", "Teleorientación"],
            "n": [1, 1, 1, 1], "porcentaje": [25.0] * 4,
        }),
        "estabilidad_semillas": pd.DataFrame({"algoritmo": ["Reglas", "PPO"]}),
        "metricas_subgrupos": pd.DataFrame({
            "algoritmo": ["Reglas"] * len(risk_categories), "semilla": [42] * len(risk_categories),
            "dimension": ["categoria_riesgo"] * len(risk_categories),
            "subgrupo": list(risk_categories), "cobertura": [0.5] * len(risk_categories),
            "intensidad_media": [1.0] * len(risk_categories),
        }),
        "brechas_equidad": pd.DataFrame({
            "algoritmo": ["Reglas"], "semilla": [42], "dimension": ["categoria_riesgo"],
        }),
    }
    rows = []
    for name, frame in tables.items():
        filename = f"{name}.csv"
        frame.to_csv(directory / filename, index=False)
        rows.append({"tabla": name, "archivo": filename, "filas": len(frame)})
    pd.DataFrame(rows).to_csv(directory / "manifest.csv", index=False)


def test_load_integral_report_validates_and_fingerprints(tmp_path):
    _write_report(tmp_path)
    report = load_integral_report(tmp_path)
    assert set(report["episodios"]["algoritmo"]) == {"Reglas", "PPO"}
    assert len(report["fingerprint"]) == 12
    assert report["fingerprint"] == report_fingerprint(tmp_path, report["manifest"])


def test_missing_required_table_is_rejected(tmp_path):
    _write_report(tmp_path)
    (tmp_path / "episodios.csv").unlink()
    with pytest.raises(DashboardDataError, match="episodios.csv"):
        load_integral_report(tmp_path)


def test_manifest_row_mismatch_is_rejected(tmp_path):
    _write_report(tmp_path)
    manifest = pd.read_csv(tmp_path / "manifest.csv")
    manifest.loc[manifest["tabla"] == "episodios", "filas"] = 99
    manifest.to_csv(tmp_path / "manifest.csv", index=False)
    with pytest.raises(DashboardDataError, match="declara 99 filas"):
        load_integral_report(tmp_path)


def test_fourth_risk_category_is_rejected(tmp_path):
    _write_report(tmp_path, risk_categories=("bajo", "medio", "alto", "muy_alto"))
    with pytest.raises(DashboardDataError, match="bajo/medio/alto"):
        load_integral_report(tmp_path)


def test_filter_algorithms_returns_selected_copy(tmp_path):
    _write_report(tmp_path)
    report = load_integral_report(tmp_path)
    filtered = filter_algorithms(report["episodios"], ["PPO"])
    assert filtered["algoritmo"].tolist() == ["PPO"]
    assert len(report["episodios"]) == 2
